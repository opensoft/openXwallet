"""Fixture RPC control-plane denials; same-user TLS is not deployed isolation."""
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dataclasses import replace
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ssl
from threading import Thread
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import BindingError, canonical, decode_object, encode64, verify_observation
from workload_factory_binding_runtime.loaders import BoundService, ServiceIdentity
from workload_factory_binding_runtime.supervisor import SupervisorPeer, SupervisedBridge
from factory_binding.test_owner_integration import make_pki, owner_source
from .supervisor_fixture import s, c, configuration


@pytest.fixture
def rpc(s, tmp_path):
    owner_source()
    from openwallet_runtime.custody import TLSClient
    ca, server_peer, gate_peer, worker_peer = make_pki(tmp_path / "observer-pki")
    admin_ca, _server, admin_peer, _worker = make_pki(tmp_path / "admin-pki", ca_common_name="isolated admin CA")
    gate_identity = (s.peer.principal_ref, s.peer.credential_ref)
    state = SimpleNamespace(allow_worker_as_gate=False, admitted=0)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            try:
                peer = hashlib.sha256(self.connection.getpeercert(binary_form=True)).hexdigest()
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192:
                    self.send_error(400)
                    return
                payload = decode_object(self.rfile.read(length))
                if self.path == "/fixture/observe":
                    if peer != gate_peer[2] and not (state.allow_worker_as_gate and peer == worker_peer[2]):
                        self.send_error(403)
                        return
                    authenticated = SupervisorPeer(*gate_identity, s.h.now - 1, s.h.now + 30)
                    deadline = payload.pop("deadline", s.h.now + 30)
                    result = s.observer.observe(payload, peer=authenticated, deadline=deadline)
                    state.admitted += 1
                    state.last_expiry = result["payload"]["expires_at"]
                elif self.path == "/fixture/admin/policy":
                    if peer != admin_peer[2]:
                        self.send_error(403)
                        return
                    if payload["operation"] == "replace_gate":
                        s.observer.allowed_gate = tuple(payload["allowed_gate"])
                    result = {"allowed_gate": list(s.observer.allowed_gate)}
                elif self.path == "/fixture/admin/key":
                    if peer != admin_peer[2]:
                        self.send_error(403)
                        return
                    if payload["operation"] == "rotate":
                        s.observer._private_key = Ed25519PrivateKey.generate()
                    elif payload["operation"] != "read_public":
                        self.send_error(405)
                        return
                    result = {"public_key": encode64(s.observer._private_key.public_key().public_bytes_raw())}
                else:
                    self.send_error(404)
                    return
                body = canonical(result)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_error(403)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(str(server_peer[0]), str(server_peer[1]))
    context.load_verify_locations(cafile=str(ca))
    context.load_verify_locations(cafile=str(admin_ca))
    context.verify_mode = ssl.CERT_REQUIRED
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = "https://127.0.0.1:" + str(server.server_port)

    def client(peer):
        return TLSClient(endpoint, ca_file=ca, certificate=peer[0], private_key=peer[1], timeout=2)
    state.gate, state.worker, state.admin = client(gate_peer), client(worker_peer), client(admin_peer)

    class Connector:
        def observe(self, payload, *, deadline):
            assert s.h.now < deadline
            return canonical(state.gate._post("/fixture/observe", {**payload, "deadline": deadline}))
    supervisor = BoundService(ServiceIdentity(**s.config["services"]["supervisor"]), Connector())
    state.bridge = SupervisedBridge(bridge=s.bridge, supervisor=supervisor)
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def assert_worker_denied(rpc, payload):
    from openwallet_runtime.proof import ProofError
    try:
        rpc.worker._post("/fixture/observe", payload)
    except ProofError as error:
        if str(error) != "service-refused":
            raise AssertionError("worker denial was not established") from None
        return
    raise AssertionError("worker observation was admitted")


def test_authenticated_gate_gets_independent_measured_observation(s, rpc):
    result = rpc.bridge.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert result["human_approval"] is False
    assert s.h.calls == 1
    assert rpc.admitted == 1


def test_worker_valid_observation_request_is_denied(s, rpc):
    payload = s.payload()
    gate_observation = rpc.gate._post("/fixture/observe", payload)
    verify_observation(gate_observation, policy=s.h.policy, request=s.h.request, token=s.h.token,
                       challenge=s.h.challenge, claims=s.h.claims, now=s.h.now)
    assert_worker_denied(rpc, payload)
    assert rpc.admitted == 1
    assert s.h.calls == 0


def test_denial_probe_detects_excess_worker_permission(s, rpc):
    rpc.allow_worker_as_gate = True
    payload = s.payload()
    with pytest.raises(AssertionError, match="^worker observation was admitted$"):
        assert_worker_denied(rpc, payload)
    assert rpc.admitted == 1


@pytest.mark.parametrize("path,payload", [
    ("/fixture/admin/policy", {"operation": "read"}),
    ("/fixture/admin/policy", {"operation": "replace_gate", "allowed_gate": ["principal:other", "credential:other"]}),
    ("/fixture/admin/key", {"operation": "read_public"}),
    ("/fixture/admin/key", {"operation": "rotate"}),
    ("/fixture/admin/key", {"operation": "export_private"}),
])
def test_worker_cannot_read_or_change_supervisor_control_plane(s, rpc, path, payload):
    from openwallet_runtime.proof import ProofError
    with pytest.raises(ProofError):
        rpc.worker._post(path, payload)
    result = rpc.bridge.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert result["human_approval"] is False
    assert s.h.calls == 1


def test_admin_policy_route_is_real_and_revokes_gate_without_worker_access(s, rpc):
    from openwallet_runtime.proof import ProofError
    change = {"operation": "replace_gate", "allowed_gate": ["principal:other", "credential:other"]}
    with pytest.raises(ProofError):
        rpc.worker._post("/fixture/admin/policy", change)
    assert rpc.admin._post("/fixture/admin/policy", change) == {"allowed_gate": change["allowed_gate"]}
    with pytest.raises(BindingError):
        rpc.bridge.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert s.h.calls == 0


def test_admin_rotation_is_real_and_unaccepted_key_refuses_observation(s, rpc):
    old = rpc.admin._post("/fixture/admin/key", {"operation": "read_public"})
    new = rpc.admin._post("/fixture/admin/key", {"operation": "rotate"})
    assert old != new
    with pytest.raises(BindingError):
        rpc.bridge.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert s.h.calls == 0


def test_worker_channel_deadline_is_forwarded_to_remote_supervisor(s, rpc):
    s.context = replace(s.context, expires_at=s.h.now + 10)
    result = rpc.bridge.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert result["human_approval"] is False
    assert rpc.last_expiry == s.h.now + 10


def test_outage_does_not_count_as_worker_denial(s):
    owner_source()
    from openwallet_runtime.proof import ProofError
    class Outage:
        def _post(self, *_args):
            raise ProofError("service-unavailable")
    fake = SimpleNamespace(worker=Outage())
    payload = s.payload()
    with pytest.raises(AssertionError, match="^worker denial was not established$"):
        assert_worker_denied(fake, payload)
