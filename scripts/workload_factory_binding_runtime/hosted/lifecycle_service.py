"""Selected private mTLS lifecycle ports and independent scheduler logic.

No listener/scheduler is started on import or by default CLI/workflow bindings.
Listener construction and certificate permissions are trusted hosting choices.
"""
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import secrets
import ssl
import threading
from workload_factory_binding.evidence import BindingError, byte_digest, canonical, digest, integer, require, valid_digest
from ..config import _handle
from ..github_bootstrap.common import Decision, document
from ..lifecycle import RunScope, ResourceReadback, CleanupReadback, LeaseReadback
from ..loaders import BoundService
from .private_http import PrivateHttps, Response
from .readback import ReadBudget, PROFILE as OBSERVATION_PROFILE
from .lifecycle import HostedLifecycle, _state, _closed, run_plan
from .lifecycle_store import LifecycleStore, ERROR

PROFILE = "openxfactory-hosted-lifecycle-internal-v1"
PRIMARY = frozenset({"register", "generation", "prepare", "release", "cleanup", "lease", "status"})
AUDIT = frozenset({"ack-stage", "ack-final", "cleanup-audit", "stage-lease"})
EXTRA = {"register": {"unit_digest"}, "cleanup": {"outcome"}, "lease": {"plan_ref"},
         "cleanup-audit": {"attempt_ref"}}


def _resources(values):
    require(type(values) is list and 1 <= len(values) <= 64, ERROR)
    refs = set()
    for value in values:
        _closed(value, "ref instance_ref present revoked")
        _handle(value["ref"])
        _handle(value["instance_ref"])
        require(type(value["present"]) is bool and type(value["revoked"]) is bool
                and value["ref"] not in refs, ERROR)
        refs.add(value["ref"])


def _facts(operation, value, scope, extra, principal, decision):
    fields = {
        "register": "registration_digest", "prepare": "plan_digest", "release": "state plan_digest",
        "cleanup": "state owner", "generation": "generation resource",
        "status": "registration_digest owner closed expires_at cleanup_until generation_bound",
        "ack-stage": "scope_digest unit_digest state expires_at registration_digest",
        "ack-final": "registration_digest plan_digest generation_digest observed_at expires_at principal_ref",
        "lease": "plan_digest scope status issued_at expires_at observed_at valid_until",
    }
    if operation in fields:
        _closed(value, fields[operation])
    for name in ("registration_digest", "plan_digest", "generation_digest", "scope_digest", "unit_digest"):
        if name in value:
            require(valid_digest(value[name]), ERROR)
    if operation == "generation":
        generation, resource = value["generation"], value["resource"]
        _closed(generation, "unit_digest pid start_time session_id boot_id uid policy_digest cgroup_digest")
        _closed(resource, "ref instance_ref kind retention")
        _handle(resource["ref"])
        require(all(type(generation[k]) is int and generation[k] > 0 for k in ("pid", "start_time", "session_id", "uid"))
                and generation["pid"] == generation["session_id"] and generation["uid"] == scope["worker_uid"]
                and generation["boot_id"] == scope["boot_id"] and generation["policy_digest"] == scope["hosting_selection_digest"]
                and all(valid_digest(generation[k]) for k in ("unit_digest", "policy_digest", "cgroup_digest"))
                and resource["kind"] == "process" and resource["retention"] == "run"
                and resource["instance_ref"] == f"process:{generation['pid']}:{generation['start_time']}", ERROR)
    if operation in ("cleanup", "status"):
        require(value["owner"] in ("stage", "final"), ERROR)
    if operation == "cleanup":
        require(value["state"] == "cleanup-requested", ERROR)
    if operation == "release":
        require(value["state"] == "final-owned", ERROR)
    if operation == "status":
        require(type(value["closed"]) is bool and type(value["generation_bound"]) is bool
                and integer(value["expires_at"]) and integer(value["cleanup_until"])
                and value["expires_at"] < value["cleanup_until"], ERROR)
    if operation == "ack-stage":
        require(value["scope_digest"] == digest(scope) and value["state"] == "acknowledged"
                and integer(value["expires_at"]) and decision.now() < value["expires_at"], ERROR)
    if operation == "ack-final":
        require(value["principal_ref"] == principal and integer(value["observed_at"]) and integer(value["expires_at"])
                and value["observed_at"] <= decision.now() < value["expires_at"] <= value["observed_at"] + 60, ERROR)
    if operation == "lease":
        _closed(value["scope"], "config_digest case_ref run_id run_attempt lease_ref cleanup_ref receipt_retention_ref")
        require(value["status"] in ("active", "closed", "revoked", "cancelled")
                and all(integer(value[k]) for k in ("issued_at", "expires_at", "observed_at", "valid_until"))
                and value["scope"]["case_ref"] == scope["case_ref"] and value["scope"]["run_id"] == scope["run_id"]
                and value["scope"]["run_attempt"] == scope["run_attempt"]
                and value["scope"]["cleanup_ref"] == scope["cleanup_ref"], ERROR)
    if operation == "cleanup-audit":
        require(value.get("kind") in ("stage", "final"), ERROR)
        if value["kind"] == "stage":
            _closed(value, "kind registration_digest scope_digest resources attempt_ref observed_at expires_at")
            require(valid_digest(value["registration_digest"]) and value["scope_digest"] == digest(scope)
                    and value["attempt_ref"] == extra["attempt_ref"] and integer(value["observed_at"])
                    and integer(value["expires_at"]) and value["observed_at"] <= decision.now() < value["expires_at"], ERROR)
            _resources(value["resources"])
        else:
            _closed(value, "kind record")
            record = value["record"]
            _closed(record, "plan_digest scope lease_status resources observed_at valid_until attempt_ref")
            _closed(record["scope"], "config_digest case_ref run_id run_attempt lease_ref cleanup_ref receipt_retention_ref")
            require(valid_digest(record["plan_digest"]) and record["attempt_ref"] == extra["attempt_ref"]
                    and record["lease_status"] in ("closed", "revoked", "cancelled")
                    and all(record["scope"][k] == scope[k] for k in ("case_ref", "run_id", "run_attempt", "cleanup_ref"))
                    and integer(record["observed_at"]) and integer(record["valid_until"])
                    and record["observed_at"] <= decision.now() < record["valid_until"], ERROR)
            _resources(record["resources"])


class LifecycleServer(ThreadingMixIn, HTTPServer):
    daemon_threads = False
    block_on_close = True
    request_queue_size = 8

    def __init__(self, *, lifecycle, mode, principal, cert_file, key_file, ca_file,
                 permissions, clock, monotonic, load_final=None, observation_scope=None, listen=("127.0.0.1", 0)):
        require(type(lifecycle) is HostedLifecycle and mode in ("primary", "audit")
                and type(permissions) is dict and len(permissions) <= 32
                and (mode != "primary" or callable(load_final)), ERROR)
        _handle(principal)
        allowed = PRIMARY if mode == "primary" else AUDIT
        require(all(valid_digest(k) and type(v) is frozenset and v <= allowed for k, v in permissions.items()), ERROR)
        self.lifecycle, self.mode, self.principal = lifecycle, mode, principal
        self.permissions = dict(permissions)
        self.clock, self.monotonic, self.load_final = clock, monotonic, load_final
        self.observation_scope = observation_scope
        self.slots = threading.BoundedSemaphore(8)
        self.tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.tls.minimum_version = ssl.TLSVersion.TLSv1_2
        self.tls.verify_mode = ssl.CERT_REQUIRED
        self.tls.load_verify_locations(cafile=ca_file)
        self.tls.load_cert_chain(cert_file, key_file)
        super().__init__(listen, _Handler)

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(2)
        return request, address

    def finish_request(self, request, address):
        with self.tls.wrap_socket(request, server_side=True) as secured:
            self.RequestHandlerClass(secured, address, self)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()

    def handle_error(self, request, address):
        pass


class _Handler(BaseHTTPRequestHandler):
    server_version = "HostedLifecycle"
    sys_version = ""

    def setup(self):
        super().setup()
        self.timer = threading.Timer(10, self._expire)
        self.timer.daemon = True
        self.timer.start()

    def _expire(self):
        try:
            self.connection.shutdown(2)
        except OSError:
            pass

    def finish(self):
        self.timer.cancel()
        self.timer.join(timeout=1)
        super().finish()

    def log_message(self, *_args):
        pass

    def _reply(self, status, value):
        raw = canonical(value)
        require(len(raw) <= 65536, ERROR)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True

    def send_error(self, *_args, **_kwargs):
        self._reply(400, {"error": ERROR})

    def do_POST(self):
        try:
            decision = Decision(clock=self.server.clock, monotonic=self.server.monotonic)
            observation = self.path == "/readback"
            operation = "stage-lease" if observation else self.path.removeprefix("/lifecycle/")
            allowed = PRIMARY if self.server.mode == "primary" else AUDIT
            require(operation in allowed and (observation or self.path == "/lifecycle/" + operation), ERROR)
            peer = byte_digest(self.connection.getpeercert(binary_form=True))
            permitted = operation in self.server.permissions.get(peer, frozenset())
            require(sum(len(k) + len(v) for k, v in self.headers.items()) <= 32768
                    and self.headers.get_all("Content-Type") == ["application/json"]
                    and self.headers.get("Transfer-Encoding") is None, ERROR)
            lengths = self.headers.get_all("Content-Length")
            require(lengths and len(lengths) == 1 and lengths[0].isascii() and lengths[0].isdigit()
                    and len(lengths[0]) <= 5 and 0 < int(lengths[0]) <= 65536, ERROR)
            raw = self.rfile.read(int(lengths[0]))
            require(len(raw) == int(lengths[0]), ERROR)
            if not permitted:
                self._reply(403, {"error": "hosted-lifecycle-denied"})
                return
            value = document(raw)
            before = decision.now()
            if observation:
                _closed(value, "profile operation reference nonce")
                require(value["profile"] == OBSERVATION_PROFILE and value["operation"] == "stage-lease"
                        and self.server.observation_scope is not None, ERROR)
                facts = self.server.lifecycle.stage_lease(value["reference"], decision=decision)
                self._reply(200, {"profile": OBSERVATION_PROFILE, "principal_ref": self.server.principal,
                    "operation": "stage-lease", "reference": value["reference"], "nonce": value["nonce"],
                    "scope": self.server.observation_scope.record(), "facts": facts,
                    "observed_at": before, "expires_at": decision.deadline})
                return
            _closed(value, "profile nonce deadline arguments")
            require(value["profile"] == PROFILE and type(value["nonce"]) is str and len(value["nonce"]) == 64
                    and all(c in "0123456789abcdef" for c in value["nonce"]), ERROR)
            decision.clip(value["deadline"])
            args = value["arguments"]
            require(type(args) is dict and set(args) == {"launch_ref", "scope_digest"} | EXTRA.get(operation, set())
                    and args["launch_ref"] == self.server.lifecycle.scope["launch_ref"]
                    and args["scope_digest"] == digest(self.server.lifecycle.scope), ERROR)
            life, ref = self.server.lifecycle, args["launch_ref"]
            if operation == "register":
                facts = life.register(ref, args["unit_digest"], decision=decision)
            elif operation == "generation":
                facts = life.bind_generation(ref, decision=decision)
            elif operation == "prepare":
                finalized, plan = self.server.load_final(ref, deadline=decision.deadline)
                from .finalization import register_finalized_lifecycle
                facts = register_finalized_lifecycle(finalized, life.context, lifecycle=life, plan=plan, decision=decision)
            elif operation == "release":
                facts = life.release_stage(ref, decision=decision)
            elif operation == "cleanup":
                facts = life.cleanup(ref, args["outcome"], decision=decision)
            elif operation == "lease":
                facts = asdict(life.final_lease(args["plan_ref"], decision=decision))
            elif operation == "ack-stage":
                facts = life.acknowledge_stage(ref, decision=decision)
            elif operation == "ack-final":
                facts = life.acknowledge_final(ref, decision=decision)
            elif operation == "cleanup-audit":
                facts = life.audit_cleanup(ref, args["attempt_ref"], decision=decision)
            else:
                state = life._registration(ref, decision)
                reg = state["registration"]
                facts = {"registration_digest": digest(reg), "owner": "final" if state["released"] else "stage",
                    "closed": state["closed"], "expires_at": run_plan(state["final"]["plan"]).expires_at if state["released"] else reg["expires_at"],
                    "cleanup_until": reg["cleanup_until"], "generation_bound": state["generation"] is not None}
            decision.now()
            self._reply(200, {"profile": PROFILE, "principal_ref": self.server.principal, "nonce": value["nonce"],
                "operation": operation, "scope_digest": digest(life.scope), "facts": facts,
                "observed_at": before, "expires_at": decision.deadline})
        except Exception:
            try:
                self._reply(400, {"error": ERROR})
            except OSError:
                pass


class LifecycleClient:
    def __init__(self, *, origin, principal, scope, transport):
        _handle(principal)
        require(type(transport) is PrivateHttps and transport.lifecycle_origin == origin
                and type(scope) is dict and valid_digest(transport.server_certificate_digest), ERROR)
        self.origin, self.principal, self.transport, self.raw = origin, principal, transport, canonical(scope)
        self.binding = (origin, principal, transport.server_certificate_digest, transport.materials(), digest(scope))

    def current(self):
        require(self.binding == (self.origin, self.principal, self.transport.server_certificate_digest, self.transport.materials(), digest(document(self.raw)))
                and self.transport.lifecycle_origin == self.origin, ERROR)

    def call(self, operation, *, decision, accounted=False, **extra):
        self.current()
        require(operation in (PRIMARY | AUDIT) - {"stage-lease"} and set(extra) == EXTRA.get(operation, set()), ERROR)
        if not accounted:
            ReadBudget(decision).consume("private")
        scope = document(self.raw)
        nonce = secrets.token_hex(32)
        body = {"profile": PROFILE, "nonce": nonce, "deadline": decision.deadline,
                "arguments": {"launch_ref": scope["launch_ref"], "scope_digest": digest(scope), **extra}}
        before = decision.now()
        response = self.transport.exchange("POST", self.origin + "/lifecycle/" + operation,
            headers={"Content-Type": "application/json", "Accept": "application/json"}, body=canonical(body),
            decision=decision, before_send=lambda: ReadBudget(decision).check())
        self.current()
        require(type(response) is Response and response.status == 200, ERROR)
        value = document(response.body)
        _closed(value, "profile principal_ref nonce operation scope_digest facts observed_at expires_at")
        require(value["profile"] == PROFILE and value["principal_ref"] == self.principal
                and value["nonce"] == nonce and value["operation"] == operation and value["scope_digest"] == digest(scope)
                and type(value["facts"]) is dict and integer(value["observed_at"]) and integer(value["expires_at"])
                and before <= value["observed_at"] <= decision.now() < value["expires_at"] <= value["observed_at"] + 60, ERROR)
        decision.clip(value["expires_at"])
        _facts(operation, value["facts"], scope, extra, self.principal, decision)
        return value["facts"]


class CleanupRegistration:
    """Trusted opt-in callback retaining the controller's original Decision."""
    def __init__(self, primary, audit):
        require(type(primary) is LifecycleClient and type(audit) is LifecycleClient
                and primary.raw == audit.raw and primary.origin != audit.origin
                and primary.principal != audit.principal, ERROR)
        self.primary, self.audit = primary, audit

    def register(self, scope, unit, *, decision):
        require(canonical(scope) == self.primary.raw, ERROR)
        registered = self.primary.call("register", unit_digest=digest(unit), decision=decision, accounted=True)
        acknowledged = self.audit.call("ack-stage", decision=decision)
        require(registered["registration_digest"] == acknowledged["registration_digest"]
                and acknowledged["scope_digest"] == digest(scope) and acknowledged["unit_digest"] == digest(unit), ERROR)


    __call__ = register


class FinalLifecyclePorts:
    """Existing RunLifecycle ports; cleanup gets one separate bounded Decision.

    A cleanup writer timeout leaves that same Decision available to the separate
    audit read. It never retries the mutation or revives the operation Decision.
    """
    def __init__(self, *, primary, audit, operation, plan_ref, clock, monotonic):
        require(type(primary) is LifecycleClient and type(audit) is LifecycleClient
                and primary.raw == audit.raw and primary.origin != audit.origin
                and type(operation) is Decision, ERROR)
        _handle(plan_ref)
        self.plan_ref = plan_ref
        self.primary, self.audit, self.operation = primary, audit, operation
        self.clock, self.monotonic = clock, monotonic
        self.local = threading.local()

    def read_lease(self, ref, *, deadline):
        require(ref == self.plan_ref, ERROR)
        self.operation.clip(deadline)
        value = self.primary.call("lease", plan_ref=ref, decision=self.operation)
        _closed(value, "plan_digest scope status issued_at expires_at observed_at valid_until")
        value["scope"] = RunScope(**value["scope"])
        return LeaseReadback(**value)

    def finalize(self, ref, *, deadline):
        require(ref == self.plan_ref, ERROR)
        self.local.cleanup = Decision(clock=self.clock, monotonic=self.monotonic, deadline=deadline)
        HostedLifecycle.narrow(self.local.cleanup, deadline)
        self.primary.call("cleanup", outcome="failure", decision=self.local.cleanup)

    def read_cleanup(self, ref, *, attempt_ref, deadline):
        require(ref == self.plan_ref, ERROR)
        decision = getattr(self.local, "cleanup", None)
        require(type(decision) is Decision, ERROR)
        HostedLifecycle.narrow(decision, deadline)
        value = self.audit.call("cleanup-audit", attempt_ref=attempt_ref, decision=decision)
        require(value["kind"] == "final", ERROR)
        record = value["record"]
        _closed(record, "plan_digest scope lease_status resources observed_at valid_until attempt_ref")
        record["scope"] = RunScope(**record["scope"])
        record["resources"] = tuple(ResourceReadback(**r) for r in record["resources"])
        return CleanupReadback(**record)


class IndependentScheduler:
    def __init__(self, *, intake, client, clock, monotonic):
        require(type(intake) is LifecycleStore and intake.kind == "scheduler" and type(client) is LifecycleClient, ERROR)
        self.intake, self.client, self.clock, self.monotonic = intake, client, clock, monotonic
        self.next_discovery = None

    def tick(self):
        decision = Decision(clock=self.clock, monotonic=self.monotonic)
        events = self.intake.events(decision=decision)
        if any(e["kind"] == "cleanup-request" for e in events):
            return "reconcile-only"
        expiries = [e["data"]["expires_at"] for e in events if e["kind"] in ("stage-intake", "final-intake")]
        if expiries:
            if decision.now() < min(expiries):
                return "active"
        else:
            # Registration may have committed before scheduler-intake delivery
            # was interrupted. Discover only this preselected scope by reads;
            # never replay registration or manufacture a launch acknowledgement.
            decision.now()
            if self.next_discovery is not None and decision.last_mono < self.next_discovery:
                return "awaiting-registration"
            self.next_discovery = decision.last_mono + 1
        status = self.client.call("status", decision=decision)
        decision.clip(status["cleanup_until"])
        if decision.now() < status["expires_at"]:
            return "active"
        def consume(events, append):
            if any(e["kind"] == "cleanup-request" for e in events):
                return False
            append("cleanup-request", {"scope_digest": digest(document(self.client.raw))})
            return True
        if not self.intake.mutate(consume, decision=decision):
            return "reconcile-only"
        self.client.call("cleanup", outcome="expired", decision=decision)
        return "cleanup-requested"


def probe_worker_denial(client, operation, *, decision, **extra):
    require(type(client) is LifecycleClient and set(extra) == EXTRA.get(operation, set()), ERROR)
    client.current()
    ReadBudget(decision).consume("private")
    scope = document(client.raw)
    raw = canonical({"profile": PROFILE, "nonce": secrets.token_hex(32), "deadline": decision.deadline,
        "arguments": {"launch_ref": scope["launch_ref"], "scope_digest": digest(scope), **extra}})
    response = client.transport.exchange("POST", client.origin + "/lifecycle/" + operation,
        headers={"Content-Type": "application/json", "Accept": "application/json"}, body=raw, decision=decision)
    client.current()
    require(type(response) is Response and response.status == 403
            and document(response.body) == {"error": "hosted-lifecycle-denied"}, ERROR)
    return {"outcome": "denied", "service_ref": client.principal}
