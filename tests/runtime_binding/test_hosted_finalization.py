"""T012O isolated v2 source controls; provider/admin facts remain fixture-only."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import select
import subprocess
import sys
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import BindingError, CLAIMS, byte_digest, canonical, digest
from workload_factory_binding_runtime.bootstrap import DispatchContext, selection_digest
from workload_factory_binding_runtime.config import validate_config
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.github_bootstrap.identity import BootstrapVerifier, IdentityPolicy, BOOTSTRAP_AUDIENCE
from workload_factory_binding_runtime.hosted import ERROR
from workload_factory_binding_runtime.hosted.plan import PROFILE, DERIVATION, template_digest, validate_plan
from workload_factory_binding_runtime.hosted.admission import PlanBindings, PlanFacts, preflight
from workload_factory_binding_runtime.hosted.measurement import MeasurementBindings, LaunchObservation
from workload_factory_binding_runtime.hosted.finalization import (StagingReadback, FinalizationBindings,
    FinalAuthority, finalize, admit_finalized)
from workload_factory_binding_runtime.launch import ProcessLaunch, worker_configuration
from workload_factory_binding_runtime.workflow import EnvironmentReadback
from factory_binding.conftest import jwt
from .test_workflow import w, c, configuration, l

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def v(w, tmp_path):
    c, h = w.c, w.c.h
    config, policy = deepcopy(c.config), deepcopy(h.policy)
    for key in ("run_id", "run_attempt"):
        del config["launch"][key]
    del config["composition_digest"], config["authority"]["policy_digest"], policy["composition_digest"]
    policy["claims"] = deepcopy(config["launch"])
    worker = tmp_path / "worker.py"
    worker.write_bytes(Path(__file__).with_name("supervisor_worker.py").read_bytes())
    conf = tmp_path / "worker.json"
    cwd = tmp_path / "run"
    cwd.mkdir()
    executable = Path(sys.executable).resolve()
    paths = {"worker": worker, "supervisor": ROOT / "scripts/workload_factory_binding_runtime/supervisor.py",
             "measurement_module": ROOT / "scripts/workload_factory_binding_runtime/launch.py"}
    roots = {"root:case": tmp_path, "root:code": ROOT, "root:python": executable.parent}
    def spec(path):
        for ref in ("root:python", "root:case", "root:code"):
            if path.is_relative_to(roots[ref]):
                return {"root_ref": ref, "path": path.relative_to(roots[ref]).as_posix()}
        raise AssertionError("unselected fixture root")
    artifacts = {name: {**spec(path), "digest": byte_digest(path.read_bytes())} for name, path in paths.items()}
    for role in ("worker", "supervisor"):
        config["sources"][role]["digest"] = artifacts[role]["digest"]
    stage_policy = {"launch_ref": "launch:fixture-001", "host_ref": "host:fixture", "incarnation_ref": "incarnation:fixture",
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(), "cleanup_ref": config["lifecycle"]["cleanup_ref"],
        "scheduler_capability_digest": digest({"scheduler": "fixture-only"}), "template_digest": "",
        "max_status_reads": 6, "status_window_seconds": 60}
    plan = {"profile": PROFILE, "configuration_template": config, "policy_template": policy,
        "measurement_plan": {"executable": spec(executable), "executable_digest": byte_digest(executable.read_bytes()),
            "worker": spec(worker), "configuration": spec(conf), "cwd": spec(cwd), "artifacts": artifacts,
            "uid": os.getuid(), "capabilities": []}, "derivation_rules": DERIVATION,
        "staging_policy": stage_policy, "hosting_selection_digest": digest({"hosting": "isolated-fixture"}),
        "source_hold_ref": "hold:fixture"}
    stage_policy["template_digest"] = template_digest(plan)
    raw = canonical(plan)
    selected = validate_plan(raw, approved_digest=digest(plan), now=h.now)
    # The commitment exists before this fixture constructs any run-bound projection or child.
    context = DispatchContext(**{k: getattr(w.context, k) for k in DispatchContext.__dataclass_fields__
                                if k not in ("selection_digest", "preauthorization_ref")},
                              selection_digest=selected.digest, preauthorization_ref="preauth:hosted")
    result = SimpleNamespace(w=w, c=c, h=h, plan=plan, raw=raw, context=context, selected=selected,
        process=None, paths=paths, roots=roots, conf=conf, cwd=cwd, executable=executable, calls=[], hooks={})
    launch = {**config["launch"], "run_id": context.run_id, "run_attempt": context.run_attempt}
    result.facts = PlanFacts("principal:plan-reader", selected.digest, context.preauthorization_ref,
        config["case_ref"], context.accepted_commit, launch, plan["hosting_selection_digest"],
        plan["source_hold_ref"], digest(config["protection"]), stage_policy["scheduler_capability_digest"],
        "consumed-current", h.now, h.now + 30)
    result.environment = EnvironmentReadback("principal:environment-reader", True, deepcopy(config["protection"]), h.now, h.now + 30)
    def read(role):
        def callback(ref, *, deadline):
            result.calls.append((role, ref, deadline))
            if role in result.hooks:
                result.hooks[role]()
            return getattr(result, role)
        return callback
    result.read = read
    def identity(phase):
        expected = {**launch, "event_name": "workflow_dispatch"}
        if phase == "preflight":
            del expected["environment"]
            expected["sub"] = "repo:opensoft/openXwallet:ref:refs/heads/main"
        policy = IdentityPolicy(phase, BOOTSTRAP_AUDIENCE, config["issuer"]["audience"], expected)
        claims = {**h.claims, **expected, "aud": BOOTSTRAP_AUDIENCE}
        if phase == "preflight":
            del claims["environment"]
        return policy, jwt(h.issuer_key, claims)

    pre, result.pre_token = identity("preflight")
    protected, result.token = identity("protected")
    common = dict(approved_plan_digest=selected.digest, load_plan=lambda: result.raw,
        verifier=BootstrapVerifier(c.r.source), facts_principal=result.facts.principal_ref, read_facts=read("facts"),
        environment_principal=result.environment.principal_ref, read_environment=read("environment"),
        clock=lambda: h.now, monotonic=lambda: c.r.clock.mono)
    result.preflight = PlanBindings(policy=pre, **common)
    result.protected = PlanBindings(policy=protected, **common)
    def observation(principal):
        def observe(ref, *, deadline):
            assert result.process is not None
            result.calls.append((principal, ref, deadline))
            if principal in result.hooks:
                result.hooks[principal]()
            process = ProcessLaunch.capture(result.process, executable=executable,
                executable_digest=plan["measurement_plan"]["executable_digest"], worker=worker,
                configuration_file=conf, cwd=cwd, artifacts={k: v for k, v in paths.items() if k != "measurement_module"})
            return LaunchObservation(principal, ref, stage_policy["host_ref"], stage_policy["incarnation_ref"],
                stage_policy["boot_id"], "invocation:fixture-001", process, h.now, h.now + 20)
        return observe
    result.observe = observation
    result.measurement = MeasurementBindings("principal:launch-observer", roots, observation("principal:launch-observer"))
    def start():
        assert result.process is None
        run_config = deepcopy(config)
        run_config["launch"].update(run_id=context.run_id, run_attempt=context.run_attempt)
        projection = worker_configuration(run_config, policy)
        conf.write_bytes(canonical(projection))
        result.process = subprocess.Popen([str(executable), "-I", "-B", str(worker), str(conf)], cwd=cwd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={"PATH": os.defpath, "LANG": "C.UTF-8"})
        assert select.select([result.process.stdout], [], [], 5)[0]
        assert result.process.stdout.readline() == b"ready\n"
        observed = result.measurement.observe(stage_policy["launch_ref"], deadline=h.now + 20)
        generation = {k: getattr(observed, k) for k in ("launch_ref", "host_ref", "incarnation_ref", "boot_id", "invocation_ref")}
        generation.update(pid=observed.process.pid, start_time=observed.process.start_time)
        (tmp_path / "hosted-generation.json").write_text(json.dumps({"pid": result.process.pid, "start_time": observed.process.start_time}))
        result.stage = StagingReadback("principal:stage-reader", selected.digest, config["case_ref"], context.run_id,
            context.run_attempt, stage_policy["launch_ref"], stage_policy["cleanup_ref"], generation,
            "cleanup-acknowledged", h.now, h.now + 20)
        result.projection, result.launch = projection, observed.process
        result.calls.clear()
    result.start = start
    result.bindings = FinalizationBindings(result.protected, result.measurement,
        "principal:stage-reader", read("stage"), "principal:final-authority")
    # Separate observer capability and independently retained approved plan bytes.
    result.authority_bindings = replace(result.bindings,
        plan=replace(result.protected, load_plan=lambda: raw),
        measurement=MeasurementBindings("principal:authority-observer", roots, observation("principal:authority-observer")))
    result.authority = FinalAuthority(result.authority_bindings)
    result.finalize = lambda: finalize(context, result.token, bindings=result.bindings, authority=result.authority)
    try:
        yield result
    finally:
        if result.process:
            if result.process.poll() is None:
                result.process.terminate()
                try: result.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    result.process.kill(); result.process.wait(timeout=5)
            for stream in (result.process.stdin, result.process.stdout, result.process.stderr):
                stream.close()
            assert result.process.poll() is not None


def test_static_plan_commits_before_any_run_or_process(v):
    config = v.selected.value()["configuration_template"]
    assert v.process is None
    assert set(config["launch"]) == CLAIMS
    assert "composition_digest" not in config
    assert "policy_digest" not in config["authority"]
    assert "composition_digest" not in v.selected.value()["policy_template"]
    assert v.selected.digest == digest(v.plan)


@pytest.mark.parametrize("group", ["sources", "dependency_digest", "issuer", "launch", "protection", "authority", "services", "state", "lifecycle", "case_ref", "expires_at"])
def test_no_additional_static_field_can_be_omitted(v, group):
    plan = deepcopy(v.plan); del plan["configuration_template"][group]
    plan["staging_policy"]["template_digest"] = template_digest(plan)
    with pytest.raises(BindingError): validate_plan(canonical(plan), approved_digest=digest(plan), now=v.h.now)


@pytest.mark.parametrize("member", ["run_id", "run_attempt", "composition_digest", "policy_digest"])
@pytest.mark.parametrize("placeholder", [None, "pending", "sha256:" + "0" * 64])
def test_exact_four_late_fields_must_be_absent_not_placeholders(v, member, placeholder):
    plan = deepcopy(v.plan); c = plan["configuration_template"]
    target = c["launch"] if member.startswith("run_") else c["authority"] if member == "policy_digest" else c
    target[member] = placeholder
    plan["staging_policy"]["template_digest"] = template_digest(plan)
    with pytest.raises(BindingError): validate_plan(canonical(plan), approved_digest=digest(plan), now=v.h.now)


@pytest.mark.parametrize("change", ["extra", "profile", "derivation", "policy", "template", "root-path", "root-uid", "capabilities", "status-count", "status-window"])
def test_closed_versioned_plan_rejects_unapproved_shape_or_algorithm(v, change):
    p = deepcopy(v.plan)
    if change == "extra": p["patch"] = {}
    elif change == "profile": p["profile"] = "openxfactory-dispatch-selection-internal-v1"
    elif change == "derivation": p["derivation_rules"] = "eval:candidate"
    elif change == "policy": p["policy_template"]["claims"]["sha"] = "c" * 40
    elif change == "template": p["staging_policy"]["template_digest"] = "sha256:" + "f" * 64
    elif change == "root-path":
        p["measurement_plan"]["worker"]["path"] = "../worker.py"
        p["measurement_plan"]["artifacts"]["worker"]["path"] = "../worker.py"
    elif change == "root-uid": p["measurement_plan"]["uid"] = 0
    elif change == "capabilities": p["measurement_plan"]["capabilities"] = ["CAP_SYS_ADMIN"]
    elif change == "status-count": p["staging_policy"]["max_status_reads"] = 7
    else: p["staging_policy"]["status_window_seconds"] = 61
    if change != "template":
        p["staging_policy"]["template_digest"] = template_digest(p)
    with pytest.raises(BindingError): validate_plan(canonical(p), approved_digest=digest(p), now=v.h.now)


@pytest.mark.parametrize("raw", [b"{}", b"[]", b'{"profile":1,"profile":2}', b'{"a":NaN}', b" " * 65537])
def test_malformed_or_oversized_plan_has_only_fixed_error(v, raw):
    with pytest.raises(BindingError, match="^" + ERROR + "$"): validate_plan(raw, approved_digest=v.selected.digest, now=v.h.now)


def test_v2_is_not_accepted_by_any_v1_or_full_configuration_route(v):
    with pytest.raises(BindingError): selection_digest(v.raw)
    with pytest.raises(BindingError): validate_config(v.raw, trust=v.c.trust)


def test_signed_preflight_is_plan_only_and_has_no_effectful_ports(v):
    result = preflight(v.context, v.pre_token, bindings=v.preflight)
    assert result.plan_digest == v.selected.digest
    assert result.environment == v.plan["configuration_template"]["launch"]["environment"]
    assert not hasattr(result, "config_digest")
    assert not hasattr(result, "operation_grant_ref")
    assert v.process is None
    assert v.h.calls == 0
    assert {role for role, _, _ in v.calls} == {"facts", "environment"}


@pytest.mark.parametrize("member", ["principal_ref", "plan_digest", "preauthorization_ref", "case_ref", "accepted_commit", "launch", "hosting_selection_digest", "source_hold_ref", "protection_digest", "scheduler_capability_digest", "state", "observed_at", "expires_at"])
def test_each_independent_current_fact_is_required_before_plan_readiness(v, member):
    old = getattr(v.facts, member)
    value = v.h.now + 1 if member == "observed_at" else v.h.now if member == "expires_at" else {} if member == "launch" else "ref:changed"
    v.facts = replace(v.facts, **{member: value})
    with pytest.raises(BindingError): preflight(v.context, v.pre_token, bindings=v.preflight)
    assert v.process is None
    assert v.h.calls == 0


@pytest.mark.parametrize("change", ["wrong-phase", "wrong-audience", "wrong-key", "environment", "missing", "bypass", "branch", "source", "rerun"])
def test_preflight_requires_valid_purpose_identity_and_independent_existing_protection(v, change):
    context, token, bindings = v.context, v.pre_token, v.preflight
    if change == "wrong-phase": token = v.token
    elif change in ("wrong-audience", "environment"):
        from workload_factory_binding.evidence import decode64, decode_object
        claims = decode_object(decode64(token.split(".")[1]))
        if change == "wrong-audience": claims["aud"] = v.preflight.policy.proof_audience
        else: claims["environment"] = "qa"
        token = jwt(v.h.issuer_key, claims)
    elif change == "wrong-key":
        token = token[:-8] + "invalidx"
    elif change == "missing": v.environment = replace(v.environment, exists=False)
    elif change == "bypass": v.environment.protection["can_admins_bypass"] = True
    elif change == "branch": v.environment.protection["deployment_refs"] = ["refs/tags/main"]
    elif change == "source": context = replace(context, source_commit="c" * 40)
    else: context = replace(context, run_attempt="2")
    with pytest.raises(BindingError): preflight(context, token, bindings=bindings)
    assert v.process is None
    assert v.h.calls == 0


def test_actual_generation_finalizes_complete_bytes_with_independent_recomputation(v):
    v.start(); result = v.finalize()
    config, policy = json.loads(result.configuration), json.loads(result.policy)
    assert config["launch"]["run_id"] == v.context.run_id
    assert config["authority"]["policy_digest"] == digest(policy)
    assert config["composition_digest"] == policy["composition_digest"]
    assert result.binding.config_digest == digest(config)
    assert {role for role, _, _ in v.calls} >= {"principal:launch-observer", "principal:authority-observer"}
    assert v.h.calls == 0
    original = deepcopy(config)
    for member in ("run_id", "run_attempt"): del config["launch"][member]
    del config["composition_digest"], config["authority"]["policy_digest"]
    assert config == v.plan["configuration_template"]
    assert original["composition_digest"] != "sha256:" + "0" * 64


@pytest.mark.parametrize("member", ["principal_ref", "launch_ref", "host_ref", "incarnation_ref", "boot_id", "invocation_ref", "pid", "start_time", "executable_digest", "cwd", "source", "projection"])
def test_actual_observed_generation_source_or_projection_mutation_refuses(v, member):
    v.start()
    original = v.measurement.observe
    def altered(ref, *, deadline):
        observation = original(ref, deadline=deadline)
        if member == "source": v.paths["worker"].write_text("changed source")
        elif member == "projection": v.conf.write_bytes(canonical({"changed": True}))
        elif member in ("pid", "start_time", "executable_digest", "cwd"):
            value = observation.process.pid + 100000 if member == "pid" else observation.process.start_time + 1 if member == "start_time" else "sha256:" + "f" * 64 if member == "executable_digest" else v.cwd.parent
            observation = replace(observation, process=replace(observation.process, **{member: value}))
        else: observation = replace(observation, **{member: "ref:changed"})
        return observation
    v.bindings = replace(v.bindings, measurement=replace(v.measurement, observe=altered))
    with pytest.raises(BindingError): v.finalize()
    assert v.h.calls == 0


@pytest.mark.parametrize("member", ["plan_digest", "case_ref", "run_id", "run_attempt", "launch_ref", "cleanup_ref", "generation", "state", "principal_ref"])
def test_current_cleanup_ack_is_mandatory_and_generation_bound(v, member):
    v.start(); v.stage = replace(v.stage, **{member: {} if member == "generation" else "ref:changed"})
    with pytest.raises(BindingError): v.finalize()
    assert v.h.calls == 0


def test_protected_finalization_cannot_use_a_signature_valid_preflight_token(v):
    v.start()
    with pytest.raises(BindingError): finalize(v.context, v.pre_token, bindings=v.bindings, authority=v.authority)
    assert v.h.calls == 0


def test_final_authority_compares_complete_bytes_not_caller_supplied_hashes(v):
    v.start(); result = v.finalize()
    changed = json.loads(result.configuration); changed["state"]["recovery_ref"] = "recovery:other"
    decision = Decision(clock=v.protected.clock, monotonic=v.protected.monotonic)
    with pytest.raises(BindingError):
        v.authority.approve(v.context, v.token, configuration=canonical(changed), policy=result.policy, decision=decision)
    changed = json.loads(result.policy); changed["wallet"]["holder"]["display_label"] = "other"
    with pytest.raises(BindingError):
        v.authority.approve(v.context, v.token, configuration=result.configuration, policy=canonical(changed),
            decision=Decision(clock=v.protected.clock, monotonic=v.protected.monotonic))


@pytest.mark.parametrize("where", ["facts", "environment", "stage", "principal:launch-observer", "principal:authority-observer"])
@pytest.mark.parametrize("change", ["expiry", "wall-regression", "monotonic", "private-error"])
def test_every_blocking_phase_retains_parent_deadline_and_redacts_failures(v, where, change):
    v.start()
    def alter():
        if change == "expiry": v.h.now += 20
        elif change == "wall-regression": v.h.now -= 1
        elif change == "monotonic": v.c.r.clock.mono += 11
        else: raise OSError("private-error-canary")
    v.hooks[where] = alter
    with pytest.raises(BindingError, match="^" + ERROR + "$") as caught: v.finalize()
    assert "private-error-canary" not in str(caught.value)
    assert v.h.calls == 0


def test_v2_reaches_unchanged_full_admission_and_real_owning_proof(v):
    v.start(); result = v.finalize(); c, h, w = v.c, v.h, v.w
    c.config.clear(); c.config.update(json.loads(result.configuration)); h.policy = json.loads(result.policy)
    h.claims.update(c.config["launch"])
    h.artifacts, h.configuration = dict(v.launch.artifacts), v.launch.expected_configuration(v.projection)
    h.reset_evidence(); c.reselect_policy()
    life = w.lease_fixture
    life.plan = replace(life.plan, scope=replace(life.plan.scope, config_digest=result.binding.config_digest))
    life.janitor.plan = life.plan
    for ref, managed in life.managed.items():
        if managed.resource.retention == "run": life.managed[ref] = replace(managed, owner_scope_digest=digest(asdict(life.plan.scope)))
    life.life = life.make()
    w.bindings = replace(w.bindings, runtime_trust=c.trust, lifecycle=life.life)
    w.authorization = replace(w.authorization, config_digest=result.binding.config_digest)
    w.scheduler = replace(w.scheduler, plan_digest=life.plan.digest)
    context = replace(w.context, config_digest=result.binding.config_digest)
    admission = admit_finalized(result, context, bindings=w.bindings)
    assert admission.config_digest == result.binding.config_digest
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    h.binding = TrustedKeyBinding(**asdict(h.binding))
    bridge = c.make(create_proof=create_proof)
    proof = bridge.sign(h.challenge.id, h.request, h.token, h.observation)
    assert verify_proof(proof["proof"], expected_digest=h.challenge.digest, binding=h.binding, now=h.now).subject_ref == h.binding.subject_ref
    assert proof["human_approval"] is False
    assert h.calls == 1


def test_finalization_does_not_replace_full_config_grant_or_cleanup_admission(v):
    v.start(); result = v.finalize()
    with pytest.raises(BindingError): admit_finalized(result, v.w.context, bindings=v.w.bindings)
    assert v.h.calls == 0


def test_source_hold_drift_during_environment_read_refuses_before_output(v):
    def revoke():
        v.facts = replace(v.facts, state="revoked")
    v.hooks["environment"] = revoke
    with pytest.raises(BindingError): preflight(v.context, v.pre_token, bindings=v.preflight)
    assert v.process is None
    assert v.h.calls == 0


@pytest.mark.parametrize("change", ["expired-clock", "authority-timeout", "private-error"])
def test_independent_authority_checks_own_current_clock_and_redacts_errors(v, change):
    v.start()
    if change == "expired-clock":
        b = replace(v.authority_bindings, plan=replace(v.authority_bindings.plan, clock=lambda: v.h.now + 100))
    elif change == "authority-timeout":
        mono = iter([0, 0] + [20] * 50)
        b = replace(v.authority_bindings, plan=replace(v.authority_bindings.plan, monotonic=lambda: next(mono)))
    else:
        def broken(): raise OSError("authority-private-canary")
        b = replace(v.authority_bindings, plan=replace(v.authority_bindings.plan, load_plan=broken))
    v.authority = FinalAuthority(b)
    with pytest.raises(BindingError, match="^" + ERROR + "$"): v.finalize()
    assert v.h.calls == 0


def test_process_drift_after_authority_acceptance_is_rechecked_before_return(v, monkeypatch):
    v.start()
    original = FinalAuthority.approve
    def changed(authority, *args, **kwargs):
        accepted = original(authority, *args, **kwargs)
        v.conf.write_bytes(canonical({"after-acceptance": True}))
        return accepted
    monkeypatch.setattr(FinalAuthority, "approve", changed)
    with pytest.raises(BindingError): v.finalize()
    assert v.h.calls == 0


@pytest.mark.parametrize("member,value", [("observed_at", True), ("observed_at", "future"),
    ("expires_at", True), ("expires_at", "expired"), ("expires_at", "extended")])
def test_final_authority_cannot_extend_or_forge_accepted_time(v, monkeypatch, member, value):
    v.start(); original = FinalAuthority.approve
    def changed(authority, *args, **kwargs):
        record = original(authority, *args, **kwargs)
        actual = v.h.now + 1 if value == "future" else v.h.now if value == "expired" else v.h.now + 61 if value == "extended" else value
        return replace(record, **{member: actual})
    monkeypatch.setattr(FinalAuthority, "approve", changed)
    with pytest.raises(BindingError): v.finalize()
    assert v.h.calls == 0


def test_matching_signed_token_and_policy_cannot_replace_factory_bootstrap_purpose(v):
    from workload_factory_binding.evidence import decode64, decode_object
    claims = decode_object(decode64(v.pre_token.split(".")[1]))
    claims["aud"] = "urn:fixture:another-purpose"
    changed = replace(v.preflight, policy=replace(v.preflight.policy, audience=claims["aud"], expected=dict(v.preflight.policy.expected)))
    with pytest.raises(BindingError): preflight(v.context, jwt(v.h.issuer_key, claims), bindings=changed)
    assert v.process is None
    assert v.h.calls == 0


@pytest.mark.parametrize("change", ["adapter-repository", "reusable-graph"])
def test_reapproval_cannot_replace_fixed_source_or_local_reusable_graph(v, change):
    from workload_factory_binding.evidence import decode64, decode_object
    plan = deepcopy(v.plan)
    config = plan["configuration_template"]
    expected = dict(v.preflight.policy.expected)
    if change == "adapter-repository":
        config["sources"]["adapter"]["repository"] = "fixture/other-adapter"
    else:
        config["sources"]["reusable_workflow"]["path"] = ".github/workflows/other.yml"
        config["launch"]["job_workflow_ref"] = v.context.repository + "/.github/workflows/other.yml@refs/heads/main"
        plan["policy_template"]["claims"] = deepcopy(config["launch"])
        expected["job_workflow_ref"] = config["launch"]["job_workflow_ref"]
    plan["staging_policy"]["template_digest"] = template_digest(plan)
    v.raw = canonical(plan)
    approved = digest(plan)
    context = replace(v.context, selection_digest=approved)
    v.facts = replace(v.facts, plan_digest=approved, launch={**config["launch"], "run_id": context.run_id, "run_attempt": context.run_attempt})
    claims = decode_object(decode64(v.pre_token.split(".")[1])); claims.update(expected)
    bindings = replace(v.preflight, approved_plan_digest=approved, policy=replace(v.preflight.policy, expected=expected))
    with pytest.raises(BindingError): preflight(context, jwt(v.h.issuer_key, claims), bindings=bindings)
    assert v.process is None
    assert v.h.calls == 0


def test_late_mutation_of_reused_stage_snapshot_cannot_mask_generation_drift(v):
    v.start(); calls = 0
    def changed():
        nonlocal calls
        calls += 1
        # Last coordinator derivation, after its measurement, during recheck.
        if calls == 11:
            v.stage.generation["pid"] += 1
    v.hooks["facts"] = changed
    with pytest.raises(BindingError): v.finalize()
    assert v.h.calls == 0


@pytest.mark.parametrize("member", ["pid", "invocation_ref"])
def test_callback_mutation_cannot_replace_the_frozen_acknowledged_generation(v, member):
    v.start()
    measured = deepcopy(v.stage.generation)
    acknowledged = deepcopy(measured)
    acknowledged[member] = measured[member] + 1 if member == "pid" else "invocation:other"
    def restore_acknowledgement():
        v.stage.generation.clear(); v.stage.generation.update(acknowledged)
    def substitute_measured_generation():
        v.stage.generation.clear(); v.stage.generation.update(measured)
    # Each authoritative read acknowledges A. A reused callback dictionary briefly
    # changes to measured B, then returns to A before the next stage read.
    v.hooks["stage"] = restore_acknowledgement
    v.hooks["principal:launch-observer"] = substitute_measured_generation
    v.hooks["principal:authority-observer"] = substitute_measured_generation
    with pytest.raises(BindingError): v.finalize()
    assert v.h.calls == 0
