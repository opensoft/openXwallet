"""Current static-v2 stage scope and independent provider/review corroboration."""
from dataclasses import dataclass,asdict
from workload_factory_binding.evidence import BindingError,canonical,digest,integer,require,valid_digest
from ..config import _handle
from ..github_bootstrap.common import number,Decision
from ..github_bootstrap.controller import run_binding,approved_reviews
from ..github_bootstrap.graph import validate_plan_graph
from ..github_bootstrap.provider import ProviderReader
from .admission import selected_plan,current_plan,PlanBindings
from .readback import ObservationClient,ReadBudget
from .github_readback import GithubReadbacks,positive
from .stage_store import ERROR


@dataclass(frozen=True,repr=False)
class StagePolicy:
    workflow_id:str
    broker_actor_id:str
    initiating_user_id:str
    reviewer_ids:tuple
    hold_owner:str

    def record(self):
        require(all(number(v) for v in (self.workflow_id,self.broker_actor_id,self.initiating_user_id))
                and self.initiating_user_id!=self.broker_actor_id and type(self.reviewer_ids) is tuple
                and 0<len(self.reviewer_ids)<=6 and len(set(self.reviewer_ids))==len(self.reviewer_ids)
                and all(number(v) and v not in (self.initiating_user_id,self.broker_actor_id) for v in self.reviewer_ids),ERROR)
        _handle(self.hold_owner);return asdict(self)


def scope_of(plan,context,policy):
    value=plan.value();c,s=value["configuration_template"],value["staging_policy"]
    return {"case_ref":c["case_ref"],"plan_digest":plan.digest,"source_commit":context.source_commit,
            "run_id":context.run_id,"run_attempt":context.run_attempt,"launch_ref":s["launch_ref"],
            "host_ref":s["host_ref"],"incarnation_ref":s["incarnation_ref"],"boot_id":s["boot_id"],
            "cleanup_ref":s["cleanup_ref"],"template_digest":s["template_digest"],
            "hosting_selection_digest":value["hosting_selection_digest"],"worker_uid":value["measurement_plan"]["uid"],"review_policy":policy.record()}


class StageAuthority:
    def __init__(self,*,grant,lease,grant_ref):
        require(type(grant) is ObservationClient and type(lease) is ObservationClient
                and grant.principal!=lease.principal and grant.origin!=lease.origin
                and grant.transport.server_certificate_digest!=lease.transport.server_certificate_digest
                and grant.scope==lease.scope,ERROR)
        _handle(grant_ref);self.grant,self.lease,self.ref=grant,lease,grant_ref

    def launch_grant(self,scope,*,decision):
        value=self.grant.read("stage-grant",self.ref,decision=decision).data()
        require(set(value)=={"scope","action","state","not_before","expires_at"}
                and canonical(value["scope"])==canonical(scope) and value["action"]=="launch-inert"
                and value["state"]=="active" and integer(value["not_before"]) and integer(value["expires_at"])
                and value["not_before"]<=decision.now()<value["expires_at"],ERROR)
        decision.clip(value["expires_at"]);return value

    def acknowledged(self,scope,unit,*,decision):
        value=self.lease.read("stage-lease",scope["cleanup_ref"],decision=decision).data()
        require(set(value)=={"scope_digest","unit_digest","state","expires_at"}
                and value["scope_digest"]==digest(scope) and value["unit_digest"]==digest(unit)
                and value["state"]=="acknowledged" and integer(value["expires_at"])
                and decision.now()<value["expires_at"],ERROR)
        decision.clip(value["expires_at"]);return value


class StageCorrelator:
    def __init__(self,*,github,hold,provider,policy):
        require(type(github) is GithubReadbacks and type(hold) is ObservationClient
                and type(provider) is ProviderReader and type(policy) is StagePolicy,ERROR)
        self.github,self.hold,self.provider,self.policy=github,hold,provider,policy
        self.policy_raw=canonical(policy.record())

    def hold_current(self,plan,*,decision):
        result=self.hold.read("hold",plan.value()["source_hold_ref"],decision=decision);value=result.data()
        require(set(value)==set("source_sha owner_ref control_id control_digest state not_before expires_at".split())
            and value["source_sha"]==self.hold.scope.source_commit and value["owner_ref"]==self.policy.hold_owner
            and value["state"]=="active" and valid_digest(value["control_digest"])
            and integer(value["not_before"]) and integer(value["expires_at"])
            and value["not_before"]<=decision.now()<value["expires_at"],ERROR)
        positive(value["control_id"]);decision.clip(value["expires_at"]);return result

    def correlate(self,context,token,bindings,*,phase,decision):
        require(type(bindings) is PlanBindings and canonical(self.policy.record())==self.policy_raw,ERROR)
        plan=selected_plan(context,token,bindings,phase=phase,decision=decision)
        scope=scope_of(plan,context,self.policy);c=plan.value()["configuration_template"];launch=c["launch"]
        hold=self.hold_current(plan,decision=decision);identifier=self.github.begin_control(hold.data()["control_id"],decision=decision)
        source=self.github.begin_source(context.source_commit,decision=decision);validate_plan_graph(source.graph,plan)
        reads=self.provider.decision(context.repository,decision)
        def run():return run_binding(reads.run(context.run_id),launch=launch,workflow_id=self.policy.workflow_id,
                                     broker_actor_id=self.policy.broker_actor_id,run_id=context.run_id)
        first=run();jobs=reads.jobs(context.run_id,"1");name="invoke / "+("admission" if phase=="preflight" else "protected-qualification")
        eligible=[j for j in jobs if j.get("name")==name]
        require(len(eligible)==1 and eligible[0].get("status")=="in_progress"
                and eligible[0].get("head_sha")==context.source_commit
                and type(eligible[0].get("run_id")) is int and str(eligible[0]["run_id"])==context.run_id,ERROR)
        if phase=="protected":approved_reviews(reads.reviews(context.run_id),protection=c["protection"],
            environment=launch["environment"],reviewer_ids=self.policy.reviewer_ids,initiating_user_id=self.policy.initiating_user_id)
        current=current_plan(context,token,bindings,phase=phase,decision=decision);require(current.raw==plan.raw,ERROR)
        require(run()==first,ERROR);self.github.finish_source(source,decision=decision)
        control=self.github.finish_control(identifier,decision=decision);require(control.digest==hold.data()["control_digest"],ERROR)
        require(self.hold_current(plan,decision=decision).digest==hold.digest,ERROR)
        ReadBudget(decision).check();return plan,scope
