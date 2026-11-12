"""Opt-in bounded HTTPS. Default offline entrypoints do not construct or call it."""
import base64
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import select
import subprocess
import sys
import time

from workload_factory_binding.evidence import BindingError, require
from . import _https_worker as wire

_WORKER = Path(wire.__file__).resolve()


@dataclass(frozen=True)
class FetchResponse:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


class HttpsTransport:
    """Trusted Linux embedding only; no proxy, cookies, credentials or token input.

    A selected CA file is an operator input, never a worker parameter. Otherwise
    use compiled system CA locations, ignoring ambient trust/keylog variables.
    A short child bounds blocking OS DNS and TLS. OS process creation/scheduling
    remains in the trusted-host boundary, not a hard realtime guarantee.
    """
    def __init__(self, *, ca_file=None):
        require(ca_file is None or (type(ca_file) is str and bool(ca_file)
                and "\x00" not in ca_file), "invalid-issuer-configuration")
        self.ca_file = ca_file

    def fetch(self, url, *, deadline):
        require(type(url) is str and url in (wire.DISCOVERY_URL, wire.JWKS_URL),
                "invalid-issuer-endpoint")
        require(type(deadline) in (int, float) and math.isfinite(deadline),
                "invalid-issuer-configuration")
        started = time.monotonic()
        end = min(deadline, started + wire.FETCH_SECONDS)
        require(end > started, "issuer-fetch-unavailable")
        process = None
        try:
            endpoint = "discovery" if url == wire.DISCOVERY_URL else "jwks"
            process = subprocess.Popen(
                [sys.executable, "-I", str(_WORKER), endpoint, self.ca_file or "", str(end - started)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env={"PATH": os.defpath, "LANG": "C.UTF-8"}, bufsize=0,
            )
            wait = min(end, started + wire.CONNECT_SECONDS) - time.monotonic()
            require(wait > 0 and select.select([process.stdout], [], [], wait)[0],
                    "issuer-fetch-unavailable")
            require(process.stdout.read(1) == b"C", "issuer-fetch-unavailable")
            remaining = end - time.monotonic()
            require(remaining > 0, "issuer-fetch-unavailable")
            frame, _ = process.communicate(timeout=remaining)
            require(process.returncode == 0 and len(frame) <= wire.MAX_FRAME
                    and time.monotonic() < end, "issuer-fetch-unavailable")
            result = json.loads(frame)
            require(type(result) is dict and set(result) == {"status", "headers", "body"},
                    "issuer-fetch-unavailable")
            body = base64.b64decode(result["body"], validate=True)
            require(len(body) <= wire.MAX_BODY, "issuer-fetch-unavailable")
            return FetchResponse(result["status"], tuple(tuple(x) for x in result["headers"]), body)
        except Exception:
            raise BindingError("issuer-fetch-unavailable") from None
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    raise BindingError("issuer-worker-cleanup-failed") from None
                finally:
                    if process.stdout is not None:
                        process.stdout.close()
