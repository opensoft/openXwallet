"""Fresh bootstrap session adapting correlated configuration to existing admission."""
from dataclasses import asdict, replace
from workload_factory_binding.evidence import (BindingError, canonical, digest,
    integer, require)
from ..bootstrap import BootstrapBindings, BootstrapReadback, selection_digest, selection_document, validate_dispatch_context
from ..config import _configuration, _handle
from ..workflow import WorkflowBindings, OperationReadback
from . import ERROR, PROFILE, USER_AGENT
from .common import Decision, closed, document
from .https import Https, Response

def validate_response(value, context, *, bootstrap_principal, operation_principal, now, deadline):
    closed(value, "profile configuration bootstrap operation")
    require(value["profile"] == PROFILE, ERROR)
    config = value["configuration"]
    _configuration(config)
    require(selection_digest(selection_document(config)) == context.selection_digest, ERROR)
    closed(value["bootstrap"], " ".join(BootstrapReadback.__dataclass_fields__))
    closed(value["operation"], " ".join(OperationReadback.__dataclass_fields__))
    b, o = BootstrapReadback(**value["bootstrap"]), OperationReadback(**value["operation"])
    c, now = context, now
    require(integer(now) and integer(deadline) and now < deadline, ERROR)
    for record in (b, o):
        require(integer(record.observed_at) and integer(record.expires_at)
        and record.observed_at <= now < record.expires_at <= record.observed_at + 60, ERROR)
    require(b.principal_ref == bootstrap_principal and o.principal_ref == operation_principal
            and b.preauthorization_ref == c.preauthorization_ref and b.selection_digest == c.selection_digest
            and b.accepted_commit == o.accepted_commit == c.accepted_commit
            and b.repository_id == c.repository_id and b.case_ref == o.case_ref == config["case_ref"]
            and b.run_id == o.run_id == config["launch"]["run_id"] == c.run_id
            and b.run_attempt == o.run_attempt == config["launch"]["run_attempt"] == c.run_attempt
            and b.config_digest == o.config_digest == digest(config)
            and b.operation_grant_ref == o.grant_ref and o.action == "qualify-existing-resources"
            and bootstrap_principal != config["services"]["worker_channel"]["principal_ref"]
            and operation_principal != config["services"]["worker_channel"]["principal_ref"], ERROR)
    for ref in (b.case_ref, b.operation_grant_ref, bootstrap_principal, operation_principal):
        _handle(ref)
    require(len(canonical(config)) <= 16384, ERROR)
    return value

class ReadinessClient:
    """One independently selected HTTPS controller route per trusted phase.

    The request endpoint/CA and token request capability belong to orchestration
    hosting. No resolver or credential material is exposed to the worker.
    """
    def __init__(self, *, endpoint, token_client, clock, transport=None):
        from urllib.parse import urlsplit
        parsed = urlsplit(endpoint)
        require(parsed.scheme == "https" and parsed.hostname and parsed.username is None
                and parsed.password is None and not parsed.query and not parsed.fragment, ERROR)
        self.endpoint, self.token_client, self.clock = endpoint, token_client, clock
        self.transport = transport if transport is not None else Https()

    def read(self, context, *, environment, deadline):
        try:
            decision = Decision(clock=self.clock, deadline=deadline)
            token = self.token_client.acquire(environment, decision=decision)
            raw = canonical({"profile": PROFILE, "context": asdict(context), "token": token})
            response = self.transport.exchange("POST", self.endpoint,
                headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
                body=raw, decision=decision)
            decision.now()
            require(type(response) is Response and response.status == 200, ERROR)
            value = document(response.body)
            require(type(value) is dict, ERROR)
            return value
        except Exception:
            raise BindingError(ERROR) from None

class ControllerEndpoint:
    """Internal handler for separately selected bounded HTTPS hosting, no listener.

    Phase is intrinsic to the controller instance; no body flag selects it.
    Materialization is an independently approved configuration/operation capability,
    not a token-authorized grant issuer. Hosting must authenticate every connector.
    """
    def __init__(self, *, controller, materialize, clock, bootstrap_principal, operation_principal):
        self.controller, self.materialize, self.clock = controller, materialize, clock
        self.bootstrap_principal, self.operation_principal = bootstrap_principal, operation_principal

    def handle(self, raw, *, deadline):
        try:
            from ..bootstrap import DispatchContext
            value = document(raw)
            closed(value, "profile context token")
            require(value["profile"] == PROFILE and type(value["context"]) is dict, ERROR)
            context = DispatchContext(**value["context"])
            validate_dispatch_context(context)
            decision = Decision(clock=self.clock, deadline=deadline)
            correlated = self.controller.correlate(context.preauthorization_ref, value["token"], context, decision=decision)
            before = decision.now()
            response = self.materialize(correlated, deadline=decision.deadline)
            decision.now()
            raw = canonical(response)
            require(len(raw) <= 65536, ERROR)
            response = document(raw)
            validate_response(response, context, bootstrap_principal=self.bootstrap_principal,
                operation_principal=self.operation_principal, now=decision.now(), deadline=decision.deadline)
            require(all(response[name]["observed_at"] >= before for name in ("bootstrap", "operation")), ERROR)
            # Materialization can block; repeat current authentication/authority after it.
            current = self.controller.recheck(correlated, decision=decision)
            for name in ("bootstrap", "operation"):
                response[name]["expires_at"] = min(response[name]["expires_at"], current.valid_until)
            return canonical(response)
        except Exception:
            raise BindingError(ERROR) from None

class Session:
    def __init__(self, client, *, context, environment, deadline,
                 bootstrap_principal, operation_principal):
        validate_dispatch_context(context)
        self.client, self.context, self.environment = client, context, environment
        self.bootstrap_principal, self.operation_principal = bootstrap_principal, operation_principal
        self.deadline = deadline
        self.value = self._read(deadline)
        self.raw = canonical(self.value["configuration"])

    def _read(self, deadline):
        try:
            require(integer(deadline), ERROR)
            deadline = min(deadline, self.deadline)
            value = self.client.read(self.context, environment=self.environment, deadline=deadline)
            validate_response(value, self.context, bootstrap_principal=self.bootstrap_principal,
                operation_principal=self.operation_principal, now=self.client.clock(), deadline=deadline)
            if hasattr(self, "value"):
                require(value["configuration"] == self.value["configuration"]
                        and value["bootstrap"]["operation_grant_ref"] == self.value["bootstrap"]["operation_grant_ref"], ERROR)
            self.deadline = min(self.deadline, deadline, value["bootstrap"]["expires_at"], value["operation"]["expires_at"])
            return value
        except Exception:
            raise BindingError(ERROR) from None

    def bindings(self, workflow):
        require(type(workflow) is WorkflowBindings, ERROR)
        def read_bootstrap(ref, context, *, deadline):
            require(ref == self.context.preauthorization_ref and context == self.context, ERROR)
            return BootstrapReadback(**self._read(deadline)["bootstrap"])
        def read_authorization(ref, *, deadline):
            result = OperationReadback(**self._read(deadline)["operation"])
            require(ref == result.grant_ref, ERROR)
            return result
        trust = replace(workflow.runtime_trust, approved_config_digest=digest(self.value["configuration"]))
        workflow = replace(workflow, runtime_trust=trust, load_config=lambda: self.raw,
            authorization_principal_ref=self.operation_principal, read_authorization=read_authorization)
        return BootstrapBindings(self.context.selection_digest, self.bootstrap_principal, read_bootstrap, workflow)
