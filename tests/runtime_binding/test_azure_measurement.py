"""Connected P05 eligibility experiments; no deployed administration claim."""
from contextlib import ExitStack
from dataclasses import asdict, replace
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
import json
import os
import secrets
import stat
import time
import pytest
from workload_factory_binding.evidence import BindingError,canonical,digest
from workload_factory_binding_runtime.github_bootstrap.common import Decision,document
from workload_factory_binding_runtime.hosted.admission import PlanFacts
from workload_factory_binding_runtime.hosted.finalization import StagingReadback
from workload_factory_binding_runtime.hosted.nonces import NonceLedger
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
from workload_factory_binding_runtime.hosted.readback import DecisionRead,ReadBudget
from workload_factory_binding_runtime.azure_composition.local_host import (
    Scope,PeerApproval,LocalObserver,MeasurementServer,PROFILE)
from workload_factory_binding_runtime.azure_composition.remote_evidence import (
    MeasurementClient,WorkerRoots,RemoteBindings,RemoteFinalizer,VerifiedRemote)
from .launch_fixture import stage,v,g,rb,configuration,c,l,w
from .conftest import r
from .hosted_fixture import child_generations
from factory_binding.test_owner_integration import make_pki


@pytest.fixture
def measured(stage,tmp_path):
    v,rb=stage.v,stage.rb
    base=v.h.now;epoch=[None]
    def wall():
        now=base+(int(time.monotonic()-epoch[0]) if epoch[0] is not None else 0)
        v.h.now=rb.now=now
        return now
    scope=Scope(v.selected,v.context,'deployment:p05-fixture',
                ('principal:measurement-a','principal:measurement-b'))
    roots=WorkerRoots(tuple((k,str(p)) for k,p in stage.spec.roots.items()))
    result=SimpleNamespace(stage=stage,scope=scope,wall=wall,epoch=epoch,servers=[],clients=[],rows=[],pkis=[])
    with ExitStack() as cleanup:
        for index,principal in enumerate(scope.observer_refs):
            ca,server,gate,worker=make_pki(tmp_path/('observer-'+str(index)))
            directory=tmp_path/('nonce-'+str(index))
            identity=NonceLedger.initialize(directory)
            ledger=NonceLedger(directory,identity=identity)
            observer=LocalObserver(manager=stage.agent,scope=scope,principal=principal)
            approval=PeerApproval('principal:control-'+str(index),'control',v.context.source_commit,
                scope.record()['host_ref'],scope.record()['incarnation_ref'],digest(scope.record()),base-1,base+30)
            peers={'sha256:'+gate[2]:approval}
            service=MeasurementServer(observer=observer,ledger=ledger,peers=peers,
                cert_file=str(server[0]),key_file=str(server[1]),ca_file=str(ca),clock=wall,monotonic=time.monotonic)
            thread=Thread(target=lambda service=service:service.serve_forever(poll_interval=.01))
            thread.start()
            def stop(service=service,thread=thread):
                service.shutdown();service.server_close();thread.join(timeout=3)
                assert not thread.is_alive()
            cleanup.callback(stop)
            stage.spec.private=(*stage.spec.private,server[1],gate[1],worker[1],directory/'issuance.sqlite')
            origin='https://127.0.0.1:'+str(service.server_port)
            transport=PrivateHttps(ca_file=str(ca),certificate=str(gate[0]),private_key=str(gate[1]),
                observation_origin=origin,server_certificate_digest='sha256:'+server[2])
            client=MeasurementClient(scope=scope,principal=principal,transport=transport,
                credential_origin='credential-origin:observer-'+str(index),approval_origin='approval-origin:observer-'+str(index),
                not_before=base-1,expires_at=base+30,milliseconds=1000)
            result.servers.append(service);result.clients.append(client);result.pkis.append((ca,server,gate,worker))
        # Original retained manager launches exactly one real confined worker.
        wall()
        try:
            ready=stage.protected.read(v.context,v.token,decision=stage.use())
        except BaseException as error:
            import traceback
            # Fixed structural diagnostics only; never exception text or locals.
            (tmp_path/'setup-failure.json').write_text(json.dumps(dict(
                phase='inherited protected stage before P05 original decision',
                kind=type(error).__name__,frames=[dict(file=Path(f.filename).name,line=f.lineno,name=f.name)
                    for f in traceback.extract_tb(error.__traceback__)]),indent=2))
            raise
        assert ready.state=='running'
        # Authenticated generation selection precedes this P05 operation. It is
        # not substituted for the producers' six current original-store reads.
        status=stage.host.status(scope.record()['launch_ref'],decision=stage.use())
        unit=status['unit'];owned=status['generation']
        generation={k:scope.record()[k] for k in ('launch_ref','host_ref','incarnation_ref','boot_id')}
        generation.update(invocation_ref=unit['invocation_ref'],pid=owned['pid'],start_time=owned['start_time'])
        result.generation=generation
        # Administrative/provider contents are explicit local fixture doubles;
        # the capability actually opens protected current state on every call.
        state=tmp_path/'current-control-state.json';state.write_bytes(canonical(asdict(v.facts)));state.chmod(0o600)
        info=state.stat();identity=(info.st_dev,info.st_ino);result.fact_reads=[]
        def current_facts(ref,*,decision):
            assert ref==v.context.preauthorization_ref
            fd=os.open(state,os.O_RDONLY|os.O_NOFOLLOW)
            try:
                info=os.fstat(fd)
                if not (stat.S_ISREG(info.st_mode) and info.st_uid==os.geteuid() and not info.st_mode&0o077 and (info.st_dev,info.st_ino)==identity):raise BindingError('fixture-current-state-refused')
                raw=os.read(fd,16385)
            finally:os.close(fd)
            value=document(raw,16384);now=decision.now();result.fact_reads.append(now)
            value['observed_at']=now;value['expires_at']=min(value['expires_at'],decision.deadline)
            return PlanFacts(**value)
        github=rb.github()
        plan=replace(v.protected,clock=wall,monotonic=time.monotonic,
            facts_principal=v.facts.principal_ref,read_facts=DecisionRead(current_facts),
            environment_principal=rb.primary.principal,read_environment=DecisionRead(github.environment))
        frozen_raw=bytes(v.raw)
        independent=replace(plan,load_plan=lambda:frozen_raw,clock=lambda:wall(),monotonic=lambda:time.monotonic())
        result.stage_reads=[]
        def current_stage(ref,*,decision):
            lease=stage.agent.authority.acknowledged(stage.scope,unit,decision=decision)
            result.stage_reads.append(lease['expires_at'])
            return StagingReadback(stage.authority.lease.principal,v.selected.digest,scope.record()['case_ref'],
                v.context.run_id,v.context.run_attempt,ref,v.plan['staging_policy']['cleanup_ref'],
                dict(generation),'cleanup-acknowledged',decision.now(),min(lease['expires_at'],decision.deadline))
        binding=RemoteBindings(plan,independent,*result.clients,roots,stage.authority.lease.principal,
                               DecisionRead(current_stage),'principal:final-authority')
        result.binding=binding;result.finalizer=RemoteFinalizer(binding);result.state=state
        # The P05 real elapsed clock is selected once, after independent fixture
        # setup/launch. No P05 Decision exists before this point; never reset it.
        epoch[0]=time.monotonic()
        result.use=lambda:Decision(clock=wall,monotonic=time.monotonic)
        yield result


def connected(p,tmp_path):
    use=p.use();end=use.end;start=time.monotonic();local_reads=[]
    originals=[s.observer._row for s in p.servers]
    # Instrument actual producer reads without replacing their implementation.
    from workload_factory_binding_runtime.azure_composition.local_host import LocalObserver
    original=LocalObserver._row
    def tracked(observer,decision):
        value=original(observer,decision);local_reads.append(observer.principal);return value
    LocalObserver._row=tracked
    try:result=p.finalizer.finalize(p.stage.v.context,p.stage.v.token,decision=use)
    finally:LocalObserver._row=original
    elapsed=time.monotonic()-start;b=ReadBudget(use)
    assert type(result) is VerifiedRemote
    assert result._generation==canonical(p.generation)
    assert use.end==end
    assert b.count('private') == 9
    assert b.count('protection') == 12
    assert b.state['protection_observations'] == 6
    assert len(b.state['members']) == 2
    assert len(p.fact_reads) == 12
    assert len(p.stage_reads) == 6
    assert local_reads.count(p.scope.observer_refs[0]) == 4
    assert local_reads.count(p.scope.observer_refs[1]) == 2
    assert elapsed < 10
    assert use.remaining() > 0
    proof=dict(scope='isolated connected P05 eligibility only',private=9,protection=12,github=b.github_requests,
        local_current_facts=len(p.fact_reads),fresh_stage_leases=len(p.stage_reads),
        actual_original_manager_journal_reads=len(local_reads),independent_observers=2,
        elapsed_seconds=elapsed,remaining_seconds=use.remaining(),original_monotonic_end_preserved=True,
        configuration_bytes=len(result._configuration),policy_bytes=len(result._policy),
        generation_digest=digest(p.generation),independent_root_derivation=True,
        admin_provider_facts='explicit fixture doubles; no live issuer/provider/enrollment qualification')
    (tmp_path/'connected-proof.json').write_text(json.dumps(proof,indent=2))
    return result,use


def test_connected_original_manager_two_observers_complete_derivation_and_original_budget(measured,tmp_path):
    result,use=connected(measured,tmp_path)
    assert result._configuration
    assert result._policy
    assert len(measured.stage.agent.children)==1


def test_known_available_measurement_explicitly_denies_valid_worker_preimage(measured,tmp_path):
    p=measured;result,use=connected(p,tmp_path)
    ca,server,gate,worker=p.pkis[0]
    transport=PrivateHttps(ca_file=str(ca),certificate=str(worker[0]),private_key=str(worker[1]),
        observation_origin=p.clients[0].origin,server_certificate_digest='sha256:'+server[2])
    request=canonical(dict(profile=PROFILE,operation='measure',request_nonce=secrets.token_hex(32),
        **{k:p.scope.record()[k] for k in ('deployment_ref','plan_digest','case_ref','source_commit','run_id','run_attempt','launch_ref')},
        deadline=use.deadline,remaining_milliseconds=500))
    ReadBudget(use).consume('private')
    response=transport.exchange('POST',p.clients[0].origin+'/readback',
        headers={'Content-Type':'application/json','Accept':'application/json'},body=request,decision=use)
    assert response.status==403
    assert document(response.body)=={'error':'azure-measurement-denied'}
    # The exact body denied to the worker is valid for the approved control peer.
    ReadBudget(use).consume('private')
    accepted=p.clients[0].transport.exchange('POST',p.clients[0].origin+'/readback',
        headers={'Content-Type':'application/json','Accept':'application/json'},body=request,decision=use)
    assert accepted.status==200
    assert document(accepted.body)['request_nonce']==document(request)['request_nonce']


def test_reconstructed_manager_cannot_adopt_original_owned_process(measured):
    from workload_factory_binding_runtime.hosted.host_agent import HostAgent
    from workload_factory_binding_runtime.azure_composition.local_host import LocalClock
    p=measured
    # Known current service positive precedes the ownership mutation.
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    original=p.stage.agent
    clone=HostAgent(worker=original.worker,store=original.store,authority=original.authority)
    clone.children=dict(original.children)
    try:
        observer=LocalObserver(manager=clone,scope=p.scope,principal=p.scope.observer_refs[0])
        with pytest.raises(BindingError):observer.read(use=LocalClock(p.wall,time.monotonic,p.wall()+5,1000))
    finally:
        # Clone owns no worker generation: never stop the original's copied child.
        clone.children.clear();clone.close()
    assert original.children[p.scope.record()['launch_ref']].poll() is None


def test_source_peer_approval_change_refuses_before_measurement_nonce_consumption(measured):
    from dataclasses import replace
    import sqlite3
    p=measured
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    server=p.servers[0];key=next(iter(server.peers))
    with sqlite3.connect(server.ledger.directory/'issuance.sqlite') as db:before=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
    server.peers[key]=replace(server.peers[key],source_commit='f'*40)
    with pytest.raises(BindingError):p.clients[0].read(decision=p.use())
    with sqlite3.connect(server.ledger.directory/'issuance.sqlite') as db:after=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
    assert after==before


def test_consumed_measurement_nonce_cannot_replay_after_success(measured):
    p=measured;server=p.servers[0];saved=[];actual=server.measure
    def capture(raw,peer):saved.append(raw);return actual(raw,peer)
    server.measure=capture
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    use=p.use();ReadBudget(use).consume('private')
    response=p.clients[0].transport.exchange('POST',p.clients[0].origin+'/readback',
        headers={'Content-Type':'application/json','Accept':'application/json'},body=saved[0],decision=use)
    assert response.status==400
    assert document(response.body)=={'error':'azure-measurement-refused'}


WIRE_MUTATIONS=('profile','missing_nonce','nonce','duplicate','noncanonical','extra','oversized',
                'principal','observer_refs','deployment','plan','case','source','run','attempt',
                'launch','host','incarnation','boot','pid_bool','start_bool','invocation',
                'configuration_type','policy_type','observed_bool','observed_future','expiry','expiry_bool')

@pytest.mark.parametrize('change',WIRE_MUTATIONS)
def test_authenticated_response_cannot_change_closed_canonical_scope(measured,change):
    p=measured;client=p.clients[0];server=p.servers[0]
    assert client.read(decision=p.use()).generation==canonical(p.generation)
    actual=server.measure
    def altered(raw,peer):
        value=document(actual(raw,peer))
        if change=='profile':value['profile']='openxfactory-azure-local-measurement-internal-v1'
        elif change=='missing_nonce':del value['request_nonce']
        elif change=='nonce':value['request_nonce']='f'*64
        elif change=='duplicate':return canonical(value)[:-1]+b',"request_nonce":'+canonical(value['request_nonce'])+b'}'
        elif change=='noncanonical':return b' '+canonical(value)
        elif change=='extra':value['unexpected']=True
        elif change=='oversized':
            value['configuration']['case_ref']='case:'+('x'*6000)
            value['policy']['grant_ref']='grant:'+('y'*6000)
            assert len(canonical(value['configuration']))<=16384
            assert len(canonical(value['policy']))<=16384
            assert len(canonical(value))>16384
        elif change=='principal':value['principal_ref']='principal:unselected'
        elif change=='observer_refs':value['independent_observer_refs'].reverse()
        elif change=='pid_bool':value['pid']=True
        elif change=='start_bool':value['start_time']=True
        elif change=='configuration_type':value['configuration']='digest-only'
        elif change=='policy_type':value['policy']='digest-only'
        elif change=='observed_bool':value['observed_at']=True
        elif change=='observed_future':value['observed_at']+=20
        elif change=='expiry':value['expires_at']+=1
        elif change=='expiry_bool':value['expires_at']=True
        else:
            key={'deployment':'deployment_ref','plan':'plan_digest','case':'case_ref','source':'source_commit',
                 'run':'run_id','attempt':'run_attempt','launch':'launch_ref','host':'host_ref',
                 'incarnation':'incarnation_ref','boot':'boot_id','invocation':'invocation_ref'}[change]
            value[key]=('invalid?invocation' if change=='invocation' else
                        '2' if key=='run_attempt' else 'unselected:'+value[key])
        return canonical(value)
    server.measure=altered
    with pytest.raises(BindingError) as error:client.read(decision=p.use())
    assert str(error.value)=='azure-measurement-refused'
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


@pytest.mark.parametrize('change',('source','scope','host','incarnation','role','not_before','expiry'))
def test_effective_peer_authority_precedes_durable_attempt(measured,change):
    import sqlite3
    p=measured;server=p.servers[0];client=p.clients[0]
    assert client.read(decision=p.use()).generation==canonical(p.generation)
    key=next(iter(server.peers));approved=server.peers[key]
    changes=dict(source=dict(source_commit='e'*40),scope=dict(scope_digest=digest({'unapproved':True})),
        host=dict(host_ref='host:foreign'),incarnation=dict(incarnation_ref='incarnation:foreign'),
        role=dict(role='worker'),not_before=dict(not_before=p.wall()+20),expiry=dict(expires_at=p.wall()))
    with sqlite3.connect(server.ledger.directory/'issuance.sqlite') as db:before=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
    server.peers[key]=replace(approved,**changes[change])
    with pytest.raises(BindingError):client.read(decision=p.use())
    with sqlite3.connect(server.ledger.directory/'issuance.sqlite') as db:after=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
    assert after==before


@pytest.mark.parametrize('change',('worker','configuration','namespace','creator','scope','unit','generation','lease','store','stopped'))
def test_actual_original_manager_or_protected_target_change_refuses(measured,change):
    import sqlite3
    p=measured;client=p.clients[0];manager=p.stage.agent
    assert client.read(decision=p.use()).generation==canonical(p.generation)
    if change=='worker':p.stage.spec.paths['worker'].write_bytes(b'# changed source\n')
    elif change=='configuration':p.stage.spec.paths['configuration'].chmod(0o600);p.stage.spec.paths['configuration'].write_bytes(b'{}')
    elif change=='namespace':
        info=Path('/proc/self/ns/net').stat();foreign=(info.st_dev,info.st_ino)
        manager.pid_namespace=p.servers[0].observer._namespace=foreign
    elif change=='creator':
        from concurrent.futures import ThreadPoolExecutor
        other=ThreadPoolExecutor(max_workers=1)
        original=manager.launch_owner
        manager.launch_owner=other
        try:
            with pytest.raises(BindingError):client.read(decision=p.use())
        finally:manager.launch_owner=original;other.shutdown(wait=True)
        return
    elif change=='store':
        from workload_factory_binding_runtime.hosted.stage_store import StageStore
        manager.store=StageStore(manager.store.directory,identity=manager.store.identity,kind='host')
    elif change=='stopped':
        process=manager.children[p.scope.record()['launch_ref']]
        process.terminate();process.communicate(timeout=3)
    else:
        with sqlite3.connect(manager.store.directory/'staging.sqlite') as db:
            scope,unit,generation,lease=db.execute('SELECT scope,unit,generation,lease FROM stages').fetchone()
            scope,unit,generation,lease=map(document,(scope,unit,generation,lease))
            if change=='scope':scope['case_ref']='case:foreign'
            elif change=='unit':
                unit['manager_pid']+=1
                generation['unit_digest']=lease['unit_digest']=digest(unit)
            elif change=='generation':generation['start_time']+=1
            else:lease['unit_digest']=digest({'wrong':True})
            db.execute('UPDATE stages SET scope=?,unit=?,generation=?,lease=?',tuple(map(canonical,(scope,unit,generation,lease))))
    with pytest.raises(BindingError):client.read(decision=p.use())


@pytest.mark.parametrize('change',('configuration','policy','roots'))
def test_two_agreeing_observers_cannot_replace_independent_complete_derivation(measured,tmp_path,change):
    p=measured
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    if change=='roots':
        entries=list(p.binding.roots.entries);key,value=entries[0];entries[0]=(key,value+'-foreign')
        finalizer=RemoteFinalizer(replace(p.binding,roots=WorkerRoots(tuple(entries))))
    else:
        for server in p.servers:
            actual=server.measure
            def altered(raw,peer,actual=actual):
                value=document(actual(raw,peer))
                if change=='configuration':value['configuration']['lifecycle']['cleanup_ref']='cleanup:unapproved'
                else:value['policy']['grant_ref']='grant:unapproved'
                return canonical(value)
            server.measure=altered
        first=p.clients[0].read(decision=p.use());second=p.clients[1].read(decision=p.use())
        assert first.configuration==second.configuration
        assert first.policy==second.policy
        finalizer=p.finalizer
    with pytest.raises(BindingError):finalizer.finalize(p.stage.v.context,p.stage.v.token,decision=p.use())


@pytest.mark.parametrize('change',('credential_origin','approval_origin','principal','server_pin','ca'))
def test_collapsed_observer_selection_is_ineligible(measured,change):
    p=measured;a,b=p.clients
    assert a.read(decision=p.use()).generation==canonical(p.generation)
    kwargs=dict(scope=b.scope,principal=b.principal,transport=b.transport,
        credential_origin=b.credential_origin,approval_origin=b.approval_origin,
        not_before=b.not_before,expires_at=b.expires_at)
    if change in ('credential_origin','approval_origin','principal'):kwargs[change]=getattr(a,change)
    else:
        transport=PrivateHttps(ca_file=a.transport.ca if change=='ca' else b.transport.ca,
            certificate=str(b.transport.cert),private_key=str(b.transport.key),observation_origin=b.origin,
            server_certificate_digest=a.transport.server_certificate_digest if change=='server_pin' else b.transport.server_certificate_digest)
        kwargs['transport']=transport
    other=MeasurementClient(**kwargs)
    with pytest.raises(BindingError):RemoteFinalizer(replace(p.binding,independent=other))


def test_final_tls_material_checkpoint_refuses_fixed_interval_before_go(measured,monkeypatch):
    p=measured;client=p.clients[0];server=p.servers[0]
    assert client.read(decision=p.use()).generation==canonical(p.generation)
    actual_exchange=PrivateHttps.exchange;actual_materials=PrivateHttps.materials
    calls=[];armed=[];use=p.use();actual_measure=server.measure
    def measured_request(raw,peer):calls.append(True);return actual_measure(raw,peer)
    server.measure=measured_request
    def exchange(transport,*args,**kwargs):
        callback=kwargs['before_send']
        def checkpoint():callback();armed.append(transport)
        kwargs['before_send']=checkpoint
        return actual_exchange(transport,*args,**kwargs)
    def materials(transport):
        value=actual_materials(transport)
        if armed and armed[-1] is transport:
            armed.clear();use.end=time.monotonic()+.5
        return value
    monkeypatch.setattr(PrivateHttps,'exchange',exchange)
    monkeypatch.setattr(PrivateHttps,'materials',materials)
    with pytest.raises(BindingError):client.read(decision=use)
    assert not calls


@pytest.mark.parametrize('change',('wall','monotonic','deadline_extension','end_extension','clock_rebind','ledger_replace','counts_replace','private_regression'))
def test_original_authority_cannot_expire_renew_or_reset_during_current_reads(measured,change):
    from workload_factory_binding_runtime.hosted.readback import start_finalization
    p=measured;original=p.binding.plan.read_facts.reader;changed=[]
    use=p.use();start_finalization(use);ReadBudget(use).consume('private')
    def current(ref,*,decision):
        value=original(ref,decision=decision)
        if not changed:
            changed.append(True)
            if change=='wall':decision.deadline=decision.now()
            elif change=='monotonic':decision.end=decision.monotonic()
            elif change=='deadline_extension':
                decision.deadline+=1;value=replace(value,expires_at=decision.deadline)
            elif change=='end_extension':decision.end+=1
            elif change=='clock_rebind':decision.clock=lambda:value.observed_at
            elif change=='ledger_replace':decision._hosted_reads=dict(decision._hosted_reads)
            elif change=='counts_replace':decision._hosted_reads['counts']=dict(decision._hosted_reads['counts'])
            else:decision._hosted_reads['counts']['private']=0
        return value
    finalizer=RemoteFinalizer(replace(p.binding,plan=replace(p.binding.plan,read_facts=DecisionRead(current))))
    with pytest.raises(BindingError):finalizer.finalize(p.stage.v.context,p.stage.v.token,decision=use)
    assert changed


@pytest.mark.parametrize('change',('revoked','source','replacement'))
def test_current_local_control_state_changes_after_observation_refuse(measured,change):
    p=measured;server=p.servers[0];actual=server.measure;changed=[]
    def measured_then_changed(raw,peer):
        reply=actual(raw,peer)
        if not changed:
            value=document(p.state.read_bytes())
            if change=='revoked':value['state']='revoked'
            elif change=='source':value['accepted_commit']='f'*40
            if change=='replacement':
                replacement=p.state.with_suffix('.replacement');replacement.write_bytes(canonical(value));replacement.chmod(0o600);replacement.replace(p.state)
            else:p.state.write_bytes(canonical(value))
            changed.append(True)
        return reply
    server.measure=measured_then_changed
    with pytest.raises(BindingError):p.finalizer.finalize(p.stage.v.context,p.stage.v.token,decision=p.use())
    assert changed


@pytest.mark.parametrize('change',('missing','replaced','object'))
def test_measurement_nonce_state_is_existing_selected_and_not_reinitialized(measured,tmp_path,change):
    p=measured;server=p.servers[0]
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    directory=server.ledger.directory
    if change=='missing':(directory/'issuance.sqlite').unlink()
    elif change=='replaced':
        replacement=directory/'replacement';replacement.write_bytes((directory/'issuance.sqlite').read_bytes());replacement.chmod(0o600);replacement.replace(directory/'issuance.sqlite')
    else:
        other=tmp_path/'other-nonce';identity=NonceLedger.initialize(other)
        server.ledger=NonceLedger(other,identity=identity)
    with pytest.raises(BindingError):p.clients[0].read(decision=p.use())
    if change=='missing':assert not (directory/'issuance.sqlite').exists()


def test_lost_response_keeps_durable_nonce_consumed(measured):
    import sqlite3
    p=measured;server=p.servers[0];actual=server.measure;requests=[]
    def lost(raw,peer):
        result=actual(raw,peer);requests.append(raw)
        raise OSError('private-measurement-canary')
    server.measure=lost
    with pytest.raises(BindingError) as error:p.clients[0].read(decision=p.use())
    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    nonce=document(requests[0])['request_nonce']
    with sqlite3.connect(server.ledger.directory/'issuance.sqlite') as db:
        row=db.execute('SELECT state FROM attempts WHERE nonce=?',(nonce,)).fetchone()
    assert row==('consumed',)
    server.measure=actual
    use=p.use();ReadBudget(use).consume('private')
    result=p.clients[0].transport.exchange('POST',p.clients[0].origin+'/readback',
        headers={'Content-Type':'application/json','Accept':'application/json'},body=requests[0],decision=use)
    assert result.status==400


@pytest.mark.parametrize('surface',('client','observed','verified'))
def test_normal_state_export_cannot_disclose_private_selected_material(measured,tmp_path,surface):
    import copy,pickle
    p=measured
    if surface=='client':value=p.clients[0]
    elif surface=='observed':value=p.clients[0].read(decision=p.use())
    else:value,_=connected(p,tmp_path)
    ca,server,gate,worker=p.pkis[0]
    private_values=(str(gate[1]),p.clients[0].origin,gate[1].read_text())
    for rendered in (str(value),repr(value)):
        assert all(secret not in rendered for secret in private_values)
    for operation in (lambda:vars(value),lambda:value.__getstate__(),lambda:pickle.dumps(value),lambda:copy.deepcopy(value)):
        with pytest.raises((BindingError,TypeError)) as error:operation()
        assert all(secret not in str(error.value) for secret in private_values)
        assert error.value.__cause__ is None


def test_cancelled_tls_attempt_reaps_helper_without_private_error_context(measured,monkeypatch):
    p=measured;client=p.clients[0]
    assert client.read(decision=p.use()).generation==canonical(p.generation)
    actual=PrivateHttps.exchange
    def exchange(transport,*args,**kwargs):
        def cancelled():raise KeyboardInterrupt('private-measurement-cancellation-canary')
        kwargs['before_send']=cancelled
        return actual(transport,*args,**kwargs)
    monkeypatch.setattr(PrivateHttps,'exchange',exchange)
    with pytest.raises(KeyboardInterrupt) as error:client.read(decision=p.use())
    assert error.value.args==()
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


@pytest.mark.parametrize('change',('invocation_ref','pid','start_time'))
def test_well_typed_foreign_generation_cannot_construct_verified_handoff(measured,change):
    p=measured;server=p.servers[0];actual=server.measure
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    def foreign(raw,peer):
        value=document(actual(raw,peer))
        value[change]='invocation:foreign' if change=='invocation_ref' else value[change]+1
        return canonical(value)
    server.measure=foreign
    with pytest.raises(BindingError):p.finalizer.finalize(p.stage.v.context,p.stage.v.token,decision=p.use())


@pytest.mark.parametrize('change',('ca','server_pin','client_certificate'))
def test_real_tls_requires_selected_server_and_client_material(measured,change):
    p=measured;a,b=p.clients
    assert a.read(decision=p.use()).generation==canonical(p.generation)
    transport=PrivateHttps(ca_file=b.transport.ca if change=='ca' else a.transport.ca,
        certificate=b.transport.cert if change=='client_certificate' else a.transport.cert,
        private_key=b.transport.key if change=='client_certificate' else a.transport.key,
        observation_origin=a.origin,server_certificate_digest='sha256:'+'f'*64 if change=='server_pin' else a.transport.server_certificate_digest)
    selected=MeasurementClient(scope=a.scope,principal=a.principal,transport=transport,
        credential_origin=a.credential_origin,approval_origin=a.approval_origin,
        not_before=a.not_before,expires_at=a.expires_at)
    with pytest.raises(BindingError):selected.read(decision=p.use())
    assert a.read(decision=p.use()).generation==canonical(p.generation)


@pytest.mark.parametrize('change',('ca','client_certificate','client_key','server_key'))
def test_selected_material_bytes_are_rechecked_before_measurement(measured,change):
    p=measured;a=p.clients[0]
    assert a.read(decision=p.use()).generation==canonical(p.generation)
    path=Path({'ca':a.transport.ca,'client_certificate':a.transport.cert,
               'client_key':a.transport.key,'server_key':p.pkis[0][1][1]}[change])
    original=path.read_bytes();path.write_bytes(original+b'\n')
    try:
        with pytest.raises(BindingError):a.read(decision=p.use())
    finally:path.write_bytes(original)
    assert a.read(decision=p.use()).generation==canonical(p.generation)


@pytest.mark.parametrize('position',range(1,7))
def test_each_current_stage_lease_is_required_at_its_original_checkpoint(measured,position):
    p=measured;ref=p.scope.record()['launch_ref'];original=p.binding.read_stage.reader;calls=[]
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    assert p.binding.read_stage(ref,decision=p.use()).state=='cleanup-acknowledged'
    def current(ref,*,decision):
        calls.append(len(calls)+1)
        if len(calls)==position:
            path=p.stage.rb.stage_lease_path;value=document(path.read_bytes());value['state']='revoked';path.write_bytes(canonical(value))
        return original(ref,decision=decision)
    selected=RemoteFinalizer(replace(p.binding,read_stage=DecisionRead(current)))
    with pytest.raises(BindingError):selected.finalize(p.stage.v.context,p.stage.v.token,decision=p.use())
    assert len(calls)==position


@pytest.mark.parametrize('observer',(0,1))
def test_late_actual_protection_change_after_observer_io_refuses(measured,observer):
    p=measured;service=p.servers[observer];actual=service.measure;changed=[]
    def observed_then_changed(raw,peer):
        result=actual(raw,peer)
        if not changed:
            p.stage.rb.policies['branch_policies'][0]['type']='tag';changed.append(True)
        return result
    service.measure=observed_then_changed
    with pytest.raises(BindingError):p.finalizer.finalize(p.stage.v.context,p.stage.v.token,decision=p.use())
    assert changed


def test_independent_observer_does_not_accept_dead_worker_with_fresh_echo(measured):
    p=measured;service=p.servers[0];actual=service.measure;stopped=[]
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    def observed_then_stopped(raw,peer):
        result=actual(raw,peer)
        process=p.stage.agent.children[p.scope.record()['launch_ref']]
        process.terminate();process.communicate(timeout=3);stopped.append(True)
        return result
    service.measure=observed_then_stopped
    with pytest.raises(BindingError):p.finalizer.finalize(p.stage.v.context,p.stage.v.token,decision=p.use())
    assert stopped


def test_server_cancellation_after_reservation_keeps_attempt_consumed(measured,monkeypatch):
    import sqlite3
    p=measured;service=p.servers[0];requests=[];actual=service.measure
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    def capture(raw,peer):requests.append(raw);return actual(raw,peer)
    service.measure=capture
    original=LocalObserver.read
    def cancel(observer,*,use):
        if observer is service.observer:raise KeyboardInterrupt('private-server-cancellation-canary')
        return original(observer,use=use)
    monkeypatch.setattr(LocalObserver,'read',cancel)
    with pytest.raises(BindingError) as error:p.clients[0].read(decision=p.use())
    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    nonce=document(requests[0])['request_nonce']
    with sqlite3.connect(service.ledger.directory/'issuance.sqlite') as db:state=db.execute('SELECT state FROM attempts WHERE nonce=?',(nonce,)).fetchone()
    assert state==('consumed',)



def test_final_observation_is_followed_by_actual_current_control_state(measured):
    p=measured;service=p.servers[0];actual=service.measure;calls=[]
    assert p.clients[0].read(decision=p.use()).generation==canonical(p.generation)
    def observed_then_revoked(raw,peer):
        result=actual(raw,peer);calls.append(True)
        if len(calls)==2:
            value=document(p.state.read_bytes());value['state']='revoked';p.state.write_bytes(canonical(value))
        return result
    service.measure=observed_then_revoked
    with pytest.raises(BindingError):p.finalizer.finalize(p.stage.v.context,p.stage.v.token,decision=p.use())
    assert len(calls)==2
