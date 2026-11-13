"""Confined credential binding/refusal vectors and real owning-service G03."""
from dataclasses import asdict, replace
import base64
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

import pytest

from workload_factory_binding.evidence import BindingError, byte_digest, digest
from workload_factory_binding_runtime.loaders import BoundService, ServiceIdentity
from factory_binding.conftest import multibase
from factory_binding.test_owner_integration import launch, owner_source, private_write
from .composition_fixture import c
from .custody_fixture import k
from .test_config import configuration, encoded


def test_selected_issuance_and_material_allow_unchanged_sign_interface(k):
    assert k.signer.sign(b"bounded owning preimage") == b"s" * 64
    assert [entry[0] for entry in k.calls] == ["sign"]
    assert k.deadlines == [k.c.h.now + 30, k.c.h.now + 25]
    assert "private" not in repr(k.signer.material)
    assert "principal:gate" not in repr(k.access)


@pytest.mark.parametrize("field,value", [
    ("deployment_ref", "deployment:other"), ("boundary_ref", "boundary:other"),
    ("issuance_ref", "issuance:other"), ("gate_principal", "principal:worker_channel"),
    ("config_digest", "sha256:" + "f" * 64), ("sources_digest", "sha256:" + "f" * 64),
    ("case_ref", "case:other"), ("run_id", "999"), ("run_attempt", "2"),
    ("certificate_digest", "sha256:" + "f" * 64), ("endpoint_digest", "sha256:" + "f" * 64),
    ("subject_ref", "agent:other"), ("key_ref", "key:other"), ("custody_ref", "custody:other"),
    ("actions", ("resolve", "sign")), ("actions", ["sign"]), ("actions", ()),
])
def test_each_fresh_binding_or_scope_change_refuses_before_signing(k, field, value):
    k.access = replace(k.access, **{field: value})
    with pytest.raises(BindingError):
        k.signer.sign(b"preimage")
    assert k.calls == []


@pytest.mark.parametrize("field", ["service_ref", "principal_ref", "credential_ref", "trust_digest"])
def test_each_intrinsic_service_identity_change_refuses(k, field):
    k.access = replace(k.access, service=replace(k.identity, **{field: "changed"}))
    with pytest.raises(BindingError, match="^custody-issuance-mismatch$"):
        k.signer.sign(b"preimage")
    assert k.calls == []


@pytest.mark.parametrize("field,value", [("issued_at", True), ("issued_at", 1800000001),
                                       ("expires_at", True), ("expires_at", 0)])
def test_invalid_or_stale_access_refuses(k, field, value):
    k.access = replace(k.access, **{field: value})
    with pytest.raises(BindingError, match="^custody-access-expired$"):
        k.signer.sign(b"preimage")
    assert k.calls == []


def test_expired_overlong_and_future_access_refuse(k):
    original = k.access
    for changes in ({"expires_at": k.c.h.now}, {"expires_at": k.c.h.now + 60},
                    {"issued_at": k.c.h.now + 1}):
        k.access = replace(original, **changes)
        with pytest.raises(BindingError, match="^custody-access-expired$"):
            k.signer.sign(b"preimage")
    assert k.calls == []


@pytest.mark.parametrize("role", ["worker_channel", "supervisor", "readback"])
def test_gate_principal_is_separate_from_worker_supervisor_and_readback(k, role):
    principal = (k.c.trust.readback_principal if role == "readback" else
                 k.c.config["services"][role]["principal_ref"])
    trust = replace(k.trust, gate_principal=principal)
    with pytest.raises(BindingError, match="^custody-gate-not-independent$"):
        k.make(custody_trust=trust)
    assert k.calls == []


@pytest.mark.parametrize("name", ["ca_file", "certificate", "private_key"])
def test_changed_actual_files_refuse(k, name):
    path = getattr(k.material, name)
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(BindingError, match="^custody-material-changed$"):
        k.signer.sign(b"preimage")
    assert k.calls == []


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory", "oversize", "unsafe-key"])
def test_unsafe_or_unavailable_material_refuses_without_blocking(k, tmp_path, kind):
    path = tmp_path / "bad-material"
    if kind == "symlink":
        path.symlink_to(k.material.private_key)
    elif kind == "fifo":
        import os
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        path.write_bytes(b"x" * (16385 if kind == "oversize" else 10))
        path.chmod(0o644)
    material = replace(k.material, private_key=path)
    with pytest.raises(BindingError, match="^custody-material-unavailable$"):
        k.make(material=material)
    assert k.calls == []


def test_worker_boolean_body_cannot_supply_access(k):
    k.access = {"confined": True, "worker_denied": True}
    with pytest.raises(BindingError, match="^custody-access-unverified$"):
        k.signer.sign(b"preimage")
    assert k.calls == []


def test_new_custody_assertion_model_requires_upstream_owner(k):
    with pytest.raises(BindingError, match="^custody-owner-decision-required$"):
        k.make(trust_model="custody-verifies-per-use-assertion")
    assert k.calls == []


def test_client_construction_material_race_refuses(k):
    def changed(*args, **kwargs):
        k.material.private_key.write_bytes(b"different-private-key")
        return object()
    with pytest.raises(BindingError, match="^custody-material-changed$"):
        k.make(tls_client=changed)


def test_readback_failure_is_redacted_and_no_signer_called(k):
    def fail():
        raise RuntimeError("sensitive-credential-value")
    k.hook = fail
    with pytest.raises(BindingError, match="^custody-readback-unavailable$") as caught:
        k.signer.sign(b"preimage")
    assert "sensitive" not in str(caught.value)
    assert k.calls == []


def test_post_sign_revocation_refuses_without_emitting_result(k):
    def sign(message):
        k.access = replace(k.access, issuance_ref="issuance:revoked")
        return b"s" * 64
    k.signer.remote.sign = sign
    with pytest.raises(BindingError, match="^custody-deployment-mismatch$"):
        k.signer.sign(b"preimage")


def test_access_deadline_cannot_be_extended_during_use(k):
    calls = []
    def hook():
        calls.append(True)
        if len(calls) == 2:
            k.c.h.now += 25
            k.access = replace(k.access, issued_at=k.c.h.now, expires_at=k.c.h.now + 20)
    k.hook = hook
    with pytest.raises(BindingError, match="^custody-access-expired$"):
        k.signer.sign(b"preimage")
    assert len(k.calls) == 1  # An already-created signature is never claimed undone.


def test_clock_regression_inside_readback_refuses(k):
    k.hook = lambda: setattr(k.c.h, "now", k.c.h.now - 1)
    with pytest.raises(BindingError, match="^custody-clock-unavailable$"):
        k.signer.sign(b"preimage")
    assert k.calls == []


def test_clock_regression_across_runtime_preflight_refuses(k):
    # Regression after validate_config's final clock must also be detected.
    clocks = iter([k.c.h.now, k.c.h.now, k.c.h.now + 1, k.c.h.now])
    k.signer.runtime_trust = replace(k.c.trust, clock=lambda: next(clocks))
    with pytest.raises(BindingError, match="^custody-clock-unavailable$"):
        k.signer.sign(b"preimage")
    assert k.calls == []


def test_expiry_during_signing_does_not_emit_signature(k):
    def late(message):
        k.c.h.now += 25
        return b"s" * 64
    k.signer.remote.sign = late
    with pytest.raises(BindingError, match="^custody-access-expired$"):
        k.signer.sign(b"preimage")


def test_wrong_ca_approval_and_subject_refuse_before_client_construction(k):
    wrong_identity = replace(k.identity, trust_digest="sha256:" + "f" * 64)
    with pytest.raises(BindingError):
        k.make(identity=wrong_identity)
    with pytest.raises(BindingError, match="^custody-scope-mismatch$"):
        k.make(subject_ref="agent:other")
    assert k.calls == []


@pytest.mark.parametrize("value", [b"", b"x" * 8193, "preimage", None])
def test_invalid_signing_input_refuses_before_readback_or_signer(k, value):
    with pytest.raises(BindingError, match="^invalid-custody-message$"):
        k.signer.sign(value)
    assert k.calls == [] and k.deadlines == []


def test_signer_failure_and_bad_signature_are_safe(k):
    def fail(message):
        raise RuntimeError("private-value")
    k.signer.remote.sign = fail
    with pytest.raises(BindingError, match="^custody-service-unavailable$"):
        k.signer.sign(b"preimage")
    k.signer.remote.sign = lambda message: b"short"
    with pytest.raises(BindingError, match="^invalid-custody-signature$"):
        k.signer.sign(b"preimage")


def test_outer_proof_deadline_limits_added_custody_readback_before_sign(k):
    c, signed = k.c, []
    c.context = replace(c.context, expires_at=c.h.now + 2)
    c.services["custody"] = k.signer.service
    c.bridge = c.make()
    k.hook = lambda: setattr(c.h, "now", c.h.now + 3)
    def sign(message):
        signed.append(True)
        return c.h.sign(message)
    k.signer.remote.sign = sign
    with pytest.raises(BindingError):
        c.run()
    assert signed == [], "custody signed after the outer proof deadline"
    assert k.deadlines == [c.context.expires_at]


def test_custody_lease_deadline_survives_later_proof_io(k):
    c, signed = k.c, []
    k.access = replace(k.access, expires_at=c.h.now + 2)
    c.services["custody"] = k.signer.service
    c.bridge = c.make()
    def sign(message):
        signed.append(True)
        return c.h.sign(message)
    def policy_read():
        if signed:
            c.h.now += 3
    k.signer.remote.sign = sign
    c.records.hook = policy_read
    with pytest.raises(BindingError):
        c.run()
    assert signed == [True]


def _worker_probe(k, owner, endpoint, message, directory):
    config = directory / "worker-probe.json"
    private_write(config, encoded({
        "owner_code": str(owner), "endpoint": endpoint, "ca_file": str(k.ca),
        "certificate": str(k.worker[0]), "private_key": str(k.worker[1]),
        "subject_ref": k.c.h.binding.subject_ref, "key_ref": k.c.h.binding.key_ref,
        "now": k.c.h.now, "message": base64.b64encode(message).decode(),
    }))
    process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).with_name("custody_worker.py")), str(config)],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={"PATH": os.defpath, "LANG": "C.UTF-8"}, umask=0o077)
    try:
        output, errors = process.communicate(timeout=10)
        assert process.returncode == 0, "worker direct-sign probe failed"
        assert output == b'{"direct_sign_denied":true}'
    finally:
        _stop(process)


def _stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except Exception:
            process.kill()
            process.wait(timeout=5)
    for stream in (process.stdout, process.stderr):
        if stream:
            stream.close()


def _owning_run(k, directory, *, allow_worker_sign=False, fail_after_proof=False):
    owner = owner_source()
    from openwallet_runtime.custody import RemoteRegistry, RemoteSigner, TLSClient
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    from openwallet_runtime.reference_service import provision_key
    from openwallet_runtime.registry import BindingRegistry
    c, h = k.c, k.c.h
    public = provision_key(directory / "keys", h.binding.key_ref)
    h.binding = TrustedKeyBinding(**{**asdict(h.binding), "public_key": public})
    registry = BindingRegistry(directory / "registry")
    registry.register(h.binding, expected_revision=None)
    h.policy["binding"]["public_key_digest"] = byte_digest(public)
    h.policy["wallet"]["key_reference"]["public_key_multibase"] = multibase(public)
    h.reset_evidence()
    c.reselect_policy()
    ready = directory / "ready"
    # These are actual custody policies. Readback below derives granted scope
    # from them instead of unconditionally asserting a denied worker boolean.
    policies = {k.gate[2]: {"actions": ["sign"], "subjects": [h.binding.subject_ref]},
                k.worker[2]: {"actions": ["resolve", "sign"] if allow_worker_sign else ["resolve"],
                              "subjects": [h.binding.subject_ref]}}
    process, _ = launch("custody", {
        "owner_code": str(owner), "now": h.now, "registry_directory": str(directory / "registry"),
        "key_directory": str(directory / "keys"), "ca_file": str(k.ca),
        "certificate": str(k.server[0]), "private_key": str(k.server[1]),
        "ready": str(ready), "policies": policies,
    }, directory, wait=False)
    try:
        deadline = time.monotonic() + 10
        while not ready.exists():
            assert process.poll() is None, "custody exited"
            assert time.monotonic() < deadline, "custody readiness timeout"
            time.sleep(0.02)
        endpoint = "https://127.0.0.1:" + ready.read_text()
        k.material = replace(k.material, endpoint=endpoint)
        k.access = replace(k.access, config_digest=digest(c.config),
                           endpoint_digest=byte_digest(endpoint.encode()),
                           actions=tuple(policies[k.gate[2]]["actions"]))
        signer = k.make(tls_client=TLSClient, remote_signer=RemoteSigner)
        worker_client = TLSClient(endpoint, ca_file=k.ca, certificate=k.worker[0], private_key=k.worker[1])
        remote_registry = RemoteRegistry(worker_client)
        # Positive resolve proves a live authenticated service and current binding.
        assert remote_registry.resolve(h.binding.subject_ref, now=h.now) == h.binding
        messages = []
        remote_sign = signer.remote.sign
        def capture(message):
            messages.append(message)
            return remote_sign(message)
        signer.remote.sign = capture
        c.services["custody"] = signer.service
        c.services["registry"] = BoundService(ServiceIdentity(**c.config["services"]["registry"]), remote_registry)
        c.bridge = c.make(create_proof=create_proof)
        result = c.run()
        verified = verify_proof(result["proof"], expected_digest=h.challenge.digest, binding=h.binding, now=h.now)
        assert verified.subject_ref == h.binding.subject_ref
        assert result["human_approval"] is False
        assert len(messages) == 1
        # Submit an owning-generated valid canonical preimage. Require an explicit
        # service refusal, never count TLS/network/parse failure as denial.
        _worker_probe(k, owner, endpoint, messages[0], directory)
        with pytest.raises(BindingError):
            c.run()  # one-use reservation remains enforced
        assert len(messages) == 1
        if fail_after_proof:
            raise RuntimeError("injected-after-proof")
        return messages[0]
    finally:
        _stop(process)
        assert process.poll() is not None


@pytest.mark.parametrize("fail_after_proof", [False, True])
def test_owning_proof_worker_valid_preimage_denial_and_cleanup(k, tmp_path, fail_after_proof):
    with TemporaryDirectory(prefix="custody-g03-", dir=tmp_path) as folder:
        directory = Path(folder)
        if fail_after_proof:
            with pytest.raises(RuntimeError, match="^injected-after-proof$"):
                _owning_run(k, directory, fail_after_proof=True)
        else:
            _owning_run(k, directory)
    assert not directory.exists()


def test_excess_worker_permission_mutation_breaks_denial_probe(k, tmp_path):
    with TemporaryDirectory(prefix="custody-mutation-", dir=tmp_path) as folder:
        directory = Path(folder)
        with pytest.raises(AssertionError, match="worker direct-sign probe failed"):
            _owning_run(k, directory, allow_worker_sign=True)
    assert not directory.exists()


def test_custody_outage_does_not_pass_worker_denial_probe(k, tmp_path):
    owner = owner_source()
    with pytest.raises(AssertionError, match="worker direct-sign probe failed"):
        _worker_probe(k, owner, "https://127.0.0.1:1", b"unused-without-positive-resolve", tmp_path)
