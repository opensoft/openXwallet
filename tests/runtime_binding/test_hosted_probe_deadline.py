"""Real mTLS deadline/ownership controls; no operational provider or dispatch."""
import base64
from dataclasses import asdict
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import ssl
from threading import Event, Thread
import time

import pytest

from factory_binding.test_owner_integration import owner_source
from workload_factory_binding.evidence import BindingError, canonical
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.qualification import WorkerProbe
from .composition_fixture import c
from .custody_fixture import k
from .test_config import configuration


def _children():
    return set(Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children").read_text().split())


@pytest.fixture
def probe(k):
    owner_source()
    from openwallet_runtime.custody import TLSClient
    from openwallet_runtime.proof import TrustedKeyBinding
    from openwallet_runtime.registry import binding_record
    binding = TrustedKeyBinding(**asdict(k.c.h.binding))
    state = {"calls": [], "fault": None, "mode": None, "stop": Event()}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            credential = hashlib.sha256(self.connection.getpeercert(binary_form=True)).hexdigest()
            phase = "excess" if self.server.excess else "resolve" if self.path == "/v0/resolve" else (
                "positive" if credential == k.gate[2] else "denial")
            state["calls"].append((phase, credential))
            status = 403 if phase == "denial" else 200
            value = {"error": "service-refused"} if status == 403 else binding_record(binding) if phase == "resolve" else {
                "signature": base64.urlsafe_b64encode(k.c.h.wallet_key.sign(base64.urlsafe_b64decode(request["message"]))).decode()}
            raw = canonical(value)
            try:
                if state["fault"] == phase and state["mode"] == "pause":
                    state["stop"].wait(2)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                if state["fault"] == phase and state["mode"] == "trickle":
                    for byte in raw:
                        self.wfile.write(bytes([byte])); self.wfile.flush()
                        if state["stop"].wait(.08):
                            break
                else:
                    self.wfile.write(raw)
            except (OSError, ssl.SSLError):
                pass
    servers = []
    for excess in (False, True):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = False
        server.excess = excess
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(k.server[0]), str(k.server[1]))
        context.load_verify_locations(cafile=str(k.ca)); context.verify_mode = ssl.CERT_REQUIRED
        server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": .02})
        thread.start(); servers.append((server, thread)); state["receiver_thread"] = thread
    def client(i, material):
        return TLSClient("https://127.0.0.1:" + str(servers[i][0].server_port), ca_file=k.ca,
            certificate=material[0], private_key=material[1], timeout=3)
    worker, positive, excess = client(0, k.worker), client(0, k.gate), client(1, k.worker)
    excess.context = worker.context
    state.update(probe=WorkerProbe(worker, positive, excess), binding=binding, worker=k.worker[2], gate=k.gate[2])
    try:
        yield state
    finally:
        state["stop"].set()
        for server, thread in servers:
            server.shutdown(); server.server_close(); thread.join(timeout=3)
            assert not thread.is_alive()


def test_probe_uses_same_loaded_credential_and_exact_four_calls_without_reload(probe, k):
    # Loaded SSLContexts, not file paths or a replacement credential, cross the boundary.
    for path in (k.ca, k.worker[0], k.worker[1], k.gate[0], k.gate[1]):
        path.unlink()
    before = _children()
    decision = Decision(clock=lambda: k.c.h.now)
    assert probe["probe"].check(b"accepted preimage", probe["binding"], now=k.c.h.now, decision=decision).startswith("sha256:")
    assert probe["calls"] == [("resolve", probe["worker"]), ("positive", probe["gate"]),
        ("denial", probe["worker"]), ("excess", probe["worker"])]
    assert decision._hosted_reads["counts"]["private"] == 4
    assert _children() == before


@pytest.mark.parametrize("phase", ["resolve", "positive", "denial", "excess"])
@pytest.mark.parametrize("mode", ["pause", "trickle"])
def test_original_decision_bounds_each_actual_tls_rpc_and_reaps_before_return(probe, k, phase, mode):
    before = _children()
    shift = [0.]
    decision = Decision(clock=lambda: k.c.h.now, monotonic=lambda: time.monotonic() + shift[0])
    # Simulate time already consumed in the SAME original Decision, no renewed authority.
    shift[0] = 9.4
    probe.update(fault=phase, mode=mode)
    started = time.monotonic()
    with pytest.raises(BindingError, match="^qualification-failed$"):
        probe["probe"].check(b"accepted preimage", probe["binding"], now=k.c.h.now, decision=decision)
    assert time.monotonic() - started < 1.5  # socket/trickle would otherwise exceed remaining .6s
    phases = [v[0] for v in probe["calls"]]
    assert phases == ["resolve", "positive", "denial", "excess"][:phases.index(phase) + 1]
    assert decision._hosted_reads["counts"]["private"] == len(phases)
    assert _children() == before


@pytest.mark.parametrize("boundary", ["fork-return", "other-thread", "close", "close-read",
    "close-before", "close-read-before", "double-cancel", "between-cleanup"])
def test_probe_cancellation_cannot_lose_owned_child(probe, k, monkeypatch, boundary):
    import io
    from workload_factory_binding_runtime.hosted import probe_io
    before = _children(); original = KeyboardInterrupt("private-probe-cancel-canary")
    parent = os.getpid(); fork = os.fork; closes = [0]; pipes = []; fds = []
    if boundary in ("fork-return", "other-thread"):
        def interrupted_fork():
            pid = fork()
            if pid:
                if boundary == "other-thread":
                    signal.pthread_kill(probe["receiver_thread"].ident, signal.SIGINT)
                    time.sleep(.02)
                else:
                    os.kill(parent, signal.SIGINT)
            return pid
        monkeypatch.setattr(probe_io.os, "fork", interrupted_fork)
    else:
        class InterruptedPipe(io.FileIO):
            def close(self):
                if os.getpid() != parent:
                    return super().close()
                closes[0] += 1
                hit = closes[0] == (2 if boundary.startswith("close-read") else 1)
                if hit and boundary.endswith("before"):
                    raise original
                value = super().close()
                if boundary == "between-cleanup":
                    if closes[0] == 2:
                        os.kill(parent, signal.SIGINT)
                elif hit:
                    raise original
                return value
        def managed(fd, mode, *, buffering):
            assert buffering == 0
            value = InterruptedPipe(fd, mode); pipes.append(value); fds.append(fd)
            return value
        monkeypatch.setattr(probe_io.os, "fdopen", managed)
        # Keep the real owned child blocked, without parent server FD reuse
        # obscuring whether our exact two descriptors were retired.
        monkeypatch.setattr(probe_io, "_perform", lambda *a, **kw: time.sleep(3))
        if boundary == "double-cancel":
            waitpid = os.waitpid; injected = [False]
            secondary = SystemExit("private-secondary-reap-cancel-canary")
            def interrupted_waitpid(*a):
                if os.getpid() == parent and not injected[0]:
                    injected[0] = True
                    raise secondary
                return waitpid(*a)
            monkeypatch.setattr(probe_io.os, "waitpid", interrupted_waitpid)
    decision = Decision(clock=lambda:k.c.h.now)
    if boundary.startswith("close-read") or boundary == "between-cleanup":
        decision.end -= 9.4
    old_handler = signal.getsignal(signal.SIGINT)
    if boundary == "between-cleanup":
        def cancel(signum, frame):
            raise original
        signal.signal(signal.SIGINT, cancel)
    try:
        with pytest.raises(KeyboardInterrupt) as caught:
            probe["probe"].check(b"accepted preimage", probe["binding"], now=k.c.h.now, decision=decision)
    finally:
        signal.signal(signal.SIGINT, old_handler)
    if boundary not in ("fork-return", "other-thread"):
        assert caught.value is original
        assert all(pipe.closed for pipe in pipes)
        for fd in fds:
            with pytest.raises(OSError) as closed:
                os.fstat(fd)
            assert closed.value.errno == 9
    assert _children() == before



def test_probe_child_cancellation_cannot_unwind_into_parent_lifecycle(probe, k, monkeypatch):
    from workload_factory_binding_runtime.hosted import probe_io
    before = _children(); fork = os.fork
    def interrupted_child():
        pid = fork()
        if pid == 0:
            os.kill(os.getpid(), signal.SIGINT)
        return pid
    monkeypatch.setattr(probe_io.os, "fork", interrupted_child)
    with pytest.raises(BindingError, match="^qualification-failed$"):
        probe["probe"].check(b"accepted preimage", probe["binding"], now=k.c.h.now,
            decision=Decision(clock=lambda:k.c.h.now))
    assert not probe["calls"]
    assert _children() == before


def test_probe_secondary_thread_refuses_before_rpc_or_private_read(probe, k):
    before = _children(); caught = []; decision = Decision(clock=lambda:k.c.h.now)
    def invoke():
        try:
            probe["probe"].check(b"accepted preimage", probe["binding"], now=k.c.h.now, decision=decision)
        except BindingError as error:
            caught.append(str(error))
    thread = Thread(target=invoke); thread.start(); thread.join(timeout=3)
    assert not thread.is_alive()
    assert caught == ["qualification-failed"]
    assert not probe["calls"]
    assert not hasattr(decision, "_hosted_reads")
    assert _children() == before


def test_probe_success_reply_does_not_renew_deadline_while_child_finishes(probe, k, monkeypatch):
    from workload_factory_binding_runtime.hosted import probe_io
    before = _children(); exit_process = os._exit
    def slow_exit(code):
        time.sleep(2)
        exit_process(code)
    monkeypatch.setattr(probe_io.os, "_exit", slow_exit)
    decision = Decision(clock=lambda:k.c.h.now); decision.end -= 9.4
    started = time.monotonic()
    with pytest.raises(BindingError, match="^qualification-failed$"):
        probe["probe"].check(b"accepted preimage", probe["binding"], now=k.c.h.now, decision=decision)
    assert time.monotonic() - started < 1.5
    assert _children() == before
    assert [v[0] for v in probe["calls"]] == ["resolve"]
    assert decision._hosted_reads["counts"]["private"] == 1


def test_probe_observes_cancellation_during_blocked_io_without_waiting_for_lease(probe, k, monkeypatch):
    from threading import Timer
    from workload_factory_binding_runtime.hosted import probe_io
    before = _children()
    monkeypatch.setattr(probe_io, "_perform", lambda *a, **kw: time.sleep(3))
    decision = Decision(clock=lambda:k.c.h.now)
    timer = Timer(.15, lambda:os.kill(os.getpid(), signal.SIGINT))
    started = time.monotonic(); timer.start()
    try:
        with pytest.raises(KeyboardInterrupt):
            probe["probe"].check(b"accepted preimage", probe["binding"], now=k.c.h.now, decision=decision)
    finally:
        timer.cancel(); timer.join(timeout=1)
    assert time.monotonic() - started < 1.5
    assert _children() == before
    assert decision.remaining() > 5
    assert not probe["calls"]


def test_probe_restores_all_handlers_when_first_restoration_is_cancelled(probe, k, monkeypatch):
    from workload_factory_binding_runtime.hosted import probe_io
    parent = os.getpid(); before = _children(); setter = signal.signal; injected = [False]
    original = KeyboardInterrupt("private-restore-cancel-canary")
    def cancel(signum, frame):
        raise original
    def other(signum, frame):
        pass
    saved = {sig:signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGUSR1)}
    setter(signal.SIGINT, cancel); setter(signal.SIGUSR1, other)
    def interrupted_restore(signum, handler):
        value = setter(signum, handler)
        if os.getpid() == parent and handler is cancel and not injected[0]:
            injected[0] = True
            os.kill(parent, signal.SIGINT)
        return value
    monkeypatch.setattr(probe_io.signal, "signal", interrupted_restore)
    try:
        with pytest.raises(KeyboardInterrupt) as caught:
            probe["probe"].check(b"accepted preimage", probe["binding"], now=k.c.h.now,
                decision=Decision(clock=lambda:k.c.h.now))
        assert caught.value is original
        assert injected[0]
        assert _children() == before
        assert signal.getsignal(signal.SIGINT) is cancel
        assert signal.getsignal(signal.SIGUSR1) is other
    finally:
        for sig, handler in saved.items():
            setter(sig, handler)
