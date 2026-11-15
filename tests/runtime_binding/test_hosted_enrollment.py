"""Actual CSR/mTLS source qualification; provider/guest facts are isolated fixtures."""
from dataclasses import asdict,replace
from datetime import datetime,timedelta,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import secrets
import ssl
from threading import Thread
import time
from types import SimpleNamespace
import pytest
from .hosted_fixture import child_generations
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from workload_factory_binding.evidence import BindingError,byte_digest,canonical,digest,encode64,decode64
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.enrollment import EnrollmentAuthority,EnrollmentSelection,EnrollmentCurrent
from workload_factory_binding_runtime.hosted.nonces import NonceLedger,ERROR,Unavailable
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps


def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o600);return path


@pytest.fixture
def enrollment(tmp_path, request):
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    now=datetime.now(timezone.utc);name=x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME,"T012P isolated CA")])
    ca=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
        .not_valid_after(now+timedelta(hours=1)).add_extension(x509.BasicConstraints(ca=True,path_length=0),True).sign(key,hashes.SHA256()))
    ca_file=put(tmp_path/"ca.pem",ca.public_bytes(serialization.Encoding.PEM))
    def leaf(role,server=False):
        k=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        b=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME,role)]))
            .issuer_name(name).public_key(k.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(minutes=10))
            .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH if server else x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]),False))
        if server:b=b.add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),False)
        cert=b.sign(key,hashes.SHA256());cp=put(tmp_path/role/"cert.pem",cert.public_bytes(serialization.Encoding.PEM))
        kp=put(tmp_path/role/"key.pem",k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        return cp,kp,cert,k
    server,bootstrap,worker=leaf("server",True),leaf("bootstrap"),leaf("worker")
    service_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    csr=x509.CertificateSigningRequestBuilder().subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME,"self-asserted-admin")])).sign(service_key,hashes.SHA256())
    s=SimpleNamespace(now=int(time.time()),mono=0.,nonce=secrets.token_hex(32),facts=None,request_changes={},replies=[],service_key=service_key,ca=ca,ca_key=key)
    s.selection=EnrollmentSelection("enrollment:fixture","host:fixture","incarnation:fixture",digest({"source":"approved"}),"case:fixture",digest({"plan":"approved"}),os.getuid(),
        getattr(request,"param","broker"),byte_digest(service_key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)),
        "sha256:"+bootstrap[2].fingerprint(hashes.SHA256()).hex(),"issuer:fixture","key-version:fixture",byte_digest(ca.public_bytes(serialization.Encoding.DER)),s.now,s.now+60)
    identity=NonceLedger.initialize(tmp_path/"state");s.ledger=NonceLedger(tmp_path/"state",identity=identity)
    def current(ref,*,deadline):
        return s.facts if s.facts is not None else EnrollmentCurrent("principal:bootstrap-reader",s.authority.selection_digest,
            s.selection.ref,s.nonce,True,s.now,s.now+30)
    s.authority=EnrollmentAuthority(selection=s.selection,ledger=s.ledger,ca_key=key,ca_certificate=ca,
        read_current=current,current_principal="principal:bootstrap-reader")
    s.raw={k:getattr(s.selection,k) for k in ("ref","host_ref","incarnation_ref","source_digest","uid","role")}
    s.raw.update(nonce=s.nonce,csr=encode64(csr.public_bytes(serialization.Encoding.DER)))
    def d():return Decision(clock=lambda:s.now,monotonic=lambda:s.mono)
    s.decision=d
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            try:
                n=int(self.headers.get("Content-Length","0"))
                if not 0<n<=16384:raise ValueError
                raw=self.rfile.read(n)
                if self.path=="/enroll":value=s.authority.enroll(raw,channel=self.connection,decision=d())
                elif self.path=="/private" and hasattr(s,"delivery"):
                    value=s.delivery.deliver(raw,channel=self.connection,decision=d())
                elif self.path=="/private":
                    role=s.authority.authorize(channel=self.connection,role=s.selection.role,decision=d())
                    value={"role":role,"credential":s.deliver(role,d()) if hasattr(s,"deliver") else "fixture-private-role-capability"}
                else:raise ValueError
                self.reply(200,value)
            except Unavailable:self.reply(503,{"error":ERROR})
            except Exception:self.reply(403,{"error":ERROR})
        def reply(self,status,value):
            s.replies.append(status);raw=canonical(value);self.send_response(status)
            self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
    http=ThreadingHTTPServer(("127.0.0.1",0),Handler);ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(str(server[0]),str(server[1]));ctx.load_verify_locations(cafile=str(ca_file));ctx.verify_mode=ssl.CERT_REQUIRED
    http.socket=ctx.wrap_socket(http.socket,server_side=True);thread=Thread(target=http.serve_forever,daemon=True);thread.start()
    s.ca_file,s.server_material,s.worker_material=ca_file,server,worker
    s.endpoint="https://127.0.0.1:"+str(http.server_port)
    s.bootstrap=PrivateHttps(ca_file=str(ca_file),certificate=str(bootstrap[0]),private_key=str(bootstrap[1]))
    s.worker=PrivateHttps(ca_file=str(ca_file),certificate=str(worker[0]),private_key=str(worker[1]))
    def enroll(raw=None,client=None):return (client or s.bootstrap).exchange("POST",s.endpoint+"/enroll",headers={"Content-Type":"application/json"},body=canonical(s.raw if raw is None else raw),decision=d())
    s.enroll=enroll
    def enrolled():
        r=enroll();assert r.status==200
        value=json.loads(r.body);cert=x509.load_der_x509_certificate(decode64(value["certificate"]))
        cp=put(tmp_path/"issued"/"cert.pem",cert.public_bytes(serialization.Encoding.PEM))
        kp=put(tmp_path/"issued"/"key.pem",service_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        client=PrivateHttps(ca_file=str(ca_file),certificate=str(cp),private_key=str(kp));return value,cert,client
    s.enrolled=enrolled
    try:yield s
    finally:http.shutdown();http.server_close();thread.join(timeout=5);assert not thread.is_alive()


def test_actual_csr_enrollment_and_mtls_role_delivery(enrollment):
    s=enrollment;value,cert,client=s.enrolled()
    s.ca_key.public_key().verify(cert.signature,cert.tbs_certificate_bytes,padding.PKCS1v15(),cert.signature_hash_algorithm)
    assert cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value==s.selection.role
    assert value["public_key_digest"]==s.selection.public_key_digest
    assert value["issuer_ref"]==s.selection.issuer_ref
    assert value["key_version"]==s.selection.key_version
    assert value["expires_at"]<=s.now+30
    r=client.exchange("POST",s.endpoint+"/private",headers={},body=b"{}",decision=s.decision())
    assert r.status==200
    assert json.loads(r.body)["credential"]=="fixture-private-role-capability"
    denied=s.worker.exchange("POST",s.endpoint+"/private",headers={},body=b"{}",decision=s.decision())
    assert denied.status==403
    assert "fixture-private-role" not in denied.body.decode()
    assert s.enroll().status==403


@pytest.mark.parametrize("field,value",[("host_ref","host:other"),("incarnation_ref","incarnation:other"),
    ("source_digest",digest({"other":True})),("uid",0),("uid",True),("role","issuer-admin"),("nonce","f"*64),("ref","enrollment:other")])
def test_each_self_claim_cannot_replace_approved_enrollment(enrollment,field,value):
    s=enrollment;raw={**s.raw,field:value};assert s.enroll(raw).status==403
    assert s.enroll().status==200


@pytest.mark.parametrize("field,value",[("active",False),("principal_ref","principal:worker"),
    ("selection_digest",digest({"other":True})),("nonce","e"*64),("expires_at",0)])
def test_independent_enrollment_facts_are_required(enrollment,field,value):
    s=enrollment;facts=EnrollmentCurrent("principal:bootstrap-reader",s.authority.selection_digest,s.selection.ref,s.nonce,True,s.now,s.now+30)
    s.facts=replace(facts,**{field:value});assert s.enroll().status==403
    s.facts=None;assert s.enroll().status==200


def test_valid_worker_bootstrap_request_is_explicitly_denied_before_nonce_use(enrollment):
    s=enrollment;assert s.enroll(client=s.worker).status==403
    assert s.enroll().status==200


def test_unsigned_or_substituted_csr_never_authenticates_itself(enrollment):
    s=enrollment;other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    csr=x509.CertificateSigningRequestBuilder().subject_name(x509.Name([])).sign(other,hashes.SHA256())
    assert s.enroll({**s.raw,"csr":encode64(csr.public_bytes(serialization.Encoding.DER))}).status==403
    raw=bytearray(decode64(s.raw["csr"]));raw[-1]^=1
    assert s.enroll({**s.raw,"csr":encode64(bytes(raw))}).status==403
    assert s.enroll().status==200


@pytest.mark.parametrize("change",["revoked","expired"])
def test_current_revocation_and_expiry_block_valid_issued_certificate(enrollment,change):
    s=enrollment;_,_,client=s.enrolled()
    if change=="revoked":s.facts=EnrollmentCurrent("principal:bootstrap-reader",s.authority.selection_digest,s.selection.ref,s.nonce,False,s.now,s.now+30)
    else:s.now+=61
    r=client.exchange("POST",s.endpoint+"/private",headers={},body=b"{}",decision=s.decision())
    assert r.status==403


from .test_hosted_issuance import provider


def test_enrolled_broker_receives_actual_narrow_app_token_over_mtls(enrollment,provider):
    s,p=enrollment,provider;p.now=s.now;p.selection=replace(p.selection,enrollment_digest=s.authority.selection_digest);issuer=p.issuer()
    from workload_factory_binding_runtime.hosted.issuance import RoleDelivery
    s.delivery=RoleDelivery(enrollment=s.authority,issuer=issuer)
    _,_,client=s.enrolled()
    bad=client.exchange("POST",s.endpoint+"/private",headers={},body=canonical({"ref":p.ref,"nonce":p.nonce,"role":"broker"}),decision=s.decision())
    assert bad.status==403
    assert p.calls==[]
    r=client.exchange("POST",s.endpoint+"/private",headers={},body=canonical({"ref":p.ref,"nonce":p.nonce}),decision=s.decision())
    assert r.status==200
    s.capability=issuer.pending(p.ref)
    assert json.loads(r.body)["credential"]==s.capability.credential
    assert p.active[s.capability.credential]
    assert s.worker.exchange("POST",s.endpoint+"/private",headers={},body=canonical({"ref":p.ref,"nonce":p.nonce}),decision=s.decision()).status==403
    assert len(p.active)==1
    from workload_factory_binding_runtime.hosted.issuance import InstallationRetirer
    retired=InstallationRetirer(writer=p.routed(),observer=p.routed()).retire(s.capability,decision=s.decision())
    assert retired["state"]=="retired"


@pytest.mark.parametrize("enrollment",["custody-gate"],indirect=True)
def test_enrolled_certificate_uses_unchanged_owning_software_ed25519_custody(enrollment,tmp_path):
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from factory_binding.conftest import Harness
    from openwallet_runtime.custody import RemoteSigner,TLSClient
    from openwallet_runtime.proof import TrustedKeyBinding,create_proof,verify_proof,ProofError
    from openwallet_runtime.registry import BindingRegistry
    from openwallet_runtime.reference_service import CustodyApplication,ReferenceServer,provision_key,server_context
    s=enrollment;value,cert,issued=s.enrolled();(tmp_path/"proof").mkdir();h=Harness(tmp_path/"proof")
    public=provision_key(tmp_path/"wallet-keys",h.binding.key_ref)
    binding=TrustedKeyBinding(**{**asdict(h.binding),"public_key":public})
    registry=BindingRegistry(tmp_path/"registry");registry.register(binding,expected_revision=None)
    app=CustodyApplication(registry,key_directory=tmp_path/"wallet-keys",clock=lambda:h.now,
        policies={cert.fingerprint(hashes.SHA256()).hex():{"actions":["resolve","sign"],"subjects":[binding.subject_ref]}})
    context=server_context(ca_file=s.ca_file,certificate=s.server_material[0],private_key=s.server_material[1])
    server=ReferenceServer(("127.0.0.1",0),context=context,application=app)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    endpoint="https://127.0.0.1:"+str(server.server_port)
    client=TLSClient(endpoint,ca_file=issued.ca,certificate=issued.cert,private_key=issued.key)
    remote=RemoteSigner(client,subject_ref=binding.subject_ref);messages=[]
    class Signer:
        def sign(self,message):messages.append(message);return remote.sign(message)
    try:
        proof=create_proof(h.challenge.digest,binding,Signer(),now=h.now)
        assert verify_proof(proof,expected_digest=h.challenge.digest,binding=binding,now=h.now).subject_ref==binding.subject_ref
        assert len(messages)==1
        worker=TLSClient(endpoint,ca_file=s.ca_file,certificate=s.worker_material[0],private_key=s.worker_material[1])
        signer=RemoteSigner(worker, subject_ref=binding.subject_ref)
        with pytest.raises(ProofError, match='^service-refused$'):
            signer.sign(messages[0])
        assert value["role"]=="custody-gate"
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5);assert not thread.is_alive()



def test_enrollment_readback_outage_is_not_an_authenticated_denial(enrollment):
    s=enrollment;_,_,client=s.enrolled()
    assert client.exchange("POST",s.endpoint+"/private",headers={},body=b"{}",decision=s.decision()).status==200
    def outage(*args,**kwargs):raise OSError("private-provider-canary")
    s.authority.read_current=outage
    response=s.worker.exchange("POST",s.endpoint+"/private",headers={},body=b"{}",decision=s.decision())
    assert response.status==503
    assert "private-provider-canary" not in response.body.decode()
    with pytest.raises(AssertionError):assert response.status==403



def test_issuer_certificate_version_cannot_be_only_a_label(enrollment):
    s=enrollment
    selected=replace(s.selection,issuer_certificate_digest=digest({"wrong-certificate":True}))
    with pytest.raises(BindingError):EnrollmentAuthority(selection=selected,ledger=s.ledger,ca_key=s.ca_key,ca_certificate=s.ca,
        read_current=s.authority.read_current,current_principal="principal:bootstrap-reader")
    assert s.enroll().status==200



def test_reader_enrollment_cannot_be_attached_to_broker_issuer(enrollment,provider):
    from workload_factory_binding_runtime.hosted.issuance import RoleDelivery
    s,p=enrollment,provider
    wrong=replace(s.authority.selection,role="reader")
    s.authority.selection=wrong
    issuer=p.issuer()
    with pytest.raises(BindingError):
        RoleDelivery(enrollment=s.authority, issuer=issuer)
    assert p.calls==[]



def test_same_role_from_another_enrollment_scope_cannot_receive_app_capability(enrollment,provider):
    from workload_factory_binding_runtime.hosted.issuance import RoleDelivery
    issuer=provider.issuer()
    with pytest.raises(BindingError):
        RoleDelivery(enrollment=enrollment.authority, issuer=issuer)



def test_changed_enrollment_case_cannot_reuse_the_old_approval(enrollment):
    s=enrollment;old=s.authority.selection;s.authority.selection=replace(old,case_ref="case:other")
    assert s.enroll().status==403
    s.authority.selection=old
    assert s.enroll().status==200



def test_issuer_provider_outage_is_not_private_role_denial(enrollment,provider):
    from workload_factory_binding_runtime.hosted.issuance import RoleDelivery
    s,p=enrollment,provider;p.now=s.now;p.selection=replace(p.selection,enrollment_digest=s.authority.selection_digest)
    issuer=p.issuer()
    class Outage:
        def exchange(self,*args,**kwargs):raise OSError("private-provider-outage-canary")
    issuer.transport=Outage();s.delivery=RoleDelivery(enrollment=s.authority,issuer=issuer)
    _,_,client=s.enrolled()
    response=client.exchange("POST",s.endpoint+"/private",headers={},body=canonical({"ref":p.ref,"nonce":p.nonce}),decision=s.decision())
    assert response.status==503
    assert "private-provider-outage-canary" not in response.body.decode()
