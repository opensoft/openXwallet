"""One trusted qualification operation, real owning verification and existing cleanup.

No resolver, signer authority, service initialization or worker-selectable plugin.
Private observation slots are filled only at existing successful checks. Operational
origin additionally requires an independently selected operator signature over the
exact observed run/phase/generation/issuance, not a Python type or live/body flag.
"""
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from threading import Lock
from types import MappingProxyType

from workload_factory_binding.evidence import (BindingError, WorkloadEvidence, byte_digest, canonical,
    decode64, decode_object, digest, integer, require)
from ..config import ValidatedConfig
from ..custody import CustodyAccess
from ..issuer import IssuerWorkloadVerifier
from ..runtime import RuntimeBridge
from ..workflow import WorkflowBindings, WorkflowContext
from .finalization import FinalizedPlan, admit_finalized
from .readback import ReadBudget
from ..github_bootstrap.common import Decision
from .evidence import CaseObservation, PROOF_FIELDS

_RESULT_SEAL = object()


def _binding_digest(binding):
    value = asdict(binding)
    value["public_key"] = byte_digest(binding.public_key)
    return digest(value)


class ProofTrace:
    """Bounded, per-call private observation; never a serialized assertion."""
    __slots__ = ("used", "selected", "workload", "issuer_source", "registry", "challenge",
                 "access", "reservation", "preimage")
    def __init__(self):
        self.used = False
        self.selected = self.workload = self.issuer_source = self.registry = None
        self.challenge = self.access = self.reservation = self.preimage = None


@dataclass(frozen=True, repr=False)
class BarrierInputs:
    """Already selected valid-signed negative capabilities, never a signer API."""
    audience_token: str
    environment_token: str


@dataclass(frozen=True, repr=False)
class WorkerProbe:
    """Existing clients and an optional disposable excess-policy control.

    The same loaded worker credential must sign the same accepted preimage at
    the separately selected control endpoint. Without that control the denial
    remains incomplete. No production permission or owning protocol is changed.
    """
    worker: object
    positive: object
    excess: object = None

    def check(self, message, binding, *, now, decision):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from openwallet_runtime.custody import TLSClient
        from .probe_io import exchange
        require(type(self.worker) is TLSClient and type(self.positive) is TLSClient
                and type(message) is bytes and 0 < len(message) <= 8192, "qualification-failed")
        def call(client, kind):
            return exchange(client, kind, message=message, binding=binding, now=now, decision=decision)
        call(self.worker, "resolve")
        signature = call(self.positive, "sign")
        key = Ed25519PublicKey.from_public_bytes(binding.public_key)
        key.verify(signature, message)
        call(self.worker, "deny")
        if self.excess is None:
            return None
        require(type(self.excess) is TLSClient and self.excess.context is self.worker.context
                and (self.excess.host, self.excess.port) != (self.worker.host, self.worker.port),
                "qualification-failed")
        control = call(self.excess, "sign")
        key.verify(control, message)
        return digest({"preimage_digest": byte_digest(message), "binding_digest": _binding_digest(binding),
            "positive_signature_digest": byte_digest(signature), "excess_signature_digest": byte_digest(control),
            "denial": "http403-service-refused"})


ORIGIN_CONTEXT = b"openxfactory/runtime-report-origin/internal-v1\x00"


@dataclass(frozen=True, repr=False)
class OriginTrust:
    """Existing operator/readback authentication, selected outside worker input.

    This introduces no signing API, listener or runtime role. load(ref, deadline)
    must independently obtain existing factual run observations; it receives only
    the registered plan reference, never a caller's candidate facts to countersign.
    Operational keys/transport/actual hosting selection remain T013 prerequisites.
    Fixture roots are explicitly fixture-scoped and cannot authorize protected scope.
    """
    principal_ref: str
    public_key: bytes
    scope: str
    load: object


def _origin(raw, *, trust, principal, expected, now):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        require(type(trust) is OriginTrust and trust.principal_ref == principal
                and type(trust.public_key) is bytes and len(trust.public_key) == 32
                and trust.scope in ("isolated-fixture", "protected-machine"), "protected-report-refused")
        require(type(raw) is bytes and 0 < len(raw) <= 4096, "protected-report-refused")
        frame = decode_object(raw)
        require(set(frame) == {"payload", "signature"} and type(frame["payload"]) is dict,
                "protected-report-refused")
        value = frame["payload"]
        require(set(value) == {*expected, "principal_ref", "scope", "observed_at", "expires_at"}
                and all(value[k] == v for k, v in expected.items())
                and value["principal_ref"] == principal and value["scope"] == trust.scope
                and integer(value["observed_at"]) and integer(value["expires_at"])
                and value["observed_at"] <= now < value["expires_at"] <= value["observed_at"] + 60,
                "protected-report-refused")
        Ed25519PublicKey.from_public_bytes(trust.public_key).verify(
            decode64(frame["signature"]), ORIGIN_CONTEXT + canonical(value))
        return value["scope"], digest(value), value["expires_at"]
    except Exception:
        raise BindingError("protected-report-refused") from None


@dataclass(frozen=True, repr=False)
class QualificationBindings:
    selected: ValidatedConfig
    finalized: FinalizedPlan
    context: WorkflowContext
    workflow: WorkflowBindings
    bridge: RuntimeBridge
    decision: Decision
    barriers: BarrierInputs | None = None
    worker_probe: WorkerProbe | None = None
    origin: OriginTrust | None = None


@dataclass(frozen=True, repr=False)
class QualificationResult:
    selected: ValidatedConfig
    plan: object
    cleanup: object
    started_at: int
    operation_floor: int
    outcome: str
    phase_provenance_digest: str
    generation_digest: str
    issuance_digest: str
    cases: tuple
    proof: object
    _seal: object
    _operational_origin: object

    def _projection(self, now):
        return {name: getattr(self, name) for name in ("selected", "plan", "cleanup", "started_at",
            "operation_floor", "outcome", "phase_provenance_digest", "generation_digest", "issuance_digest",
            "cases")} | {"now": now, "proof": dict(self.proof)}

    def fixture_receipt(self, *, now):
        """Honest old-profile fixture output, without protected/H/live promotion."""
        from ..evidence import CASES, CaseResult, build_receipt
        require(self._seal is _RESULT_SEAL and self._operational_origin is None, "protected-report-refused")
        cases = tuple(CaseResult(c.case_id, 1, int(c.status == "passed"), int(c.status == "failed"), 0, 0,
                                 c.observed_at, c.artifact_digest) for c in self.cases if c.case_id in CASES)
        # Old profile retains its original all-case-before-cleanup ordering.
        if self.outcome == "success":
            error = None
        elif self.outcome == "cancel":
            error = BindingError("qualification-cancelled")
        else:
            error = BindingError("qualification-failed")
        return build_receipt(scope="isolated-fixture", selected=self.selected, cases=cases,
            started_at=self.started_at, now=now, plan=self.plan, cleanup=self.cleanup,
            error=error)


def _is_workload_mismatch(error):
    """One exact fixed-code refusal invariant for both signed-claim barriers."""
    return (type(error) is BindingError and len(error.args) == 1
            and type(error.args[0]) is str and error.args[0] == "workload-mismatch")


def _barrier(token, kind, bridge, now, selected, inputs):
    # First establish a signature-valid single-claim counterfactual. The payload
    # is untrusted until this independent verification has succeeded.
    require(type(token) is str and 0 < len(token) <= 16384 and token.count(".") == 2,
            "qualification-failed")
    claims = decode_object(decode64(token.split(".")[1]))
    expected = dict(selected.selection["launch"])
    audience = selected.selection["issuer"]["audience"]
    if kind == "audience":
        require(type(claims.get("aud")) is str and claims["aud"] != audience, "qualification-failed")
        counter_audience, counter_expected = claims["aud"], expected
    else:
        require(type(claims.get("environment")) is str and claims["environment"] != expected["environment"],
                "qualification-failed")
        counter_audience, counter_expected = audience, {**expected, "environment": claims["environment"]}
    valid = IssuerWorkloadVerifier(audience=counter_audience, source=bridge.issuer_source).verify(
        token, counter_expected, now=now)
    # All other workload claims remain independently constrained; an invalid
    # signature/outage/expiry is not equivalent to the exact claim refusal.
    try:
        IssuerWorkloadVerifier(audience=audience, source=bridge.issuer_source).verify(token, expected, now=now)
    except BindingError as error:
        require(_is_workload_mismatch(error), "qualification-failed")
    else:
        raise BindingError("qualification-failed")
    negative = ProofTrace()
    try:
        bridge.sign_observed(inputs[0], inputs[1], token, inputs[3], trace=negative)
    except BindingError as error:
        require(_is_workload_mismatch(error) and negative.reservation is None,
                "qualification-failed")
    else:
        raise BindingError("qualification-failed")
    return digest({"kind": kind, "token_digest": byte_digest(token.encode()),
                   "verified_claims_digest": digest(dict(valid.claims)), "refusal": "workload-mismatch"})


class RegisteredCleanupClient:
    """One audit-only read over an original authenticated registration.

    Trusted hosting selects the immutable plan/context and existing observer TLS
    client. No active config, operation grant, writer or RunLifecycle is needed.
    The service binds the returned plan and original cleanup_until/timeout.
    """
    __slots__ = ("_selected", "_lock", "_used")

    @property
    def context(self):
        return self._selected[0]

    def __init__(self, *, context, plan, audit, identity, clock, monotonic):
        from ..lifecycle import _plan
        from ..loaders import ServiceIdentity
        from .lifecycle_service import LifecycleClient
        require(type(context) is WorkflowContext and type(audit) is LifecycleClient
                and type(identity) is ServiceIdentity and callable(clock) and callable(monotonic),
                "lifecycle-cleanup-unverified")
        require(all(type(getattr(context, name)) is str for name in context.__dataclass_fields__),
                "lifecycle-cleanup-unverified")
        _plan(plan)
        from ..config import _handle
        from workload_factory_binding.evidence import valid_digest
        for field in ("service_ref", "principal_ref", "credential_ref"):
            _handle(getattr(identity, field))
        require(valid_digest(identity.trust_digest), "lifecycle-cleanup-unverified")
        scope = decode_object(audit.raw)
        require({"case_ref", "run_id", "run_attempt", "source_commit"} <= set(scope),
                "lifecycle-cleanup-unverified")
        require(context.config_digest == plan.scope.config_digest
                and scope["case_ref"] == plan.scope.case_ref
                and scope["run_id"] == plan.scope.run_id == context.run_id
                and scope["run_attempt"] == plan.scope.run_attempt == context.run_attempt
                and scope["source_commit"] == context.source_commit
                and audit.principal == identity.principal_ref
                and identity.principal_ref != plan.janitor.principal_ref
                and identity.credential_ref != plan.janitor.credential_ref,
                "lifecycle-cleanup-unverified")
        self._selected = (context, plan, audit, identity, clock, monotonic)
        self._lock, self._used = Lock(), False

    def reconcile_cleanup(self):
        from secrets import token_hex
        from ..lifecycle import CleanupVerification, verify_cleanup_record
        from .lifecycle import HostedLifecycle
        from .lifecycle_service import _final_cleanup_record
        with self._lock:
            require(not self._used, "lifecycle-cleanup-unverified")
            self._used = True
            _context, plan, audit, identity, clock, monotonic = self._selected
        try:
            decision = Decision(clock=clock, monotonic=monotonic)
            before = decision.now()
            HostedLifecycle.narrow(decision, before + plan.cleanup_timeout)
            attempt = "cleanup-attempt:" + token_hex(16)
            value = audit.call("cleanup-audit", attempt_ref=attempt, decision=decision)
            record = _final_cleanup_record(value)
            now = decision.now()
            verify_cleanup_record(plan, record, before, now, attempt)
        except Exception:
            raise BindingError("lifecycle-cleanup-unverified") from None
        # An audit alone does not establish the dead operation's success.
        return CleanupVerification(plan.digest, plan.scope, "cancel", now,
            record.observed_at, record.valid_until, digest(asdict(record)),
            digest(asdict(identity)), digest(attempt))


class _QualificationAttempt:
    """Facts accumulated by one operation and its independent cleanup observation."""

    def __init__(self, bindings, inputs, verify_proof):
        self.bindings = bindings
        self.inputs = inputs
        self.verify_proof = verify_proof
        self.life = bindings.workflow.lifecycle
        self.selected = bindings.selected
        self.trace = ProofTrace()
        self.started = bindings.decision.last
        require(integer(self.started), "qualification-failed")
        self.observations = []
        self.proof = {"status": "not-performed"}
        self.phase = None
        self.issuance = digest({"status": "not-performed"})
        self.outcome, self.floor = "failure", self.started
        self.failure = self.cancelled = None
        self.origin_scope = self.origin_digest = None

    def _record(self, name, value):
        self.observations.append(CaseObservation(name, self.bindings.decision.now(), digest(value), "passed"))

    def _proof_values(self, accepted):
        b, trace = self.bindings, self.trace
        require(trace.selected.config_digest == self.selected.config_digest and trace.reservation == "reserved"
                and type(trace.access) is CustodyAccess and type(trace.workload) is WorkloadEvidence,
                "qualification-failed")
        verified = self.verify_proof(accepted["proof"], expected_digest=trace.challenge.digest,
                                    binding=trace.registry, now=b.decision.now())
        require(verified.subject_ref == trace.registry.subject_ref, "qualification-failed")
        self.issuance = digest(asdict(trace.access))
        # Replay the exact accepted inputs while the original lease is active.
        replay = ProofTrace()
        try:
            b.bridge.sign_observed(*self.inputs, trace=replay)
        except BindingError:
            require(replay.reservation == "replay-refused", "qualification-failed")
        else:
            raise BindingError("qualification-failed")
        return {"accepted_proof_digest": digest(accepted["proof"]),
            "verification_digest": digest({"subject_ref": verified.subject_ref,
                "challenge_digest": trace.challenge.digest, "binding_digest": _binding_digest(trace.registry)}),
            "replay_refusal_digest": digest({"proof_digest": digest(accepted["proof"]), "refusal": replay.reservation})}

    def _observe_proof(self, values):
        b, trace = self.bindings, self.trace
        if b.barriers is not None:
            require(type(b.barriers) is BarrierInputs, "qualification-failed")
            for kind in ("audience", "environment"):
                values[kind + "_barrier_digest"] = _barrier(getattr(b.barriers, kind + "_token"),
                    kind, b.bridge, b.decision.now(), self.selected, self.inputs)
        if b.worker_probe is not None:
            require(type(b.worker_probe) is WorkerProbe and type(trace.preimage) is bytes,
                    "qualification-failed")
            denial = b.worker_probe.check(trace.preimage, trace.registry,
                now=b.decision.now(), decision=b.decision)
            if denial is not None:
                values["worker_denial_digest"] = denial
                self._record("G03", {"worker_denial_digest": denial})
        if set(values) == set(PROOF_FIELDS):
            self.proof = {"status": "verified", **values}
            self._record("H10", values)

    def _observe_origin(self):
        b = self.bindings
        require(type(b.origin) is OriginTrust and callable(b.origin.load), "protected-report-refused")
        phase_value = digest({"admission": asdict(self.phase), "finalization": asdict(b.finalized.binding),
            "readback_digest": self.selected.readback_digest,
            "workload_digest": digest(dict(self.trace.workload.claims))})
        expected = {"config_digest": self.selected.config_digest,
            "case_digest": digest(self.selected.selection["case_ref"]),
            "run_id": b.context.run_id, "run_attempt": b.context.run_attempt,
            "phase_provenance_digest": phase_value,
            "generation_digest": b.finalized.binding.generation_digest,
            "issuance_digest": self.issuance, "plan_digest": self.life.plan.digest}
        ReadBudget(b.decision).consume("private")
        before = b.decision.now()
        raw = b.origin.load(self.life.plan.ref, deadline=b.decision.deadline)
        now = b.decision.now()
        self.origin_scope, self.origin_digest, expiry = _origin(raw, trust=b.origin,
            principal=b.workflow.runtime_trust.readback_principal, expected=expected, now=now)
        require(before <= decode_object(raw)["payload"]["observed_at"], "protected-report-refused")
        b.decision.clip(expiry)

    def operation(self):
        b, selected = self.bindings, self.selected
        try:
            require(selected.config_digest == b.finalized.binding.config_digest == b.context.config_digest
                    and self.life.plan.scope.config_digest == selected.config_digest, "qualification-failed")
            self.phase = admit_finalized(b.finalized, b.context, bindings=b.workflow)
            b.decision.clip(self.phase.valid_until)
            require(self.phase.config_digest == selected.config_digest, "qualification-failed")
            accepted = b.bridge.sign_observed(*self.inputs, trace=self.trace)
            self._observe_proof(self._proof_values(accepted))
            if b.origin is not None:
                self._observe_origin()
            self.floor = b.decision.now()
            self.outcome = "success"
            return accepted
        except BaseException as error:
            self.floor = max(self.floor, b.decision.last)
            self._record_outcome(error)
            self.proof = {"status": "failed"}
            raise

    def _record_lifecycle_failure(self, _kind, error, _traceback):
        if error is None:
            return False
        self.failure = error
        self._record_outcome(error)
        return True

    def _record_outcome(self, error):
        if isinstance(error, Exception):
            self.outcome = "failure"
        else:
            self.outcome, self.cancelled = "cancel", error

    def run_lifecycle(self):
        # Keep the outcome available for independent post-cleanup observation.
        # The caller propagates the saved cancellation after building the result.
        with ExitStack() as lifecycle:
            lifecycle.push(self._record_lifecycle_failure)
            self.life.run(self.operation)

    def _record_privacy_failure(self, now, error):
        if error is None:
            return False
        self.observations.append(CaseObservation("H12", now, digest({"privacy": "refused"}), "failed"))
        if self.failure is None:
            self.failure = error
        if not isinstance(error, Exception):
            self.outcome = "cancel"
            if self.cancelled is None:
                self.cancelled = error
        elif self.outcome != "cancel":
            self.outcome = "failure"
        return True

    def report(self):
        b, selected, trace = self.bindings, self.selected, self.trace
        cleanup = self.life.cleanup_verification
        # Use the independent historical clock for post-cleanup facts.
        now = self.life.cleanup_clock()
        require(integer(now) and now >= self.floor, "qualification-failed")
        if cleanup is not None:
            require(now >= cleanup.checked_at, "qualification-failed")
            self.observations.append(CaseObservation("H11", now, digest(asdict(cleanup)), "passed"))
            self.observations.append(CaseObservation("L01", cleanup.observed_at, digest(asdict(cleanup)), "passed"))
        # Observe the pre-report projection without hashing the report into itself.
        from .privacy import observe_privacy
        with ExitStack() as privacy_observation:
            privacy_observation.push(lambda _kind, error, _tb: self._record_privacy_failure(now, error))
            privacy = observe_privacy({"config_digest": selected.config_digest, "proof": self.proof,
                "cleanup_digest": None if cleanup is None else digest(asdict(cleanup))})
            self.observations.append(CaseObservation("H12", now, privacy, "passed"))
        operational = self.origin_scope == "protected-machine" and self.origin_digest is not None
        phase_digest = digest({"admission": None if self.phase is None else asdict(self.phase),
            "finalization": asdict(b.finalized.binding), "readback_digest": selected.readback_digest,
            "workload_digest": None if trace.workload is None else digest(dict(trace.workload.claims))})
        return QualificationResult(selected, self.life.plan, cleanup, self.started, self.floor, self.outcome,
            self.origin_digest or phase_digest, b.finalized.binding.generation_digest, self.issuance,
            tuple(self.observations), MappingProxyType(self.proof), _RESULT_SEAL, _RESULT_SEAL if operational else None)


class Qualifier:
    """One operation inside the supplied lifecycle; no hidden budget or retry."""
    def __init__(self, bindings, *, challenge_id, request, token, observation):
        require(type(bindings) is QualificationBindings and type(bindings.bridge) is RuntimeBridge
                and type(bindings.selected) is ValidatedConfig and type(bindings.finalized) is FinalizedPlan
                and type(bindings.context) is WorkflowContext and type(bindings.workflow) is WorkflowBindings
                and type(bindings.decision) is Decision and bindings.bridge.lifecycle is bindings.workflow.lifecycle
                and bindings.bridge.lifecycle is not None, "qualification-failed")
        from .lifecycle_service import FinalLifecyclePorts
        ports = bindings.workflow.lifecycle.janitor.target
        if type(ports) is FinalLifecyclePorts:
            require(bindings.decision is ports.operation, "qualification-failed")
        self.bindings = bindings
        self.inputs = (challenge_id, decode_object(canonical(request)), token, decode_object(canonical(observation)))
        self._lock, self._used, self.result = Lock(), False, None
        self._cleanup_client = None

    def run(self):
        from openwallet_runtime.proof import verify_proof
        with self._lock:
            require(not self._used, "qualification-failed")
            self._used = True
        attempt = _QualificationAttempt(self.bindings, self.inputs, verify_proof)
        attempt.run_lifecycle()
        try:
            self.result = attempt.report()
        except BaseException:
            # A secondary report error cannot replace a saved cancellation.
            if attempt.cancelled is not None:
                raise attempt.cancelled
            raise
        if attempt.cancelled is not None:
            raise attempt.cancelled
        if attempt.failure is not None:
            raise BindingError("qualification-failed") from None
        return self.result

    def reconcile_cleanup(self):
        """Fresh same-reference independent readback only, never cleanup resend."""
        from secrets import token_hex
        from ..lifecycle import CleanupVerification
        life = self.bindings.workflow.lifecycle
        from .lifecycle_service import FinalLifecyclePorts
        target = life.readback.target
        if type(target) is FinalLifecyclePorts:
            with self._lock:
                if self._cleanup_client is None:
                    self._cleanup_client = RegisteredCleanupClient(context=self.bindings.context,
                        plan=life.plan, audit=target.audit, identity=life.readback.identity,
                        clock=target.clock, monotonic=target.monotonic)
                client = self._cleanup_client
            checked = client.reconcile_cleanup()
            from dataclasses import replace
            return replace(checked, outcome=self.result.outcome if self.result is not None else "cancel")
        before = life.cleanup_clock()
        require(integer(before), "qualification-failed")
        deadline = min(before + life.plan.cleanup_timeout, life.plan.expires_at + life.plan.cleanup_timeout)
        require(before < deadline, "qualification-failed")
        attempt = "cleanup-attempt:" + token_hex(16)
        try:
            record = target.read_cleanup(life.plan.ref, attempt_ref=attempt, deadline=deadline)
            now = life.cleanup_clock()
            require(integer(now) and before <= now < deadline, "qualification-failed")
            floor = max(before, self.result.operation_floor if self.result is not None else before)
            life._verify_cleanup(record, floor, now, attempt)
        except Exception:
            raise BindingError("lifecycle-cleanup-unverified") from None
        return CleanupVerification(life.plan.digest, life.plan.scope,
            self.result.outcome if self.result is not None else "cancel", now,
            record.observed_at, record.valid_until, digest(asdict(record)),
            digest(asdict(life.readback.identity)), digest(attempt))
