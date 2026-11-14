"""Private fixture PKI and separate authority process, never deployed trust."""
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
import pytest

from factory_binding.test_owner_integration import private_write
from workload_factory_binding.evidence import canonical
from workload_factory_binding_runtime.reference_authority.client import AuthorityClient
from workload_factory_binding_runtime.reference_authority.model import signed_observation
from workload_factory_binding_runtime.reference_authority.store import AuthorityStore, initialize_store
from .test_bootstrap import b
from .test_workflow import w
from .composition_fixture import c
from .test_config import configuration
from .test_lifecycle import l


def pki(root):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "fixture authority CA")])
    now = datetime.now(timezone.utc)
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
          .not_valid_after(now + timedelta(hours=1))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), True).sign(key, hashes.SHA256()))
    ca_file = root / "ca.pem"
    private_write(ca_file, ca.public_bytes(serialization.Encoding.PEM))
    result = {}
    for role in ("server", "operator", "controller", "reader", "worker"):
        leaf = ec.generate_private_key(ec.SECP256R1())
        builder = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, role)]))
                   .issuer_name(name).public_key(leaf.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(hours=1))
                   .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH if role == "server"
                                                        else x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]), False))
        if role == "server":
            builder = builder.add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
        cert = builder.sign(key, hashes.SHA256())
        cert_file, key_file = root / role / "cert.pem", root / role / "key.pem"
        private_write(cert_file, cert.public_bytes(serialization.Encoding.PEM))
        private_write(key_file, leaf.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                  serialization.NoEncryption()))
        result[role] = (str(cert_file), str(key_file), "sha256:" + cert.fingerprint(hashes.SHA256()).hex())
    return str(ca_file), result


@pytest.fixture
def a(b, tmp_path):
    root = tmp_path / "authority"
    root.mkdir(mode=0o700)
    controller_key = ed25519.Ed25519PrivateKey.generate()
    public_key = controller_key.public_key().public_bytes_raw()
    identity = initialize_store(root / "state", public_key)
    result = SimpleNamespace(b=b, root=root, key=controller_key, public_key=public_key, identity=identity,
                             now=b.w.c.h.now, processes=[], launches=0)
    result.open = lambda: AuthorityStore(root / "state", identity=identity, controller_public_key=public_key,
                                         clock=lambda: result.now)
    result.store = result.open()
    result.envelope = lambda context=b.context, event="event:assigned": signed_observation(
        controller_key, context, event_ref=event, now=result.now, expires_at=result.now + 50)
    ca, peers = pki(root / "tls")
    result.ca, result.peers = ca, peers
    def launch(permissions=None):
        result.launches += 1
        directory = root / ("process-" + str(result.launches))
        directory.mkdir(mode=0o700)
        selected = dict(directory=str(root / "state"), identity=asdict(identity), public_key=public_key.hex(),
                        now=result.now, ca_file=ca, cert_file=peers["server"][0], key_file=peers["server"][1],
                        ready=str(directory / "ready"), permissions=permissions or {
                            peers["operator"][2]: ["authorize", "revoke"], peers["controller"][2]: ["observe"],
                            peers["reader"][2]: ["claim", "operation"], peers["worker"][2]: []})
        config = directory / "config.json"
        private_write(config, canonical(selected))
        process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).with_name("authority_process.py")), str(config)],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env={"PATH": os.defpath, "LANG": "C.UTF-8"}, umask=0o077)
        result.processes.append(process)
        timeout = time.monotonic() + 8
        while not Path(selected["ready"]).exists():
            assert process.poll() is None, "authority process failed"
            assert time.monotonic() < timeout, "authority process did not start"
            time.sleep(0.02)
        port = int(Path(selected["ready"]).read_text())
        clients = {role: AuthorityClient(port=port, ca_file=ca, cert_file=peer[0], key_file=peer[1],
                    server_fingerprint=peers["server"][2], clock=lambda: result.now)
                   for role, peer in peers.items() if role != "server"}
        return SimpleNamespace(process=process, port=port, clients=clients)
    result.launch = launch
    try:
        yield result
    finally:
        for process in result.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            for stream in (process.stdout, process.stderr):
                stream.close()
            assert process.poll() is not None


def authorization(a):
    return dict(ref=a.b.context.preauthorization_ref, selection=json.loads(a.b.document),
                not_before=a.now, expires_at=a.now + 60)


def approve(a):
    a.store.authorize(**authorization(a))
    a.store.observe(envelope=a.envelope())


def assigned(a, **changes):
    return dict(context={**asdict(a.b.context), **changes}, event_ref="event:assigned")
