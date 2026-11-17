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
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        response = connection.getresponse()
        raw = response.read(8193)
        require(response.status == 403 and response.getheader("Content-Type") == "application/json"
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


def exchange(client, kind, *, binding, message, now, decision):
    from openwallet_runtime.custody import TLSClient
    require(current_thread() is main_thread() and type(client) is TLSClient
            and kind in ("resolve", "sign", "deny"), ERROR)
    ReadBudget(decision).consume("private")
    decision.now()
    # Resolve libc before forking; the child inherits precisely the loaded TLS
    # credential and the parent's UID/groups/capability/no-new-privileges state.
    libc = ctypes.CDLL(None, use_errno=True)
    parent = os.getpid()
    read_fd, write_fd = os.pipe2(os.O_CLOEXEC)
    pid = None
    handlers, pending = {}, []
    def defer(signum, frame):
        pending.append((signum, frame))
    def restore():
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
    try:
        # CPython executes handlers on main even when another OS thread received
        # the signal. Defer callable Python handlers, rather than merely masking
        # this thread, until the child PID has been recorded. This private
        # adapter admits only the trusted main-thread qualifier entrypoint.
        for signum in signal.valid_signals():
            handler = signal.getsignal(signum)
            if callable(handler):
                handlers[signum] = handler
                signal.signal(signum, defer)
        pid = os.fork()
        if pid == 0:
            try:
                os.close(read_fd)
                # PR_SET_PDEATHSIG plus the post-prctl parent race check prevents
                # orphaned RPCs if this trusted caller dies before finally runs.
                require(libc.prctl(1, signal.SIGKILL, 0, 0, 0) == 0 and os.getppid() == parent, ERROR)
                restore()
                for signum, frame in pending:
                    handlers[signum](signum, frame)
                payload = _perform(client, kind, binding=binding, message=message, now=now)
                os.write(write_fd, b"\x01" + payload)
            except BaseException:
                try:
                    os.write(write_fd, b"\x00")
                except OSError:
                    pass
            finally:
                os._exit(0)
        restore()
        for signum, frame in pending:
            handlers[signum](signum, frame)
        owned_write, write_fd = write_fd, None
        os.close(owned_write)
        with selectors.DefaultSelector() as selector:
            selector.register(read_fd, selectors.EVENT_READ)
            require(bool(selector.select(decision.remaining())), ERROR)
        raw = os.read(read_fd, 66)
        decision.now()
        require(raw == b"\x01" if kind != "sign" else len(raw) == 65 and raw[:1] == b"\x01", ERROR)
        return raw[1:]
    except Exception:
        raise BindingError(ERROR) from None
    finally:
        try:
            restore()
        finally:
            try:
                os.close(read_fd)
            finally:
                try:
                    if write_fd is not None:
                        os.close(write_fd)
                finally:
                    if pid not in (None, 0):
                        _reap(pid)
