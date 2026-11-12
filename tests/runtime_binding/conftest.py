"""Synthetic issuer fixtures; none of these observations qualify deployed trust."""
from pathlib import Path
from types import SimpleNamespace
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
from factory_binding.conftest import Harness, jwk, jwt
from workload_factory_binding_runtime import (
    DISCOVERY_URL, ISSUER, JWKS_URL, FetchResponse, IssuerKeySource,
    IssuerWorkloadVerifier,
)


class Clock:
    def __init__(self, harness):
        self.harness, self.mono = harness, 100.0

    def wall(self):
        return float(self.harness.now)

    def advance(self, seconds):
        self.harness.now += seconds
        self.mono += seconds


class Transport:
    def __init__(self, key):
        self.documents = {
            DISCOVERY_URL: {"issuer": ISSUER, "jwks_uri": JWKS_URL},
            JWKS_URL: {"keys": [jwk(key)]},
        }
        self.headers, self.calls, self.hook = {}, [], None

    def fetch(self, url, *, deadline):
        self.calls.append((url, deadline))
        if self.hook:
            self.hook(url)
        value = self.documents[url]
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, FetchResponse):
            return value
        raw = value if isinstance(value, bytes) else json.dumps(value).encode()
        return FetchResponse(200, self.headers.get(url, (
            ("Content-Type", "application/json"), ("Cache-Control", "max-age=300"),
        )), raw)


@pytest.fixture
def r(tmp_path):
    h = Harness(tmp_path)
    clock, transport = Clock(h), Transport(h.issuer_key)
    source = IssuerKeySource(transport=transport, clock=clock.wall,
                            monotonic=lambda: clock.mono)
    verifier = IssuerWorkloadVerifier(audience="factory:qa", source=source)
    return SimpleNamespace(h=h, clock=clock, transport=transport, source=source,
                           verifier=verifier,
                           expected={**h.policy["claims"], "run_id": "789", "run_attempt": "1"})


def check(r, token=None):
    return r.verifier.verify(token or r.h.token, r.expected, now=int(r.h.now))
