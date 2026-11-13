"""Static dispatch commitment and trusted run-bound admission, never authority issuance.

Authenticated bootstrap/approval clients are trusted hosting capabilities. The
default CLI has none. These types and dispatch fields authenticate no principal.
"""
from dataclasses import dataclass, replace

from workload_factory_binding.evidence import (
    BindingError, canonical, decode_object, digest, require, valid_digest,
)
from .config import RuntimeTrust, _configuration, _handle, _object
from .workflow import (
    WorkflowBindings, WorkflowContext, _Admission, _validate_launch_context, admit,
)

PROFILE = "openxfactory-dispatch-selection-internal-v1"


def selection_digest(raw):
    """Validate a separate static document; never validate executable runtime input."""
    try:
        selected = decode_object(raw)
        _object(selected, "profile configuration")
        require(selected["profile"] == PROFILE, "workflow-admission-refused")
        _configuration(selected["configuration"], run_bound=False)
        return digest(selected)
    except Exception:
        raise BindingError("workflow-admission-refused") from None


def selection_document(configuration):
    """Project a full, syntactically valid runtime config to its static document.

    Operators can instead prepare the closed static document before assignment;
    this projection is used to corroborate the final configuration after it.
    """
    _configuration(configuration)
    selected = decode_object(canonical(configuration))
    del selected["launch"]["run_id"]
    del selected["launch"]["run_attempt"]
    return canonical({"profile": PROFILE, "configuration": selected})


@dataclass(frozen=True, repr=False)
class DispatchContext:
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
    selection_digest: str
    preauthorization_ref: str
    source_commit: str


@dataclass(frozen=True, repr=False)
class BootstrapReadback:
    principal_ref: str
    preauthorization_ref: str
    selection_digest: str
    accepted_commit: str
    repository_id: str
    case_ref: str
    run_id: str
    run_attempt: str
    config_digest: str
    operation_grant_ref: str
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class BootstrapBindings:
    """Selected outside dispatch/worker control; not a resolver/plugin API.

    Reader authenticates actual GitHub context and atomically binds a current
    preauthorization to one run/attempt, refusing reuse. Client authentication,
    administrative isolation and atomicity require separate deployed acceptance.
    """
    approved_selection_digest: str
    principal_ref: str
    read_bootstrap: object
    workflow: WorkflowBindings


def validate_dispatch_context(context):
    require(type(context) is DispatchContext, "workflow-context-mismatch")
    _validate_launch_context(context)
    require(valid_digest(context.selection_digest), "workflow-context-mismatch")
    try:
        _handle(context.preauthorization_ref)
    except Exception:
        raise BindingError("workflow-context-mismatch") from None


def bootstrap(context, *, bindings):
    """Fresh independent bootstrap then full existing admission, with no signing."""
    validate_dispatch_context(context)
    require(type(bindings) is BootstrapBindings and type(bindings.workflow) is WorkflowBindings
            and type(bindings.workflow.runtime_trust) is RuntimeTrust
            and bindings.workflow.accepted_commit == context.accepted_commit
            and valid_digest(bindings.approved_selection_digest)
            and bindings.approved_selection_digest == context.selection_digest
            and callable(bindings.read_bootstrap), "workflow-admission-refused")
    try:
        _handle(bindings.principal_ref)
    except Exception:
        raise BindingError("workflow-admission-refused") from None
    use = _Admission(bindings.workflow)
    use.deadline = use.now() + 60
    bound = use.read(bindings.read_bootstrap, context.preauthorization_ref, context, kind=BootstrapReadback)
    require(bound.principal_ref == bindings.principal_ref
            and bound.preauthorization_ref == context.preauthorization_ref
            and bound.selection_digest == context.selection_digest
            and bound.accepted_commit == context.accepted_commit
            and bound.repository_id == context.repository_id
            and bound.run_id == context.run_id and bound.run_attempt == context.run_attempt
            and valid_digest(bound.config_digest)
            and bound.config_digest == bindings.workflow.runtime_trust.approved_config_digest,
            "workflow-admission-refused")
    try:
        _handle(bound.case_ref)
        _handle(bound.operation_grant_ref)
    except Exception:
        raise BindingError("workflow-admission-refused") from None

    def load_config():
        try:
            raw = bindings.workflow.load_config()
            config = decode_object(raw)
            require(selection_digest(selection_document(config)) == context.selection_digest
                    and config["case_ref"] == bound.case_ref
                    and bindings.principal_ref != config["services"]["worker_channel"]["principal_ref"],
                    "workflow-admission-refused")
            return raw
        except Exception:
            raise BindingError("workflow-input-unavailable") from None

    # Existing runtime context preserves full digest/grant meanings. It obtains
    # these only from the authenticated reader, never an immutable dispatch input.
    runtime = WorkflowContext(**{name: getattr(context, name) for name in (
        "repository", "repository_id", "event_name", "ref", "sha", "workflow_ref",
        "workflow_sha", "run_id", "run_attempt", "accepted_commit", "source_commit")},
        config_digest=bound.config_digest, operation_grant_ref=bound.operation_grant_ref)
    workflow = replace(bindings.workflow, load_config=load_config,
                       runtime_trust=replace(bindings.workflow.runtime_trust, clock=use.now))
    admitted = admit(runtime, bindings=workflow, deadline=use.deadline)
    use.now()
    return admitted
