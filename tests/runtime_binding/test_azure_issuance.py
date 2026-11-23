"""P06 real isolated TLS/crypto/kernel/state controls; provider/admin facts are doubles."""
from dataclasses import replace
import base64
import copy
import json
import os
from pathlib import Path
import pickle
import select
import subprocess
import sys
import sqlite3
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
import time
from types import SimpleNamespace
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from workload_factory_binding.evidence import BindingError, canonical, decode64, digest
from workload_factory_binding_runtime.azure_composition import issuance as composition
from workload_factory_binding_runtime.azure_composition.issuance import Issuance, Retirement
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.credential import (CredentialBroker, KernelPrincipal,
    credential_channels)
from workload_factory_binding_runtime.hosted.enrollment import EnrollmentCurrent
from workload_factory_binding_runtime.hosted.issuance import IssuanceCurrent, permissions
from workload_factory_binding_runtime.hosted.nonces import NonceLedger, ERROR, Unavailable
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
from workload_factory_binding_runtime.hosted.readback import ReadBudget
from .test_hosted_enrollment import enrollment
from .test_hosted_issuance import provider
from .hosted_fixture import child_generations


def rows(ledger):
    with sqlite3.connect((ledger.directory/'issuance.sqlite').as_uri()+'?mode=ro', uri=True) as db:
        return db.execute('SELECT ref,nonce,state,token_digest FROM attempts').fetchall()


@pytest.fixture
def composed(enrollment, provider, tmp_path):
    s, p = enrollment, provider
    p.now = s.now
    p.selection = replace(p.selection, role=s.selection.role, enrollment_digest=s.authority.selection_digest)
    p.install_permissions = permissions(s.selection.role)
    p.token_permissions = dict(p.install_permissions)
    original = p.issuer()
    decision = Decision(clock=lambda:s.now, monotonic=time.monotonic)
    c = SimpleNamespace(s=s, p=p, decision=decision, exceptions=[], resolutions=[], stop=Event())
    broker = CredentialBroker(principals=(KernelPrincipal.current('issuer'),),
        capabilities={'resolver': (('issuer',), lambda **_:c.resolutions.append(True) or b'fixture-vault-credential')})
    server_channel, channel = credential_channels()
    c.channel=channel
    def serve():
        while not c.stop.is_set():
            if select.select([server_channel], [], [], .02)[0]:
                broker.serve_once(server_channel, decision=decision)
    broker_thread = Thread(target=serve, daemon=True)
    broker_thread.start()
    c.construct = lambda **kw:Issuance(**{**dict(enrollment=s.authority, selection=p.selection, ledger=p.ledger,
        transport=p.transport(), credential_channel=channel, read_current=original.read_current,
        current_principal=original.principal, decision=decision), **kw})
    c.actor = c.construct()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):pass
        def do_POST(self):
            try:
                n = int(self.headers['Content-Length'])
                assert 0 < n <= 16384
                raw = self.rfile.read(n)
                if self.path == '/enroll':value = c.actor.enroll(raw, channel=self.connection)
                elif self.path == '/private':value = c.actor.deliver(raw, channel=self.connection)
                else:raise ValueError
                status = 200
            except Unavailable as error:
                c.exceptions.append(error); status=503; value={'error':ERROR}
            except Exception as error:
                c.exceptions.append(error); status=403; value={'error':ERROR}
            raw = canonical(value)
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(s.server_material[0]), str(s.server_material[1]))
    context.load_verify_locations(cafile=str(s.ca_file)); context.verify_mode=ssl.CERT_REQUIRED
    server.socket=context.wrap_socket(server.socket, server_side=True)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    c.origin='https://127.0.0.1:'+str(server.server_port)
    def client(old):
        return PrivateHttps(ca_file=old.ca,certificate=old.cert,private_key=old.key,fixture_origin=c.origin)
    c.bootstrap, c.worker = client(s.bootstrap), client(s.worker)
    c.call=lambda peer,path,value:peer.exchange('POST',c.origin+path,headers={},body=canonical(value),decision=decision)
    c.body={'ref':p.ref,'nonce':p.nonce}
    def enrolled():
        result=c.call(c.bootstrap,'/enroll',s.raw)
        assert result.status==200, 'healthy composition must enroll before any mutation'
        cert=x509.load_der_x509_certificate(decode64(json.loads(result.body)['certificate']))
        cp=tmp_path/'composed-cert.pem';cp.write_bytes(cert.public_bytes(serialization.Encoding.PEM));cp.chmod(0o600)
        kp=tmp_path/'composed-key.pem'
        kp.write_bytes(s.service_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));kp.chmod(0o600)
        return PrivateHttps(ca_file=str(s.ca_file),certificate=str(cp),private_key=str(kp),fixture_origin=c.origin)
    c.enrolled=enrolled
    c.cleanup=lambda cap, **kw:Retirement(capability=cap,selection=p.selection,
        writer=p.transport(),observer=p.transport(),decision=Decision(clock=lambda:p.now,monotonic=time.monotonic),**kw)
    try:
        yield c
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        c.stop.set();broker_thread.join(timeout=5);server_channel.close();channel.close()
        assert not thread.is_alive() and not broker_thread.is_alive()
        # Explicit fixture administration is separate from the tested failure.
        # Audit known capabilities before disposing keys/state. Unknown returned-
        # response loss remains indeterminate in the tested path, never success.
        p.changes.clear();p.install_permissions=permissions(p.selection.role);p.token_permissions=dict(p.install_permissions)
        audit=[]
        for cap in c.actor.issuer._pending.values():
            if p.active.get(cap.credential):
                retire=c.cleanup(cap)
                state=rows(cap.ledger)[0][2]
                result=retire.reconcile() if state=='retiring' else retire.retire()
                assert result['state']=='retired'
            audit.append({'readback':cap.readback(),'active':p.active.get(cap.credential,False)})
        unknown=sum(bool(active) for token,active in p.active.items()
                    if token not in {cap.credential for cap in c.actor.issuer._pending.values()})
        (tmp_path/'p06-cleanup.json').write_text(json.dumps({'known':audit,'unknown_indeterminate':unknown,
            'threads_joined':True,'enrollment_store':str(s.ledger.directory),'issuance_store':str(p.ledger.directory)},indent=2))


@pytest.mark.parametrize('enrollment',['broker','reader','source-reader'],indirect=True)
def test_complete_roles_and_unused_worker_preimages_fit_original_bounds(composed,tmp_path):
    c=composed; d=c.decision;b=ReadBudget(d);state=b.state;end=d.end;deadline=d.deadline;started=time.monotonic()
    assert rows(c.s.ledger)==[] and rows(c.p.ledger)==[]
    assert c.call(c.worker,'/enroll',c.s.raw).status==403
    assert rows(c.s.ledger)==[] and c.p.calls==[]
    peer=c.enrolled()
    assert c.call(c.worker,'/private',c.body).status==403
    assert rows(c.p.ledger)==[] and c.p.calls==[] and c.resolutions==[]
    result=c.call(peer,'/private',c.body);assert result.status==200
    cap=c.actor.pending(c.p.ref)
    assert json.loads(result.body)=={'role':c.s.selection.role,'credential':cap.credential}
    assert cap.use_until<=deadline and cap._decision is d and c.p.active[cap.credential]
    retirement=Retirement(capability=cap,selection=c.p.selection,writer=c.p.transport(),observer=c.p.transport(),decision=d)
    assert retirement.retire()['state']=='retired' and not c.p.active[cap.credential]
    assert d._hosted_reads is state and d.end==end and d.deadline<=deadline and d.remaining()>0
    assert state['counts']=={'protection':0,'source':4,'control':2,'arm':0,'key':1,'private':12}
    assert len(c.p.calls)==7 and c.resolutions==[True] and time.monotonic()-started<10
    (tmp_path/'p06-positive.json').write_text(json.dumps({'role':c.s.selection.role,'counts':state['counts'],
        'worker_unused_preimages_denied':True,'same_bytes_approved':True,'retired':True,
        'elapsed_seconds':time.monotonic()-started,'provider_calls':7,'kernel_resolutions':1},indent=2))


@pytest.mark.parametrize('field,value',[
    ('ref','enrollment:other'),('host_ref','host:other'),('incarnation_ref','incarnation:other'),
    ('source_digest',digest({'source':'other'})),('uid',0),('uid',True),('role','source-reader'),
    ('nonce','f'*64),('csr','AAAA'),('extra',True)])
def test_enrollment_self_claim_cannot_select_authority(composed,field,value):
    c=composed
    result=c.call(c.bootstrap,'/enroll',{**c.s.raw,field:value})
    assert result.status==403 and rows(c.s.ledger)==[] and c.p.calls==[]
    assert c.call(c.bootstrap,'/enroll',c.s.raw).status==200


@pytest.mark.parametrize('field,value',[
    ('principal_ref','principal:worker'),('selection_digest',digest({'other':True})),
    ('ref','enrollment:other'),('nonce','e'*64),('active',False),('observed_at',0),('expires_at',0)])
def test_independent_enrollment_facts_cannot_be_self_approved(composed,field,value):
    c=composed;s=c.s
    s.facts=replace(EnrollmentCurrent(s.authority.principal,s.authority.selection_digest,s.selection.ref,s.nonce,True,s.now,s.now+30),**{field:value})
    assert c.call(c.bootstrap,'/enroll',s.raw).status==403
    assert rows(s.ledger)==[] and c.p.calls==[]
    s.facts=None
    assert c.call(c.bootstrap,'/enroll',s.raw).status==200


@pytest.mark.parametrize('change',['signature','key-version','app','installation','permissions','expired','expiry','repository','repo-id'])
def test_provider_failure_is_unavailable_and_consumed_without_retry(composed,change):
    c=composed;peer=c.enrolled();c.p.changes[change]=True
    assert c.call(peer,'/private',c.body).status==503
    before=len(c.p.calls)
    assert rows(c.p.ledger)[0][2]=='consumed'
    assert c.call(peer,'/private',c.body).status==503 and len(c.p.calls)==before
    if change in ('permissions','expired','expiry','repository','repo-id'):
        cap=c.actor.pending(c.p.ref)
        assert c.p.active[cap.credential] and 'credential' not in cap.readback()


@pytest.mark.parametrize('field,value',[
    ('principal_ref','principal:worker'),('selection_digest',digest({'other':True})),
    ('ref','issuance:other'),('nonce','e'*64),('active',False),('observed_at',0),('expires_at',0)])
def test_independent_issuance_approval_precedes_reservation(composed,field,value):
    c=composed;peer=c.enrolled();i=c.actor.issuer;p=c.p
    p.current=replace(IssuanceCurrent(i.principal,i.selection_digest,p.ref,p.nonce,True,p.now,p.now+30),**{field:value})
    assert c.call(peer,'/private',c.body).status==503
    assert rows(p.ledger)==[] and p.calls==[] and c.resolutions==[]


@pytest.mark.parametrize('mutation',['role','enrollment_digest','case','plan','host','source','bootstrap','key','principal','reader','ledger','transport'])
def test_selected_binding_substitution_refuses_before_effects(composed,mutation,tmp_path):
    c=composed;a=c.actor
    if mutation in ('role','enrollment_digest'):
        a.issuer.selection=replace(a.issuer.selection,**{mutation:'reader' if mutation=='role' else digest({'other':True})})
    elif mutation in ('case','plan','host','source','bootstrap'):
        field={'case':'case_ref','plan':'plan_digest','host':'host_ref','source':'source_digest','bootstrap':'bootstrap_peer_digest'}[mutation]
        a.enrollment.selection=replace(a.enrollment.selection,**{field:digest({'other':True}) if 'digest' in field else 'other:scope'})
    elif mutation=='key':a.issuer.selection=replace(a.issuer.selection,key_uri=a.issuer.selection.key_uri.replace('a'*32,'b'*32))
    elif mutation=='principal':a.issuer.principal='principal:worker'
    elif mutation=='reader':a.enrollment.read_current=lambda *_a,**_k:None
    elif mutation=='ledger':
        identity=NonceLedger.initialize(tmp_path/'other-ledger');a.issuer.ledger=NonceLedger(tmp_path/'other-ledger',identity=identity)
    elif mutation=='transport':a.provider.http=c.p.transport()
    assert c.call(c.bootstrap,'/enroll',c.s.raw).status in (403,503)
    assert rows(c.s.ledger)==[] and rows(c.p.ledger)==[] and c.p.calls==[]


@pytest.mark.parametrize('store',['enrollment','issuance'])
@pytest.mark.parametrize('mutation',['missing','replaced','symlink','corrupt','schema','mode'])
def test_retained_store_refuses_without_initialization_or_repair(composed,store,mutation,tmp_path):
    c=composed;ledger=c.s.ledger if store=='enrollment' else c.p.ledger;db=ledger.directory/'issuance.sqlite'
    if mutation=='missing':db.rename(db.with_suffix('.saved'))
    elif mutation=='replaced':
        raw=db.read_bytes();db.rename(db.with_suffix('.saved'));db.write_bytes(raw);db.chmod(0o600)
    elif mutation=='symlink':db.rename(db.with_suffix('.saved'));db.symlink_to(db.with_suffix('.saved'))
    elif mutation=='corrupt':db.write_bytes(b'corrupt retained database')
    elif mutation=='schema':
        with sqlite3.connect(db) as conn:conn.execute('CREATE TABLE unexpected (x)')
    elif mutation=='mode':db.chmod(0o644)
    before=db.read_bytes() if db.exists() else None
    response=c.call(c.bootstrap,'/enroll',c.s.raw)
    # Unused issuance schema is validated by the primitive before its own effects.
    if store=='issuance' and mutation in ('schema','corrupt'):
        assert response.status==200
        peer_material=json.loads(response.body)
        # Deliver through a real TLS socket using this already issued certificate.
        cert=x509.load_der_x509_certificate(decode64(peer_material['certificate']))
        cp=tmp_path/'state-peer.pem';cp.write_bytes(cert.public_bytes(serialization.Encoding.PEM));cp.chmod(0o600)
        kp=tmp_path/'state-peer-key.pem';kp.write_bytes(c.s.service_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));kp.chmod(0o600)
        peer=PrivateHttps(ca_file=str(c.s.ca_file),certificate=str(cp),private_key=str(kp),fixture_origin=c.origin)
        assert c.call(peer,'/private',c.body).status==503
    else:assert response.status in (403,503)
    assert c.p.calls==[] and (db.read_bytes() if db.exists() else None)==before


@pytest.mark.parametrize('mutation',['ledger','counts','members','phase','end','deadline','clock','counter','nested-refund'])
def test_nested_callback_cannot_refund_or_replace_original_authority(composed,mutation):
    c=composed;a=c.actor;d=c.decision;b=ReadBudget(d)
    original=a._enrollment_reader
    def reader(*args,**kwargs):
        value=original(*args,**kwargs)
        if mutation=='ledger':d._hosted_reads=copy.deepcopy(b.state)
        elif mutation=='counts':b.state['counts']=dict(b.state['counts'])
        elif mutation=='members':b.state['members']=dict(b.state['members'])
        elif mutation=='phase':b.state['qualification']=True
        elif mutation=='end':d.end+=1
        elif mutation=='deadline':d.deadline+=1
        elif mutation=='clock':d.clock=lambda:c.s.now
        elif mutation=='counter':b.state['counts']['private']=0
        else:
            b.consume('key');b.state['counts']['key']=0
        return value
    # Select the callback before constructing a fresh source actor, never mutate
    # an already selected function just to trigger the outer binding guard.
    c.s.authority.read_current=reader
    c.actor=c.construct()
    assert c.call(c.bootstrap,'/enroll',c.s.raw).status in (403,503)
    assert rows(c.s.ledger)==[] and c.p.calls==[]


@pytest.mark.parametrize('group',['private','key','source','control'])
def test_precharged_original_budget_cannot_be_replaced_for_minting(composed,group):
    c=composed;peer=c.enrolled();b=ReadBudget(c.decision)
    limit={'private':12,'key':3,'source':4,'control':2}[group]
    while b.count(group)<limit:b.consume(group)
    assert c.call(peer,'/private',c.body).status in (403,503)
    assert c.p.active=={}


@pytest.mark.parametrize('method,url',[
    ('GET','https://api.github.com/user'),('POST','https://api.github.com/app/installations/99/access_tokens'),
    ('GET','https://api.github.com/installation/repositories?per_page=100&page=1'),
    ('POST','https://other-vault.vault.azure.net/keys/app-key/'+'a'*32+'/sign?api-version=2025-07-01'),
    ('POST','https://fixture-vault.vault.azure.net/keys/app-key/'+'b'*32+'/sign?api-version=2025-07-01'),
    ('POST','http://api.github.com/app'),('GET','https://api.github.com/app#fragment')])
def test_original_closed_route_validated_before_fixture_translation(composed,method,url):
    c=composed
    with pytest.raises(BindingError):c.actor.provider.exchange(method,url,headers={},decision=c.decision)
    assert c.p.calls==[] and ReadBudget(c.decision).count('private')==0


def test_original_authority_cannot_be_renewed_but_private_cleanup_survives(composed):
    c=composed;peer=c.enrolled();assert c.call(peer,'/private',c.body).status==200
    cap=c.actor.pending(c.p.ref);end=c.decision.end
    c.s.now+=11;c.p.now=c.s.now
    with pytest.raises(BindingError):c.actor.issuer.resolve(c.p.ref,c.p.nonce,decision=Decision(clock=lambda:c.s.now))
    assert c.actor.pending(c.p.ref) is cap and c.decision.end==end
    assert c.cleanup(cap).retire()['state']=='retired' and not c.p.active[cap.credential]


@pytest.mark.parametrize('cancel',[False,True])
def test_private_failure_and_cancellation_scrub_context_while_traceback_retained(composed,monkeypatch,cancel):
    c=composed;canary='PRIVATE-CANARY-DO-NOT-RETAIN';fds=set(os.listdir('/proc/self/fd'))
    def failed(*_a,**_k):
        raise KeyboardInterrupt(canary) if cancel else RuntimeError(canary)
    monkeypatch.setattr(composition,'credential_request',failed)
    caught=None
    try:composition.private(lambda:c.actor._credential(deadline=c.decision.deadline))
    except BaseException as error:caught=error
    assert type(caught) is (KeyboardInterrupt if cancel else BindingError)
    assert caught.__context__ is None and caught.__cause__ is None and canary not in repr(caught)
    assert set(os.listdir('/proc/self/fd'))==fds and caught.__traceback__ is not None


def test_runtime_composition_has_no_activation_or_serializable_private_state(composed):
    c=composed
    for value in (c.actor,c.actor.provider):
        with pytest.raises(BindingError):pickle.dumps(value)
        assert 'fixture-vault-credential' not in repr(value)
    assert not hasattr(c.actor,'serve_forever')
    assert c.p.calls==[] and rows(c.p.ledger)==[]


@pytest.mark.parametrize('lost',['mint-response','post-mint-approval','retirement-response'])
def test_uncertainty_retains_consumption_and_never_replays_send(composed,monkeypatch,lost):
    c=composed;peer=c.enrolled();original=PrivateHttps.exchange;triggered=[]
    def exchange(http,method,url,**kwargs):
        result=original(http,method,url,**kwargs)
        selected=('/installation/token' if lost=='retirement-response' else '/app/installations/88/access_tokens')
        if url==c.p.endpoint+selected and not triggered:
            triggered.append(True)
            if lost=='post-mint-approval':
                i=c.actor.issuer
                c.p.current=IssuanceCurrent(i.principal,i.selection_digest,c.p.ref,c.p.nonce,False,c.p.now,c.p.now+30)
            else:raise RuntimeError('PRIVATE-RESPONSE-LOSS')
        return result
    monkeypatch.setattr(PrivateHttps,'exchange',exchange)
    c.actor=c.construct()
    result=c.call(peer,'/private',c.body)
    if lost=='retirement-response':
        assert result.status==200
        cap=c.actor.pending(c.p.ref);retirer=c.cleanup(cap)
        with pytest.raises(BindingError):retirer.retire()
        assert rows(c.p.ledger)[0][2]=='retiring'
        assert retirer.reconcile()['state']=='retired'
        assert sum(method=='DELETE' for method,_ in c.p.calls)==1
    else:
        assert result.status==503 and rows(c.p.ledger)[0][2]=='consumed'
        if lost=='post-mint-approval':assert c.actor.pending(c.p.ref).expires_at is None
        else:
            with pytest.raises(BindingError):c.actor.pending(c.p.ref)
        before=list(c.p.calls)
        c.p.current=None
        assert c.call(peer,'/private',c.body).status==503 and c.p.calls==before
        assert sum(path=='/app/installations/88/access_tokens' for _,path in c.p.calls)==1


def test_reconstruction_with_same_store_cannot_replay_a_completed_attempt(composed):
    c=composed;peer=c.enrolled();assert c.call(peer,'/private',c.body).status==200
    cap=c.actor.pending(c.p.ref);before=list(c.p.calls)
    # The trusted embedding may reconstruct its actor, but not initialize state.
    c.actor=c.construct()
    assert c.call(peer,'/private',c.body).status==503 and c.p.calls==before
    reopened=NonceLedger(c.p.ledger.directory,identity=c.p.ledger.identity)
    assert reopened.state(c.p.ref,decision=c.decision)['state']=='issued'
    assert c.cleanup(cap).retire()['state']=='retired'


def test_concurrent_valid_attempts_have_one_durable_winner(composed):
    c=composed;peer=c.enrolled();results=[]
    threads=[Thread(target=lambda:results.append(c.call(peer,'/private',c.body).status)) for _ in range(2)]
    for thread in threads:thread.start()
    for thread in threads:thread.join(timeout=12);assert not thread.is_alive()
    assert sorted(results)==[200,503]
    assert len(rows(c.p.ledger))==1 and rows(c.p.ledger)[0][2]=='issued'
    assert sum(path=='/app/installations/88/access_tokens' for _,path in c.p.calls)==1


@pytest.mark.parametrize('change',['wall-regression','monotonic-regression','expiry','enrollment-revoked'])
def test_current_time_or_approval_change_cannot_deliver_another_credential(composed,change):
    c=composed;peer=c.enrolled()
    if change=='wall-regression':c.s.now-=1
    elif change=='monotonic-regression':
        # A selected monotonic port with a regressed history must fail itself.
        c.decision.last_mono=c.decision.end+1
    elif change=='expiry':c.s.now+=61
    else:c.s.facts=EnrollmentCurrent(c.s.authority.principal,c.s.authority.selection_digest,c.s.selection.ref,c.s.nonce,False,c.s.now,c.s.now+30)
    if change=='enrollment-revoked':assert c.call(peer,'/private',c.body).status==403
    else:
        with pytest.raises(BindingError):c.call(peer,'/private',c.body)
    assert c.p.calls==[] and rows(c.p.ledger)==[]


@pytest.mark.parametrize('field,value',[('role','broker'),('nonce','f'*64),('ref','issuance:other'),('url','https://example.invalid')])
def test_private_request_cannot_select_role_destination_or_approval(composed,field,value):
    c=composed;peer=c.enrolled()
    assert c.call(peer,'/private',{**c.body,field:value}).status in (403,503)
    assert c.p.calls==[] and rows(c.p.ledger)==[]


@pytest.mark.parametrize('changed',['ca','cert','key','resolver','provider-check'])
def test_late_selected_material_and_capability_substitution_refuses(composed,changed):
    c=composed;peer=c.enrolled()
    if changed in ('ca','cert','key'):
        path=Path(getattr(c.actor.provider.http,changed));path.write_bytes(path.read_bytes()+b'\n')
    elif changed=='resolver':c.actor.issuer.vault_credential=lambda **_:'unselected-credential'
    else:c.actor.provider.check=lambda:None
    assert c.call(peer,'/private',c.body).status in (403,503)
    assert c.p.calls==[] and rows(c.p.ledger)==[]


@pytest.mark.parametrize('group',['protection','source','control','arm','key','private'])
def test_already_overdrawn_enclosing_group_refuses_before_enrollment(composed,group):
    c=composed;b=ReadBudget(c.decision)
    b.state['counts'][group]={'protection':3,'source':4,'control':2,'arm':24,'key':3,'private':12}[group]+1
    assert c.call(c.bootstrap,'/enroll',c.s.raw).status==403
    assert rows(c.s.ledger)==[] and c.p.calls==[]


def test_replacing_operation_decision_cannot_renew_enrollment(composed):
    c=composed;c.actor.decision=Decision(clock=lambda:c.s.now)
    assert c.call(c.bootstrap,'/enroll',c.s.raw).status==403
    assert rows(c.s.ledger)==[] and c.p.calls==[]


def test_kernel_worker_cannot_resolve_selected_issuer_capability(composed):
    c=composed;process=None
    try:
        process=subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).with_name('credential_worker.py')),str(c.channel.fileno())],
            pass_fds=(c.channel.fileno(),),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            env={'PATH':os.defpath,'LANG':'C.UTF-8'})
        assert select.select([process.stdout],[],[],3)[0] and process.stdout.readline()==b'ready\n'
        ReadBudget(c.decision).consume('private')
        raw,_=process.communicate(canonical({'role':'issuer','operation':'resolver'})+b'\n',timeout=5)
        assert process.returncode==0 and json.loads(raw)['status']=='denied' and c.resolutions==[]
        assert c.actor._credential(deadline=c.decision.deadline)=='fixture-vault-credential'
        assert c.resolutions==[True] and ReadBudget(c.decision).count('private')==2
    finally:
        if process is not None:
            if process.poll() is None:process.kill()
            process.communicate()


@pytest.mark.parametrize('failure',['credential-channel','ca','cert','key'])
@pytest.mark.parametrize('outcome',['delivered','post-mint-refusal'])
def test_known_cleanup_handle_survives_issuance_dependency_failure(composed,tmp_path,failure,outcome):
    c=composed;source=c.p.transport();paths=[]
    for index,path in enumerate([source.ca,source.cert,source.key]):
        target=tmp_path/('private-selected-'+str(index)+'.pem');target.write_bytes(Path(path).read_bytes());target.chmod(0o600);paths.append(str(target))
    transport=PrivateHttps(ca_file=paths[0],certificate=paths[1],private_key=paths[2],fixture_origin=c.p.endpoint)
    c.actor=c.construct(transport=transport);peer=c.enrolled()
    if outcome=='post-mint-refusal':c.p.changes['permissions']=True
    result=c.call(peer,'/private',c.body)
    assert result.status==(200 if outcome=='delivered' else 503)
    cap=c.actor.pending(c.p.ref);use_until=cap.use_until;original=cap._decision
    before=list(c.p.calls)
    if failure=='credential-channel':c.channel.close()
    else:Path(getattr(transport,failure)).unlink()
    assert c.actor.pending(c.p.ref) is cap and cap.use_until==use_until and cap._decision is original
    assert c.p.calls==before and c.p.active[cap.credential]
    with pytest.raises(BindingError):c.actor.issuer.resolve(c.p.ref,c.p.nonce,decision=c.decision)
    assert c.cleanup(cap).retire()['state']=='retired' and not c.p.active[cap.credential]


def test_returned_mint_token_is_retained_before_postresponse_deadline_check(composed,monkeypatch):
    c=composed;peer=c.enrolled();original=PrivateHttps.exchange;triggered=[];deadline=c.decision.deadline;end=c.decision.end
    def exchange(http,method,url,**kwargs):
        result=original(http,method,url,**kwargs)
        if url==c.p.endpoint+'/app/installations/88/access_tokens' and not triggered:
            triggered.append(True);c.s.now+=11;c.p.now=c.s.now
        return result
    monkeypatch.setattr(PrivateHttps,'exchange',exchange);c.actor=c.construct()
    with pytest.raises(BindingError):c.call(peer,'/private',c.body)
    cap=c.actor.pending(c.p.ref)
    assert rows(c.p.ledger)[0][2]=='consumed' and cap.expires_at is None
    assert cap.use_until<=deadline and cap._decision is c.decision and c.decision.end==end
    assert c.p.active[cap.credential]
    assert sum(path=='/app/installations/88/access_tokens' for _,path in c.p.calls)==1
    with pytest.raises(BindingError):c.actor.issuer.resolve(c.p.ref,c.p.nonce,decision=Decision(clock=lambda:c.s.now))
    assert c.cleanup(cap).retire()['state']=='retired'


def test_returned_mint_token_is_retained_before_postresponse_material_check(composed,tmp_path,monkeypatch):
    c=composed;source=c.p.transport();paths=[]
    for index,path in enumerate([source.ca,source.cert,source.key]):
        target=tmp_path/('late-selected-'+str(index)+'.pem');target.write_bytes(Path(path).read_bytes());target.chmod(0o600);paths.append(str(target))
    transport=PrivateHttps(ca_file=paths[0],certificate=paths[1],private_key=paths[2],fixture_origin=c.p.endpoint)
    peer=c.enrolled();original=PrivateHttps.exchange;triggered=[]
    def exchange(http,method,url,**kwargs):
        result=original(http,method,url,**kwargs)
        if url==c.p.endpoint+'/app/installations/88/access_tokens' and not triggered:
            triggered.append(True);Path(paths[2]).unlink()
        return result
    monkeypatch.setattr(PrivateHttps,'exchange',exchange);c.actor=c.construct(transport=transport)
    assert c.call(peer,'/private',c.body).status in (403,503)
    cap=c.actor.pending(c.p.ref)
    assert cap.expires_at is None and rows(c.p.ledger)[0][2]=='consumed'
    assert c.p.active[cap.credential] and c.cleanup(cap).retire()['state']=='retired'


@pytest.mark.parametrize('field',['ledger','role','selection_digest','ref','_decision'])
def test_private_cleanup_lookup_keeps_original_capability_ownership(composed,field):
    c=composed;peer=c.enrolled();assert c.call(peer,'/private',c.body).status==200
    cap=c.actor.pending(c.p.ref)
    changes={'ledger':c.s.ledger,'role':'reader','selection_digest':digest({'wrong':True}),
             'ref':'issuance:other','_decision':Decision(clock=lambda:c.s.now)}
    c.actor.issuer._pending[c.p.ref]=replace(cap,**{field:changes[field]})
    try:
        with pytest.raises(BindingError):c.actor.pending(c.p.ref)
    finally:c.actor.issuer._pending[c.p.ref]=cap
    assert c.actor.pending(c.p.ref) is cap and c.p.active[cap.credential]


@pytest.mark.parametrize('cancel',[False,True])
def test_caller_reply_pair_closes_with_traceback_held_before_gc(composed,monkeypatch,cancel):
    c=composed;canary='PRIVATE-PAIR-CANCELLATION';pairs=[];raised=[];caught=None
    original_pair=composition.socket.socketpair;original_remaining=Decision.remaining
    owned=set()
    def pair(*args,**kwargs):
        reader,writer=original_pair(*args,**kwargs)
        owned.update(os.readlink('/proc/self/fd/'+str(x.fileno())) for x in (reader,writer))
        observer=reader.dup();pairs.append((reader,writer,observer));return reader,writer
    def remaining(decision):
        if decision is c.decision and pairs and not raised:
            raised.append(True)
            raise KeyboardInterrupt(canary) if cancel else RuntimeError(canary)
        return original_remaining(decision)
    monkeypatch.setattr(composition.socket,'socketpair',pair);monkeypatch.setattr(Decision,'remaining',remaining)
    try:
        try:composition.private(lambda:c.actor._credential(deadline=c.decision.deadline))
        except BaseException as error:caught=error
        assert type(caught) is (KeyboardInterrupt if cancel else BindingError)
        assert caught.__traceback__ is not None and caught.__context__ is None and caught.__cause__ is None
        assert canary not in repr(caught) and len(pairs)==1
        reader,writer,observer=pairs[0]
        assert reader.fileno()==writer.fileno()==-1
        observer.settimeout(.2);assert observer.recv(16)==b''
    finally:
        for reader,writer,observer in pairs:reader.close();writer.close();observer.close()
    # Other fixture threads may close unrelated descriptors during this call.
    # Inspect the two owned kernel socket identities, including any leaked alias.
    live=[]
    for name in os.listdir('/proc/self/fd'):
        try:live.append(os.readlink('/proc/self/fd/'+name))
        except FileNotFoundError:pass
    assert caught.__traceback__ is not None and len(owned)==2 and owned.isdisjoint(live)
