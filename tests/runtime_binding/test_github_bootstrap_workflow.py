"""Opt-in phase admission and owning proof/cleanup; all provider observations synthetic."""
from copy import deepcopy
from dataclasses import asdict, replace
import importlib.util
import multiprocessing
import os
from pathlib import Path
import sqlite3
import time
from types import SimpleNamespace
import pytest
from workload_factory_binding.evidence import BindingError, canonical, digest
from workload_factory_binding_runtime.bootstrap import BootstrapReadback, bootstrap, selection_document
from workload_factory_binding_runtime.workflow import (GithubWorkflowBindings, SchedulerReadback, OperationReadback,
    admit_github, operational_bindings)
from workload_factory_binding_runtime.github_bootstrap import ERROR, PROFILE
from workload_factory_binding_runtime.github_bootstrap.client import TokenClient
from workload_factory_binding_runtime.github_bootstrap.common import document
from workload_factory_binding_runtime.github_bootstrap.https import Response
from workload_factory_binding_runtime.github_bootstrap.journal import DATABASE
from workload_factory_binding_runtime.github_bootstrap.session import ControllerEndpoint, ReadinessClient, Session
from .test_github_bootstrap_correlation import (g, configuration, c, l, w, dispatch, row, ROOT)
from .test_github_bootstrap_identity import TokenTransport
from .custody_fixture import k
from .lifecycle_process_fixture import p
from .test_custody import _owning_run
from .test_lifecycle_process import assert_removed


def materialize(g, correlated, *, deadline):
    config, context = g.approval.configuration, g.context
    config["launch"].update(run_id=context.run_id, run_attempt=context.run_attempt)
    bound = BootstrapReadback("principal:bootstrap", context.preauthorization_ref, context.selection_digest,
        context.accepted_commit, context.repository_id, config["case_ref"], context.run_id,
        context.run_attempt, digest(config), "grant:github-operation", g.now, correlated.valid_until)
    operation = OperationReadback("principal:operation-reader", bound.operation_grant_ref, "qualify-existing-resources",
        digest(config), context.accepted_commit, config["case_ref"], context.run_id, context.run_attempt, g.now, correlated.valid_until)
    return {"profile": PROFILE, "configuration": config, "bootstrap": asdict(bound), "operation": asdict(operation)}

class ControllerTransport:
    def __init__(self, endpoint): self.endpoint, self.calls, self.hook = endpoint, [], None
    def exchange(self, method, url, *, body, decision, **kwargs):
        self.calls.append((method, url))
        if self.hook: self.hook()
        return Response(200, self.endpoint.handle(body, deadline=decision.deadline))


def clients(g):
    result = []
    for phase in ("preflight", "protected"):
        endpoint = ControllerEndpoint(controller=g.controller(phase),
            materialize=lambda correlated, deadline: materialize(g, correlated, deadline=deadline), clock=lambda: g.now,
            bootstrap_principal="principal:bootstrap", operation_principal="principal:operation-reader")
        transport = ControllerTransport(endpoint)
        token = TokenTransport(g.token(phase))
        client = ReadinessClient(endpoint="https://controller.invalid/" + phase,
            token_client=TokenClient(endpoint="https://job.invalid/idtoken", audience=g.approval.policy("789", phase).audience,
                                     transport=token), clock=lambda: g.now, transport=transport)
        result.append((client, transport, token, endpoint))
    return result


def bindings(g, workflow=None):
    pairs = clients(g)
    return GithubWorkflowBindings(workflow or g.w.bindings, pairs[0][0], pairs[1][0],
        "principal:bootstrap", "principal:operation-reader"), pairs

ENV = {"ACTIONS_ID_TOKEN_REQUEST_URL": "https://job.invalid/idtoken", "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fixture-request-capability"}


def test_opt_in_admission_uses_distinct_intrinsic_phase_routes_and_fresh_authority(g):
    dispatch(g)
    selected, pairs = bindings(g)
    assert admit_github(g.context, bindings=selected, phase="preflight", environment=ENV).run_id == "789"
    assert pairs[0][1].calls
    assert not pairs[1][1].calls
    assert admit_github(g.context, bindings=selected, phase="protected-admission", environment=ENV).run_id == "789"
    assert pairs[1][1].calls
    assert g.w.c.h.calls == 0
    # A still-valid identity is never sufficient after current operator revocation.
    g.approval = replace(g.approval, revoked=True)
    with pytest.raises(BindingError): admit_github(g.context, bindings=selected, phase="preflight", environment=ENV)

@pytest.mark.parametrize("change", ["wrong-phase-token", "worker-token", "controller-outage", "late-revoke", "wrong-context", "wrong-profile", "extra-field"])
def test_controller_client_refuses_without_any_proof_or_environment_output(g, change):
    dispatch(g);selected, pairs = bindings(g)
    client, transport, token, endpoint = pairs[0]
    if change == "wrong-phase-token": token.response = Response(200, canonical({"value": g.token("protected")}))
    elif change == "worker-token": token.response = Response(200, canonical({"value": g.token(job_workflow_ref="opensoft/openXwallet/.github/workflows/worker.yml@refs/heads/main")}))
    elif change == "controller-outage":
        def fail(): raise OSError("provider-private-canary")
        transport.hook = fail
    elif change == "late-revoke":
        original = endpoint.materialize
        def revoke(correlated, deadline):
            value = original(correlated, deadline=deadline);g.approval = replace(g.approval, revoked=True);return value
        endpoint.materialize = revoke
    else:
        original = endpoint.materialize
        def changed(correlated, deadline):
            value = original(correlated, deadline=deadline)
            if change == "wrong-context": value["bootstrap"]["run_id"] = "999"
            elif change == "wrong-profile": value["profile"] = "fixture-profile"
            else: value["raw_token"] = "private-canary"
            return value
        endpoint.materialize = changed
    with pytest.raises(BindingError): admit_github(g.context, bindings=selected, phase="preflight", environment=ENV)
    assert g.w.c.h.calls == 0

@pytest.mark.parametrize("phase", ["qualify", "cleanup", "worker", ""])
def test_no_phase_flag_or_shared_route_can_select_an_operational_host(g, phase):
    selected, _ = bindings(g)
    with pytest.raises(BindingError): admit_github(g.context, bindings=selected, phase=phase, environment=ENV)
    selected = replace(selected, protected_client=selected.preflight_client)
    with pytest.raises(BindingError): admit_github(g.context, bindings=selected, phase="preflight", environment=ENV)
    with pytest.raises(BindingError, match="^workflow-operational-host-unselected$"): operational_bindings()


def test_actual_cli_new_protected_phase_still_refuses_before_token_access(tmp_path):
    import subprocess, sys
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    output = tmp_path / "outputs"
    env = dict(os.environ, GITHUB_REPOSITORY="opensoft/openXwallet", GITHUB_REPOSITORY_ID="123", GITHUB_EVENT_NAME="workflow_dispatch",
        GITHUB_REF="refs/heads/main", GITHUB_SHA=head, GITHUB_WORKFLOW_REF="opensoft/openXwallet/.github/workflows/protected-runtime-qualification.yml@refs/heads/main",
        GITHUB_WORKFLOW_SHA=head, GITHUB_RUN_ID="789", GITHUB_RUN_ATTEMPT="1", OPENXWALLET_ACCEPTED_COMMIT=head,
        OPENXWALLET_SELECTION_DIGEST="sha256:" + "a" * 64, OPENXWALLET_PREAUTHORIZATION_REF="grant:fixture", GITHUB_OUTPUT=str(output),
        ACTIONS_ID_TOKEN_REQUEST_URL="https://127.0.0.1:9/forbidden", ACTIONS_ID_TOKEN_REQUEST_TOKEN="private-capability-canary")
    result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "scripts/prepare-protected-runtime.py"), "--phase", "protected-admission"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() == "workflow-operational-host-unselected"
    assert not output.exists()


def test_internal_controller_handler_is_closed_and_cannot_select_its_phase(g):
    dispatch(g);_, pairs = bindings(g);endpoint = pairs[0][3]
    valid = {"profile": PROFILE, "context": asdict(g.context), "token": g.token()}
    for value in (dict(valid, phase="protected"), dict(valid, profile="other"), dict(valid, context={}), dict(valid, token="invalid")):
        with pytest.raises(BindingError, match="^" + ERROR + "$"): endpoint.handle(canonical(value), deadline=g.now + 10)


@pytest.mark.parametrize("outcome", ["success", "failure", "cancel", "hard-exit"])
def test_github_correlated_owning_proof_replay_and_independent_cleanup(g, k, request, tmp_path, outcome):
    retained = {}
    def before_proof(c, create_proof):
        # All actual owning-custody fixture preparation is complete before this
        # one static approval and mock dispatch attempt are frozen.
        g.approval = replace(g.approval, selection=selection_document(c.config))
        g.context = g.approval.context("789")
        assert dispatch(g) == "789"
        janitor = request.getfixturevalue("p")
        retained["janitor"] = janitor
        selected_scheduler = SchedulerReadback(g.w.scheduler.principal_ref, c.config["lifecycle"]["cleanup_ref"],
            janitor.plan.digest, janitor.life.readback.identity.principal_ref, c.h.now, c.h.now + 20)
        selected, pairs = bindings(g, replace(g.w.bindings, runtime_trust=c.trust, lifecycle=janitor.life,
            read_scheduler=lambda ref, deadline: selected_scheduler))
        admitted = admit_github(g.context, bindings=selected, phase="protected-admission", environment=ENV)
        assert admitted.config_digest == digest(c.config)
        assert c.h.calls == 0
        # A signed worker-context token is denied by the same positive controller.
        worker_request = canonical({"profile": PROFILE, "context": asdict(g.context),
            "token": g.token("protected", job_workflow_ref="opensoft/openXwallet/.github/workflows/worker.yml@refs/heads/main")})
        with pytest.raises(BindingError): pairs[1][3].handle(worker_request, deadline=g.now + 10)
        retained["shared"] = (janitor.root / "shared").read_bytes()
        session = Session(pairs[1][0], context=g.context, environment=ENV, deadline=g.now + 10,
            bootstrap_principal="principal:bootstrap", operation_principal="principal:operation-reader")
        c.bridge = c.make(load_config=lambda: session.raw, trust=selected.workflow.runtime_trust,
                          create_proof=create_proof, lifecycle=janitor.life)
        reserve = c.h.ledger.reserve
        retained["replay_refusals"] = []
        def observe(**arguments):
            try: return reserve(**arguments)
            except BindingError as exc:
                retained["replay_refusals"].append(str(exc));raise
        c.h.ledger.reserve = observe

    def one_use(run):
        result = run()
        with pytest.raises(BindingError, match="^runtime-service-unavailable$"): run()
        assert retained["replay_refusals"] == ["replay-refused"]
        return result

    def perform(run):
        janitor = retained["janitor"]
        if outcome == "hard-exit":
            parent, child = multiprocessing.get_context("fork").Pipe(duplex=False)
            def runner():
                one_use(run);child.send_bytes(b"proof-complete");time.sleep(300)
            process = multiprocessing.get_context("fork").Process(target=runner)
            process.start()
            try:
                assert parent.poll(8)
                assert parent.recv_bytes() == b"proof-complete"
                process.kill();process.join(timeout=4);assert not process.is_alive()
                k.c.h.now = janitor.plan.expires_at;janitor.clock.value = janitor.plan.expires_at
                end = time.monotonic() + 5
                while True:
                    state = janitor.audit.read_cleanup(janitor.plan.ref, deadline=janitor.clock.value + 10)
                    if state.lease_status == "closed" and all(not r.present for r in state.resources[:3]): break
                    assert time.monotonic() < end;time.sleep(0.03)
                janitor.life.finalize("cancel")
            finally:
                if process.is_alive(): process.kill();process.join(timeout=3)
                process.close();parent.close();child.close()
            raise RuntimeError("runner-hard-exit-observed")
        def operation():
            result = one_use(run)
            from openwallet_runtime.proof import verify_proof
            proof = verify_proof(result["proof"], expected_digest=k.c.h.challenge.digest, binding=k.c.h.binding, now=k.c.h.now)
            assert proof.subject_ref == k.c.h.binding.subject_ref
            assert result["human_approval"] is False
            if outcome == "failure": raise RuntimeError("after-proof")
            if outcome == "cancel": raise KeyboardInterrupt()
            return result
        return janitor.life.run(operation)

    k.c.h.claims.update(k.c.config["launch"])
    k.c.h.policy["claims"].update({name: k.c.config["launch"][name] for name in k.c.h.policy["claims"]})
    k.access = replace(k.access, sources_digest=digest(k.c.config["sources"]))
    directory = tmp_path / "github-owning-custody";directory.mkdir(mode=0o700)
    if outcome == "success": _owning_run(k, directory, before_proof=before_proof, perform=perform)
    else:
        expected = {"failure": BindingError, "cancel": KeyboardInterrupt, "hard-exit": RuntimeError}[outcome]
        with pytest.raises(expected): _owning_run(k, directory, before_proof=before_proof, perform=perform)
    janitor = retained["janitor"]
    assert_removed(janitor)
    assert (janitor.root / "shared").read_bytes() == retained["shared"]
    with sqlite3.connect(k.c.h.ledger.path) as db: assert db.execute("SELECT count(*) FROM reservations").fetchone() == (1,)
    assert len(row(g)) == 1
    assert row(g)[0][-1] == "789"


def test_actual_tls_readiness_authenticates_signed_identity_and_denies_worker(g, tmp_path):
    from .test_github_bootstrap_identity import loopback
    dispatch(g)
    _, pairs = bindings(g)
    endpoint = pairs[0][3]
    with loopback(tmp_path, post=lambda raw: endpoint.handle(raw, deadline=g.now + 10)) as (transport, url, requests):
        token = TokenTransport(g.token())
        client = ReadinessClient(endpoint=url, token_client=TokenClient(endpoint=ENV["ACTIONS_ID_TOKEN_REQUEST_URL"],
            audience=g.approval.policy("789", "preflight").audience, transport=token), clock=lambda: g.now, transport=transport)
        session = Session(client, context=g.context, environment=ENV, deadline=g.now + 10,
            bootstrap_principal="principal:bootstrap", operation_principal="principal:operation-reader")
        assert session.value["bootstrap"]["run_id"] == "789"
        assert len(requests) == 1
        token.response = Response(200, canonical({"value": g.token(job_workflow_ref="opensoft/openXwallet/.github/workflows/worker.yml@refs/heads/main")}))
        with pytest.raises(BindingError):
            client.read(g.context, environment=ENV, deadline=g.now + 10)
        assert len(requests) == 2
        assert g.w.c.h.calls == 0



def test_session_retains_outer_deadline_across_bootstrap_refresh(g):
    dispatch(g)
    selected, pairs = bindings(g)
    client, transport, _, _ = pairs[0]
    start = g.now
    caller_deadlines, transport_deadlines, replies = [], [], []
    original_read, original_exchange = client.read, transport.exchange
    def advance(seconds):
        g.now += seconds
        g.w.c.h.now += seconds
    def exchange(*arguments, **keywords):
        transport_deadlines.append(keywords["decision"].deadline)
        if len(transport_deadlines) == 2: advance(3)
        return original_exchange(*arguments, **keywords)
    transport.exchange = exchange
    def read(context, *, environment, deadline):
        caller_deadlines.append(deadline)
        value = original_read(context, environment=environment, deadline=deadline)
        replies.append(g.now)
        if len(replies) == 1: advance(8)
        return value
    client.read = read
    with pytest.raises(BindingError): admit_github(g.context, bindings=selected, phase="preflight", environment=ENV)
    assert caller_deadlines == [start + 10, start + 10]
    assert transport_deadlines == [start + 10, start + 10]
    assert replies == [start]
    assert len(g.reads.calls) == 3
    assert g.w.c.h.calls == 0


def test_session_retains_earliest_readback_expiry_and_stops_before_new_token(g):
    dispatch(g)
    _, pairs = bindings(g)
    client, _, token, endpoint = pairs[0]
    original = endpoint.materialize
    def short(correlated, deadline):
        value = original(correlated, deadline=deadline)
        for name in ("bootstrap", "operation"):
            value[name]["expires_at"] = min(value[name]["expires_at"], g.now + 4)
        return value
    endpoint.materialize = short
    start = g.now
    session = Session(client, context=g.context, environment=ENV, deadline=start + 10,
        bootstrap_principal="principal:bootstrap", operation_principal="principal:operation-reader")
    assert session.deadline == start + 4
    g.now += 2
    g.w.c.h.now += 2
    session._read(start + 60)
    assert session.deadline == start + 4
    calls = len(token.calls)
    g.now += 2
    g.w.c.h.now += 2
    with pytest.raises(BindingError): session._read(start + 60)
    assert len(token.calls) == calls
