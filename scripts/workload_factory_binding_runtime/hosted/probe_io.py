"""Owned, total-deadline probe I/O using the already loaded neutral TLS clients.

The Linux-only adapter forks a short-lived trusted helper because SSLContext is
opaque and the neutral client has per-socket, rather than total, timeouts. No
credential reload, neutral API change, retry, detached thread or new service role.
Only a fixed success marker and optional 64-byte signature cross a fresh pipe.
"""
import base64
import ctypes
import http.client
import os
import selectors
import signal
from threading import current_thread, main_thread

from workload_factory_binding.evidence import BindingError, canonical, decode_object, require
from .readback import ReadBudget

ERROR = "qualification-failed"
JSON_MEDIA_TYPE = "application/json"


def _perform(client, kind, *, binding, message, now):
    from openwallet_runtime.custody import RemoteRegistry, RemoteSigner
    if kind == "resolve":
        require(RemoteRegistry(client).resolve(binding.subject_ref, now=now) == binding, ERROR)
        return b""
    if kind == "sign":
        value = RemoteSigner(client, subject_ref=binding.subject_ref).sign(message)
        require(type(value) is bytes and len(value) == 64, ERROR)
        return value
    # A generic outage/HTTP exception must never count as worker denial.
    connection = http.client.HTTPSConnection(client.host, client.port,
        context=client.context, timeout=client.timeout)
    try:
        connection.request("POST", "/v0/sign", body=canonical({"subject_ref": binding.subject_ref,
            "message": base64.urlsafe_b64encode(message).decode()}),
            headers={"Content-Type": JSON_MEDIA_TYPE, "Accept": JSON_MEDIA_TYPE})
        response = connection.getresponse()
        raw = response.read(8193)
        require(response.status == 403 and response.getheader("Content-Type") == JSON_MEDIA_TYPE
                and len(raw) <= 8192 and decode_object(raw) == {"error": "service-refused"}, ERROR)
        return b""
    finally:
        connection.close()


class _RetirementErrors:
    """Defer errors until all owned resources have been retired."""

    def __init__(self, cancelled=None):
        self.first = None
        self.cancelled = cancelled

    def __enter__(self):
        return self

    def __exit__(self, _kind, error, _traceback):
        if error is None:
            return False
        if self.first is None:
            self.first = error
        if self.cancelled is None and not isinstance(error, Exception):
            self.cancelled = error
        return True

    def raise_first(self):
        if self.first is not None:
            raise self.first


def _reap(pid):
    # Kill before a blocking reap, even after success. No probe I/O may remain
    # active when the caller starts lifecycle cleanup. Repeated cancellation
    # cannot leave this owned child behind.
    errors = _RetirementErrors()
    while True:
        with errors:
            try:
                if os.waitpid(pid, os.WNOHANG)[0] == 0:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    os.waitpid(pid, 0)
            except ChildProcessError:
                pass
            break
    errors.raise_first()


def _close(pipe):
    """FileIO owns its descriptor across interrupted close; never close a reused fd."""
    errors = _RetirementErrors()
    while not pipe.closed:
        with errors:
            pipe.close()
    errors.raise_first()


class _SignalDeferral:
    def __init__(self):
        self.handlers = {}
        self.pending = {}

    def defer(self, signum, frame):
        self.pending.setdefault(signum, frame)

    def install(self):
        for signum in signal.valid_signals():
            handler = signal.getsignal(signum)
            if callable(handler):
                self.handlers[signum] = handler
                signal.signal(signum, self.defer)

    def restore(self):
        remaining = dict(self.handlers)
        errors = _RetirementErrors()
        while remaining:
            with errors:
                for signum, handler in tuple(remaining.items()):
                    signal.signal(signum, handler)
                    remaining.pop(signum)
        errors.raise_first()

    def replay(self):
        for signum, frame in tuple(self.pending.items()):
            self.pending.pop(signum, None)
            self.handlers[signum](signum, frame)


def _probe_child(reader, writer, signals, libc, parent, perform):
    completed = False
    try:
        _close(reader)
        require(libc.prctl(1, signal.SIGKILL, 0, 0, 0) == 0 and os.getppid() == parent, ERROR)
        signals.restore()
        signals.replay()
        payload = perform()
        os.write(writer.fileno(), b"\x01" + payload)
        completed = True
    finally:
        # This child has one terminal path, including when a signal interrupts
        # the operation or the parent has already retired the pipe.
        try:
            if not completed:
                os.write(writer.fileno(), b"\x00")
        except OSError:
            pass
        finally:
            os._exit(0)


def _read_reply(reader, signals, decision, kind):
    raw = bytearray()
    with selectors.DefaultSelector() as selector:
        selector.register(reader, selectors.EVENT_READ)
        while True:
            signals.replay()
            ready = selector.select(min(.1, decision.remaining()))
            signals.replay()
            if not ready:
                continue
            part = os.read(reader.fileno(), 66 - len(raw))
            if not part:
                break
            raw.extend(part)
            require(len(raw) <= 65, ERROR)
    # EOF includes source-only tracing flush. It never renews the Decision.
    signals.replay()
    decision.now()
    require(raw == b"\x01" if kind != "sign" else len(raw) == 65 and raw[:1] == b"\x01", ERROR)
    return bytes(raw[1:])


def _retire_exchange(raw_fds, reader, writer, pid, signals, cancelled):
    errors = _RetirementErrors(cancelled)
    # Callable handlers stay deferred between cleanup actions, even while a
    # prior cancellation is waiting to propagate.
    try:
        if raw_fds is not None:
            for pipe, fd in ((reader, raw_fds[0]), (writer, raw_fds[1])):
                with errors:
                    if pipe is None:
                        os.close(fd)
                    else:
                        _close(pipe)
        if pid not in (None, 0):
            with errors:
                _reap(pid)
    finally:
        try:
            with errors:
                signals.restore()
        finally:
            if errors.cancelled is not None:
                raise errors.cancelled
            signals.replay()
            if errors.first is not None:
                raise BindingError(ERROR) from None


def exchange(client, kind, *, binding, message, now, decision):
    from openwallet_runtime.custody import TLSClient
    require(current_thread() is main_thread() and type(client) is TLSClient
            and kind in ("resolve", "sign", "deny"), ERROR)
    ReadBudget(decision).consume("private")
    decision.now()
    libc = ctypes.CDLL(None, use_errno=True)
    parent = os.getpid()
    raw_fds, reader, writer, pid, cancelled = None, None, None, None, None
    signals = _SignalDeferral()

    def perform():
        return _perform(client, kind, binding=binding, message=message, now=now)

    try:
        # A signal delivered to another thread can still run its Python
        # handler on main. Defer it while installing and owning resources.
        signals.install()
        raw_fds = os.pipe2(os.O_CLOEXEC)
        reader = os.fdopen(raw_fds[0], "rb", buffering=0)
        writer = os.fdopen(raw_fds[1], "wb", buffering=0)
        pid = os.fork()
        if pid == 0:
            _probe_child(reader, writer, signals, libc, parent, perform)
        signals.replay()
        _close(writer)
        return _read_reply(reader, signals, decision, kind)
    except BaseException as error:
        if not isinstance(error, Exception):
            cancelled = error
            raise
        raise BindingError(ERROR) from None
    finally:
        _retire_exchange(raw_fds, reader, writer, pid, signals, cancelled)
