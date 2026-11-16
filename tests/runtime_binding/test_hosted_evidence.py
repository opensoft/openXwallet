"""T012T real owning/hosted composition and private golden grammar controls.

All provider identities and issuer transport are isolated fixtures. Golden report
bytes are encoder vectors only; source executions never emit protected artifacts.
"""
from dataclasses import asdict, replace
import json
import sqlite3
import time
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import BindingError, canonical, digest, observe_artifacts
from workload_factory_binding_runtime.config import validate_config
from workload_factory_binding_runtime.lifecycle import CleanupVerification
from workload_factory_binding_runtime.runtime import WorkerContext
from workload_factory_binding_runtime.loaders import ServiceIdentity
from workload_factory_binding_runtime.github_bootstrap.common import Decision, document
from workload_factory_binding_runtime.hosted.evidence import (PROFILE, CASES, PROOF_FIELDS,
    CaseObservation, _project, build_receipt)
from workload_factory_binding_runtime.hosted.qualification import (ProofTrace, BarrierInputs,
    QualificationBindings, Qualifier, WorkerProbe, _barrier)
from workload_factory_binding_runtime.workflow import SchedulerReadback
from workload_factory_binding_runtime.launch import worker_configuration
from factory_binding.conftest import jwt
from .launch_fixture import stage, v, g, rb, configuration, c, l, w
from .test_hosted_issuance import provider
from .hosted_lifecycle_fixture import lh
from .custody_fixture import k
from .hosted_fixture import child_generations
from .test_custody import _owning_run


@pytest.fixture
def vector(c, l):
    now = c.h.now
    selected = validate_config(c.bridge.load_config(), trust=c.trust)
    cleanup = CleanupVerification(l.plan.digest, l.plan.scope, "success", now, now, now + 20,
        digest({"readback": "golden"}), digest({"identity": "golden"}), digest({"attempt": "golden"}))
    return dict(selected=selected, plan=l.plan, cleanup=cleanup, started_at=now, now=now,
        operation_floor=now, outcome="success", phase_provenance_digest=digest({"phase": "golden"}),
        generation_digest=digest({"generation": "golden"}), issuance_digest=digest({"issuance": "golden"}),
        cases=tuple(CaseObservation(n, now, digest({"case": n}), "passed") for n in CASES),
        proof={"status": "verified", **{n: digest({"proof": n}) for n in PROOF_FIELDS}})


def test_private_encoder_vector_has_exact_closed_grammar_and_no_authority(vector):
    raw = _project(**vector); value = json.loads(raw)
    assert raw == canonical(value) and len(raw) <= 16384
    assert set(value) == {"profile", "scope", "status", "started_at", "issued_at", "context",
        "phase_provenance_digest", "generation_digest", "issuance_digest", "proof", "cleanup", "results",
        "error_code", "protected_machine_qualified", "human_approval", "domain_effect", "consumer_dependency_lock"}
    assert value["profile"] == PROFILE and value["status"] == "passed"
    assert set(value["results"]) == set(CASES) and len(CASES) == 27
    assert all(value[n] is False for n in ("human_approval", "domain_effect", "consumer_dependency_lock"))
    with pytest.raises(BindingError, match="^protected-report-refused$"):
        build_receipt(value, now=vector["now"])


@pytest.mark.parametrize("case", CASES)
def test_every_missing_slot_is_unperformed_and_never_qualified(vector, case):
    vector["cases"] = tuple(v for v in vector["cases"] if v.case_id != case)
    result = json.loads(_project(**vector))
    assert result["results"][case] == {"status": "not-performed"}
    assert result["status"] == "incomplete" and not result["protected_machine_qualified"]


@pytest.mark.parametrize("case", CASES)
def test_every_actual_failed_case_cannot_be_upgraded_by_cleanup(vector, case):
    vector["cases"] = tuple(replace(v, status="failed") if v.case_id == case else v for v in vector["cases"])
    result = json.loads(_project(**vector))
    assert result["status"] == "failed" and not result["protected_machine_qualified"]


@pytest.mark.parametrize("field", PROOF_FIELDS)
def test_each_missing_proof_barrier_refuses(vector, field):
    del vector["proof"][field]
    with pytest.raises(BindingError, match="^protected-report-refused$"):
        _project(**vector)


@pytest.mark.parametrize("field", ("phase_provenance_digest", "generation_digest", "issuance_digest"))
@pytest.mark.parametrize("value", (None, True, "private-canary", "sha256:" + "0" * 64))
def test_unavailable_or_placeholder_provenance_cannot_enter_projection(vector, field, value):
    vector[field] = value
    with pytest.raises(BindingError, match="^protected-report-refused$") as caught:
        _project(**vector)
    assert "private-canary" not in str(caught.value)


@pytest.mark.parametrize("outcome,status", [("failure", "failed"), ("cancel", "cancelled"), ("incomplete", "incomplete")])
def test_operation_outcome_remains_authoritative_after_successful_cleanup(vector, outcome, status):
    result = json.loads(_project(**{**vector, "outcome": outcome}))
    assert result["status"] == status and not result["protected_machine_qualified"]


def test_cancellation_precedes_failed_case_and_cleanup(vector):
    vector["cleanup"] = replace(vector["cleanup"], outcome="failure")
    vector["cases"] = (replace(vector["cases"][0], status="failed"), *vector["cases"][1:])
    result = json.loads(_project(**{**vector, "outcome": "cancel"}))
    assert result["status"] == "cancelled"


def test_cleanup_and_privacy_slots_can_follow_cleanup_without_self_digest_cycle(vector):
    vector["now"] += 2
    vector["cases"] = tuple(replace(v, observed_at=vector["now"]) if v.case_id in ("H11", "H12", "R01") else v
                            for v in vector["cases"])
    result = json.loads(_project(**vector))
    assert result["status"] == "passed"
    assert result["results"]["H12"]["observed_at"] > result["cleanup"]["checked_at"]
    assert "report_digest" not in result


@pytest.mark.parametrize("change", ["missing", "stale", "wrong-plan", "wrong-scope", "wrong-attempt", "before-use"])
def test_independent_cleanup_binding_and_freshness_cannot_be_fabricated(vector, change):
    if change == "missing":
        vector["cleanup"] = None
        result = json.loads(_project(**vector));assert result["status"] == "incomplete";return
    if change == "stale":
        vector["now"] += 20
        result = json.loads(_project(**vector));assert result["status"] == "incomplete";return
    if change == "wrong-plan":vector["cleanup"] = replace(vector["cleanup"], plan_digest=digest({"other": True}))
    if change == "wrong-scope":vector["cleanup"] = replace(vector["cleanup"], scope=replace(vector["plan"].scope, run_id="999"))
    if change == "wrong-attempt":vector["cleanup"] = replace(vector["cleanup"], attempt_digest="sha256:" + "0" * 64)
    if change == "before-use":vector["operation_floor"] += 1;vector["now"] += 1
    with pytest.raises(BindingError, match="^protected-report-refused$"):
        _project(**vector)


@pytest.mark.parametrize("kind", ["duplicate", "unknown", "dict", "future", "boolean", "placeholder", "raw-status"])
def test_wrong_case_shape_or_raw_payload_refuses(vector, kind):
    c = vector["cases"][0]
    if kind == "duplicate":vector["cases"] = (c, c)
    if kind == "unknown":vector["cases"] = (replace(c, case_id="private-canary"),)
    if kind == "dict":vector["cases"] = (asdict(c),)
    if kind == "future":vector["cases"] = (replace(c, observed_at=vector["now"] + 1),)
    if kind == "boolean":vector["cases"] = (replace(c, observed_at=True),)
    if kind == "placeholder":vector["cases"] = (replace(c, artifact_digest="sha256:" + "0" * 64),)
    if kind == "raw-status":vector["cases"] = (replace(c, status="private-canary"),)
    with pytest.raises(BindingError, match="^protected-report-refused$") as error:
        _project(**vector)
    assert "private-canary" not in str(error.value)


@pytest.mark.parametrize("candidate", [True, {"live": True}, {"authenticated": True, "scope": "protected-machine"}, None])
def test_body_flags_and_fixture_labels_never_establish_operational_origin(vector, candidate):
    with pytest.raises(BindingError, match="^protected-report-refused$"):
        build_receipt(candidate, now=vector["now"])


def test_observed_runtime_preserves_actual_reservation_cause_and_no_extra_reads(c):
    trace = ProofTrace()
    c.bridge.sign_observed(c.h.challenge.id, c.h.request, c.h.token, c.h.observation, trace=trace)
    before = len(c.r.transport.calls)
    replay = ProofTrace()
    with pytest.raises(BindingError):
        c.bridge.sign_observed(c.h.challenge.id, c.h.request, c.h.token, c.h.observation, trace=replay)
    assert trace.reservation == "reserved" and replay.reservation == "replay-refused"
    assert len(c.r.transport.calls) == before == 2
    with pytest.raises(BindingError):
        c.bridge.sign_observed(c.h.challenge.id, c.h.request, c.h.token, c.h.observation, trace=trace)


@pytest.mark.parametrize("kind", ["audience", "environment"])
def test_barriers_require_real_valid_signature_and_exact_claim_refusal(c, kind):
    c.run()
    selected = validate_config(c.bridge.load_config(), trust=c.trust)
    field = "aud" if kind == "audience" else "environment"
    token = jwt(c.h.issuer_key, {**c.h.claims, field: "other-valid-value"})
    value = _barrier(token, kind, c.bridge, c.h.now, selected,
                     (c.h.challenge.id, c.h.request, c.h.token, c.h.observation))
    assert value.startswith("sha256:")
    parts = token.split(".");parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
    bad = ".".join(parts)
    with pytest.raises(BindingError):
        _barrier(bad, kind, c.bridge, c.h.now, selected,
                 (c.h.challenge.id, c.h.request, c.h.token, c.h.observation))


def test_connected_hosted_proof_refuses_at_original_private_read_cap_and_cleans_up(k, w, request, tmp_path):
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.custody import TLSClient
    k.access = replace(k.access, sources_digest=digest(k.c.config["sources"]))
    retained = {}
    def prepare(c, create_proof):
        c.h.claims.update(c.config["launch"])
        c.h.policy["claims"].update({name: c.config["launch"][name] for name in c.h.policy["claims"]})
        c.h.reset_evidence();c.reselect_policy()
        hosted = request.getfixturevalue("lh")
        retained["hosted"] = hosted
        hosted.launch(full=True);final, plan = hosted.finalize();hosted.takeover()
        life = hosted.runtime()
        original_run = life.run
        def traced_run(operation):
            def traced():
                try:
                    return operation()
                except BaseException as error:
                    import traceback
                    frames = [{"file": __import__("pathlib").Path(f.filename).name, "line": f.lineno,
                               "function": f.name} for f in traceback.extract_tb(error.__traceback__)]
                    (tmp_path / "qualification-failure.json").write_text(json.dumps({"type": type(error).__name__,
                        "frames": frames}))
                    raise
            return original_run(traced)
        life.run = traced_run
        c.config = document(final.configuration)
        c.h.policy = document(final.policy)
        c.h.artifacts = dict(hosted.stage.spec.artifacts)
        c.h.configuration = worker_configuration(c.config, c.h.policy)
        c.h.claims.update(c.config["launch"])
        c.h.token = jwt(c.h.issuer_key, c.h.claims)
        from workload_factory_binding.gate import request_digest
        c.h.challenge = replace(c.h.challenge, request_digest=request_digest(c.h.policy, c.h.request))
        c.records.value = c.h.policy
        c.challenge.value = asdict(c.h.challenge)
        c.trust = life.runtime_trust
        c.context = WorkerContext(ServiceIdentity(**c.config["services"]["worker_channel"]), digest(c.config),
            c.config["case_ref"], c.h.request["run_id"], c.h.request["run_attempt"], c.h.now, c.h.now + 20)
        k.access = replace(k.access, config_digest=digest(c.config), sources_digest=digest(c.config["sources"]))
        signer = c.services["custody"].target
        signer.runtime_trust = c.trust
        signer.load_config = lambda: final.configuration
        def debug_operation(name, function):
            def call(*a, **kw):
                try:
                    return function(*a, **kw)
                except BaseException as error:
                    import traceback
                    frames = [{"file": __import__("pathlib").Path(f.filename).name, "line": f.lineno,
                               "function": f.name} for f in traceback.extract_tb(error.__traceback__)]
                    (tmp_path / (name+"-failure.json")).write_text(json.dumps({"type": type(error).__name__, "frames": frames}))
                    raise
            return call
        signer.sign_for_use_observed = debug_operation("custody-use", signer.sign_for_use_observed)
        life.janitor.target.read_lease = debug_operation("lease-read", life.janitor.target.read_lease)
        c.bridge = c.make(create_proof=debug_operation("owning-create", create_proof), lifecycle=life,
            load_config=lambda: final.configuration)
        from workload_factory_binding_runtime.launch import ProcessLaunch
        from workload_factory_binding_runtime.supervisor import SupervisorObserver, SupervisorPeer
        spec = hosted.stage.spec
        process = hosted.stage.agent.children[hosted.stage.scope["launch_ref"]]
        measured = ProcessLaunch.capture(process, executable=spec.paths["executable"],
            executable_digest=spec.m["executable_digest"], worker=spec.paths["worker"],
            configuration_file=spec.paths["configuration"], cwd=spec.paths["cwd"], artifacts=spec.artifacts)
        peer = c.config["services"]["supervisor"]
        observer = SupervisorObserver(load_config=lambda: final.configuration, trust=c.trust,
            services={n:c.services[n] for n in ("records", "challenge")}, issuer_source=c.r.source,
            launch=measured, private_key=c.h.supervisor,
            allowed_gate=(peer["principal_ref"], peer["credential_ref"]))
        c.h.observation = observer.observe({"challenge_id": c.h.challenge.id, "request": c.h.request,
            "token": c.h.token}, peer=SupervisorPeer(peer["principal_ref"], peer["credential_ref"],
            c.h.now, c.h.now+10), deadline=c.h.now+10)
        actual = c.bridge.sign_observed
        def observed(*a, **kw):
            value = actual(*a, **kw)
            retained["accepted"] = value
            return value
        c.bridge.sign_observed = observed
        context = replace(w.context, config_digest=final.binding.config_digest)
        workflow = replace(w.bindings, load_config=lambda: final.configuration, runtime_trust=c.trust, lifecycle=life,
            read_authorization=lambda ref, deadline: replace(w.authorization, config_digest=context.config_digest),
            read_scheduler=lambda ref, deadline: SchedulerReadback(w.scheduler.principal_ref,
                c.config["lifecycle"]["cleanup_ref"], plan.digest, life.readback.identity.principal_ref, c.h.now, c.h.now+10))
        barrier = BarrierInputs(jwt(c.h.issuer_key, {**c.h.claims, "aud": "factory:negative"}),
            jwt(c.h.issuer_key, {**c.h.claims, "environment": "negative-environment"}))
        worker = TLSClient(k.material.endpoint, ca_file=k.ca, certificate=k.worker[0], private_key=k.worker[1])
        positive = TLSClient(k.material.endpoint, ca_file=k.ca, certificate=k.gate[0], private_key=k.gate[1])
        bindings = QualificationBindings(validate_config(final.configuration, trust=c.trust), final, context,
            workflow, c.bridge, life.janitor.target.operation, barrier, WorkerProbe(worker, positive))
        retained["qualifier"] = Qualifier(bindings, challenge_id=c.h.challenge.id, request=c.h.request,
            token=c.h.token, observation=c.h.observation)
    def perform(_run):
        qualifier = retained["qualifier"]
        result = qualifier.run()
        retained["result"] = result
        return retained["accepted"]
    directory = tmp_path / "owning-connected";directory.mkdir(mode=0o700)
    with pytest.raises(BindingError, match="^qualification-failed$"):
        _owning_run(k, directory, before_proof=prepare, perform=perform)
    qualifier = retained["qualifier"];result = qualifier.result;hosted = retained["hosted"]
    assert result is not None and result.cleanup is not None
    assert result.outcome == "failure"
    from workload_factory_binding_runtime.hosted.readback import ReadBudget
    assert qualifier.bindings.workflow.lifecycle.janitor.target.operation._hosted_reads["counts"]["private"] == 12
    frames = json.loads((tmp_path / "lease-read-failure.json").read_text())["frames"]
    assert any(f["file"] == "readback.py" and f["function"] == "consume" for f in frames)
    assert not hosted.temporary.exists() and hosted.shared.read_bytes() == b"retained shared generation"
    with pytest.raises(BindingError, match="^protected-report-refused$"):
        build_receipt(result, now=k.c.h.now)
    with pytest.raises(BindingError):qualifier.run()


@pytest.fixture
def origin_vector(c):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from workload_factory_binding.evidence import encode64
    from workload_factory_binding_runtime.hosted.qualification import OriginTrust, ORIGIN_CONTEXT
    key = Ed25519PrivateKey.generate()
    expected = {"config_digest": digest(c.config), "case_digest": digest(c.config["case_ref"]),
        "run_id": c.config["launch"]["run_id"], "run_attempt": c.config["launch"]["run_attempt"],
        "phase_provenance_digest": digest({"phase": "fixture"}), "generation_digest": digest({"generation": "fixture"}),
        "issuance_digest": digest({"issuance": "fixture"}), "plan_digest": digest({"plan": "fixture"})}
    principal = c.trust.readback_principal
    payload = {**expected, "principal_ref": principal, "scope": "isolated-fixture",
               "observed_at": c.h.now, "expires_at": c.h.now + 10}
    def sign(value):
        return canonical({"payload": value, "signature": encode64(key.sign(ORIGIN_CONTEXT+canonical(value)))})
    return SimpleNamespace(expected=expected, payload=payload, sign=sign, now=c.h.now, principal=principal,
        trust=OriginTrust(principal, key.public_key().public_bytes_raw(), "isolated-fixture", lambda *_a,**_kw: None))


def test_real_operator_signature_authenticates_exact_fixture_origin_without_live_promotion(origin_vector):
    from workload_factory_binding_runtime.hosted.qualification import _origin
    v = origin_vector
    scope, proof, until = _origin(v.sign(v.payload), trust=v.trust, principal=v.principal,
        expected=v.expected, now=v.now)
    assert scope == "isolated-fixture" and proof == digest(v.payload) and until == v.now+10


@pytest.mark.parametrize("field", ["config_digest", "case_digest", "run_id", "run_attempt",
    "phase_provenance_digest", "generation_digest", "issuance_digest", "plan_digest", "scope", "principal_ref"])
def test_each_operator_origin_binding_must_match_even_with_a_valid_signature(origin_vector, field):
    from workload_factory_binding_runtime.hosted.qualification import _origin
    v = origin_vector;value = {**v.payload,field:"protected-machine" if field=="scope" else "other"}
    with pytest.raises(BindingError,match="^protected-report-refused$"):
        _origin(v.sign(value),trust=v.trust,principal=v.principal,expected=v.expected,now=v.now)


@pytest.mark.parametrize("kind", ["signature", "wrong-key", "expiry", "future", "boolean", "duplicate", "extra", "dict", "oversize"])
def test_origin_requires_actual_signature_bounded_freshness_and_closed_shape(origin_vector, kind):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from workload_factory_binding_runtime.hosted.qualification import _origin
    v=origin_vector;raw=v.sign(v.payload);trust=v.trust
    if kind=="signature":
        frame=json.loads(raw);frame["signature"]=("A" if frame["signature"][0]!="A" else "B")+frame["signature"][1:];raw=canonical(frame)
    if kind=="wrong-key":trust=replace(trust,public_key=Ed25519PrivateKey.generate().public_key().public_bytes_raw())
    if kind=="expiry":raw=v.sign({**v.payload,"expires_at":v.now})
    if kind=="future":raw=v.sign({**v.payload,"observed_at":v.now+1})
    if kind=="boolean":raw=v.sign({**v.payload,"observed_at":True})
    if kind=="duplicate":raw=raw.replace(b'"scope":"isolated-fixture"',b'"scope":"isolated-fixture","scope":"isolated-fixture"')
    if kind=="extra":raw=v.sign({**v.payload,"live":True})
    if kind=="dict":raw=json.loads(raw)
    if kind=="oversize":raw=b"x"*4097
    with pytest.raises(BindingError,match="^protected-report-refused$"):
        _origin(raw,trust=trust,principal=v.principal,expected=v.expected,now=v.now)


@pytest.mark.parametrize("outcome", ["success", "cancel", "worker-excess"])
def test_portable_qualifier_component_real_proof_barriers_and_cleanup(k, w, tmp_path, outcome):
    """Existing IPC lifecycle component; never substituted for hosted qualification."""
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.custody import TLSClient
    from workload_factory_binding_runtime.hosted.finalization import FinalizedPlan, FinalizationBinding
    from workload_factory_binding_runtime.evidence import _plain
    from .lifecycle_process_fixture import p as portable_fixture
    k.access = replace(k.access, sources_digest=digest(k.c.config["sources"]))
    state = {}
    def prepare(c, create_proof):
        c.h.claims.update(c.config["launch"])
        c.h.policy["claims"].update({n:c.config["launch"][n] for n in c.h.policy["claims"]})
        c.h.reset_evidence();c.reselect_policy()
        fixture = portable_fixture.__wrapped__(c,tmp_path)
        portable = next(fixture);state.update(fixture=fixture,portable=portable)
        life = portable.life
        original_life_run=life.run
        def debug_run(operation):
            def captured():
                try:return operation()
                except BaseException as error:
                    import traceback
                    frames=[{"file":__import__("pathlib").Path(f.filename).name,"line":f.lineno,"function":f.name}
                            for f in traceback.extract_tb(error.__traceback__)]
                    (tmp_path/"component-failure.json").write_text(json.dumps({"type":type(error).__name__,"frames":frames}))
                    raise
            return original_life_run(captured)
        life.run=debug_run
        count = {"lease_reads":1}
        read = life.janitor.target.read_lease
        def counted(*a,**kw):
            count["lease_reads"]+=1
            return read(*a,**kw)
        life.janitor.target.read_lease = counted
        k.access = replace(k.access,config_digest=digest(c.config),sources_digest=digest(c.config["sources"]))
        signer = c.services["custody"].target;signer.runtime_trust=c.trust
        c.bridge=c.make(create_proof=create_proof,lifecycle=life)
        observed=c.bridge.sign_observed
        def sign(*a,**kw):
            value=observed(*a,**kw);state["accepted"]=value
            if outcome=="cancel":raise KeyboardInterrupt("private-cancel-canary")
            return value
        c.bridge.sign_observed=sign
        now=c.h.now;cfg=digest(c.config)
        # A component-only finalization VECTOR, explicitly not real hosted output.
        final=FinalizedPlan(canonical(c.config),canonical(c.h.policy),FinalizationBinding("principal:component-vector",
            digest({"component":"portable"}),c.config["case_ref"],w.context.source_commit,w.context.run_id,
            w.context.run_attempt,digest([asdict(r) for r in life.plan.resources]),digest(c.h.policy),cfg,now,now+10))
        workflow=replace(w.bindings,runtime_trust=c.trust,lifecycle=life,
            read_authorization=lambda ref,deadline:replace(w.authorization,config_digest=cfg),
            read_scheduler=lambda ref,deadline:SchedulerReadback(w.scheduler.principal_ref,
                c.config["lifecycle"]["cleanup_ref"],life.plan.digest,life.readback.identity.principal_ref,now,now+10))
        barriers=BarrierInputs(jwt(c.h.issuer_key,{**c.h.claims,"aud":"negative:audience"}),
            jwt(c.h.issuer_key,{**c.h.claims,"environment":"negative-environment"}))
        worker=TLSClient(k.material.endpoint,ca_file=k.ca,certificate=k.worker[0],private_key=k.worker[1])
        positive=TLSClient(k.material.endpoint,ca_file=k.ca,certificate=k.gate[0],private_key=k.gate[1])
        state["qualifier"]=Qualifier(QualificationBindings(validate_config(c.bridge.load_config(),trust=c.trust),
            final,replace(w.context,config_digest=cfg),workflow,c.bridge,
            Decision(clock=lambda:c.h.now,monotonic=time.monotonic),barriers,WorkerProbe(worker,positive)),
            challenge_id=c.h.challenge.id,request=c.h.request,token=c.h.token,observation=c.h.observation)
        state["count"]=count
    def perform(_run):
        result=state["qualifier"].run()
        state["operation_lease_reads"]=state["count"]["lease_reads"]
        return state["accepted"]
    directory=tmp_path/"owning-component";directory.mkdir(mode=0o700)
    try:
        if outcome=="success":_owning_run(k,directory,before_proof=prepare,perform=perform)
        else:
            with pytest.raises(KeyboardInterrupt if outcome=="cancel" else BindingError):
                _owning_run(k,directory,allow_worker_sign=outcome=="worker-excess",before_proof=prepare,perform=perform)
        result=state["qualifier"].result
        assert result.cleanup is not None and result.outcome=={"success":"success","cancel":"cancel","worker-excess":"failure"}[outcome]
        with pytest.raises(BindingError,match="^protected-report-refused$"):build_receipt(result,now=k.c.h.now)
        value=json.loads(result.fixture_receipt(now=k.c.h.now))
        assert value["scope"]=="isolated-fixture" and not value["protected_machine_qualified"]
        assert "private-cancel-canary" not in json.dumps(value)
        if outcome=="success":
            assert result.proof["status"]=="verified"
            (tmp_path/"component-read-measurement.json").write_text(json.dumps({
                "transport":"accepted portable IPC component, not hosted qualification",
                "lease_reads":state["operation_lease_reads"],
                "private_probe_reads":state["qualifier"].bindings.decision._hosted_reads["counts"]["private"]}))
    finally:
        if "fixture" in state:state["fixture"].close()


@pytest.mark.parametrize("error", [KeyboardInterrupt("private-cancel-canary"),
    SystemExit("private-cancel-canary"), GeneratorExit("private-cancel-canary")])
def test_cli_cancellation_is_fixed_and_never_prints_exception_payload(monkeypatch,tmp_path,capsys,error):
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[2]/"scripts/prepare-protected-runtime.py"
    spec=importlib.util.spec_from_file_location("prepare_protected_runtime_t012t",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(module.subprocess,"run",lambda *a,**kw:SimpleNamespace(stdout="b"*40))
    monkeypatch.setattr(module,"validate_dispatch_context",lambda _context:None)
    def cancel():raise error
    monkeypatch.setattr(module,"operational_bindings",cancel)
    monkeypatch.setattr(module.sys,"argv",[str(path),"--phase","qualify"])
    output=tmp_path/"must-not-exist";monkeypatch.setenv("GITHUB_OUTPUT",str(output))
    assert module.main()==130
    captured=capsys.readouterr()
    assert captured.out=="" and captured.err=="qualification-cancelled\n"
    assert not output.exists()
