"""Prepared manual/reusable workflow admission; no dispatch or provider setup."""
from copy import deepcopy
from dataclasses import replace
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

from workload_factory_binding.evidence import BindingError, digest
from workload_factory_binding_runtime.workflow import (
    CALLER, REF, REPOSITORY, REUSABLE, EnvironmentReadback, OperationReadback,
    SchedulerReadback, WorkflowBindings, WorkflowContext, admit, operational_bindings, validate_context,
)
from .composition_fixture import c
from .test_config import configuration, encoded
from .test_lifecycle import l

ROOT = Path(__file__).resolve().parents[2]
SHA = "b" * 40


@pytest.fixture
def w(c, request):
    config = c.config
    config["launch"].update(repository=REPOSITORY, repository_owner="opensoft", ref=REF, sha=SHA,
                            workflow_ref=REPOSITORY + "/" + CALLER + "@" + REF, workflow_sha=SHA,
                            job_workflow_ref=REPOSITORY + "/" + REUSABLE + "@" + REF, job_workflow_sha=SHA)
    for role in ("worker", "adapter", "caller_workflow", "reusable_workflow"):
        config["sources"][role].update(repository=REPOSITORY, commit=SHA)
    config["sources"]["caller_workflow"]["path"] = CALLER
    config["sources"]["reusable_workflow"]["path"] = REUSABLE
    c.reselect_policy()
    lease_fixture = request.getfixturevalue("l")
    life = lease_fixture.life
    launch = config["launch"]
    context = WorkflowContext(REPOSITORY, launch["repository_id"], "workflow_dispatch", REF, SHA,
                              launch["workflow_ref"], SHA, launch["run_id"], launch["run_attempt"],
                              SHA, digest(config), "grant:operation", SHA)
    b = SimpleNamespace(c=c, life=life, lease_fixture=lease_fixture, context=context, calls=[], hooks={})
    b.environment = EnvironmentReadback("principal:environment-reader", True, deepcopy(config["protection"]),
                                         c.h.now, c.h.now + 20)
    b.authorization = OperationReadback("principal:operation-reader", context.operation_grant_ref,
                                        "qualify-existing-resources", digest(config), SHA, config["case_ref"],
                                        context.run_id, context.run_attempt, c.h.now, c.h.now + 20)
    b.scheduler = SchedulerReadback("principal:scheduler", config["lifecycle"]["cleanup_ref"], life.plan.digest,
                                    life.readback.identity.principal_ref, c.h.now, c.h.now + 20)
    def reader(role):
        def read(ref, *, deadline):
            b.calls.append((role, ref, deadline))
            if role in b.hooks:b.hooks[role]()
            return getattr(b, role)
        return read
    b.bindings = WorkflowBindings(SHA, lambda: encoded(c.config), c.trust,
                                  b.environment.principal_ref, reader("environment"),
                                  b.authorization.principal_ref, reader("authorization"),
                                  b.scheduler.principal_ref, reader("scheduler"), life)
    return b


def test_independent_readiness_binds_existing_environment_grant_and_scheduler(w):
    result = admit(w.context, bindings=w.bindings)
    assert result.environment == w.c.config["launch"]["environment"]
    assert result.source_commit == SHA
    assert result.config_digest == w.context.config_digest
    assert result.run_id == w.context.run_id
    assert result.run_attempt == w.context.run_attempt
    assert result.valid_until == w.c.h.now + 20
    assert [role for role, _, _ in w.calls] == ["environment", "authorization", "scheduler"]
    assert all(deadline <= w.c.h.now + 30 for _, _, deadline in w.calls)


@pytest.mark.parametrize("field,value", [("repository", "attacker/fork"), ("repository_id", "0"),
    ("event_name", "pull_request_target"), ("ref", "refs/heads/unreviewed"), ("sha", "c" * 40),
    ("workflow_ref", REPOSITORY + "/other.yml@" + REF), ("workflow_sha", "c" * 40),
    ("run_id", "0"), ("run_id", "1\u0661"), ("run_attempt", "0"), ("accepted_commit", "main"),
    ("source_commit", "c" * 40), ("config_digest", "raw-sensitive-canary"),
    ("operation_grant_ref", "bad\nready=true")])
def test_wrong_dispatch_source_identity_or_injected_output_refuses_before_readback(w, field, value):
    context = replace(w.context, **{field: value})
    with pytest.raises(BindingError, match="^workflow-context-mismatch$"):
        admit(context, bindings=w.bindings)
    assert w.calls == []


def test_dispatch_source_input_cannot_approve_itself(w):
    bindings = replace(w.bindings, accepted_commit="c" * 40)
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=bindings)
    assert w.calls == []


def test_dispatch_digest_must_match_independently_approved_runtime_selection(w):
    context = replace(w.context, config_digest="sha256:" + "f" * 64)
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(context, bindings=w.bindings)
    assert w.calls == []


@pytest.mark.parametrize("field", ["prevent_self_review", "can_admins_bypass", "reviewer_ids",
                                  "deployment_refs", "repository_id", "environment_id", "environment"])
def test_each_actual_protection_setting_must_match_approved_projection(w, field):
    changed = deepcopy(w.environment.protection)
    changed[field] = None
    w.environment = replace(w.environment, protection=changed)
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=w.bindings)
    assert [role for role, _, _ in w.calls] == ["environment"]


@pytest.mark.parametrize("exists", [False, "true", None])
def test_absent_or_unverified_environment_cannot_queue_environment_bound_job(w, exists):
    w.environment = replace(w.environment, exists=exists)
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=w.bindings)


@pytest.mark.parametrize("field,value", [("principal_ref", "principal:other"), ("grant_ref", "grant:other"),
    ("action", "setup-resources"), ("config_digest", "sha256:" + "f" * 64), ("accepted_commit", "c" * 40),
    ("case_ref", "case:other"), ("run_id", "999"), ("run_attempt", "2")])
def test_source_acceptance_is_not_case_bound_operational_authorization(w, field, value):
    w.authorization = replace(w.authorization, **{field: value})
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=w.bindings)
    assert [role for role, _, _ in w.calls] == ["environment", "authorization"]


@pytest.mark.parametrize("field", ["principal_ref", "cleanup_ref", "plan_digest", "readback_principal_ref"])
def test_missing_or_wrong_independent_scheduler_readback_cannot_qualify_readiness(w, field):
    w.scheduler = replace(w.scheduler, **{field: "ref:other"})
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=w.bindings)


@pytest.mark.parametrize("role", ["environment", "authorization", "scheduler"])
@pytest.mark.parametrize("change", ["future", "expired", "too-long", "dictionary", "absent"])
def test_every_external_readback_has_a_fresh_bounded_typed_snapshot(w, role, change):
    record = getattr(w, role)
    if change == "future":record = replace(record, observed_at=w.c.h.now + 1)
    elif change == "expired":record = replace(record, expires_at=w.c.h.now)
    elif change == "too-long":record = replace(record, expires_at=w.c.h.now + 61)
    elif change == "dictionary":record = {"approved": True, "private": "secret-canary"}
    else:record = None
    setattr(w, role, record)
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=w.bindings)


@pytest.mark.parametrize("role", ["environment", "authorization", "scheduler"])
def test_readback_outage_is_fixed_and_cannot_supply_readiness(w, role):
    def fail():raise OSError("sensitive-provider-canary")
    w.hooks[role] = fail
    with pytest.raises(BindingError, match="^workflow-input-unavailable$") as caught:
        admit(w.context, bindings=w.bindings)
    assert "sensitive-provider-canary" not in str(caught.value)


@pytest.mark.parametrize("role", ["environment", "authorization", "scheduler"])
def test_expiry_during_each_readback_never_extends_admission(w, role):
    def expire():w.c.h.now += 31
    w.hooks[role] = expire
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=w.bindings)


@pytest.mark.parametrize("field", ["environment_principal_ref", "authorization_principal_ref", "scheduler_principal_ref"])
def test_worker_identity_cannot_supply_trusted_readback(w, field):
    worker = w.c.config["services"]["worker_channel"]["principal_ref"]
    bindings = replace(w.bindings, **{field: worker})
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=bindings)
    assert w.calls == []


def test_current_lease_revocation_is_checked_before_admission_returns(w):
    w.lease_fixture.status = "revoked"
    with pytest.raises(BindingError):
        admit(w.context, bindings=w.bindings)


def test_production_host_is_unselected_and_has_no_environment_activation_switch(monkeypatch):
    monkeypatch.setenv("OPENXWALLET_APPROVED", "true")
    monkeypatch.setenv("OPENXWALLET_HOST_PLUGIN", "attacker.module")
    with pytest.raises(BindingError, match="^workflow-operational-host-unselected$"):
        operational_bindings()


@pytest.mark.parametrize("phase", ["preflight", "qualify", "cleanup"])
@pytest.mark.parametrize("input_mode", ["static", "legacy"])
def test_actual_cli_blocks_before_outputs_oidc_or_live_operations(tmp_path, phase, input_mode):
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()
    output = tmp_path / "github-output"
    environment = dict(os.environ, GITHUB_REPOSITORY=REPOSITORY, GITHUB_REPOSITORY_ID="123",
        GITHUB_EVENT_NAME="workflow_dispatch", GITHUB_REF=REF, GITHUB_SHA=head,
        GITHUB_WORKFLOW_REF=REPOSITORY + "/" + CALLER + "@" + REF, GITHUB_WORKFLOW_SHA=head,
        GITHUB_RUN_ID="789", GITHUB_RUN_ATTEMPT="1", OPENXWALLET_ACCEPTED_COMMIT=head,
        OPENXWALLET_SELECTION_DIGEST="sha256:" + "a" * 64, OPENXWALLET_PREAUTHORIZATION_REF="grant:secret-canary",
        GITHUB_OUTPUT=str(output), ACTIONS_ID_TOKEN_REQUEST_TOKEN="private-token-canary",
        ACTIONS_ID_TOKEN_REQUEST_URL="https://invalid.example/private-canary")
    if input_mode == "legacy":
        environment.pop("OPENXWALLET_SELECTION_DIGEST")
        environment.pop("OPENXWALLET_PREAUTHORIZATION_REF")
        environment.update(OPENXWALLET_CONFIG_DIGEST="sha256:" + "a" * 64,
                           OPENXWALLET_OPERATION_GRANT_REF="grant:secret-canary")
    result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "scripts/prepare-protected-runtime.py"),
                             "--phase", phase], cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=15)
    assert result.returncode == 2
    assert result.stdout == ""
    expected = "workflow-operational-host-unselected" if input_mode == "static" else "workflow-context-mismatch"
    assert result.stderr.strip() == expected
    assert not output.exists()


def load_workflow(path):
    return yaml.load((ROOT / path).read_text(), Loader=yaml.BaseLoader)


def test_workflow_has_manual_caller_and_same_commit_local_reusable_claim_binding():
    caller, reusable = load_workflow(CALLER), load_workflow(REUSABLE)
    assert set(caller["on"]) == {"workflow_dispatch"}
    assert set(reusable["on"]) == {"workflow_call"}
    assert caller["permissions"] == {}
    assert reusable["permissions"] == {}
    invoke = caller["jobs"]["invoke"]
    assert invoke["uses"] == "./" + REUSABLE
    assert invoke["permissions"] == {"contents": "read", "id-token": "write"}
    assert "secrets" not in invoke
    assert caller["concurrency"]["cancel-in-progress"] == "false"
    names = {"accepted_commit", "selection_digest", "preauthorization_ref"}
    assert set(caller["on"]["workflow_dispatch"]["inputs"]) == names
    assert set(reusable["on"]["workflow_call"]["inputs"]) == names
    assert invoke["with"] == {name: "${{ inputs." + name + " }}" for name in names}
    assert reusable["env"] == {
        "OPENXWALLET_ACCEPTED_COMMIT": "${{ inputs.accepted_commit }}",
        "OPENXWALLET_SELECTION_DIGEST": "${{ inputs.selection_digest }}",
        "OPENXWALLET_PREAUTHORIZATION_REF": "${{ inputs.preauthorization_ref }}"}


def test_environment_follows_admission_and_oidc_is_job_scoped():
    jobs = load_workflow(REUSABLE)["jobs"]
    assert set(jobs) == {"admission", "protected-qualification"}
    before, protected = jobs["admission"], jobs["protected-qualification"]
    assert before["if"] == "${{ github.repository == 'opensoft/openXwallet' && github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' && github.workflow_ref == 'opensoft/openXwallet/.github/workflows/protected-runtime-qualification.yml@refs/heads/main' }}"
    assert before["permissions"] == {"contents": "read", "id-token": "write"}
    assert "environment" not in before
    assert before["outputs"]["ready"] == "${{ steps.admit.outputs.ready }}"
    assert protected["needs"] == "admission"
    assert protected["if"] == "${{ needs.admission.result == 'success' && needs.admission.outputs.ready == 'true' }}"
    assert protected["environment"]["name"] == "${{ needs.admission.outputs.environment }}"
    assert protected["permissions"] == {"contents": "read", "id-token": "write"}


def test_checkout_action_dependencies_and_workflow_inputs_never_float_or_execute_as_shell():
    workflow = load_workflow(REUSABLE)
    for job in workflow["jobs"].values():
        assert int(job["timeout-minutes"]) <= 15
        for step in job["steps"]:
            if "uses" in step:
                assert re.fullmatch(r"actions/(checkout|setup-python)@[0-9a-f]{40}", step["uses"])
            if step.get("uses", "").startswith("actions/checkout@"):
                assert step["with"]["ref"] == "${{ github.workflow_sha }}"
                assert step["with"]["persist-credentials"] == "false"
                assert step["with"]["submodules"] == "false"
            if "run" in step:
                assert "${{" not in step["run"]
                assert "--require-hashes" in step["run"] or "scripts/prepare-protected-runtime.py" in step["run"]


def test_protected_job_rechecks_after_approval_and_has_independent_cleanup_handoff():
    steps = load_workflow(REUSABLE)["jobs"]["protected-qualification"]["steps"]
    commands = [s for s in steps if "scripts/prepare-protected-runtime.py" in s.get("run", "")]
    assert [s["run"].split()[-1] for s in commands] == ["protected-admission", "qualify", "cleanup"]
    assert commands[-1]["if"] == "${{ always() }}"
    assert all("upload-artifact" not in s.get("uses", "") for s in steps)


@pytest.mark.parametrize("ref", ["https://invalid.example/grant", "../grant", "grant:pending", "grant:latest"])
def test_operation_reference_is_an_opaque_selected_handle_not_a_resolver(w, ref):
    context = replace(w.context, operation_grant_ref=ref)
    with pytest.raises(BindingError, match="^workflow-context-mismatch$"):
        validate_context(context)


def test_scheduler_cannot_rotate_the_bound_plan_during_admission(w):
    old = w.life.plan
    def rotate():w.life.plan = replace(old, ref="plan:other")
    w.hooks["scheduler"] = rotate
    with pytest.raises(BindingError):
        admit(w.context, bindings=w.bindings)


@pytest.mark.parametrize("role", ["environment", "authorization", "scheduler"])
def test_clock_regression_during_each_readback_refuses(w, role):
    def regress():w.c.h.now -= 1
    w.hooks[role] = regress
    with pytest.raises(BindingError, match="^workflow-admission-refused$"):
        admit(w.context, bindings=w.bindings)
