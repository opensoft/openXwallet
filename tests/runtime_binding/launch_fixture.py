"""Isolated actual TLS services, independent grant/lease state and inert host unit."""
from copy import deepcopy
from contextlib import ExitStack
from dataclasses import replace,asdict
import json,os,sys
from pathlib import Path
from types import SimpleNamespace
from threading import Thread
import pytest
from workload_factory_binding.evidence import canonical,digest,byte_digest
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.plan import validate_plan,template_digest
from workload_factory_binding_runtime.hosted.stage_store import StageStore
from workload_factory_binding_runtime.hosted.staging import StagePolicy,StageAuthority,StageCorrelator,scope_of
from workload_factory_binding_runtime.hosted.host_agent import WorkerSpec,HostAgent,hosting_selection,loader_for
from workload_factory_binding_runtime.hosted.stage_controller import StageController
from workload_factory_binding_runtime.hosted.stage_http import StageServer
from workload_factory_binding_runtime.hosted.stage_client import Channel,HostClient,AdmissionClient
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
from workload_factory_binding_runtime.github_bootstrap.provider import ProviderReader
from workload_factory_binding_runtime.github_bootstrap.https import Response
from .test_hosted_finalization import v
from .test_github_bootstrap_correlation import g,configuration,c,l,w
from .test_hosted_readback_flow import plan_readers
from .readback_fixture import rb
from .hosted_fixture import child_generations
from .worker_runtime import system_runtime
from factory_binding.test_owner_integration import make_pki

ROOT=Path(__file__).resolve().parents[2]


def _register_stage_teardown(stack):
    failures = []

    def report_failures():
        if len(failures) == 1:
            raise failures[0]
        if failures:
            raise BaseExceptionGroup("stage teardown failed", failures)

    def register(callback):
        def close():
            try:
                callback()
            except BaseException as error:
                failures.append(error)

        stack.callback(close)

    stack.callback(report_failures)
    return register


@pytest.fixture
def stage(v,g,rb,tmp_path,request):
    with ExitStack() as cleanup:
        register_teardown = _register_stage_teardown(cleanup)
        result=SimpleNamespace(v=v,g=g,rb=rb,tmp=tmp_path,events=[])
        executable,runtime=system_runtime()
        roots=dict(v.roots);roots['root:python']=executable.parent;roots['root:runtime']=runtime[0].parent
        v.executable=executable
        loader=loader_for(executable)
        if not any(loader.is_relative_to(root) for root in roots.values()):roots['root:loader']=loader.parent
        plan=deepcopy(v.plan);m=plan['measurement_plan']
        m['executable']={'root_ref':'root:python','path':executable.name};m['executable_digest']=byte_digest(executable.read_bytes())
        mode=getattr(request,'param',None)
        assert mode in (None,'partial-ready')
        if mode=='partial-ready':
            v.paths['worker'].write_text("import sys,time\nsys.stdout.write('r');sys.stdout.flush();time.sleep(30)\n")
            m['artifacts']['worker']['digest']=byte_digest(v.paths['worker'].read_bytes())
            plan['configuration_template']['sources']['worker']['digest']=m['artifacts']['worker']['digest']
        for role,name in [('host_agent','host_agent.py'),('launch_helper','_launch_exec.py'),('sandbox','worker_sandbox.py')]:
            path=ROOT/'scripts/workload_factory_binding_runtime/hosted'/name
            m['artifacts'][role]={'root_ref':'root:code','path':path.relative_to(ROOT).as_posix(),'digest':byte_digest(path.read_bytes())}
        plan['hosting_selection_digest']=digest(hosting_selection(m,roots,runtime,os.getegid()))
        plan['staging_policy']['template_digest']=template_digest(plan)
        v.plan=plan;v.raw=canonical(plan);v.selected=validate_plan(v.raw,approved_digest=digest(plan),now=v.h.now)
        v.context=replace(v.context,selection_digest=v.selected.digest)
        v.facts=replace(v.facts,plan_digest=v.selected.digest,hosting_selection_digest=plan['hosting_selection_digest'])
        v.preflight=replace(v.preflight,approved_plan_digest=v.selected.digest)
        v.protected=replace(v.protected,approved_plan_digest=v.selected.digest)
        readers,seen=plan_readers(v,rb);result.seen=seen;rb.g=g
        rb.plan_fact_path=tmp_path/"current-operator-context.json";rb.plan_fact_path.write_bytes(canonical(rb.planfacts));rb.plan_fact_path.chmod(0o600)
        preflight=replace(v.preflight,**readers);protected=replace(v.protected,**readers)
        policy=StagePolicy(g.approval.workflow_id,g.approval.broker_actor_id,g.approval.initiating_user_id,
            tuple(g.approval.approved_reviewer_user_ids),'principal:hold-owner')
        result.policy=policy;scope=scope_of(v.selected,v.context,policy);result.scope=deepcopy(scope)
        rb.hold.update(source_sha=v.context.source_commit,not_before=rb.now-1,expires_at=rb.now+60)
        rb.stage_grant={'scope':deepcopy(scope),'action':'launch-inert','state':'active','not_before':rb.now-1,'expires_at':rb.now+40}
        lease_root=tmp_path/'independent-janitor';lease_root.mkdir(mode=0o700);rb.stage_lease_path=lease_root/'registration.json'
        agent_ca,agent_cert,controller_cert,worker_cert=make_pki(tmp_path/'host-agent-pki',ca_common_name='stage host CA')
        public_ca,public_cert,_,_=make_pki(tmp_path/'admission-pki',ca_common_name='admission CA')
        host_dir=tmp_path/'host-state';host_id=StageStore.initialize(host_dir,kind='host')
        control_dir=tmp_path/'controller-state';control_id=StageStore.initialize(control_dir,kind='controller')
        authority=StageAuthority(grant=rb.client(),lease=rb.client(rb.secondary),grant_ref='stage-grant:fixture')
        private_files=[agent_cert[1],controller_cert[1],worker_cert[1],public_cert[1],rb.primary.gate[1],rb.secondary.gate[1],host_dir/'staging.sqlite',control_dir/'staging.sqlite']
        spec=WorkerSpec(plan=v.selected,context=v.context,policy=policy,roots=roots,runtime_roots=runtime,gid=os.getegid(),private_files=private_files)
        agent=HostAgent(worker=spec,store=StageStore(host_dir,identity=host_id,kind='host'),authority=authority)
        result.spec,result.agent,result.authority=spec,agent,authority
        register_teardown(agent.close)
        servers=[]
        def close_servers():
            for server,thread in reversed(servers):server.shutdown();server.server_close();thread.join(timeout=5);assert not thread.is_alive()
        register_teardown(close_servers)
        def serve(service,principal,cert,ca=None,permissions=None):
            server=StageServer(service=service,principal=principal,cert_file=str(cert[0]),key_file=str(cert[1]),
                clock=lambda:v.h.now,monotonic=lambda:v.c.r.clock.mono,ca_file=str(ca) if ca is not None else None,permissions=permissions)
            thread=Thread(target=lambda:server.serve_forever(poll_interval=.02));thread.start();servers.append((server,thread))
            return server,'https://127.0.0.1:'+str(server.server_port)
        agent_server,agent_origin=serve(agent,'principal:host-agent',agent_cert,agent_ca,{'sha256:'+controller_cert[2]:frozenset({'register','start','status'})})
        result.agent_server=agent_server;result.agent_origin=agent_origin
        def host_transport(peer='controller',pin=None):
            cert=controller_cert if peer=='controller' else worker_cert
            return PrivateHttps(ca_file=str(agent_ca),certificate=str(cert[0]),private_key=str(cert[1]),agent_origin=agent_origin,
                server_certificate_digest=pin or 'sha256:'+agent_cert[2])
        result.host_transport=host_transport
        channel=Channel(origin=agent_origin,principal='principal:host-agent',transport=host_transport(),private=True)
        host=HostClient(channel=channel,scope=scope);result.host=host
        class ActualProvider:
            def exchange(self,*args,**kwargs):
                r=rb.routed().exchange(*args,**kwargs);return Response(r.status,r.body)
        provider=ProviderReader(credential=lambda **_:'fixture-reader',transport=ActualProvider())
        correlator=StageCorrelator(github=rb.github(),hold=rb.client(),provider=provider,policy=policy)
        def register_cleanup(scope,unit,*,deadline):
            actual=agent.store.read(scope['launch_ref'],decision=Decision(clock=lambda:v.h.now,monotonic=lambda:v.c.r.clock.mono))
            assert actual['state']=='registered' and canonical(actual['unit'])==canonical(unit)
            result.events.append('cleanup-durable')
            value={'scope_digest':digest(actual['scope']),'unit_digest':digest(actual['unit']),'state':'acknowledged','expires_at':v.h.now+35}
            fd=os.open(rb.stage_lease_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            try:os.write(fd,canonical(value));os.fsync(fd)
            finally:os.close(fd)
            fd=os.open(lease_root,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
        controller=StageController(context=v.context,preflight=preflight,protected=protected,correlator=correlator,
            authority=authority,host=host,store=StageStore(control_dir,identity=control_id,kind='controller'),register_cleanup=register_cleanup)
        result.controller=controller
        public_server,public_origin=serve(controller,'principal:admission-controller',public_cert)
        result.public_server=public_server;result.public_origin=public_origin
        public=Channel(origin=public_origin,principal='principal:admission-controller',private=False,
            transport=PrivateHttps(ca_file=str(public_ca),admission_origin=public_origin,server_certificate_digest='sha256:'+public_cert[2]))
        result.plan=AdmissionClient(channel=public,phase='preflight');result.protected=AdmissionClient(channel=public,phase='protected')
        result.use=lambda:Decision(clock=lambda:v.h.now,monotonic=lambda:v.c.r.clock.mono)
        result.controller_cert,result.worker_cert=controller_cert,worker_cert
        yield result
