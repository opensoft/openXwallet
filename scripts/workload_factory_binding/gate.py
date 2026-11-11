"""Current factory authority composed with injected owning wallet proof APIs."""
from copy import deepcopy
from datetime import datetime, timezone

from .evidence import (
    BindingError, CLAIMS, byte_digest, canonical, decode64, digest, integer,
    reference, require, valid_digest, verify_observation,
)

BINDING_REFS = ("binding_ref", "wallet_ref", "key_ref", "subject_ref", "custody_ref")
POLICY_FIELDS = frozenset(("schema_version", "profile", "policy_ref", "revision",
                          "not_before", "expires_at", "claims", "binding", "grant_ref",
                          "wallet", "grants", "composition_digest", "supervisor_public_key"))
REQUEST_FIELDS = frozenset(("act", "object_ref", "run_id", "run_attempt"))


def request_digest(policy, request):
    require(type(request) is dict and set(request) == REQUEST_FIELDS
            and all(reference(v) for v in request.values()), "invalid-request")
    require(all(request[k].isascii() and request[k].isdigit() and int(request[k]) > 0
                for k in ("run_id", "run_attempt")), "invalid-request")
    return digest({
        "profile": "openxfactory-workload-request-candidate-v0",
        "policy_ref": policy["policy_ref"], "policy_revision": policy["revision"],
        "binding": policy["binding"], "grant_ref": policy["grant_ref"],
        "composition_digest": policy["composition_digest"], "request": request,
    })


def _time(value):
    require(type(value) is str and value.endswith("Z"), "invalid-grant")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        stamp = parsed.timestamp()
        require(parsed.utcoffset() == timezone.utc.utcoffset(parsed)
                and stamp.is_integer() and stamp >= 0, "invalid-grant")
        return int(stamp)
    except (ValueError, OverflowError):
        raise BindingError("invalid-grant") from None


def _members(value):
    require(type(value) is list and 0 < len(value) <= 64
            and all(reference(v) for v in value) and len(set(value)) == len(value),
            "invalid-grant")
    return set(value)


def _policy(policy, now):
    require(type(policy) is dict and set(policy) == POLICY_FIELDS
            and type(policy["schema_version"]) is int and policy["schema_version"] == 1
            and policy["profile"] == "openxfactory-workload-binding-candidate-v0"
            and reference(policy["policy_ref"]) and integer(policy["revision"])
            and policy["revision"] > 0 and integer(policy["not_before"])
            and integer(policy["expires_at"])
            and policy["not_before"] <= now < policy["expires_at"], "inactive-policy")
    claims = policy["claims"]
    require(type(claims) is dict and set(claims) == CLAIMS
            and all(reference(v) for v in claims.values()), "invalid-workload-policy")
    for key in ("repository_id", "repository_owner_id"):
        require(claims[key].isascii() and claims[key].isdigit()
                and int(claims[key]) > 0, "invalid-workload-policy")
    for key in ("sha", "workflow_sha", "job_workflow_sha"):
        require(len(claims[key]) == 40 and all(c in "0123456789abcdef" for c in claims[key]),
                "invalid-workload-policy")
    require(valid_digest(policy["composition_digest"]), "invalid-policy")
    binding = policy["binding"]
    require(type(binding) is dict
            and set(binding) == set(BINDING_REFS) | {"binding_revision", "public_key_digest"}
            and all(reference(binding[k]) for k in BINDING_REFS)
            and integer(binding["binding_revision"]) and binding["binding_revision"] > 0
            and valid_digest(binding["public_key_digest"]), "invalid-policy")
    require(reference(policy["grant_ref"]) and type(policy["grants"]) is dict
            and 0 < len(policy["grants"]) <= 64
            and len(canonical(policy)) <= 262144, "invalid-policy")
    require(len(decode64(policy["supervisor_public_key"])) == 32, "invalid-supervisor-key")
    wallet = policy["wallet"]
    require(type(wallet) is dict and set(wallet) == {
                "schema_version", "kind", "wallet_id", "holder", "key_reference",
                "custody", "state", "created_at", "policy_version"}
            and type(wallet.get("schema_version")) is int
            and wallet["schema_version"] == 1
            and wallet.get("kind") == "xfactory_wallet_record" and wallet.get("state") == "active"
            and wallet.get("wallet_id") == binding["wallet_ref"], "wallet-mismatch")
    holder, custody, key = (wallet.get(k) for k in ("holder", "custody", "key_reference"))
    require(type(holder) is dict and set(holder) == {"holder_id", "holder_class", "display_label"}
            and holder.get("holder_class") == "agent"
            and holder.get("holder_id") == binding["subject_ref"]
            and type(custody) is dict and set(custody) == {
                "model", "registry_version", "declared_at", "declared_by"}
            and custody.get("model") == "isolated_per_use_authorized"
            and type(key) is dict and set(key) == {
                "did", "key_id", "public_key_multibase", "signature_algorithm"}
            and key.get("key_id") == binding["key_ref"]
            and key.get("signature_algorithm") == "ed25519"
            and reference(key.get("did")) and reference(custody.get("declared_by"))
            and integer(custody.get("registry_version")) and custody["registry_version"] > 0
            and integer(wallet.get("policy_version")) and wallet["policy_version"] > 0
            and _time(wallet.get("created_at")) <= now
            and _time(custody.get("declared_at")) <= now, "wallet-mismatch")


def _wallet_public_key(encoded):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    require(reference(encoded) and encoded.startswith("z") and len(encoded) <= 64,
            "wallet-key-mismatch")
    value = 0
    for character in encoded[1:]:
        require(character in alphabet, "wallet-key-mismatch")
        value = value * 58 + alphabet.index(character)
    payload = encoded[1:]
    raw = bytes([0]) * (len(payload) - len(payload.lstrip("1")))
    raw += value.to_bytes((value.bit_length() + 7) // 8, "big")
    require(len(raw) == 34 and raw[:2] == bytes.fromhex("ed01"), "wallet-key-mismatch")
    return raw[2:]



def _chain(policy, request, now):
    """Narrow same-wallet act-only projection of the existing grant vocabulary."""
    chain, seen, child = [], set(), None
    grant_ref = policy["grant_ref"]
    while grant_ref is not None:
        require(reference(grant_ref) and grant_ref not in seen and len(chain) < 16,
                "invalid-grant-chain")
        seen.add(grant_ref)
        grant = policy["grants"].get(grant_ref)
        require(type(grant) is dict and set(grant) <= {
                    "schema_version", "kind", "grant_id", "audience", "scope",
                    "issued_at", "expires_at", "issued_by", "state", "parent_grant_ref"}
                and type(grant.get("schema_version")) is int
                and grant["schema_version"] == 1 and grant.get("kind") == "xfactory_wallet_grant"
                and grant.get("grant_id") == grant_ref and grant.get("state") == "active"
                and reference(grant.get("issued_by")), "inactive-grant")
        issued, expires = _time(grant.get("issued_at")), _time(grant.get("expires_at"))
        require(issued <= now < expires, "inactive-grant")
        require(grant.get("audience") == {
            "wallet_ref": policy["binding"]["wallet_ref"],
            "holder_ref": policy["binding"]["subject_ref"]}, "grant-audience-mismatch")
        scope = grant.get("scope")
        require(type(scope) is dict
                and set(scope) == {"acts", "objects", "authority_tier", "approval_posture"}
                and scope.get("authority_tier") == "act", "unsupported-authority")
        acts, objects = _members(scope["acts"]), _members(scope["objects"])
        posture = scope["approval_posture"]
        require(type(posture) is dict and set(posture) == {
            "hermes_approval_required_before_apply", "authority_agents_may_approve",
            "human_escalation_required_for"}
            and posture["hermes_approval_required_before_apply"] is True
            and posture["authority_agents_may_approve"] is False
            and type(posture["human_escalation_required_for"]) is list
            and all(reference(v) for v in posture["human_escalation_required_for"]),
            "approval-posture-refused")
        human = set(posture["human_escalation_required_for"])
        if child is not None:
            require(child["acts"] <= acts and child["objects"] <= objects
                    and child["expires"] <= expires and child["issued"] >= issued
                    and human <= child["human"], "delegation-widened")
        require(request["act"] in acts and request["object_ref"] in objects,
                "scope-refused")
        chain.append(grant_ref)
        child = {"acts": acts, "objects": objects, "issued": issued,
                 "expires": expires, "human": human}
        grant_ref = grant.get("parent_grant_ref")
    return chain


class ProofGate:
    """Trusted embedding only. Workers cannot choose any constructor dependency."""
    def __init__(self, *, load_policy, workload_verifier, registry, load_challenge,
                 ledger, signer, create_proof, clock):
        require(all(callable(v) for v in (load_policy, load_challenge, create_proof, clock))
                and callable(getattr(registry, "resolve", None))
                and callable(getattr(signer, "sign", None))
                and callable(getattr(ledger, "reserve", None))
                and callable(getattr(workload_verifier, "verify", None)),
                "invalid-gate-configuration")
        self.load_policy, self.workload_verifier = load_policy, workload_verifier
        self.registry, self.load_challenge = registry, load_challenge
        self.ledger, self.signer, self.create_proof, self.clock = ledger, signer, create_proof, clock

    def _validate(self, challenge_id, request, token, observation):
        now = self.clock()
        require(integer(now) and reference(challenge_id), "invalid-request")
        try:
            # Isolate this use from loader-owned mutable records.
            policy = deepcopy(self.load_policy())
            _policy(policy, now)
            expected_digest = request_digest(policy, request)
            challenge = self.load_challenge(challenge_id)
            require(challenge.id == challenge_id and reference(challenge.issuer)
                    and challenge.subject_ref == policy["binding"]["subject_ref"]
                    and integer(challenge.issued_at) and integer(challenge.expires_at)
                    and challenge.issued_at <= now < challenge.expires_at
                    and challenge.expires_at <= challenge.issued_at + 120
                    and challenge.request_digest == expected_digest
                    and valid_digest(challenge.digest), "challenge-mismatch")
            claims = self.workload_verifier.verify(
                token, {**policy["claims"], **{k: request[k] for k in ("run_id", "run_attempt")}},
                now=now)
            binding = self.registry.resolve(policy["binding"]["subject_ref"], now=now)
            require(all(getattr(binding, k) == policy["binding"][k] for k in BINDING_REFS)
                    and type(binding.revision) is int
                    and binding.revision == policy["binding"]["binding_revision"]
                    and type(binding.public_key) is bytes and len(binding.public_key) == 32
                    and byte_digest(binding.public_key) == policy["binding"]["public_key_digest"]
                    and binding.revoked is False and integer(binding.not_before)
                    and integer(binding.expires_at)
                    and binding.not_before <= now < binding.expires_at,
                    "registry-binding-mismatch")
            require(_wallet_public_key(policy["wallet"]["key_reference"]["public_key_multibase"])
                    == binding.public_key, "wallet-key-mismatch")
            require(decode64(policy["supervisor_public_key"]) != binding.public_key,
                    "supervisor-not-independent")
            chain = _chain(policy, request, now)
            verify_observation(observation, policy=policy, request=request, token=token,
                               challenge=challenge, claims=claims, now=now)
            return policy, binding, challenge, claims, chain, now
        except BindingError:
            raise
        except Exception:
            raise BindingError("trusted-input-unavailable") from None

    def sign(self, challenge_id, request, token, observation):
        # Copy untrusted mutable containers once so no thread can change the
        # checked request/observation while opaque custody is running.
        try:
            request, observation = deepcopy(request), deepcopy(observation)
        except Exception:
            raise BindingError("invalid-request") from None
        policy, binding, challenge, claims, chain, now = self._validate(
            challenge_id, request, token, observation)
        self.ledger.reserve(issuer=self.workload_verifier.issuer, jti=claims["jti"],
                            challenge_issuer=challenge.issuer, challenge_id=challenge.id, now=now)
        try:
            proof = self.create_proof(challenge.digest, binding, self.signer, now=now)
        except Exception:
            raise BindingError("signer-unavailable") from None
        current = self._validate(challenge_id, request, token, observation)
        require(current[1] == binding and current[2] == challenge
                and digest(current[0]) == digest(policy), "authority-changed")
        return {
            "proof": proof,
            "authority": {"actor_ref": binding.subject_ref, "wallet_ref": binding.wallet_ref,
                          "key_ref": binding.key_ref, "grant_chain": chain,
                          "act": request["act"], "object_ref": request["object_ref"],
                          "request_digest": challenge.request_digest},
            "assurance": "possession", "human_approval": False,
        }
