"""Protected-phase reconstruction and independent complete-byte acceptance.

Staging launch and authority issuance are separate capabilities. Explicit T012S
registration can hand accepted bytes to selected lifecycle construction; the result
still requires unchanged full admission and never implies proof readiness.
"""
from dataclasses import dataclass, asdict, replace
from workload_factory_binding.evidence import BindingError, canonical, digest, integer, require
from ..config import _handle
from ..github_bootstrap.common import Decision, document
from . import ERROR
from .admission import PlanBindings, current_plan, read_current
from .measurement import MeasurementBindings, LaunchObservation, measure
from .readback import ReadBudget, start_finalization


@dataclass(frozen=True, repr=False)
class StagingReadback:
    principal_ref: str
    plan_digest: str
    case_ref: str
    run_id: str
    run_attempt: str
    launch_ref: str
    cleanup_ref: str
    generation: dict
    state: str
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class FinalizationBindings:
    plan: PlanBindings
    measurement: MeasurementBindings
    stage_principal: str
    read_stage: object
    authority_principal: str


@dataclass(frozen=True, repr=False)
class FinalizationBinding:
    principal_ref: str
    plan_digest: str
    case_ref: str
    source_commit: str
    run_id: str
    run_attempt: str
    generation_digest: str
    policy_digest: str
    config_digest: str
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class FinalizedPlan:
    configuration: bytes
    policy: bytes
    binding: FinalizationBinding


def _derive(context, token, bindings, *, decision):
    require(type(bindings) is FinalizationBindings and type(bindings.plan) is PlanBindings
            and type(bindings.measurement) is MeasurementBindings
            and callable(bindings.read_stage) and callable(bindings.measurement.observe), ERROR)
    plan = current_plan(context, token, bindings.plan, phase="protected", decision=decision)
    value = plan.value()
    config, s = value["configuration_template"], value["staging_policy"]
    worker = config["services"]["worker_channel"]["principal_ref"]
    principals = (bindings.stage_principal, bindings.measurement.principal_ref, bindings.authority_principal)
    for principal in principals:
        _handle(principal)
    require(worker not in principals and len(set(principals)) == 3, ERROR)
    stage = read_current(bindings.read_stage, s["launch_ref"], kind=StagingReadback, decision=decision)
    require(stage.principal_ref == bindings.stage_principal and stage.plan_digest == plan.digest
            and stage.case_ref == config["case_ref"] and stage.run_id == context.run_id
            and stage.run_attempt == context.run_attempt and stage.launch_ref == s["launch_ref"]
            and stage.cleanup_ref == s["cleanup_ref"] and stage.state == "cleanup-acknowledged", ERROR)
    # Freeze the acknowledged scope before any callback can mutate a reused dict.
    initial = asdict(stage)
    del initial["observed_at"], initial["expires_at"]
    stage_snapshot = canonical(initial)
    observed = read_current(bindings.measurement.observe, s["launch_ref"], kind=LaunchObservation, decision=decision)
    _handle(observed.invocation_ref)
    raw, policy, generation = measure(plan, context, bindings.measurement, observed, decision=decision)
    require(canonical(initial["generation"]) == canonical(generation), ERROR)
    # Recheck revocation/source/hold/protection after blocking kernel/file reads.
    current = current_plan(context, token, bindings.plan, phase="protected", decision=decision)
    require(current.raw == plan.raw, ERROR)
    final_stage = read_current(bindings.read_stage, s["launch_ref"], kind=StagingReadback, decision=decision)
    final = asdict(final_stage)
    del final["observed_at"], final["expires_at"]
    require(stage_snapshot == canonical(final), ERROR)
    return plan, raw, policy, generation


class FinalAuthority:
    """Independently selected capability; recomputes actual bytes, not caller hashes.

    Deployed authentication/admin separation is a later qualification gate.
    No worker constructor, network listener or signer is exposed by this class.
    """
    def __init__(self, bindings):
        require(type(bindings) is FinalizationBindings, ERROR)
        self.bindings = bindings

    def approve(self, context, token, *, configuration, policy, decision):
        try:
            require(type(decision) is Decision, ERROR)
            remaining = decision.remaining()
            own = Decision(clock=self.bindings.plan.clock, monotonic=self.bindings.plan.monotonic,
                           deadline=decision.deadline)
            own.end = min(own.end, own.last_mono + remaining)
            ReadBudget(decision).join(own)
            plan, actual, actual_policy, generation = _derive(context, token, self.bindings, decision=own)
            require(type(configuration) is bytes and type(policy) is bytes
                    and configuration == actual and policy == actual_policy, ERROR)
            ReadBudget(own).check()
            now = own.now()
            decision.clip(own.deadline)
            config = document(actual, 16384)
            return FinalizationBinding(self.bindings.authority_principal, plan.digest, config["case_ref"],
                context.source_commit, context.run_id, context.run_attempt, digest(generation),
                digest(document(actual_policy, 16384)), digest(config), now, own.deadline)
        except Exception:
            raise BindingError(ERROR) from None


def finalize(context, token, *, bindings, authority):
    try:
        require(type(bindings) is FinalizationBindings and type(authority) is FinalAuthority
                and authority.bindings is not bindings
                and authority.bindings.measurement.principal_ref != bindings.measurement.principal_ref
                and authority.bindings.authority_principal == bindings.authority_principal, ERROR)
        decision = Decision(clock=bindings.plan.clock, monotonic=bindings.plan.monotonic)
        start_finalization(decision)
        plan, configuration, policy, generation = _derive(context, token, bindings, decision=decision)
        accepted = authority.approve(context, token, configuration=configuration, policy=policy, decision=decision)
        require(type(accepted) is FinalizationBinding and accepted.principal_ref == bindings.authority_principal
                and accepted.plan_digest == plan.digest and accepted.generation_digest == digest(generation)
                and accepted.config_digest == digest(document(configuration, 16384))
                and accepted.policy_digest == digest(document(policy, 16384))
                and accepted.case_ref == plan.value()["configuration_template"]["case_ref"]
                and accepted.source_commit == context.source_commit and accepted.run_id == context.run_id
                and accepted.run_attempt == context.run_attempt, ERROR)
        now = decision.now()
        require(integer(accepted.observed_at) and integer(accepted.expires_at)
                and accepted.observed_at <= now < accepted.expires_at <= accepted.observed_at + 60
                and accepted.expires_at <= decision.deadline, ERROR)
        decision.clip(accepted.expires_at)
        fresh_plan, fresh_config, fresh_policy, fresh_generation = _derive(context, token, bindings, decision=decision)
        require(fresh_plan.raw == plan.raw and fresh_config == configuration and fresh_policy == policy
                and fresh_generation == generation, ERROR)
        decision.now()
        ReadBudget(decision).check()
        return FinalizedPlan(configuration, policy, accepted)
    except Exception:
        raise BindingError(ERROR) from None


def admit_finalized(finalized, context, *, bindings):
    """Explicit handoff to unchanged full admission and final cleanup checks.

    Callers must supply separately approved actual-run WorkflowBindings, operation
    grant and final lifecycle. Finalization alone supplies none of those capabilities.
    """
    from ..workflow import WorkflowBindings, WorkflowContext, admit
    try:
        require(type(finalized) is FinalizedPlan and type(finalized.binding) is FinalizationBinding
                and type(context) is WorkflowContext and type(bindings) is WorkflowBindings, ERROR)
        bound = finalized.binding
        require(context.config_digest == bound.config_digest
                and context.source_commit == bound.source_commit and context.run_id == bound.run_id
                and context.run_attempt == bound.run_attempt
                and bindings.runtime_trust.approved_config_digest == bound.config_digest, ERROR)
        def load():
            raw = bindings.load_config()
            require(canonical(document(raw, 16384)) == finalized.configuration, ERROR)
            return raw
        return admit(context, bindings=replace(bindings, load_config=load), deadline=bound.expires_at)
    except Exception:
        raise BindingError(ERROR) from None


def register_finalized_lifecycle(finalized, context, *, lifecycle, plan, decision):
    """Source-selected T012S handoff; no default activation or proof authority."""
    from .lifecycle import HostedLifecycle
    require(type(lifecycle) is HostedLifecycle and type(finalized) is FinalizedPlan
            and context == lifecycle.context and type(decision) is Decision, ERROR)
    return lifecycle.prepare_final(lifecycle.scope["launch_ref"], finalized, plan, decision=decision)
