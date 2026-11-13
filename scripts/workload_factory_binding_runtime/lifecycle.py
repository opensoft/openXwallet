"""Run-scoped leases and independently verified cleanup; trusted embedding only.

Hosting supplies protected durable registrations, authenticated bounded connectors
and an independent scheduler/readback plane. Python objects are not administrative
isolation. No provider resolver, provisioning operation or public wire API lives here.
"""
from dataclasses import asdict, dataclass
from secrets import token_hex
from threading import Lock

from workload_factory_binding.evidence import BindingError, digest, integer, reference, require, valid_digest
from .config import RuntimeTrust, validate_config
from .loaders import BoundService, ServiceIdentity, check_service


@dataclass(frozen=True, repr=False)
class RunScope:
    config_digest: str
    case_ref: str
    run_id: str
    run_attempt: str
    lease_ref: str
    cleanup_ref: str
    receipt_retention_ref: str


@dataclass(frozen=True, repr=False)
class RunResource:
    ref: str
    instance_ref: str
    kind: str
    retention: str


@dataclass(frozen=True, repr=False)
class RunPlan:
    ref: str
    scope: RunScope
    janitor: ServiceIdentity
    resources: tuple
    issued_at: int
    expires_at: int
    cleanup_timeout: int
    retained_state_ref: str

    @property
    def digest(self):
        return digest({**asdict(self), "resources": [asdict(r) for r in self.resources]})


@dataclass(frozen=True, repr=False)
class LeaseReadback:
    plan_digest: str
    scope: RunScope
    status: str
    issued_at: int
    expires_at: int
    observed_at: int
    valid_until: int


@dataclass(frozen=True, repr=False)
class ManagedResource:
    """Actual provider identity/ownership, independently of the requested plan."""
    resource: RunResource
    owner_scope_digest: str


@dataclass(frozen=True, repr=False)
class ResourceReadback:
    ref: str
    instance_ref: str
    present: bool
    revoked: bool


@dataclass(frozen=True, repr=False)
class CleanupReadback:
    plan_digest: str
    scope: RunScope
    lease_status: str
    resources: tuple
    observed_at: int
    valid_until: int
    attempt_ref: str


@dataclass(frozen=True, repr=False)
class LifecycleUse:
    valid_until: int
    checked_at: int


@dataclass(frozen=True, repr=False)
class CleanupVerification:
    """Internal checkpoint only; full redacted receipt work remains T011."""
    plan_digest: str
    scope: RunScope
    outcome: str
    checked_at: int


@dataclass(frozen=True, repr=False)
class JanitorPeer:
    """Authenticated transport metadata, never deserialized from a worker body."""
    principal_ref: str
    credential_ref: str


def _plan(plan):
    require(type(plan) is RunPlan and type(plan.scope) is RunScope
            and type(plan.janitor) is ServiceIdentity and reference(plan.ref)
            and type(plan.resources) is tuple and 1 <= len(plan.resources) <= 64
            and integer(plan.issued_at) and integer(plan.expires_at) and plan.issued_at < plan.expires_at
            and integer(plan.cleanup_timeout) and 1 <= plan.cleanup_timeout <= 60, "invalid-lifecycle-plan")
    require(valid_digest(plan.scope.config_digest)
            and all(reference(getattr(plan.scope, name)) for name in (
                "case_ref", "run_id", "run_attempt", "lease_ref", "cleanup_ref", "receipt_retention_ref"))
            and all(type(value) is str for value in asdict(plan.janitor).values()), "invalid-lifecycle-plan")
    require(all(type(r) is RunResource and reference(r.ref) and reference(r.instance_ref)
                and r.kind in ("process", "credential", "file")
                and r.retention in ("run", "retained", "shared") for r in plan.resources)
            and len({r.ref for r in plan.resources}) == len(plan.resources)
            and len({r.instance_ref for r in plan.resources}) == len(plan.resources), "invalid-lifecycle-plan")
    retained = [r for r in plan.resources if r.ref == plan.retained_state_ref]
    require(reference(plan.retained_state_ref) and len(retained) == 1
            and retained[0].retention == "retained" and retained[0].kind == "file", "lifecycle-state-not-retained")


class _Clock:
    def __init__(self, clock, *, deadline=None, checked_at=None):
        self.source, self.deadline, self.last = clock, deadline, checked_at

    def now(self):
        try:
            now = self.source()
            require(integer(now) and (self.last is None or now >= self.last), "lifecycle-clock-unavailable")
        except Exception:
            raise BindingError("lifecycle-clock-unavailable") from None
        require(self.deadline is None or now < self.deadline, "lifecycle-expired")
        self.last = now
        return now


def _lease(record, plan, now, *, active):
    require(type(record) is LeaseReadback and record.plan_digest == plan.digest
            and type(record.scope) is RunScope and record.scope == plan.scope
            and type(record.issued_at) is int and record.issued_at == plan.issued_at
            and type(record.expires_at) is int and record.expires_at == plan.expires_at
            and record.status in ("active", "closed", "revoked", "cancelled"), "lifecycle-lease-mismatch")
    require(integer(record.observed_at) and integer(record.valid_until)
            and record.observed_at <= now < record.valid_until <= record.observed_at + 60,
            "lifecycle-lease-stale")
    if active:
        require(record.status == "active" and record.issued_at <= now < record.expires_at,
                "lifecycle-lease-inactive")


class _Use:
    def __init__(self, lifecycle, *, deadline=None, checked_at=None):
        self.lifecycle = lifecycle
        self.clock = _Clock(lifecycle.runtime_trust.clock, deadline=deadline, checked_at=checked_at)
        self.check()

    def check(self):
        life, before = self.lifecycle, self.clock.now()
        try:
            raw = life.load_config()
        except Exception:
            raise BindingError("runtime-config-unavailable") from None
        current = validate_config(raw, trust=life.runtime_trust)
        require(current.checked_at >= before, "lifecycle-clock-unavailable")
        self.clock.last = current.checked_at
        self.clock.deadline = min(self.clock.deadline or current.valid_until, current.valid_until,
                                  life.plan.expires_at)
        selected, plan = current.selection, life.plan
        expected = RunScope(current.config_digest, selected["case_ref"], selected["launch"]["run_id"],
                            selected["launch"]["run_attempt"], **dict(selected["lifecycle"]))
        require(plan.scope == expected and selected["not_before"] <= plan.issued_at
                and plan.expires_at <= selected["expires_at"], "lifecycle-scope-mismatch")
        check_service(life.janitor, selected["services"]["janitor"], "read_lease")
        require(life.janitor.identity == plan.janitor
                and callable(getattr(life.janitor.target, "finalize", None)), "lifecycle-service-mismatch")
        forbidden = {selected["services"]["worker_channel"]["principal_ref"], plan.janitor.principal_ref}
        require(life.readback.identity.principal_ref not in forbidden
                and life.readback.identity.credential_ref not in (
                    selected["services"]["worker_channel"]["credential_ref"], plan.janitor.credential_ref)
                and plan.janitor.principal_ref != selected["services"]["worker_channel"]["principal_ref"],
                "lifecycle-readback-not-independent")
        require(plan.retained_state_ref == selected["state"]["store_ref"], "lifecycle-state-not-retained")
        self.clock.now()
        try:
            record = life.janitor.target.read_lease(plan.ref, deadline=self.clock.deadline)
        except Exception:
            raise BindingError("lifecycle-lease-unavailable") from None
        _lease(record, plan, self.clock.now(), active=True)
        self.clock.deadline = min(self.clock.deadline, record.valid_until)
        self.clock.now()


class RunLifecycle:
    """One trusted synchronous run; return a value only after verified cleanup.

    Hosting supplies this object to RuntimeBridge and calls run(bridge-operation).
    No operation callback or constructor argument comes from a worker request.
    Expiry/cancellation cleanup also needs an independently scheduled janitor;
    finally cannot run after process death. Cleanup uses its own clock/authority
    and the frozen accepted plan, without requiring live proof configuration.
    """
    def __init__(self, *, plan, load_config, runtime_trust, janitor, readback, cleanup_clock):
        _plan(plan)
        require(type(runtime_trust) is RuntimeTrust and type(janitor) is BoundService
                and type(readback) is BoundService and type(readback.identity) is ServiceIdentity
                and callable(getattr(readback.target, "read_cleanup", None))
                and callable(load_config) and callable(cleanup_clock), "invalid-lifecycle-embedding")
        require(all(reference(getattr(readback.identity, field)) for field in
                    ("service_ref", "principal_ref", "credential_ref"))
                and valid_digest(readback.identity.trust_digest), "invalid-lifecycle-embedding")
        self.plan, self.load_config, self.runtime_trust = plan, load_config, runtime_trust
        self.janitor, self.readback, self.cleanup_clock = janitor, readback, cleanup_clock
        self._lock, self._used, self._active_use = Lock(), False, None
        _Use(self)

    def check_for_use(self, *, deadline, checked_at):
        require(integer(deadline) and integer(checked_at), "invalid-lifecycle-checkpoint")
        with self._lock:
            active = self._active_use
            if active is not None:
                deadline = min(deadline, active.clock.deadline)
                checked_at = max(checked_at, active.clock.last)
        use = _Use(self, deadline=deadline, checked_at=checked_at)
        checkpoint = LifecycleUse(use.clock.deadline, use.clock.last)
        self.retain_use(checkpoint)
        return checkpoint

    def retain_use(self, checkpoint):
        """Trusted return checkpoint handoff with no extra clock sample or I/O."""
        require(type(checkpoint) is LifecycleUse and integer(checkpoint.valid_until)
                and integer(checkpoint.checked_at), "invalid-lifecycle-checkpoint")
        with self._lock:
            active = self._active_use
            if active is not None:
                require(checkpoint.checked_at >= active.clock.last, "lifecycle-clock-unavailable")
                active.clock.last = checkpoint.checked_at
                active.clock.deadline = min(active.clock.deadline, checkpoint.valid_until)

    def finalize(self, outcome):
        require(outcome in ("success", "failure", "cancel"), "invalid-lifecycle-outcome")
        clock = _Clock(self.cleanup_clock)
        started = clock.now()
        attempt = "cleanup-attempt:" + token_hex(16)
        with self._lock:
            floor = started if self._active_use is None else max(started, self._active_use.clock.last)
        clock.deadline = started + self.plan.cleanup_timeout
        failed = False
        try:
            self.janitor.target.finalize(self.plan.ref, deadline=clock.deadline)
        except Exception:
            failed = True
        # Never substitute the cleanup actor's acknowledgement for independent readback.
        try:
            record = self.readback.target.read_cleanup(self.plan.ref, attempt_ref=attempt, deadline=clock.deadline)
            now = clock.now()
            self._verify_cleanup(record, floor, now, attempt)
        except Exception:
            raise BindingError("lifecycle-cleanup-unverified") from None
        require(not failed, "lifecycle-cleanup-unverified")
        return CleanupVerification(self.plan.digest, self.plan.scope, outcome, now)

    def _verify_cleanup(self, record, started, now, attempt):
        require(type(record) is CleanupReadback and type(record.scope) is RunScope
                and record.plan_digest == self.plan.digest and record.scope == self.plan.scope
                and record.attempt_ref == attempt
                and record.lease_status in ("closed", "revoked", "cancelled")
                and integer(record.observed_at) and integer(record.valid_until)
                and started <= record.observed_at <= now < record.valid_until <= record.observed_at + 60
                and type(record.resources) is tuple and len(record.resources) == len(self.plan.resources),
                "lifecycle-cleanup-mismatch")
        require(all(type(r) is ResourceReadback and type(r.present) is bool and type(r.revoked) is bool
                    for r in record.resources), "lifecycle-cleanup-mismatch")
        observed = {r.ref: r for r in record.resources}
        require(len(observed) == len(record.resources), "lifecycle-cleanup-mismatch")
        for selected in self.plan.resources:
            actual = observed.get(selected.ref)
            require(actual is not None and actual.instance_ref == selected.instance_ref, "lifecycle-cleanup-mismatch")
            if selected.retention == "run":
                require(not actual.present and (selected.kind != "credential" or actual.revoked),
                        "lifecycle-cleanup-incomplete")
            else:
                require(actual.present and not actual.revoked, "lifecycle-preserved-resource-changed")

    def run(self, operation):
        require(callable(operation), "invalid-lifecycle-operation")
        with self._lock:
            require(not self._used, "lifecycle-run-already-used")
            self._used = True
        outcome = "failure"
        try:
            use = _Use(self)
            with self._lock:
                self._active_use = use
            result = operation()
            use.check()
            outcome = "success"
        except BaseException as error:
            outcome = "failure" if isinstance(error, Exception) else "cancel"
            self.finalize(outcome)
            if isinstance(error, Exception):
                raise BindingError("lifecycle-operation-failed") from None
            raise
        verification = self.finalize(outcome)
        require(verification.checked_at >= use.clock.last, "lifecycle-clock-unavailable")
        use.clock.last = verification.checked_at
        use.clock.now()
        return result


class RunJanitor:
    """Independent service logic over protected durable provider registrations.

    cleanup(expected_resource, deadline=epoch) must conditionally revoke/remove
    that exact generation and owner, never resolve an arbitrary worker path.
    read_lease/finalize peers come from authenticated transport. sweep is a local
    scheduler capability, never exposed on the worker/gate request plane.
    """
    def __init__(self, *, plan, allowed_gate, load_plan, load_lease, load_resource, close_lease, cleanup, clock):
        _plan(plan)
        require(type(allowed_gate) is JanitorPeer and reference(allowed_gate.principal_ref)
                and reference(allowed_gate.credential_ref) and all(callable(c) for c in
                    (load_plan, load_lease, load_resource, close_lease, cleanup, clock)), "invalid-janitor-embedding")
        self.allowed_gate, self.load_plan, self.load_lease = allowed_gate, load_plan, load_lease
        self.load_resource, self.close_lease, self.cleanup, self.clock = load_resource, close_lease, cleanup, clock
        self.plan = plan

    def _peer(self, peer):
        require(type(peer) is JanitorPeer and peer == self.allowed_gate, "janitor-peer-denied")

    def _selected(self, ref, deadline):
        require(reference(ref) and integer(deadline), "invalid-janitor-request")
        require(ref == self.plan.ref, "janitor-plan-mismatch")
        clock = _Clock(self.clock, deadline=deadline)
        clock.deadline = min(deadline, clock.now() + self.plan.cleanup_timeout)
        clock.now()
        try:
            plan = self.load_plan(ref, deadline=clock.deadline)
        except Exception:
            raise BindingError("janitor-plan-unavailable") from None
        _plan(plan)
        require(plan.digest == self.plan.digest and plan.ref == ref
                and plan.janitor.principal_ref == self.allowed_gate.principal_ref
                and plan.janitor.credential_ref == self.allowed_gate.credential_ref, "janitor-plan-mismatch")
        clock.now()
        return plan, clock

    def read_lease(self, ref, *, peer, deadline):
        self._peer(peer)
        plan, clock = self._selected(ref, deadline)
        try:
            record = self.load_lease(ref, deadline=clock.deadline)
        except Exception:
            raise BindingError("janitor-lease-unavailable") from None
        _lease(record, plan, clock.now(), active=False)
        return record

    def finalize(self, ref, *, peer, deadline):
        self._peer(peer)
        plan, clock = self._selected(ref, deadline)
        self._cleanup(plan, clock)

    def sweep(self, ref, *, deadline):
        plan, clock = self._selected(ref, deadline)
        record = self.load_lease(ref, deadline=clock.deadline)
        now = clock.now()
        _lease(record, plan, now, active=False)
        require(record.status != "active" or now >= record.expires_at, "janitor-lease-still-active")
        self._cleanup(plan, clock)

    def _cleanup(self, plan, clock):
        failed = False
        try:
            self.close_lease(plan.ref, deadline=clock.deadline)
            clock.now()
        except Exception:
            failed = True
        for resource in plan.resources:
            if resource.retention != "run":
                continue
            try:
                clock.now()
                actual = self.load_resource(resource.ref, deadline=clock.deadline)
                clock.now()
                require(type(actual) is ManagedResource and type(actual.resource) is RunResource
                        and actual.resource == resource and actual.owner_scope_digest == digest(asdict(plan.scope)),
                        "janitor-resource-not-owned")
                self.cleanup(actual, deadline=clock.deadline)
                clock.now()
            except Exception:
                failed = True
        require(not failed, "janitor-cleanup-failed")
