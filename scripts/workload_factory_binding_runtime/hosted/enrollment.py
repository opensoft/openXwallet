"""Independently approved CSR enrollment and actual mTLS role authentication."""
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import ssl
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa,ec
from workload_factory_binding.evidence import byte_digest,encode64,decode64,integer,require,valid_digest
from ..config import _handle
from ..github_bootstrap.common import document
from .nonces import NonceLedger
from workload_factory_binding.evidence import BindingError,digest
from .nonces import ERROR,Unavailable
@dataclass(frozen=True,repr=False)
class EnrollmentSelection:
    ref:str
    host_ref:str
    incarnation_ref:str
    source_digest:str
    case_ref:str
    plan_digest:str
    uid:int
    role:str
    public_key_digest:str
    bootstrap_peer_digest:str
    issuer_ref:str
    key_version:str
    issuer_certificate_digest:str
    not_before:int
    expires_at:int
@dataclass(frozen=True,repr=False)
class EnrollmentCurrent:
    principal_ref:str
    selection_digest:str
    ref:str
    nonce:str
    active:bool
    observed_at:int
    expires_at:int
def peer_digest(channel):
    require(type(channel) is ssl.SSLSocket and channel.server_side is True
            and channel.context.verify_mode==ssl.CERT_REQUIRED and channel.version() in ("TLSv1.2","TLSv1.3"),ERROR)
    raw=channel.getpeercert(binary_form=True);require(type(raw) is bytes and 0<len(raw)<=16384,ERROR)
    return byte_digest(raw),x509.load_der_x509_certificate(raw)


class EnrollmentAuthority:
    def __init__(self,*,selection,ledger,ca_key,ca_certificate,read_current,current_principal):
        require(type(selection) is EnrollmentSelection and type(ledger) is NonceLedger
                and isinstance(ca_key,rsa.RSAPrivateKey) and 2048<=ca_key.key_size<=4096
                and isinstance(ca_certificate,x509.Certificate) and callable(read_current),ERROR)
        for value in (selection.ref,selection.host_ref,selection.incarnation_ref,selection.issuer_ref,selection.key_version,selection.case_ref,current_principal):_handle(value)
        _handle("role:"+selection.role)
        require(all(valid_digest(value) for value in (selection.source_digest,selection.public_key_digest,selection.bootstrap_peer_digest,selection.issuer_certificate_digest,selection.plan_digest))
                and integer(selection.uid) and selection.uid>0 and integer(selection.not_before) and integer(selection.expires_at)
                and 0<selection.expires_at-selection.not_before<=60
                and byte_digest(ca_certificate.public_bytes(serialization.Encoding.DER))==selection.issuer_certificate_digest
                and ca_certificate.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
                and ca_key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
                    ==ca_certificate.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo),ERROR)
        self.selection,self.selection_digest=selection,digest(asdict(selection));self.ledger=ledger
        self.key,self.ca,self.read_current,self.principal=ca_key,ca_certificate,read_current,current_principal

    def current(self,decision,nonce=None):
        now=decision.now();s=self.selection
        require(digest(asdict(s))==self.selection_digest
                and byte_digest(self.ca.public_bytes(serialization.Encoding.DER))==s.issuer_certificate_digest,ERROR)
        require(s.not_before<=now<s.expires_at,ERROR);decision.clip(s.expires_at)
        before=decision.now()
        try:value=self.read_current(s.ref,deadline=decision.deadline)
        except Exception:raise Unavailable(ERROR) from None
        now=decision.now()
        require(type(value) is EnrollmentCurrent and value.principal_ref==self.principal
                and value.selection_digest==self.selection_digest and value.ref==s.ref
                and type(value.nonce) is str and len(value.nonce)==64
                and (nonce is None or value.nonce==nonce) and value.active is True
                and integer(value.observed_at) and integer(value.expires_at)
                and before<=value.observed_at<=now<value.expires_at<=value.observed_at+60,ERROR)
        decision.clip(value.expires_at);return value

    def enroll(self,raw,*,channel,decision):
        try:
            peer,_=peer_digest(channel);s=self.selection;require(peer==s.bootstrap_peer_digest,ERROR)
            value=document(raw,16384)
            require(type(value) is dict and set(value)=={"ref","host_ref","incarnation_ref","source_digest","uid","role","nonce","csr"}
                and type(value["uid"]) is int
                and all(value[k]==getattr(s,k) for k in ("ref","host_ref","incarnation_ref","source_digest","uid","role")),ERROR)
            current=self.current(decision,value["nonce"])
            csr_bytes=decode64(value["csr"]);require(len(csr_bytes)<=8192,ERROR)
            csr=x509.load_der_x509_csr(csr_bytes);public=csr.public_key()
            require(csr.is_signature_valid and csr.signature_hash_algorithm.name=="sha256" and len(csr.extensions)==0
                and ((isinstance(public,rsa.RSAPublicKey) and 2048<=public.key_size<=4096)
                    or (isinstance(public,ec.EllipticCurvePublicKey) and isinstance(public.curve,ec.SECP256R1)))
                and byte_digest(public.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo))==s.public_key_digest,ERROR)
            self.current(decision,current.nonce)
            self.ledger.reserve(s.ref,current.nonce,digest({"selection":self.selection_digest,"nonce":current.nonce}),decision=decision)
            now=decision.now();expiry=min(s.expires_at,current.expires_at,int(self.ca.not_valid_after_utc.timestamp()))
            require(now<expiry,ERROR)
            cert=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME,s.role)]))
                .issuer_name(self.ca.subject).public_key(public).serial_number(x509.random_serial_number())
                .not_valid_before(datetime.fromtimestamp(now,timezone.utc)).not_valid_after(datetime.fromtimestamp(expiry,timezone.utc))
                .add_extension(x509.BasicConstraints(ca=False,path_length=None),True)
                .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]),True).sign(self.key,hashes.SHA256()))
            der=cert.public_bytes(serialization.Encoding.DER);fingerprint=byte_digest(der)
            self.current(decision,current.nonce)
            self.ledger.transition(s.ref,("consumed",),"issued",decision=decision,token_digest=fingerprint)
            decision.now()
            return {"certificate":encode64(der),"certificate_digest":fingerprint,"public_key_digest":s.public_key_digest,
                    "issuer_ref":s.issuer_ref,"key_version":s.key_version,"case_ref":s.case_ref,"plan_digest":s.plan_digest,"source_digest":s.source_digest,"role":s.role,"ref":s.ref,"issued_at":now,"expires_at":expiry}
        except Unavailable:raise
        except Exception:raise BindingError(ERROR) from None

    def authorize(self,*,channel,role,decision):
        try:
            fingerprint,cert=peer_digest(channel);s=self.selection;require(role==s.role,ERROR)
            current=self.current(decision);row=self.ledger.state(s.ref,decision=decision)
            require(row["state"]=="issued" and row["token_digest"]==fingerprint
                and row["commitment"]==digest({"selection":self.selection_digest,"nonce":current.nonce})
                and int(cert.not_valid_before_utc.timestamp())<=decision.now()<int(cert.not_valid_after_utc.timestamp()),ERROR)
            self.current(decision,current.nonce);return s.role
        except Unavailable:raise
        except Exception:raise BindingError(ERROR) from None
