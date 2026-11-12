"""Actual loopback mTLS connectors; synthetic services, never deployed evidence."""
from dataclasses import asdict
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ssl
from threading import Thread

import pytest

from workload_factory_binding.evidence import BindingError, canonical, decode_object
from workload_factory_binding_runtime.loaders import BoundService, ServiceIdentity
from workload_factory_binding_runtime.runtime import WorkerContext
from factory_binding.test_owner_integration import make_pki, owner_source
from .composition_fixture import c, configuration


@pytest.fixture
def authenticated_service(c, tmp_path):
    owner_source()
    from openwallet_runtime.custody import TLSClient
    ca, server_peer, gate_peer, worker_peer = make_pki(tmp_path / "loader-pki")
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            peer = hashlib.sha256(self.connection.getpeercert(binary_form=True)).hexdigest()
            if self.path == "/fixture/channel":
                if peer != worker_peer[2]:
                    self.send_error(403)
                    return
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                value = canonical(asdict(c.context))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(value)))
                self.end_headers()
                self.wfile.write(value)
                return
            if peer != gate_peer[2]:
                self.send_error(403)
                return
            length = int(self.headers.get("Content-Length", "0"))
            if self.path != "/fixture/current" or not 0 < length <= 8192:
                self.send_error(400)
                return
            request = decode_object(self.rfile.read(length))
            role = request["role"]
            reader = {"records": c.records, "challenge": c.challenge}[role]
            calls.append(role)
            value = reader.read(request["operation"], request["reference"], deadline=c.h.now + 1)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(value)))
            self.end_headers()
            self.wfile.write(value)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(str(server_peer[0]), str(server_peer[1]))
    context.load_verify_locations(cafile=str(ca))
    context.verify_mode = ssl.CERT_REQUIRED
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = "https://127.0.0.1:" + str(server.server_port)

    def select(peer, *, ca_file=ca):
        for role in ("records", "challenge"):
            client = TLSClient(endpoint, ca_file=ca_file, certificate=peer[0], private_key=peer[1], timeout=1)

            class Connector:
                def __init__(self, selected_client, selected_role):
                    self.client, self.role = selected_client, selected_role

                def read(self, operation, reference, *, deadline):
                    assert c.h.now < deadline
                    value = self.client._post("/fixture/current", {
                        "role": self.role, "operation": operation, "reference": reference})
                    return canonical(value)
            selected = c.services[role]
            c.services[role] = BoundService(selected.identity, Connector(client, role))
        c.bridge = c.make()

    def channel(peer):
        client = TLSClient(endpoint, ca_file=ca, certificate=peer[0], private_key=peer[1], timeout=1)
        def load_context():
            value = client._post("/fixture/channel", {})
            value["identity"] = ServiceIdentity(**value["identity"])
            return WorkerContext(**value)
        c.bridge = c.make(load_worker_context=load_context)

    try:
        yield select, gate_peer, worker_peer, calls, channel
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_authenticated_current_services_support_one_isolated_proof(c, authenticated_service):
    select, gate, _worker, calls, _channel = authenticated_service
    select(gate)
    result = c.run()
    assert result["human_approval"] is False
    assert c.h.calls == 1
    assert set(calls) == {"records", "challenge"}


def test_matching_metadata_cannot_replace_actual_client_authentication(c, authenticated_service):
    select, _gate, worker, calls, _channel = authenticated_service
    select(worker)
    with pytest.raises(BindingError, match="^runtime-service-unavailable$"):
        c.run()
    assert c.h.calls == 0
    assert calls == []


def test_wrong_server_trust_refuses_before_records(c, authenticated_service, tmp_path):
    select, gate, _worker, calls, _channel = authenticated_service
    wrong_ca, *_peers = make_pki(tmp_path / "unselected-pki")
    select(gate, ca_file=wrong_ca)
    with pytest.raises(BindingError, match="^runtime-service-unavailable$"):
        c.run()
    assert c.h.calls == 0
    assert calls == []


def test_trusted_hosting_observes_actual_worker_certificate_outside_request_body(c, authenticated_service):
    select, gate, worker, _calls, channel = authenticated_service
    select(gate)
    channel(worker)
    result = c.run()
    assert c.h.calls == 1
    assert result["human_approval"] is False


def test_another_valid_certificate_cannot_claim_selected_worker_channel(c, authenticated_service):
    select, gate, _worker, calls, channel = authenticated_service
    select(gate)
    channel(gate)
    with pytest.raises(BindingError, match="^runtime-channel-unavailable$"):
        c.run()
    assert c.h.calls == 0
    assert calls == []
    assert c.r.transport.calls == []
