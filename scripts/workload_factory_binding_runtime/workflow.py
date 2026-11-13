"""Admission for the prepared workflow; operational clients remain unselected.

Trusted hosting supplies authenticated current environment, authorization and
scheduler readbacks. Types and worker/dispatch fields confer no authority. No
provider resolver, token request, setup, execution or cleanup write lives here.
"""
from dataclasses import dataclass
import re

from workload_factory_binding.evidence import BindingError, digest, integer, reference, require, valid_digest
from .config import RuntimeTrust, _handle, _protection, validate_config
from .lifecycle import RunLifecycle
from .evidence import _plain

REPOSITORY = "opensoft/openXwallet"
CALLER = ".github/workflows/protected-runtime-qualification.yml"
REUSABLE = ".github/workflows/protected-runtime-qualification-run.yml"
REF = "refs/heads/main"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_NUMBER = re.compile(r"[1-9][0-9]{0,19}\Z")


@dataclass(frozen=True, repr=False)
class WorkflowContext:
    repository: str
    repository_id: str
    event_name: str
    ref: str
    sha: str
    workflow_ref: str
    workflow_sha: str
    run_id: str
    run_attempt: str
    accepted_commit: str
    config_digest: str
    operation_grant_ref: str
    source_commit: str


@dataclass(frozen=True, repr=False)
class EnvironmentReadback:
    principal_ref: str
    exists: bool
    protection: dict
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class OperationReadback:
    principal_ref: str
    grant_ref: str
    action: str
    config_digest: str
    accepted_commit: str
    case_ref: str
    run_id: str
    run_attempt: str
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class SchedulerReadback:
    principal_ref: str
    cleanup_ref: str
    plan_digest: str
    readback_principal_ref: str
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class WorkflowBindings:
    """Authenticated capabilities selected outside dispatch/worker input.

    Readbacks must obtain actual independent facts, never echo candidate fields.
    Their I/O must enforce the supplied epoch deadline. Production selection and
    real clients are T013/T014 hosting inputs; this is not an authentication API.
    """
    accepted_commit: str
    load_config: object
    runtime_trust: RuntimeTrust
    environment_principal_ref: str
    read_environment: object
    authorization_principal_ref: str
    read_authorization: object
    scheduler_principal_ref: str
    read_scheduler: object
    lifecycle: RunLifecycle


@dataclass(frozen=True, repr=False)
class WorkflowAdmission:
    environment: str
    source_commit: str
    config_digest: str
    run_id: str
    run_attempt: str
    valid_until: int


def validate_context(context):
    require(type(context) is WorkflowContext, "workflow-context-mismatch")
    require(context.repository == REPOSITORY and context.event_name == "workflow_dispatch"
            and context.ref == REF and context.workflow_ref == REPOSITORY + "/" + CALLER + "@" + REF
            and all(type(v) is str and _SHA.fullmatch(v) and v != "0" * 40 for v in
                    (context.sha, context.workflow_sha, context.accepted_commit, context.source_commit))
            and context.sha == context.workflow_sha == context.accepted_commit == context.source_commit
            and all(type(v) is str and _NUMBER.fullmatch(v) for v in
                    (context.repository_id, context.run_id, context.run_attempt))
            and valid_digest(context.config_digest) and reference(context.operation_grant_ref),
            "workflow-context-mismatch")
    try:
        _handle(context.operation_grant_ref)
    except Exception:
        raise BindingError("workflow-context-mismatch") from None


class _Admission:
    def __init__(self, bindings):
        self.bindings, self.last, self.deadline = bindings, None, None

    def now(self):
        try:
            now = self.bindings.runtime_trust.clock()
            require(integer(now) and (self.last is None or self.last <= now)
                    and (self.deadline is None or now < self.deadline), "workflow-admission-refused")
        except Exception:
            raise BindingError("workflow-admission-refused") from None
        self.last = now
        return now

    def read(self, callback, *args, kind):
        before = self.now()
        try:
            record = callback(*args, deadline=self.deadline)
        except Exception:
            raise BindingError("workflow-input-unavailable") from None
        now = self.now()
        require(type(record) is kind and integer(record.observed_at) and integer(record.expires_at)
                and before <= record.observed_at <= now < record.expires_at <= record.observed_at + 60,
                "workflow-admission-refused")
        self.deadline = min(self.deadline, record.expires_at)
        self.now()
        return record


def admit(context, *, bindings):
    """Check readiness before an environment/id-token-capable job is queued.

    This is bounded admission, not live qualification or authority issuance.
    Protected hosting must repeat fresh admission after environment approval.
    An external janitor/readback remains mandatory after runner hard death.
    """
    validate_context(context)
    require(type(bindings) is WorkflowBindings and type(bindings.runtime_trust) is RuntimeTrust
            and type(bindings.lifecycle) is RunLifecycle
            and bindings.accepted_commit == context.accepted_commit
            and all(callable(c) for c in (bindings.load_config, bindings.read_environment,
                                          bindings.read_authorization, bindings.read_scheduler))
            and all(reference(r) for r in (bindings.environment_principal_ref,
                                           bindings.authorization_principal_ref, bindings.scheduler_principal_ref)),
            "workflow-admission-refused")
    use = _Admission(bindings)
    before = use.now()
    try:
        selected = validate_config(bindings.load_config(), trust=bindings.runtime_trust)
    except Exception:
        raise BindingError("workflow-input-unavailable") from None
    require(selected.checked_at >= before and selected.config_digest == context.config_digest,
            "workflow-admission-refused")
    use.last, use.deadline = selected.checked_at, selected.valid_until
    use.now()
    selection, launch = selected.selection, selected.selection["launch"]
    require(all(launch[key] == getattr(context, key) for key in
                ("repository", "repository_id", "ref", "sha", "workflow_ref", "workflow_sha", "run_id", "run_attempt"))
            and launch["job_workflow_ref"] == REPOSITORY + "/" + REUSABLE + "@" + REF
            and launch["job_workflow_sha"] == context.source_commit
            and selection["sources"]["adapter"]["commit"] == context.source_commit
            and selection["sources"]["adapter"]["repository"] == REPOSITORY
            and selection["sources"]["caller_workflow"]["path"] == CALLER
            and selection["sources"]["reusable_workflow"]["path"] == REUSABLE,
            "workflow-admission-refused")
    worker = selection["services"]["worker_channel"]["principal_ref"]
    require(worker not in (bindings.environment_principal_ref, bindings.authorization_principal_ref,
                           bindings.scheduler_principal_ref), "workflow-admission-refused")
    environment = use.read(bindings.read_environment, launch["environment"], kind=EnvironmentReadback)
    try:
        _protection(environment.protection, dict(launch))
    except Exception:
        raise BindingError("workflow-admission-refused") from None
    require(type(environment) is EnvironmentReadback and environment.exists is True
            and environment.principal_ref == bindings.environment_principal_ref
            and digest(environment.protection) == digest(_plain(selection["protection"])),
            "workflow-admission-refused")
    grant = use.read(bindings.read_authorization, context.operation_grant_ref, kind=OperationReadback)
    require(type(grant) is OperationReadback and grant.principal_ref == bindings.authorization_principal_ref
            and grant.grant_ref == context.operation_grant_ref and grant.action == "qualify-existing-resources"
            and grant.config_digest == selected.config_digest and grant.accepted_commit == context.source_commit
            and grant.case_ref == selection["case_ref"] and grant.run_id == context.run_id
            and grant.run_attempt == context.run_attempt, "workflow-admission-refused")
    life = bindings.lifecycle
    plan, readback = life.plan, life.readback
    require(plan.scope.config_digest == selected.config_digest, "workflow-admission-refused")
    scheduler = use.read(bindings.read_scheduler, plan.ref, kind=SchedulerReadback)
    require(type(scheduler) is SchedulerReadback and scheduler.principal_ref == bindings.scheduler_principal_ref
            and scheduler.cleanup_ref == selection["lifecycle"]["cleanup_ref"]
            and scheduler.plan_digest == plan.digest
            and scheduler.readback_principal_ref == readback.identity.principal_ref,
            "workflow-admission-refused")
    checkpoint = life.check_for_use(deadline=use.deadline, checked_at=use.last)
    require(checkpoint.checked_at >= use.last, "workflow-admission-refused")
    use.last, use.deadline = checkpoint.checked_at, min(use.deadline, checkpoint.valid_until)
    use.now()
    require(life.plan is plan and life.readback is readback, "workflow-admission-refused")
    return WorkflowAdmission(launch["environment"], context.source_commit, selected.config_digest,
                             context.run_id, context.run_attempt, use.deadline)


def operational_bindings():
    """No environment flag/file/plugin can turn source acceptance into operation.

    A concrete authenticated hosting integration and operational authority must
    be separately selected/reviewed in T013/T014. No production service selected.
    """
    raise BindingError("workflow-operational-host-unselected")
