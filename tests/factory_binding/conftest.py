"""Synthetic issuer/operator fixtures. They are never live GitHub evidence."""
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from workload_factory_binding import ProofGate, ReplayLedger, WorkloadVerifier
from workload_factory_binding.evidence import (
    artifact_digest, byte_digest, canonical, digest, encode64, observe_artifacts,
)
from workload_factory_binding.gate import request_digest

ISSUER = "https://token.actions.githubusercontent.com"


@dataclass(frozen=True)
class Binding:
    binding_ref: str
    wallet_ref: str
    key_ref: str
    subject_ref: str
    custody_ref: str
    public_key: bytes
    revision: int
    not_before: int
    expires_at: int
    revoked: bool = False


@dataclass(frozen=True)
class Challenge:
    id: str
    issuer: str
    subject_ref: str
    issued_at: int
    expires_at: int
    request_digest: str

    @property
    def digest(self):
        return digest(self.__dict__)


def timestamp(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat().replace("+00:00", "Z")


def jwk(key, kid="fixture-issuer"):
    numbers = key.public_key().public_numbers()
    return {"kty": "RSA", "alg": "RS256", "use": "sig", "kid": kid,
            "e": encode64(numbers.e.to_bytes(3, "big")),
            "n": encode64(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big"))}


def jwt(key, claims, header=None, raw_claims=None):
    header = header or {"alg": "RS256", "typ": "JWT", "kid": "fixture-issuer"}
    signing = encode64(canonical(header)) + "." + encode64(
        canonical(claims) if raw_claims is None else raw_claims)
    return signing + "." + encode64(key.sign(signing.encode(), padding.PKCS1v15(), hashes.SHA256()))


def multibase(public):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    raw = bytes.fromhex("ed01") + public
    value = int.from_bytes(raw, "big")
    encoded = ""
    while value:
        value, index = divmod(value, 58)
        encoded = alphabet[index] + encoded
    return "z" + encoded


class Harness:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.now = 1794400000
        self.wallet_key, self.supervisor = ed25519.Ed25519PrivateKey.generate(), ed25519.Ed25519PrivateKey.generate()
        self.issuer_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.binding = Binding("binding:qa", "wallet:qa", "key:qa", "agent:qa", "custody:qa",
                               self.wallet_key.public_key().public_bytes_raw(), 1,
                               self.now - 1000, self.now + 1000)
        self.artifact = self.directory / "worker.py"
        self.artifact.write_text("print('fixture worker')\n")
        self.configuration = {"tools": [], "purpose": "isolated-reference-only"}
        self.artifacts = {"worker": str(self.artifact)}
        expected = {
            "repository": "fixture/factory", "repository_id": "123",
            "repository_owner": "fixture", "repository_owner_id": "456",
            "environment": "qa", "sub": "repo:fixture/factory:environment:qa",
            "ref": "refs/heads/main", "sha": "a" * 40,
            "workflow_ref": "fixture/factory/.github/workflows/pilot.yml@refs/heads/main",
            "workflow_sha": "b" * 40,
            "job_workflow_ref": "fixture/trust/.github/workflows/gate.yml@" + "c" * 40,
            "job_workflow_sha": "c" * 40,
        }
        posture = {"hermes_approval_required_before_apply": True,
                   "authority_agents_may_approve": False,
                   "human_escalation_required_for": ["irreversible_external_effect"]}
        grant = {
            "schema_version": 1, "kind": "xfactory_wallet_grant", "grant_id": "grant:root",
            "audience": {"wallet_ref": "wallet:qa", "holder_ref": "agent:qa"},
            "scope": {"acts": ["prove", "inspect"], "objects": ["object:qa", "object:other"],
                      "authority_tier": "act", "approval_posture": posture},
            "issued_at": timestamp(self.now - 500), "expires_at": timestamp(self.now + 600),
            "issued_by": "operator:fixture", "state": "active",
        }
        child = deepcopy(grant)
        child.update(grant_id="grant:child", parent_grant_ref="grant:root",
                     issued_at=timestamp(self.now - 300), expires_at=timestamp(self.now + 300))
        child["scope"]["acts"] = ["prove"]
        child["scope"]["objects"] = ["object:qa"]
        self.policy = {
            "schema_version": 1, "profile": "openxfactory-workload-binding-candidate-v0",
            "policy_ref": "policy:fixture", "revision": 1,
            "not_before": self.now - 500, "expires_at": self.now + 300,
            "claims": expected,
            "binding": {**{k: getattr(self.binding, k) for k in
                          ("binding_ref", "wallet_ref", "key_ref", "subject_ref", "custody_ref")},
                        "binding_revision": 1, "public_key_digest": byte_digest(self.binding.public_key)},
            "grant_ref": "grant:child",
            "wallet": {"schema_version": 1, "kind": "xfactory_wallet_record",
                       "wallet_id": "wallet:qa", "state": "active",
                       "holder": {"holder_id": "agent:qa", "holder_class": "agent", "display_label": "QA fixture"},
                       "custody": {"model": "isolated_per_use_authorized", "registry_version": 1,
                                   "declared_at": timestamp(self.now - 1000), "declared_by": "operator:fixture"},
                       "key_reference": {"key_id": "key:qa", "signature_algorithm": "ed25519",
                                         "did": "did:web:fixture.invalid:qa",
                                         "public_key_multibase": multibase(self.binding.public_key)},
                       "created_at": timestamp(self.now - 1000), "policy_version": 1},
            "grants": {"grant:root": grant, "grant:child": child},
            "composition_digest": artifact_digest(self.artifacts, self.configuration),
            "supervisor_public_key": encode64(self.supervisor.public_key().public_bytes_raw()),
        }
        self.request = {"act": "prove", "object_ref": "object:qa", "run_id": "789", "run_attempt": "1"}
        self.claims = {**expected, "run_id": "789", "run_attempt": "1", "iss": ISSUER,
                       "aud": "factory:qa", "jti": "token:1", "iat": self.now,
                       "nbf": self.now, "exp": self.now + 120}
        self.keys = {"expires_at": self.now + 300, "keys": [jwk(self.issuer_key)]}
        self.calls = 0
        self.fail_signing = False
        self.on_sign = None
        self.reset_evidence()
        self.verifier = WorkloadVerifier(issuer=ISSUER, audience="factory:qa", load_keys=lambda: self.keys)
        self.ledger = ReplayLedger(self.directory / "ledger")
        self.gate = self.make_gate()

    def resolve(self, subject, *, now):
        assert subject == self.binding.subject_ref
        return self.binding

    def sign(self, message):
        self.calls += 1
        if self.on_sign:
            self.on_sign()
        if self.fail_signing:
            raise OSError("synthetic outage")
        return self.wallet_key.sign(message)

    @staticmethod
    def unit_proof(challenge_digest, binding, signer, *, now):
        # Unit seam, not the owning proof wire format; owning integration is separate.
        message = canonical({"digest": challenge_digest, "subject": binding.subject_ref})
        signature = signer.sign(message)
        ed25519.Ed25519PublicKey.from_public_bytes(binding.public_key).verify(signature, message)
        return {"unit_digest": challenge_digest, "signature": encode64(signature)}

    def make_gate(self, **overrides):
        arguments = dict(load_policy=lambda: self.policy, workload_verifier=self.verifier,
                         registry=self, load_challenge=lambda cid: self.challenge if cid == self.challenge.id else None,
                         ledger=self.ledger, signer=self, create_proof=self.unit_proof, clock=lambda: self.now)
        arguments.update(overrides)
        return ProofGate(**arguments)

    def reset_evidence(self):
        self.token = jwt(self.issuer_key, self.claims)
        self.challenge = Challenge("challenge:1", "mfa:fixture", "agent:qa", self.now,
                                   self.now + 120, request_digest(self.policy, self.request))
        self.observation = observe_artifacts(
            policy=self.policy, request=self.request, token=self.token, challenge=self.challenge,
            artifacts=self.artifacts, configuration=self.configuration, private_key=self.supervisor,
            now=self.now, expires_at=self.now + 60)

    def run(self):
        return self.gate.sign(self.challenge.id, self.request, self.token, self.observation)


@pytest.fixture
def h(tmp_path):
    return Harness(tmp_path)
