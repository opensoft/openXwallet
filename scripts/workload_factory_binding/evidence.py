"""Strict offline workload verification and a bounded reference artifact observer."""
import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
import rfc8785

CLAIMS = frozenset(("repository", "repository_id", "repository_owner",
                    "repository_owner_id", "environment", "sub", "ref", "sha",
                    "workflow_ref", "workflow_sha", "job_workflow_ref", "job_workflow_sha"))
RUN_CLAIMS = frozenset(("run_id", "run_attempt"))
OBS_CONTEXT = b"openxfactory-workload-observation-candidate-v0\n"
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


class BindingError(ValueError):
    """Fixed refusal codes only; evidence and credentials are never interpolated."""


def require(condition, code):
    if not condition:
        raise BindingError(code)


def integer(value):
    return type(value) is int and 0 <= value <= 2**53 - 1


def reference(value):
    return (type(value) is str and 0 < len(value) <= 512 and value == value.strip()
            and not any(ord(c) < 33 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF
                        or c in "*?[]" for c in value))


def canonical(value):
    try:
        return rfc8785.dumps(value)
    except (ValueError, TypeError, RecursionError):
        raise BindingError("invalid-data") from None


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def byte_digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def encode64(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def decode64(value):
    require(type(value) is str and 0 < len(value) <= 24000, "invalid-encoding")
    require(re.fullmatch(r"[A-Za-z0-9_-]+", value) is not None, "invalid-encoding")
    try:
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except ValueError:
        raise BindingError("invalid-encoding") from None
    require(encode64(raw) == value, "invalid-encoding")
    return raw


def decode_object(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 16384, "invalid-data")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate-member")
            result[key] = value
        return result

    def constant(_value):
        raise BindingError("invalid-data")

    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError):
        raise BindingError("invalid-data") from None
    require(type(result) is dict, "invalid-data")
    return result


def valid_digest(value):
    return type(value) is str and DIGEST.fullmatch(value) is not None


@dataclass(frozen=True)
class WorkloadEvidence:
    """Verified claims plus the independent administrative key-snapshot deadline."""
    claims: dict
    valid_until: int


class WorkloadVerifier:
    """Trust snapshot loader is administrative, never selected by a token.

    Snapshot: {expires_at: epoch, keys: [public RSA JWK, ...]}.
    Refresh/authenticity belong to the embedding. No networking is performed.
    """
    def __init__(self, *, issuer, audience, load_keys):
        require(issuer == "https://token.actions.githubusercontent.com"
                and reference(audience) and callable(load_keys), "invalid-issuer-configuration")
        self.issuer, self.audience, self.load_keys = issuer, audience, load_keys

    def verify(self, token, expected, *, now):
        require(integer(now) and type(token) is str and len(token) <= 16384, "invalid-token")
        require(type(expected) is dict and set(expected) == CLAIMS | RUN_CLAIMS
                and all(reference(v) for v in expected.values()), "invalid-workload-policy")
        parts = token.split(".")
        require(len(parts) == 3, "invalid-token")
        header, claims = (decode_object(decode64(part)) for part in parts[:2])
        require({"alg", "kid", "typ"} <= set(header) <= {"alg", "kid", "typ", "x5t"}
                and header["alg"] == "RS256"
                and header["typ"] == "JWT" and reference(header["kid"]), "unsupported-token")
        if "x5t" in header:
            # Documented issuer metadata only. Trust still comes exclusively
            # from the configured key snapshot and signed kid/algorithm.
            require(type(header["x5t"]) is str and 0 < len(header["x5t"]) <= 128
                    and re.fullmatch(r"[A-Za-z0-9_-]+", header["x5t"]) is not None,
                    "unsupported-token")
        try:
            snapshot = self.load_keys()
            require(type(snapshot) is dict and set(snapshot) == {"expires_at", "keys"}
                    and integer(snapshot["expires_at"]) and now < snapshot["expires_at"],
                    "issuer-keys-unavailable")
            keys = snapshot["keys"]
            require(type(keys) is list and 0 < len(keys) <= 16, "issuer-keys-unavailable")
            require(all(type(key) is dict and reference(key.get("kid")) for key in keys),
                    "issuer-keys-unavailable")
            require(len({key["kid"] for key in keys}) == len(keys), "issuer-keys-unavailable")
            matches = [key for key in keys if key["kid"] == header["kid"]]
            require(len(matches) == 1, "unknown-issuer-key")
            key = matches[0]
            require(key.get("kty") == "RSA" and key.get("alg") == "RS256"
                    and key.get("use") == "sig" and key.get("key_ops", ["verify"]) == ["verify"]
                    and not any(k in key for k in ("d", "p", "q", "dp", "dq", "qi")),
                    "invalid-issuer-key")
            modulus = int.from_bytes(decode64(key["n"]), "big")
            exponent = int.from_bytes(decode64(key["e"]), "big")
            require(2048 <= modulus.bit_length() <= 4096 and exponent == 65537,
                    "invalid-issuer-key")
            rsa.RSAPublicNumbers(exponent, modulus).public_key().verify(
                decode64(parts[2]), (parts[0] + "." + parts[1]).encode("ascii"),
                padding.PKCS1v15(), hashes.SHA256())
        except BindingError:
            raise
        except Exception:
            raise BindingError("workload-unverified") from None
        require(claims.get("iss") == self.issuer and claims.get("aud") == self.audience,
                "workload-mismatch")
        require(all(type(claims.get(k)) is str and claims[k] == v for k, v in expected.items()),
                "workload-mismatch")
        require(reference(claims.get("jti")), "invalid-token")
        require(all(integer(claims.get(k)) for k in ("iat", "nbf", "exp"))
                and claims["iat"] <= now < claims["exp"] and claims["nbf"] <= now
                and 0 < claims["exp"] - claims["iat"] <= 300, "inactive-token")
        return WorkloadEvidence(claims, min(claims["exp"], snapshot["expires_at"]))


def artifact_digest(artifacts, configuration):
    """Read fixed supervisor-selected regular files; logical names enter the digest."""
    require(type(artifacts) is dict and 0 < len(artifacts) <= 32
            and all(reference(name) for name in artifacts), "invalid-artifacts")
    measured = {}
    for name, path in artifacts.items():
        try:
            fd = os.open(Path(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                require(stat.S_ISREG(info.st_mode) and info.st_size <= 1024 * 1024,
                        "invalid-artifacts")
                raw = stream.read(1024 * 1024 + 1)
                require(len(raw) <= 1024 * 1024, "invalid-artifacts")
                measured[name] = byte_digest(raw)
        except OSError:
            raise BindingError("artifacts-unavailable") from None
    return digest({"artifacts": measured, "configuration": configuration})


def observation_payload(policy, request, token, challenge, *, now, expires_at, composition):
    return {
        "profile": "openxfactory-workload-observation-candidate-v0",
        "policy_ref": policy["policy_ref"], "policy_revision": policy["revision"],
        "token_digest": byte_digest(token.encode("ascii")),
        "challenge_digest": challenge.digest, "request_digest": challenge.request_digest,
        "composition_digest": composition,
        "subject_ref": policy["binding"]["subject_ref"],
        "wallet_ref": policy["binding"]["wallet_ref"], "key_ref": policy["binding"]["key_ref"],
        "grant_ref": policy["grant_ref"],
        "run_id": request["run_id"], "run_attempt": request["run_attempt"],
        "issued_at": now, "expires_at": expires_at,
    }


def observe_artifacts(*, policy, request, token, challenge, artifacts, configuration,
                      private_key, now, expires_at):
    """Reference helper for a trusted observer; not a worker-callable attestation API."""
    require(integer(now) and integer(expires_at) and now < expires_at <= now + 60,
            "invalid-observation")
    measured = artifact_digest(artifacts, configuration)
    require(measured == policy["composition_digest"], "composition-mismatch")
    payload = observation_payload(policy, request, token, challenge, now=now,
                                  expires_at=expires_at, composition=measured)
    signature = private_key.sign(OBS_CONTEXT + canonical(payload))
    return {"payload": payload, "signature": encode64(signature)}


def verify_observation(observation, *, policy, request, token, challenge, claims, now):
    require(type(observation) is dict and set(observation) == {"payload", "signature"},
            "invalid-observation")
    payload = observation["payload"]
    require(type(payload) is dict, "invalid-observation")
    issued, expires = payload.get("issued_at"), payload.get("expires_at")
    require(integer(issued) and integer(expires) and issued <= now < expires <= issued + 60
            and max(claims["iat"], challenge.issued_at) <= issued
            and expires <= min(claims["exp"], challenge.expires_at, policy["expires_at"]),
            "inactive-observation")
    expected = observation_payload(policy, request, token, challenge, now=issued,
                                   expires_at=expires, composition=policy["composition_digest"])
    require(integer(payload.get("policy_revision")) and canonical(payload) == canonical(expected),
            "observation-mismatch")
    try:
        public = decode64(policy["supervisor_public_key"])
        require(len(public) == 32, "invalid-supervisor-key")
        ed25519.Ed25519PublicKey.from_public_bytes(public).verify(
            decode64(observation["signature"]), OBS_CONTEXT + canonical(payload))
    except (InvalidSignature, ValueError, TypeError):
        raise BindingError("observation-unverified") from None
