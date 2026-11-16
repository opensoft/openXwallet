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
    with pytest.raises(BindingError):
        store.events(decision=use())


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
    with pytest.raises(BindingError):
        store.events(decision=use(1001))
    now = [1002]
    decision = Decision(clock=lambda: now[0], monotonic=lambda: 0.)
    now[0] = 1012
    with pytest.raises(BindingError):
        store.events(decision=decision)
    assert sum(e["kind"] == "stage-intake" for e in store.events(decision=use(1012))) == 1


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
    assert value.state == "running" and state["registration"] and state["generation"]
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
    with pytest.raises(BindingError):
        lh.primary().call("lease", plan_ref=plan.ref, decision=lh.use())
    lh.audit().call("ack-final", decision=lh.use())
    assert lh.life.state(decision=lh.use())["released"] is False
    lh.primary().call("release", decision=lh.use())
    state = lh.life.state(decision=lh.use())
    assert state["released"] is True and state["final"]["binding"]["config_digest"] == finalized.binding.config_digest
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
    assert (lh.shared.stat().st_dev, lh.shared.stat().st_ino, lh.shared.read_bytes()) == shared_before
    assert (retained.stat().st_dev, retained.stat().st_ino) == retained_before
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
    with pytest.raises(BindingError):
        lh.stage.protected.read(lh.stage.v.context, lh.stage.v.token, decision=lh.use())
    state = lh.life.state(decision=lh.use())
    assert state["registration"] is not None and state["generation"] is None
    assert not lh.stage.agent.children
    assert not state["released"]


@pytest.mark.parametrize("where", ["primary-store", "audit-store"])
def test_missing_registration_or_independent_ack_store_never_starts_a_worker(lh, where):
    store = lh.stores["primary" if where == "primary-store" else "audit"]
    replacement = store.directory.with_name(store.directory.name + "-held")
    store.directory.rename(replacement)
    try:
        with pytest.raises(BindingError):
            lh.stage.protected.read(lh.stage.v.context, lh.stage.v.token, decision=lh.use())
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
    with pytest.raises(BindingError):
        lh.stage.protected.read(lh.stage.v.context, lh.stage.v.token, decision=lh.use())
    assert not lh.stage.agent.children
    assert lh.stage.protected.read(lh.stage.v.context, lh.stage.v.token, decision=lh.use()).state == "registered"
    assert calls.count(reply) == 1
    state = lh.life.state(decision=lh.use())
    assert state["registration"] and state["generation"] is None and not state["released"]


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
    assert response.status == 403 and json.loads(response.body) == {"error": "hosted-lifecycle-denied"}


@pytest.mark.parametrize("lh", ["excess-worker"], indirect=True)
def test_excess_lifecycle_permission_breaks_worker_denial_positive(lh):
    lh.register()
    assert lh.primary("worker").call("status", decision=lh.use())["owner"] == "stage"
    with pytest.raises(BindingError):
        probe_worker_denial(lh.primary("worker"), "status", decision=lh.use())


def test_lifecycle_service_outage_does_not_count_as_worker_denial(lh):
    lh.register()
    assert lh.primary().call("status", decision=lh.use())
    lh.processes[1].kill()
    lh.processes[1].join(timeout=3)
    with pytest.raises(BindingError):
        probe_worker_denial(lh.primary("worker"), "status", decision=lh.use())


@pytest.mark.parametrize("field", ["path", "url", "principal_ref", "resources", "final_plan", "unit_digest", "worker_ref", "accepted_commit"])
def test_lifecycle_request_cannot_select_control_targets_or_authority(lh, field):
    lh.register()
    client = lh.primary()
    body = {"profile": PROFILE, "nonce": secrets.token_hex(32), "deadline": lh.use().deadline,
        "arguments": {"launch_ref": lh.stage.scope["launch_ref"], "scope_digest": digest(lh.stage.scope), field: "fixture:unapproved"}}
    response = client.transport.exchange("POST", client.origin + "/lifecycle/status", headers={"Content-Type": "application/json"},
        body=canonical(body), decision=lh.use())
    assert response.status == 400 and json.loads(response.body) == {"error": "hosted-lifecycle-refused"}
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
    with pytest.raises(BindingError):
        lh.primary().call("prepare", decision=lh.use())
    state = lh.life.state(decision=lh.use())
    assert not state["released"] and state["final"] is None and state["registration"]


def test_final_takeover_requires_actual_independent_ack_and_preserves_generation(lh):
    lh.launch()
    lh.finalize()
    before = lh.life.state(decision=lh.use())["generation"]
    lh.primary().call("prepare", decision=lh.use())
    with pytest.raises(BindingError):
        lh.primary().call("release", decision=lh.use())
    lh.audit().call("ack-final", decision=lh.use())
    lh.primary().call("release", decision=lh.use())
    state = lh.life.state(decision=lh.use())
    assert state["generation"] == before and state["released"]
    with pytest.raises(BindingError):
        lh.primary().call("release", decision=lh.use())
    with pytest.raises(BindingError):
        lh.primary().call("prepare", decision=lh.use())
    with pytest.raises(BindingError):
        lh.life.stage_lease(lh.stage.scope["cleanup_ref"], decision=lh.use())


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
    assert lh.shared.exists() and lh.stage.v.h.ledger.path.exists()
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
    with pytest.raises(BindingError):
        lh.audit().call("ack-final", decision=lh.use()) if boundary == "before-ack" else lh.primary().call("release", decision=lh.use())
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
    with pytest.raises(BindingError):
        lh.primary().call("release", decision=lh.use())
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
    with pytest.raises(BindingError):
        lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:changed-file", decision=lh.use())
    assert (target.stat().st_dev, target.stat().st_ino, target.read_bytes()) == expected
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
    with pytest.raises(BindingError):
        lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    deletes = sum(method == "DELETE" and path == "/installation/token" for method, path in lh.provider.calls)
    assert deletes == 1
    try:
        lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    except BindingError:
        assert still_active
    assert sum(method == "DELETE" and path == "/installation/token" for method, path in lh.provider.calls) == 1
    if still_active:
        with pytest.raises(BindingError):
            lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:retirement-unknown", decision=lh.use())
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
    assert calls == ["cleanup"] and runtime.cleanup_verification is None, errors
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
    with pytest.raises(BindingError):
        lh.primary().call("cleanup", outcome="failure", decision=lh.use())
    with pytest.raises(BindingError):
        lh.audit().call("cleanup-audit", attempt_ref="cleanup-attempt:unpersisted", decision=lh.use())
    state = lh.life.state(decision=lh.use())
    assert state["registration"] is not None and state["generation"] is None
    assert state["closed"] and not state["released"] and not state["actions"]
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
        with pytest.raises(BindingError):
            if target == "lifecycle":
                lh.life.state(decision=lh.use())
            else:
                lh.life.resources.observe(resource, decision=lh.use())
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
    assert row["state"] == "start-consumed" and row["generation"] is None
    assert lh.life.state(decision=lh.use())["registration"] is not None


def test_dead_final_scheduler_refuses_operation_but_independent_closed_lease_cleanup_survives(lh):
    lh.launch()
    lh.finalize()
    lh.takeover()
    assert lh.primary().call("lease", plan_ref=lh.plan.ref, decision=lh.use())["status"] == "active"
    runtime = lh.runtime()
    lh.processes[0].kill()
    lh.processes[0].join(timeout=3)
    with pytest.raises(BindingError):
        lh.primary().call("lease", plan_ref=lh.plan.ref, decision=lh.use())
    entered = []
    with pytest.raises(BindingError, match="lifecycle-operation-failed"):
        runtime.run(lambda: entered.append(True))
    assert not entered
    assert runtime.cleanup_verification is not None
    assert lh.primary().call("lease", plan_ref=lh.plan.ref, decision=lh.use())["status"] == "closed"
    assert not lh.provider.active[lh.token.credential]
