"""Current canonical inputs through operator-selected authenticated connectors.

BoundService is an embedding capability, not a wire format or proof of isolation.
Its identity must come from the authenticated connector's protected configuration,
not candidate/worker data. Connectors authenticate peers, bound I/O and return
current bytes. No URL, credential or callback is accepted from a worker request.
"""
from dataclasses import asdict, dataclass

from workload_factory_binding.evidence import (
    BindingError, CLAIMS, decode_object, digest, integer, reference, require, valid_digest,
)
from workload_factory_binding.gate import _chain, _policy, _time, request_digest


@dataclass(frozen=True, repr=False)
class ServiceIdentity:
    service_ref: str
    principal_ref: str
    credential_ref: str
    trust_digest: str


@dataclass(frozen=True, repr=False)
class BoundService:
    identity: ServiceIdentity
    target: object


def check_service(service, selected, method):
    require(type(service) is BoundService and type(service.identity) is ServiceIdentity,
            "runtime-service-binding-mismatch")
    values = asdict(service.identity)
    require(all(type(v) is str for v in values.values()) and values == dict(selected)
            and callable(getattr(service.target, method, None)), "runtime-service-binding-mismatch")


@dataclass(frozen=True)
class CurrentChallenge:
    """Existing factory challenge projection; no new neutral challenge protocol."""
    id: str
    issuer: str
    subject_ref: str
    issued_at: int
    expires_at: int
    request_digest: str

    @property
    def digest(self):
        return digest(asdict(self))


class CurrentLoaders:
    """One per proof use. The gate reloads policy/challenge after signing."""
    def __init__(self, *, use, records, challenge, request):
        self.use, self.records, self.challenge = use, records, challenge
        self.request, self._policy = request, None

    def _read(self, role, service, operation, selected_ref):
        raw = self.use.service_call(role, service, "read", operation, selected_ref,
                                    deadline=self.use.valid_until)
        try:
            return decode_object(raw)
        except Exception:
            raise BindingError("invalid-runtime-service-data") from None

    def load_policy(self):
        selected = self.use.selection
        authority = selected["authority"]
        policy = self._read("records", self.records, "policy", authority["policy_ref"])
        _policy(policy, self.use.clock())
        require(digest(policy) == authority["policy_digest"]
                and policy["policy_ref"] == authority["policy_ref"]
                and policy["revision"] == authority["policy_revision"]
                and policy["grant_ref"] == authority["grant_ref"]
                and policy["composition_digest"] == selected["composition_digest"]
                and policy["claims"] == {name: selected["launch"][name] for name in CLAIMS}
                and all(policy["binding"][name] == authority[name] for name in
                        ("subject_ref", "wallet_ref", "key_ref", "custody_ref")),
                "runtime-policy-mismatch")
        chain = _chain(policy, self.request, self.use.clock())
        self.use.limit(min(policy["expires_at"], *(_time(policy["grants"][ref]["expires_at"]) for ref in chain)))
        self._policy = policy
        return policy

    def load_challenge(self, challenge_id):
        require(self._policy is not None and reference(challenge_id), "runtime-challenge-unavailable")
        record = self._read("challenge", self.challenge, "challenge", challenge_id)
        require(set(record) == {"id", "issuer", "subject_ref", "issued_at", "expires_at", "request_digest"},
                "invalid-runtime-challenge")
        now, selected = self.use.clock(), self.use.selection
        require(record["id"] == challenge_id and reference(record["issuer"])
                and record["issuer"] == selected["services"]["challenge"]["service_ref"]
                and record["subject_ref"] == selected["authority"]["subject_ref"]
                and integer(record["issued_at"]) and integer(record["expires_at"])
                and record["issued_at"] <= now < record["expires_at"] <= record["issued_at"] + 120
                and valid_digest(record["request_digest"])
                and record["request_digest"] == request_digest(self._policy, self.request),
                "runtime-challenge-mismatch")
        self.use.limit(record["expires_at"])
        return CurrentChallenge(**record)
