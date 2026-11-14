"""Selected HTTPS with bounded resolver/TLS/process lifetime and a send checkpoint."""
from dataclasses import dataclass
import base64
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time
from urllib.parse import urlsplit
from workload_factory_binding.evidence import BindingError, canonical, require
from . import ERROR
from .common import document

@dataclass(frozen=True, repr=False)
class Response:
    status: int
    body: bytes

class Https:
    def __init__(self, *, ca_file=None):
        self.ca_file = str(ca_file) if ca_file is not None else None

    def exchange(self, method, url, *, headers, body=b"", decision, before_send=lambda: None):
        process = None
        try:
            parsed = urlsplit(url)
            require(method in ("GET", "POST") and parsed.scheme == "https" and parsed.hostname
                    and parsed.username is None and parsed.password is None and not parsed.fragment
                    and parsed.path.startswith("/") and len(url) <= 4096
                    and all(32 < ord(c) < 127 for c in url)
                    and type(body) is bytes and len(body) <= 65536
                    and type(headers) is dict and len(headers) <= 12
                    and all(type(x) is str and 0 < len(x) <= 16384
                            and all(32 <= ord(c) < 127 for c in x) for pair in headers.items() for x in pair), ERROR)
            now = decision.now()
            remaining = min(10, decision.deadline - now, decision.end - decision.monotonic())
            require(remaining > 0, ERROR)
            process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).with_name("_io_worker.py"))],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env={"PATH": os.defpath, "LANG": "C.UTF-8"})
            message = {"url": url, "method": method, "headers": headers,
                       "body": base64.b64encode(body).decode("ascii"), "seconds": remaining,
                       "ca_file": self.ca_file}
            process.stdin.write(canonical(message) + b"\n")
            process.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                require(bool(selector.select(min(5, remaining))), ERROR)
            require(process.stdout.readline(64) == b"READY\n", ERROR)
            before_send()  # after credential resolution AND TLS; no further application I/O before GO
            decision.now()
            require(decision.monotonic() < decision.end, ERROR)
            raw, _ = process.communicate(b"GO\n", timeout=max(0.001, min(
                decision.end - decision.monotonic(), decision.deadline - decision.now())))
            decision.now()
            require(process.returncode == 0 and len(raw) <= 1500000, ERROR)
            value = document(raw, 1500000)
            require(set(value) == {"status", "headers", "body"} and type(value["status"]) is int, ERROR)
            # Every response must be JSON without content transformation. No redirect follows.
            pairs = value["headers"]
            require(type(pairs) is list and len(pairs) <= 64, ERROR)
            content = [v for k, v in pairs if k.lower() == "content-type"]
            require(len(content) == 1 and content[0].split(";", 1)[0].strip()
                    in ("application/json", "application/vnd.github+json"), ERROR)
            decoded = base64.b64decode(value["body"], validate=True)
            require(0 < len(decoded) <= 1048576, ERROR)
            return Response(value["status"], decoded)
        except Exception:
            raise BindingError(ERROR) from None
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.communicate()
