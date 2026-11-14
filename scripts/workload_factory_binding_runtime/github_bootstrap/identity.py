"""Separate bootstrap-purpose verification; protected proof policy is untouched."""
from dataclasses import dataclass
from types import MappingProxyType
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from workload_factory_binding.evidence import (BindingError, CLAIMS, RUN_CLAIMS, decode64,
    decode_object, integer, reference, require)
from ..issuer import IssuerKeySource
from .._https_worker import ISSUER
from . import ERROR
from .common import number, SHA

BOOTSTRAP_AUDIENCE = "urn:opensoft:openxfactory:bootstrap-admission:v1"
BASE_CLAIMS = (CLAIMS - {"environment"}) | RUN_CLAIMS | {"event_name"}

@dataclass(frozen=True, repr=False)
class IdentityPolicy:
    phase: str
    audience: str
    proof_audience: str
    expected: object

    def __post_init__(self):
        require(self.phase in ("preflight", "protected") and reference(self.audience)
                and reference(self.proof_audience) and self.audience != self.proof_audience, ERROR)
        required = BASE_CLAIMS | ({"environment"} if self.phase == "protected" else set())
        require(type(self.expected) is dict and set(self.expected) == required
                and all(reference(x) for x in self.expected.values()), ERROR)
        expected = dict(self.expected)
        require(expected["event_name"] == "workflow_dispatch" and expected["ref"] == "refs/heads/main"
                and all(number(expected[k]) for k in ("repository_id", "repository_owner_id", "run_id", "run_attempt"))
                and expected["run_attempt"] == "1"
                and all(SHA.fullmatch(expected[k]) and expected[k] != "0" * 40 for k in
                        ("sha", "workflow_sha", "job_workflow_sha"))
                and expected["sha"] == expected["workflow_sha"] == expected["job_workflow_sha"], ERROR)
        object.__setattr__(self, "expected", MappingProxyType(expected))

@dataclass(frozen=True, repr=False)
class BootstrapIdentity:
    claims: object
    valid_until: int
    phase: str

class BootstrapVerifier:
    def __init__(self, source):
        require(isinstance(source, IssuerKeySource), ERROR)
        self.source = source

    def verify(self, token, policy, *, now):
        try:
            require(type(policy) is IdentityPolicy and integer(now) and type(token) is str
                    and len(token) <= 16384, ERROR)
            parts = token.split(".")
            require(len(parts) == 3, ERROR)
            header, claims = (decode_object(decode64(x)) for x in parts[:2])
            require({"alg", "kid", "typ"} <= set(header) <= {"alg", "kid", "typ", "x5t"}
                    and header["alg"] == "RS256" and header["typ"] == "JWT"
                    and reference(header["kid"]), ERROR)
            if "x5t" in header:
                import re
                require(type(header["x5t"]) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", header["x5t"]), ERROR)
            snapshot = self.source._for_key(header["kid"], now)
            checked = self.source._current(snapshot, now)
            key = snapshot.keys[header["kid"]]
            rsa.RSAPublicNumbers(int.from_bytes(decode64(key["e"]), "big"),
                                 int.from_bytes(decode64(key["n"]), "big")).public_key().verify(
                decode64(parts[2]), (parts[0] + "." + parts[1]).encode("ascii"),
                padding.PKCS1v15(), hashes.SHA256())
            require(claims.get("iss") == ISSUER and type(claims.get("aud")) is str
                    and claims["aud"] == policy.audience
                    and all(type(claims.get(k)) is str and claims[k] == v for k, v in policy.expected.items())
                    and (policy.phase != "preflight" or "environment" not in claims)
                    and reference(claims.get("jti")), ERROR)
            after = self.source._current(snapshot, checked)
            require(all(integer(claims.get(k)) for k in ("iat", "nbf", "exp"))
                    and claims["nbf"] <= after and claims["iat"] <= checked <= after < claims["exp"]
                    and 0 < claims["exp"] - claims["iat"] <= 300
                    and after < claims["iat"] + 60, ERROR)
            return BootstrapIdentity(MappingProxyType(claims),
                min(claims["exp"], claims["iat"] + 60, snapshot.expires_at), policy.phase)
        except Exception:
            raise BindingError(ERROR) from None
