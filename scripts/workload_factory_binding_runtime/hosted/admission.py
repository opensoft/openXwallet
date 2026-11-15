"""Read-only v2 phase admission through explicitly selected trusted capabilities.

Typed records do not authenticate their source. Hosting must authenticate callback
peers and obtain actual journal/provider/control facts; T012Q supplies real clients.
No full-config/grant, launch, credential issuance or custody port is available here.
"""
from dataclasses import dataclass
from workload_factory_binding.evidence import BindingError, canonical, digest, integer, require, valid_digest
from ..bootstrap import validate_dispatch_context
from ..config import _handle, _protection
from ..github_bootstrap.common import Decision
from ..github_bootstrap.identity import BootstrapVerifier, IdentityPolicy, BOOTSTRAP_AUDIENCE
from ..workflow import EnvironmentReadback, REUSABLE, REF
from . import ERROR
from .plan import validate_plan


@dataclass(frozen=True, repr=False)
class PlanFacts:
    principal_ref: str
    plan_digest: str
    preauthorization_ref: str
    case_ref: str
    accepted_commit: str
    launch: dict
    hosting_selection_digest: str
    source_hold_ref: str
    protection_digest: str
    scheduler_capability_digest: str
    state: str
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class PlanBindings:
    approved_plan_digest: str
    load_plan: object
    verifier: BootstrapVerifier
    policy: IdentityPolicy
    facts_principal: str
    read_facts: object
    environment_principal: str
    read_environment: object
    clock: object
    monotonic: object


@dataclass(frozen=True, repr=False)
class PlanAdmission:
    plan_digest: str
    case_ref: str
    source_commit: str
    run_id: str
    run_attempt: str
    environment: str
    valid_until: int


def read_current(callback, *args, kind, decision):
    before = decision.now()
    result = callback(*args, deadline=decision.deadline)
    now = decision.now()
    require(type(result) is kind and integer(result.observed_at) and integer(result.expires_at)
            and before <= result.observed_at <= now < result.expires_at <= result.observed_at + 60, ERROR)
    decision.clip(result.expires_at)
    return result


def current_plan(context, token, bindings, *, phase, decision):
    require(type(bindings) is PlanBindings and type(bindings.policy) is IdentityPolicy
            and type(bindings.verifier) is BootstrapVerifier and bindings.policy.phase == phase
            and bindings.policy.audience == BOOTSTRAP_AUDIENCE
            and all(callable(f) for f in (bindings.load_plan, bindings.read_facts,
                                         bindings.read_environment, bindings.clock, bindings.monotonic)), ERROR)
    validate_dispatch_context(context)
    require(context.run_attempt == "1" and context.selection_digest == bindings.approved_plan_digest, ERROR)
    for ref in (bindings.facts_principal, bindings.environment_principal):
        _handle(ref)
    identity = bindings.verifier.verify(token, bindings.policy, now=decision.now())
    decision.clip(identity.valid_until)
    raw = bindings.load_plan()
    decision.now()
    plan = validate_plan(raw, approved_digest=bindings.approved_plan_digest, now=decision.now())
    decision.clip(plan.valid_until)
    value = plan.value()
    config = value["configuration_template"]
    launch = {**config["launch"], "run_id": context.run_id, "run_attempt": context.run_attempt}
    for k in ("repository", "repository_id", "sha", "ref", "workflow_ref", "workflow_sha"):
        require(launch[k] == getattr(context, k), ERROR)
    require(config["sources"]["adapter"]["commit"] == context.source_commit
            and config["sources"]["adapter"]["repository"] == context.repository
            and launch["job_workflow_ref"] == context.repository + "/" + REUSABLE + "@" + REF
            and launch["job_workflow_sha"] == context.source_commit
            and bindings.policy.proof_audience == config["issuer"]["audience"]
            and all(bindings.policy.expected[k] == v for k, v in launch.items()
                    if k not in ({"environment", "sub"} if phase == "preflight" else set())), ERROR)
    worker = config["services"]["worker_channel"]["principal_ref"]
    require(worker not in (bindings.facts_principal, bindings.environment_principal), ERROR)
    facts = read_current(bindings.read_facts, context.preauthorization_ref, kind=PlanFacts, decision=decision)
    def validate_facts(facts):
        require(facts.principal_ref == bindings.facts_principal and facts.plan_digest == plan.digest
                and facts.preauthorization_ref == context.preauthorization_ref and facts.case_ref == config["case_ref"]
                and facts.accepted_commit == context.accepted_commit and canonical(facts.launch) == canonical(launch)
                and facts.hosting_selection_digest == value["hosting_selection_digest"]
                and facts.source_hold_ref == value["source_hold_ref"]
                and facts.protection_digest == digest(config["protection"])
                and facts.scheduler_capability_digest == value["staging_policy"]["scheduler_capability_digest"]
                and facts.state == "consumed-current", ERROR)
    validate_facts(facts)
    env = read_current(bindings.read_environment, launch["environment"], kind=EnvironmentReadback, decision=decision)
    _protection(env.protection, launch)
    require(env.principal_ref == bindings.environment_principal and env.exists is True
            and canonical(env.protection) == canonical(config["protection"]), ERROR)
    # Source/hold/consumed scope may change while protection is read.
    final_facts = read_current(bindings.read_facts, context.preauthorization_ref, kind=PlanFacts, decision=decision)
    validate_facts(final_facts)
    # Reauthenticate after blocking reads; this grants neither proof nor staging authority.
    final_identity = bindings.verifier.verify(token, bindings.policy, now=decision.now())
    decision.clip(final_identity.valid_until)
    return plan


def preflight(context, token, *, bindings):
    try:
        require(type(bindings) is PlanBindings, ERROR)
        decision = Decision(clock=bindings.clock, monotonic=bindings.monotonic)
        plan = current_plan(context, token, bindings, phase="preflight", decision=decision)
        config = plan.value()["configuration_template"]
        decision.now()
        return PlanAdmission(plan.digest, config["case_ref"], context.source_commit,
                             context.run_id, context.run_attempt, config["launch"]["environment"], decision.deadline)
    except Exception:
        raise BindingError(ERROR) from None
