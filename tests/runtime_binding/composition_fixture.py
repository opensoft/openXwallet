"""Synthetic trusted embedding; no deployed authentication or isolation claim."""
from copy import deepcopy
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import digest
from workload_factory_binding_runtime.config import RuntimeTrust
from workload_factory_binding_runtime.loaders import BoundService, ServiceIdentity
from workload_factory_binding_runtime.runtime import RuntimeBridge, StateBinding, WorkerContext
from .test_config import configuration, encoded, trust_for


class Reader:
    def __init__(self, operation, reference, value):
        self.operation, self.reference, self.value = operation, reference, value
        self.calls, self.hook = [], None

    def read(self, operation, reference, *, deadline):
        self.calls.append((operation, reference, deadline))
        if self.hook:
            self.hook()
        if (operation, reference) != (self.operation, self.reference):
            raise OSError("fixture unknown record")
        return self.value if type(self.value) is bytes else encoded(self.value)


@pytest.fixture
def c(r, configuration):
    h, config = r.h, configuration
    config.update(not_before=h.now - 1, expires_at=h.now + 120,
                  composition_digest=h.policy["composition_digest"], launch=deepcopy(r.expected))
    config["sources"]["worker"].update(repository=r.expected["repository"], commit=r.expected["sha"])
    for role, claim, sha in (("caller_workflow", "workflow_ref", "workflow_sha"),
                             ("reusable_workflow", "job_workflow_ref", "job_workflow_sha")):
        workflow = r.expected[claim].split("@")[0].split("/")
        config["sources"][role].update(repository="/".join(workflow[:2]),
                                        path="/".join(workflow[2:]), commit=r.expected[sha])
    config["protection"].update(repository_id=r.expected["repository_id"], environment=r.expected["environment"])
    config["authority"] = {"policy_ref": h.policy["policy_ref"], "policy_revision": h.policy["revision"],
                           "policy_digest": digest(h.policy), "grant_ref": h.policy["grant_ref"],
                           **{name: h.policy["binding"][name] for name in
                              ("subject_ref", "wallet_ref", "key_ref", "custody_ref")}}
    config["services"]["challenge"]["service_ref"] = h.challenge.issuer
    _, readback = trust_for(config)
    readback.update(observed_at=h.now - 1, expires_at=h.now + 30)
    result = SimpleNamespace(r=r, h=h, config=config, readback=readback)
    result.trust = RuntimeTrust(digest(config), "principal:operator", lambda: encoded(result.readback), lambda: h.now)
    result.context = WorkerContext(ServiceIdentity(**config["services"]["worker_channel"]), digest(config),
                                   config["case_ref"], r.expected["run_id"], r.expected["run_attempt"],
                                   h.now - 1, h.now + 30)
    result.records = Reader("policy", h.policy["policy_ref"], deepcopy(h.policy))
    result.challenge = Reader("challenge", h.challenge.id, asdict(h.challenge))
    targets = {"records": result.records, "challenge": result.challenge, "registry": h, "custody": h}
    result.services = {role: BoundService(ServiceIdentity(**config["services"][role]), target)
                       for role, target in targets.items()}
    result.state = StateBinding(**config["state"], ledger=h.ledger)

    def make(**overrides):
        arguments = dict(load_config=lambda: encoded(result.config), trust=result.trust,
                         load_worker_context=lambda: result.context, services=result.services,
                         state=result.state, issuer_source=r.source, create_proof=h.unit_proof)
        arguments.update(overrides)
        return RuntimeBridge(**arguments)
    result.make = make
    result.bridge = make()
    result.run = lambda: result.bridge.sign(h.challenge.id, h.request, h.token, h.observation)

    def reselect_policy():
        # Explicitly approve a different synthetic baseline before a new use.
        result.config["authority"]["policy_digest"] = digest(h.policy)
        result.records.value = deepcopy(h.policy)
        result.challenge.value = asdict(h.challenge)
        _, observed = trust_for(result.config)
        observed.update(observed_at=h.now - 1, expires_at=h.now + 30)
        result.readback = observed
        result.trust = replace(result.trust, approved_config_digest=digest(result.config))
        result.context = replace(result.context, config_digest=digest(result.config))
        result.bridge = make()
    result.reselect_policy = reselect_policy
    return result
