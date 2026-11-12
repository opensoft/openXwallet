"""Per-use trusted preflight composition; no deployed acceptance claim."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace

import pytest

from workload_factory_binding.evidence import BindingError
from workload_factory_binding.evidence import observe_artifacts
from factory_binding.conftest import timestamp
from .composition_fixture import c, configuration


def test_replay_is_consumed_by_unchanged_gate(c):
    c.run()
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 1


@pytest.mark.parametrize("context", [True, False, {"authenticated": True}, None])
def test_worker_boolean_or_dictionary_is_not_authentication(c, context):
    c.context = context
    with pytest.raises(BindingError):
        c.run()
    assert c.r.transport.calls == []
    assert c.records.calls == []
    assert c.h.calls == 0


@pytest.mark.parametrize("field,value", [("config_digest", "sha256:" + "f" * 64),
    ("case_ref", "case:other"), ("run_id", "999"), ("run_attempt", "2"),
    ("issued_at", 9999999999), ("expires_at", 0)])
def test_hosting_context_must_bind_exact_approved_launch(c, field, value):
    c.context = replace(c.context, **{field: value})
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 0
    assert c.records.calls == []


@pytest.mark.parametrize("claim", ["repository", "repository_id", "repository_owner", "repository_owner_id",
    "environment", "sub", "ref", "sha", "workflow_ref", "workflow_sha", "job_workflow_ref",
    "job_workflow_sha", "run_id", "run_attempt"])
def test_wrong_workload_token_refuses_before_record_or_challenge_access(c, claim):
    c.h.claims[claim] = "changed"
    c.h.reset_evidence()
    with pytest.raises(BindingError):
        c.run()
    assert c.records.calls == []
    assert c.challenge.calls == []
    assert c.h.calls == 0


@pytest.mark.parametrize("name", ["sources", "protection", "dependency_digest", "composition_digest",
                                   "launch", "services", "state", "lifecycle"])
def test_preflight_drift_during_issuer_io_refuses_before_current_loaders(c, name):
    def change(_url):
        c.readback[name] = None
    c.r.transport.hook = change
    with pytest.raises(BindingError):
        c.run()
    assert c.records.calls == []
    assert c.h.calls == 0


@pytest.mark.parametrize("field", ["store_ref", "initialization_ref", "retention_ref", "recovery_ref"])
def test_selected_state_binding_cannot_be_substituted(c, field):
    state = replace(c.state, **{field: "state:other"})
    c.bridge = c.make(state=state)
    with pytest.raises(BindingError):
        c.run()
    assert c.records.calls == []
    assert c.h.calls == 0


def test_new_readback_cannot_extend_earliest_use_deadline(c):
    def late():
        c.h.now += 30
        c.readback.update(observed_at=c.h.now, expires_at=c.h.now + 30)
        c.context = replace(c.context, issued_at=c.h.now, expires_at=c.h.now + 30)
    c.records.hook = late
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 0


def test_changed_protection_during_signing_returns_no_proof_and_keeps_reservation(c):
    original = deepcopy(c.readback["protection"])
    c.h.on_sign = lambda: c.readback["protection"].update(can_admins_bypass=True)
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 1
    c.readback["protection"] = original
    c.h.on_sign = None
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 1


def test_worker_cannot_add_a_replacement_challenge_or_loader(c):
    c.h.request["challenge"] = {"authenticated": True}
    with pytest.raises(BindingError):
        c.run()
    assert c.records.calls == []
    assert c.h.calls == 0


@pytest.mark.parametrize("deadline", ["observation", "registry", "grant", "issuer"])
def test_expiry_during_post_reservation_preflight_prevents_actual_custody_use(c, deadline):
    if deadline == "observation":
        c.h.observation = observe_artifacts(
            policy=c.h.policy, request=c.h.request, token=c.h.token, challenge=c.h.challenge,
            artifacts=c.h.artifacts, configuration=c.h.configuration, private_key=c.h.supervisor,
            now=c.h.now, expires_at=c.h.now + 5)
    elif deadline == "registry":
        c.h.binding = replace(c.h.binding, expires_at=c.h.now + 5)
    elif deadline == "grant":
        c.h.policy["grants"]["grant:child"]["expires_at"] = timestamp(c.h.now + 5)
        c.h.reset_evidence()
        c.reselect_policy()
    else:
        c.r.transport.headers = {url: (("Cache-Control", "max-age=5"),) for url in c.r.transport.documents}
    phase = {"reserved": False, "checks": 0}
    ledger = c.h.ledger

    class ObservedLedger:
        def reserve(self, **kwargs):
            ledger.reserve(**kwargs)
            phase["reserved"] = True

    c.state = replace(c.state, ledger=ObservedLedger())
    original = c.trust.load_readback
    def readback():
        if phase["reserved"]:
            phase["checks"] += 1
            if phase["checks"] == 2:
                c.h.now += 6
        return original()
    c.bridge = c.make(trust=replace(c.trust, load_readback=readback), state=c.state)
    with pytest.raises(BindingError):
        c.run()
    assert phase["reserved"] is True
    assert c.h.calls == 0


def test_token_expiring_in_post_crypto_preflight_cannot_reach_record_service(c):
    c.h.claims["exp"] = c.h.now + 5
    c.h.reset_evidence()
    phase = {"keys_loaded": False}
    def fetched(_url):
        phase["keys_loaded"] = True
    c.r.transport.hook = fetched
    original = c.trust.load_readback
    def readback():
        if phase["keys_loaded"]:
            phase["keys_loaded"] = False
            c.h.now += 6
        return original()
    c.bridge = c.make(trust=replace(c.trust, load_readback=readback))
    with pytest.raises(BindingError):
        c.run()
    assert c.records.calls == []
    assert c.h.calls == 0


def test_concurrent_uses_keep_independent_scope_and_one_reservation(c):
    def invoke(_number):
        try:
            return c.run()
        except BindingError:
            return None
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(invoke, range(3)))
    assert sum(result is not None for result in results) == 1
    assert c.h.calls == 1


def test_owning_proof_primitive_accepts_composed_result(c):
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    binding = TrustedKeyBinding(**asdict(c.h.binding))
    c.h.binding = binding
    c.bridge = c.make(create_proof=create_proof)
    result = c.run()
    checked = verify_proof(result["proof"], expected_digest=c.h.challenge.digest, binding=binding, now=c.h.now)
    assert checked.subject_ref == c.h.binding.subject_ref
    assert result["human_approval"] is False
    assert c.h.calls == 1
