"""Durable broker and versioned GitHub correlation against deterministic fixtures."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict, replace
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import pytest
import yaml
from workload_factory_binding.evidence import BindingError, canonical, digest, byte_digest
from workload_factory_binding_runtime.bootstrap import selection_document
from workload_factory_binding_runtime.workflow import CALLER, REUSABLE, REF, EnvironmentReadback
from workload_factory_binding_runtime.github_bootstrap import ERROR
from workload_factory_binding_runtime.github_bootstrap.approval import Approval
from workload_factory_binding_runtime.github_bootstrap.broker import DispatchBroker, SourceReadback, API, VERSION
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.github_bootstrap.controller import Controller
from workload_factory_binding_runtime.github_bootstrap.graph import GraphSource, validate_graph
from workload_factory_binding_runtime.github_bootstrap.https import Response
from workload_factory_binding_runtime.github_bootstrap.identity import BootstrapVerifier
from workload_factory_binding_runtime.github_bootstrap.journal import DATABASE, Journal, initialize
from workload_factory_binding_runtime.github_bootstrap.provider import ProviderReader
from .conftest import Transport, jwt
from .composition_fixture import c
from .test_config import configuration as original_configuration
from .test_lifecycle import l
from .test_workflow import w
from workload_factory_binding_runtime.issuer import IssuerKeySource

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def configuration():
    config = original_configuration.__wrapped__()
    for role, path in (("caller_workflow", CALLER), ("reusable_workflow", REUSABLE)):
        config["sources"][role]["digest"] = byte_digest((ROOT / path).read_bytes())
    return config

class BrokerTransport:
    def __init__(self, g):
        self.g, self.sent, self.hook = g, [], None
        self.response = Response(200, canonical({"workflow_run_id": 789,
            "run_url": "https://worker.invalid/ignored", "html_url": "https://worker.invalid/ignored"}))
        self.after_send = None
    def exchange(self, *args, before_send, **kwargs):
        if self.hook: self.hook()
        before_send()
        self.sent.append((args, kwargs))
        if self.after_send: self.after_send()
        return self.response

class ReadTransport:
    def __init__(self, g): self.g, self.calls, self.hook = g, [], None
    def exchange(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.hook: self.hook()
        if "/jobs?" in url:
            page = int(url.rsplit("=", 1)[1]);value = {"total_count": len(self.g.jobs), "jobs": self.g.jobs[(page-1)*100:page*100]}
        elif url.endswith("/approvals"): value = self.g.reviews
        else: value = self.g.run
        return Response(self.g.status, canonical(value))

@pytest.fixture
def g(w, tmp_path):
    now = w.c.h.now
    approval = Approval("preauthorization:github", selection_document(w.c.config), "1234", "88", "77",
        "repo:opensoft/openXwallet:ref:refs/heads/main", ("99",), "coordinated", 1,
        now - 1, now + 100, now, now + 30)
    root = tmp_path / "dispatch-journal"
    identity = initialize(root, identity_name="journal:fixture")
    g = SimpleNamespace(w=w, approval=approval, now=now, root=root, identity=identity,
        source=w.context.sha, status=200, hook=None)
    def current(ref, *, deadline):
        assert ref == g.approval.ref
        if g.hook: g.hook()
        return replace(g.approval, observed_at=g.now, valid_until=g.now + 30)
    g.current = current
    g.open = lambda: Journal(root, identity=g.identity, clock=lambda: g.now)
    g.journal = g.open()
    g.send = BrokerTransport(g)
    g.broker = lambda: DispatchBroker(journal=g.open(), read_approval=current,
        read_source=lambda deadline: SourceReadback("principal:source-reader", g.source, g.now, g.now + 20),
        source_principal="principal:source-reader", credential=lambda deadline: "broker-credential-canary", transport=g.send)
    g.decision = lambda: Decision(clock=lambda: g.now)
    g.context = approval.context("789")
    g.run = {"id": 789, "run_attempt": 1, "workflow_id": 1234, "head_sha": g.source,
        "head_branch": "main", "path": CALLER, "event": "workflow_dispatch", "status": "in_progress",
        "repository": {"id": 123, "full_name": "opensoft/openXwallet", "owner": {"id": 456, "login": "opensoft"}},
        "head_repository": {"id": 123, "full_name": "opensoft/openXwallet"},
        "actor": {"id": 77}, "triggering_actor": {"id": 77},
        "referenced_workflows": [{"path": "opensoft/openXwallet/" + REUSABLE + "@" + REF, "sha": g.source}]}
    g.jobs = [{"id": 1, "run_id": 789, "name": "invoke / admission", "head_sha": g.source, "status": "in_progress"},
              {"id": 2, "run_id": 789, "name": "invoke / protected-qualification", "head_sha": g.source, "status": "in_progress"}]
    g.reviews = [{"state": "approved", "user": {"id": 99, "type": "User"}, "environments": [{"id": 101, "name": w.c.config["launch"]["environment"]}]}]
    g.reads = ReadTransport(g)
    g.graph = GraphSource(g.source, (ROOT / CALLER).read_bytes(), (ROOT / REUSABLE).read_bytes())
    keys = IssuerKeySource(transport=Transport(w.c.h.issuer_key), clock=lambda: float(g.now), monotonic=lambda: float(g.now))
    g.verifier = BootstrapVerifier(keys)
    def controller(phase):
        return Controller(phase=phase, journal=g.open(), read_approval=current, verifier=g.verifier,
            provider=ProviderReader(credential=lambda deadline: "reader-credential-canary", transport=g.reads),
            load_graph=lambda deadline: g.graph, read_environment=lambda name, deadline: replace(w.environment,
                observed_at=g.now, expires_at=g.now + 20), environment_principal=w.environment.principal_ref)
    g.controller = controller
    def token(phase="preflight", **changes):
        policy = approval.policy("789", phase)
        claims = {**dict(policy.expected), "iss": "https://token.actions.githubusercontent.com", "aud": policy.audience,
            "jti": "token:github", "iat": g.now, "nbf": g.now, "exp": g.now + 120, **changes}
        return jwt(w.c.h.issuer_key, claims)
    g.token = token
    return g

def dispatch(g):
    return g.broker().dispatch(g.approval.ref, decision=g.decision())

def correlate(g, phase="preflight", **changes):
    return g.controller(phase).correlate(g.approval.ref, g.token(phase, **changes), g.context, decision=g.decision())

def row(g):
    with sqlite3.connect(g.root / DATABASE) as db:
        return db.execute("SELECT ref, commitment, request, initiating_user, broker_actor, run_id FROM attempts").fetchall()

def test_dispatch_is_durably_consumed_before_one_fixed_version_request(g):
    g.send.hook = lambda: (len(row(g)) == 1 and row(g)[0][-1] is None) or pytest.fail("dispatch not reserved")
    assert dispatch(g) == "789"
    assert len(g.send.sent) == 1
    assert row(g)[0][-1] == "789"
    (method, url), args = g.send.sent[0]
    assert method == "POST"
    assert url == API + "/repos/opensoft/openXwallet/actions/workflows/1234/dispatches"
    assert args["headers"]["X-GitHub-Api-Version"] == VERSION == "2026-03-10"
    request = json.loads(args["body"])
    assert set(request) == {"ref", "inputs"}
    assert request["ref"] == "main"
    assert set(request["inputs"]) == {"accepted_commit", "selection_digest", "preauthorization_ref"}
    assert "return_run_details" not in request
    assert row(g)[0][3:5] == ("88", "77")
    with sqlite3.connect(g.root / DATABASE) as db:
        scope = json.loads(db.execute("SELECT scope FROM attempts").fetchone()[0])
    assert scope == g.approval.journal_scope
    assert scope["case_ref"] == g.approval.configuration["case_ref"]
    assert (scope["not_before"], scope["expires_at"]) == (g.approval.not_before, g.approval.expires_at)
    with pytest.raises(BindingError): dispatch(g)
    assert len(g.send.sent) == 1

@pytest.mark.parametrize("failure", ["lost", "204", "redirect", "rate-limit", "bad-json", "missing-id", "boolean-id", "string-id", "oversize"])
def test_ambiguous_dispatch_never_retries_or_rebinds_after_restart(g, failure):
    if failure == "lost":
        def lost(): raise OSError("response-payload-canary")
        g.send.after_send = lost
    else:
        status = {"204": 204, "redirect": 302, "rate-limit": 429}.get(failure, 200)
        body = {"bad-json": b"private-canary", "missing-id": b"{}", "boolean-id": b'{"workflow_run_id":true}',
                "string-id": b'{"workflow_run_id":"789"}', "oversize": b"x" * 65537}.get(failure, b"{}")
        g.send.response = Response(status, body)
    with pytest.raises(BindingError, match="^" + ERROR + "$"): dispatch(g)
    assert len(row(g)) == 1
    assert row(g)[0][-1] is None
    assert len(g.send.sent) == 1
    g.journal = g.open()
    with pytest.raises(BindingError): correlate(g)
    assert not g.reads.calls  # A valid token/public run cannot manufacture lost correlation.
    with pytest.raises(BindingError): dispatch(g)
    assert len(g.send.sent) == 1

@pytest.mark.parametrize("boundary", ["credential", "tls", "source-read"])
@pytest.mark.parametrize("failure", ["revoked", "expired", "source-drift"])
def test_reserved_winner_rechecks_after_blocking_work_and_sends_zero(g, boundary, failure):
    def change():
        if failure == "revoked": g.approval = replace(g.approval, revoked=True)
        elif failure == "expired": g.now += 101
        else: g.source = "c" * 40
    broker = g.broker()
    if boundary == "credential":
        def credential(deadline): change();return "broker-credential-canary"
        broker.credential = credential
    elif boundary == "tls": g.send.hook = change
    else:
        calls = []
        def source(deadline):
            calls.append(1)
            if len(calls) == 2: change()
            return SourceReadback("principal:source-reader", g.source, g.now, g.now + 20)
        broker.read_source = source
    use = g.decision()
    with pytest.raises(BindingError): broker.dispatch(g.approval.ref, decision=use)
    assert len(row(g)) == 1
    assert row(g)[0][-1] is None
    assert not g.send.sent


def test_concurrent_brokers_have_exactly_one_durable_winner(g):
    def attempt(_):
        try: return dispatch(g)
        except BindingError: return "refused"
    with ThreadPoolExecutor(max_workers=8) as pool: results = list(pool.map(attempt, range(8)))
    assert results.count("789") == 1
    assert results.count("refused") == 7
    assert len(g.send.sent) == len(row(g)) == 1


def test_process_crash_before_io_stays_consumed_after_restart(g):
    request = {"ref": "main", "inputs": {"accepted_commit": g.source, "selection_digest": g.context.selection_digest,
                                       "preauthorization_ref": g.approval.ref}}
    def child():
        g.open().reserve(g.approval, request)
        os._exit(17)
    process = multiprocessing.get_context("fork").Process(target=child)
    process.start();process.join(timeout=4)
    try: assert process.exitcode == 17
    finally:
        if process.is_alive(): process.kill();process.join(timeout=2)
        process.close()
    assert len(row(g)) == 1
    assert row(g)[0][-1] is None
    with pytest.raises(BindingError): dispatch(g)
    assert not g.send.sent

@pytest.mark.parametrize("failure", ["missing", "replaced", "unsafe", "schema", "clock", "wrong-identity"])
def test_journal_never_recreates_or_repairs_missing_unsafe_state(g, failure):
    dispatch(g)
    if failure == "missing": (g.root / DATABASE).unlink()
    elif failure == "replaced":
        data = (g.root / DATABASE).read_bytes()
        (g.root / DATABASE).rename(g.root / "retained-old.sqlite")
        (g.root / DATABASE).write_bytes(data)
        (g.root / DATABASE).chmod(0o600)
    elif failure == "unsafe": (g.root / DATABASE).chmod(0o644)
    elif failure == "schema":
        with sqlite3.connect(g.root / DATABASE) as db: db.execute("CREATE TABLE surprise (value TEXT)")
    elif failure == "clock": g.now -= 1
    else: g.identity = replace(g.identity, name="journal:other")
    with pytest.raises(BindingError): g.open()
    if failure == "missing": assert not (g.root / DATABASE).exists()


def test_expired_business_refusal_retains_clock_highwater(g):
    dispatch(g);g.now += 101
    with pytest.raises(BindingError): g.journal.read(g.approval)
    g.now -= 1
    with pytest.raises(BindingError): g.open()
    with sqlite3.connect(g.root / DATABASE) as db: assert db.execute("SELECT highwater FROM metadata").fetchone() == (g.now + 1,)


def test_independent_run_api_and_signed_identity_corroborate_both_phases(g):
    dispatch(g)
    pre = correlate(g)
    assert pre.phase == "preflight"
    assert pre.run_id == "789"
    assert pre.valid_until <= g.now + 10
    post = correlate(g, "protected")
    assert post.phase == "protected"
    assert g.w.c.h.calls == 0
    assert len(g.reads.calls) == 7
    assert all(method == "GET" and url.startswith(API + "/repos/opensoft/openXwallet/") for method, url, _ in g.reads.calls)
    assert all(a["headers"]["Authorization"] == "Bearer reader-credential-canary" for _, _, a in g.reads.calls)

@pytest.mark.parametrize("field", ["id", "run_attempt", "workflow_id", "head_sha", "head_branch", "path", "event", "status", "repository", "head_repository", "actor", "triggering_actor", "referenced_workflows"])
def test_each_provider_binding_is_independently_required(g, field):
    dispatch(g);g.run[field] = None
    with pytest.raises(BindingError): correlate(g)
    assert g.w.c.h.calls == 0

@pytest.mark.parametrize("change", ["human-review", "app-review", "wrong-env", "rejected", "missing", "wrong-user", "no-env", "team-label"])
def test_app_dispatch_does_not_hide_originating_human_self_review(g, change):
    dispatch(g)
    review = g.reviews[0]
    if change == "human-review": review["user"]["id"] = 88
    elif change == "app-review": review["user"]["id"] = 77
    elif change == "wrong-env": review["environments"][0]["id"] = 999
    elif change == "rejected": review["state"] = "rejected"
    elif change == "missing": g.reviews = []
    elif change == "wrong-user": review["user"]["id"] = 100
    elif change == "no-env": review["environments"] = []
    else: review["user"]["type"] = "Team"
    with pytest.raises(BindingError): correlate(g, "protected")

@pytest.mark.parametrize("field", ["sub", "sha", "repository_id", "run_id", "run_attempt", "aud", "event_name"])
def test_signed_wrong_context_refuses_before_provider_io(g, field):
    dispatch(g)
    with pytest.raises(BindingError): correlate(g, **{field: "wrong"})
    assert not g.reads.calls

@pytest.mark.parametrize("change", ["duplicate-job", "job-status", "job-source", "job-run", "missing-job", "api-outage", "late-revocation", "late-expiry", "main-drift"])
def test_missing_ambiguous_stale_or_revoked_correlation_cannot_issue_readiness(g, change):
    dispatch(g)
    if change == "duplicate-job": g.jobs.append(dict(g.jobs[0], id=3))
    elif change == "job-status": g.jobs[0]["status"] = "completed"
    elif change == "job-source": g.jobs[0]["head_sha"] = "c" * 40
    elif change == "job-run": g.jobs[0]["run_id"] = 999
    elif change == "missing-job": g.jobs = g.jobs[1:]
    elif change == "api-outage": g.status = 503
    elif change == "late-revocation": g.reads.hook = lambda: setattr(g, "approval", replace(g.approval, revoked=True))
    elif change == "late-expiry": g.reads.hook = lambda: setattr(g, "now", g.now + 61)
    else: g.run["head_sha"] = "c" * 40
    with pytest.raises(BindingError, match="^" + ERROR + "$"): correlate(g)


def test_two_job_pages_are_bounded_and_urls_never_followed(g):
    dispatch(g)
    g.jobs += [{"id": x, "run_id": 789, "name": "other", "head_sha": g.source, "status": "completed"} for x in range(3, 102)]
    assert correlate(g, "preflight").run_id == "789"
    assert len(g.reads.calls) == 4
    with pytest.raises(BindingError): correlate(g, "protected")
    g.jobs += [{"id": x} for x in range(102, 202)]
    with pytest.raises(BindingError): correlate(g)

@pytest.mark.parametrize("change", ["third-job", "worker-command", "preflight-env", "permission", "duplicate-yaml", "protected-no-env", "source"])
def test_graph_phase_ambiguity_refuses_even_with_reapproved_byte_digests(g, change):
    reusable = yaml.load(g.graph.reusable, Loader=yaml.BaseLoader)
    if change == "third-job": reusable["jobs"]["worker"] = deepcopy(reusable["jobs"]["admission"])
    elif change == "worker-command": reusable["jobs"]["admission"]["steps"].append({"run": "python3 worker.py"})
    elif change == "preflight-env": reusable["jobs"]["admission"]["environment"] = "qa"
    elif change == "permission": reusable["jobs"]["admission"]["permissions"]["actions"] = "write"
    elif change == "protected-no-env": del reusable["jobs"]["protected-qualification"]["environment"]
    raw = yaml.safe_dump(reusable).encode()
    if change == "duplicate-yaml": raw += b"\npermissions: {}\n"
    graph = replace(g.graph, reusable=raw, commit="c" * 40 if change == "source" else g.source)
    selected = json.loads(g.approval.selection)
    selected["configuration"]["sources"]["reusable_workflow"]["digest"] = byte_digest(raw)
    approved = replace(g.approval, selection=canonical(selected))
    with pytest.raises(BindingError): validate_graph(graph, approved)


@pytest.mark.parametrize("field,value", [("run_attempt", 2), ("run_attempt", True), ("head_sha", "c" * 40), ("status", "completed")])
def test_final_provider_observation_detects_attempt_or_source_change_during_reads(g, field, value):
    dispatch(g)
    def change():
        if len(g.reads.calls) == 2: g.run[field] = value
    g.reads.hook = change
    with pytest.raises(BindingError): correlate(g)
    assert len(g.reads.calls) == 3


def test_final_provider_projection_ignores_unselected_display_metadata(g):
    dispatch(g)
    def display_update():
        if len(g.reads.calls) == 2: g.run["display_title"] = "provider-private-canary"
    g.reads.hook = display_update
    assert correlate(g).run_id == "789"


def test_dispatch_cancellation_after_reservation_is_not_a_retry_grant(g):
    def cancelled(): raise KeyboardInterrupt
    g.send.hook = cancelled
    with pytest.raises(KeyboardInterrupt): dispatch(g)
    assert len(row(g)) == 1
    assert row(g)[0][-1] is None
    assert not g.send.sent
    g.send.hook = None
    with pytest.raises(BindingError): dispatch(g)
    assert not g.send.sent


def test_changed_approval_scope_cannot_reuse_a_consumed_reference(g):
    dispatch(g)
    g.approval = replace(g.approval, revision=2)
    with pytest.raises(BindingError): correlate(g)
    with pytest.raises(BindingError): dispatch(g)
    assert len(row(g)) == len(g.send.sent) == 1


def test_provider_read_budget_is_shared_by_helpers_in_one_decision(g):
    use = g.decision()
    provider = ProviderReader(credential=lambda deadline: "reader-only", transport=g.reads)
    for _ in range(4): provider.decision("opensoft/openXwallet", use).run("789")
    final_reader = provider.decision("opensoft/openXwallet", use)
    with pytest.raises(BindingError): final_reader.run("789")
    assert len(g.reads.calls) == 4


@pytest.mark.parametrize("change", ["stale", "future", "expired", "principal", "dictionary", "floating-time"])
def test_source_readback_cannot_be_stale_or_self_reported(g, change):
    broker = g.broker()
    value = SourceReadback("principal:source-reader", g.source, g.now, g.now + 20)
    if change == "stale": value = replace(value, observed_at=g.now - 1)
    elif change == "future": value = replace(value, observed_at=g.now + 1)
    elif change == "expired": value = replace(value, expires_at=g.now)
    elif change == "principal": value = replace(value, principal_ref="principal:worker")
    elif change == "floating-time": value = replace(value, observed_at=float(g.now))
    else: value = {"sha": g.source, "approved": True}
    broker.read_source = lambda deadline: value
    use = g.decision()
    with pytest.raises(BindingError): broker.dispatch(g.approval.ref, decision=use)
    assert not row(g)
    assert not g.send.sent


@pytest.mark.parametrize("field", ["scope", "request"])
def test_persisted_scope_and_dispatch_bytes_cannot_diverge_from_approval(g, field):
    dispatch(g)
    with sqlite3.connect(g.root / DATABASE) as db:
        db.execute("UPDATE attempts SET " + field + "=?", ('{}',))
    with pytest.raises(BindingError): correlate(g)
    assert not g.reads.calls
    assert len(row(g)) == 1


@pytest.mark.parametrize("suffix", ["; python3 worker.py preflight", "\npython3 worker.py preflight", " && python3 worker.py preflight", " | python3 worker.py preflight"])
def test_phase_command_requires_complete_exact_match_not_prefix_and_last_word(g, suffix):
    reusable = yaml.load(g.graph.reusable, Loader=yaml.BaseLoader)
    reusable["jobs"]["admission"]["steps"][-1]["run"] += suffix
    raw = yaml.safe_dump(reusable).encode()
    selected = json.loads(g.approval.selection)
    selected["configuration"]["sources"]["reusable_workflow"]["digest"] = byte_digest(raw)
    approved = replace(g.approval, selection=canonical(selected))
    graph = replace(g.graph, reusable=raw)
    with pytest.raises(BindingError): validate_graph(graph, approved)

@pytest.mark.parametrize("change", ["guard", "phase-order", "action-order", "admit-id", "cleanup-if", "timeout-zero"])
def test_exact_job_phase_and_step_structure_is_required_after_hash_approval(g, change):
    reusable = yaml.load(g.graph.reusable, Loader=yaml.BaseLoader)
    admission = reusable["jobs"]["admission"]
    protected = reusable["jobs"]["protected-qualification"]
    if change == "guard": protected["if"] = "${{ always() }}"
    elif change == "phase-order": protected["steps"][3], protected["steps"][4] = protected["steps"][4], protected["steps"][3]
    elif change == "action-order": admission["steps"][0], admission["steps"][1] = admission["steps"][1], admission["steps"][0]
    elif change == "admit-id": admission["steps"][-1]["id"] = "different"
    elif change == "cleanup-if": del protected["steps"][-1]["if"]
    else: admission["timeout-minutes"] = "0"
    raw = yaml.safe_dump(reusable).encode()
    selected = json.loads(g.approval.selection)
    selected["configuration"]["sources"]["reusable_workflow"]["digest"] = byte_digest(raw)
    approved = replace(g.approval, selection=canonical(selected))
    graph = replace(g.graph, reusable=raw)
    with pytest.raises(BindingError): validate_graph(graph, approved)

@pytest.mark.parametrize("caller,called,ref", [("bare", "full", None), ("short", "full", REF), ("bare", "short", REF), ("short", "short", REF)])
def test_documented_rest_path_forms_map_only_to_selected_main_and_sha(g, caller, called, ref):
    dispatch(g)
    if caller == "short": g.run["path"] = CALLER + "@main"
    reference = g.run["referenced_workflows"][0]
    if called == "short": reference["path"] = "opensoft/openXwallet/" + REUSABLE + "@main"
    if ref is not None: reference["ref"] = ref
    assert correlate(g).run_id == "789"

@pytest.mark.parametrize("change", ["short-no-ref", "short-tag-ref", "full-conflicting-ref", "foreign-path", "caller-tag", "caller-case", "caller-extra-suffix"])
def test_rest_wire_mapping_refuses_ambiguous_or_changed_source(g, change):
    dispatch(g)
    reference = g.run["referenced_workflows"][0]
    if change.startswith("short"):
        reference["path"] = "opensoft/openXwallet/" + REUSABLE + "@main"
        if change == "short-tag-ref": reference["ref"] = "refs/tags/main"
    elif change == "full-conflicting-ref": reference["ref"] = "refs/tags/main"
    elif change == "foreign-path": reference["path"] = "foreign/openXwallet/" + REUSABLE + "@main"
    elif change == "caller-tag": g.run["path"] = CALLER + "@refs/tags/main"
    elif change == "caller-case": g.run["path"] = CALLER.replace("workflows", "Workflows")
    else: g.run["path"] = CALLER + "@main@other"
    with pytest.raises(BindingError): correlate(g)


def test_expired_reservation_never_resolves_credential_after_journal_returns(g):
    broker, use, credentials = g.broker(), g.decision(), []
    original = broker.journal.reserve
    def delayed(approval, request, **arguments):
        original(approval, request, **arguments)
        g.now += 11
    broker.journal.reserve = delayed
    def credential(deadline):
        credentials.append(deadline)
        return "unused-fixture-credential"
    broker.credential = credential
    with pytest.raises(BindingError): broker.dispatch(g.approval.ref, decision=use)
    assert not credentials
    assert not g.send.sent
    assert len(row(g)) == 1
    assert row(g)[0][-1] is None


def test_late_journal_commit_refuses_success_but_retains_correlated_consumption(g):
    broker, use, budgets = g.broker(), g.decision(), []
    original = broker.journal.record_run
    def delayed(approval, run_id, **arguments):
        budgets.append(arguments["budget"])
        original(approval, run_id, **arguments)
        g.now += 3
    broker.journal.record_run = delayed
    g.send.hook = lambda: setattr(g, "now", g.now + 8)
    with pytest.raises(BindingError): broker.dispatch(g.approval.ref, decision=use)
    assert 0 < budgets[0] <= 2
    assert g.now >= use.deadline
    assert row(g)[0][-1] == "789"
    assert len(g.send.sent) == 1
    with pytest.raises(BindingError): dispatch(g)
    assert len(g.send.sent) == 1


def test_journal_lock_wait_honors_remaining_caller_budget(g):
    import time
    lock = sqlite3.connect(g.root / DATABASE, isolation_level=None)
    lock.execute("BEGIN IMMEDIATE")
    try:
        started = time.monotonic()
        with pytest.raises(BindingError): g.journal.read(g.approval, budget=0.05)
        assert time.monotonic() - started < 1
    finally:
        lock.execute("ROLLBACK")
        lock.close()

@pytest.mark.parametrize("component", ["reader", "broker"])
@pytest.mark.parametrize("include_agent", [True, False])
def test_actual_rest_wire_requires_fixed_user_agent(g, tmp_path, monkeypatch, component, include_agent):
    from .test_github_bootstrap_identity import loopback
    from workload_factory_binding_runtime.github_bootstrap import USER_AGENT
    from workload_factory_binding_runtime.github_bootstrap import provider as reader_module
    from workload_factory_binding_runtime.github_bootstrap import broker as broker_module
    with loopback(tmp_path, post=lambda raw: canonical({"workflow_run_id": 789}), require_user_agent=True) as (tls, endpoint, requests):
        origin = endpoint.rsplit("/", 1)[0]
        class SelectedTransport:
            def exchange(self, *arguments, headers, **keywords):
                selected = dict(headers)
                if not include_agent: selected.pop("User-Agent")
                return tls.exchange(*arguments, headers=selected, **keywords)
        if component == "reader":
            monkeypatch.setattr(reader_module, "API", origin)
            provider = ProviderReader(credential=lambda deadline: "fixture-reader-only", transport=SelectedTransport())
            reads = provider.decision("opensoft/openXwallet", g.decision())
            operation = lambda: reads.run("789")
        else:
            monkeypatch.setattr(broker_module, "API", origin)
            broker = g.broker()
            broker.transport = SelectedTransport()
            use = g.decision()
            operation = lambda: broker.dispatch(g.approval.ref, decision=use)
        if include_agent:
            assert operation() is not None
        else:
            with pytest.raises(BindingError): operation()
        assert len(requests) == 1
        assert requests[0][1].get("User-Agent") == (USER_AGENT if include_agent else None)


def test_concurrent_commit_can_remove_delete_journal_before_sidecar_stat(g, monkeypatch):
    dispatch(g)
    database = g.journal.directory / DATABASE
    sidecar = g.journal.directory / (DATABASE + "-journal")
    other = sqlite3.connect(database, isolation_level=None)
    committed = []
    original = Path.lstat
    try:
        other.execute("BEGIN IMMEDIATE")
        other.execute("UPDATE metadata SET highwater=highwater+1")
        assert sidecar.exists()
        def concurrent_commit(path, *args, **kwargs):
            if path == sidecar and not committed:
                other.execute("COMMIT")
                committed.append(True)
            return original(path, *args, **kwargs)
        monkeypatch.setattr(Path, "lstat", concurrent_commit)
        # Another client finishes its normal DELETE-journal transaction exactly
        # before this reader measures the sidecar. It must not look like damage.
        g.now += 1
        assert g.journal.read(g.approval) == "789"
        assert committed == [True]
        assert not sidecar.exists()
    finally:
        if other.in_transaction:
            other.rollback()
        other.close()
