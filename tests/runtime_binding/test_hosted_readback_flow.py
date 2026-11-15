"""Complete protected correlation with independent current readers; no live operations."""
from copy import deepcopy
from dataclasses import replace,asdict
from types import SimpleNamespace
import pytest
from workload_factory_binding.evidence import BindingError,digest,canonical
from workload_factory_binding_runtime.github_bootstrap.provider import ProviderReader
from workload_factory_binding_runtime.github_bootstrap.https import Response as LegacyResponse
from workload_factory_binding_runtime.hosted.readback import ReadScope,ReadBudget,ERROR
from workload_factory_binding_runtime.hosted.github_readback import ProtectedReadbacks
from .hosted_fixture import child_generations
from .readback_fixture import rb,GITHUB
from .test_github_bootstrap_correlation import g,configuration,c,l,w,dispatch,row
from .test_hosted_finalization import v
from .custody_fixture import k
from .test_custody import _owning_run
from workload_factory_binding_runtime.bootstrap import selection_document
from workload_factory_binding_runtime.hosted.admission import preflight
from workload_factory_binding_runtime.hosted.finalization import FinalAuthority
from workload_factory_binding_runtime.hosted.readback import DecisionRead
from workload_factory_binding_runtime.hosted.platform_readback import PlanFactReader


def select(g,rb):
    # Freeze independent source observations once; later candidate or provider
    # mutations do not rewrite this authoritative fixture snapshot.
    config=g.approval.configuration
    rb.g=g;rb.now=g.now;rb.scope=ReadScope(config["case_ref"],g.context.selection_digest,g.source,g.context.run_id,"1")
    rb.main_sha=g.source;rb.hold.update(source_sha=g.source,not_before=g.now-1,expires_at=g.now+60)
    rb.keydata["attributes"].update(nbf=g.now-1,exp=g.now+100);rb.issuer["credential_expires_at"]=g.now+40
    p=config["protection"];rb.environment.update(id=int(p["environment_id"]),name=p["environment"])
    rb.environment["protection_rules"][0]["reviewers"]=[{"type":x["type"],"reviewer":{"id":int(x["id"])}} for x in p["reviewer_ids"]]
    class ActualProvider:
        def exchange(self,*args,**kwargs):
            result=rb.routed().exchange(*args,**kwargs);return LegacyResponse(result.status,result.body)
    controller=g.controller("protected");controller.provider=ProviderReader(credential=lambda **_:"fixture-reader",transport=ActualProvider())
    return ProtectedReadbacks(controller=controller,github=rb.github(),hold=rb.client(),hold_ref="hold:fixture",hold_owner="principal:hold-owner")


def run(g,rb,**changes):
    selected=select(g,rb);dispatch(g);use=g.decision()
    return selected.correlate(g.approval.ref,g.token("protected",**changes),g.context,decision=use),use


def test_complete_protected_correlation_current_source_protection_and_hold(g,rb):
    selected=select(g,rb);dispatch(g);use=g.decision()
    result=selected.correlate(g.approval.ref,g.token("protected"),g.context,decision=use)
    assert result.correlation.run_id=="789"
    assert result.correlation.phase=="protected"
    assert result.environment.protection==g.approval.configuration["protection"]
    assert result.control.digest==rb.hold["control_digest"]
    assert result.valid_until<=g.now+10
    assert ReadBudget(use).github_requests==12
    assert use.api_requests==4
    assert ReadBudget(use).count("source")==4
    assert ReadBudget(use).count("protection")==2
    assert ReadBudget(use).count("control")==2
    assert len(row(g))==1
    assert all(method=="GET" or path=="/readback" for method,path in rb.calls)
    assert g.w.c.h.calls==0


@pytest.mark.parametrize("where,change",[("run","sha"),("run","attempt"),("run","repo"),("review","human"),("review","self"),
    ("source","main"),("source","blob"),("protection","bypass"),("control","digest"),("hold","revoke"),("hold","owner"),("hold","window")])
def test_each_independent_protected_fact_mutation_refuses_with_fixed_candidate(g,rb,where,change):
    selected=select(g,rb);dispatch(g);candidate=g.approval.commitment
    if where=="run":
        if change=="sha":g.run["head_sha"]="c"*40
        elif change=="attempt":g.run["run_attempt"]=2
        else:g.run["repository"]["id"]=999
    elif where=="review":g.reviews[0]["user"]["id"]=int(g.approval.initiating_user_id) if change=="self" else 999
    elif where=="source":
        if change=="main":rb.main_sha="c"*40
        else:rb.contents[next(iter(rb.contents))]["content"]="eA=="
    elif where=="protection":rb.environment["can_admins_bypass"]=True
    elif where=="control":rb.hold["control_digest"]="sha256:"+"f"*64
    elif change=="revoke":rb.hold["state"]="revoked"
    elif change=="owner":rb.hold["owner_ref"]="worker:unselected"
    else:rb.hold["expires_at"]=g.now
    use=g.decision();token=g.token("protected")
    with pytest.raises(BindingError):selected.correlate(g.approval.ref,token,g.context,decision=use)
    assert g.approval.commitment==candidate
    assert g.w.c.h.calls==0


@pytest.mark.parametrize("change",["source","hold","control","wall","monotonic"])
def test_late_current_mutation_after_blocking_reads_cannot_return_readiness(g,rb,change):
    selected=select(g,rb);dispatch(g);seen=[];use=g.decision()
    def mutate(method,path):
        if path.endswith("/approvals"):
            seen.append(True)
            if change=="source":rb.main_sha="c"*40
            elif change=="hold":rb.hold["state"]="revoked"
            elif change=="control":rb.rule["bypass_actors"]=[{"actor_type":"Team","actor_id":42,"bypass_mode":"always"}]
            elif change=="wall":g.now+=10;rb.now=g.now
            else:use.end=use.monotonic()
    rb.hook=mutate;token=g.token("protected")
    with pytest.raises(BindingError):selected.correlate(g.approval.ref,token,g.context,decision=use)
    assert seen
    assert g.w.c.h.calls==0


def test_two_job_pages_cannot_reset_existing_four_correlation_reads(g,rb):
    selected=select(g,rb);dispatch(g)
    g.jobs=[g.jobs[0],g.jobs[1]]+[{"id":n+10,"name":"unrelated","run_id":789,"status":"completed"} for n in range(99)]
    use=g.decision();token=g.token("protected")
    with pytest.raises(BindingError):selected.correlate(g.approval.ref,token,g.context,decision=use)
    assert use.api_requests==4
    assert ReadBudget(use).github_requests<=13


def test_bootstrap_identity_wrong_phase_or_worker_cannot_reach_current_protected_path(g,rb):
    selected=select(g,rb);dispatch(g);use=g.decision();wrong=g.token("preflight")
    with pytest.raises(BindingError):selected.correlate(g.approval.ref,wrong,g.context,decision=use)
    assert g.w.c.h.calls==0



def test_all_selected_fact_sources_share_the_protected_parent_decision(g,rb):
    selected=select(g,rb);dispatch(g);use=g.decision()
    result=selected.correlate(g.approval.ref,g.token("protected"),g.context,decision=use)
    deployment=rb.deployment_reader().read(decision=use)
    issuer=rb.issuer_reader().read("issuance:fixture",decision=use)
    guest=rb.guest_reader().read("guest:fixture",decision=use)
    state=rb.state_reader().read(decision=use)
    assert deployment.data()["vm_id"]==guest.data()["host_id"]
    assert deployment.data()["incarnation_id"]==guest.data()["incarnation_id"]
    assert issuer.data()["repository_id"]==result.environment.protection["repository_id"]
    assert state.data()["initialization_digest"]==digest(rb.initial)
    assert ReadBudget(use).github_requests==12
    assert ReadBudget(use).count("arm")==6
    assert ReadBudget(use).count("private")==7
    assert use.deadline<=result.valid_until



def plan_readers(v,rb):
    config=v.selected.value()["configuration_template"]
    rb.now=v.h.now;rb.scope=ReadScope(config["case_ref"],v.selected.digest,v.context.source_commit,v.context.run_id,"1")
    rb.main_sha=v.context.source_commit
    p=config["protection"];rb.environment.update(id=int(p["environment_id"]),name=p["environment"])
    rb.environment["protection_rules"][0]["reviewers"]=[{"type":x["type"],"reviewer":{"id":int(x["id"])}} for x in p["reviewer_ids"]]
    rb.planfacts={k:value for k,value in asdict(v.facts).items() if k not in ("principal_ref","observed_at","expires_at")}
    facts=PlanFactReader(client=rb.client());github=rb.github();seen=[]
    def fact(ref,*,decision):seen.append(decision);return facts.read(ref,decision=decision)
    def environment(name,*,decision):seen.append(decision);return github.environment(name,decision=decision)
    return {"facts_principal":rb.primary.principal,"read_facts":DecisionRead(fact),"environment_principal":rb.primary.principal,
        "read_environment":DecisionRead(environment)},seen


def test_v2_preflight_uses_pinned_current_plan_facts_and_actual_environment_reader(v,rb):
    readers,seen=plan_readers(v,rb);bindings=replace(v.preflight,**readers)
    result=preflight(v.context,v.pre_token,bindings=bindings)
    assert result.plan_digest==v.selected.digest
    assert result.environment==v.plan["configuration_template"]["launch"]["environment"]
    assert v.process is None
    assert len(seen)==3
    assert all(item is seen[0] for item in seen)
    assert ReadBudget(seen[0]).count("protection")==2
    assert ReadBudget(seen[0]).count("private")==2
    assert not hasattr(result,"config_digest")


@pytest.mark.parametrize("change",["state","preauthorization","plan","case","source","run","hosting","protection","scheduler"])
def test_current_v2_plan_facts_are_independent_of_approved_candidate(v,rb,change):
    readers,seen=plan_readers(v,rb);bindings=replace(v.preflight,**readers)
    if change=="state":rb.planfacts["state"]="revoked"
    elif change=="preauthorization":rb.planfacts["preauthorization_ref"]="preauth:other"
    elif change=="plan":rb.planfacts["plan_digest"]="sha256:"+"f"*64
    elif change=="case":rb.planfacts["case_ref"]="case:other"
    elif change=="source":rb.planfacts["accepted_commit"]="c"*40
    elif change=="run":rb.planfacts["launch"]["run_id"]="999"
    else:rb.planfacts[{"hosting":"hosting_selection_digest","protection":"protection_digest","scheduler":"scheduler_capability_digest"}[change]]="sha256:"+"f"*64
    with pytest.raises(BindingError):preflight(v.context,v.pre_token,bindings=bindings)
    assert v.process is None


def test_v2_revocation_after_environment_read_is_currently_observed(v,rb):
    readers,seen=plan_readers(v,rb);bindings=replace(v.preflight,**readers)
    def revoked(method,path):
        if "/deployment-branch-policies" in path:rb.planfacts["state"]="revoked"
    rb.hook=revoked
    with pytest.raises(BindingError):preflight(v.context,v.pre_token,bindings=bindings)
    assert len(seen)==3
    assert v.process is None


def test_repeated_finalization_protection_reads_refuse_instead_of_resetting_budget(v,rb):
    from workload_factory_binding_runtime.hosted.admission import current_plan
    from workload_factory_binding_runtime.github_bootstrap.common import Decision
    readers,seen=plan_readers(v,rb);bindings=replace(v.protected,**readers)
    use=Decision(clock=bindings.clock,monotonic=bindings.monotonic)
    current_plan(v.context,v.token,bindings,phase="protected",decision=use)
    with pytest.raises(BindingError):current_plan(v.context,v.token,bindings,phase="protected",decision=use)
    assert ReadBudget(use).count("protection")==3
    assert sum("/deployment-branch-policies" in path for _,path in rb.calls)==1
    assert v.h.calls==0


def test_current_protected_readbacks_gate_existing_owning_proof_and_replay(g,rb,k,tmp_path):
    retained={}
    def before_proof(current,create_proof):
        g.approval=replace(g.approval,selection=selection_document(current.config));g.context=g.approval.context("789")
        selected=select(g,rb);dispatch(g);use=g.decision()
        result=selected.correlate(g.approval.ref,g.token("protected"),g.context,decision=use)
        assert result.correlation.run_id==current.config["launch"]["run_id"]
        current.context=replace(current.context,expires_at=min(current.context.expires_at,result.valid_until))
        retained["decision"]=use;retained["result"]=result
        current.bridge=current.make(create_proof=create_proof)
    def perform(run):
        result=run()
        from openwallet_runtime.proof import verify_proof
        verified=verify_proof(result["proof"],expected_digest=k.c.h.challenge.digest,binding=k.c.h.binding,now=k.c.h.now)
        assert verified.subject_ref==k.c.h.binding.subject_ref
        assert result["human_approval"] is False
        with pytest.raises(BindingError):run()
        return result
    k.c.h.claims.update(k.c.config["launch"])
    k.c.h.policy["claims"].update({name:k.c.config["launch"][name] for name in k.c.h.policy["claims"]})
    k.access=replace(k.access,sources_digest=digest(k.c.config["sources"]))
    directory=tmp_path/"readback-owning-custody";directory.mkdir(mode=0o700)
    _owning_run(k,directory,before_proof=before_proof,perform=perform)
    assert ReadBudget(retained["decision"]).github_requests==12
    assert len(row(g))==1


def current_finalizer(v,rb):
    readers,seen=plan_readers(v,rb);v.start()
    v.bindings=replace(v.bindings,plan=replace(v.bindings.plan,**readers))
    v.authority=FinalAuthority(replace(v.authority_bindings,plan=replace(v.authority_bindings.plan,**readers)))
    return seen


def test_six_fresh_protection_observations_finish_actual_finalization(v,rb):
    seen=current_finalizer(v,rb);result=v.finalize()
    assert result.binding.plan_digest==v.selected.digest
    assert result.configuration and result.policy and v.h.calls==0
    members=set(seen);assert len(members)==2
    states=[ReadBudget(item).state for item in members];assert states[0] is states[1]
    assert ReadBudget(seen[0]).count("protection")==12
    assert ReadBudget(seen[0]).count("private")==12
    assert sum("/deployment-branch-policies" in path for _,path in rb.calls)==6


@pytest.mark.parametrize("position",range(1,7))
def test_each_finalization_protection_observation_is_fresh_and_independent(v,rb,position):
    seen=current_finalizer(v,rb);original=deepcopy(v.plan);calls=0
    def change(method,path):
        nonlocal calls
        if "/deployment-branch-policies" in path:
            calls+=1
            if calls==position:rb.policies["branch_policies"][0]["type"]="tag"
    rb.hook=change
    with pytest.raises(BindingError):v.finalize()
    assert calls==position and v.plan==original and v.h.calls==0


def test_current_finalization_reaches_unchanged_admission_and_owning_proof(v,rb):
    import json
    from workload_factory_binding_runtime.hosted.finalization import admit_finalized
    current_finalizer(v,rb);result=v.finalize();c,h,w=v.c,v.h,v.w
    c.config.clear(); c.config.update(json.loads(result.configuration)); h.policy = json.loads(result.policy)
    h.claims.update(c.config["launch"])
    h.artifacts, h.configuration = dict(v.launch.artifacts), v.launch.expected_configuration(v.projection)
    h.reset_evidence(); c.reselect_policy()
    life = w.lease_fixture
    life.plan = replace(life.plan, scope=replace(life.plan.scope, config_digest=result.binding.config_digest))
    life.janitor.plan = life.plan
    for ref, managed in life.managed.items():
        if managed.resource.retention == "run": life.managed[ref] = replace(managed, owner_scope_digest=digest(asdict(life.plan.scope)))
    life.life = life.make()
    w.bindings = replace(w.bindings, runtime_trust=c.trust, lifecycle=life.life)
    w.authorization = replace(w.authorization, config_digest=result.binding.config_digest)
    w.scheduler = replace(w.scheduler, plan_digest=life.plan.digest)
    context = replace(w.context, config_digest=result.binding.config_digest)
    admission = admit_finalized(result, context, bindings=w.bindings)
    assert admission.config_digest == result.binding.config_digest
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    h.binding = TrustedKeyBinding(**asdict(h.binding))
    bridge = c.make(create_proof=create_proof)
    proof = bridge.sign(h.challenge.id, h.request, h.token, h.observation)
    assert verify_proof(proof["proof"], expected_digest=h.challenge.digest, binding=h.binding, now=h.now).subject_ref == h.binding.subject_ref
    assert proof["human_approval"] is False
    assert h.calls == 1

    with pytest.raises(BindingError):bridge.sign(h.challenge.id,h.request,h.token,h.observation)
    assert h.calls==1
