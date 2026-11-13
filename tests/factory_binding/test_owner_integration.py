"""Exact accepted-source integration; explicitly requested source must fail, never skip."""
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import ipaddress
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from workload_factory_binding.evidence import (
    artifact_digest, byte_digest, canonical, decode_object,
)
from .conftest import Harness, multibase
from .fixture_role import worker_configuration

OWNER_COMMIT = "bb0e9dae89a771b05f6c235d0a77237288b95c85"
ROLE = Path(__file__).with_name("fixture_role.py")


class InjectedFailure(RuntimeError):
    pass


def owner_source():
    selected = os.environ.get("WALLET_BINDING_OWNER_CODE")
    if selected is None:
        pytest.skip("owning-source integration requires explicit WALLET_BINDING_OWNER_CODE; matrix is separate")
    path = Path(selected).resolve(strict=True)
    actual = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True,
                            capture_output=True, text=True, timeout=30).stdout.strip()
    assert actual == OWNER_COMMIT, "unapproved owner source"
    subprocess.run(["git", "-C", str(path), "diff", "--exit-code", "HEAD", "--"],
                   check=True, capture_output=True, timeout=30)
    status = subprocess.run(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"],
                            check=True, capture_output=True, text=True, timeout=30).stdout
    assert not status, "owner source is dirty"
    sys.path.insert(0, str(path))
    import openwallet_runtime.proof as proof
    assert Path(proof.__file__).resolve().is_relative_to(path), "ambient package substituted for selected source"
    return path


def private_write(path, raw):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)


def make_pki(directory, *, ca_common_name="isolated fixture CA"):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, ca_common_name)])
    now = datetime.now(timezone.utc)
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
          .not_valid_after(now + timedelta(hours=1))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .sign(key, hashes.SHA256()))
    ca_file = directory / "ca.pem"
    private_write(ca_file, ca.public_bytes(serialization.Encoding.PEM))

    def leaf(role, server=False):
        leaf_key = ec.generate_private_key(ec.SECP256R1())
        builder = (x509.CertificateBuilder()
                   .subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, role)]))
                   .issuer_name(name).public_key(leaf_key.public_key())
                   .serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(hours=1))
                   .add_extension(x509.ExtendedKeyUsage(
                       [x509.oid.ExtendedKeyUsageOID.SERVER_AUTH if server else
                        x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False))
        if server:
            builder = builder.add_extension(
                x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
        certificate = builder.sign(key, hashes.SHA256())
        cert_file, key_file = directory / role / "cert.pem", directory / role / "key.pem"
        private_write(cert_file, certificate.public_bytes(serialization.Encoding.PEM))
        private_write(key_file, leaf_key.private_bytes(serialization.Encoding.PEM,
                      serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        return cert_file, key_file, certificate.fingerprint(hashes.SHA256()).hex()
    return ca_file, leaf("custody", True), leaf("gate"), leaf("worker")


def launch(role, config, directory, *, wait=True):
    config_path = directory / (role + ".json")
    private_write(config_path, canonical(config))
    process = subprocess.Popen([sys.executable, str(ROLE), role, str(config_path)],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={"PATH": os.defpath, "LANG": "C.UTF-8", "PYTHONNOUSERSITE": "1",
                                    "PYTHONDONTWRITEBYTECODE": "1"}, umask=0o077)
    if wait:
        try:
            output, errors = process.communicate(timeout=15)
        except BaseException:
            process.kill()
            process.wait(timeout=5)
            raise
        assert process.returncode == 0, "fixture role failed"
        return process, decode_object(output)
    return process, None


def qualify(owner, directory, processes, inject_failure, allow_worker_sign=False, worker_drift=None):
    from openwallet_runtime.custody import RemoteRegistry, RemoteSigner, TLSClient
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    from openwallet_runtime.reference_service import provision_key
    from openwallet_runtime.registry import BindingRegistry, binding_record

    h = Harness(directory)
    ca, server, gate_peer, worker_peer = make_pki(directory / "tls")
    registry_dir, key_dir = directory / "registry", directory / "custody-keys"
    public_key = provision_key(key_dir, h.binding.key_ref)
    binding = TrustedKeyBinding(**{**asdict(h.binding), "public_key": public_key})
    registry = BindingRegistry(registry_dir)
    registry.register(binding, expected_revision=None)
    h.binding = binding
    h.policy["binding"]["public_key_digest"] = byte_digest(public_key)
    h.policy["wallet"]["key_reference"]["public_key_multibase"] = multibase(public_key)
    h.artifact = ROLE
    h.artifacts = {"worker": str(ROLE)}
    h.configuration = {"role": "worker", "owner_commit": OWNER_COMMIT, "tools": []}
    h.policy["composition_digest"] = artifact_digest(h.artifacts, h.configuration)
    h.reset_evidence()
    ready = directory / "custody.ready"
    config = {
        "owner_code": str(owner), "now": h.now, "registry_directory": str(registry_dir),
        "key_directory": str(key_dir), "ca_file": str(ca),
        "certificate": str(server[0]), "private_key": str(server[1]), "ready": str(ready),
        "policies": {
            gate_peer[2]: {"actions": ["resolve", "sign"], "subjects": [binding.subject_ref]},
            worker_peer[2]: {"actions": ["resolve", "sign"] if allow_worker_sign else ["resolve"],
                             "subjects": [binding.subject_ref]},
        },
    }
    custody, _ = launch("custody", config, directory, wait=False)
    processes.append(custody)
    deadline = time.monotonic() + 10
    while not ready.exists():
        assert custody.poll() is None, "custody exited before readiness"
        assert time.monotonic() < deadline, "custody readiness timeout"
        time.sleep(0.03)
    endpoint = "https://127.0.0.1:" + ready.read_text()
    client = TLSClient(endpoint, ca_file=ca, certificate=gate_peer[0], private_key=gate_peer[1])
    remote = RemoteSigner(client, subject_ref=binding.subject_ref)
    registry_client = RemoteRegistry(client)

    class CountingSigner:
        calls = 0

        def sign(self, message):
            self.calls += 1
            return remote.sign(message)

    signer = CountingSigner()
    h.gate = h.make_gate(registry=registry_client, signer=signer, create_proof=create_proof)

    # Separate observer gets trusted selected paths/config and its own private key.
    observer_key = directory / "observer" / "key.pem"
    private_write(observer_key, h.supervisor.private_bytes(serialization.Encoding.PEM,
                  serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    challenge = {**asdict(h.challenge), "digest": h.challenge.digest}
    worker_config = directory / "worker-observed.json"
    worker_record = {
        "owner_code": str(owner), "endpoint": endpoint, "ca_file": str(ca),
        "certificate": str(worker_peer[0]), "private_key": str(worker_peer[1]),
        "binding": binding_record(binding), "challenge_digest": h.challenge.digest, "now": h.now,
    }
    h.configuration = worker_configuration(worker_record)
    h.policy["composition_digest"] = artifact_digest(h.artifacts, h.configuration)
    h.reset_evidence()
    challenge = {**asdict(h.challenge), "digest": h.challenge.digest}
    worker_record["challenge_digest"] = h.challenge.digest
    if worker_drift == "challenge_digest":
        worker_record["challenge_digest"] = "sha256:" + "f" * 64
    elif worker_drift == "binding":
        worker_record["binding"]["key_ref"] = "key:other"
    elif worker_drift == "endpoint":
        worker_record["endpoint"] = "https://127.0.0.1:1"
    elif worker_drift == "owner_code":
        worker_record["owner_code"] = str(directory)
    private_write(worker_config, canonical(worker_record))
    observer, observed = launch("observe", {
        "private_key": str(observer_key), "policy": h.policy, "request": h.request,
        "token": h.token, "challenge": challenge, "artifacts": h.artifacts,
        "configuration": h.configuration, "now": h.now, "worker_config": str(worker_config),
    }, directory)
    processes.append(observer)
    assert observed["worker"] == {"direct_sign_denied": True}
    assert observed["worker_exited"] is True
    h.observation = observed["observation"]
    result = h.run()
    verified = verify_proof(result["proof"], expected_digest=h.challenge.digest,
                            binding=registry_client.resolve(binding.subject_ref, now=h.now), now=h.now)
    assert verified.subject_ref == "agent:qa"
    assert result["human_approval"] is False
    assert signer.calls == 1

    # Binding changes are observed from the actual remote registry.
    registry.revoke(binding.binding_ref)
    from workload_factory_binding import BindingError
    with pytest.raises(BindingError):
        h.run()
    assert signer.calls == 1
    if inject_failure:
        raise InjectedFailure("after owning proof verification")
    return result


@pytest.mark.parametrize("inject_failure", [False, True], ids=["success-cleanup", "failure-cleanup"])
def test_owning_custody_and_cleanup(tmp_path, inject_failure):
    owner = owner_source()
    processes = []
    temporary = None
    try:
        with TemporaryDirectory(prefix="factory-binding-", dir=tmp_path) as folder:
            temporary = Path(folder)
            try:
                if inject_failure:
                    with pytest.raises(InjectedFailure):
                        qualify(owner, temporary, processes, True)
                else:
                    qualify(owner, temporary, processes, False)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
                    if process.stdout:
                        process.stdout.close()
                    if process.stderr:
                        process.stderr.close()
    finally:
        assert all(process.poll() is not None for process in processes)
        assert temporary is not None
        assert not temporary.exists(), "ephemeral keys/state remain"


def test_denial_probe_detects_excess_worker_permission(tmp_path):
    owner = owner_source()
    processes = []
    with TemporaryDirectory(prefix="factory-binding-mutation-", dir=tmp_path) as folder:
        temporary = Path(folder)
        try:
            with pytest.raises(AssertionError, match="fixture role failed"):
                qualify(owner, temporary, processes, False, allow_worker_sign=True)
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
    assert all(process.poll() is not None for process in processes)
    assert not temporary.exists()


@pytest.mark.parametrize("drift", ["challenge_digest", "binding", "endpoint", "owner_code"])
def test_observer_refuses_changed_worker_configuration(tmp_path, drift):
    owner = owner_source()
    processes = []
    with TemporaryDirectory(prefix="factory-binding-drift-", dir=tmp_path) as folder:
        temporary = Path(folder)
        try:
            with pytest.raises(AssertionError, match="fixture role failed"):
                qualify(owner, temporary, processes, False, worker_drift=drift)
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
    assert all(process.poll() is not None for process in processes)
    assert not temporary.exists()
