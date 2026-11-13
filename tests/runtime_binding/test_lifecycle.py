"""Synthetic lifecycle capabilities; actual process isolation is tested separately."""
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import BindingError, digest
from workload_factory_binding_runtime.lifecycle import (
    CleanupReadback, JanitorPeer, LeaseReadback, ManagedResource, ResourceReadback,
    RunJanitor, RunLifecycle, RunPlan, RunResource, RunScope,
)
from workload_factory_binding_runtime.loaders import BoundService, ServiceIdentity
from .composition_fixture import c
from .test_config import configuration, encoded


@pytest.fixture
def l(c):
    cfg, now = c.config, c.h.now
    scope = RunScope(digest(cfg), cfg["case_ref"], cfg["launch"]["run_id"], cfg["launch"]["run_attempt"],
                     **cfg["lifecycle"])
    resources = (
        RunResource("resource:worker", "instance:worker", "process", "run"),
        RunResource("resource:credential", "instance:credential", "credential", "run"),
        RunResource("resource:temporary", "instance:temporary", "file", "run"),
        RunResource(cfg["state"]["store_ref"], "instance:state", "file", "retained"),
        RunResource("resource:shared", "instance:shared", "file", "shared"),
    )
    identity = ServiceIdentity(**cfg["services"]["janitor"])
    plan = RunPlan("plan:fixture", scope, identity, resources, now - 1, now + 60, 10, cfg["state"]["store_ref"])
    b = SimpleNamespace(c=c, plan=plan, status="active", calls=[], present={r.ref: True for r in resources},
                        revoked={r.ref: False for r in resources}, lease_hook=None, cleanup_hook=None,
                        readback_hook=None, close_hook=None)
    b.managed = {r.ref: ManagedResource(r, digest(asdict(scope)) if r.retention == "run" else "shared")
                 for r in resources}
    gate = JanitorPeer(identity.principal_ref, identity.credential_ref)

    def load_plan(ref, *, deadline):
        b.calls.append(("plan", ref, deadline))
        assert ref == plan.ref
        return b.plan
    def load_lease(ref, *, deadline):
        b.calls.append(("lease", ref, deadline))
        if b.lease_hook:
            b.lease_hook()
        return LeaseReadback(b.plan.digest, b.plan.scope, b.status, b.plan.issued_at, b.plan.expires_at,
                             c.h.now, c.h.now + 30)
    def load_resource(ref, *, deadline):
        b.calls.append(("resource", ref, deadline))
        return b.managed[ref]
    def close(ref, *, deadline):
        b.calls.append(("close", ref, deadline))
        if b.close_hook:
            b.close_hook()
        b.status = "closed"
    def cleanup(expected, *, deadline):
        b.calls.append(("cleanup", expected.resource.ref, deadline))
        if b.cleanup_hook:
            b.cleanup_hook(expected)
        assert b.managed[expected.resource.ref] == expected  # provider compare-and-remove seam
        b.present[expected.resource.ref] = False
        b.revoked[expected.resource.ref] = expected.resource.kind == "credential"
    b.janitor = RunJanitor(plan=plan, allowed_gate=gate, load_plan=load_plan, load_lease=load_lease,
                          load_resource=load_resource, close_lease=close, cleanup=cleanup, clock=lambda: c.h.now)
    class Gate:
        def read_lease(self, ref, *, deadline):
            return b.janitor.read_lease(ref, peer=gate, deadline=deadline)
        def finalize(self, ref, *, deadline):
            b.janitor.finalize(ref, peer=gate, deadline=deadline)
    class Readback:
        def read_cleanup(self, ref, *, attempt_ref, deadline):
            b.calls.append(("readback", ref, deadline))
            if b.readback_hook:
                return b.readback_hook(attempt_ref)
            return CleanupReadback(b.plan.digest, b.plan.scope, b.status,
                                   tuple(ResourceReadback(r.ref, b.managed[r.ref].resource.instance_ref,
                                                          b.present[r.ref], b.revoked[r.ref]) for r in resources),
                                   c.h.now, c.h.now + 30, attempt_ref)
    b.gate_service = BoundService(identity, Gate())
    b.readback_service = BoundService(ServiceIdentity("service:readback", "principal:readback", "credential:readback",
                                                     "sha256:" + "f" * 64), Readback())
    def make(**overrides):
        args = dict(plan=b.plan, load_config=lambda: encoded(c.config), runtime_trust=c.trust,
                    janitor=b.gate_service, readback=b.readback_service, cleanup_clock=lambda: c.h.now)
        args.update(overrides)
        return RunLifecycle(**args)
    b.make = make
    b.life = make()
    c.bridge = c.make(lifecycle=b.life)
    b.calls.clear()
    return b


def assert_clean(l):
    assert l.status == "closed"
    for resource in l.plan.resources:
        assert l.present[resource.ref] is (resource.retention != "run")
    assert l.revoked["resource:credential"] is True
    assert [ref for op, ref, _ in l.calls if op == "cleanup"] == [r.ref for r in l.plan.resources if r.retention == "run"]


def test_proof_returns_only_after_independent_cleanup_and_preserves_shared_state(l):
    result = l.life.run(l.c.run)
    assert result["human_approval"] is False
    assert l.c.h.calls == 1
    assert_clean(l)
    assert l.calls[-1][0] == "readback"
    with pytest.raises(BindingError):
        l.c.run()  # closed run lease refuses before another signer use


@pytest.mark.parametrize("error", [RuntimeError("private-value"), KeyboardInterrupt(), SystemExit(2)])
def test_failure_and_cancellation_finalize_before_propagation(l, error):
    def fail():
        raise error
    expected = BindingError if isinstance(error, Exception) else type(error)
    with pytest.raises(expected) as caught:
        l.life.run(fail)
    assert "private-value" not in str(caught.value)
    assert_clean(l)


def test_expired_proof_configuration_does_not_disable_cleanup(l):
    def expire():
        l.c.h.now += 121
        return "must-not-return"
    with pytest.raises(BindingError):
        l.life.run(expire)
    assert_clean(l)


def test_expiry_janitor_works_without_runner_finally(l):
    l.c.h.now = l.plan.expires_at
    l.janitor.sweep(l.plan.ref, deadline=l.c.h.now + 10)
    verification = l.life.finalize("cancel")  # fresh readback; repeated cleanup is idempotent
    assert verification.outcome == "cancel"
    assert l.status == "closed"
    assert l.present["resource:shared"] is True


def test_sweeper_cannot_remove_an_active_unexpired_run(l):
    with pytest.raises(BindingError, match="^janitor-lease-still-active$"):
        l.janitor.sweep(l.plan.ref, deadline=l.c.h.now + 10)
    assert not any(op == "cleanup" for op, _, _ in l.calls)


def test_janitor_attempt_budget_includes_registration_lookup(l):
    original, started = l.janitor.load_plan, l.c.h.now
    def delayed(ref, *, deadline):
        l.c.h.now += l.plan.cleanup_timeout + 1
        return original(ref, deadline=deadline)
    l.janitor.load_plan = delayed
    with pytest.raises(BindingError, match="^lifecycle-expired$"):
        l.janitor.finalize(l.plan.ref, peer=l.janitor.allowed_gate, deadline=started + 100)
    assert not any(op == "close" for op, _, _ in l.calls)


def test_other_plan_is_rejected_before_registration_lookup(l):
    with pytest.raises(BindingError, match="^janitor-plan-mismatch$"):
        l.janitor.finalize("plan:other", peer=l.janitor.allowed_gate, deadline=l.c.h.now + 10)
    assert l.calls == []


def test_changed_registration_cannot_widen_the_frozen_manifest(l):
    l.plan = replace(l.plan, resources=l.plan.resources +
                     (RunResource("resource:other", "instance:other", "file", "run"),))
    with pytest.raises(BindingError, match="^janitor-plan-mismatch$"):
        l.janitor.finalize(l.plan.ref, peer=l.janitor.allowed_gate, deadline=l.c.h.now + 10)
    assert not any(op == "close" for op, _, _ in l.calls)


@pytest.mark.parametrize("peer", [JanitorPeer("principal:worker_channel", "credential:worker_channel"),
                                  {"principal_ref": "principal:janitor", "credential_ref": "credential:janitor"}])
def test_worker_or_body_peer_denied_before_protected_io(l, peer):
    with pytest.raises(BindingError, match="^janitor-peer-denied$"):
        l.janitor.finalize(l.plan.ref, peer=peer, deadline=l.c.h.now + 10)
    assert l.calls == []


@pytest.mark.parametrize("field", ["config_digest", "case_ref", "run_id", "run_attempt", "lease_ref",
                                   "cleanup_ref", "receipt_retention_ref"])
def test_each_scope_binding_refuses(l, field):
    value = "sha256:" + "a" * 64 if field == "config_digest" else "changed:scope"
    plan = replace(l.plan, scope=replace(l.plan.scope, **{field: value}))
    with pytest.raises(BindingError, match="^lifecycle-scope-mismatch$"):
        l.make(plan=plan)


@pytest.mark.parametrize("field", ["principal_ref", "credential_ref"])
def test_readback_credential_and_principal_must_be_independent(l, field):
    identity = replace(l.readback_service.identity, **{field: getattr(l.plan.janitor, field)})
    readback = BoundService(identity, l.readback_service.target)
    with pytest.raises(BindingError, match="^lifecycle-readback-not-independent$"):
        l.make(readback=readback)


def test_replay_store_cannot_enter_run_deletion_manifest(l):
    resources = tuple(replace(r, retention="run") if r.ref == l.c.config["state"]["store_ref"] else r
                      for r in l.plan.resources)
    plan = replace(l.plan, resources=resources)
    with pytest.raises(BindingError, match="^lifecycle-state-not-retained$"):
        l.make(plan=plan)


@pytest.mark.parametrize("mutation", ["generation", "owner"])
def test_current_resource_generation_and_owner_are_checked_before_delete(l, mutation):
    selected = l.managed["resource:worker"]
    if mutation == "generation":
        selected = replace(selected, resource=replace(selected.resource, instance_ref="instance:replacement"))
    else:
        selected = replace(selected, owner_scope_digest="sha256:" + "e" * 64)
    l.managed["resource:worker"] = selected
    with pytest.raises(BindingError, match="^lifecycle-cleanup-unverified$"):
        l.life.finalize("cancel")
    assert l.present["resource:worker"] is True
    assert l.present["resource:temporary"] is False  # remaining cleanup still attempted
    assert l.present["resource:shared"] is True


def test_partial_cleanup_failure_does_not_skip_remaining_or_independent_readback(l):
    def fail(resource):
        if resource.resource.kind == "process":
            raise OSError("private-provider-detail")
    l.cleanup_hook = fail
    with pytest.raises(BindingError, match="^lifecycle-cleanup-unverified$"):
        l.life.finalize("failure")
    assert l.present["resource:temporary"] is False
    assert l.revoked["resource:credential"] is True
    assert l.calls[-1][0] == "readback"


@pytest.mark.parametrize("bad", [None, {"clean": True}])
def test_missing_or_worker_claimed_readback_never_qualifies(l, bad):
    l.readback_hook = lambda attempt: bad
    with pytest.raises(BindingError, match="^lifecycle-cleanup-unverified$"):
        l.life.run(lambda: "result")


@pytest.mark.parametrize("mutation", ["scope", "lease", "missing", "duplicate", "stale", "future", "numeric-bool",
                                     "credential-not-revoked", "preserved-missing", "old-attempt"])
def test_independent_cleanup_readback_is_exact_fresh_and_substantive(l, mutation):
    original = l.readback_service.target.read_cleanup
    l.readback_hook = None
    record = original(l.plan.ref, deadline=l.c.h.now + 10, attempt_ref="cleanup-attempt:previous")
    # Expected terminal readback; individual mutations must prevent qualification.
    values = tuple(replace(r, present=False, revoked=l.managed[r.ref].resource.kind == "credential")
                   if l.managed[r.ref].resource.retention == "run" else r for r in record.resources)
    record = replace(record, lease_status="closed", resources=values)
    if mutation == "scope":record = replace(record, scope=replace(record.scope, run_attempt="other"))
    elif mutation == "lease":record = replace(record, lease_status="active")
    elif mutation == "missing":record = replace(record, resources=values[:-1])
    elif mutation == "duplicate":record = replace(record, resources=values[:-1] + (values[0],))
    elif mutation == "stale":record = replace(record, observed_at=l.c.h.now - 1)
    elif mutation == "future":record = replace(record, observed_at=l.c.h.now + 1)
    elif mutation == "numeric-bool":record = replace(record, resources=(replace(values[0], present=0),) + values[1:])
    elif mutation == "credential-not-revoked":record = replace(record, resources=tuple(replace(r, revoked=False) for r in values))
    elif mutation == "preserved-missing":record = replace(record, resources=tuple(replace(r, present=False) for r in values))
    l.readback_hook = lambda attempt: record if mutation == "old-attempt" else replace(record, attempt_ref=attempt)
    with pytest.raises(BindingError, match="^lifecycle-cleanup-unverified$"):
        l.life.finalize("success")


def test_lease_expiry_during_proof_io_prevents_signing_but_cleanup_runs(l):
    l.c.records.hook = lambda: setattr(l.c.h, "now", l.plan.expires_at)
    with pytest.raises(BindingError):
        l.life.run(l.c.run)
    assert l.c.h.calls == 0
    assert_clean(l)


def test_one_shot_run_does_not_execute_or_cleanup_again(l):
    assert l.life.run(lambda: "ok") == "ok"
    before = list(l.calls)
    with pytest.raises(BindingError, match="^lifecycle-run-already-used$"):
        l.life.run(lambda: "bad")
    assert l.calls == before


def test_cleanup_after_lost_config_readback_uses_accepted_frozen_plan(l):
    def lost():
        l.c.readback["expires_at"] = l.c.h.now
        raise OSError("configuration source lost")
    with pytest.raises(BindingError):
        l.life.run(lost)
    assert_clean(l)


def test_child_and_active_run_share_latest_clock_floor(l):
    def regress():
        l.c.h.now += 2
        l.life.check_for_use(deadline=l.c.h.now + 10, checked_at=l.c.h.now)
        l.c.h.now -= 1
        return "must-not-return"
    with pytest.raises(BindingError):
        l.life.run(regress)
    assert l.present["resource:temporary"] is False  # best effort cleanup despite bad qualification time


def test_proof_expiry_during_cleanup_refuses_after_retaining_reservation(l):
    l.c.context = replace(l.c.context, expires_at=l.c.h.now + 2)
    def delayed_cleanup(resource):
        if resource.resource.kind == "process":
            l.c.h.now += 3
    l.cleanup_hook = delayed_cleanup
    with pytest.raises(BindingError):
        l.life.run(l.c.run)
    assert l.c.h.calls == 1
    assert_clean(l)
    import sqlite3
    with sqlite3.connect(l.c.h.ledger.path) as db:
        assert db.execute("SELECT count(*) FROM reservations").fetchone() == (1,)


def test_cleanup_verification_latest_clock_is_retained_before_return(l):
    now = l.c.h.now
    samples = iter([now, now + 2])
    l.life.cleanup_clock = lambda: next(samples)
    with pytest.raises(BindingError):
        l.life.run(l.c.run)
    assert l.c.h.calls == 1
    assert_clean(l)


def test_final_bridge_only_clock_sample_reaches_the_active_run(l):
    original = l.life.check_for_use
    def later_bridge_sample(**kwargs):
        checkpoint = original(**kwargs)
        if l.c.h.calls:
            l.c.h.now += 1  # the bridge samples this after receiving its child checkpoint
        return checkpoint
    l.life.check_for_use = later_bridge_sample
    def operation():
        result = l.c.run()
        l.c.h.now -= 1  # older than the bridge's final sample, equal to its last child sample
        return result
    with pytest.raises(BindingError):
        l.life.run(operation)
    assert l.c.h.calls == 1
    assert l.present["resource:temporary"] is False


def test_control_interruption_during_cleanup_leaves_work_for_independent_sweep(l):
    def interrupt(resource):
        raise KeyboardInterrupt()
    l.cleanup_hook = interrupt
    with pytest.raises(KeyboardInterrupt):
        l.life.run(lambda: "must-not-return")
    assert l.status == "closed"
    assert l.present["resource:temporary"] is True
    l.cleanup_hook = None
    l.c.h.now = l.plan.expires_at
    l.janitor.sweep(l.plan.ref, deadline=l.c.h.now + 10)
    verification = l.life.finalize("cancel")
    assert verification.outcome == "cancel"
    assert l.present["resource:temporary"] is False
    assert l.present["resource:shared"] is True


def test_revoked_lease_prevents_signing_and_still_cleans(l):
    l.status = "revoked"
    with pytest.raises(BindingError):
        l.life.run(l.c.run)
    assert l.c.h.calls == 0
    assert_clean(l)
