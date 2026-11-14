"""Actual RSA signatures and loopback HTTPS only; no provider token is requested."""
from dataclasses import replace
from copy import deepcopy
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os
import ssl
import subprocess
import threading
import time
from types import SimpleNamespace
import pytest
from workload_factory_binding.evidence import BindingError, canonical, decode64, encode64
from workload_factory_binding.ledger import ReplayLedger
from workload_factory_binding_runtime.github_bootstrap import ERROR
from workload_factory_binding_runtime.github_bootstrap.client import TokenClient
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.github_bootstrap.https import Https, Response
from workload_factory_binding_runtime.github_bootstrap.identity import (IdentityPolicy, BootstrapVerifier,
    BOOTSTRAP_AUDIENCE, BASE_CLAIMS)
from .conftest import jwt
from .test_https import certificates

@pytest.fixture
def identity(r):
    expected = {**r.expected, "event_name": "workflow_dispatch"}
    expected.update(sha="b" * 40, workflow_sha="b" * 40, job_workflow_sha="b" * 40)
    del expected["environment"]
    expected["sub"] = "repo:fixture/factory:ref:refs/heads/main"
    policy = IdentityPolicy("preflight", BOOTSTRAP_AUDIENCE, "factory:qa", expected)
    claims = {**r.h.claims, **expected, "aud": BOOTSTRAP_AUDIENCE}
    del claims["environment"]
    return SimpleNamespace(r=r, policy=policy, claims=claims, verifier=BootstrapVerifier(r.source))

def verify(i, claims=None):
    return i.verifier.verify(jwt(i.r.h.issuer_key, claims or i.claims), i.policy, now=i.r.h.now)

def test_bootstrap_signature_and_selected_phase_are_independent(identity):
    i = identity
    evidence = verify(i)
    assert evidence.phase == "preflight"
    assert evidence.valid_until == i.r.h.now + 60
    assert "environment" not in evidence.claims
    assert i.r.h.calls == 0
    with pytest.raises(TypeError): evidence.claims["aud"] = "other"
    protected = {**dict(i.policy.expected), "environment": "qa", "sub": "repo:fixture/factory:environment:qa"}
    policy = IdentityPolicy("protected", BOOTSTRAP_AUDIENCE, "factory:qa", protected)
    token = jwt(i.r.h.issuer_key, {**i.claims, **protected})
    assert i.verifier.verify(token, policy, now=i.r.h.now).phase == "protected"
    with pytest.raises(BindingError, match="^" + ERROR + "$"):
        i.verifier.verify(token, i.policy, now=i.r.h.now)

@pytest.mark.parametrize("field", sorted(BASE_CLAIMS | {"iss", "aud", "jti"}))
def test_each_bootstrap_claim_is_independently_required(identity, field):
    changed = dict(identity.claims)
    changed[field] = "" if field == "jti" else "wrong-canary"
    with pytest.raises(BindingError, match="^" + ERROR + "$"): verify(identity, changed)
    assert identity.r.h.calls == 0

@pytest.mark.parametrize("field", ["iat", "nbf", "exp"])
@pytest.mark.parametrize("value", [None, True, -1, "1800000000", 1.5])
def test_time_claims_require_exact_bounded_integers(identity, field, value):
    changed = dict(identity.claims, **{field: value})
    with pytest.raises(BindingError): verify(identity, changed)

@pytest.mark.parametrize("change", ["stale", "future-iat", "future-nbf", "expired", "overlong", "array-audience", "environment"])
def test_staleness_and_wrong_phase_cannot_extend_identity(identity, change):
    c, now = dict(identity.claims), identity.r.h.now
    if change == "stale": c["iat"] = now - 60
    elif change == "future-iat": c["iat"] = now + 1
    elif change == "future-nbf": c["nbf"] = now + 1
    elif change == "expired": c["exp"] = now
    elif change == "overlong": c["exp"] = now + 301
    elif change == "array-audience": c["aud"] = [BOOTSTRAP_AUDIENCE]
    else: c["environment"] = "qa"
    with pytest.raises(BindingError): verify(identity, c)

@pytest.mark.parametrize("barrier", ["audience-only", "environment-only", "provider-shaped"])
def test_signed_proof_controls_isolate_audience_and_environment_before_custody(r, tmp_path, barrier):
    r.h.gate = r.h.make_gate(workload_verifier=r.verifier)
    assert r.h.run()["assurance"] == "possession"
    assert r.h.calls == 1
    # Fresh reservation scope prevents replay failure from masking a removed identity guard.
    r.h.ledger = ReplayLedger(tmp_path / "independent-control-ledger")
    r.h.calls = 0
    baseline = dict(r.h.claims)
    if barrier == "audience-only": r.h.claims["aud"] = BOOTSTRAP_AUDIENCE
    else:
        del r.h.claims["environment"]
        if barrier == "provider-shaped": r.h.claims["sub"] = "repo:fixture/factory:ref:refs/heads/main"
    expected_changes = {"aud"} if barrier == "audience-only" else {"environment"}
    if barrier == "provider-shaped": expected_changes.add("sub")
    assert {k for k in baseline.keys() | r.h.claims.keys() if baseline.get(k) != r.h.claims.get(k)} == expected_changes
    r.h.reset_evidence()
    r.h.gate = r.h.make_gate(workload_verifier=r.verifier)
    with pytest.raises(BindingError, match="^workload-mismatch$"): r.h.run()
    assert r.h.calls == 0

@pytest.mark.parametrize("failure", ["bad-signature", "bad-alg", "token-url", "unknown-key", "oversize", "duplicate"])
def test_untrusted_token_data_cannot_select_keys_or_leak_payload(identity, failure):
    i = identity
    token = jwt(i.r.h.issuer_key, i.claims)
    if failure == "bad-signature":
        parts = token.split(".")
        signature = bytearray(decode64(parts[2]))
        signature[0] ^= 1
        token = ".".join([*parts[:2], encode64(bytes(signature))])
    elif failure == "bad-alg": token = jwt(i.r.h.issuer_key, i.claims, {"alg": "none", "typ": "JWT", "kid": "issuer-key"})
    elif failure == "token-url": token = jwt(i.r.h.issuer_key, i.claims, {"alg": "RS256", "typ": "JWT", "kid": "issuer-key", "jku": "https://canary.invalid"})
    elif failure == "unknown-key": token = jwt(i.r.h.issuer_key, i.claims, {"alg": "RS256", "typ": "JWT", "kid": "unknown"})
    elif failure == "oversize": token = "secret-canary" * 2000
    else: token = "e30.eyJhdWQiOiJhIiwiYXVkIjoiYiJ9.YQ"
    with pytest.raises(BindingError, match="^" + ERROR + "$") as caught:
        i.verifier.verify(token, i.policy, now=i.r.h.now)
    assert "canary" not in str(caught.value)

class TokenTransport:
    def __init__(self, value=None):
        self.response = Response(200, canonical({"value": value or "synthetic.jwt.only"}))
        self.calls = []
    def exchange(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response

def test_token_request_is_pinned_and_audience_is_encoded_not_a_permission_limit():
    transport = TokenTransport()
    endpoint = "https://issuer-job.invalid/idtoken?api-version=2.0"
    client = TokenClient(endpoint=endpoint, audience=BOOTSTRAP_AUDIENCE, transport=transport)
    environment = {"ACTIONS_ID_TOKEN_REQUEST_URL": endpoint, "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "credential-canary"}
    assert client.acquire(environment, decision=Decision(clock=lambda: 1800000000)) == "synthetic.jwt.only"
    (method, url), args = transport.calls[0]
    assert method == "GET"
    assert "audience=urn%3Aopensoft%3A" in url
    assert args["headers"]["Authorization"] == "Bearer credential-canary"
    assert "credential-canary" not in repr(client)

@pytest.mark.parametrize("change", ["url", "credential", "newline", "redirect", "status", "malformed", "oversize", "missing-value", "duplicate"])
def test_token_acquisition_refuses_changed_endpoint_and_bad_response(change):
    transport = TokenTransport()
    endpoint = "https://issuer-job.invalid/idtoken"
    client = TokenClient(endpoint=endpoint, audience=BOOTSTRAP_AUDIENCE, transport=transport)
    env = {"ACTIONS_ID_TOKEN_REQUEST_URL": endpoint, "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "credential-canary"}
    if change == "url": env["ACTIONS_ID_TOKEN_REQUEST_URL"] = "https://worker.invalid"
    elif change == "credential": env.pop("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    elif change == "newline": env["ACTIONS_ID_TOKEN_REQUEST_TOKEN"] = "x\nCANARY"
    else:
        body = {"malformed": b"private-canary", "oversize": b"x" * 24577,
                "missing-value": b'{"count":1}', "duplicate": b'{"value":"x","value":"y"}'}.get(change, b"{}")
        transport.response = Response(302 if change == "redirect" else 429 if change == "status" else 200, body)
    with pytest.raises(BindingError, match="^" + ERROR + "$"):
        client.acquire(env, decision=Decision(clock=lambda: 1800000000))
    if change in ("url", "credential", "newline"): assert not transport.calls

@contextmanager
def loopback(tmp_path, *, wrong_host=False, mode="normal", post=None, require_user_agent=False):
    directory = tmp_path / "bootstrap-tls"
    directory.mkdir(mode=0o700)
    ca, cert, key = certificates(directory, wrong_host=wrong_host)
    requests, stop = [], threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_POST(self):
            requests.append((self.path, dict(self.headers)))
            try:
                length = int(self.headers["Content-Length"])
                if not 0 < length <= 65536 or post is None:
                    raise ValueError("invalid-fixture-request")
                if require_user_agent and not self.headers.get("User-Agent"):
                    raise ValueError("missing-fixture-user-agent")
                body = post(self.rfile.read(length))
                self.send_response(200)
            except Exception:
                body = b'{"error":"github-bootstrap-refused"}'
                self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            requests.append((self.path, dict(self.headers)))
            body = b'{"value":"synthetic.jwt.only"}'
            status = 302 if mode == "redirect" else 200
            if require_user_agent and not self.headers.get("User-Agent"):
                status = 403
                body = b'{"error":"missing-fixture-user-agent"}'
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Location", "https://127.0.0.1:9/not-followed")
            if mode == "oversize": body = b"x" * 1048577
            self.send_header("Content-Length", str(len(body) + (10 if mode == "truncated" else 0)))
            if mode == "compressed": self.send_header("Content-Encoding", "gzip")
            self.end_headers()
            try:
                if mode == "slow":
                    self.wfile.write(body[:1]);self.wfile.flush()
                    stop.wait(3)
                    return
                self.wfile.write(body)
            except OSError: pass
    server = HTTPServer(("127.0.0.1", 0), Handler)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert, key)
    server.socket = tls.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.03))
    thread.start()
    try:
        yield Https(ca_file=ca), "https://127.0.0.1:" + str(server.server_port) + "/idtoken", requests
    finally:
        stop.set();server.shutdown();server.server_close();thread.join(timeout=3)
        assert not thread.is_alive()

def test_real_tls_token_request_has_no_ambient_proxy_ca_or_keylog(tmp_path, monkeypatch):
    keylog = tmp_path / "forbidden-keylog"
    monkeypatch.setenv("SSLKEYLOGFILE", str(keylog));monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("SSL_CERT_FILE", str(tmp_path / "untrusted"))
    with loopback(tmp_path) as (transport, endpoint, requests):
        client = TokenClient(endpoint=endpoint, audience=BOOTSTRAP_AUDIENCE, transport=transport)
        env = {"ACTIONS_ID_TOKEN_REQUEST_URL": endpoint, "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fixture-request-capability"}
        assert client.acquire(env, decision=Decision(clock=lambda: int(time.time()))) == "synthetic.jwt.only"
        assert len(requests) == 1
        assert requests[0][1]["Authorization"] == "Bearer fixture-request-capability"
    assert not keylog.exists()

@pytest.mark.parametrize("mode", ["wrong-host", "untrusted-ca", "redirect", "oversize", "truncated", "compressed", "slow"])
def test_real_tls_failures_never_follow_redirect_and_reap_child(tmp_path, monkeypatch, mode):
    processes = []
    original = subprocess.Popen
    def capture(*args, **kwargs):
        child = original(*args, **kwargs);processes.append(child);return child
    monkeypatch.setattr(subprocess, "Popen", capture)
    with loopback(tmp_path, wrong_host=mode == "wrong-host", mode=mode) as (transport, endpoint, requests):
        if mode == "untrusted-ca": transport = Https()
        client = TokenClient(endpoint=endpoint, audience=BOOTSTRAP_AUDIENCE, transport=transport)
        env = {"ACTIONS_ID_TOKEN_REQUEST_URL": endpoint, "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fixture-request-capability"}
        with pytest.raises(BindingError):
            client.acquire(env, decision=Decision(clock=lambda: int(time.time()), deadline=int(time.time()) + (1 if mode == "slow" else 10)))
        assert len(requests) <= 1
    assert processes
    for child in processes:
        assert child.poll() is not None
        assert child.stdin.closed
        assert child.stdout.closed


def test_interrupt_after_tls_reaps_child_before_transmitting_credentials(tmp_path, monkeypatch):
    processes = []
    original = subprocess.Popen
    def capture(*args, **kwargs):
        child = original(*args, **kwargs);processes.append(child);return child
    monkeypatch.setattr(subprocess, "Popen", capture)
    def interrupt(): raise KeyboardInterrupt
    with loopback(tmp_path) as (transport, endpoint, requests):
        with pytest.raises(KeyboardInterrupt):
            transport.exchange("GET", endpoint, headers={"Authorization": "Bearer fixture-only"},
                decision=Decision(clock=lambda: int(time.time())), before_send=interrupt)
        assert not requests
    assert processes
    for child in processes:
        assert child.poll() is not None
        assert child.stdin.closed
        assert child.stdout.closed

@pytest.mark.parametrize("endpoint", ["http://worker.invalid/token", "https://name:password@worker.invalid/token",
    "https://worker.invalid/token#fragment", "https://worker.invalid/token?audience=wrong", "https://worker.invalid/token?a=1&a=2"])
def test_token_endpoint_must_be_an_exact_selected_https_target(endpoint):
    with pytest.raises(BindingError): TokenClient(endpoint=endpoint, audience=BOOTSTRAP_AUDIENCE)


def test_external_token_metadata_is_projected_out_not_echoed_or_authoritative():
    transport = TokenTransport()
    transport.response = Response(200, canonical({"count": 1, "value": "synthetic.jwt.only", "metadata": "provider-private-canary"}))
    endpoint = "https://issuer-job.invalid/idtoken"
    client = TokenClient(endpoint=endpoint, audience=BOOTSTRAP_AUDIENCE, transport=transport)
    result = client.acquire({"ACTIONS_ID_TOKEN_REQUEST_URL": endpoint, "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fixture-only"},
                            decision=Decision(clock=lambda: 1800000000))
    assert result == "synthetic.jwt.only"
    assert "canary" not in result


def test_signature_negative_reaches_crypto_after_canonical_decode(identity, monkeypatch):
    from workload_factory_binding_runtime.github_bootstrap import identity as implementation
    original = implementation.rsa.RSAPublicNumbers
    calls = []
    def public_numbers(*numbers):
        key = original(*numbers).public_key()
        def checked_verify(*arguments):
            calls.append(True)
            return key.verify(*arguments)
        return SimpleNamespace(public_key=lambda: SimpleNamespace(verify=checked_verify))
    monkeypatch.setattr(implementation, "rsa", SimpleNamespace(RSAPublicNumbers=public_numbers))
    i = identity
    token = jwt(i.r.h.issuer_key, i.claims)
    assert i.verifier.verify(token, i.policy, now=i.r.h.now).phase == "preflight"
    parts = token.split(".")
    signature = bytearray(decode64(parts[2]))
    signature[0] ^= 1
    encoded = encode64(bytes(signature))
    assert decode64(encoded) == bytes(signature)
    invalid = ".".join([*parts[:2], encoded])
    with pytest.raises(BindingError, match="^" + ERROR + "$"):
        i.verifier.verify(invalid, i.policy, now=i.r.h.now)
    assert len(calls) == 2
