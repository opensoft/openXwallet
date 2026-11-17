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


def _connected_hosted_qualification(k, w, request, tmp_path, *, qualified=False, origin=False, fault=None):
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.custody import TLSClient
    k.access = replace(k.access, sources_digest=digest(k.c.config["sources"]))
    retained = {}
    def cancel_here():
        error=KeyboardInterrupt("private-combined-cancel-canary")
        error.add_note("private-combined-cancel-canary")
        retained["original_cancel"]=error
        raise error
    def prepare(c, create_proof):
        c.h.claims.update(c.config["launch"])
        c.h.policy["claims"].update({name: c.config["launch"][name] for name in c.h.policy["claims"]})
        c.h.reset_evidence();c.reselect_policy()
        hosted = request.getfixturevalue("lh")
        retained["hosted"] = hosted
        hosted.launch(full=True);final, plan = hosted.finalize();hosted.takeover()
        wall=[None];shift=[0.]
        decision = Decision(clock=lambda:hosted.clock.value if wall[0] is None else wall[0],
            monotonic=lambda:time.monotonic()+shift[0])
        if qualified:
            from workload_factory_binding_runtime.hosted.readback import start_qualification
            start_qualification(decision)
        life = hosted.runtime(operation=decision)
        original_run = life.run
        def traced_run(operation):
            def traced():
                try:
                    value=operation();retained["operation_finished"]=True;return value
                except BaseException as error:
                    import traceback
                    frames = [{"file": __import__("pathlib").Path(f.filename).name, "line": f.lineno,
                               "function": f.name} for f in traceback.extract_tb(error.__traceback__)]
                    (tmp_path / "qualification-failure.json").write_text(json.dumps({"type": type(error).__name__,
                        "frames": frames}))
                    raise
            retained["life_entered"]=True
            return original_run(traced)
        life.run = traced_run
        if fault in ("cancel-entry-lost","cancel-operation-lost","cancel-closing-lost"):
            original_call=life.janitor.target.primary.call
            def lost_cleanup(operation,**kw):
                value=original_call(operation,**kw)
                if operation=="cleanup":
                    retained["cleanup_mutations"]=retained.get("cleanup_mutations",0)+1
                    raise BindingError("fixture-lost-cleanup-reply")
                return value
            life.janitor.target.primary.call=lost_cleanup
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
        original_lease=debug_operation("lease-read",life.janitor.target.read_lease)
        def lease(*a,**kw):
            inject=(fault=="cancel-entry-lost" and retained.get("life_entered")) or (
                fault=="cancel-closing-lost" and retained.get("operation_finished"))
            if inject and "original_cancel" not in retained:cancel_here()
            return original_lease(*a,**kw)
        life.janitor.target.read_lease=lease
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
            if not retained.get("fault_injected"):
                retained["fault_injected"]=True
                if fault=="runner-death":__import__("os")._exit(23)
                if fault=="cancel-operation-lost":cancel_here()
                if fault=="cancel":raise KeyboardInterrupt("private-hosted-cancel-canary")
                if fault=="failure":raise RuntimeError("private-hosted-failure-canary")
                if fault=="wall-expiry":wall[0]=hosted.clock.value+10
                if fault=="wall-regression":wall[0]=hosted.clock.value-1
                if fault=="monotonic-expiry":shift[0]=20.
                if fault=="monotonic-regression":shift[0]=-100.
                if fault=="read-exhaustion":
                    for _ in range(2):life.janitor.target.read_lease(life.plan.ref,deadline=decision.deadline)
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
        excess = None
        if qualified:
            from factory_binding.test_owner_integration import launch
            from .test_custody import _stop
            control = directory/"excess-control";control.mkdir(mode=0o700);ready=control/"ready"
            process,_=launch("custody",{"owner_code":str(owner_source()),"now":c.h.now,
                "registry_directory":str(directory/"registry"),"key_directory":str(directory/"keys"),
                "ca_file":str(k.ca),"certificate":str(k.server[0]),"private_key":str(k.server[1]),
                "ready":str(ready),"policies":{k.worker[2]:{"actions":["resolve","sign"],
                    "subjects":[c.h.binding.subject_ref]}}},control,wait=False)
            request.addfinalizer(lambda:_stop(process))
            limit=time.monotonic()+10
            while not ready.exists():
                assert process.poll() is None and time.monotonic()<limit
                time.sleep(0.02)
            excess=TLSClient("https://127.0.0.1:"+ready.read_text(),ca_file=k.ca,
                certificate=k.worker[0],private_key=k.worker[1]);excess.context=worker.context
        if fault=="worker-outage":
            from openwallet_runtime.custody import RemoteSigner
            sign=RemoteSigner.sign
            def disconnect_after_available_positive(self,message):
                value=sign(self,message)
                if self.client is positive:worker.port=0  # actual next connection refuses
                return value
            request.getfixturevalue("monkeypatch").setattr(RemoteSigner,"sign",disconnect_after_available_positive)
        if fault=="privacy-failure":
            from workload_factory_binding_runtime.hosted import privacy
            request.getfixturevalue("monkeypatch").setattr(privacy,"safe_error",lambda error:"private-privacy-canary")
        bindings = QualificationBindings(validate_config(final.configuration, trust=c.trust), final, context,
            workflow, c.bridge, life.janitor.target.operation, barrier, WorkerProbe(worker, positive, excess))
        if origin:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from workload_factory_binding.evidence import encode64
            from workload_factory_binding_runtime.hosted import qualification as module
            key=Ed25519PrivateKey.generate()
            observe=module.admit_finalized
            def capture(*a,**kw):
                value=observe(*a,**kw);retained["phase"]=value;return value
            request.getfixturevalue("monkeypatch").setattr(module,"admit_finalized",capture)
            def load(ref,*,deadline):
                assert ref==life.plan.ref
                # Independently verify the fixture token; the origin receives a
                # selected reference, never caller-supplied candidate facts.
                workload=module.IssuerWorkloadVerifier(audience=c.config["issuer"]["audience"],
                    source=c.r.source).verify(c.h.token,dict(c.config["launch"]),now=c.h.now)
                phase_digest=digest({"admission":asdict(retained["phase"]),"finalization":asdict(final.binding),
                    "readback_digest":bindings.selected.readback_digest,"workload_digest":digest(dict(workload.claims))})
                payload={"config_digest":bindings.selected.config_digest,"case_digest":digest(c.config["case_ref"]),
                    "run_id":context.run_id,"run_attempt":context.run_attempt,"phase_provenance_digest":phase_digest,
                    "generation_digest":final.binding.generation_digest,"issuance_digest":digest(asdict(k.access)),
                    "plan_digest":life.plan.digest,"principal_ref":workflow.runtime_trust.readback_principal,
                    "scope":"isolated-fixture","observed_at":c.h.now,"expires_at":c.h.now+10}
                if fault=="origin-mismatch":payload["run_id"]="999"
                return canonical({"payload":payload,"signature":encode64(key.sign(module.ORIGIN_CONTEXT+canonical(payload)))})
            bindings=replace(bindings,origin=module.OriginTrust(workflow.runtime_trust.readback_principal,
                key.public_key().public_bytes_raw(),"isolated-fixture",load))
        retained["qualifier"] = Qualifier(bindings, challenge_id=c.h.challenge.id, request=c.h.request,
            token=c.h.token, observation=c.h.observation)
    def perform(_run):
        qualifier = retained["qualifier"]
        if fault=="runner-death":
            import multiprocessing
            from workload_factory_binding_runtime.hosted.lifecycle import process_instance
            process=multiprocessing.get_context("fork").Process(target=qualifier.run)
            process.start()
            instance=process_instance(process.pid)[0]
            assert instance is not None
            (tmp_path/"runner-generation.json").write_bytes(canonical({"pid":process.pid,"instance_ref":instance}))
            try:
                process.join(timeout=15)
                assert process.exitcode==23
            finally:
                if process.is_alive():process.kill();process.join(timeout=5)
            hosted=retained["hosted"]
            original=hosted.life.state(decision=hosted.use())
            hosted.advance(original["registration"]["expires_at"]+1)
            end=time.monotonic()+8
            while time.monotonic()<end:
                try:
                    observed=hosted.audit().call("cleanup-audit",attempt_ref="cleanup-attempt:qualification-death",decision=hosted.use())
                    if observed["kind"]=="final":break
                except BindingError:pass
                time.sleep(.05)
            else:pytest.fail("independent original-scope cleanup not observed")
            retained["death_cleanup"]=qualifier.reconcile_cleanup()
            raise BindingError("fixture-runner-death")
        result = qualifier.run()
        retained["result"] = result
        retained["operation_private_reads"] = qualifier.bindings.decision._hosted_reads["counts"]["private"]
        return retained["accepted"]
    directory = tmp_path / "owning-connected";directory.mkdir(mode=0o700)
    def execute():
        return _owning_run(k, directory, before_proof=prepare, perform=perform)
    return execute, retained


def test_connected_hosted_proof_refuses_at_original_private_read_cap_and_cleans_up(k, w, request, tmp_path):
    execute, retained = _connected_hosted_qualification(k,w,request,tmp_path)
    with pytest.raises(BindingError, match="^qualification-failed$"):
        execute()
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


def test_source_accepted_hosted_qualification_completes_on_one_original_decision(k,w,request,tmp_path):
    execute, state = _connected_hosted_qualification(k,w,request,tmp_path,qualified=True)
    execute()
    qualifier=state["qualifier"];result=qualifier.result
    assert result.outcome=="success" and result.proof["status"]=="verified" and result.cleanup is not None
    decision=qualifier.bindings.decision
    assert decision is qualifier.bindings.workflow.lifecycle.janitor.target.operation
    assert decision._hosted_reads["qualification"] is True
    assert len(decision._hosted_reads["members"])==1
    assert state["operation_private_reads"]==38
    assert decision._hosted_reads["counts"]["private"]==39  # helper closed-lease negative follows the measured operation
    assert not state["hosted"].temporary.exists()
    assert state["hosted"].shared.read_bytes()==b"retained shared generation"
    with pytest.raises(BindingError,match="^protected-report-refused$"):build_receipt(result,now=k.c.h.now)
    (tmp_path/"hosted-qualification-measurement.json").write_text(json.dumps({
        "scope":"isolated-source","private_reads":state["operation_private_reads"],"operation_outcome":result.outcome,
        "proof_status":result.proof["status"],"independent_cleanup_verified":True}))


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


@pytest.mark.parametrize("outcome", ["success", "missing-excess", "cancel", "cancel-entry", "cancel-close", "worker-excess"])
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
                try:
                    value=operation();state["operation_finished"]=True;return value
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
            if (outcome=="cancel-entry" or (outcome=="cancel-close" and state.get("operation_finished"))) and not state.get("cancelled"):
                state["cancelled"]=True
                raise KeyboardInterrupt("private-cancel-canary")
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
        excess = None
        if outcome != "missing-excess":
            # Disposable source-only counterfactual; no existing service policy is mutated.
            from factory_binding.test_owner_integration import launch
            from .test_custody import _stop
            control_dir=directory/"excess-control";control_dir.mkdir(mode=0o700)
            ready=control_dir/"ready"
            process,_=launch("custody",{"owner_code":str(owner_source()),"now":c.h.now,
                "registry_directory":str(directory/"registry"),"key_directory":str(directory/"keys"),
                "ca_file":str(k.ca),"certificate":str(k.server[0]),"private_key":str(k.server[1]),
                "ready":str(ready),"policies":{k.worker[2]:{"actions":["resolve","sign"],
                    "subjects":[c.h.binding.subject_ref]}}},control_dir,wait=False)
            state["excess_process"]=process
            limit=time.monotonic()+10
            while not ready.exists():
                assert process.poll() is None and time.monotonic()<limit
                time.sleep(0.02)
            excess=TLSClient("https://127.0.0.1:"+ready.read_text(),ca_file=k.ca,
                certificate=k.worker[0],private_key=k.worker[1])
            excess.context=worker.context
        state["qualifier"]=Qualifier(QualificationBindings(validate_config(c.bridge.load_config(),trust=c.trust),
            final,replace(w.context,config_digest=cfg),workflow,c.bridge,
            Decision(clock=lambda:c.h.now,monotonic=time.monotonic),barriers,WorkerProbe(worker,positive,excess)),
            challenge_id=c.h.challenge.id,request=c.h.request,token=c.h.token,observation=c.h.observation)
        state["count"]=count
    def perform(_run):
        result=state["qualifier"].run()
        state["operation_lease_reads"]=state["count"]["lease_reads"]
        return state["accepted"]
    directory=tmp_path/"owning-component";directory.mkdir(mode=0o700)
    try:
        if outcome in ("success","missing-excess"):_owning_run(k,directory,before_proof=prepare,perform=perform)
        else:
            with pytest.raises(KeyboardInterrupt if outcome.startswith("cancel") else BindingError):
                _owning_run(k,directory,allow_worker_sign=outcome=="worker-excess",before_proof=prepare,perform=perform)
        result=state["qualifier"].result
        assert result.cleanup is not None and result.outcome==("cancel" if outcome.startswith("cancel") else "failure" if outcome=="worker-excess" else "success")
        with pytest.raises(BindingError,match="^protected-report-refused$"):build_receipt(result,now=k.c.h.now)
        value=json.loads(result.fixture_receipt(now=k.c.h.now))
        assert value["scope"]=="isolated-fixture" and not value["protected_machine_qualified"]
        assert "private-cancel-canary" not in json.dumps(value)
        assert not {"G01","G02","S01",*("H%02d"%n for n in range(1,10))} & {x.case_id for x in result.cases}
        if outcome=="missing-excess":
            assert result.proof["status"]=="not-performed"
            assert not {"G03","H10"} & {x.case_id for x in result.cases}
        if outcome=="success":
            assert result.proof["status"]=="verified"
            (tmp_path/"component-read-measurement.json").write_text(json.dumps({
                "transport":"accepted portable IPC component, not hosted qualification",
                "lease_reads":state["operation_lease_reads"],
                "private_probe_reads":state["qualifier"].bindings.decision._hosted_reads["counts"]["private"]}))
    finally:
        if "excess_process" in state:
            from .test_custody import _stop
            _stop(state["excess_process"])
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


@pytest.mark.parametrize("mode", ["normal", "lost-response", "stale-audit"])
def test_fresh_hosted_cleanup_audit_reads_original_window_without_mutation(lh, mode):
    from concurrent.futures import ThreadPoolExecutor
    from secrets import token_hex
    from workload_factory_binding_runtime.hosted.lifecycle_service import FinalLifecyclePorts
    lh.launch();lh.finalize();lh.takeover()
    runtime=lh.runtime()
    if mode=="lost-response":
        original=runtime.janitor.target.primary.call
        def lost(operation,**kw):
            value=original(operation,**kw)
            if operation=="cleanup":raise BindingError("private-lost-response")
            return value
        runtime.janitor.target.primary.call=lost
        with pytest.raises(BindingError):runtime.run(lambda:None)
    else:runtime.run(lambda:None)
    old=runtime.janitor.target
    before=len([x for x in lh.stores["primary"].events(decision=lh.use()) if x["kind"]=="cleanup-request"])
    if mode=="stale-audit":
        (lh.stores["audit"].directory/"lifecycle.sqlite").write_bytes(b"corrupt")
    fresh=FinalLifecyclePorts(primary=old.primary,audit=old.audit,operation=old.operation,
        plan_ref=old.plan_ref,clock=old.clock,monotonic=old.monotonic)
    def read():
        attempt="cleanup-attempt:"+token_hex(16)
        now=runtime.cleanup_clock()
        record=fresh.audit_cleanup(runtime.plan.ref,attempt_ref=attempt,
            deadline=min(now+runtime.plan.cleanup_timeout,runtime.plan.expires_at+runtime.plan.cleanup_timeout))
        runtime._verify_cleanup(record,now,runtime.cleanup_clock(),attempt)
        return record
    with ThreadPoolExecutor(max_workers=1) as executor:
        future=executor.submit(read)
        if mode=="stale-audit":
            with pytest.raises(BindingError):future.result(timeout=10)
        else:assert future.result(timeout=10).lease_status in ("closed","revoked","cancelled")
    after=len([x for x in lh.stores["primary"].events(decision=lh.use()) if x["kind"]=="cleanup-request"])
    assert before==after


@pytest.mark.parametrize("entry,limit", [("ordinary",12),("staging",16),("finalization",12),("qualification",39)])
def test_accepted_qualification_cap_keeps_other_phase_private_bounds(entry,limit):
    from workload_factory_binding_runtime.hosted.readback import (ReadBudget,start_qualification,start_staging,start_finalization)
    d=Decision(clock=lambda:1000,monotonic=lambda:0.)
    if entry!="ordinary":locals()["start_"+entry](d)
    b=ReadBudget(d)
    for _ in range(limit):b.consume("private")
    assert b.count("private")==limit
    with pytest.raises(BindingError):b.consume("private")
    assert b.count("private")==limit


@pytest.mark.parametrize("used", ["ordinary","staging","finalization","qualification","correlation"])
def test_qualification_entry_cannot_upgrade_used_phase_or_correlation(used):
    from workload_factory_binding_runtime.hosted.readback import (ReadBudget,start_qualification,start_staging,start_finalization)
    d=Decision(clock=lambda:1000,monotonic=lambda:0.)
    if used=="ordinary":ReadBudget(d).consume("private")
    elif used=="correlation":d.api_requests=1
    else:locals()["start_"+used](d)
    before=getattr(d,"_hosted_reads",None)
    with pytest.raises(BindingError):start_qualification(d)
    assert getattr(d,"_hosted_reads",None) is before


@pytest.mark.parametrize("mode", ["join","wall-expiry","monotonic-expiry","wall-regression","monotonic-regression","earliest-expiry","protection","correlation"])
def test_qualification_does_not_enlarge_other_authority_or_clocks(mode):
    from workload_factory_binding_runtime.hosted.readback import ReadBudget,start_qualification
    wall=[1000];mono=[10.]
    d=Decision(clock=lambda:wall[0],monotonic=lambda:mono[0]);start_qualification(d);b=ReadBudget(d)
    if mode=="join":
        with pytest.raises(BindingError):b.join(Decision(clock=lambda:1000,monotonic=lambda:10.))
        assert len(b.state["members"])==1
        return
    if mode=="protection":
        for _ in range(3):b.consume("protection")
        with pytest.raises(BindingError):b.consume("protection")
        return
    if mode=="correlation":
        for _ in range(4):b.consume_correlation()
        with pytest.raises(BindingError):b.consume_correlation()
        return
    if mode=="earliest-expiry":d.clip(1002);wall[0]=1002
    elif mode=="wall-expiry":wall[0]=1010
    elif mode=="monotonic-expiry":mono[0]=20.
    elif mode=="wall-regression":wall[0]=999
    elif mode=="monotonic-regression":mono[0]=9.
    with pytest.raises(BindingError):b.consume("private")
    assert b.state["counts"]["private"]==0


@pytest.mark.parametrize("mutation", ["raw-error", "wrong-safe-code", "private-projection"])
def test_privacy_observation_requires_actual_independent_controls(vector,monkeypatch,mutation):
    from workload_factory_binding_runtime.hosted import privacy
    projection={"config_digest":vector["selected"].config_digest,"proof":vector["proof"],"cleanup_digest":None}
    assert privacy.observe_privacy(projection).startswith("sha256:")
    if mutation=="raw-error":monkeypatch.setattr(privacy,"safe_error",lambda error:error.args[0])
    elif mutation=="wrong-safe-code":monkeypatch.setattr(privacy,"safe_error",lambda error:"qualification-failed")
    else:projection["proof"]={**projection["proof"],"private_token":"private-canary"}
    with pytest.raises(BindingError,match="^protected-report-refused$"):privacy.observe_privacy(projection)


@pytest.mark.parametrize("kind", ["audience","environment"])
def test_signed_claim_barrier_detects_independent_removed_check(c,monkeypatch,kind):
    from workload_factory_binding_runtime.issuer import IssuerWorkloadVerifier
    from workload_factory_binding.evidence import decode64,decode_object
    c.run();selected=validate_config(c.bridge.load_config(),trust=c.trust)
    field="aud" if kind=="audience" else "environment"
    token=jwt(c.h.issuer_key,{**c.h.claims,field:"independent-negative"})
    inputs=(c.h.challenge.id,c.h.request,c.h.token,c.h.observation)
    assert _barrier(token,kind,c.bridge,c.h.now,selected,inputs).startswith("sha256:")
    original=IssuerWorkloadVerifier.verify
    def removed(self,token,expected,*,now):
        claims=decode_object(decode64(token.split(".")[1]))
        if kind=="audience":
            return original(IssuerWorkloadVerifier(audience=claims["aud"],source=self._source),token,expected,now=now)
        return original(self,token,{**expected,"environment":claims["environment"]},now=now)
    monkeypatch.setattr(IssuerWorkloadVerifier,"verify",removed)
    with pytest.raises(BindingError,match="^qualification-failed$"):_barrier(token,kind,c.bridge,c.h.now,selected,inputs)


def test_connected_authenticated_fixture_origin_uses_last_read_without_live_promotion(k,w,request,tmp_path):
    execute,state=_connected_hosted_qualification(k,w,request,tmp_path,qualified=True,origin=True)
    execute();result=state["qualifier"].result
    assert result.outcome=="success" and result.proof["status"]=="verified" and result.cleanup is not None
    assert state["operation_private_reads"]==39
    assert {x.case_id:x.status for x in result.cases}["H12"]=="passed"
    assert result._operational_origin is None
    with pytest.raises(BindingError,match="^protected-report-refused$"):build_receipt(result,now=k.c.h.now)


@pytest.mark.parametrize("fault", ["failure","cancel","read-exhaustion","wall-expiry","wall-regression",
    "monotonic-expiry","monotonic-regression","origin-mismatch","worker-outage","privacy-failure"])
def test_connected_qualification_faults_keep_original_cleanup_and_cannot_report_success(k,w,request,tmp_path,fault):
    execute,state=_connected_hosted_qualification(k,w,request,tmp_path,qualified=True,
        origin=fault=="origin-mismatch",fault=fault)
    with pytest.raises(KeyboardInterrupt if fault=="cancel" else BindingError):execute()
    q=state["qualifier"];result=q.result
    assert result is not None and result.cleanup is not None
    assert result.outcome==("cancel" if fault=="cancel" else "failure")
    assert q.bindings.decision._hosted_reads["counts"]["private"]<=39
    if fault=="worker-outage":assert not {"G03","H10"} & {c.case_id for c in result.cases}
    if fault=="privacy-failure":assert {c.case_id:c.status for c in result.cases}["H12"]=="failed"
    if fault=="read-exhaustion":assert q.bindings.decision._hosted_reads["counts"]["private"]==39
    if fault=="origin-mismatch":assert q.bindings.decision._hosted_reads["counts"]["private"]==38  # failed origin skips closing lease read
    assert not state["hosted"].temporary.exists()
    assert state["hosted"].shared.read_bytes()==b"retained shared generation"
    with pytest.raises(BindingError,match="^protected-report-refused$"):build_receipt(result,now=k.c.h.now)


@pytest.mark.parametrize("kind", ["runtime","binding","interrupt","exit","generator"])
def test_actual_cli_redacts_private_args_notes_causes_and_context(monkeypatch,tmp_path,capsys,kind):
    import importlib.util
    from pathlib import Path
    canary="private-token-PEM-provider-proof-challenge-path-canary"
    errors={"runtime":RuntimeError,"binding":BindingError,"interrupt":KeyboardInterrupt,"exit":SystemExit,"generator":GeneratorExit}
    error=errors[kind](canary);error.add_note(canary);error.__cause__=ValueError(canary);error.__context__=ValueError(canary)
    path=Path(__file__).resolve().parents[2]/"scripts/prepare-protected-runtime.py"
    spec=importlib.util.spec_from_file_location("prepare_protected_runtime_privacy",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(module.subprocess,"run",lambda *a,**kw:SimpleNamespace(stdout="b"*40))
    monkeypatch.setattr(module,"validate_dispatch_context",lambda context:None)
    def fail():raise error
    monkeypatch.setattr(module,"operational_bindings",fail)
    monkeypatch.setattr(module.sys,"argv",[str(path),"--phase","qualify"])
    assert module.main()==(2 if isinstance(error,Exception) else 130)
    value=capsys.readouterr();assert value.out==""
    assert value.err==("qualification-failed\n" if isinstance(error,Exception) else "qualification-cancelled\n")


def test_actual_qualifier_runner_death_keeps_independent_original_cleanup(k,w,request,tmp_path):
    execute,state=_connected_hosted_qualification(k,w,request,tmp_path,qualified=True,fault="runner-death")
    with pytest.raises(BindingError,match="^fixture-runner-death$"):execute()
    q=state["qualifier"];hosted=state["hosted"]
    assert q.result is None and state["death_cleanup"].plan_digest==q.bindings.workflow.lifecycle.plan.digest
    assert not hosted.temporary.exists() and hosted.shared.read_bytes()==b"retained shared generation"
    assert not hosted.provider.active[hosted.token.credential]
    assert sum(e["kind"]=="cleanup-request" for e in hosted.stores["scheduler"].events(decision=hosted.use()))==1
    with pytest.raises(BindingError,match="^protected-report-refused$"):build_receipt(q.result,now=hosted.clock.value)


def test_reconciliation_refuses_after_original_registered_cleanup_window(k,w,request,tmp_path):
    execute,state=_connected_hosted_qualification(k,w,request,tmp_path,qualified=True)
    execute();q=state["qualifier"];hosted=state["hosted"]
    registered=hosted.life.state(decision=hosted.use())["registration"]
    before=sum(e["kind"]=="lease-closed" for e in hosted.stores["primary"].events(decision=hosted.use()))
    hosted.advance(registered["cleanup_until"])
    with pytest.raises(BindingError,match="^lifecycle-cleanup-unverified$"):q.reconcile_cleanup()
    after=sum(e["kind"]=="lease-closed" for e in hosted.stores["primary"].events(decision=hosted.use()))
    assert before==after==1
    assert not hosted.temporary.exists() and hosted.shared.read_bytes()==b"retained shared generation"


@pytest.mark.parametrize("kind", ["invalid-phase","unknown-argument","missing-phase"])
def test_cli_parse_failure_never_echoes_private_input_or_reads_context(monkeypatch,tmp_path,capsys,kind):
    import importlib.util
    from pathlib import Path
    canary="private-token-proof-PEM-path-input-canary"
    path=Path(__file__).resolve().parents[2]/"scripts/prepare-protected-runtime.py"
    spec=importlib.util.spec_from_file_location("prepare_protected_runtime_parse",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    arguments={"invalid-phase":["--phase",canary],"unknown-argument":["--phase","qualify","--token",canary],"missing-phase":["--token",canary]}
    monkeypatch.setattr(module.sys,"argv",[str(path),*arguments[kind]])
    def unexpected(*a,**kw):pytest.fail("parse failure read context or selected operational bindings")
    monkeypatch.setattr(module.subprocess,"run",unexpected)
    monkeypatch.setattr(module,"operational_bindings",unexpected)
    output=tmp_path/"never-created";monkeypatch.setenv("GITHUB_OUTPUT",str(output))
    assert module.main()==2
    result=capsys.readouterr()
    assert result.out=="" and result.err=="workflow-input-unavailable\n"
    assert canary not in result.err and not output.exists()


@pytest.mark.parametrize("kind", ["interrupt","exit","generator"])
def test_cli_parse_cancellation_redacts_private_payload_before_context(monkeypatch,capsys,kind):
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[2]/"scripts/prepare-protected-runtime.py"
    spec=importlib.util.spec_from_file_location("prepare_protected_runtime_parse_cancel",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    error={"interrupt":KeyboardInterrupt,"exit":SystemExit,"generator":GeneratorExit}[kind]("private-parse-cancel-canary")
    error.add_note("private-parse-cancel-canary")
    def cancel(*a,**kw):raise error
    monkeypatch.setattr(module._PrivateParser,"parse_args",cancel)
    assert module.main()==130
    value=capsys.readouterr();assert value.out=="" and value.err=="qualification-cancelled\n"


@pytest.mark.parametrize("mode", ["fresh-process","wrong-run","worker-credential","expired","qualify-refused"])
def test_fresh_audit_only_workflow_needs_no_active_lease_or_writer(k,w,request,tmp_path,mode):
    from dataclasses import fields
    from workload_factory_binding_runtime.bootstrap import DispatchContext
    from workload_factory_binding_runtime.hosted.qualification import RegisteredCleanupClient
    from workload_factory_binding_runtime.hosted.lifecycle import process_instance
    from workload_factory_binding_runtime.workflow import QualificationWorkflowBindings,qualify_hosted
    execute,state=_connected_hosted_qualification(k,w,request,tmp_path,qualified=True)
    execute();q=state["qualifier"];hosted=state["hosted"];life=q.bindings.workflow.lifecycle
    original=hosted.life.state(decision=hosted.use())["registration"]
    # The final lease and proof configuration are expired. Only the original
    # registered cleanup window and selected observer credentials remain usable.
    hosted.advance(original["cleanup_until"] if mode=="expired" else original["expires_at"]+1)
    before=sum(e["kind"]=="lease-closed" for e in hosted.stores["primary"].events(decision=hosted.use()))
    context=q.bindings.context
    if mode=="wrong-run":context=replace(context,run_id="999")
    def new_client():
        return RegisteredCleanupClient(context=context,plan=life.plan,
            audit=hosted.audit("worker" if mode=="worker-credential" else "observer"),
            identity=life.readback.identity,clock=lambda:hosted.clock.value,monotonic=time.monotonic)
    incoming=DispatchContext(**{f.name:getattr(q.bindings.context,f.name) if hasattr(q.bindings.context,f.name)
        else getattr(hosted.stage.v.context,f.name) for f in fields(DispatchContext)})
    def read():return qualify_hosted(incoming,bindings=QualificationWorkflowBindings(new_client()),
        phase="qualify" if mode=="qualify-refused" else "cleanup")
    if mode=="fresh-process":
        import os,subprocess,sys
        from pathlib import Path
        from factory_binding.test_owner_integration import private_write
        from .test_custody import _stop
        audit=hosted.audit("observer");transport=audit.transport
        selected=tmp_path/"selected-audit-only.json"
        private_write(selected,canonical({"plan":asdict(life.plan),"context":asdict(context),
            "dispatch":asdict(incoming),"identity":asdict(life.readback.identity),"now":hosted.clock.value,
            "audit":{"origin":audit.origin,"principal":audit.principal,"scope":document(audit.raw),
                "ca":transport.ca,"certificate":transport.cert,"key":transport.key,
                "server_certificate_digest":transport.server_certificate_digest}}))
        process=subprocess.Popen([sys.executable,"-I","-B",str(Path(__file__).with_name("cleanup_observer.py")),str(selected)],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={"PATH":os.defpath,"LANG":"C.UTF-8"})
        instance=process_instance(process.pid)[0];assert instance is not None
        (tmp_path/"runner-generation.json").write_bytes(canonical({"pid":process.pid,"instance_ref":instance}))
        try:
            output,errors=process.communicate(timeout=15)
            assert process.returncode==0 and errors==b""
            assert json.loads(output)=={"verified":True,"outcome":"cancel"}
        finally:_stop(process)
    else:
        with pytest.raises(BindingError):read()
    after=sum(e["kind"]=="lease-closed" for e in hosted.stores["primary"].events(decision=hosted.use()))
    assert before==after==1
    assert not hosted.temporary.exists() and hosted.shared.read_bytes()==b"retained shared generation"


@pytest.mark.parametrize("fault", ["cancel-entry-lost","cancel-operation-lost","cancel-closing-lost"])
def test_original_cancellation_survives_lost_cleanup_reply_and_read_only_reconciliation(k,w,request,tmp_path,fault):
    execute,state=_connected_hosted_qualification(k,w,request,tmp_path,qualified=True,fault=fault)
    with pytest.raises(KeyboardInterrupt) as caught:execute()
    assert caught.value is state["original_cancel"]
    q=state["qualifier"];result=q.result
    assert result.outcome=="cancel" and result.cleanup is None
    assert state["cleanup_mutations"]==1
    checked=q.reconcile_cleanup()
    assert checked.plan_digest==q.bindings.workflow.lifecycle.plan.digest and checked.outcome=="cancel"
    assert state["cleanup_mutations"]==1
    assert not state["hosted"].temporary.exists()
    assert state["hosted"].shared.read_bytes()==b"retained shared generation"
    with pytest.raises(BindingError,match="^protected-report-refused$"):build_receipt(result,now=k.c.h.now)


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, GeneratorExit])
@pytest.mark.parametrize("clock_fault", ["raises", "before-operation", "before-cleanup"])
def test_original_cancellation_survives_post_cleanup_clock_failure(k, w, request, tmp_path, monkeypatch, error_type, clock_fault):
    from workload_factory_binding_runtime.lifecycle import RunLifecycle
    execute, state = _connected_hosted_qualification(k, w, request, tmp_path, qualified=True)
    original_cancel = error_type("private-post-cleanup-cancel-canary")
    original_cancel.add_note("private-post-cleanup-cancel-canary")
    original_run = RunLifecycle.run
    def instrumented_run(life, operation):
        qualifier = state.get("qualifier")
        if qualifier is None or life is not qualifier.bindings.workflow.lifecycle:
            return original_run(life, operation)
        floor = qualifier.bindings.decision.last
        def cancel_operation():
            hosted = state["hosted"]
            hosted.advance(hosted.clock.value + 1)
            raise original_cancel
        try:
            return original_run(life, cancel_operation)
        except BaseException as error:
            assert error is original_cancel
            cleanup = life.cleanup_verification
            assert cleanup is not None and cleanup.outcome == "cancel" and cleanup.checked_at > floor
            state["verified_cleanup"] = cleanup
            def broken_historical_clock():
                state["historical_clock_sampled"] = True
                if clock_fault == "raises":
                    raise RuntimeError("private-post-cleanup-clock-canary")
                return floor - 1 if clock_fault == "before-operation" else cleanup.checked_at - 1
            monkeypatch.setattr(life, "cleanup_clock", broken_historical_clock)
            raise
    monkeypatch.setattr(RunLifecycle, "run", instrumented_run)
    with pytest.raises(error_type) as caught:
        execute()
    assert caught.value is original_cancel
    qualifier, hosted = state["qualifier"], state["hosted"]
    assert state["historical_clock_sampled"] and qualifier.result is None
    assert state["verified_cleanup"].plan_digest == qualifier.bindings.workflow.lifecycle.plan.digest
    assert not hosted.temporary.exists() and hosted.shared.read_bytes() == b"retained shared generation"
    assert not hosted.provider.active[hosted.token.credential]
    with pytest.raises(BindingError, match="^protected-report-refused$"):
        build_receipt(qualifier.result, now=hosted.clock.value)
