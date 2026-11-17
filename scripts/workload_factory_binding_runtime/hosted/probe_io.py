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


def _reap(pid):
    # Kill before a blocking reap, even after success. No probe I/O may remain
    # active when the caller starts lifecycle cleanup. Repeated cancellation
    # cannot leave this owned child behind.
    interrupted = None
    while True:
        try:
            if os.waitpid(pid, os.WNOHANG)[0] == 0:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                os.waitpid(pid, 0)
            break
        except ChildProcessError:
            break
        except BaseException as error:
            interrupted = error if interrupted is None else interrupted
    if interrupted is not None:
        raise interrupted


def _close(pipe):
    """FileIO owns its descriptor across interrupted close; never close a reused fd."""
    interrupted = None
    while not pipe.closed:
        try:
            pipe.close()
        except BaseException as error:
            interrupted = error if interrupted is None else interrupted
    if interrupted is not None:
        raise interrupted


def exchange(client, kind, *, binding, message, now, decision):
    from openwallet_runtime.custody import TLSClient
    require(current_thread() is main_thread() and type(client) is TLSClient
            and kind in ("resolve", "sign", "deny"), ERROR)
    ReadBudget(decision).consume("private")
    decision.now()
    libc = ctypes.CDLL(None, use_errno=True)
    parent = os.getpid()
    raw_fds, reader, writer, pid, cancelled = None, None, None, None, None
    handlers, pending = {}, {}
    def defer(signum, frame):
        pending.setdefault(signum, frame)
    def restore():
        remaining = dict(handlers)
        interrupted = None
        while remaining:
            try:
                for signum, handler in tuple(remaining.items()):
                    signal.signal(signum, handler)
                    remaining.pop(signum)
            except BaseException as error:
                interrupted = error if interrupted is None else interrupted
        if interrupted is not None:
            raise interrupted
    def replay():
        for signum, frame in tuple(pending.items()):
            pending.pop(signum, None)
            handlers[signum](signum, frame)
    def child():
        try:
            _close(reader)
            require(libc.prctl(1, signal.SIGKILL, 0, 0, 0) == 0 and os.getppid() == parent, ERROR)
            restore()
            replay()
            payload = _perform(client, kind, binding=binding, message=message, now=now)
            os.write(writer.fileno(), b"\x01" + payload)
        except BaseException:
            try:
                os.write(writer.fileno(), b"\x00")
            except OSError:
                pass
        finally:
            os._exit(0)
    try:
        # Python handlers can run on main after a signal reaches another thread.
        # Defer them throughout owned I/O/retirement, sampling at most every
        # 100ms during waits. At most one frame per signal is retained. Restore
        # only after resources are gone. FileIO retains ownership through close.
        for signum in signal.valid_signals():
            handler = signal.getsignal(signum)
            if callable(handler):
                handlers[signum] = handler
                signal.signal(signum, defer)
        raw_fds = os.pipe2(os.O_CLOEXEC)
        reader = os.fdopen(raw_fds[0], "rb", buffering=0)
        writer = os.fdopen(raw_fds[1], "wb", buffering=0)
        pid = os.fork()
        if pid == 0:
            child()
        replay()
        _close(writer)
        raw = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(reader, selectors.EVENT_READ)
            while True:
                replay()
                ready = selector.select(min(.1, decision.remaining()))
                replay()
                if not ready:
                    continue
                part = os.read(reader.fileno(), 66 - len(raw))
                if not part:
                    break
                raw.extend(part)
                require(len(raw) <= 65, ERROR)
        # EOF includes source-only tracing flush. It never renews the Decision.
        replay()
        decision.now()
        require(raw == b"\x01" if kind != "sign" else len(raw) == 65 and raw[:1] == b"\x01", ERROR)
        return bytes(raw[1:])
    except BaseException as error:
        if not isinstance(error, Exception):
            cancelled = error
            raise
        raise BindingError(ERROR) from None
    finally:
        cleanup_error = None
        def finish(action):
            nonlocal cancelled, cleanup_error
            try:
                action()
            except BaseException as error:
                if cancelled is None and not isinstance(error, Exception):
                    cancelled = error
                cleanup_error = error if cleanup_error is None else cleanup_error
        # Callable signal handlers remain deferred between cleanup actions too.
        # No asynchronous user cancellation can jump past owned child retirement.
        try:
            if raw_fds is not None:
                for pipe, fd in ((reader, raw_fds[0]), (writer, raw_fds[1])):
                    finish(lambda pipe=pipe, fd=fd: _close(pipe) if pipe is not None else os.close(fd))
            if pid not in (None, 0):
                finish(lambda: _reap(pid))
        finally:
            try:
                finish(restore)
            finally:
                if cancelled is not None:
                    raise cancelled
                replay()
                if cleanup_error is not None:
                    raise BindingError(ERROR) from None
