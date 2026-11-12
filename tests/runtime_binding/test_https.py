"""Actual TLS and helper-process limits, exclusively against run-owned loopback."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import ipaddress
import json
import os
from pathlib import Path
import ssl
import time
from threading import Event, Thread

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
import pytest

from workload_factory_binding import BindingError
from workload_factory_binding_runtime import (
    DISCOVERY_URL, ISSUER, JWKS_URL, HttpsTransport, IssuerKeySource,
    IssuerWorkloadVerifier,
)
from workload_factory_binding_runtime import transport, _https_worker as wire
from .conftest import jwk, jwt


def private_file(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
    return path


def certificates(directory, *, wrong_host=False):
    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "isolated issuer fixture")])
    leaf_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "loopback issuer leaf")])
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=1))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
          .sign(ca_key, hashes.SHA256()))
    san = x509.DNSName("wrong.invalid") if wrong_host else x509.IPAddress(ipaddress.ip_address("127.0.0.1"))
    leaf = (x509.CertificateBuilder().subject_name(leaf_name).issuer_name(name)
            .public_key(server_key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
            .add_extension(x509.SubjectAlternativeName([san]), critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(ca_key, hashes.SHA256()))
    ca_path = private_file(directory / "ca.pem", ca.public_bytes(serialization.Encoding.PEM))
    cert_path = private_file(directory / "server.pem", leaf.public_bytes(serialization.Encoding.PEM))
    key_path = private_file(directory / "server.key", server_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    return ca_path, cert_path, key_path


@contextmanager
def server(r, tmp_path, monkeypatch, *, mode="normal", wrong_host=False):
    directory = tmp_path / "tls"
    directory.mkdir(mode=0o700)
    ca, cert, key = certificates(directory, wrong_host=wrong_host)
    stopped, requests = Event(), []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass
        def do_GET(self):
            requests.append((self.path, dict(self.headers)))
            if mode == "redirect":
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:9/not-followed")
                body = b"{}"
            else:
                self.send_response(200)
                value = ({"issuer": ISSUER, "jwks_uri": JWKS_URL}
                         if self.path.endswith("openid-configuration")
                         else {"keys": [jwk(r.h.issuer_key)]})
                body = json.dumps(value).encode()
            if mode == "oversized":
                body = b"x" * (wire.MAX_BODY + 1)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "max-age=300")
            self.send_header("Content-Length", str(len(body) + (10 if mode == "truncated" else 0)))
            if mode == "compressed":
                self.send_header("Content-Encoding", "gzip")
            self.end_headers()
            try:
                if mode == "slow":
                    self.wfile.write(body[:1])
                    self.wfile.flush()
                    if stopped.wait(3):
                        return
                    body = body[1:]
                self.wfile.write(body)
            except OSError:
                pass  # Expected when the bounded client closes a refusal case.
    host = HTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    host.socket = context.wrap_socket(host.socket, server_side=True)
    worker = directory / "loopback_worker.py"
    worker.write_text(
        "import importlib.util,sys\n"
        f"s=importlib.util.spec_from_file_location('fixture_wire',{str(Path(wire.__file__).resolve())!r})\n"
        "w=importlib.util.module_from_spec(s);s.loader.exec_module(w)\n"
        f"w.HOST='127.0.0.1';w.PORT={host.server_port}\n"
        "sys.exit(w.main())\n")
    monkeypatch.setattr(transport, "_WORKER", worker)  # Private fixture seam only.
    thread = Thread(target=lambda: host.serve_forever(poll_interval=0.05))
    thread.start()
    try:
        yield HttpsTransport(ca_file=str(ca)), requests, ca
    finally:
        stopped.set()
        host.shutdown()
        host.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()


def test_actual_tls_metadata_signature_and_no_ambient_credentials(r, tmp_path, monkeypatch):
    keylog = tmp_path / "forbidden-keylog"
    monkeypatch.setenv("SSLKEYLOGFILE", str(keylog))
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("SSL_CERT_FILE", str(tmp_path / "missing-ca"))
    monkeypatch.setenv("GITHUB_TOKEN", "CANARY-not-a-credential")
    with server(r, tmp_path, monkeypatch) as (client, requests, _ca):
        now = int(time.time())
        claims = {**r.h.claims, "iat": now, "nbf": now, "exp": now + 120}
        verifier = IssuerWorkloadVerifier(audience="factory:qa", source=IssuerKeySource(transport=client))
        evidence = verifier.verify(jwt(r.h.issuer_key, claims), r.expected, now=now)
        assert evidence.claims == claims
        assert evidence.valid_until == now + 120
        assert len(requests) == 2
        for _path, headers in requests:
            names = {name.lower() for name in headers}
            assert not {"authorization", "proxy-authorization", "cookie"} & names
            assert headers["Accept-Encoding"] == "identity"
    assert not keylog.exists()


@pytest.mark.parametrize("kind", ["untrusted-ca", "wrong-host"])
def test_actual_tls_requires_chain_and_hostname(r, tmp_path, monkeypatch, kind):
    with server(r, tmp_path, monkeypatch, wrong_host=kind == "wrong-host") as (client, requests, ca):
        if kind == "untrusted-ca":
            monkeypatch.setenv("SSL_CERT_FILE", str(ca))
            client = HttpsTransport()  # Ambient test CA must not become trusted.
        with pytest.raises(BindingError, match="^issuer-fetch-unavailable$"):
            client.fetch(DISCOVERY_URL, deadline=time.monotonic() + 10)
        assert not requests


@pytest.mark.parametrize("mode", ["oversized", "compressed", "truncated"])
def test_actual_transport_rejects_malformed_or_oversized_response(r, tmp_path, monkeypatch, mode):
    with server(r, tmp_path, monkeypatch, mode=mode) as (client, requests, _ca):
        with pytest.raises(BindingError, match="^issuer-fetch-unavailable$"):
            client.fetch(DISCOVERY_URL, deadline=time.monotonic() + 10)
        assert len(requests) == 1


def test_actual_transport_does_not_follow_redirect(r, tmp_path, monkeypatch):
    with server(r, tmp_path, monkeypatch, mode="redirect") as (client, requests, _ca):
        source = IssuerKeySource(transport=client)
        verifier = IssuerWorkloadVerifier(audience="factory:qa", source=source)
        with pytest.raises(BindingError, match="^invalid-issuer-response$"):
            verifier.verify(r.h.token, r.expected, now=int(time.time()))
        assert len(requests) == 1


@pytest.mark.parametrize("url", ["http://token.actions.githubusercontent.com/.well-known/jwks",
                                JWKS_URL + "?kid=worker", "https://other.invalid/keys"])
def test_unapproved_endpoint_fails_before_spawn(monkeypatch, url):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("unapproved endpoint reached subprocess")
    monkeypatch.setattr(transport.subprocess, "Popen", forbidden)
    with pytest.raises(BindingError, match="^invalid-issuer-endpoint$"):
        HttpsTransport().fetch(url, deadline=time.monotonic() + 10)


def test_slow_body_is_bounded_and_worker_is_reaped(r, tmp_path, monkeypatch):
    processes = []
    original = transport.subprocess.Popen
    def capture(*args, **kwargs):
        process = original(*args, **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(transport.subprocess, "Popen", capture)
    with server(r, tmp_path, monkeypatch, mode="slow") as (client, requests, _ca):
        with pytest.raises(BindingError, match="^issuer-fetch-unavailable$"):
            client.fetch(DISCOVERY_URL, deadline=time.monotonic() + 1)
        assert len(requests) == 1
    assert processes and all(p.poll() is not None and p.stdout.closed for p in processes)


def test_connect_phase_is_bounded_and_worker_is_reaped(tmp_path, monkeypatch):
    worker = tmp_path / "no-connect.py"
    worker.write_text("import time; time.sleep(5)\n")
    monkeypatch.setattr(transport, "_WORKER", worker)
    monkeypatch.setattr(wire, "CONNECT_SECONDS", 0.2)
    processes = []
    original = transport.subprocess.Popen
    def capture(*args, **kwargs):
        process = original(*args, **kwargs)
        processes.append(process)
        return process
    monkeypatch.setattr(transport.subprocess, "Popen", capture)
    started = time.monotonic()
    with pytest.raises(BindingError, match="^issuer-fetch-unavailable$"):
        HttpsTransport().fetch(DISCOVERY_URL, deadline=started + 10)
    assert time.monotonic() - started < 2
    assert processes and all(p.poll() is not None for p in processes)


def test_interrupt_reaps_connected_worker(tmp_path, monkeypatch):
    worker = tmp_path / "connected.py"
    worker.write_text("import sys,time;sys.stdout.write('C');sys.stdout.flush();time.sleep(5)\n")
    monkeypatch.setattr(transport, "_WORKER", worker)
    processes = []
    original = transport.subprocess.Popen
    def capture(*args, **kwargs):
        process = original(*args, **kwargs)
        processes.append(process)
        def interrupt(*_a, **_kw):
            raise KeyboardInterrupt
        process.communicate = interrupt
        return process
    monkeypatch.setattr(transport.subprocess, "Popen", capture)
    with pytest.raises(KeyboardInterrupt):
        HttpsTransport().fetch(DISCOVERY_URL, deadline=time.monotonic() + 10)
    assert processes and all(p.poll() is not None and p.stdout.closed for p in processes)
