"""P04 local TLS, signed identity and intrinsic controller controls; no live OIDC."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace
import copy
import json
import pickle
import ssl
import subprocess
import threading

import pytest
from workload_factory_binding.evidence import BindingError, canonical, decode64
from workload_factory_binding_runtime.azure_composition.runner_transport import RunnerCapture, RunnerPolicy, ERROR
from workload_factory_binding_runtime.github_bootstrap.https import Https
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
from workload_factory_binding_runtime.hosted.readback import ReadBudget, start_qualification
from workload_factory_binding_runtime.workflow import operational_bindings
from .launch_fixture import stage, v, g, rb, configuration, c, l, w
from .test_https import certificates
from .conftest import jwt

URL = "ACTIONS_ID_TOKEN_REQUEST_URL"
BEARER = "ACTIONS_ID_TOKEN_REQUEST_TOKEN"
SECRET = "p04-private-request-canary"


class EqualityAlias(str):
    """Changed injection value that claims equality without retaining the bytes."""
    def __eq__(self, other): return True
    __hash__ = str.__hash__



@pytest.fixture
def runner(stage, tmp_path):
    root = tmp_path / "original-runner-tls"
    root.mkdir(mode=0o700)
    ca, cert, key = certificates(root)
    r = SimpleNamespace(stage=stage, token=stage.v.pre_token, status=200, mode="normal",
                        requests=[], after_get=None, posts=[], decisions=[])
    stop = threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_GET(self):
            r.requests.append((self.path, dict(self.headers)))
            body = canonical({"value": r.token})
            if r.mode == "malformed": body = b'{"value":"private-canary","value":"duplicate"}'
            if r.mode == "body-limit": body = b"x" * 24577
            self.send_response(r.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Location", "https://127.0.0.1:9/forbidden")
            self.send_header("Content-Length", str(len(body) + (10 if r.mode == "truncated" else 0)))
            if r.mode == "compressed": self.send_header("Content-Encoding", "gzip")
            self.end_headers()
            if r.after_get: r.after_get()
            try:
                if r.mode == "slow":
                    self.wfile.write(body[:1]); self.wfile.flush(); stop.wait(2)
                else: self.wfile.write(body)
            except OSError: pass
    server = HTTPServer(("127.0.0.1", 0), Handler)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert, key)
    server.socket = tls.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.02))
    thread.start()
    r.transport = Https(ca_file=ca)
    r.tls = tls
    # Independent literal policy; never obtain a policy by parsing injection.
    r.policy = RunnerPolicy(stage.v.context.source_commit, "preflight",
                            "https://127.0.0.1:" + str(server.server_port), "/job/token", (("api-version", "2.0"),))
    r.endpoint = "https://127.0.0.1:" + str(server.server_port) + "/job/token?api-version=2.0"
    r.environment = {URL: r.endpoint, BEARER: SECRET}
    def capture(phase="preflight", *, decision=None, policy=None, environment=None, transport=None, context=None):
        chosen = policy or replace(r.policy, phase=phase)
        use = decision or stage.use()
        r.decisions.append(use)
        return RunnerCapture(policy=chosen, context=context or stage.v.context,
            original_environment=r.environment if environment is None else environment,
            admission=stage.plan if phase == "preflight" else stage.protected,
            transport=transport or r.transport, decision=use)
    r.capture = capture
    try: yield r
    finally:
        stop.set(); server.shutdown(); server.server_close(); thread.join(timeout=4)
        assert not thread.is_alive()


def observe_post(monkeypatch, runner):
    original = PrivateHttps.exchange
    def exchange(transport, method, url, **kwargs):
        if url in (runner.stage.public_origin + "/v2/plan", runner.stage.public_origin + "/v2/protected"):
            runner.posts.append((url, kwargs["decision"], kwargs["headers"]["Authorization"]))
        return original(transport, method, url, **kwargs)
    monkeypatch.setattr(PrivateHttps, "exchange", exchange)


def fresh_positive(r):
    result = r.capture().admit()
    assert result.state == "plan-ready"
    assert len(r.requests) == 1
    return result


@pytest.mark.parametrize("phase", ["preflight", "protected-admission"])
def test_real_tls_signed_identity_provider_correlation_and_intrinsic_phase(runner, monkeypatch, phase):
    r = runner
    r.token = r.stage.v.pre_token if phase == "preflight" else r.stage.v.token
    observe_post(monkeypatch, r)
    get_decisions = []
    original_get = Https.exchange
    def get(transport, *args, **kwargs):
        get_decisions.append(kwargs["decision"])
        return original_get(transport, *args, **kwargs)
    monkeypatch.setattr(Https, "exchange", get)
    capture = r.capture(phase)
    assert r.requests == []
    result = capture.admit()
    assert result.state == ("plan-ready" if phase == "preflight" else "running")
    assert result.run_id == r.stage.v.context.run_id
    assert len(r.requests) == 1
    assert len(r.posts) == 1
    assert r.requests[0][0] == "/job/token?api-version=2.0&audience=urn%3Aopensoft%3Aopenxfactory%3Abootstrap-admission%3Av1"
    assert r.requests[0][1]["Authorization"] == "Bearer " + SECRET
    assert r.posts[0][0] == r.stage.public_origin + ("/v2/plan" if phase == "preflight" else "/v2/protected")
    assert get_decisions == [r.decisions[0]]
    assert r.posts[0][1] is r.decisions[0]
    assert r.posts[0][2] == "Bearer " + r.token
    assert r.stage.v.h.calls == 0
    if phase == "protected-admission":
        assert len(r.stage.agent.children) == 1
        assert r.stage.events == ["cleanup-durable"]
        server_budget = ReadBudget(r.stage.seen[0])
        assert server_budget.github_requests == 24
        assert server_budget.state["counts"]["source"] == 8
        assert server_budget.state["counts"]["protection"] == 4
        assert server_budget.state["counts"]["control"] == 4
        assert server_budget.state["staging"] is True
    else:
        assert r.stage.agent.children == {}
        assert ReadBudget(r.stage.seen[0]).github_requests <= 13
    assert r.decisions[0].api_requests == 0  # fixed GET is not a REST correlation slot
    assert ReadBudget(r.decisions[0]).github_requests == 0


@pytest.mark.parametrize("suffix", ["#fragment", "&audience=other", "&AUDIENCE=other", "&api-version=2.0",
    "&extra=x", "&api%2Dversion=2.0", "&audience=", "&x=%0a"])
def test_unapproved_query_and_fragment_refuse_before_bearer_transmission(runner, suffix):
    r = runner
    environment = dict(r.environment, **{URL: r.endpoint + suffix})
    with pytest.raises(BindingError, match="^" + ERROR + "$"):
        r.capture(environment=environment)
    assert r.requests == []


@pytest.mark.parametrize("change", ["origin", "port", "userinfo", "http", "path", "encoded", "dot", "slash", "backslash"])
def test_unselected_origin_path_and_encoding_refuse_before_send(runner, change):
    r = runner
    url = {"origin": "https://worker.invalid/job/token?api-version=2.0",
           "port": "https://127.0.0.1:9/job/token?api-version=2.0",
           "userinfo": r.endpoint.replace("https://", "https://user:pass@"),
           "http": r.endpoint.replace("https:", "http:"),
           "path": r.endpoint.replace("/job/token", "/other/token"),
           "encoded": r.endpoint.replace("/job/", "/%6aob/"),
           "dot": r.endpoint.replace("/job/", "/other/../job/"),
           "slash": r.endpoint.replace("/job/", "//job/"),
           "backslash": r.endpoint.replace("/job/", "/job\\")}[change]
    with pytest.raises(BindingError): r.capture(environment={URL: url, BEARER: SECRET})
    assert r.requests == []


@pytest.mark.parametrize("field,value", [("origin", "http://worker.invalid"), ("origin", "https://worker.invalid/"),
    ("origin", "https://WORKER.invalid"), ("origin", "https://worker.invalid:0443"),
    ("path", "/a/../token"), ("path", "/a/%74oken"), ("path", "//token"),
    ("path", "/token?query=x"), ("query", (("audience", "x"),)),
    ("query", (("AUDIENCE", "x"),)), ("query", (("x", "a"), ("x", "b"))),
    ("query", (("x", "a&b"),)), ("phase", EqualityAlias("qualify")), ("phase", "qualify"), ("phase", "cleanup"), ("source_commit", "0" * 40)])
def test_policy_requires_closed_independent_selection(field, value):
    policy = RunnerPolicy("a" * 40, "preflight", "https://selected.invalid", "/job/token")
    assert policy.endpoint() == "https://selected.invalid/job/token"
    with pytest.raises(BindingError, match="^" + ERROR + "$"): replace(policy, **{field: value}).endpoint()


@pytest.mark.parametrize("change", ["url", "bearer", "pair", "missing-url", "missing-bearer"])
@pytest.mark.parametrize("checkpoint", ["before-get", "tls-ready"])
def test_later_injection_drift_is_refused_without_substitution(runner, monkeypatch, change, checkpoint):
    r = runner
    capture = r.capture()
    def mutate():
        if change in ("url", "pair"): r.environment[URL] = "https://127.0.0.1:9/replacement"
        if change in ("bearer", "pair"): r.environment[BEARER] = "replacement-private-canary"
        if change == "missing-url": r.environment.pop(URL)
        if change == "missing-bearer": r.environment.pop(BEARER)
    if checkpoint == "before-get": mutate()
    else:
        original = Https.exchange
        def exchange(transport, *args, before_send, **kwargs):
            def guard(): mutate(); before_send()
            return original(transport, *args, before_send=guard, **kwargs)
        monkeypatch.setattr(Https, "exchange", exchange)
    with pytest.raises(BindingError, match="^" + ERROR + "$"): capture.admit()
    assert r.requests == []
    r.environment.update({URL: r.endpoint, BEARER: SECRET})
    with pytest.raises(BindingError): capture.admit()
    assert r.requests == []


def test_original_pair_is_not_reconsulted_or_used_for_post(runner, monkeypatch):
    r = runner
    observe_post(monkeypatch, r)
    r.after_get = lambda: r.environment.update({URL: "https://127.0.0.1:9/changed", BEARER: "changed"})
    result = r.capture().admit()
    assert result.state == "plan-ready"
    assert len(r.posts) == 1
    assert r.posts[0][2] == "Bearer " + r.token


@pytest.mark.parametrize("kind", ["success", "redirect", "lost-reply", "cancel"])
def test_attempt_is_consumed_before_uncertainty_and_never_reopens(runner, monkeypatch, kind):
    r = runner
    capture = r.capture()
    if kind == "redirect": r.status = 302
    if kind in ("lost-reply", "cancel"):
        original = Https.exchange
        def exchange(*a, **kw):
            result = original(*a, **kw)
            if kind == "cancel": raise KeyboardInterrupt("private-canary")
            raise OSError("private-canary")
        monkeypatch.setattr(Https, "exchange", exchange)
    if kind == "success": assert capture.admit().state == "plan-ready"
    else:
        with pytest.raises(KeyboardInterrupt if kind == "cancel" else BindingError): capture.admit()
    assert len(r.requests) == 1
    with pytest.raises(BindingError): capture.admit()
    assert len(r.requests) == 1


def test_concurrent_acquisition_has_one_attempt(runner):
    r = runner
    capture = r.capture()
    def run(_):
        try: return capture.admit().state
        except BindingError: return "refused"
    with ThreadPoolExecutor(max_workers=6) as pool: results = list(pool.map(run, range(6)))
    assert results.count("plan-ready") == 1
    assert results.count("refused") == 5
    assert len(r.requests) == 1


@pytest.mark.parametrize("field", ["aud", "sha", "repository_id", "run_id", "job_workflow_ref", "environment"])
def test_validly_signed_wrong_claims_cannot_produce_readiness(runner, field):
    r = runner
    claims = json.loads(decode64(r.token.split(".")[1]))
    claims[field] = {"aud": "urn:fixture:proof", "sha": "f" * 40, "repository_id": "999", "run_id": "999",
                     "job_workflow_ref": "opensoft/openXwallet/.github/workflows/worker.yml@refs/heads/main",
                     "environment": "qa"}[field]
    r.token = jwt(r.stage.v.h.issuer_key, claims)
    with pytest.raises(BindingError, match="^" + ERROR + "$"): r.capture().admit()
    assert len(r.requests) == 1
    assert r.stage.agent.children == {}


@pytest.mark.parametrize("change", ["wrong-run", "self-review", "source-moved", "hold-revoked"])
def test_current_provider_corroboration_is_required_after_real_get(runner, change):
    r = runner
    r.token = r.stage.v.token
    if change == "wrong-run": r.stage.g.run["run_attempt"] = 2
    elif change == "self-review": r.stage.g.reviews[0]["user"]["id"] = int(r.stage.policy.initiating_user_id)
    elif change == "source-moved": r.stage.rb.main_sha = "f" * 40
    else: r.stage.rb.hold["state"] = "revoked"
    with pytest.raises(BindingError): r.capture("protected-admission").admit()
    assert len(r.requests) == 1
    assert r.stage.agent.children == {}
    assert not r.stage.rb.stage_lease_path.exists()


@pytest.mark.parametrize("mode", ["redirect", "compressed", "truncated", "malformed", "body-limit", "wrong-ca", "wrong-host", "slow"])
def test_transport_failures_are_bounded_and_reap_private_helpers(runner, monkeypatch, mode, tmp_path):
    r = runner
    children = []
    original = subprocess.Popen
    def popen(*args, **kwargs):
        process = original(*args, **kwargs); children.append(process)
        assert SECRET not in repr(args)
        assert r.endpoint not in repr(args)
        assert not any(k in kwargs.get("env", {}) for k in (URL, BEARER, "HTTPS_PROXY", "SSL_CERT_FILE", "SSLKEYLOGFILE"))
        return process
    monkeypatch.setattr(subprocess, "Popen", popen)
    r.mode = mode
    if mode == "redirect": r.status = 302
    if mode == "wrong-ca": r.transport = Https()
    if mode == "wrong-host":
        other = tmp_path / "wrong-host-ca"
        other.mkdir(mode=0o700)
        ca, cert, key = certificates(other, wrong_host=True)
        r.tls.load_cert_chain(cert, key)
        r.transport = Https(ca_file=ca)
    use = r.stage.use()
    if mode == "slow": use.clip(r.stage.v.h.now + 1); use.end = use.monotonic() + .4
    with pytest.raises(BindingError): r.capture(decision=use).admit()
    assert len(r.requests) <= 1
    assert children
    assert all(child.poll() is not None for child in children)
    assert all(child.stdin.closed for child in children)
    assert all(child.stdout.closed for child in children)


def test_ambient_proxy_trust_and_keylog_cannot_redirect_capture(runner, monkeypatch, tmp_path):
    keylog = tmp_path / "forbidden-keylog"
    for key, value in {"HTTPS_PROXY": "http://127.0.0.1:9", "SSL_CERT_FILE": str(tmp_path / "bad-ca"),
                       "REQUESTS_CA_BUNDLE": str(tmp_path / "bad-ca"), "SSLKEYLOGFILE": str(keylog)}.items():
        monkeypatch.setenv(key, value)
    fresh_positive(runner)
    assert not keylog.exists()


@pytest.mark.parametrize("bad", ["", "x" * 513, "line\nbreak", "x y", None])
def test_effective_512_character_request_credential_bound(runner, bad):
    r = runner
    with pytest.raises(BindingError): r.capture(environment={URL: r.endpoint, BEARER: bad})
    assert r.requests == []


def test_fitting_512_character_bearer_is_sent_without_truncation(runner):
    r = runner
    r.environment[BEARER] = "a" * 512
    fresh_positive(r)
    assert r.requests[0][1]["Authorization"] == "Bearer " + "a" * 512


def test_oversized_returned_jwt_refuses_before_intrinsic_post(runner, monkeypatch):
    r = runner
    observe_post(monkeypatch, r)
    r.token = "x" * 16378
    reads = []
    from workload_factory_binding_runtime.hosted.stage_client import AdmissionClient
    original = AdmissionClient.read
    def read(client, *args, **kwargs):
        reads.append(True)
        return original(client, *args, **kwargs)
    monkeypatch.setattr(AdmissionClient, "read", read)
    with pytest.raises(BindingError): r.capture().admit()
    assert reads == []
    assert len(r.requests) == 1
    assert r.posts == []


@pytest.mark.parametrize("change", ["source", "phase", "route", "ca"])
def test_rebinding_source_phase_route_or_transport_refuses_before_get(runner, change):
    r = runner
    if change == "source":
        with pytest.raises(BindingError): r.capture(policy=replace(r.policy, source_commit="f" * 40))
    elif change == "phase":
        with pytest.raises(BindingError): r.capture(policy=replace(r.policy, phase="protected-admission"))
    else:
        capture = r.capture()
        if change == "route": r.stage.plan.path = "/v2/protected"
        else: r.transport.ca_file = "/unselected/private-canary"
        with pytest.raises(BindingError): capture.admit()
    assert r.requests == []


@pytest.mark.parametrize("change", ["wall-expired", "mono-expired", "wall-regression", "mono-regression", "renew-wall", "renew-mono", "replace-ledger"])
def test_original_decision_cannot_reset_extend_or_survive_expiry(runner, change):
    r = runner
    use = r.stage.use()
    capture = r.capture(decision=use)
    if change == "wall-expired": r.stage.v.h.now = use.deadline
    elif change == "mono-expired": r.stage.v.c.r.clock.mono = use.end
    elif change == "wall-regression": r.stage.v.h.now -= 1
    elif change == "mono-regression": r.stage.v.c.r.clock.mono -= 1
    elif change == "renew-wall": use.deadline += 1
    elif change == "renew-mono": use.end += 1
    else: use._hosted_reads = dict(use._hosted_reads)
    with pytest.raises(BindingError): capture.admit()
    assert r.requests == []


def test_qualification_allocation_is_preserved_without_join_or_upgrade(runner):
    r = runner
    use = r.stage.use()
    start_qualification(use)
    budget = ReadBudget(use)
    for _ in range(39): budget.consume("private")
    capture = r.capture(decision=use)
    assert capture.admit().state == "plan-ready"
    assert budget.count("private") == 39
    assert budget.github_requests == 0
    with pytest.raises(BindingError): budget.consume("private")
    with pytest.raises(BindingError): budget.join(r.stage.use())


def test_tls_send_cancellation_reaps_child_before_request(runner, monkeypatch):
    r = runner
    children = []
    original_popen, original_exchange = subprocess.Popen, Https.exchange
    def popen(*a, **kw):
        child = original_popen(*a, **kw); children.append(child); return child
    def exchange(transport, *a, before_send, **kw):
        def cancelled(): before_send(); raise KeyboardInterrupt("private-canary")
        return original_exchange(transport, *a, before_send=cancelled, **kw)
    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr(Https, "exchange", exchange)
    capture = r.capture()
    with pytest.raises(KeyboardInterrupt) as error: capture.admit()
    assert str(error.value) == ""
    assert error.value.__context__ is None
    assert r.requests == []
    assert children
    assert all(p.poll() is not None for p in children)
    assert all(p.stdin.closed for p in children)
    assert all(p.stdout.closed for p in children)
    with pytest.raises(BindingError): capture.admit()


@pytest.mark.parametrize("operation", [repr, pickle.dumps, copy.copy, copy.deepcopy, vars, asdict])
def test_capture_cannot_export_private_runner_material(runner, operation):
    capture = runner.capture()
    if operation is repr:
        value = operation(capture)
    else:
        with pytest.raises((BindingError, TypeError)) as error:
            operation(capture)
        value = str(error.value)
    assert SECRET not in value
    assert runner.endpoint not in value


def test_canary_exception_has_no_retained_cause_or_context(runner):
    r = runner
    class Broken(dict):
        def get(self, key): raise ValueError(SECRET + r.endpoint)
    with pytest.raises(BindingError) as error: r.capture(environment=Broken(r.environment))
    assert str(error.value) == ERROR
    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    assert SECRET not in repr(error.value)


def test_default_operational_binding_still_refuses_before_acquisition(runner):
    with pytest.raises(BindingError, match="^workflow-operational-host-unselected$"): operational_bindings()
    assert runner.requests == []


def test_large_valid_signed_jwt_fits_intrinsic_post_without_truncation(runner, monkeypatch):
    r = runner
    claims = json.loads(decode64(r.token.split(".")[1]))
    # Build a genuine signed near-limit JWT independently of the product limit.
    candidates = []
    for size in range(11000, 12000):
        claims["fixture_padding"] = "x" * size
        token = jwt(r.stage.v.h.issuer_key, claims)
        if len(token) in (16376, 16377):
            candidates.append(token)
            break
    assert candidates
    r.token = candidates[0]
    observe_post(monkeypatch, r)
    assert r.capture().admit().state == "plan-ready"
    assert len(r.posts) == 1
    assert r.posts[0][2] == "Bearer " + r.token


@pytest.mark.parametrize("change", ["wall", "monotonic", "earlier-expiry"])
def test_get_cannot_renew_remaining_time_or_post_after_expiry(runner, monkeypatch, change):
    r = runner
    observe_post(monkeypatch, r)
    use = r.stage.use()
    if change == "earlier-expiry": use.clip(r.stage.v.h.now + 2)
    capture = r.capture(decision=use)
    def expire():
        if change == "monotonic": r.stage.v.c.r.clock.mono = use.end
        else: r.stage.v.h.now = use.deadline
    r.after_get = expire
    with pytest.raises(BindingError): capture.admit()
    assert len(r.requests) == 1
    assert r.posts == []


@pytest.mark.parametrize("group", ["private", "source", "protection", "control", "correlation"])
def test_observed_read_charges_cannot_regress_before_send(runner, group):
    r = runner
    use = r.stage.use()
    budget = ReadBudget(use)
    if group == "correlation": budget.consume_correlation()
    else: budget.consume(group)
    capture = r.capture(decision=use)
    if group == "correlation": use.api_requests = 0
    else: budget.state["counts"][group] = 0
    with pytest.raises(BindingError): capture.admit()
    assert r.requests == []



@pytest.mark.parametrize("field", [URL, BEARER])
def test_non_string_injection_drift_cannot_forge_equality(runner, field):
    r = runner
    capture = r.capture()
    r.environment[field] = EqualityAlias("substituted-private-canary")
    with pytest.raises(BindingError): capture.admit()
    assert r.requests == []


def test_non_string_original_endpoint_cannot_authenticate_itself(runner):
    r = runner
    environment = {URL: EqualityAlias("https://unselected.invalid/token"), BEARER: SECRET}
    with pytest.raises(BindingError): r.capture(environment=environment)
    assert r.requests == []


@pytest.mark.parametrize("target", ["capture", "token-transport"])
def test_normal_state_hook_cannot_export_runner_material(runner, target):
    r = runner
    capture = r.capture()
    selected = capture if target == "capture" else capture._token_client.transport
    with pytest.raises(BindingError, match="^" + ERROR + "$") as caught:
        selected.__getstate__()
    assert str(caught.value) == ERROR
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert SECRET not in repr(caught.value)
    assert r.endpoint not in repr(caught.value)
    assert r.requests == []
