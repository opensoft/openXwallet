"""Selected independent observer composition; no public server or deployment claim."""
from dataclasses import dataclass
from types import MappingProxyType

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from workload_factory_binding.evidence import (
    BindingError, OBS_CONTEXT, byte_digest, canonical, decode_object, encode64,
    integer, observation_payload, reference, require, verify_observation,
)
from workload_factory_binding.gate import REQUEST_FIELDS
from .config import RuntimeTrust, validate_config
from .issuer import IssuerKeySource, IssuerWorkloadVerifier
from .launch import ProcessLaunch, worker_configuration
from .loaders import CurrentLoaders, check_service
from .runtime import RuntimeBridge, _Use, _Verifier


@dataclass(frozen=True, repr=False)
class SupervisorPeer:
    """Transport-authenticated peer metadata; never taken from the request body."""
    principal_ref: str
    credential_ref: str
    issued_at: int
    expires_at: int


def _request(payload):
    require(type(payload) is dict and set(payload) == {"challenge_id", "request", "token"},
            "invalid-supervisor-request")
    challenge_id, request, token = (payload[name] for name in ("challenge_id", "request", "token"))
    require(reference(challenge_id) and type(token) is str and 0 < len(token) <= 16384
            and type(request) is dict and set(request) == REQUEST_FIELDS
            and all(reference(value) for value in request.values()), "invalid-supervisor-request")
    return challenge_id, dict(request), token


class _ObservationUse:
    def __init__(self, observer, peer, deadline):
        require(type(peer) is SupervisorPeer
                and (peer.principal_ref, peer.credential_ref) == observer.allowed_gate,
                "supervisor-peer-denied")
        self.observer, self.peer = observer, peer
        self.valid_until, self._last, self._config_digest = deadline, None, None
        self.selection = None
        self.check()

    def clock(self):
        try:
            now = self.observer.trust.clock()
            require(integer(now) and (self._last is None or self._last <= now), "supervisor-clock-unavailable")
        except Exception:
            raise BindingError("supervisor-clock-unavailable") from None
        require(integer(self.valid_until) and now < self.valid_until, "supervisor-expired")
        self._last = now
        return now

    def limit(self, deadline):
        require(integer(deadline), "supervisor-expired")
        self.valid_until = min(self.valid_until, deadline)
        self.clock()

    def check(self):
        before = self.clock()
        try:
            raw = self.observer.load_config()
        except Exception:
            raise BindingError("supervisor-config-unavailable") from None
        current = validate_config(raw, trust=self.observer.trust)
        require(current.checked_at >= before
                and (self._config_digest is None or current.config_digest == self._config_digest),
                "supervisor-config-changed")
        self._config_digest, self.selection = current.config_digest, current.selection
        self.limit(current.valid_until)
        peer, now = self.peer, self.clock()
        selected = self.selection["services"]["supervisor"]
        require(type(peer) is SupervisorPeer
                and (peer.principal_ref, peer.credential_ref) == self.observer.allowed_gate
                and self.observer.allowed_gate == (selected["principal_ref"], selected["credential_ref"])
                and peer.principal_ref != self.selection["services"]["worker_channel"]["principal_ref"]
                and peer.credential_ref != self.selection["services"]["worker_channel"]["credential_ref"]
                and integer(peer.issued_at) and integer(peer.expires_at)
                and peer.issued_at <= now < peer.expires_at <= peer.issued_at + 60,
                "supervisor-peer-denied")
        self.limit(peer.expires_at)

    def guarded(self, operation, *args, **kwargs):
        self.check()
        try:
            result = operation(*args, **kwargs)
        except BindingError:
            raise
        except Exception:
            raise BindingError("supervisor-service-unavailable") from None
        self.check()
        return result

    def service_call(self, role, service, method, *args):
        def invoke():
            check_service(service, self.selection["services"][role], method)
            return service.target.read(*args, deadline=self.valid_until)
        return self.guarded(invoke)


class SupervisorObserver:
    """Admin-owned observer/key/policy/measurement dependencies, outside worker RPC.

    An authenticated server must derive SupervisorPeer independently, expose only
    the observation operation to the selected gate, and isolate its admin/key/
    launch control. Same-user fixtures qualify behavior, not that deployment.
    """
    def __init__(self, *, load_config, trust, services, issuer_source, launch, private_key, allowed_gate):
        require(callable(load_config) and type(trust) is RuntimeTrust
                and type(services) is dict and set(services) == {"records", "challenge"}
                and isinstance(issuer_source, IssuerKeySource) and type(launch) is ProcessLaunch
                and isinstance(private_key, Ed25519PrivateKey) and type(allowed_gate) is tuple
                and len(allowed_gate) == 2 and all(reference(value) for value in allowed_gate),
                "invalid-supervisor-configuration")
        self.load_config, self.trust, self.services = load_config, trust, MappingProxyType(dict(services))
        self.issuer_source, self.launch, self._private_key = issuer_source, launch, private_key
        self.allowed_gate = allowed_gate

    def observe(self, payload, *, peer, deadline):
        challenge_id, request, token = _request(payload)
        use = _ObservationUse(self, peer, deadline)
        verifier = IssuerWorkloadVerifier(audience=use.selection["issuer"]["audience"], source=self.issuer_source)
        evidence = verifier.verify(token, dict(use.selection["launch"]), now=use.clock())
        use.limit(evidence.valid_until)
        use.check()
        require(all(request[name] == use.selection["launch"][name] for name in ("run_id", "run_attempt")),
                "supervisor-launch-mismatch")
        loaders = CurrentLoaders(use=use, records=self.services["records"], challenge=self.services["challenge"],
                                 request=request)
        policy, challenge = loaders.load_policy(), loaders.load_challenge(challenge_id)
        public = self._private_key.public_key().public_bytes_raw()
        require(encode64(public) == policy["supervisor_public_key"]
                and byte_digest(public) != policy["binding"]["public_key_digest"], "supervisor-key-mismatch")
        configuration = worker_configuration(use.selection, policy)
        measured = self.launch.measure(configuration, use.selection, deadline=use.valid_until, clock=use.clock)
        require(measured == policy["composition_digest"], "composition-mismatch")
        use.check()
        issued = use.clock()
        payload = observation_payload(policy, request, token, challenge, now=issued,
                                      expires_at=min(issued + 60, use.valid_until), composition=measured)
        observation = {"payload": payload, "signature": encode64(self._private_key.sign(OBS_CONTEXT + canonical(payload)))}
        use.check()
        current_policy, current_challenge = loaders.load_policy(), loaders.load_challenge(challenge_id)
        require(canonical(current_policy) == canonical(policy) and current_challenge == challenge,
                "supervisor-authority-changed")
        final = self.launch.measure(configuration, use.selection, deadline=use.valid_until, clock=use.clock)
        require(final == measured, "launch-measurement-changed")
        use.check()
        verify_observation(observation, policy=policy, request=request, token=token, challenge=challenge,
                           claims=evidence.claims, now=use.clock())
        return observation


class SupervisedBridge:
    """Trusted wrapper acquiring an observation; the accepted four-argument bridge stays intact."""
    def __init__(self, *, bridge, supervisor):
        require(type(bridge) is RuntimeBridge, "invalid-supervised-bridge")
        self.bridge, self.supervisor = bridge, supervisor

    def sign(self, challenge_id, request, token):
        challenge_id, request, token = _request({"challenge_id": challenge_id, "request": request, "token": token})
        use = _Use(self.bridge)
        use.check_dependencies()
        verifier = _Verifier(use, self.bridge.issuer_source)
        evidence = verifier.verify(token, dict(use.selection["launch"]), now=use.clock())
        require(all(request[name] == use.selection["launch"][name] for name in ("run_id", "run_attempt")),
                "supervisor-launch-mismatch")
        loaders = CurrentLoaders(use=use, records=self.bridge.services["records"],
                                 challenge=self.bridge.services["challenge"], request=request)
        policy, challenge = loaders.load_policy(), loaders.load_challenge(challenge_id)
        body = {"challenge_id": challenge_id, "request": request, "token": token}
        def invoke():
            check_service(self.supervisor, use.selection["services"]["supervisor"], "observe")
            return self.supervisor.target.observe(body, deadline=use.valid_until)
        raw = use.guarded(invoke)
        check_service(self.supervisor, use.selection["services"]["supervisor"], "observe")
        try:
            observation = decode_object(raw)
        except Exception:
            raise BindingError("invalid-supervisor-response") from None
        verify_observation(observation, policy=policy, request=request, token=token, challenge=challenge,
                           claims=evidence.claims, now=use.clock())
        require(observation["payload"]["expires_at"] <= use.valid_until, "supervisor-deadline-mismatch")
        use.limit(observation["payload"]["expires_at"])
        return self.bridge.sign(challenge_id, request, token, observation)
