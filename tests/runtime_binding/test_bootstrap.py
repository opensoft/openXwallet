"""Offline bootstrap into real admission; no GitHub dispatch or provider client."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
import json
import threading
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import BindingError, digest
from workload_factory_binding_runtime.bootstrap import (
    PROFILE, BootstrapBindings, BootstrapReadback, DispatchContext, bootstrap,
    selection_digest, selection_document,
)
from workload_factory_binding_runtime.config import validate_config
from .composition_fixture import c
from .test_config import configuration, encoded, trust_for
from .test_lifecycle import l
from .test_workflow import SHA, w


@pytest.fixture
def b(w):
    # This commitment can be prepared without actual GitHub run fields.
    document = selection_document(w.c.config)
    commitment = selection_digest(document)
    context = DispatchContext(**{name: getattr(w.context, name) for name in (
        "repository", "repository_id", "event_name", "ref", "sha", "workflow_ref",
        "workflow_sha", "run_id", "run_attempt", "accepted_commit", "source_commit")},
        selection_digest=commitment, preauthorization_ref="preauthorization:fixture")
    bound = BootstrapReadback("principal:bootstrap", context.preauthorization_ref,
        commitment, SHA, context.repository_id, w.c.config["case_ref"], context.run_id,
        context.run_attempt, digest(w.c.config), w.context.operation_grant_ref,
        w.c.h.now, w.c.h.now + 10)
    result = SimpleNamespace(w=w, context=context, bound=bound, document=document,
                             calls=[], hook=None)
    def read(ref, observed, *, deadline):
        result.calls.append((ref, observed, deadline))
        if result.hook:result.hook()
        return result.bound
    result.bindings = BootstrapBindings(commitment, bound.principal_ref, read, w.bindings)
    return result


def test_predispatch_commitment_needs_no_run_and_admits_assigned_run(b):
    static = json.loads(b.document)
    assert static["profile"] == PROFILE
    assert "run_id" not in static["configuration"]["launch"]
    assert "run_attempt" not in static["configuration"]["launch"]
    admitted = bootstrap(b.context, bindings=b.bindings)
    assert admitted.config_digest == b.bound.config_digest != b.context.selection_digest
    assert admitted.run_id == b.context.run_id
    assert admitted.run_attempt == b.context.run_attempt
    assert admitted.valid_until == b.bound.expires_at
    assert [role for role, _, _ in b.w.calls] == ["environment", "authorization", "scheduler"]
    assert all(deadline <= b.bound.expires_at for _, _, deadline in b.w.calls)
    assert b.w.c.h.calls == 0  # admission never reaches custody


@pytest.mark.parametrize("field,value", [("run_id", "790"), ("run_attempt", "2")])
def test_only_assigned_run_fields_are_absent_from_static_commitment(b, field, value):
    changed = deepcopy(b.w.c.config)
    changed["launch"][field] = value
    assert selection_digest(selection_document(changed)) == b.context.selection_digest
    assert digest(changed) != b.bound.config_digest
    with pytest.raises(BindingError):
        bootstrap(replace(b.context, **{field: value}), bindings=b.bindings)


@pytest.mark.parametrize("group", ["profile", "revision", "not_before", "expires_at", "case_ref", "sources",
    "dependency_digest", "composition_digest", "issuer", "launch", "protection", "authority",
    "services", "state", "lifecycle"])
def test_static_document_requires_every_configuration_group(b, group):
    selected = json.loads(b.document)
    del selected["configuration"][group]
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        selection_digest(encoded(selected))


@pytest.mark.parametrize("change", ["run_id", "run_attempt", "wrapper", "profile", "extra", "pending", "oversize", "duplicate"])
def test_static_document_is_closed_bounded_and_not_runtime_input(b, change):
    selected = json.loads(b.document)
    if change in ("run_id", "run_attempt"):selected["configuration"]["launch"][change] = "1"
    elif change == "wrapper":selected["extra"] = True
    elif change == "profile":selected["profile"] = "other"
    elif change == "extra":selected["configuration"]["extra"] = True
    elif change == "pending":selected["configuration"]["case_ref"] = "case:pending"
    raw = encoded(selected)
    if change == "oversize":raw += b" " * 16384
    if change == "duplicate":raw = raw.replace(b'"profile":', b'"profile":"other","profile":', 1)
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        selection_digest(raw)


@pytest.mark.parametrize("field", ["run_id", "run_attempt"])
def test_static_validation_cannot_weaken_full_runtime_validation(b, field):
    changed = deepcopy(b.w.c.config)
    del changed["launch"][field]
    raw = encoded(changed)
    trust = trust_for(b.w.c.config)[0]
    with pytest.raises(BindingError, match="^invalid-runtime-config$"):
        validate_config(raw, trust=trust)


@pytest.mark.parametrize("field,value", [("repository", "attacker/fork"), ("event_name", "pull_request_target"),
    ("ref", "refs/heads/other"), ("sha", "c" * 40), ("source_commit", "c" * 40),
    ("run_id", "0"), ("run_attempt", "1\u0661"), ("selection_digest", "secret-canary"),
    ("preauthorization_ref", "grant:pending"), ("preauthorization_ref", "bad\nready=true")])
def test_invalid_dispatch_refuses_before_any_authenticated_reader(b, field, value):
    with pytest.raises(BindingError, match="^workflow-context-mismatch$"):
        bootstrap(replace(b.context, **{field: value}), bindings=b.bindings)
    assert b.calls == b.w.calls == []


def test_dispatch_hash_does_not_approve_itself(b):
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        bootstrap(replace(b.context, selection_digest="sha256:" + "f" * 64), bindings=b.bindings)
    assert b.calls == b.w.calls == []


def test_bootstrap_selected_source_must_match_before_reader(b):
    bindings = replace(b.bindings, workflow=replace(b.bindings.workflow, accepted_commit="c" * 40))
    with pytest.raises(BindingError):bootstrap(b.context, bindings=bindings)
    assert b.calls == b.w.calls == []


@pytest.mark.parametrize("value", [None, {"approved": True}])
def test_worker_objects_cannot_supply_bootstrap_bindings(b, value):
    with pytest.raises(BindingError):bootstrap(b.context, bindings=value)
    assert b.calls == b.w.calls == []


@pytest.mark.parametrize("field,value", [("principal_ref", "principal:other"),
    ("preauthorization_ref", "preauthorization:other"), ("selection_digest", "sha256:" + "f" * 64),
    ("accepted_commit", "c" * 40), ("repository_id", "999"), ("case_ref", "case:other"),
    ("run_id", "999"), ("run_attempt", "2"), ("config_digest", "sha256:" + "f" * 64),
    ("operation_grant_ref", "grant:other"), ("operation_grant_ref", "../grant")])
def test_bootstrap_substitution_never_returns_readiness(b, field, value):
    b.bound = replace(b.bound, **{field: value})
    with pytest.raises(BindingError):bootstrap(b.context, bindings=b.bindings)


@pytest.mark.parametrize("change", ["future", "expired", "too-long", "absent", "dictionary", "outage", "regression", "slow"])
def test_bootstrap_readback_is_current_typed_bounded_and_safe(b, change):
    if change == "future":b.bound = replace(b.bound, observed_at=b.w.c.h.now + 1)
    elif change == "expired":b.bound = replace(b.bound, expires_at=b.w.c.h.now)
    elif change == "too-long":b.bound = replace(b.bound, expires_at=b.w.c.h.now + 61)
    elif change == "absent":b.bound = None
    elif change == "dictionary":b.bound = {"approved": True, "private": "sensitive-canary"}
    elif change == "outage":
        def fail():raise OSError("sensitive-canary")
        b.hook = fail
    else:
        def move():b.w.c.h.now += -1 if change == "regression" else 61
        b.hook = move
    with pytest.raises(BindingError) as caught:bootstrap(b.context, bindings=b.bindings)
    assert "sensitive-canary" not in str(caught.value)
    assert b.w.calls == []


@pytest.mark.parametrize("role", ["environment", "authorization", "scheduler"])
def test_bootstrap_expiry_during_existing_admission_cannot_extend_readiness(b, role):
    def expire():b.w.c.h.now += 11
    b.w.hooks[role] = expire
    with pytest.raises(BindingError):bootstrap(b.context, bindings=b.bindings)


@pytest.mark.parametrize("group", ["case_ref", "issuer", "protection", "sources", "services", "state", "lifecycle",
                                   "authority", "dependency_digest", "composition_digest", "expires_at"])
def test_independently_reapproved_runtime_cannot_substitute_a_static_selection(b, group):
    config = b.w.c.config
    if group in ("dependency_digest", "composition_digest"):config[group] = "sha256:" + "f" * 64
    elif group == "case_ref":config[group] = "case:other"
    elif group == "issuer":config[group]["audience"] = "factory:other"
    elif group == "protection":config[group]["environment_id"] = "999"
    elif group == "sources":config[group]["supervisor"]["commit"] = "c" * 40
    elif group == "services":config[group]["registry"]["principal_ref"] = "principal:other"
    elif group == "state":config[group]["store_ref"] = "store:other"
    elif group == "lifecycle":config[group]["lease_ref"] = "lease:other"
    elif group == "authority":config[group]["wallet_ref"] = "wallet:other"
    else:config[group] += 1
    b.w.c.reselect_policy()
    runtime = replace(b.w.bindings, runtime_trust=b.w.c.trust)
    b.bindings = replace(b.bindings, workflow=runtime)
    b.bound = replace(b.bound, config_digest=digest(config), case_ref=config["case_ref"])
    with pytest.raises(BindingError):bootstrap(b.context, bindings=b.bindings)
    assert b.w.calls == []


def test_worker_principal_cannot_supply_bootstrap(b):
    worker = b.w.c.config["services"]["worker_channel"]["principal_ref"]
    b.bindings = replace(b.bindings, principal_ref=worker)
    b.bound = replace(b.bound, principal_ref=worker)
    with pytest.raises(BindingError):bootstrap(b.context, bindings=b.bindings)
    assert b.w.calls == []


def test_repeated_after_environment_approval_requires_fresh_authority(b):
    bootstrap(b.context, bindings=b.bindings)
    b.bound = None  # authority revoked between jobs
    with pytest.raises(BindingError):bootstrap(b.context, bindings=b.bindings)
    assert len(b.calls) == 2


def test_independent_reference_authority_atomically_binds_one_concurrent_run(b):
    # Synthetic authority models the required hosting contract. Atomic issuance
    # is deliberately outside the worker/adapter; this is not a deployed service.
    lock, selected = threading.Lock(), []
    def read(ref, context, *, deadline):
        with lock:
            identity = (context.run_id, context.run_attempt)
            if selected and selected[0] != identity:raise OSError("preauthorization consumed")
            if not selected:selected.append(identity)
            return replace(b.bound, run_id=context.run_id, run_attempt=context.run_attempt)
    contexts = [replace(b.context, run_id=str(1000 + i)) for i in range(8)]
    def claim(context):
        try:return read(context.preauthorization_ref, context, deadline=b.w.c.h.now + 10)
        except OSError:return None
    with ThreadPoolExecutor(max_workers=8) as pool:results = list(pool.map(claim, contexts))
    winners = [r for r in results if r is not None]
    assert len(winners) == 1
    winner = next(c for c in contexts if c.run_id == winners[0].run_id)
    assert read(winner.preauthorization_ref, winner, deadline=b.w.c.h.now + 10) == winners[0]
    with pytest.raises(OSError):read(winner.preauthorization_ref, replace(winner, run_attempt="2"), deadline=1)
