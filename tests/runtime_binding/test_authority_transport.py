"""Actual separate-process mTLS. Network failures never qualify role denial."""
from dataclasses import replace
import http.client
import ssl

import pytest

from workload_factory_binding.evidence import BindingError, canonical
from workload_factory_binding_runtime.bootstrap import bootstrap
from workload_factory_binding_runtime.reference_authority.client import AuthorityClient, AuthoritySession, probe_worker_denied
from .authority_fixture import a, approve, assigned, authorization, b, w, c, configuration, l


def selected(a, *, permissions=None):
    service = a.launch(permissions)
    clients = service.clients
    clients["operator"].request("authorize", deadline=a.now + 10, **authorization(a))
    clients["controller"].request("observe", deadline=a.now + 10, envelope=a.envelope())
    return service


def test_real_mtls_roles_bootstrap_admission_restart_and_revocation(a):
    service = selected(a)
    reader = service.clients["reader"]
    session = AuthoritySession(reader, context=a.b.context, event_ref="event:assigned", deadline=a.now + 10)
    result = bootstrap(a.b.context, bindings=session.bindings(a.b.w.bindings))
    assert result.run_id == a.b.context.run_id
    assert result.config_digest == session.value["bootstrap"]["config_digest"]
    assert a.b.w.c.h.calls == 0
    probe_worker_denied(service.clients["worker"], context=a.b.context, event_ref="event:assigned", deadline=a.now + 10)
    service.process.kill();service.process.wait(timeout=5)
    service = a.launch()
    restarted = AuthoritySession(service.clients["reader"], context=a.b.context,
                                 event_ref="event:assigned", deadline=a.now + 10)
    assert restarted.value == session.value
    service.clients["operator"].request("revoke", ref=a.b.context.preauthorization_ref, deadline=a.now + 10)
    with pytest.raises(BindingError):
        bootstrap(a.b.context, bindings=restarted.bindings(a.b.w.bindings))


@pytest.mark.parametrize("role,method", [("worker", "authorize"), ("worker", "observe"), ("worker", "claim"),
    ("worker", "operation"), ("worker", "revoke"), ("reader", "authorize"), ("reader", "observe"),
    ("reader", "revoke"), ("controller", "authorize"), ("controller", "claim"), ("operator", "observe"),
    ("operator", "claim")])
def test_peer_role_cannot_be_elevated_by_body(a, role, method):
    service = selected(a)
    arguments = {"authorize": authorization(a), "observe": {"envelope": a.envelope()},
                 "revoke": {"ref": a.b.context.preauthorization_ref},
                 "claim": assigned(a), "operation": assigned(a)}[method]
    with pytest.raises(BindingError, match="^bootstrap-authority-denied$"):
        service.clients[role].request(method, deadline=a.now + 10, **arguments)
    # Actual positive path disambiguates outage/invalid TLS from refusal.
    assert AuthoritySession(service.clients["reader"], context=a.b.context,
                            event_ref="event:assigned", deadline=a.now + 10).value["scope"] == "isolated-fixture"


def test_excess_worker_permission_breaks_denial_probe(a):
    service = selected(a, permissions={a.peers["operator"][2]: ["authorize", "revoke"],
        a.peers["controller"][2]: ["observe"], a.peers["reader"][2]: ["claim", "operation"],
        a.peers["worker"][2]: ["claim"]})
    service.clients["reader"].request("claim", deadline=a.now + 10, **assigned(a))
    with pytest.raises(BindingError, match="^bootstrap-authority-refused$"):
        probe_worker_denied(service.clients["worker"], context=a.b.context,
                            event_ref="event:assigned", deadline=a.now + 10)


def test_authority_outage_does_not_count_as_worker_denial(a):
    service = selected(a)
    service.clients["reader"].request("claim", deadline=a.now + 10, **assigned(a))
    service.process.kill();service.process.wait(timeout=5)
    with pytest.raises(BindingError):
        probe_worker_denied(service.clients["worker"], context=a.b.context,
                            event_ref="event:assigned", deadline=a.now + 10)


@pytest.mark.parametrize("change", ["pin", "ca", "certificate"])
def test_selected_server_and_mutual_certificate_are_required(a, change):
    service = selected(a)
    client = service.clients["reader"]
    if change == "pin":client.server_fingerprint = "sha256:" + "0" * 64
    elif change == "ca":client.tls = ssl.create_default_context()
    else:
        client.tls = ssl.create_default_context(cafile=a.ca)  # no client certificate
    with pytest.raises(BindingError, match="^workflow-input-unavailable$"):
        client.request("claim", deadline=a.now + 10, **assigned(a))


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1.5}', b'[]', b'x' * 65537,
    b'{"method":"claim","arguments":{"peer":"operator"}}', b'{"method":"claim","arguments":{},"principal":"operator"}'])
def test_malformed_bounded_wire_input_is_safely_refused(a, raw):
    service = selected(a)
    client = service.clients["reader"]
    connection = http.client.HTTPSConnection("127.0.0.1", service.port, context=client.tls, timeout=3)
    try:
        connection.request("POST", "/", body=raw, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        assert response.status == 400
        assert response.read() == b'{"error":"bootstrap-authority-refused"}'
    finally:
        connection.close()


def test_lost_response_after_binding_never_allows_another_run(a):
    service = selected(a)
    # Send a complete request then discard its response. Commit outcome is ambiguous
    # to this caller; a restart must consult retained state rather than compensate.
    client = service.clients["reader"]
    connection = http.client.HTTPSConnection("127.0.0.1", service.port, context=client.tls, timeout=3)
    connection.request("POST", "/", body=canonical(dict(method="claim", arguments=assigned(a))),
                       headers={"Content-Type": "application/json"})
    response = connection.getresponse()
    assert response.status == 200  # service committed; intentionally do not consume body
    connection.close()
    service.process.kill();service.process.wait(timeout=5)
    other = replace(a.b.context, run_attempt="2")
    a.store.observe(envelope=a.envelope(other, "event:retry"))
    service = a.launch()
    with pytest.raises(BindingError):
        AuthoritySession(service.clients["reader"], context=other, event_ref="event:retry", deadline=a.now + 10)
    assert AuthoritySession(service.clients["reader"], context=a.b.context,
                            event_ref="event:assigned", deadline=a.now + 10).value["bootstrap"]["run_attempt"] == "1"


@pytest.mark.parametrize("mode", ["redirect", "duplicate-length", "duplicate-json", "oversized", "slow"])
def test_actual_response_errors_and_total_deadline_fail_closed(a, mode):
    from http.server import BaseHTTPRequestHandler
    import threading
    import time
    from workload_factory_binding_runtime.reference_authority.transport import AuthorityServer
    class Reply(BaseHTTPRequestHandler):
        def log_message(self, *args):pass
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            raw = b'{"a":1,"a":2}' if mode == "duplicate-json" else b'{"ok":true}'
            self.send_response(302 if mode == "redirect" else 200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(65537 if mode == "oversized" else len(raw)))
            if mode == "duplicate-length":self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            try:
                for byte in raw:
                    self.wfile.write(bytes([byte]));self.wfile.flush()
                    if mode == "slow":time.sleep(0.3)
            except OSError:pass
    with AuthorityServer(store=a.store, ca_file=a.ca, cert_file=a.peers["server"][0],
                         key_file=a.peers["server"][1], permissions={a.peers["reader"][2]: frozenset({"claim"})}) as server:
        server.RequestHandlerClass = Reply
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05})
        thread.start()
        try:
            client = AuthorityClient(port=server.server_port, ca_file=a.ca, cert_file=a.peers["reader"][0],
                key_file=a.peers["reader"][1], server_fingerprint=a.peers["server"][2], clock=lambda: a.now)
            started = time.monotonic()
            with pytest.raises(BindingError, match="^workflow-input-unavailable$"):
                client.request("claim", deadline=a.now + 2, **assigned(a))
            assert time.monotonic() - started < 3
        finally:
            server.shutdown();thread.join(timeout=3)
            assert not thread.is_alive()
