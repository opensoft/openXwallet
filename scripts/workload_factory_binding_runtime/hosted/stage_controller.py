"""Explicit source-selected v2 controller; public requests select no host capability."""
from dataclasses import dataclass
from workload_factory_binding.evidence import BindingError,canonical,digest,require
from ..github_bootstrap.common import Decision
from .admission import PlanBindings,selected_plan
from .staging import StageAuthority,StageCorrelator,scope_of
from .stage_store import StageStore,ERROR
from .readback import ReadBudget


@dataclass(frozen=True,repr=False)
class StageAdmission:
    profile:str
    phase:str
    case_ref:str
    plan_digest:str
    environment:str
    launch_ref:str
    state:str
    valid_until:int


class StageController:
    def __init__(self,*,context,preflight,protected,correlator,authority,host,store,register_cleanup):
        require(type(preflight) is PlanBindings and preflight.policy.phase=="preflight"
                and type(protected) is PlanBindings and protected.policy.phase=="protected"
                and type(correlator) is StageCorrelator and type(authority) is StageAuthority
                and type(store) is StageStore and store.kind=="controller" and callable(register_cleanup),ERROR)
        self.context,self.preflight,self.protected=context,preflight,protected
        self.correlator,self.authority,self.host,self.store,self.register_cleanup=correlator,authority,host,store,register_cleanup

    def _inputs(self,value):
        require(type(value) is dict and set(value)=={"accepted_commit","selection_digest","preauthorization_ref"}
                and all(value[k]==getattr(self.context,k) for k in value),ERROR)

    def _admission(self,plan,phase,state,decision):
        value=plan.value();decision.now()
        return StageAdmission("openxfactory-hosted-admission-internal-v2",phase,value["configuration_template"]["case_ref"],
            plan.digest,value["configuration_template"]["launch"]["environment"],value["staging_policy"]["launch_ref"],state,decision.deadline)

    def handle(self,phase,inputs,token,*,decision):
        try:
            require(phase in ("preflight","protected"),ERROR);self._inputs(inputs)
            bindings=self.preflight if phase=="preflight" else self.protected
            # Signed identity is authenticated before protected grant/provider effects.
            plan=selected_plan(self.context,token,bindings,phase=phase,decision=decision)
            scope=scope_of(plan,self.context,self.correlator.policy)
            grant=None;status_counted=False
            if phase=="protected":
                if self.store.known(scope["launch_ref"],scope,decision=decision):
                    self.store.status_read(scope["launch_ref"],decision=decision);status_counted=True
                grant=self.authority.launch_grant(scope,decision=decision)
            current,actual_scope=self.correlator.correlate(self.context,token,bindings,phase=phase,decision=decision)
            require(current.raw==plan.raw and canonical(scope)==canonical(actual_scope),ERROR)
            if phase=="preflight":return self._admission(plan,phase,"plan-ready",decision)
            ref=scope["launch_ref"]
            new=self.store.reserve(ref,scope,decision=decision,expires_at=grant["expires_at"])
            if not new:
                if not status_counted:self.store.status_read(ref,decision=decision)
                row=self.store.read(ref,decision=decision);status=self.host.status(ref,decision=decision)
                if row["unit"] is not None:require(canonical(status["unit"])==canonical(row["unit"]),ERROR)
                elif status["state"]=="registered":
                    self.store.transition(ref,"reserved","registered",decision=decision,unit=status["unit"])
                if status["state"]=="running":
                    require(row["state"] in ("start-consumed","running") and row["unit"] is not None,ERROR)
                    if row["generation"] is None:
                        self.store.transition(ref,"start-consumed","running",decision=decision,generation=status["generation"])
                    else:require(canonical(status["generation"])==canonical(row["generation"]),ERROR)
                return self._admission(plan,phase,status["state"],decision)
            registered=self.host.register(ref,decision=decision)
            require(registered["state"]=="registered" and registered["scope_digest"]==digest(scope),ERROR)
            unit=registered["unit"];self.store.transition(ref,"reserved","registered",decision=decision,unit=unit)
            ReadBudget(decision).consume("private")
            # Request result confers no acknowledgement: read independent mTLS facts.
            self.register_cleanup(scope,unit,deadline=decision.deadline)
            lease=self.authority.acknowledged(scope,unit,decision=decision);self.store.bind_lease(ref,lease,decision=decision)
            self.store.transition(ref,"registered","start-consumed",decision=decision)
            def still_current():
                self.authority.launch_grant(scope,decision=decision)
                require(canonical(self.authority.acknowledged(scope,unit,decision=decision))==canonical(lease),ERROR)
            result=self.host.start(ref,digest(unit),decision=decision,before_send=still_current)
            require(result["scope_digest"]==digest(scope) and result["state"]=="running"
                    and canonical(result["unit"])==canonical(unit) and result["generation"] is not None,ERROR)
            self.store.transition(ref,"start-consumed","running",decision=decision,generation=result["generation"])
            return self._admission(plan,phase,"running",decision)
        except Exception:raise BindingError(ERROR) from None
