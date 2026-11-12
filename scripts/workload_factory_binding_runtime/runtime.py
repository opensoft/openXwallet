"""Opt-in trusted composition of the unchanged proof gate, with per-use preflight.

Hosting supplies authenticated/bounded connector capabilities and worker context.
Python types do not establish an administrative/process boundary. Supervisor,
custody confinement, initialized-state and lifecycle qualification remain separate.
"""
from dataclasses import dataclass
from types import MappingProxyType

from workload_factory_binding import ProofGate
from workload_factory_binding.evidence import (
    BindingError, WorkloadEvidence, canonical, decode_object, integer, reference, require,
)
from workload_factory_binding.gate import REQUEST_FIELDS
from .config import RuntimeTrust, validate_config
from .issuer import IssuerKeySource, IssuerWorkloadVerifier
from .loaders import BoundService, CurrentLoaders, ServiceIdentity, check_service

_METHODS = {"records": "read", "challenge": "read", "registry": "resolve", "custody": "sign"}
_STATE_FIELDS = ("store_ref", "initialization_ref", "retention_ref", "recovery_ref")


@dataclass(frozen=True, repr=False)
class WorkerContext:
    """Authenticated hosting channel metadata, obtained outside worker arguments."""
    identity: ServiceIdentity
    config_digest: str
    case_ref: str
    run_id: str
    run_attempt: str
    issued_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class StateBinding:
    """Selected existing store handle, not evidence of initialization or recovery."""
    store_ref: str
    initialization_ref: str
    retention_ref: str
    recovery_ref: str
    ledger: object


class _Use:
    def __init__(self, bridge):
        self.bridge, self.selection = bridge, None
        self.valid_until, self._last = None, None
        self.check()

    def clock(self):
        try:
            now = self.bridge.trust.clock()
            require(integer(now) and (self._last is None or self._last <= now), "runtime-clock-unavailable")
        except Exception:
            raise BindingError("runtime-clock-unavailable") from None
        require(self.valid_until is None or now < self.valid_until, "runtime-use-expired")
        self._last = now
        return now

    def limit(self, expires_at):
        require(integer(expires_at), "runtime-use-expired")
        self.valid_until = min(self.valid_until, expires_at)
        self.clock()

    def check(self):
        before = self.clock()
        try:
            raw = self.bridge.load_config()
        except Exception:
            raise BindingError("runtime-config-unavailable") from None
        current = validate_config(raw, trust=self.bridge.trust)
        require(current.checked_at >= before, "runtime-clock-unavailable")
        self.selection = current.selection
        self.valid_until = (current.valid_until if self.valid_until is None
                            else min(self.valid_until, current.valid_until))
        self._last = current.checked_at
        try:
            context = self.bridge.load_worker_context()
        except Exception:
            raise BindingError("runtime-channel-unavailable") from None
        now = self.clock()
        require(type(context) is WorkerContext and type(context.identity) is ServiceIdentity,
                "runtime-channel-unverified")
        # An authenticated connector supplies metadata; body booleans are never consulted.
        channel = BoundService(context.identity, self.bridge)
        check_service(channel, self.selection["services"]["worker_channel"], "load_worker_context")
        launch = self.selection["launch"]
        require(context.config_digest == current.config_digest
                and context.case_ref == self.selection["case_ref"]
                and context.run_id == launch["run_id"] and context.run_attempt == launch["run_attempt"]
                and integer(context.issued_at) and integer(context.expires_at)
                and context.issued_at <= now < context.expires_at <= context.issued_at + 60,
                "runtime-channel-mismatch")
        self.valid_until = min(self.valid_until, context.expires_at)
        self.clock()

    def check_dependencies(self):
        for role, method in _METHODS.items():
            check_service(self.bridge.services[role], self.selection["services"][role], method)
        self.check_state()

    def check_state(self):
        state = self.bridge.state
        require(type(state) is StateBinding
                and all(type(getattr(state, name)) is str
                        and getattr(state, name) == self.selection["state"][name] for name in _STATE_FIELDS)
                and callable(getattr(state.ledger, "reserve", None)), "runtime-state-binding-mismatch")

    def guarded(self, operation, *args, **kwargs):
        self.check()
        self.check_dependencies()
        try:
            result = operation(*args, **kwargs)
        except Exception:
            raise BindingError("runtime-service-unavailable") from None
        self.check()
        self.check_dependencies()
        return result

    def service_call(self, role, service, method, *args, **kwargs):
        check_service(service, self.selection["services"][role], method)
        return self.guarded(getattr(service.target, method), *args, **kwargs)


class _Verifier:
    def __init__(self, use, source):
        self.use = use
        self.verifier = IssuerWorkloadVerifier(audience=use.selection["issuer"]["audience"], source=source)
        self.issuer = self.verifier.issuer

    def verify(self, token, expected, *, now):
        self.use.check()
        require(expected == dict(self.use.selection["launch"]), "runtime-launch-mismatch")
        evidence = self.verifier.verify(token, expected, now=max(now, self.use.clock()))
        self.use.limit(evidence.valid_until)
        self.use.check()
        return WorkloadEvidence(evidence.claims, min(evidence.valid_until, self.use.valid_until))


class _Registry:
    def __init__(self, use):
        self.use = use

    def resolve(self, subject_ref, *, now):
        binding = self.use.service_call("registry", self.use.bridge.services["registry"], "resolve", subject_ref, now=now)
        self.use.limit(getattr(binding, "expires_at", None))
        return binding


class _Signer:
    def __init__(self, use):
        self.use = use

    def sign(self, message):
        return self.use.service_call("custody", self.use.bridge.services["custody"], "sign", message)


class _Ledger:
    def __init__(self, use):
        self.use = use

    def reserve(self, **kwargs):
        return self.use.guarded(self.use.bridge.state.ledger.reserve, **kwargs)


def _worker_inputs(challenge_id, request, token, observation):
    require(reference(challenge_id) and type(token) is str and 0 < len(token) <= 16384
            and type(request) is dict and set(request) == REQUEST_FIELDS
            and all(reference(value) for value in request.values()), "invalid-runtime-request")
    require(type(observation) is dict and set(observation) == {"payload", "signature"}
            and type(observation["signature"]) is str and len(observation["signature"]) <= 128,
            "invalid-runtime-request")
    payload = observation["payload"]
    require(type(payload) is dict and len(payload) <= 32
            and all(type(name) is str and len(name) <= 128 for name in payload)
            and all((type(value) is str and len(value) <= 1024) or integer(value)
                    for value in payload.values()), "invalid-runtime-request")
    require(integer(payload.get("expires_at")), "invalid-runtime-request")
    # Bounded flat values can now be copied without worker-owned mutable containers.
    return dict(request), decode_object(canonical(observation))


class RuntimeBridge:
    """Trusted embedding only. Worker input remains the four accepted gate arguments.

    Service connectors own authentication and bounded I/O. Their identities and
    the channel callback must never be synthesized from a worker body. State is
    pre-provisioned by hosting; this class never creates/reset stores or credentials.
    One issuer source is shared across uses; selection preflight is never cached.
    """
    def __init__(self, *, load_config, trust, load_worker_context, services, state,
                 issuer_source, create_proof):
        require(type(trust) is RuntimeTrust and type(services) is dict and set(services) == set(_METHODS)
                and isinstance(issuer_source, IssuerKeySource)
                and all(callable(value) for value in (load_config, load_worker_context, create_proof)),
                "invalid-runtime-embedding")
        self.load_config, self.trust, self.load_worker_context = load_config, trust, load_worker_context
        self.services, self.state = MappingProxyType(dict(services)), state
        self.issuer_source, self.create_proof = issuer_source, create_proof

    def sign(self, challenge_id, request, token, observation):
        request, observation = _worker_inputs(challenge_id, request, token, observation)
        use = _Use(self)
        use.check_dependencies()
        # An unverified worker deadline may only shorten this use. The unchanged
        # gate still verifies the entire signed observation before reservation.
        use.limit(observation["payload"]["expires_at"])
        require(all(request[name] == use.selection["launch"][name] for name in ("run_id", "run_attempt")),
                "runtime-launch-mismatch")
        verifier = _Verifier(use, self.issuer_source)
        # Reject the wrong workload before current-record/challenge service access.
        verifier.verify(token, dict(use.selection["launch"]), now=use.clock())
        loaders = CurrentLoaders(use=use, records=self.services["records"], challenge=self.services["challenge"],
                                 request=request)
        def create_proof(*args, **kwargs):
            return use.guarded(self.create_proof, *args, **kwargs)
        gate = ProofGate(load_policy=loaders.load_policy, workload_verifier=verifier, registry=_Registry(use),
                         load_challenge=loaders.load_challenge, ledger=_Ledger(use), signer=_Signer(use),
                         create_proof=create_proof, clock=use.clock)
        result = gate.sign(challenge_id, request, token, observation)
        use.check()
        return result
