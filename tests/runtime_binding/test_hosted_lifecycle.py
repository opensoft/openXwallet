"""T012S actual retained lifecycle journal and isolated cleanup controls."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import pytest
from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.lifecycle_store import LifecycleStore


def use(now=1000):
    return Decision(clock=lambda: now, monotonic=lambda: 0.)


def journal(tmp_path, kind="primary"):
    root, witness = tmp_path / "journal", tmp_path / "witness"
    identity = LifecycleStore.initialize(root, witness, kind=kind)
    return LifecycleStore(root, witness, identity=identity, kind=kind), identity


def test_missing_lifecycle_registration_store_is_never_created_on_open(tmp_path):
    with pytest.raises(BindingError):
        LifecycleStore(tmp_path / "missing", tmp_path / "missing-witness", identity=(), kind="primary")
    assert not (tmp_path / "missing").exists()
    assert not (tmp_path / "missing-witness").exists()


def test_initialized_lifecycle_journal_and_independent_witness_survive_reconstruction(tmp_path):
    store, identity = journal(tmp_path)
    store.record("stage-intake", {"ref": "launch:one"}, decision=use())
    reopened = LifecycleStore(store.directory, store.witness, identity=identity, kind="primary")
    events = reopened.events(decision=use())
    assert [(e["kind"], e["data"]) for e in events if e["kind"] != "clock"] == [("stage-intake", {"ref": "launch:one"})]
    with pytest.raises(BindingError):
        LifecycleStore.initialize(store.directory, store.witness, kind="primary")
    assert reopened.events(decision=use()) == events


@pytest.mark.parametrize("change", ["database", "witness", "corrupt", "kind", "rollback", "witness-extra", "permissions"])
def test_lifecycle_store_loss_replacement_corruption_or_rollback_refuses(tmp_path, change):
    store, identity = journal(tmp_path)
    store.record("stage-intake", {"ref": "launch:one"}, decision=use())
    if change == "database":
        original = store.directory / "lifecycle.sqlite"
        replacement = store.directory / "replacement.sqlite"
        replacement.write_bytes(original.read_bytes())
        replacement.chmod(0o600)
        assert replacement.stat().st_ino != original.stat().st_ino
        replacement.replace(original)
    elif change == "witness":
        next(store.witness.glob("00000001.witness")).unlink()
    elif change == "corrupt":
        with sqlite3.connect(store.directory / "lifecycle.sqlite") as db:
            db.execute("UPDATE events SET body=? WHERE kind='stage-intake'", (b'{"ref":"launch:other"}',))
    elif change == "kind":
        with pytest.raises(BindingError):
            LifecycleStore(store.directory, store.witness, identity=identity, kind="audit")
        return
    elif change == "rollback":
        with sqlite3.connect(store.directory / "lifecycle.sqlite") as db:
            db.execute("DELETE FROM events WHERE kind='stage-intake'")
    elif change == "witness-extra":
        (store.witness / "unexpected").write_text("not an admitted journal event")
    else:
        (store.directory / "lifecycle.sqlite").chmod(0o644)
    events_decision = use()
    with pytest.raises(BindingError):
        store.events(decision=events_decision)



def test_completed_sqlite_delete_journal_overlap_preserves_exact_committed_events(tmp_path, monkeypatch):
    import threading
    from workload_factory_binding_runtime.hosted import lifecycle_store as module
    store, _ = journal(tmp_path)
    ready, release = threading.Event(), threading.Event()
    errors, observed = [], []
    main = threading.current_thread()
    original = module._private
    def writer():
        try:
            def mutation(events, append):
                append("stage-intake", {"ref": "launch:overlap"})
                ready.set()
                if not release.wait(2):
                    raise RuntimeError("writer synchronization timed out")
            store.mutate(mutation, decision=use())
        except BaseException as error:
            errors.append(error)
    thread = threading.Thread(target=writer)
    def concurrent_private(path, directory=False):
        if (path == store.directory / "lifecycle.sqlite-journal"
                and threading.current_thread() is main and not observed):
            assert path.exists()
            observed.append(path.name)
            release.set()
            thread.join(2)
            assert not thread.is_alive()
            assert not errors
            assert not path.exists()
        return original(path, directory)
    thread.start()
    try:
        assert ready.wait(2)
        monkeypatch.setattr(module, "_private", concurrent_private)
        decision = use()
        deadline = decision.deadline
        events = store.events(decision=decision)
        assert decision.deadline == deadline
        assert [(e["kind"], e["data"]) for e in events if e["kind"] != "clock"] == [
            ("stage-intake", {"ref": "launch:overlap"})]
        assert observed == ["lifecycle.sqlite-journal"]
    finally:
        release.set()
        thread.join(2)
    assert not thread.is_alive()
    assert not errors
    assert store.events(decision=use()) == events


@pytest.mark.parametrize("artifact", ["journal-mode", "journal-symlink", "wal", "shm"])
def test_optional_sqlite_artifact_disappearance_does_not_admit_invalid_files(tmp_path, artifact):
    store, _ = journal(tmp_path)
    suffix = "-journal" if artifact.startswith("journal-") else "-" + artifact
    path = store.directory / ("lifecycle.sqlite" + suffix)
    if artifact == "journal-symlink":
        path.symlink_to(store.witness / "00000000.witness")
    else:
        path.write_bytes(b"untrusted optional SQLite artifact")
        path.chmod(0o644 if artifact == "journal-mode" else 0o600)
    decision = use()
    with pytest.raises(BindingError):
        store.events(decision=decision)


def test_lifecycle_journal_has_one_concurrent_registration_winner(tmp_path):
    store, _ = journal(tmp_path)
    def register(_):
        def update(events, append):
            if any(e["kind"] == "stage-intake" for e in events):
                return False
            append("stage-intake", {"ref": "launch:one"})
            return True
        return store.mutate(update, decision=use())
    with ThreadPoolExecutor(max_workers=6) as pool:
        assert sum(pool.map(register, range(6))) == 1
    assert sum(e["kind"] == "stage-intake" for e in store.events(decision=use())) == 1


def test_lifecycle_highwater_and_original_decision_cannot_regress_or_renew(tmp_path):
    store, _ = journal(tmp_path)
    store.record("stage-intake", {"ref": "launch:one"}, decision=use(1002))
    events_decision = use(1001)
    with pytest.raises(BindingError):
        store.events(decision=events_decision)
    now = [1002]
    decision = Decision(clock=lambda: now[0], monotonic=lambda: 0.)
    now[0] = 1012
    with pytest.raises(BindingError):
        store.events(decision=decision)
    assert sum(e["kind"] == "stage-intake" for e in store.events(decision=use(1012))) == 1


@pytest.mark.parametrize("failed_business", [False, True])
def test_lifecycle_commit_persists_latest_validated_clock_even_after_business_rollback(tmp_path, failed_business):
    store, _ = journal(tmp_path)
    clock = [1000]
    decision = Decision(clock=lambda: clock[0], monotonic=lambda: 0.)
    original_deadline = decision.deadline
    def operation(events, append):
        append("stage-intake", {"ref": "launch:clock-crossing"})
        clock[0] = 1009
        decision.now()
        if failed_business:
            raise BindingError("fixture-business-refused")
    if failed_business:
        with pytest.raises(BindingError):
            store.mutate(operation, decision=decision)
    else:
        store.mutate(operation, decision=decision)
    assert decision.deadline == original_deadline
    regressed = use(1001)
    with pytest.raises(BindingError):
        store.events(decision=regressed)
    events = store.events(decision=use(1009))
    assert events[-1]["kind"] == "clock"
    assert events[-1]["at"] == 1009
    expected = [] if failed_business else [{"ref": "launch:clock-crossing"}]
    assert [e["data"] for e in events if e["kind"] == "stage-intake"] == expected
    reopened = LifecycleStore(store.directory, store.witness, identity=store.identity, kind="primary")
    assert reopened.events(decision=use(1009)) == events


@pytest.mark.parametrize("append_business", [False, True])
def test_lifecycle_capacity_reserves_clock_and_exhausted_store_cannot_admit_regression(tmp_path, monkeypatch, append_business):
    from workload_factory_binding_runtime.hosted import lifecycle_store as module
    monkeypatch.setattr(module, "MAX_EVENTS", 6)
    store, _ = journal(tmp_path)
    for number in range(4):
        store.record("stage-intake", {"seed": number}, decision=use())
    clock = [1000]
    decision = Decision(clock=lambda: clock[0], monotonic=lambda: 0.)
    original_deadline = decision.deadline
    def operation(events, append):
        clock[0] = 1009
        decision.now()
        if append_business:
            append("stage-intake", {"uncommitted": True})
        return "read-only"
    if append_business:
        with pytest.raises(BindingError):
            store.mutate(operation, decision=decision)
    else:
        assert store.mutate(operation, decision=decision) == "read-only"
    assert decision.deadline == original_deadline
    for value in (1001, 1009):
        current = use(value)
        with pytest.raises(BindingError):
            store.events(decision=current)
    with sqlite3.connect(store.directory / "lifecycle.sqlite") as db:
        assert db.execute("SELECT highwater FROM metadata").fetchone() == (1009,)
        assert db.execute("SELECT count(*) FROM events").fetchone() == (6,)
        assert db.execute("SELECT kind,observed_at FROM events ORDER BY sequence DESC LIMIT 1").fetchone() == ("clock", 1009)
        rows = [json.loads(raw) for raw, in db.execute("SELECT body FROM events WHERE kind='stage-intake'")]
    assert rows == [{"seed": n} for n in range(4)]
    assert len(list(store.witness.iterdir())) == 7


from .launch_fixture import stage, v, g, rb, configuration, c, l, w
from .test_hosted_issuance import provider
from .hosted_fixture import child_generations
from .hosted_lifecycle_fixture import lh
from workload_factory_binding_runtime.hosted.readback import ReadBudget
from workload_factory_binding_runtime.hosted.lifecycle import process_instance
from workload_factory_binding_runtime.hosted.lifecycle_service import probe_worker_denial


def test_independent_durable_registration_precedes_one_actual_sandboxed_worker(lh):
    value = lh.launch(full=True)
    state = lh.life.state(decision=lh.use())
    assert value.state == "running"
    assert state["registration"]
    assert state["generation"]
    assert len({p.pid for p in lh.processes} | {__import__("os").getpid()}) == 4
    assert ReadBudget(lh.stage.seen[-1]).count("private") == 16
    assert lh.life.stage_lease(lh.stage.scope["cleanup_ref"], decision=lh.use())["state"] == "acknowledged"
    assert lh.stage.agent.store.read(lh.stage.scope["launch_ref"], decision=lh.use())["state"] == "running"


def test_actual_full_finalization_and_immutable_takeover_have_no_cleanup_gap(lh):
    lh.launch()
    finalized, plan = lh.finalize()
    assert ReadBudget(lh.stage.seen[-1]).count("private") == 12
    lh.primary().call("prepare", decision=lh.use())
    assert lh.life.state(decision=lh.use())["released"] is False
    call_target = lh.primary()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("lease", plan_ref=plan.ref, decision=call_decision)
    lh.audit().call("ack-final", decision=lh.use())
    assert lh.life.state(decision=lh.use())["released"] is False
    lh.primary().call("release", decision=lh.use())
    state = lh.life.state(decision=lh.use())
    assert state["released"] is True
    assert state["final"]["binding"]["config_digest"] == finalized.binding.config_digest
    assert state["final"]["plan"]["expires_at"] <= state["registration"]["expires_at"]


def test_final_run_lifecycle_independently_verifies_actual_cleanup_and_preservation(lh):
    lh.launch()
    lh.finalize()
    lh.takeover()
    worker = lh.life.state(decision=lh.use())["generation"]["generation"]
    shared_before = (lh.shared.stat().st_dev, lh.shared.stat().st_ino, lh.shared.read_bytes())
    retained = lh.stage.v.h.ledger.path
    retained_before = (retained.stat().st_dev, retained.stat().st_ino)
    runtime = lh.runtime()
    assert runtime.run(lambda: {"inert": True}) == {"inert": True}
    assert runtime.cleanup_verification is not None
    assert not (Path("/proc") / str(worker["pid"])).exists()
    actual_shared = (lh.shared.stat().st_dev, lh.shared.stat().st_ino, lh.shared.read_bytes())
    assert actual_shared == shared_before
    actual_retained = (retained.stat().st_dev, retained.stat().st_ino)
    assert actual_retained == retained_before
    assert not lh.provider.active[lh.token.credential]
    assert not lh.temporary.exists()


def test_available_lifecycle_worker_denial_has_allowed_controller_positive(lh):
    lh.launch()
    assert lh.primary().call("status", decision=lh.use())["owner"] == "stage"
    assert probe_worker_denial(lh.primary("worker"), "status", decision=lh.use())["outcome"] == "denied"


import multiprocessing
import os
import secrets
import time
from dataclasses import replace, asdict
from workload_factory_binding.evidence import canonical, digest
from workload_factory_binding_runtime.hosted.lifecycle_service import PRIMARY, AUDIT, PROFILE
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
from workload_factory_binding_runtime.hosted.readback import PROFILE as OBSERVATION_PROFILE


def test_stage_registration_acknowledgement_requires_actual_scheduler_process(lh):
    lh.processes[0].kill()
    lh.processes[0].join(timeout=3)
    read_decision = lh.use()
    with pytest.raises(BindingError):
        lh.stage.protected.read(lh.stage.v.context, lh.stage.v.token, decision=read_decision)
    state = lh.life.state(decision=lh.use())
    assert state["registration"] is not None
    assert state["generation"] is None
    assert not lh.stage.agent.children
    assert not state["released"]


@pytest.mark.parametrize("where", ["primary-store", "audit-store"])
def test_missing_registration_or_independent_ack_store_never_starts_a_worker(lh, where):
    store = lh.stores["primary" if where == "primary-store" else "audit"]
    replacement = store.directory.with_name(store.directory.name + "-held")
    store.directory.rename(replacement)
    try:
        read_decision = lh.use()
        with pytest.raises(BindingError):
            lh.stage.protected.read(lh.stage.v.context, lh.stage.v.token, decision=read_decision)
        assert not lh.stage.agent.children
        assert not store.directory.exists()
    finally:
        replacement.rename(store.directory)


@pytest.mark.parametrize("reply", ["register", "ack-stage"])
def test_lost_registration_or_ack_reply_retains_stage_without_mutation_retry(lh, monkeypatch, reply):
    capability = lh.stage.controller.register_cleanup.primary if reply == "register" else lh.stage.controller.register_cleanup.audit
    original = capability.call
    calls = []
    def lose(operation, **kwargs):
        value = original(operation, **kwargs)
        calls.append(operation)
        if operation == reply:
            raise BindingError("fixture-reply-lost")
        return value
    monkeypatch.setattr(capability, "call", lose)
    read_decision = lh.use()
    with pytest.raises(BindingError):
        lh.stage.protected.read(lh.stage.v.context, lh.stage.v.token, decision=read_decision)
    assert not lh.stage.agent.children
    assert lh.stage.protected.read(lh.stage.v.context, lh.stage.v.token, decision=lh.use()).state == "registered"
    assert calls.count(reply) == 1
    state = lh.life.state(decision=lh.use())
    assert state["registration"]
    assert state["generation"] is None
    assert not state["released"]


@pytest.mark.parametrize("operation", sorted(PRIMARY))
def test_each_private_lifecycle_control_denies_valid_worker_and_has_authorized_positive(lh, operation):
    if operation == "register":
        unit = lh.stage.host.register(lh.stage.scope["launch_ref"], decision=lh.use())["unit"]
        extra = {"unit_digest": digest(unit)}
    else:
        lh.launch()
        extra = {}
        if operation in ("prepare", "release", "lease"):
            lh.finalize()
        if operation in ("release", "lease"):
            lh.primary().call("prepare", decision=lh.use())
            lh.audit().call("ack-final", decision=lh.use())
        if operation == "lease":
            lh.primary().call("release", decision=lh.use())
            extra = {"plan_ref": lh.plan.ref}
        if operation == "cleanup":
            extra = {"outcome": "failure"}
    assert probe_worker_denial(lh.primary("worker"), operation, decision=lh.use(), **extra)["outcome"] == "denied"
    assert lh.primary().call(operation, decision=lh.use(), **extra)


@pytest.mark.parametrize("operation", ["ack-stage", "ack-final", "cleanup-audit"])
def test_independent_audit_controls_deny_worker_and_have_actual_positive(lh, operation):
    if operation == "ack-stage":
        unit = lh.stage.host.register(lh.stage.scope["launch_ref"], decision=lh.use())["unit"]
        lh.primary().call("register", unit_digest=digest(unit), decision=lh.use())
    else:
        lh.launch()
        if operation == "ack-final":
            lh.finalize()
            lh.primary().call("prepare", decision=lh.use())
        else:
            lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    extra = {"attempt_ref": "cleanup-attempt:positive"} if operation == "cleanup-audit" else {}
    assert probe_worker_denial(lh.audit("worker"), operation, decision=lh.use(), **extra)["outcome"] == "denied"
    assert lh.audit().call(operation, decision=lh.use(), **extra)


def test_independent_lease_observation_explicitly_denies_worker_with_available_positive(lh):
    lh.register()
    assert lh.life.stage_lease(lh.stage.scope["cleanup_ref"], decision=lh.use())["state"] == "acknowledged"
    selected = lh.stage.agent.authority.lease
    transport = PrivateHttps(ca_file=str(lh.root / "audit-pki/ca.pem"),
        certificate=str(lh.root / "audit-pki/worker/cert.pem"), private_key=str(lh.root / "audit-pki/worker/key.pem"),
        observation_origin=selected.origin, server_certificate_digest=selected.transport.server_certificate_digest)
    response = transport.exchange("POST", selected.origin + "/readback", headers={"Content-Type": "application/json"},
        body=canonical({"profile": OBSERVATION_PROFILE, "operation": "stage-lease",
                        "reference": lh.stage.scope["cleanup_ref"], "nonce": secrets.token_hex(32)}), decision=lh.use())
    assert response.status == 403
    assert json.loads(response.body) == {"error": "hosted-lifecycle-denied"}


@pytest.mark.parametrize("lh", ["excess-worker"], indirect=True)
def test_excess_lifecycle_permission_breaks_worker_denial_positive(lh):
    lh.register()
    assert lh.primary("worker").call("status", decision=lh.use())["owner"] == "stage"
    probe_worker_denial_argument_1 = lh.primary("worker")
    probe_worker_denial_decision = lh.use()
    with pytest.raises(BindingError):
        probe_worker_denial(probe_worker_denial_argument_1, "status", decision=probe_worker_denial_decision)


def test_lifecycle_service_outage_does_not_count_as_worker_denial(lh):
    lh.register()
    assert lh.primary().call("status", decision=lh.use())
    lh.processes[1].kill()
    lh.processes[1].join(timeout=3)
    probe_worker_denial_argument_1 = lh.primary("worker")
    probe_worker_denial_decision = lh.use()
    with pytest.raises(BindingError):
        probe_worker_denial(probe_worker_denial_argument_1, "status", decision=probe_worker_denial_decision)


@pytest.mark.parametrize("field", ["path", "url", "principal_ref", "resources", "final_plan", "unit_digest", "worker_ref", "accepted_commit"])
def test_lifecycle_request_cannot_select_control_targets_or_authority(lh, field):
    lh.register()
    client = lh.primary()
    body = {"profile": PROFILE, "nonce": secrets.token_hex(32), "deadline": lh.use().deadline,
        "arguments": {"launch_ref": lh.stage.scope["launch_ref"], "scope_digest": digest(lh.stage.scope), field: "fixture:unapproved"}}
    response = client.transport.exchange("POST", client.origin + "/lifecycle/status", headers={"Content-Type": "application/json"},
        body=canonical(body), decision=lh.use())
    assert response.status == 400
    assert json.loads(response.body) == {"error": "hosted-lifecycle-refused"}
    assert client.call("status", decision=lh.use())["owner"] == "stage"
    assert not lh.life.state(decision=lh.use())["actions"]


@pytest.mark.parametrize("change", ["configuration", "policy", "authority", "run", "generation", "retention", "lease", "cleanup-ref"])
def test_independent_final_source_or_scope_mutation_refuses_before_stage_release(lh, change):
    lh.launch()
    lh.finalize()
    raw = json.loads(lh.final_path.read_bytes())
    if change == "configuration":
        raw["configuration"]["revision"] += 1
        raw["binding"]["config_digest"] = digest(raw["configuration"])
        raw["plan"]["scope"]["config_digest"] = raw["binding"]["config_digest"]
    elif change == "policy":
        raw["policy"]["revision"] += 1
        raw["binding"]["policy_digest"] = digest(raw["policy"])
        raw["configuration"]["authority"]["policy_digest"] = raw["binding"]["policy_digest"]
        raw["binding"]["config_digest"] = digest(raw["configuration"])
        raw["plan"]["scope"]["config_digest"] = raw["binding"]["config_digest"]
    elif change == "authority": raw["binding"]["principal_ref"] = "principal:worker"
    elif change == "run": raw["binding"]["run_id"] = "999"
    elif change == "generation": raw["binding"]["generation_digest"] = "sha256:" + "f" * 64
    elif change == "retention": next(r for r in raw["plan"]["resources"] if r["ref"] == "resource:shared")["retention"] = "run"
    elif change == "lease": raw["plan"]["expires_at"] += 1
    else: raw["plan"]["scope"]["cleanup_ref"] = "cleanup:other"
    lh.final_path.write_bytes(canonical(raw))
    call_target = lh.primary()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("prepare", decision=call_decision)
    state = lh.life.state(decision=lh.use())
    assert not state["released"]
    assert state["final"] is None
    assert state["registration"]


def test_final_takeover_requires_actual_independent_ack_and_preserves_generation(lh):
    lh.launch()
    lh.finalize()
    before = lh.life.state(decision=lh.use())["generation"]
    lh.primary().call("prepare", decision=lh.use())
    call_target = lh.primary()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("release", decision=call_decision)
    lh.audit().call("ack-final", decision=lh.use())
    lh.primary().call("release", decision=lh.use())
    state = lh.life.state(decision=lh.use())
    assert state["generation"] == before
    assert state["released"]
    call_target_2 = lh.primary()
    call_decision_2 = lh.use()
    with pytest.raises(BindingError):
        call_target_2.call("release", decision=call_decision_2)
    call_target_3 = lh.primary()
    call_decision_3 = lh.use()
    with pytest.raises(BindingError):
        call_target_3.call("prepare", decision=call_decision_3)
    stage_lease_decision = lh.use()
    with pytest.raises(BindingError):
        lh.life.stage_lease(lh.stage.scope["cleanup_ref"], decision=stage_lease_decision)


@pytest.mark.parametrize("boundary", ["before-prepare", "after-prepare", "after-ack", "after-release"])
def test_independent_scheduler_cleans_after_actual_runner_death_at_takeover_boundary(lh, boundary):
    lh.launch()
    lh.finalize()
    def runner():
        if boundary != "before-prepare":
            lh.primary().call("prepare", decision=lh.use())
        if boundary in ("after-ack", "after-release"):
            lh.audit().call("ack-final", decision=lh.use())
        if boundary == "after-release":
            lh.primary().call("release", decision=lh.use())
        os._exit(23)
    process = multiprocessing.get_context("fork").Process(target=runner)
    process.start()
    instance = process_instance(process.pid)[0]
    (lh.root / "runner-generation.json").write_bytes(canonical({"pid": process.pid, "instance_ref": instance}))
    process.join(timeout=15)
    assert process.exitcode == 23
    (lh.root / "accepted-final.json").unlink()
    original = lh.life.state(decision=lh.use())
    lh.advance(original["registration"]["expires_at"] + 1)
    end = time.monotonic() + 8
    while time.monotonic() < end:
        try:
            result = lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:runner-death", decision=lh.use())
            break
        except BindingError:
            time.sleep(.05)
    else:
        pytest.fail("independent registered expiry cleanup was not observed")
    assert result["kind"] == ("final" if boundary == "after-release" else "stage")
    assert lh.shared.exists()
    assert lh.stage.v.h.ledger.path.exists()
    assert not lh.provider.active[lh.token.credential]
    assert sum(e["kind"] == "cleanup-request" for e in lh.stores["scheduler"].events(decision=lh.use())) == 1


@pytest.mark.parametrize("boundary", ["before-ack", "before-release"])
def test_dead_scheduler_never_receives_released_cleanup_responsibility(lh, boundary):
    lh.launch()
    lh.finalize()
    lh.primary().call("prepare", decision=lh.use())
    if boundary == "before-release":
        lh.audit().call("ack-final", decision=lh.use())
    lh.processes[0].kill()
    lh.processes[0].join(timeout=3)
    if boundary == "before-ack":
        finalizer = lh.audit()
        final_action = "ack-final"
    else:
        finalizer = lh.primary()
        final_action = "release"
    final_decision = lh.use()
    with pytest.raises(BindingError):
        finalizer.call(final_action, decision=final_decision)
    assert not lh.life.state(decision=lh.use())["released"]


@pytest.mark.parametrize("change", ["lease-expired", "ack-expired", "clock-regressed"])
def test_expired_or_regressed_takeover_cannot_release_original_stage(lh, change):
    original_time = lh.clock.value
    lh.launch()
    lh.finalize()
    lh.primary().call("prepare", decision=lh.use())
    if change == "ack-expired":
        ack = lh.audit().call("ack-final", decision=lh.use())
        lh.advance(ack["expires_at"])
    elif change == "lease-expired":
        lh.advance(lh.plan.expires_at)
    else:
        lh.advance(lh.clock.value - 1)
    call_target = lh.primary()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("release", decision=call_decision)
    if change == "clock-regressed":
        lh.advance(original_time)
    assert not lh.life.state(decision=lh.use())["released"]


def test_concurrent_takeover_release_and_cleanup_retain_one_actual_owner(lh):
    lh.launch()
    lh.finalize()
    lh.primary().call("prepare", decision=lh.use())
    lh.audit().call("ack-final", decision=lh.use())
    def act(operation):
        try:
            extra = {"outcome": "failure"} if operation == "cleanup" else {}
            return lh.primary().call(operation, decision=lh.use(), **extra)
        except BindingError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(act, ["release", "cleanup"]))
    assert any(outcomes)
    state = lh.life.state(decision=lh.use())
    assert state["closed"]
    audit = lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:concurrent-owner", decision=lh.use())
    assert audit["kind"] == ("final" if state["released"] else "stage")
    assert {a["owner"] for a in state["actions"].values()} == {"final" if state["released"] else "stage"}
    assert sum(method == "DELETE" and path == "/installation/token" for method, path in lh.provider.calls) == 1


def test_concurrent_stage_and_final_cleanup_cannot_repeat_any_destructive_generation(lh):
    lh.launch()
    lh.finalize()
    lh.takeover()
    def cleanup(_):
        try:
            return lh.primary().call("cleanup", outcome="cancel", decision=lh.use())
        except BindingError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(cleanup, range(2)))
    state = lh.life.state(decision=lh.use())
    run_resources = [r for r in lh.plan.resources if r.retention == "run"]
    assert len(state["actions"]) == len(run_resources)
    assert len({a["key"] for a in state["actions"].values()}) == len(run_resources)
    assert sum(method == "DELETE" and path == "/installation/token" for method, path in lh.provider.calls) == 1
    assert lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:concurrent-actions", decision=lh.use())["kind"] == "final"


@pytest.mark.parametrize("resource", ["run-file", "retained-file", "shared-file"])
def test_changed_file_generation_is_preserved_and_never_counted_as_cleanup(lh, resource):
    lh.launch()
    target = lh.temporary if resource == "run-file" else lh.stage.v.h.ledger.path if resource == "retained-file" else lh.shared
    replacement = target.with_name(target.name + ".replacement")
    replacement.write_bytes(b"independent newer generation")
    replacement.chmod(0o600)
    assert replacement.stat().st_ino != target.stat().st_ino
    replacement.replace(target)
    expected = (target.stat().st_dev, target.stat().st_ino, target.read_bytes())
    try:
        lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    except BindingError:
        pass
    call_target = lh.audit()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("cleanup-audit", attempt_ref="cleanup-attempt:changed-file", decision=call_decision)
    actual_target = (target.stat().st_dev, target.stat().st_ino, target.read_bytes())
    assert actual_target == expected
    assert lh.life.state(decision=lh.use())["registration"] is not None


def test_retained_lifecycle_generation_survives_host_journal_loss_without_rebinding(lh):
    lh.launch()
    # Independent journal loss after actual launch is not substituted with a
    # candidate PID or a new launch reference. Both retained records remain.
    with sqlite3.connect(lh.stage.agent.store.directory / "staging.sqlite") as db:
        db.execute("UPDATE stages SET generation=NULL")
    # The previously bound lifecycle generation stays immutable and supports
    # exact cleanup; this local journal loss never overwrites that observation.
    before = lh.life.state(decision=lh.use())["generation"]
    assert lh.primary().call("generation", decision=lh.use()) == before
    lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    assert lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:retained-generation", decision=lh.use())["kind"] == "stage"
    assert lh.life.state(decision=lh.use())["generation"] == before


@pytest.mark.parametrize("still_active", [False, True])
def test_lost_retirement_result_is_read_only_reconciled_without_second_delete(lh, still_active):
    lh.launch()
    lh.provider.changes["retirement-outage"] = True
    lh.provider.changes["still-active"] = still_active
    call_target = lh.primary()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("cleanup", outcome="failure", decision=call_decision)
    deletes = sum(method == "DELETE" and path == "/installation/token" for method, path in lh.provider.calls)
    assert deletes == 1
    try:
        lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    except BindingError:
        assert still_active
    assert sum(method == "DELETE" and path == "/installation/token" for method, path in lh.provider.calls) == 1
    if still_active:
        call_target_2 = lh.audit()
        call_decision_2 = lh.use()
        with pytest.raises(BindingError):
            call_target_2.call("cleanup-audit", attempt_ref="cleanup-attempt:retirement-unknown", decision=call_decision_2)
    else:
        assert lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:retired", decision=lh.use())["kind"] == "stage"


@pytest.mark.parametrize("change", ["attempt", "scope", "missing", "generation", "stale", "payload"])
def test_stale_or_substituted_independent_cleanup_record_never_returns_success(lh, monkeypatch, change):
    lh.launch()
    lh.finalize()
    lh.takeover()
    runtime = lh.runtime()
    transport = runtime.readback.target.audit.transport
    original = transport.exchange
    def altered(*args, **kwargs):
        response = original(*args, **kwargs)
        value = json.loads(response.body)
        if response.status == 200:
            record = value["facts"]["record"]
            if change == "attempt": record["attempt_ref"] = "cleanup-attempt:old"
            elif change == "scope": record["scope"]["run_id"] = "999"
            elif change == "missing": record["resources"].pop()
            elif change == "generation": record["resources"][0]["instance_ref"] = "file:999:999"
            elif change == "stale": record["valid_until"] = lh.clock.value
            else: record["private_exception"] = "fixture-private-canary"
            return replace(response, body=canonical(value))
        return response
    monkeypatch.setattr(transport, "exchange", altered)
    with pytest.raises(BindingError) as caught:
        runtime.run(lambda: "inert-complete")
    assert runtime.cleanup_verification is None
    assert "fixture-private-canary" not in str(caught.value)
    assert not lh.provider.active[lh.token.credential]


def test_lost_cleanup_response_cannot_be_replayed_or_reported_as_verified(lh, monkeypatch):
    lh.launch()
    lh.finalize()
    lh.takeover()
    runtime = lh.runtime()
    primary = runtime.janitor.target.primary
    original = primary.call
    calls = []
    errors = []
    def lost(operation, **kwargs):
        try:
            result = original(operation, **kwargs)
        except BindingError as error:
            errors.append((operation, str(error)))
            raise
        if operation == "cleanup":
            calls.append(operation)
            raise BindingError("fixture-lost-cleanup-reply")
        return result
    monkeypatch.setattr(primary, "call", lost)
    with pytest.raises(BindingError, match="lifecycle-cleanup-unverified"):
        runtime.run(lambda: "inert-complete")
    assert calls == ["cleanup"], errors
    assert runtime.cleanup_verification is None, errors
    assert lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:independent-reconciliation", decision=lh.use())["kind"] == "final"
    assert sum(method == "DELETE" and path == "/installation/token" for method, path in lh.provider.calls) == 1


@pytest.mark.parametrize("capability", ["external-watchdog", "control-host-loss", "infrastructure-retirement"])
def test_unsupported_external_failure_domain_or_conditional_infrastructure_is_not_qualified(lh, capability):
    with pytest.raises(BindingError, match="infrastructure-unsupported"):
        lh.life.require_infrastructure(capability)
    assert not lh.stage.agent.children


def test_actual_unpersisted_worker_generation_retains_owner_and_refuses_false_cleanup(lh):
    lh.launch(bind=False)
    with sqlite3.connect(lh.stage.agent.store.directory / "staging.sqlite") as db:
        db.execute("UPDATE stages SET state='start-consumed',generation=NULL")
    call_target = lh.primary()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("cleanup", outcome="failure", decision=call_decision)
    call_target_2 = lh.audit()
    call_decision_2 = lh.use()
    with pytest.raises(BindingError):
        call_target_2.call("cleanup-audit", attempt_ref="cleanup-attempt:unpersisted", decision=call_decision_2)
    state = lh.life.state(decision=lh.use())
    assert state["registration"] is not None
    assert state["generation"] is None
    assert state["closed"]
    assert not state["released"]
    assert not state["actions"]
    assert len(lh.stage.agent.children) == 1
    assert sum(e["kind"] == "registration" for e in lh.stores["primary"].events(decision=lh.use())) == 1


@pytest.mark.parametrize("target", ["lifecycle", "resources"])
def test_different_pid_namespace_never_interprets_an_owned_process_as_absent(lh, target):
    lh.launch()
    state = lh.life.state(decision=lh.use())
    resource = lh.life.resources_for(state)[-1]
    selected = lh.life if target == "lifecycle" else lh.life.resources
    attribute = "host_pid_namespace" if target == "lifecycle" else "pid_namespace"
    before = getattr(selected, attribute)
    try:
        setattr(selected, attribute, (before[0], before[1] + 1))
        if target == "lifecycle":
            state_decision = lh.use()
            with pytest.raises(BindingError):
                lh.life.state(decision=state_decision)
        else:
            observe_decision = lh.use()
            with pytest.raises(BindingError):
                lh.life.resources.observe(resource, decision=observe_decision)
    finally:
        setattr(selected, attribute, before)
    assert not lh.life.state(decision=lh.use())["actions"]
    assert len(lh.stage.agent.children) == 1


def test_dead_acknowledged_scheduler_refuses_start_before_any_child_creation(lh):
    unit = lh.register()
    decision = lh.use()
    assert lh.stage.agent.authority.acknowledged(lh.stage.scope, unit, decision=decision)["state"] == "acknowledged"
    lh.processes[0].kill()
    lh.processes[0].join(timeout=3)
    with pytest.raises(BindingError):
        lh.life.stage_lease(lh.stage.scope["cleanup_ref"], decision=decision)
    with pytest.raises(BindingError):
        lh.stage.agent.start(lh.stage.scope["launch_ref"], digest(unit), decision=decision)
    assert not lh.stage.agent.children
    row = lh.stage.agent.store.read(lh.stage.scope["launch_ref"], decision=lh.use())
    assert row["state"] == "start-consumed"
    assert row["generation"] is None
    assert lh.life.state(decision=lh.use())["registration"] is not None


def test_dead_final_scheduler_refuses_operation_but_independent_closed_lease_cleanup_survives(lh):
    lh.launch()
    lh.finalize()
    lh.takeover()
    assert lh.primary().call("lease", plan_ref=lh.plan.ref, decision=lh.use())["status"] == "active"
    runtime = lh.runtime()
    lh.processes[0].kill()
    lh.processes[0].join(timeout=3)
    call_target = lh.primary()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("lease", plan_ref=lh.plan.ref, decision=call_decision)
    entered = []
    with pytest.raises(BindingError, match="lifecycle-operation-failed"):
        runtime.run(lambda: entered.append(True))
    assert not entered
    assert runtime.cleanup_verification is not None
    assert lh.primary().call("lease", plan_ref=lh.plan.ref, decision=lh.use())["status"] == "closed"
    assert not lh.provider.active[lh.token.credential]


from workload_factory_binding_runtime.hosted.lifecycle import (PosixResources, FileResource, TokenResource, HostedLifecycle,
    LifecycleActors, LifecycleStores)
from workload_factory_binding_runtime.hosted.issuance import InstallationRetirer
import fcntl


def file_provider(tmp_path, request, files):
    store, _ = journal(tmp_path)
    value = PosixResources(files=tuple(files), worker_ref="resource:worker", pins=store)
    request.addfinalizer(value.close)
    return value, store


@pytest.mark.parametrize("alias", ["same-path", "hardlink"])
def test_retained_run_alias_is_rejected_before_any_anchor(tmp_path, request, alias):
    target = tmp_path / "retained"
    target.write_bytes(b"retained generation")
    second = target
    if alias == "hardlink":
        second = tmp_path / "alias"
        os.link(target, second)
    store, _ = journal(tmp_path)
    posix_resources_files = ((FileResource("resource:retained", target, "retained"),
            FileResource("resource:alias", second, "run")))
    with pytest.raises(BindingError):
        PosixResources(files=posix_resources_files, worker_ref="resource:worker", pins=store)
    assert target.read_bytes() == b"retained generation"
    assert not list((store.directory / "file-pins").iterdir())


def test_run_anchor_prevents_inode_recycling_and_preserves_fenced_replacement(tmp_path, request):
    target = tmp_path / "run-file"
    target.write_bytes(b"original generation")
    resources, store = file_provider(tmp_path, request, [FileResource("resource:file", target, "run")])
    expected, = resources.inventory(decision=use(), initialize=True)
    original = target.stat()
    anchor = store.directory / "file-pins" / resources.files.slot(expected.ref)
    assert anchor.stat().st_ino == original.st_ino
    assert original.st_nlink == 2
    directory = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(directory, fcntl.LOCK_EX)
        for _ in range(16):
            target.unlink()
            target.write_bytes(b"replacement generation")
            assert target.stat().st_ino != original.st_ino
        assert anchor.stat().st_nlink == 1
    finally:
        os.close(directory)
    assert resources.observe(expected, decision=use()).instance_ref != expected.instance_ref
    cleanup_decision = use()
    with pytest.raises(BindingError):
        resources.cleanup(expected, decision=cleanup_decision)
    assert target.read_bytes() == b"replacement generation"
    assert anchor.read_bytes() == b"original generation"


def test_successful_file_retirement_removes_anchor_and_preserves_any_later_path(tmp_path, request):
    target = tmp_path / "run-file"
    target.write_bytes(b"original")
    resources, store = file_provider(tmp_path, request, [FileResource("resource:file", target, "run")])
    expected, = resources.inventory(decision=use(), initialize=True)
    resources.cleanup(expected, decision=use())
    assert not target.exists()
    assert not list((store.directory / "file-pins").iterdir())
    assert resources.observe(expected, decision=use()).present is False
    target.write_bytes(b"new slot generation")
    actual = resources.observe(expected, decision=use())
    assert actual.present
    assert actual.instance_ref != expected.instance_ref
    cleanup_decision = use()
    with pytest.raises(BindingError):
        resources.cleanup(expected, decision=cleanup_decision)
    assert target.read_bytes() == b"new slot generation"
    assert sum(e["kind"] == "file-retired" for e in store.events(decision=use())) == 1


def test_missing_file_anchor_never_recreates_or_adopts_a_generation(tmp_path, request):
    target = tmp_path / "run-file"
    target.write_bytes(b"original")
    resources, store = file_provider(tmp_path, request, [FileResource("resource:file", target, "run")])
    expected, = resources.inventory(decision=use(), initialize=True)
    anchor = store.directory / "file-pins" / resources.files.slot(expected.ref)
    anchor.unlink()
    for action in (lambda: resources.observe(expected, decision=use()),
                   lambda: resources.cleanup(expected, decision=use()),
                   lambda: resources.inventory(decision=use())):
        with pytest.raises(BindingError):
            action()
    assert not anchor.exists()
    assert target.read_bytes() == b"original"


def test_fresh_file_provider_cannot_adopt_a_registered_epoch(lh, request):
    original = lh.life.resources
    selected = tuple(v for v in original.selected.values() if type(v) is FileResource)
    tokens = tuple(v for v in original.selected.values() if type(v) is TokenResource)
    fresh = PosixResources(files=selected, tokens=tokens, worker_ref=original.worker_ref, pins=lh.stores["primary"])
    request.addfinalizer(fresh.close)
    lh.register()
    assert fresh.epoch != original.epoch
    try:
        lh.life.resources = fresh
        state_decision = lh.use()
        with pytest.raises(BindingError):
            lh.life.state(decision=state_decision)
    finally:
        lh.life.resources = original
    assert lh.life.state(decision=lh.use())["registration"] is not None


@pytest.mark.parametrize("target", ["primary", "audit", "scheduler-witness", "host", "controller"])
def test_known_control_state_can_never_be_selected_as_a_run_file(lh, request, target):
    paths = {"primary": lh.stores["primary"].directory / "lifecycle.sqlite",
             "audit": lh.stores["audit"].directory / "lifecycle.sqlite",
             "scheduler-witness": lh.stores["scheduler"].witness / "00000000.witness",
             "host": lh.stage.agent.store.directory / "staging.sqlite",
             "controller": lh.stage.controller.store.directory / "staging.sqlite"}
    path = paths[target]
    original = lh.life.resources
    selected = [v for v in original.selected.values() if type(v) is FileResource and v.path != path]
    selected.append(FileResource("resource:unsafe-control-file", path, "run"))
    resources = PosixResources(files=tuple(selected),
        tokens=tuple(v for v in original.selected.values() if type(v) is TokenResource),
        worker_ref=original.worker_ref, pins=lh.stores["primary"])
    request.addfinalizer(resources.close)
    life = lh.life
    with pytest.raises(BindingError):
        HostedLifecycle(plan=life.plan, context=life.context, policy=life.policy,
            host_store=life.host_store,
            stores=LifecycleStores(primary=life.store, intake=life.intake, audit=life.audit_store),
            resources=resources,
            actors=LifecycleActors(janitor=life.janitor, auditor=life.auditor, scheduler=json.loads(life.scheduler)),
            host_pid_namespace=life.host_pid_namespace, final_authority_principal=life.final_authority_principal,
            cleanup_until=life.cleanup_until, retained_roots=(lh.stage.controller.store.directory,))
    assert path.exists()
    assert not list((lh.stores["primary"].directory / "file-pins").iterdir())
    assert lh.life.state(decision=lh.use())["registration"] is None


def tick_cleanup(lh):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        lh.pipes[0].send("tick")
        assert lh.pipes[0].poll(8)
        outcome = lh.pipes[0].recv()
        if outcome in ("cleanup-requested", "reconcile-only"):
            return outcome
        time.sleep(.05)
    pytest.fail("independent cleanup did not run within its bounded fixture wait")


def test_independent_expiry_retires_registered_scope_that_never_started(lh):
    lh.register()
    registration = lh.life.state(decision=lh.use())["registration"]
    lh.advance(registration["expires_at"])
    tick_cleanup(lh)
    record = lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:prestart", decision=lh.use())
    assert record["kind"] == "stage"
    assert all(r["ref"] != lh.life.resources.worker_ref for r in record["resources"])
    state = lh.life.state(decision=lh.use())
    assert state["closed"]
    assert state["prestart_closed"]
    assert state["generation"] is None
    assert not lh.stage.agent.children
    assert not lh.temporary.exists()
    assert not lh.provider.active[lh.token.credential]


def test_persisted_worker_exit_before_lifecycle_binding_still_retires_exact_scope(lh):
    lh.launch(bind=False)
    row = lh.stage.agent.store.read(lh.stage.scope["launch_ref"], decision=lh.use())
    child = lh.stage.agent.children[lh.stage.scope["launch_ref"]]
    child.terminate()
    child.communicate(timeout=3)
    assert process_instance(child.pid)[0] is None
    lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    record = lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:known-dead", decision=lh.use())
    assert record["kind"] == "stage"
    assert lh.life.state(decision=lh.use())["generation"]["generation"] == row["generation"]
    assert not lh.temporary.exists()
    assert not lh.provider.active[lh.token.credential]


@pytest.mark.parametrize("lh", ["short-cleanup"], indirect=True)
@pytest.mark.parametrize("owner", ["stage", "final"])
def test_short_cleanup_timeout_bounds_backend_on_the_same_wall_and_monotonic_decision(lh, monkeypatch, owner):
    lh.launch()
    if owner == "final":
        lh.finalize()
        lh.takeover()
    monotonic = [0.]
    decision = Decision(clock=lambda: lh.clock.value, monotonic=lambda: monotonic[0])
    original = lh.life.resources.cleanup
    called = []
    def delayed(resource, *, decision, **kwargs):
        called.append((decision.deadline, decision.end))
        monotonic[0] += 2
        original(resource, decision=decision, **kwargs)
    monkeypatch.setattr(lh.life.resources, "cleanup", delayed)
    with pytest.raises(BindingError):
        lh.life.cleanup(lh.stage.scope["launch_ref"], "failure", decision=decision)
    assert called
    assert called[0][0] == lh.clock.value + 1
    assert called[0][1] <= 1
    assert lh.temporary.exists()
    assert lh.provider.active[lh.token.credential]


@pytest.mark.parametrize("lh", ["intake-crash"], indirect=True)
@pytest.mark.parametrize("replacement", [False, True])
def test_primary_death_after_registration_commit_is_discovered_without_replaying_registration(lh, replacement):
    with pytest.raises(BindingError):
        lh.register()
    lh.processes[1].join(timeout=3)
    assert lh.processes[1].exitcode == 23
    state = lh.life.state(decision=lh.use())
    assert state["registration"]
    assert state["generation"] is None
    assert not any(e["kind"] == "stage-intake" for e in lh.stores["scheduler"].events(decision=lh.use()))
    anchor = lh.stores["primary"].directory / "file-pins" / lh.life.resources.files.slot("resource:temporary")
    assert anchor.stat().st_ino == lh.temporary.stat().st_ino
    if replacement:
        fd = os.open(lh.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            lh.temporary.unlink()
            lh.temporary.write_bytes(b"replacement after API actor crash")
            assert lh.temporary.stat().st_ino != anchor.stat().st_ino
        finally:
            os.close(fd)
    lh.restart_primary()
    call_target = lh.audit()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("ack-stage", decision=call_decision)
    lh.advance(state["registration"]["expires_at"])
    tick_cleanup(lh)
    if replacement:
        call_target_2 = lh.audit()
        call_decision_2 = lh.use()
        with pytest.raises(BindingError):
            call_target_2.call("cleanup-audit", attempt_ref="cleanup-attempt:registration-crash", decision=call_decision_2)
        assert lh.temporary.read_bytes() == b"replacement after API actor crash"
        assert anchor.exists()
    else:
        record = lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:registration-crash", decision=lh.use())
        assert record["kind"] == "stage"
        assert not lh.temporary.exists()
    assert not lh.stage.agent.children
    assert not lh.provider.active[lh.token.credential]
    assert sum(e["kind"] == "registration" for e in lh.stores["primary"].events(decision=lh.use())) == 1


@pytest.mark.parametrize("lh", ["three-tokens"], indirect=True)
@pytest.mark.parametrize("owner", ["stage", "final"])
def test_maximum_selected_token_manifest_completes_cleanup_within_private12(lh, owner):
    lh.launch()
    if owner == "final":
        lh.finalize()
        lh.takeover()
    lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    record = lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:three-tokens", decision=lh.use())
    assert record["kind"] == owner
    assert len(lh.tokens) == 3
    assert all(not lh.provider.active[cap.credential] for cap in lh.tokens)
    assert sum(method == "DELETE" and path == "/installation/token" for method, path in lh.provider.calls) == 3


def test_token_manifest_over_cleanup_budget_is_rejected_before_registration(lh):
    extras = []
    retire = InstallationRetirer(writer=lh.provider.routed(), observer=lh.provider.routed())
    try:
        for n in range(3):
            lh.provider.ref, lh.provider.nonce = f"issuance:extra-{n}", secrets.token_hex(32)
            lh.issuer.issue(lh.provider.ref, lh.provider.nonce, decision=lh.use())
            extras.append(lh.issuer.pending(lh.provider.ref))
        original = lh.life.resources
        tokens = tuple(TokenResource(f"resource:token-{n}", cap, retire)
                       for n, cap in enumerate((lh.token, *extras)))
        posix_resources_files = tuple(v for v in original.selected.values() if type(v) is FileResource)
        with pytest.raises(BindingError):
            PosixResources(files=posix_resources_files,
                tokens=tokens, worker_ref=original.worker_ref, pins=lh.stores["primary"])
        assert lh.life.state(decision=lh.use())["registration"] is None
        assert not list((lh.stores["primary"].directory / "file-pins").iterdir())
    finally:
        for cap in extras:
            retire.retire(cap, decision=lh.use())


def test_file_retirement_without_durable_marker_stays_unverified_and_never_replays(tmp_path, request, monkeypatch):
    target = tmp_path / "run-file"
    target.write_bytes(b"original")
    resources, store = file_provider(tmp_path, request, [FileResource("resource:file", target, "run")])
    expected, = resources.inventory(decision=use(), initialize=True)
    original = store.record
    def lost(kind, data, **kwargs):
        if kind == "file-retired":
            raise BindingError("fixture-lost-retirement-marker")
        return original(kind, data, **kwargs)
    monkeypatch.setattr(store, "record", lost)
    cleanup_decision = use()
    with pytest.raises(BindingError, match="fixture-lost-retirement-marker"):
        resources.cleanup(expected, decision=cleanup_decision)
    assert not target.exists()
    assert not list((store.directory / "file-pins").iterdir())
    target.write_bytes(b"newer generation")
    observe_decision = use()
    with pytest.raises(BindingError):
        resources.observe(expected, decision=observe_decision)
    cleanup_decision_2 = use()
    with pytest.raises(BindingError):
        resources.cleanup(expected, decision=cleanup_decision_2)
    assert target.read_bytes() == b"newer generation"


def test_actual_host_manager_death_preserves_independent_cleanup_of_persisted_generation(lh):
    import select
    import sys
    import subprocess
    def observer(source):
        transport = source.transport
        return {"origin": source.origin, "principal_ref": source.principal, "scope": source.scope.record(),
            "transport": {"ca_file": str(transport.ca), "certificate": str(transport.cert),
                "private_key": str(transport.key), "observation_origin": source.origin,
                "server_certificate_digest": transport.server_certificate_digest}}
    stage, spec = lh.stage, lh.stage.spec
    receipt = lh.root.parent / "crashed-generation.json"
    refs = {"now": stage.v.h.now, "plan": stage.v.plan, "context": asdict(stage.v.context),
        "policy": asdict(stage.policy), "roots": {k: str(v) for k,v in spec.roots.items()},
        "runtime": [str(p) for p in spec.runtime], "private": [str(p) for p in spec.private], "gid": spec.gid,
        "directory": str(stage.agent.store.directory), "identity": stage.agent.store.identity,
        "grant": observer(stage.agent.authority.grant), "lease": observer(stage.agent.authority.lease),
        "grant_ref": stage.agent.authority.ref, "receipt": str(receipt), "persist_generation": True}
    path = lh.root.parent / "manager-crash-refs.json"
    path.write_bytes(canonical(refs));path.chmod(0o600)
    helper = Path(__file__).with_name("stage_crash_role.py")
    process = subprocess.Popen([sys.executable, "-I", "-B", str(helper), "supervisor", str(path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, close_fds=True)
    try:
        assert select.select([process.stdout], [], [], 10)[0]
        unit = json.loads(process.stdout.readline())
        records_path = lh.root / "lifecycle-processes.json"
        records = json.loads(records_path.read_bytes())
        records["generations"].append({"pid": unit["manager_pid"],
            "instance_ref": f"process:{unit['manager_pid']}:{unit['manager_start']}"})
        records_path.write_bytes(canonical(records))
        lh.primary().call("register", unit_digest=digest(unit), decision=lh.use())
        lh.audit().call("ack-stage", decision=lh.use())
        out, error = process.communicate("start\n", timeout=22)
        assert process.returncode == 0, error
        result = json.loads(out)
        assert result["manager_exit"] == 73
        assert result["worker_reaped"]
        assert result["worker_signal"] == 9
        assert process_instance(result["worker_pid"])[0] is None
        assert all(role.is_alive() for role in lh.processes[:3])
        row = stage.agent.store.read(stage.scope["launch_ref"], decision=lh.use())
        assert row["state"] == "running"
        assert row["generation"] is not None
        assert lh.life.state(decision=lh.use())["generation"] is None
        lh.primary().call("cleanup", outcome="failure", decision=lh.use())
        record = lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:real-manager-death", decision=lh.use())
        assert record["kind"] == "stage"
        assert not lh.provider.active[lh.token.credential]
        assert not lh.temporary.exists()
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=3)


def test_process_generation_disappearance_during_proc_read_is_absent(monkeypatch):
    from workload_factory_binding_runtime.hosted.lifecycle import process_instance

    def gone(_path, *args, **kwargs):
        raise ProcessLookupError("process reaped during proc stat read")

    monkeypatch.setattr(Path, "read_text", gone)
    assert process_instance(123456) == (None, None)


def test_lifecycle_aggregate_snapshot_exceeds_document_limit_without_raising_event_bounds(tmp_path):
    store, identity = journal(tmp_path)
    payload = {"ref": "launch:aggregate", "nested": {"value": "x" * 25000}}
    for n in range(3):
        store.record("stage-intake", {**payload, "index": n}, decision=use())
    events = store.events(decision=use())
    assert len(canonical(events)) > 65536
    assert len(events) < 2048
    assert all(len(canonical(e["data"])) <= 65536 for e in events)
    events[1]["data"]["nested"]["value"] = "caller mutation"
    reopened = LifecycleStore(store.directory, store.witness, identity=identity, kind="primary")
    assert reopened.events(decision=use())[1]["data"]["nested"]["value"] == payload["nested"]["value"]
    record_decision = use()
    with pytest.raises(BindingError):
        reopened.record("stage-intake", {"value": "x" * 65536}, decision=record_decision)
    assert len(reopened.events(decision=use())) == len(events)


@pytest.mark.parametrize("lh", ["large-manifest"], indirect=True)
def test_large_final_manifest_cleans_and_audits_above_aggregate_document_limit(lh):
    lh.launch()
    lh.finalize()
    lh.takeover()
    state = lh.life.state(decision=lh.use())
    resources = lh.life.resources_for(state)
    assert len(resources) == 64
    assert sum(r.kind == "file" and r.retention == "run" for r in resources) == 30
    assert sum(r.kind == "file" and r.retention != "run" for r in resources) == 32
    selected = lh.life.resources.selected
    kept = {r.ref: (selected[r.ref].path.stat().st_dev, selected[r.ref].path.stat().st_ino)
            for r in resources if r.kind == "file" and r.retention != "run"}
    lh.primary().call("cleanup", outcome="success", decision=lh.use())
    audit = lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:large-manifest", decision=lh.use())
    assert audit["kind"] == "final"
    assert len(audit["record"]["resources"]) == 64
    actual = {r["ref"]: r for r in audit["record"]["resources"]}
    for resource in resources:
        observed = actual[resource.ref]
        assert observed["instance_ref"] == resource.instance_ref
        assert observed["present"] is (resource.retention != "run")
        if resource.kind == "credential":
            assert observed["revoked"]
        if resource.kind == "file":
            path = selected[resource.ref].path
            if resource.retention == "run":
                assert not path.exists()
            else:
                actual_resource_identity = (path.stat().st_dev, path.stat().st_ino)
                assert actual_resource_identity == kept[resource.ref]
    assert not lh.provider.active[lh.token.credential]
    assert not list((lh.stores["primary"].directory / "file-pins").iterdir())
    events = lh.stores["primary"].events(decision=lh.use())
    assert len(canonical(events)) > 65536
    assert len(events) < 2048
    assert all(len(canonical(e["data"])) <= 65536 for e in events)


@pytest.mark.parametrize("fence", ["parent", "pins"])
def test_busy_file_fence_keeps_unattempted_generation_available_for_bounded_cleanup(lh, monkeypatch, fence):
    import fcntl
    lh.launch()
    lh.finalize()
    lh.takeover()
    state = lh.life.state(decision=lh.use())
    target = next(r for r in lh.plan.resources if r.ref == "resource:temporary")
    path = lh.temporary
    anchor = lh.life.resources.files.root / lh.life.resources.files.slot(target.ref)
    original_generation = (path.stat().st_dev, path.stat().st_ino, path.read_bytes(), path.stat().st_nlink)
    backend = lh.life.resources.cleanup
    blocked = []
    def hold_after_observation(resource, *, decision, **kwargs):
        if resource.ref != target.ref or blocked:
            return backend(resource, decision=decision, **kwargs)
        blocked.append(True)
        directory = path.parent if fence == "parent" else anchor.parent
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return backend(resource, decision=decision, **kwargs)
        finally:
            os.close(fd)
    monkeypatch.setattr(lh.life.resources, "cleanup", hold_after_observation)
    cleanup_decision = lh.use()
    with pytest.raises(BindingError):
        lh.life.cleanup(lh.stage.scope["launch_ref"], "failure", decision=cleanup_decision)
    partial = lh.life.state(decision=lh.use())
    assert blocked
    assert partial["closed"]
    assert partial["released"]
    assert partial["registration"] == state["registration"]
    assert target.ref not in {a["resource"]["ref"] for a in partial["actions"].values()}
    actual_generation = (path.stat().st_dev, path.stat().st_ino, path.read_bytes(), path.stat().st_nlink)
    assert actual_generation == original_generation
    assert (anchor.stat().st_dev, anchor.stat().st_ino, anchor.stat().st_nlink) == (original_generation[0], original_generation[1], 2)
    assert not any(e["kind"] == "file-retired" and e["data"]["ref"] == target.ref
                   for e in lh.stores["primary"].events(decision=lh.use()))
    call_target = lh.audit()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("cleanup-audit", attempt_ref="cleanup-attempt:still-owned", decision=call_decision)
    monkeypatch.setattr(lh.life.resources, "cleanup", backend)
    lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    assert lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:fence-released", decision=lh.use())["kind"] == "final"
    final = lh.life.state(decision=lh.use())
    assert final["registration"]["cleanup_until"] == state["registration"]["cleanup_until"]
    assert set(partial["actions"]) <= set(final["actions"])
    assert sum(a["resource"]["ref"] == target.ref for a in final["actions"].values()) == 1
    assert sum(e["kind"] == "file-retired" and e["data"]["ref"] == target.ref
               for e in lh.stores["primary"].events(decision=lh.use())) == 1
    assert sum(method == "DELETE" and route == "/installation/token" for method, route in lh.provider.calls) == 1


def test_file_failure_after_durable_claim_never_replays_an_unknown_unlink(lh, monkeypatch):
    lh.launch()
    lh.finalize()
    lh.takeover()
    target = next(r for r in lh.plan.resources if r.ref == "resource:temporary")
    generation = (lh.temporary.stat().st_dev, lh.temporary.stat().st_ino, lh.temporary.read_bytes())
    unlink = os.unlink
    attempted = []
    def fail_unlink(path, *args, **kwargs):
        if os.fspath(path) == lh.temporary.name and kwargs.get("dir_fd") is not None:
            attempted.append(True)
            raise OSError("fixture file mutation result unavailable")
        return unlink(path, *args, **kwargs)
    monkeypatch.setattr(os, "unlink", fail_unlink)
    cleanup_decision = lh.use()
    with pytest.raises(BindingError):
        lh.life.cleanup(lh.stage.scope["launch_ref"], "failure", decision=cleanup_decision)
    monkeypatch.setattr(os, "unlink", unlink)
    state = lh.life.state(decision=lh.use())
    assert attempted == [True]
    assert sum(a["resource"]["ref"] == target.ref for a in state["actions"].values()) == 1
    call_target = lh.primary()
    call_decision = lh.use()
    with pytest.raises(BindingError):
        call_target.call("cleanup", outcome="failure", decision=call_decision)
    actual_temporary = (lh.temporary.stat().st_dev, lh.temporary.stat().st_ino, lh.temporary.read_bytes())
    assert actual_temporary == generation
    assert lh.life.state(decision=lh.use())["actions"] == state["actions"]
    assert not any(e["kind"] == "file-retired" and e["data"]["ref"] == target.ref
                   for e in lh.stores["primary"].events(decision=lh.use()))
    call_target_2 = lh.audit()
    call_decision_2 = lh.use()
    with pytest.raises(BindingError):
        call_target_2.call("cleanup-audit", attempt_ref="cleanup-attempt:unknown-file", decision=call_decision_2)
    assert sum(method == "DELETE" and route == "/installation/token" for method, route in lh.provider.calls) == 1


def test_stage_release_without_final_plan_preserves_bound_generation(lh):
    lh.launch()
    before = lh.life.state(decision=lh.use())
    assert before["final"] is None
    assert before["generation"] is not None
    decision = lh.use()
    with pytest.raises(BindingError, match="hosted-lifecycle-refused"):
        lh.life.release_stage(lh.stage.scope["launch_ref"], decision=decision)
    after = lh.life.state(decision=lh.use())
    assert after["final"] is None
    assert not after["released"]
    assert after["generation"] == before["generation"]


def test_stage_readback_without_generation_refuses_before_authority_read(lh, monkeypatch):
    from workload_factory_binding_runtime.hosted.lifecycle import RegisteredStageReadback
    lh.register()
    before = lh.life.state(decision=lh.use())
    assert before["generation"] is None
    def forbidden(*args, **kwargs):
        raise AssertionError("generation-less readback reached authority")
    monkeypatch.setattr(lh.life, "stage_lease", forbidden)
    readback = RegisteredStageReadback(lh.life)
    decision = lh.use()
    with pytest.raises(BindingError, match="hosted-lifecycle-refused"):
        readback.read(lh.stage.scope["launch_ref"], decision=decision)
    after = lh.life.state(decision=lh.use())
    assert after["generation"] is None
    assert not after["released"]
    assert lh.stage.agent.children == {}
