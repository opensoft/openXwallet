"""Actual janitor/readback processes and generation-bound isolated resources."""
from dataclasses import asdict
import multiprocessing
import sqlite3
import time

import pytest

from workload_factory_binding.evidence import BindingError
from factory_binding.test_owner_integration import owner_source
from .composition_fixture import c
from .lifecycle_process_fixture import p
from .test_config import configuration


def assert_removed(p):
    record = p.audit.read_cleanup(p.plan.ref, deadline=p.clock.value + 10)
    assert record.lease_status == "closed"
    expected = {r.ref: r for r in p.plan.resources}
    for actual in record.resources:
        assert actual.present is (expected[actual.ref].retention != "run")
        if expected[actual.ref].kind == "credential":
            assert actual.revoked is True
    with pytest.raises(BindingError, match="^fixture-credential-denied$"):
        p.gate.request("credential", ref=p.plan.ref, deadline=p.clock.value + 10)


@pytest.mark.parametrize("outcome", ["success", "failure", "cancel"])
def test_real_owning_proof_cleanup_and_retained_state(p, outcome):
    owner_source()
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    c = p.c
    c.h.binding = TrustedKeyBinding(**asdict(c.h.binding))
    c.bridge = c.make(create_proof=create_proof, lifecycle=p.life)
    shared = (p.root / "shared").read_bytes()
    def operation():
        proof = c.run()
        if outcome == "failure":
            raise RuntimeError("injected after owning signature")
        if outcome == "cancel":
            raise KeyboardInterrupt()
        return proof
    if outcome == "success":
        result = p.life.run(operation)
        verified = verify_proof(result["proof"], expected_digest=c.h.challenge.digest,
                                binding=c.h.binding, now=c.h.now)
        assert verified.subject_ref == c.h.binding.subject_ref
        assert result["human_approval"] is False
    else:
        exception = BindingError if outcome == "failure" else KeyboardInterrupt
        with pytest.raises(exception):
            p.life.run(operation)
    assert_removed(p)
    assert (p.root / "shared").read_bytes() == shared
    with sqlite3.connect(c.h.ledger.path) as db:
        assert db.execute("SELECT count(*) FROM reservations").fetchone() == (1,)


def test_worker_cannot_forge_peer_finalize_or_access_credential(p):
    for method in ("read_lease", "finalize", "credential", "register", "sweep"):
        with pytest.raises(BindingError, match="^janitor-peer-denied$"):
            p.worker.request(method, ref=p.plan.ref, deadline=p.clock.value + 10,
                             peer={"principal_ref": p.plan.janitor.principal_ref,
                                   "credential_ref": p.plan.janitor.credential_ref})
    assert p.life.run(lambda: "ok") == "ok"
    assert_removed(p)


def test_success_acknowledgement_without_actual_file_removal_fails_independent_audit(p):
    p.admin.request("mode", mode="skip-file")
    with pytest.raises(BindingError, match="^lifecycle-cleanup-unverified$"):
        p.life.run(lambda: "must-not-return")
    assert (p.root / "temporary").exists()
    p.admin.request("mode", mode="normal")
    p.life.finalize("failure")
    assert_removed(p)


def test_independent_expiry_cleanup_survives_runner_hard_exit(p):
    # The runner has no finally opportunity. Janitor and audit processes survive it.
    context = multiprocessing.get_context("fork")
    parent, child = context.Pipe(duplex=False)
    def runner():
        p.gate.read_lease(p.plan.ref, deadline=p.clock.value + 10)
        child.send_bytes(b"ready")
        time.sleep(300)
    process = context.Process(target=runner)
    process.start()
    try:
        assert parent.poll(4)
        assert parent.recv_bytes() == b"ready"
        process.kill()
        process.join(timeout=4)
        assert not process.is_alive()
        p.c.h.now = p.plan.expires_at
        p.clock.value = p.plan.expires_at
        deadline = time.monotonic() + 5
        while True:
            record = p.audit.read_cleanup(p.plan.ref, deadline=p.clock.value + 10)
            if record.lease_status == "closed" and all(not r.present for r in record.resources[:3]):
                break
            assert time.monotonic() < deadline, "independent janitor did not clean expired run"
            time.sleep(0.03)
        assert_removed(p)
        p.life.finalize("cancel")
        assert all(proc.is_alive() for proc in p.processes)
    finally:
        if process.is_alive():
            process.kill()
            process.join(timeout=3)
        process.close()
        parent.close()
        child.close()


def test_missing_independent_reader_cannot_qualify_cleanup(p):
    reader = p.processes[1]
    p.audit.request("stop")
    reader.join(timeout=3)
    assert not reader.is_alive()
    with pytest.raises(BindingError, match="^lifecycle-cleanup-unverified$"):
        p.life.run(lambda: "must-not-return")
    assert not (p.root / "credential.key").exists()
    assert (p.root / "shared").exists()


def test_actual_replacement_generation_is_preserved_and_fails_cleanup(p):
    path = p.root / "temporary"
    replacement = p.root / "replacement"
    replacement.write_bytes(b"different resource generation")
    replacement.chmod(0o600)
    replacement.replace(path)
    with pytest.raises(BindingError, match="^lifecycle-cleanup-unverified$"):
        p.life.finalize("failure")
    assert path.read_bytes() == b"different resource generation"
    assert (p.root / "shared").exists()
