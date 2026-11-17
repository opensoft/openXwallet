"""T012R source-only staged launch boundaries; no operational host activation."""
import pytest
from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.hosted.stage_store import StageStore
from workload_factory_binding_runtime.hosted.worker_sandbox import install


def test_missing_stage_store_is_not_initialized_by_runtime(tmp_path):
    path=tmp_path/"missing"
    with pytest.raises(BindingError):StageStore(path,identity=(1,2,3,4),kind="controller")
    assert not path.exists()

from concurrent.futures import ThreadPoolExecutor
import json,os,sys,subprocess
from pathlib import Path
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from .hosted_fixture import child_generations
from .worker_runtime import system_runtime


def use():return Decision(clock=lambda:1000,monotonic=lambda:0.)


def test_stage_reservation_is_durable_and_concurrent_winner_is_unique(tmp_path):
    path=tmp_path/"state";identity=StageStore.initialize(path,kind="controller")
    def reserve(_):return StageStore(path,identity=identity,kind="controller").reserve("launch:one",{"source":"fixed"},decision=use())
    with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(reserve,range(8)))
    assert results.count(True)==1
    store=StageStore(path,identity=identity,kind="controller")
    assert store.read("launch:one",decision=use())["state"]=="reserved"
    reserve_decision = use()
    with pytest.raises(BindingError):store.reserve("launch:one",{"source":"changed"},decision=reserve_decision)


@pytest.mark.parametrize("change",["directory","database","permissions","schema","kind","clock"])
def test_stage_store_loss_replacement_or_regression_never_recreates_scope(tmp_path,change):
    path=tmp_path/"state";identity=StageStore.initialize(path,kind="host");store=StageStore(path,identity=identity,kind="host")
    store.reserve("launch:one",{"source":"fixed"},decision=use())
    if change=="database":(path/"staging.sqlite").unlink()
    elif change=="directory":path.rename(tmp_path/"old")
    elif change=="permissions":(path/"staging.sqlite").chmod(0o644)
    elif change=="schema":
        import sqlite3
        with sqlite3.connect(path/"staging.sqlite") as db:db.execute("DROP TABLE stages")
    elif change=="kind":store.kind="controller"
    else:
        late=Decision(clock=lambda:999,monotonic=lambda:0.)
        with pytest.raises(BindingError):store.read("launch:one",decision=late)
        return
    existed=path.exists();db_existed=(path/"staging.sqlite").exists()
    read_decision = use()
    with pytest.raises(BindingError):store.read("launch:one",decision=read_decision)
    assert path.exists()==existed
    assert (path/"staging.sqlite").exists()==db_existed


@pytest.mark.parametrize("transition",[("reserved","running"),("registered","running"),("running","registered"),("indeterminate","registered")])
def test_stage_state_cannot_skip_consumption_or_reopen_old_attempt(tmp_path,transition):
    path=tmp_path/"state";identity=StageStore.initialize(path,kind="host");store=StageStore(path,identity=identity,kind="host")
    store.reserve("launch:one",{"source":"fixed"},decision=use())
    transition_decision = use()
    with pytest.raises(BindingError):store.transition("launch:one",*transition,decision=transition_decision)


@pytest.fixture
def sandbox_case(tmp_path):
    root=Path(__file__).resolve().parents[2];probe=tmp_path/"probe.py";config=tmp_path/"config.json";private=tmp_path/"controller-key.pem"
    private.write_text("fixture-private-value");private.chmod(0o600)
    probe.write_text("""import json,os,socket,ctypes,sys
value=json.load(open(sys.argv[1]));results={}
for name,path,mode in [('key',value['key'],'r'),('config',sys.argv[1],'w'),('source',__file__,'w')]:
 try:
  with open(path,mode) as stream:
   if mode=='r':stream.read()
  results[name]='allowed'
 except PermissionError:results[name]='denied'
for name,family in [('imds',socket.AF_INET),('control',socket.AF_UNIX)]:
 try:s=socket.socket(family);s.close();results[name]='allowed'
 except PermissionError:results[name]='denied'
try:
 child=os.fork()
 if child==0:os._exit(0)
 os.waitpid(child,0);results['fork']='allowed'
except PermissionError:results['fork']='denied'
try:os.chmod(sys.argv[1],0o644);results['metadata']='allowed'
except PermissionError:results['metadata']='denied'
results['fence']='denied' if ctypes.CDLL(None).prctl(1,0,0,0,0)==-1 else 'allowed'
results['uid']=os.geteuid();results['no_new_privs']=ctypes.CDLL(None).prctl(39,0,0,0,0)
print(json.dumps(results),flush=True)
""")
    config.write_text(json.dumps({'key':str(private)}));probe.chmod(0o444);config.chmod(0o444)
    from workload_factory_binding_runtime.hosted.host_agent import loader_for
    selected,runtime=system_runtime();exe=str(selected);loader=str(loader_for(selected))
    directories=[str(x) for x in runtime]
    message={'files':[exe,loader,str(probe),str(config)],'directories':directories,'execute':[exe,loader],
             'argv':[exe,'-I','-B',str(probe),str(config)],'uid':os.geteuid(),'gid':os.getegid(),'parent_pid':os.getpid()}
    helper=root/'scripts/workload_factory_binding_runtime/hosted/_launch_exec.py'
    def run(change=None):
        value=json.loads(json.dumps(message))
        if change=='key-read':value['files'].append(str(private))
        if change in ('-c','--help'):value['argv'][3:]=[change,'print(12345)']
        process=subprocess.Popen([exe,'-I','-B',str(helper)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 env={'PATH':os.defpath,'LANG':'C.UTF-8'})
        try:out,error=process.communicate(json.dumps(value).encode()+b'\n',timeout=5)
        except BaseException:process.kill();process.communicate();raise
        if change in ('-c','--help'):
            assert process.returncode==2
            assert out==b''
            return
        assert process.returncode==0,error.decode(errors='replace')
        return json.loads(out)
    return run


def test_actual_worker_sandbox_has_allowed_controls_and_kernel_denials(sandbox_case):
    value=sandbox_case()
    assert value=={'key':'denied','config':'denied','source':'denied','imds':'denied','control':'denied','fork':'denied','metadata':'denied','fence':'denied','uid':os.geteuid(),'no_new_privs':1}


def test_excess_private_read_permission_breaks_the_denial_positive(sandbox_case):
    value=sandbox_case('key-read')
    assert value['key']=='allowed'
    assert not all(value[k]=='denied' for k in ('key','config','source','imds','control'))


from .launch_fixture import stage,v,g,rb,configuration,c,l,w
from workload_factory_binding.evidence import digest,canonical
from workload_factory_binding_runtime.hosted.readback import ReadBudget


def test_public_v2_plan_readiness_is_read_only_with_actual_correlation(stage):
    use=stage.use();value=stage.plan.read(stage.v.context,stage.v.pre_token,decision=use)
    assert value.state=='plan-ready'
    assert stage.agent.children=={}
    assert not stage.rb.stage_lease_path.exists()
    assert ReadBudget(stage.seen[0]).github_requests<=13
    assert not hasattr(value,'config_digest')


def test_protected_grant_and_durable_ack_precede_one_actual_sandboxed_start(stage):
    value=stage.protected.read(stage.v.context,stage.v.token,decision=stage.use())
    assert value.state=='running'
    assert stage.events==['cleanup-durable']
    assert len(stage.agent.children)==1
    row=stage.agent.store.read(stage.scope['launch_ref'],decision=stage.use())
    assert row['state']=='running'
    assert row['generation']['pid']==row['generation']['session_id']
    assert row['generation']['policy_digest']==stage.scope['hosting_selection_digest']
    assert stage.v.h.calls==0
    assert not hasattr(value,'config_digest')


def test_admission_response_retains_total_rpc_bound_after_five_second_connect(stage,monkeypatch):
    import time
    original=stage.controller.handle
    def delayed(*args,**kwargs):time.sleep(5.25);return original(*args,**kwargs)
    monkeypatch.setattr(stage.controller,'handle',delayed)
    result=stage.plan.read(stage.v.context,stage.v.pre_token,decision=stage.use())
    assert result.state=='plan-ready'
    assert stage.agent.children=={}


@pytest.mark.parametrize('change',['missing-grant','revoked','wrong-action','wrong-scope','expired','extra-field'])
def test_valid_protected_identity_does_not_replace_separate_current_grant(stage,change):
    grant=stage.rb.stage_grant
    if change=='missing-grant':stage.rb.stage_grant=None
    elif change=='revoked':grant['state']='revoked'
    elif change=='wrong-action':grant['action']='sign'
    elif change=='wrong-scope':grant['scope']['run_id']='999'
    elif change=='expired':grant['expires_at']=stage.v.h.now
    else:grant['self_approved']=True
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert stage.agent.children=={}
    assert not stage.rb.stage_lease_path.exists()


@pytest.mark.parametrize('change',['self-review','app-review','wrong-run','missing-branch-type','hold-revoked','source-moved','context-revoked'])
def test_independent_provider_or_context_changes_refuse_before_staging(stage,change):
    original=stage.v.raw
    if change=='self-review':stage.g.reviews[0]['user']['id']=int(stage.policy.initiating_user_id)
    elif change=='app-review':stage.g.reviews[0]['user']['type']='Bot'
    elif change=='wrong-run':stage.g.run['run_attempt']=2
    elif change=='missing-branch-type':del stage.rb.policies['branch_policies'][0]['type']
    elif change=='hold-revoked':stage.rb.hold['state']='revoked'
    elif change=='source-moved':stage.rb.main_sha='f'*40
    else:
        facts=json.loads(stage.rb.plan_fact_path.read_bytes());facts['state']='revoked';stage.rb.plan_fact_path.write_bytes(canonical(facts))
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert stage.agent.children=={}
    assert stage.v.raw==original


@pytest.mark.parametrize('token',['preflight','tampered'])
def test_wrong_intrinsic_phase_or_signature_never_reaches_launch(stage,token):
    value=stage.v.pre_token if token=='preflight' else stage.v.token[:-10]+'A'*10
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,value,decision=read_decision)
    assert stage.agent.children=={}
    assert not stage.agent.store.known(stage.scope['launch_ref'],stage.scope,decision=stage.use())


@pytest.mark.parametrize('change',['no-ack','wrong-unit','expired','late-grant-revocation'])
def test_cleanup_acknowledgement_is_independently_read_before_start(stage,change):
    original=stage.controller.register_cleanup
    def registration(scope,unit,*,deadline):
        if change=='no-ack':return True
        original(scope,unit,deadline=deadline)
        data=json.loads(stage.rb.stage_lease_path.read_bytes())
        if change=='wrong-unit':data['unit_digest']='sha256:'+'f'*64
        elif change=='expired':data['expires_at']=stage.v.h.now
        else:stage.rb.stage_grant['state']='revoked'
        stage.rb.stage_lease_path.write_bytes(canonical(data))
    stage.controller.register_cleanup=registration
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert stage.agent.children=={}
    assert stage.controller.store.known(stage.scope['launch_ref'],stage.scope,decision=stage.use())
    assert stage.agent.store.known(stage.scope['launch_ref'],stage.scope,decision=stage.use())


@pytest.mark.parametrize('change',['worker-source','configuration','captured-source-selection'])
def test_changed_launch_artifact_or_projection_never_starts_a_worker(stage,change):
    original=stage.controller.register_cleanup
    def registration(scope,unit,*,deadline):
        original(scope,unit,deadline=deadline)
        if change=='captured-source-selection':stage.spec.m['uid']+=1
        else:
            path=stage.spec.paths['worker' if change=='worker-source' else 'configuration'];path.chmod(0o644);path.write_bytes(path.read_bytes()+b' ')
    stage.controller.register_cleanup=registration
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert stage.agent.children=={}
    assert stage.agent.store.read(stage.scope['launch_ref'],decision=stage.use())['state']=='start-consumed'


@pytest.mark.parametrize('operation',['register','start'])
def test_lost_mutation_response_is_consumed_and_recovers_status_without_resubmission(stage,operation,monkeypatch):
    from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
    original=PrivateHttps.exchange;calls=[];dropped=False
    def lost(transport,method,url,**kwargs):
        nonlocal dropped
        result=original(transport,method,url,**kwargs)
        if url==stage.agent_origin+'/stage/'+operation:
            calls.append(operation)
            if not dropped:dropped=True;raise OSError('lost-fixture-response')
        return result
    monkeypatch.setattr(PrivateHttps,'exchange',lost)
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert calls==[operation]
    later=stage.protected.read(stage.v.context,stage.v.token,decision=stage.use())
    assert later.state==('registered' if operation=='register' else 'running')
    assert calls==[operation]
    assert len(stage.agent.children)==(0 if operation=='register' else 1)


def test_six_status_reads_and_original_expiry_survive_controller_reconstruction(stage):
    from workload_factory_binding_runtime.hosted.stage_controller import StageController
    first=stage.protected.read(stage.v.context,stage.v.token,decision=stage.use());assert first.state=='running'
    original=stage.controller
    for _ in range(6):
        stage.public_server.service=StageController(context=original.context,preflight=original.preflight,protected=original.protected,
            correlator=original.correlator,authority=original.authority,host=original.host,store=original.store,register_cleanup=original.register_cleanup)
        assert stage.protected.read(stage.v.context,stage.v.token,decision=stage.use()).state=='running'
    count=len(stage.rb.calls)
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert len(stage.rb.calls)==count
    assert len(stage.agent.children)==1


def test_lease_expiry_cannot_be_renewed_under_existing_launch_reference(stage):
    stage.protected.read(stage.v.context,stage.v.token,decision=stage.use())
    lease=json.loads(stage.rb.stage_lease_path.read_bytes());lease['expires_at']+=1;stage.rb.stage_lease_path.write_bytes(canonical(lease))
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert len(stage.agent.children)==1


def worker_channel(stage):
    from workload_factory_binding_runtime.hosted.stage_client import Channel
    return Channel(origin=stage.agent_origin,principal='principal:host-agent',transport=stage.host_transport('worker'),private=True)


def test_authenticated_worker_control_denial_has_allowed_controller_positive(stage):
    from workload_factory_binding_runtime.hosted.stage_client import probe_worker_denial
    assert stage.host.register(stage.scope['launch_ref'],decision=stage.use())['state']=='registered'
    value=probe_worker_denial(channel=worker_channel(stage),scope=stage.scope,decision=stage.use())
    assert value['outcome']=='denied'
    assert stage.agent.children=={}


@pytest.mark.parametrize('change',['excess-permission','outage'])
def test_worker_privilege_probe_cannot_count_excess_permission_or_outage_as_denial(stage,change):
    from workload_factory_binding_runtime.hosted.stage_client import probe_worker_denial
    stage.host.register(stage.scope['launch_ref'],decision=stage.use())
    if change=='excess-permission':stage.agent_server.permissions['sha256:'+stage.worker_cert[2]]=frozenset({'register','start','status'})
    else:stage.agent_server.shutdown();stage.agent_server.server_close()
    probe_worker_denial_channel = worker_channel(stage)
    probe_worker_denial_decision = stage.use()
    with pytest.raises(BindingError):probe_worker_denial(channel=probe_worker_denial_channel,scope=stage.scope,decision=probe_worker_denial_decision)
    assert stage.agent.children=={}


def test_changed_phase_endpoint_is_refused_before_public_request(stage):
    stage.plan.path='/v2/protected'
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.plan.read(stage.v.context,stage.v.token,decision=read_decision)
    assert stage.agent.children=={}


@pytest.mark.parametrize('phase',['preflight','protected-admission'])
def test_explicit_hosted_workflow_binding_uses_intrinsic_phase_and_bootstrap_purpose(stage,phase):
    from workload_factory_binding_runtime.workflow import HostedWorkflowBindings,admit_hosted
    from workload_factory_binding_runtime.github_bootstrap.client import TokenClient
    from workload_factory_binding_runtime.github_bootstrap.identity import BOOTSTRAP_AUDIENCE
    from workload_factory_binding_runtime.github_bootstrap.https import Response
    calls=[];token=stage.v.pre_token if phase=='preflight' else stage.v.token
    class Transport:
        def exchange(self,method,url,**kwargs):calls.append(url);return Response(200,canonical({'value':token}))
    endpoint='https://job.example.invalid/oidc?case=fixture'
    bindings=HostedWorkflowBindings(stage.plan,stage.protected,TokenClient(endpoint=endpoint,audience=BOOTSTRAP_AUDIENCE,transport=Transport()),
        lambda:stage.v.h.now,lambda:stage.v.c.r.clock.mono)
    value=admit_hosted(stage.v.context,bindings=bindings,phase=phase,
        environment={'ACTIONS_ID_TOKEN_REQUEST_URL':endpoint,'ACTIONS_ID_TOKEN_REQUEST_TOKEN':'fixture-job-credential'})
    assert value.state==('plan-ready' if phase=='preflight' else 'running')
    assert len(calls)==1
    assert len(stage.agent.children)==(0 if phase=='preflight' else 1)
    assert not hasattr(value,'config_digest')


@pytest.mark.parametrize('change',['audience','endpoint','phase-client'])
def test_unapproved_hosted_workflow_inputs_refuse_before_oidc_or_launch(stage,change):
    from workload_factory_binding_runtime.workflow import HostedWorkflowBindings,admit_hosted
    from workload_factory_binding_runtime.github_bootstrap.client import TokenClient
    from workload_factory_binding_runtime.github_bootstrap.identity import BOOTSTRAP_AUDIENCE
    calls=[]
    class Transport:
        def exchange(self,*args,**kwargs):calls.append(True);raise AssertionError('must not acquire token')
    endpoint='https://job.example.invalid/oidc'
    token_client=TokenClient(endpoint=endpoint,audience='proof:wrong' if change=='audience' else BOOTSTRAP_AUDIENCE,transport=Transport())
    bindings=HostedWorkflowBindings(stage.protected if change=='phase-client' else stage.plan,stage.protected,token_client,
        lambda:stage.v.h.now,lambda:stage.v.c.r.clock.mono)
    with pytest.raises(BindingError):admit_hosted(stage.v.context,bindings=bindings,phase='preflight',
        environment={'ACTIONS_ID_TOKEN_REQUEST_URL':endpoint+'/changed' if change=='endpoint' else endpoint,'ACTIONS_ID_TOKEN_REQUEST_TOKEN':'fixture-job'})
    assert calls==[]
    assert stage.agent.children=={}


@pytest.mark.parametrize('change',['unit-ref','invocation','pid','start','cgroup','policy','coherent-invocation','coherent-pid'])
def test_current_host_generation_cannot_be_substituted_after_launch(stage,change,monkeypatch):
    from workload_factory_binding_runtime.hosted.private_http import Response
    from workload_factory_binding_runtime.hosted.stage_client import HostClient
    stage.protected.read(stage.v.context,stage.v.token,decision=stage.use())
    original=stage.host.channel.transport.exchange
    def substituted(*args,**kwargs):
        reply=original(*args,**kwargs);value=json.loads(reply.body)
        if change=='unit-ref':value['facts']['unit']['unit_ref']='unit:substituted'
        elif change=='invocation':value['facts']['unit']['invocation_ref']='invocation:substituted'
        elif change=='coherent-invocation':
            value['facts']['unit']['invocation_ref']='invocation:substituted'
            value['facts']['generation']['unit_digest']=digest(value['facts']['unit'])
        elif change=='coherent-pid':
            value['facts']['generation']['pid']+=1;value['facts']['generation']['session_id']+=1
        elif change=='pid':value['facts']['generation']['pid']+=1
        elif change=='start':value['facts']['generation']['start_time']=True
        elif change=='cgroup':value['facts']['generation']['cgroup_digest']='invalid'
        else:value['facts']['generation']['policy_digest']='sha256:'+'f'*64
        return Response(200,canonical(value))
    monkeypatch.setattr(stage.host.channel.transport,'exchange',substituted)
    status_decision = stage.use()
    with pytest.raises(BindingError):stage.host.status(stage.scope['launch_ref'],decision=status_decision)
    assert len(stage.agent.children)==1


def test_concurrent_private_starts_consume_one_attempt_and_launch_one_generation(stage):
    ref=stage.scope['launch_ref'];unit=stage.host.register(ref,decision=stage.use())['unit']
    stage.controller.register_cleanup(stage.scope,unit,deadline=stage.use().deadline)
    def start(_):
        try:return stage.host.start(ref,digest(unit),decision=stage.use(),before_send=lambda:None)['state']
        except BindingError:return 'refused'
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(start,range(4)))
    assert results.count('running')==1
    assert results.count('refused')==3
    assert len(stage.agent.children)==1
    assert stage.agent.store.read(ref,decision=stage.use())['state']=='running'


def test_manager_crash_before_pid_persistence_kills_and_reaps_worker_without_retry(stage):
    from dataclasses import asdict
    import select
    def client(source):
        t=source.transport
        return {'origin':source.origin,'principal_ref':source.principal,'scope':source.scope.record(),
            'transport':{'ca_file':str(t.ca),'certificate':str(t.cert),'private_key':str(t.key),
                'observation_origin':source.origin,'server_certificate_digest':t.server_certificate_digest}}
    spec=stage.spec;store=stage.agent.store;receipt=stage.tmp/'crashed-generation.json'
    value={'now':stage.v.h.now,'plan':stage.v.plan,'context':asdict(stage.v.context),'policy':asdict(stage.policy),
        'roots':{k:str(v) for k,v in spec.roots.items()},'runtime':[str(x) for x in spec.runtime],
        'private':[str(x) for x in spec.private],'gid':spec.gid,'directory':str(store.directory),'identity':store.identity,
        'grant':client(stage.authority.grant),'lease':client(stage.authority.lease),'grant_ref':stage.authority.ref,'receipt':str(receipt)}
    path=stage.tmp/'crash-refs.json';path.write_bytes(canonical(value));path.chmod(0o600)
    helper=Path(__file__).with_name('stage_crash_role.py')
    p=subprocess.Popen([sys.executable,'-I','-B',str(helper),'supervisor',str(path)],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True)
    try:
        assert select.select([p.stdout],[],[],10)[0]
        unit=json.loads(p.stdout.readline())
        stage.controller.register_cleanup(stage.scope,unit,deadline=stage.use().deadline)
        out,error=p.communicate('start\n',timeout=22)
        assert p.returncode==0,error
        observed=json.loads(out)
        assert observed['manager_exit']==73
        assert observed['worker_reaped']
        assert observed['worker_signal']==9
        assert not (Path('/proc')/str(observed['worker_pid'])).exists()
    finally:
        if p.poll() is None:p.kill()
        p.communicate(timeout=3)
    row=store.read(stage.scope['launch_ref'],decision=stage.use())
    assert row['state']=='start-consumed'
    assert row['generation'] is None
    assert stage.agent.status(stage.scope['launch_ref'],decision=stage.use())['state']=='indeterminate'
    start_argument_2 = digest(unit)
    start_decision = stage.use()
    with pytest.raises(BindingError):stage.agent.start(stage.scope['launch_ref'],start_argument_2,decision=start_decision)
    assert stage.agent.children=={}


@pytest.mark.parametrize('clock',['wall','monotonic'])
def test_original_decision_expiry_after_cleanup_registration_prevents_start(stage,clock):
    original=stage.controller.register_cleanup
    def registration(*args,**kwargs):
        original(*args,**kwargs)
        if clock=='wall':stage.v.h.now+=11
        else:stage.v.c.r.clock.mono+=11
    stage.controller.register_cleanup=registration
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert stage.agent.children=={}
    assert stage.rb.stage_lease_path.exists()


def test_staging_status_window_retains_earlier_durable_expiry_without_renewal(stage):
    stage.protected.read(stage.v.context,stage.v.token,decision=stage.use())
    store=stage.controller.store;ref=stage.scope['launch_ref']
    row=store.read(ref,decision=stage.use());assert row['deadline']==stage.v.h.now+35
    late=Decision(clock=lambda:row['deadline'],monotonic=lambda:0.)
    with pytest.raises(BindingError):store.status_read(ref,decision=late)
    assert len(stage.agent.children)==1


@pytest.mark.parametrize('change',['wall','monotonic','grant','lease'])
def test_post_spawn_checkpoint_refuses_expiry_or_revocation_before_worker_exec(stage,change,monkeypatch):
    original=subprocess.Popen
    def spawned(*args,**kwargs):
        child=original(*args,**kwargs)
        command=child.args
        if isinstance(command,(list,tuple)) and any(str(x).endswith('/hosted/_launch_exec.py') for x in command):
            if change=='wall':stage.v.h.now+=11
            elif change=='monotonic':stage.v.c.r.clock.mono+=11
            elif change=='grant':stage.rb.stage_grant['state']='revoked'
            else:
                lease=json.loads(stage.rb.stage_lease_path.read_bytes());lease['state']='revoked'
                stage.rb.stage_lease_path.write_bytes(canonical(lease))
        return child
    monkeypatch.setattr(subprocess,'Popen',spawned)
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert len(stage.agent.children)==1
    child=stage.agent.children[stage.scope['launch_ref']]
    assert b'_launch_exec.py' in (Path('/proc')/str(child.pid)/'cmdline').read_bytes()
    assert not select_ready(child.stdout)
    row=stage.agent.store.read(stage.scope['launch_ref'],decision=stage.use())
    assert row['state']=='start-consumed'
    assert row['generation'] is None


def select_ready(stream):
    import select
    return bool(select.select([stream],[],[],0)[0])


@pytest.mark.parametrize('change',['hold','main','context','protection','control','review','run'])
def test_complete_authority_is_refreshed_after_durable_registration(stage,change):
    original=stage.controller.register_cleanup
    def registered(*args,**kwargs):
        original(*args,**kwargs)
        if change=='hold':stage.rb.hold['state']='revoked'
        elif change=='main':stage.rb.main_sha='f'*40
        elif change=='context':
            facts=json.loads(stage.rb.plan_fact_path.read_bytes());facts['state']='revoked'
            stage.rb.plan_fact_path.write_bytes(canonical(facts))
        elif change=='protection':stage.rb.policies['branch_policies'][0]['type']='tag'
        elif change=='control':stage.rb.rule['enforcement']='disabled'
        elif change=='review':stage.g.reviews[0]['state']='rejected'
        else:stage.g.run['status']='completed'
    stage.controller.register_cleanup=registered
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert stage.events==['cleanup-durable']
    assert stage.agent.children=={}
    assert stage.agent.store.read(stage.scope['launch_ref'],decision=stage.use())['state']=='registered'


def test_second_observation_expiry_reaches_host_and_prevents_late_execution(stage,monkeypatch):
    original=stage.controller.register_cleanup;start=stage.agent.start;popen=subprocess.Popen;observed=[]
    expiry=stage.v.h.now+5
    def registered(*args,**kwargs):
        original(*args,**kwargs);stage.rb.hold['expires_at']=expiry
    def host_start(*args,**kwargs):
        observed.append(kwargs['decision'].deadline);return start(*args,**kwargs)
    def delayed(*args,**kwargs):
        child=popen(*args,**kwargs)
        if isinstance(child.args,(list,tuple)) and any(str(x).endswith('/hosted/_launch_exec.py') for x in child.args):stage.v.h.now=expiry+1
        return child
    stage.controller.register_cleanup=registered;stage.agent.start=host_start
    monkeypatch.setattr(subprocess,'Popen',delayed)
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.read(stage.v.context,stage.v.token,decision=read_decision)
    assert observed
    assert observed[0]<=expiry
    assert stage.agent.store.read(stage.scope['launch_ref'],decision=stage.use())['generation'] is None
    for child in stage.agent.children.values():
        assert b'_launch_exec.py' in (Path('/proc')/str(child.pid)/'cmdline').read_bytes()


@pytest.mark.parametrize('field,value',[('run_id','999'),('run_attempt','2'),('source_commit','f'*40),('accepted_commit','f'*40)])
def test_admission_reply_binds_actual_run_and_accepted_source(stage,field,value,monkeypatch):
    from workload_factory_binding_runtime.hosted.private_http import Response
    original=stage.plan.channel.transport.exchange
    def changed(*args,**kwargs):
        response=original(*args,**kwargs);data=json.loads(response.body);data['facts'][field]=value
        return Response(response.status,canonical(data))
    monkeypatch.setattr(stage.plan.channel.transport,'exchange',changed)
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.plan.read(stage.v.context,stage.v.pre_token,decision=read_decision)
    assert stage.agent.children=={}


@pytest.mark.parametrize('field,value',[('run_id','999'),('run_attempt','2')])
def test_readiness_for_server_run_cannot_be_attributed_to_another_context(stage,field,value):
    from dataclasses import replace
    read_argument_1 = replace(stage.v.context,**{field:value})
    read_decision = stage.use()
    with pytest.raises(BindingError):stage.plan.read(read_argument_1,stage.v.pre_token,decision=read_decision)
    assert stage.agent.children=={}


@pytest.mark.parametrize('field',['staging','finalization','read_budget'])
def test_public_input_cannot_select_a_broader_allocation(stage,field):
    inputs={k:getattr(stage.v.context,k) for k in ('accepted_commit','selection_digest','preauthorization_ref')};inputs[field]=True
    before=len(stage.rb.calls)
    call_decision = stage.use()
    with pytest.raises(BindingError):stage.protected.channel.call('/v2/protected',inputs,decision=call_decision,token=stage.v.token)
    assert stage.agent.children=={}
    assert len(stage.rb.calls)==before


@pytest.mark.parametrize('stage',['partial-ready'],indirect=True)
def test_actual_partial_ready_worker_cannot_block_host_start_or_shutdown(stage):
    import time
    ref=stage.scope['launch_ref'];unit=stage.host.register(ref,decision=stage.use())['unit']
    stage.controller.register_cleanup(stage.scope,unit,deadline=stage.use().deadline)
    before=time.monotonic()
    start_argument_2 = digest(unit)
    start_decision = stage.use()
    with pytest.raises(BindingError):stage.agent.start(ref,start_argument_2,decision=start_decision)
    assert time.monotonic()-before<5
    row=stage.agent.store.read(ref,decision=stage.use())
    assert row['state']=='start-consumed'
    assert row['generation'] is None
    assert len(stage.agent.children)==1
    stage.agent.close()
    assert all(p.poll() is not None for p in stage.agent.children.values())


def test_system_worker_runtime_is_independent_of_writable_test_driver(tmp_path,monkeypatch):
    driver=tmp_path/'tool-cache-python';driver.write_text('fixture only');driver.chmod(0o777)
    monkeypatch.setattr(sys,'executable',str(driver));monkeypatch.setattr(sys,'base_prefix',str(tmp_path))
    selected,roots=system_runtime()
    assert selected!=driver
    assert all(not p.is_relative_to(tmp_path) and not p.stat().st_mode&0o022 for p in roots)


@pytest.mark.parametrize('group,limit',[('protection',6),('source',8),('control',4),('private',16),('arm',24),('key',3)])
def test_protected_staging_group_caps_cannot_be_reset(group,limit):
    from workload_factory_binding_runtime.hosted.readback import start_staging
    decision=use();start_staging(decision)
    for _ in range(limit):ReadBudget(decision).consume(group)
    consume_target = ReadBudget(decision)
    with pytest.raises(BindingError):consume_target.consume(group)
    assert ReadBudget(decision).count(group)==limit
    with pytest.raises(BindingError):start_staging(decision)


def test_two_complete_observations_share_one_26_read_envelope():
    from workload_factory_binding_runtime.hosted.readback import start_staging
    decision=use();start_staging(decision);budget=ReadBudget(decision)
    for _ in range(2):
        budget.begin_staging_observation();budget.begin_protection()
        for group,count in [('source',4),('control',2),('protection',3)]:
            for _ in range(count):ReadBudget(decision).consume(group)
        for _ in range(4):budget.consume_correlation()
    assert budget.github_requests==26
    with pytest.raises(BindingError):budget.begin_staging_observation()
    with pytest.raises(BindingError):budget.begin_protection()
    with pytest.raises(BindingError):budget.consume_correlation()
    assert budget.github_requests==26


def test_staging_cannot_join_upgrade_or_regress_an_existing_ledger():
    from workload_factory_binding_runtime.hosted.readback import start_staging,start_finalization
    decision=use();start_staging(decision);budget=ReadBudget(decision);budget.consume_correlation()
    join_argument_1 = use()
    with pytest.raises(BindingError):budget.join(join_argument_1)
    with pytest.raises(BindingError):start_finalization(decision)
    decision.api_requests=0
    with pytest.raises(BindingError):budget.check()
    ordinary=use();ReadBudget(ordinary)
    with pytest.raises(BindingError):start_staging(ordinary)


@pytest.mark.parametrize('clock',['wall','monotonic'])
def test_staging_cannot_extend_either_original_clock(clock):
    from workload_factory_binding_runtime.hosted.readback import start_staging
    now={'wall':1000,'monotonic':0.};decision=Decision(clock=lambda:now['wall'],monotonic=lambda:now['monotonic'])
    start_staging(decision)
    staging_budget = ReadBudget(decision)
    staging_budget.begin_staging_observation()
    now[clock]+=10
    with pytest.raises(BindingError):staging_budget.begin_staging_observation()
    with pytest.raises(BindingError):ReadBudget(decision)


def test_each_staging_reader_retains_four_requests_and_aggregate_retains_eight():
    from workload_factory_binding_runtime.hosted.readback import start_staging
    from workload_factory_binding_runtime.github_bootstrap.provider import ProviderReader
    from workload_factory_binding_runtime.github_bootstrap.https import Response
    calls=[];credentials=[]
    class Transport:
        def exchange(self,*args,**kwargs):kwargs['before_send']();calls.append(True);return Response(200,b'{}')
    def credential(**kwargs):credentials.append(True);return 'fixture-reader'
    decision=use();start_staging(decision);provider=ProviderReader(credential=credential,transport=Transport())
    for _ in range(2):
        reader=provider.decision('opensoft/openXwallet',decision)
        for _ in range(4):reader.run('789')
        before=len(credentials)
        with pytest.raises(BindingError):reader.run('789')
        assert len(credentials)==before
    assert len(calls)==len(credentials)==8
    run_target = provider.decision('opensoft/openXwallet',decision)
    with pytest.raises(BindingError):run_target.run('789')
    assert len(calls)==len(credentials)==8


@pytest.fixture
def process_control_probe(tmp_path):
    from workload_factory_binding_runtime.hosted.host_agent import loader_for
    import select
    executable,runtime=system_runtime();exe=str(executable);loader=str(loader_for(executable))
    victim_file=tmp_path/'control_victim.py';probe=tmp_path/'control_probe.py';config=tmp_path/'control.json'
    victim_file.write_text("""import json,resource,signal,sys
received=False
def notice(*_):
 global received
 received=True
signal.signal(signal.SIGUSR1,notice)
before=resource.getrlimit(resource.RLIMIT_NOFILE)
print('ready',flush=True)
sys.stdin.readline()
print(json.dumps({'signal_received':received,'before':before,'after':resource.getrlimit(resource.RLIMIT_NOFILE)}),flush=True)
""")
    probe.write_text("""import ctypes,fcntl,json,os,resource,struct,sys
v=json.load(open(sys.argv[1]));libc=ctypes.CDLL(None,use_errno=True)
self_read=resource.prlimit(0,resource.RLIMIT_NOFILE)
if v['operation']=='owner':
 try:fcntl.fcntl(0,fcntl.F_SETOWN,v['pid']);result=0;error=0
 except PermissionError:result=-1;error=1
elif v['operation']=='async':
 result=libc.ioctl(0,0x5452,ctypes.byref(ctypes.c_int(1)));error=ctypes.get_errno()
elif v['operation']=='limits':
 try:resource.prlimit(v['pid'],resource.RLIMIT_NOFILE,(32,32));result=0;error=0
 except PermissionError:result=-1;error=1
else:
 info=ctypes.create_string_buffer(128)
 struct.pack_into('iii',info,0,10,0,-1);struct.pack_into('ii',info,16,os.getpid(),os.geteuid())
 if v['operation']=='queue':result=libc.syscall(129,v['pid'],10,ctypes.byref(info))
 else:result=libc.syscall(297,v['pid'],v['pid'],10,ctypes.byref(info))
 error=ctypes.get_errno()
print(json.dumps({'result':result,'errno':error,'self_read':list(self_read),'fd_read_flags':fcntl.fcntl(0,fcntl.F_GETFL)}),flush=True)
""")
    def run(operation,sandbox):
        victim=subprocess.Popen([exe,'-I','-B',str(victim_file)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True)
        try:
            assert select.select([victim.stdout],[],[],3)[0]
            assert victim.stdout.readline()=='ready\n'
            config.write_bytes(canonical({'operation':operation,'pid':victim.pid}))
            if sandbox:
                message={'files':[exe,loader,str(probe),str(config)],'directories':[str(p) for p in runtime],
                    'execute':[exe,loader],'argv':[exe,'-I','-B',str(probe),str(config)],
                    'uid':os.geteuid(),'gid':os.getegid(),'parent_pid':os.getpid()}
                helper=Path(__file__).resolve().parents[2]/'scripts/workload_factory_binding_runtime/hosted/_launch_exec.py'
                response=subprocess.run([exe,'-I','-B',str(helper)],input=canonical(message)+b'\n',capture_output=True,timeout=5)
            else:response=subprocess.run([exe,'-I','-B',str(probe),str(config)],input=b'',capture_output=True,timeout=5)
            assert response.returncode==0,response.stderr.decode(errors='replace')
            stdout,error=victim.communicate('status\n',timeout=5);assert victim.returncode==0,error
            return json.loads(response.stdout),json.loads(stdout)
        finally:
            if victim.poll() is None:victim.kill()
            victim.communicate(timeout=3)
    return run


@pytest.mark.parametrize('operation',['queue','thread-queue'])
def test_actual_queued_signal_denial_has_allowed_same_uid_delivery_control(process_control_probe,operation):
    result,victim=process_control_probe(operation,True)
    assert result['result']==-1
    assert result['errno']==1
    assert not victim['signal_received']
    assert result['self_read'][0]>0
    allowed,target=process_control_probe(operation,False)
    assert allowed['result']==0
    assert target['signal_received']


def test_actual_parent_limit_write_is_denied_while_self_read_and_unconfined_control_succeed(process_control_probe):
    result,victim=process_control_probe('limits',True)
    assert result['result']==-1
    assert result['errno']==1
    assert result['self_read'][0]>32
    assert victim['after']==victim['before']
    allowed,target=process_control_probe('limits',False)
    assert allowed['result']==0
    assert target['after']==[32,32]


@pytest.mark.parametrize('operation',['owner','async'])
def test_inherited_pipe_signal_controls_refuse_while_fd_queries_remain_allowed(process_control_probe,operation):
    result,victim=process_control_probe(operation,True)
    assert result['result']==-1
    assert result['errno']==1
    assert result['fd_read_flags']>=0
    assert not victim['signal_received']
    allowed,target=process_control_probe(operation,False)
    assert allowed['result']==0
    assert allowed['fd_read_flags']>=0


@pytest.mark.parametrize('option',['-c','--help'])
def test_private_launch_packet_cannot_substitute_python_options_for_selected_worker(sandbox_case,option):
    sandbox_case(option)


@pytest.mark.parametrize("missing", ["unit", "generation", "lease"])
def test_incomplete_running_record_refuses_before_worker_observation(stage, monkeypatch, missing):
    import sqlite3
    assert stage.protected.read(stage.v.context, stage.v.token, decision=stage.use()).state == "running"
    ref = stage.scope["launch_ref"]
    children = {name: child.pid for name, child in stage.agent.children.items()}
    with sqlite3.connect(stage.agent.store.directory / "staging.sqlite") as database:
        # The column is chosen solely from the fixed parameter set above.
        database.execute("UPDATE stages SET " + missing + "=NULL WHERE ref=?", (ref,))
    def forbidden(*args, **kwargs):
        raise AssertionError("incomplete running state reached worker observation")
    monkeypatch.setattr(stage.spec, "observe", forbidden)
    decision = stage.use()
    with pytest.raises(BindingError, match="hosted-stage-refused"):
        stage.agent.status(ref, decision=decision)
    row = stage.agent.store.read(ref, decision=stage.use())
    assert row["state"] == "running"
    assert row[missing] is None
    assert {name: child.pid for name, child in stage.agent.children.items()} == children
