"""Explicit selected remote measurement; private provenance, no full admission."""
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
import secrets
import threading
from urllib.parse import urlsplit
from workload_factory_binding.evidence import canonical, digest, require, valid_digest
from ..config import _configuration
from ..github_bootstrap.common import Decision, document
from ..hosted.admission import PlanBindings, current_plan, read_current
from ..hosted.finalization import StagingReadback
from ..hosted.private_http import PrivateHttps, Response
from ..hosted.readback import _read_checkpoint,LIMITS, ReadBudget, start_finalization
from ..launch import worker_configuration
from .local_host import ERROR, PROFILE, RESPONSE, Scope, Opaque, private
from .selection import ref

_SEAL = object()


class SendClock:
    """View of the original clock, checking the fixed interval at GO evaluation.

    PrivateHttps evaluates remaining() after its final material read and before
    communicate sends GO. This view supplies no clock, grant or ledger of its own.
    """
    __slots__ = ('original','milliseconds','send_pending')
    def __init__(self, original, milliseconds):
        self.original,self.milliseconds,self.send_pending = original,milliseconds,False
    def now(self):
        return self.original.now()
    def remaining(self):
        value = self.original.remaining()
        if self.send_pending:
            require(self.milliseconds <= value*1000, ERROR)
            self.send_pending = False
        return value


class Observed(Opaque):
    __slots__ = ('configuration','policy','generation','nonce','principal','decision')
    def __init__(self, seal, configuration, policy, generation, nonce, principal, decision):
        require(seal is _SEAL, ERROR)
        self.configuration,self.policy,self.generation = configuration,policy,generation
        self.nonce,self.principal,self.decision = nonce,principal,decision


class MeasurementClient(Opaque):
    __slots__ = ('scope','principal','transport','origin','credential_origin','approval_origin',
                 'not_before','expires_at','milliseconds','_binding','_nonces','_lock')
    def __init__(self, *, scope, principal, transport, credential_origin, approval_origin,
                 not_before, expires_at, milliseconds=1000):
        private(lambda:self._initialize(scope,principal,transport,credential_origin,approval_origin,
                                        not_before,expires_at,milliseconds))
    def _initialize(self,scope,principal,transport,credential_origin,approval_origin,not_before,expires_at,milliseconds):
        ref(principal)
        require(type(scope) is Scope and principal in scope.observer_refs
                and type(transport) is PrivateHttps and type(milliseconds) is int
                and 1 <= milliseconds <= 10000 and type(not_before) is int
                and type(expires_at) is int and not_before < expires_at, ERROR)
        for value in (credential_origin,approval_origin):
            ref(value)
        self.scope,self.principal,self.transport = scope,principal,transport
        self.origin = transport.observation_origin
        selected = urlsplit(self.origin)
        require(selected.scheme == 'https' and selected.hostname and not selected.path
                and not selected.query and not selected.fragment
                and selected.username is None and selected.password is None
                and valid_digest(transport.server_certificate_digest), ERROR)
        self.credential_origin,self.approval_origin = credential_origin,approval_origin
        self.not_before,self.expires_at,self.milliseconds = not_before,expires_at,milliseconds
        self._nonces,self._lock = set(),threading.Lock()
        self._binding = self.binding()

    def binding(self):
        t = self.transport
        for item in (self.principal,self.credential_origin,self.approval_origin):
            ref(item)
        require(type(self.not_before) is int and type(self.expires_at) is int
                and type(self.milliseconds) is int and 1 <= self.milliseconds <= 10000
                and type(self.origin) is str and type(t.server_certificate_digest) is str, ERROR)
        require(type(t) is PrivateHttps and t.observation_origin == self.origin
                and all(x is None for x in (t.fixture_origin,t.agent_origin,t.admission_origin,t.lifecycle_origin))
                and t.fixture_args == ['--observation-origin',self.origin]
                and all(x is not None for x in (t.ca,t.cert,t.key)), ERROR)
        return (canonical(self.scope.record()),self.principal,self.origin,t.server_certificate_digest,
                t.materials(),self.credential_origin,self.approval_origin,
                self.not_before,self.expires_at,self.milliseconds)

    def current(self,decision):
        require(type(decision) is Decision and self.binding() == self._binding
                and self.not_before <= decision.now() < self.expires_at, ERROR)
        decision.clip(self.expires_at)
        ReadBudget(decision).check()

    def read(self, *, decision):
        return private(lambda:self._read(decision))
    def _read(self,decision):
        self.current(decision)
        ReadBudget(decision).consume('private')
        before = decision.now()
        scope = self.scope.record()
        nonce = secrets.token_hex(32)
        from .local_host import NONCE
        require(type(nonce) is str and NONCE.fullmatch(nonce), ERROR)
        with self._lock:
            require(nonce not in self._nonces, ERROR)
            self._nonces.add(nonce)
        require(self.milliseconds <= decision.remaining()*1000, ERROR)
        deadline = decision.deadline
        request = canonical(dict(profile=PROFILE,operation='measure',request_nonce=nonce,
            **{k:scope[k] for k in ('deployment_ref','plan_digest','case_ref','source_commit','run_id','run_attempt','launch_ref')},
            deadline=deadline,remaining_milliseconds=self.milliseconds))
        require(len(request) <= 4096, ERROR)
        view = SendClock(decision,self.milliseconds)
        def checkpoint():
            self.current(decision)
            require(self.milliseconds <= decision.remaining()*1000, ERROR)
            view.send_pending = True
        result = self.transport.exchange('POST',self.origin+'/readback',
            headers={'Content-Type':'application/json','Accept':'application/json'},
            body=request,decision=view,before_send=checkpoint)
        self.current(decision)
        require(type(result) is Response and result.status == 200, ERROR)
        value = document(result.body,16384)
        require(type(value) is dict and canonical(value) == result.body and set(value) == RESPONSE
                and value['profile'] == PROFILE and value['request_nonce'] == nonce
                and value['principal_ref'] == self.principal
                and value['independent_observer_refs'] == list(self.scope.observer_refs)
                and all(value[k] == v for k,v in scope.items()), ERROR)
        require(type(value['observed_at']) is int and type(value['expires_at']) is int
                and before <= value['observed_at'] <= decision.now() < value['expires_at']
                <= min(deadline,self.expires_at,value['observed_at']+60), ERROR)
        require(type(value['pid']) is int and value['pid'] > 0
                and type(value['start_time']) is int and value['start_time'] > 0, ERROR)
        ref(value['invocation_ref'])
        require(type(value['configuration']) is dict and type(value['policy']) is dict, ERROR)
        configuration,policy = canonical(value['configuration']),canonical(value['policy'])
        require(len(configuration) <= 16384 and len(policy) <= 16384, ERROR)
        decision.clip(value['expires_at'])
        generation = {k:value[k] for k in ('launch_ref','host_ref','incarnation_ref','boot_id','invocation_ref','pid','start_time')}
        return Observed(_SEAL,configuration,policy,canonical(generation),nonce,self.principal,decision)


@dataclass(frozen=True, repr=False)
class WorkerRoots:
    """Approved worker-host paths, never resolved against control-host files."""
    entries: tuple
    def mapping(self):
        require(type(self.entries) is tuple and 0 < len(self.entries) <= 16
                and all(type(p) is tuple and len(p) == 2 for p in self.entries), ERROR)
        roots = {}
        for key,value in self.entries:
            ref(key)
            require(key not in roots and type(value) is str and value.startswith('/')
                    and str(PurePosixPath(value)) == value and not value.startswith('//'), ERROR)
            roots[key] = PurePosixPath(value)
        return roots


def expected_bytes(plan,context,generation,roots,decision):
    require(type(roots) is WorkerRoots, ERROR)
    selected = roots.mapping()
    value = plan.value()
    config,policy,m = (value[k] for k in ('configuration_template','policy_template','measurement_plan'))
    def path(item):
        return str(selected[item['root_ref']]/item['path'])
    config['launch'].update(run_id=context.run_id,run_attempt=context.run_attempt)
    process = dict(pid=generation['pid'],start_time=generation['start_time'],
        argv=[path(m['executable']),'-I','-B',path(m['worker']),path(m['configuration'])],
        cwd=path(m['cwd']),executable_digest=m['executable_digest'])
    projection = worker_configuration(config,policy)
    composition = digest({'artifacts':{k:v['digest'] for k,v in m['artifacts'].items()},
                          'configuration':{'worker_configuration':projection,'process':process}})
    policy['composition_digest'] = config['composition_digest'] = composition
    config['authority']['policy_digest'] = digest(policy)
    _configuration(config)
    from workload_factory_binding.gate import _policy
    _policy(policy,decision.now())
    return canonical(config),canonical(policy)


@dataclass(frozen=True, repr=False)
class RemoteBindings:
    plan: PlanBindings
    independent_plan: PlanBindings
    primary: MeasurementClient
    independent: MeasurementClient
    roots: WorkerRoots
    stage_principal: str
    read_stage: object
    authority_principal: str


class VerifiedRemote(Opaque):
    __slots__ = ('_configuration','_policy','_generation','_provenance','_decision','_binding')
    def __init__(self, seal, configuration, policy, generation, provenance, decision, binding):
        require(seal is _SEAL, ERROR)
        self._configuration,self._policy,self._generation = configuration,policy,generation
        self._provenance,self._decision,self._binding = provenance,decision,binding


class _FinalizationGuard(Opaque):
    """Retain one enclosing authority snapshot through every callback and join."""
    __slots__ = ('binding','expected','ledger','counts','members','count_floor',
                 'member_floor','observation_floor','budget')

    def __init__(self, finalizer, decision):
        self.binding,self.expected = finalizer.binding,finalizer._binding
        initial = self.member_bounds(decision,0)
        if not hasattr(decision,'_hosted_reads'):
            start_finalization(decision)
        self.ledger = decision._hosted_reads
        self.counts,self.members = self.ledger['counts'],self.ledger['members']
        require(type(self.counts) is dict and type(self.members) is dict
                and set(self.members) == {decision}, ERROR)
        self.count_floor = dict(self.counts)
        self.member_floor = {decision:(*initial[:-1],self.members[decision])}
        self.observation_floor = self.ledger['protection_observations']
        self.budget = ReadBudget(decision)
        self.check()

    @staticmethod
    def member_bounds(member, highwater):
        return (member.clock,member.monotonic,member.end,member.deadline,
                member.api_requests,highwater)

    def validate(self):
        require(self.binding() == self.expected and self.budget.state is self.ledger
                and self.ledger['counts'] is self.counts
                and self.ledger['members'] is self.members
                and set(self.counts) == set(self.count_floor) == set(LIMITS)
                and set(self.members) == set(self.member_floor)
                and self.ledger['finalization'] is True
                and self.ledger['staging'] is False
                and self.ledger['qualification'] is False, ERROR)
        require(all(type(value) is int and self.count_floor[key] <= value
                    <= (18 if key == 'protection' else LIMITS[key])
                    for key,value in self.counts.items()), ERROR)
        observations = self.ledger['protection_observations']
        require(type(observations) is int
                and self.observation_floor <= observations <= 6, ERROR)
        for member,bounds in self.member_floor.items():
            clock,monotonic,end,deadline,requests,highwater = bounds
            require(member._hosted_reads is self.ledger and member.clock is clock
                    and member.monotonic is monotonic and member.end <= end
                    and member.deadline <= deadline
                    and type(member.api_requests) is int and member.api_requests >= requests
                    and type(self.members[member]) is int
                    and highwater <= self.members[member] <= member.api_requests, ERROR)

    def check(self):
        self.validate()
        self.budget.check()
        # ReadBudget checks invoke both selected clocks: observe their effects
        # before retaining the next high-water snapshot, not just before I/O.
        self.validate()
        self.count_floor = dict(self.counts)
        self.member_floor = {member:self.member_bounds(member,self.members[member])
                             for member in self.member_floor}
        self.observation_floor = self.ledger['protection_observations']

    def join(self, independent):
        self.check()
        bounds = self.member_bounds(independent,0)
        self.budget.join(independent)
        self.member_floor[independent] = bounds
        self.check()


class RemoteFinalizer(Opaque):
    __slots__ = ('bindings','_binding')
    def __init__(self, bindings):
        require(type(bindings) is RemoteBindings and type(bindings.plan) is PlanBindings
                and type(bindings.independent_plan) is PlanBindings and bindings.plan is not bindings.independent_plan
                and type(bindings.primary) is MeasurementClient and type(bindings.independent) is MeasurementClient
                and type(bindings.roots) is WorkerRoots and callable(bindings.read_stage), ERROR)
        a,b = bindings.primary,bindings.independent
        require(a is not b and a.principal != b.principal and a.origin != b.origin
                and a.credential_origin != b.credential_origin and a.approval_origin != b.approval_origin
                and a._binding[3] != b._binding[3]
                and all(x != y for x,y in zip(a._binding[4],b._binding[4]))
                and canonical(a.scope.record()) == canonical(b.scope.record())
                and a.scope.observer_refs == b.scope.observer_refs
                and a.scope.observer_refs == (a.principal,b.principal), ERROR)
        for principal in (bindings.stage_principal,bindings.authority_principal):
            ref(principal)
        worker = a.scope.plan.value()['configuration_template']['services']['worker_channel']['principal_ref']
        principals = (a.principal,b.principal,bindings.stage_principal,bindings.authority_principal)
        require(worker not in principals and len(set(principals)) == 4, ERROR)
        self.bindings = bindings
        self._binding = self.binding()

    def binding(self):
        b = self.bindings
        def plan_fields(plan):
            return tuple(getattr(plan,name) for name in PlanBindings.__dataclass_fields__)
        return (b.primary,b.independent,b.primary.binding(),b.independent.binding(),
                plan_fields(b.plan),plan_fields(b.independent_plan),b.stage_principal,
                b.read_stage,b.authority_principal,canonical(b.roots.entries))

    def _stage(self,plan,context,decision):
        b = self.bindings
        result = read_current(b.read_stage,plan.value()['staging_policy']['launch_ref'],
                              kind=StagingReadback,decision=decision)
        scope = b.primary.scope.record()
        require(result.principal_ref == b.stage_principal and result.plan_digest == plan.digest
                and result.case_ref == scope['case_ref'] and result.run_id == context.run_id
                and result.run_attempt == context.run_attempt and result.launch_ref == scope['launch_ref']
                and result.cleanup_ref == plan.value()['staging_policy']['cleanup_ref']
                and result.state == 'cleanup-acknowledged', ERROR)
        snapshot = asdict(result)
        del snapshot['observed_at'],snapshot['expires_at']
        return canonical(snapshot),canonical(snapshot['generation'])

    def _derive(self,context,token,plan_binding,client,decision,guard):
        guard.check()
        plan = current_plan(context,token,plan_binding,phase='protected',decision=decision)
        guard.check()
        require(plan.raw == client.scope.plan.raw, ERROR)
        stage,generation = self._stage(plan,context,decision)
        guard.check()
        observed = client.read(decision=decision)
        guard.check()
        require(type(observed) is Observed and observed.decision is decision
                and observed.generation == generation, ERROR)
        expected = expected_bytes(plan,context,document(generation),self.bindings.roots,decision)
        guard.check()
        require((observed.configuration,observed.policy) == expected, ERROR)
        fresh = current_plan(context,token,plan_binding,phase='protected',decision=decision)
        require(fresh.raw == plan.raw and self._stage(fresh,context,decision) == (stage,generation)
                and self.binding() == self._binding, ERROR)
        guard.check()
        return expected,generation,observed.nonce

    def finalize(self,context,token,*,decision):
        return private(lambda:self._finalize(context,token,decision))
    def _finalize(self,context,token,decision):
        require(type(decision) is Decision and context == self.bindings.primary.scope.context
                and decision.clock is self.bindings.plan.clock
                and decision.monotonic is self.bindings.plan.monotonic, ERROR)
        guard = _FinalizationGuard(self,decision)
        with _read_checkpoint(decision,guard.ledger):
            return self._guarded_finalize(context,token,decision,guard)

    def _guarded_finalize(self,context,token,decision,guard):
        b = self.bindings
        expected,generation,first = self._derive(context,token,b.plan,b.primary,decision,guard)
        guard.check()
        own = Decision(clock=b.independent_plan.clock,monotonic=b.independent_plan.monotonic,
                       deadline=decision.deadline)
        guard.check()
        guard.join(own)
        second,other,independent_nonce = self._derive(context,token,b.independent_plan,b.independent,own,guard)
        require(second == expected and other == generation and independent_nonce != first, ERROR)
        guard.check()
        last,last_generation,last_nonce = self._derive(context,token,b.plan,b.primary,decision,guard)
        require(last == expected and last_generation == generation
                and len({first,independent_nonce,last_nonce}) == 3, ERROR)
        guard.check()
        provenance = canonical(dict(observers=list(b.primary.scope.observer_refs),
            credentials=[b.primary.credential_origin,b.independent.credential_origin],
            approvals=[b.primary.approval_origin,b.independent.approval_origin],
            scope=b.primary.scope.record(),nonces=[first,independent_nonce,last_nonce]))
        guard.check()
        return VerifiedRemote(_SEAL,*expected,generation,provenance,decision,self._binding)
