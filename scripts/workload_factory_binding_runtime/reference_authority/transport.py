"""Bounded loopback-only mTLS transport. Peer capabilities are server selections.

There is no URL resolver, proxy, redirect, enrollment or operational host mode.
"""
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from socketserver import ThreadingMixIn
import ssl
import threading

from workload_factory_binding.evidence import BindingError, canonical, require
from .model import ERROR, closed

LIMIT = 65536
ACTIONS = {"authorize": "ref selection not_before expires_at", "revoke": "ref",
           "observe": "envelope", "claim": "context event_ref", "operation": "context event_ref"}


def decode_message(raw):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT, ERROR)
    def unique(pairs):
        result = {}
        for k, v in pairs:
            require(k not in result, ERROR)
            result[k] = v
        return result
    def invalid(_value):
        raise BindingError(ERROR)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_float=invalid, parse_constant=invalid)
        require(type(value) is dict and len(canonical(value)) <= LIMIT, ERROR)
        return value
    except Exception:
        raise BindingError(ERROR) from None


def fingerprint(der):
    return "sha256:" + hashlib.sha256(der).hexdigest()


class AuthorityServer(ThreadingMixIn, HTTPServer):
    """Explicit selected private fixture server; callers own start/stop lifetime."""
    daemon_threads = False
    block_on_close = True
    request_queue_size = 8

    def __init__(self, *, store, ca_file, cert_file, key_file, permissions):
        require(type(permissions) is dict and permissions
                and all(type(k) is str and len(k) == 71 and k.startswith("sha256:")
                        and type(v) is frozenset and v <= ACTIONS.keys() for k, v in permissions.items()), ERROR)
        self.store, self.permissions = store, dict(permissions)
        self.slots = threading.BoundedSemaphore(8)
        self.tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.tls.minimum_version = ssl.TLSVersion.TLSv1_2
        self.tls.verify_mode = ssl.CERT_REQUIRED
        self.tls.load_verify_locations(cafile=ca_file)
        self.tls.load_cert_chain(cert_file, key_file)
        super().__init__(("127.0.0.1", 0), _Handler)

    def get_request(self):
        raw, address = super().get_request()
        try:
            raw.settimeout(2)
            return self.tls.wrap_socket(raw, server_side=True), address
        except Exception:
            raw.close()
            raise

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        pass  # Transport failures never print peer input or credential paths.


class _Handler(BaseHTTPRequestHandler):
    server_version = "FixtureAuthority"
    sys_version = ""

    def setup(self):
        super().setup()
        # A slow peer cannot reset a per-read timeout indefinitely.
        self.total_timeout = threading.Timer(5, self._expire)
        self.total_timeout.daemon = True
        self.total_timeout.start()

    def _expire(self):
        try:
            self.connection.shutdown(2)
        except OSError:
            pass

    def finish(self):
        self.total_timeout.cancel()
        self.total_timeout.join(timeout=1)
        super().finish()

    def log_message(self, format, *args):
        pass

    def _reply(self, status, value):
        body = canonical(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def do_POST(self):
        try:
            require(self.path == "/" and self.headers.get_all("Content-Length") is not None
                    and len(self.headers.get_all("Content-Length")) == 1
                    and self.headers.get("Transfer-Encoding") is None
                    and self.headers.get_all("Content-Type") == ["application/json"], ERROR)
            length = self.headers["Content-Length"]
            require(length.isascii() and length.isdecimal() and 0 < len(length) <= 6, ERROR)
            length = int(length)
            require(0 < length <= LIMIT, ERROR)
            raw = self.rfile.read(length)
            require(len(raw) == length, ERROR)
            request = decode_message(raw)
            closed(request, "method arguments")
            method, arguments = request["method"], request["arguments"]
            require(type(method) is str and method in ACTIONS, ERROR)
            closed(arguments, ACTIONS[method])
            peer = fingerprint(self.connection.getpeercert(binary_form=True))
            if method not in self.server.permissions.get(peer, frozenset()):
                self._reply(403, {"error": "bootstrap-authority-denied"})
                return
            store = self.server.store
            if method in ("claim", "operation"):
                value = store.read(**arguments, bind=method == "claim")
            else:
                value = getattr(store, method)(**arguments)
            self._reply(200, value)
        except Exception:
            try:
                self._reply(400, {"error": ERROR})
            except (OSError, ssl.SSLError):
                pass
