"""Confined-gate embedding over the unchanged owning TLS/signing API.

Hosting owns credential issuance, immutable files, authenticated deployment
readback and OS/network isolation. These checks bind that evidence to actual
client material; matching Python objects alone cannot establish confinement.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import stat

from cryptography import x509
from cryptography.hazmat.primitives import hashes

from workload_factory_binding.evidence import (
    BindingError, byte_digest, digest, integer, reference, require,
)
from .config import RuntimeTrust, validate_config
from .loaders import BoundService, ServiceIdentity, check_service


@dataclass(frozen=True, repr=False)
class CustodyMaterial:
    """Protected host paths, never worker input or committed configuration."""
    endpoint: str
    ca_file: Path
    certificate: Path
    private_key: Path


@dataclass(frozen=True, repr=False)
class CustodyAccess:
    """Intrinsic authenticated issuance/deployment readback, not a wire format.

    Hosting must measure actual selection and issued scope, not echo candidate
    data. Boundary/issuance references identify independently inspectable records.
    No worker-supplied `confined` or `denied` boolean is accepted.
    """
    deployment_ref: str
    boundary_ref: str
    issuance_ref: str
    gate_principal: str
    config_digest: str
    sources_digest: str
    case_ref: str
    run_id: str
    run_attempt: str
    service: ServiceIdentity
    certificate_digest: str
    endpoint_digest: str
    subject_ref: str
    key_ref: str
    custody_ref: str
    actions: tuple
    issued_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class CustodyTrust:
    """Operator-selected approvals and authenticated callback outside the worker.

    load_access(deadline=epoch) must bound I/O and derive CustodyAccess from
    actual protected credential/deployment control planes. This is not a new
    custody-side assertion. The neutral service still receives only sign(message).
    """
    deployment_ref: str
    boundary_ref: str
    issuance_ref: str
    gate_principal: str
    load_access: object


def _read(path, *, private=False):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and info.st_uid == os.geteuid() and 0 < info.st_size <= 16384
                and (not private or not info.st_mode & 0o077), "custody-material-unavailable")
        raw = stream.read(16385)
        require(0 < len(raw) <= 16384, "custody-material-unavailable")
        return raw


def _material(material):
    try:
        require(type(material) is CustodyMaterial, "custody-material-unavailable")
        ca, cert, key = (_read(material.ca_file), _read(material.certificate),
                         _read(material.private_key, private=True))
        certificate = x509.load_pem_x509_certificate(cert)
        return (byte_digest(ca), "sha256:" + certificate.fingerprint(hashes.SHA256()).hex(),
                byte_digest(key), byte_digest(cert))
    except Exception:
        raise BindingError("custody-material-unavailable") from None


class _Use:
    def __init__(self, signer, deadline=None):
        self.signer, self.last, self.deadline = signer, None, deadline
        self.check()

    def clock(self):
        try:
            now = self.signer.runtime_trust.clock()
            require(integer(now) and (self.last is None or now >= self.last), "custody-clock-unavailable")
        except Exception:
            raise BindingError("custody-clock-unavailable") from None
        require(self.deadline is None or now < self.deadline, "custody-access-expired")
        self.last = now
        return now

    def check(self):
        before = self.clock()
        try:
            raw = self.signer.load_config()
        except Exception:
            raise BindingError("runtime-config-unavailable") from None
        current = validate_config(raw, trust=self.signer.runtime_trust)
        require(current.checked_at >= before, "custody-clock-unavailable")
        self.last = current.checked_at
        self.deadline = min(current.valid_until, self.deadline or current.valid_until)
        selection = current.selection
        check_service(self.signer.service, selection["services"]["custody"], "sign")
        require(_material(self.signer.material) == self.signer.material_digests,
                "custody-material-changed")
        require(selection["services"]["custody"]["trust_digest"] == self.signer.material_digests[0],
                "custody-trust-mismatch")
        trust = self.signer.custody_trust
        require(trust.gate_principal not in (
            selection["services"]["worker_channel"]["principal_ref"],
            selection["services"]["supervisor"]["principal_ref"],
            self.signer.runtime_trust.readback_principal), "custody-gate-not-independent")
        self.clock()
        try:
            access = trust.load_access(deadline=self.deadline)
        except Exception:
            raise BindingError("custody-readback-unavailable") from None
        now = self.clock()
        require(type(access) is CustodyAccess and type(access.service) is ServiceIdentity,
                "custody-access-unverified")
        for name in ("deployment_ref", "boundary_ref", "issuance_ref", "gate_principal"):
            require(getattr(access, name) == getattr(trust, name), "custody-deployment-mismatch")
        require(access.config_digest == current.config_digest
                and access.sources_digest == digest({role: dict(source) for role, source in selection["sources"].items()})
                and access.case_ref == selection["case_ref"]
                and access.run_id == selection["launch"]["run_id"]
                and access.run_attempt == selection["launch"]["run_attempt"], "custody-deployment-mismatch")
        require(access.service == self.signer.service.identity
                and access.certificate_digest == self.signer.material_digests[1]
                and access.endpoint_digest == byte_digest(self.signer.material.endpoint.encode()),
                "custody-issuance-mismatch")
        authority = selection["authority"]
        require(self.signer.subject_ref == authority["subject_ref"]
                and all(getattr(access, name) == authority[name] for name in
                    ("subject_ref", "key_ref", "custody_ref"))
                and type(access.actions) is tuple and access.actions == ("sign",), "custody-scope-mismatch")
        require(integer(access.issued_at) and integer(access.expires_at)
                and access.issued_at <= now < access.expires_at <= access.issued_at + 60,
                "custody-access-expired")
        self.deadline = min(self.deadline, access.expires_at)
        self.clock()


class ConfinedCustody:
    """Trusted gate-only capability. Never export this object to a worker.

    The selected owner supplies TLSClient and RemoteSigner constructors. No
    replacement signer, endpoint, credential, trust model or per-use assertion
    comes from the worker. Immutable paths and real confinement remain hosting
    obligations; before/after snapshots cannot detect restored intermediate edits.
    """
    def __init__(self, *, load_config, runtime_trust, custody_trust, identity,
                 material, tls_client, remote_signer, subject_ref, trust_model="confined-gate"):
        require(trust_model == "confined-gate", "custody-owner-decision-required")
        require(type(runtime_trust) is RuntimeTrust and type(custody_trust) is CustodyTrust
                and type(identity) is ServiceIdentity and reference(subject_ref)
                and all(callable(value) for value in (load_config, custody_trust.load_access,
                                                     tls_client, remote_signer)), "invalid-custody-embedding")
        require(all(reference(getattr(custody_trust, name)) for name in
                    ("deployment_ref", "boundary_ref", "issuance_ref", "gate_principal")),
                "invalid-custody-embedding")
        self.load_config, self.runtime_trust, self.custody_trust = load_config, runtime_trust, custody_trust
        self.subject_ref = subject_ref
        self.material, self.material_digests = material, _material(material)
        self.service = BoundService(identity, self)
        # Validate approval, issuance and actual material before constructing the client.
        use = _Use(self)
        try:
            client = tls_client(material.endpoint, ca_file=material.ca_file,
                                certificate=material.certificate, private_key=material.private_key)
            self.remote = remote_signer(client, subject_ref=subject_ref)
            require(callable(getattr(self.remote, "sign", None)), "invalid-custody-embedding")
        except Exception:
            raise BindingError("custody-connection-unavailable") from None
        use.check()

    def sign(self, message):
        """Owning compatibility seam for trusted standalone callers only."""
        return self._sign(message, None)[0]

    def sign_for_use(self, message, *, deadline):
        """Internal bridge seam: exchange earliest deadlines, not a wire assertion."""
        require(integer(deadline), "custody-access-expired")
        return self._sign(message, deadline)

    def _sign(self, message, deadline):
        require(type(message) is bytes and 0 < len(message) <= 8192, "invalid-custody-message")
        use = _Use(self, deadline)
        try:
            signature = self.remote.sign(message)
        except Exception:
            raise BindingError("custody-service-unavailable") from None
        use.check()
        require(type(signature) is bytes and len(signature) == 64, "invalid-custody-signature")
        return signature, use.deadline
