"""One trusted qualification operation, real owning verification and existing cleanup.

No resolver, signer authority, service initialization or worker-selectable plugin.
Private observation slots are filled only at existing successful checks. Operational
origin additionally requires an independently selected operator signature over the
exact observed run/phase/generation/issuance, not a Python type or live/body flag.
"""
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
        import base64
        import http.client
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from openwallet_runtime.custody import TLSClient, RemoteRegistry, RemoteSigner
        require(type(self.worker) is TLSClient and type(self.positive) is TLSClient
                and type(message) is bytes and 0 < len(message) <= 8192, "qualification-failed")
        def call(operation):
            ReadBudget(decision).consume("private")
            decision.now()
            value = operation()
            decision.now()
            return value
        actual = call(lambda: RemoteRegistry(self.worker).resolve(binding.subject_ref, now=now))
        require(actual == binding, "qualification-failed")
        signature = call(lambda: RemoteSigner(self.positive, subject_ref=binding.subject_ref).sign(message))
        key = Ed25519PublicKey.from_public_bytes(binding.public_key)
        key.verify(signature, message)
        # The neutral client collapses all HTTP errors. Inspect the existing wire
        # response directly so a 500, redirect or malformed body is never denial.
        def denied():
            client = self.worker
            connection = http.client.HTTPSConnection(client.host, client.port,
                context=client.context, timeout=min(client.timeout, decision.remaining()))
            try:
                connection.request("POST", "/v0/sign", body=canonical({"subject_ref": binding.subject_ref,
                    "message": base64.urlsafe_b64encode(message).decode()}),
                    headers={"Content-Type": "application/json", "Accept": "application/json"})
                response = connection.getresponse()
                raw = response.read(8193)
                require(response.status == 403 and response.getheader("Content-Type") == "application/json"
                        and len(raw) <= 8192 and decode_object(raw) == {"error": "service-refused"},
                        "qualification-failed")
            finally:
                connection.close()
        call(denied)
        if self.excess is None:
            return None
        require(type(self.excess) is TLSClient and self.excess.context is self.worker.context
                and (self.excess.host, self.excess.port) != (self.worker.host, self.worker.port),
                "qualification-failed")
        control = call(lambda: RemoteSigner(self.excess, subject_ref=binding.subject_ref).sign(message))
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
        return build_receipt(scope="isolated-fixture", selected=self.selected, cases=cases,
            started_at=self.started_at, now=now, plan=self.plan, cleanup=self.cleanup,
            error=None if self.outcome == "success" else BindingError("qualification-" +
                ("cancelled" if self.outcome == "cancel" else "failed")))


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
        require(type(error) is BindingError and len(error.args) == 1 and type(error.args[0]) is str
                and error.args[0] == "workload-mismatch", "qualification-failed")
    else:
        raise BindingError("qualification-failed")
    negative = ProofTrace()
    try:
        bridge.sign_observed(inputs[0], inputs[1], token, inputs[3], trace=negative)
    except BindingError as error:
        require(type(error) is BindingError and len(error.args) == 1 and type(error.args[0]) is str
                and error.args[0] == "workload-mismatch" and negative.reservation is None,
                "qualification-failed")
    else:
        raise BindingError("qualification-failed")
    return digest({"kind": kind, "token_digest": byte_digest(token.encode()),
                   "verified_claims_digest": digest(dict(valid.claims)), "refusal": "workload-mismatch"})


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

    def run(self):
        from openwallet_runtime.proof import verify_proof
        with self._lock:
            require(not self._used, "qualification-failed")
            self._used = True
        b, trace = self.bindings, ProofTrace()
        life, selected = b.workflow.lifecycle, b.selected
        started = b.decision.last
        require(integer(started), "qualification-failed")
        observations, proof, phase = [], {"status": "not-performed"}, None
        issuance = digest({"status": "not-performed"})
        outcome, floor, cancelled = "failure", started, None
        origin_scope, origin_digest = None, None
        def record(name, value, status="passed"):
            observations.append(CaseObservation(name, b.decision.now(), digest(value), status))
        def operation():
            nonlocal phase, issuance, proof, outcome, floor, cancelled, origin_scope, origin_digest
            try:
                require(selected.config_digest == b.finalized.binding.config_digest == b.context.config_digest
                        and life.plan.scope.config_digest == selected.config_digest, "qualification-failed")
                phase = admit_finalized(b.finalized, b.context, bindings=b.workflow)
                b.decision.clip(phase.valid_until)
                require(phase.config_digest == selected.config_digest, "qualification-failed")
                accepted = b.bridge.sign_observed(*self.inputs, trace=trace)
                require(trace.selected.config_digest == selected.config_digest and trace.reservation == "reserved"
                        and type(trace.access) is CustodyAccess and type(trace.workload) is WorkloadEvidence,
                        "qualification-failed")
                verified = verify_proof(accepted["proof"], expected_digest=trace.challenge.digest,
                                        binding=trace.registry, now=b.decision.now())
                require(verified.subject_ref == trace.registry.subject_ref, "qualification-failed")
                issuance = digest(asdict(trace.access))
                # Exact accepted inputs are replayed while their original lease is
                # active. Capture the underlying atomic reservation's exact refusal.
                replay = ProofTrace()
                try:
                    b.bridge.sign_observed(*self.inputs, trace=replay)
                except BindingError:
                    require(replay.reservation == "replay-refused", "qualification-failed")
                else:
                    raise BindingError("qualification-failed")
                values = {"accepted_proof_digest": digest(accepted["proof"]),
                    "verification_digest": digest({"subject_ref": verified.subject_ref,
                        "challenge_digest": trace.challenge.digest, "binding_digest": _binding_digest(trace.registry)}),
                    "replay_refusal_digest": digest({"proof_digest": digest(accepted["proof"]), "refusal": replay.reservation})}
                if b.barriers is not None:
                    require(type(b.barriers) is BarrierInputs, "qualification-failed")
                    for kind in ("audience", "environment"):
                        values[kind + "_barrier_digest"] = _barrier(getattr(b.barriers, kind + "_token"),
                            kind, b.bridge, b.decision.now(), selected, self.inputs)
                if b.worker_probe is not None:
                    require(type(b.worker_probe) is WorkerProbe and type(trace.preimage) is bytes,
                            "qualification-failed")
                    denial = b.worker_probe.check(trace.preimage, trace.registry,
                        now=b.decision.now(), decision=b.decision)
                    if denial is not None:
                        values["worker_denial_digest"] = denial
                        record("G03", {"worker_denial_digest": denial})
                if set(values) == set(PROOF_FIELDS):
                    proof = {"status": "verified", **values}
                    record("H10", values)
                if b.origin is not None:
                    require(type(b.origin) is OriginTrust and callable(b.origin.load), "protected-report-refused")
                    phase_value = digest({"admission": asdict(phase), "finalization": asdict(b.finalized.binding),
                        "readback_digest": selected.readback_digest,
                        "workload_digest": digest(dict(trace.workload.claims))})
                    expected = {"config_digest": selected.config_digest,
                        "case_digest": digest(selected.selection["case_ref"]),
                        "run_id": b.context.run_id, "run_attempt": b.context.run_attempt,
                        "phase_provenance_digest": phase_value,
                        "generation_digest": b.finalized.binding.generation_digest,
                        "issuance_digest": issuance, "plan_digest": life.plan.digest}
                    ReadBudget(b.decision).consume("private")
                    before = b.decision.now()
                    raw = b.origin.load(life.plan.ref, deadline=b.decision.deadline)
                    now = b.decision.now()
                    origin_scope, origin_digest, expiry = _origin(raw, trust=b.origin,
                        principal=b.workflow.runtime_trust.readback_principal, expected=expected, now=now)
                    require(before <= decode_object(raw)["payload"]["observed_at"], "protected-report-refused")
                    b.decision.clip(expiry)
                floor = b.decision.now()
                outcome = "success"
                return accepted
            except BaseException as error:
                floor = max(floor, b.decision.last)
                outcome = "failure" if isinstance(error, Exception) else "cancel"
                if outcome == "cancel":
                    cancelled = error
                proof = {"status": "failed"}
                raise
        failure = None
        try:
            life.run(operation)
        except BaseException as error:
            failure = error
            outcome = "failure" if isinstance(error, Exception) else "cancel"
            if not isinstance(error, Exception):
                cancelled = error
        cleanup = life.cleanup_verification
        # Read an independent historical clock only; do not renew the original
        # Decision to encode post-cleanup privacy facts.
        now = life.cleanup_clock()
        require(integer(now) and now >= floor, "qualification-failed")
        if cleanup is not None:
            require(now >= cleanup.checked_at, "qualification-failed")
            observations.append(CaseObservation("H11", now, digest(asdict(cleanup)), "passed"))
            observations.append(CaseObservation("L01", cleanup.observed_at, digest(asdict(cleanup)), "passed"))
        # A closed projection alone does not execute independent privacy controls.
        # H12 therefore remains unperformed in this partial runtime composition.
        # Origin is established by the selected operator's actual signature over
        # these exact observations. A genuine issuer token or transport class by
        # itself cannot upgrade an isolated fixture/control-plane observation.
        operational = origin_scope == "protected-machine" and origin_digest is not None
        phase_digest = digest({"admission": None if phase is None else asdict(phase),
            "finalization": asdict(b.finalized.binding), "readback_digest": selected.readback_digest,
            "workload_digest": None if trace.workload is None else digest(dict(trace.workload.claims))})
        self.result = QualificationResult(selected, life.plan, cleanup, started, floor, outcome,
            origin_digest or phase_digest, b.finalized.binding.generation_digest, issuance, tuple(observations),
            MappingProxyType(proof), _RESULT_SEAL, _RESULT_SEAL if operational else None)
        if cancelled is not None:
            raise cancelled
        if failure is not None:
            raise BindingError("qualification-failed") from None
        return self.result


    def reconcile_cleanup(self):
        """Fresh same-reference independent readback only, never cleanup resend."""
        from secrets import token_hex
        from ..lifecycle import CleanupVerification
        life = self.bindings.workflow.lifecycle
        before = life.cleanup_clock()
        require(integer(before), "qualification-failed")
        deadline = min(before + life.plan.cleanup_timeout, life.plan.expires_at + life.plan.cleanup_timeout)
        require(before < deadline, "qualification-failed")
        attempt = "cleanup-attempt:" + token_hex(16)
        try:
            target = life.readback.target
            from .lifecycle_service import FinalLifecyclePorts
            audit = target.audit_cleanup if type(target) is FinalLifecyclePorts else target.read_cleanup
            record = audit(life.plan.ref, attempt_ref=attempt, deadline=deadline)
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
