"""Issuer-scoped public snapshots feeding the unchanged offline verifier."""
from dataclasses import dataclass
from collections.abc import Mapping
from email.utils import parsedate_to_datetime
import json
import math
import re
from threading import Condition, RLock
import time
from types import MappingProxyType

from workload_factory_binding.evidence import (
    BindingError, CLAIMS, RUN_CLAIMS, WorkloadVerifier, decode64, decode_object,
    integer, reference, require,
)
from ._https_worker import DISCOVERY_URL, FETCH_SECONDS, ISSUER, JWKS_URL, MAX_BODY
from .transport import FetchResponse, HttpsTransport

_TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")


def _document(body):
    require(type(body) is bytes and 0 < len(body) <= MAX_BODY, "invalid-issuer-response")
    def unique(pairs):
        result = {}
        for name, value in pairs:
            require(name not in result, "invalid-issuer-response")
            result[name] = value
        return result
    def constant(_value):
        raise ValueError
    try:
        value = json.loads(body.decode("utf-8"), object_pairs_hook=unique, parse_constant=constant)
        require(type(value) is dict, "invalid-issuer-response")
        return value
    except Exception:
        raise BindingError("invalid-issuer-response") from None


def _headers(pairs):
    require(type(pairs) is tuple and len(pairs) <= 64, "invalid-issuer-response")
    result, size = {}, 0
    for pair in pairs:
        require(type(pair) is tuple and len(pair) == 2, "invalid-issuer-response")
        name, value = pair
        require(type(name) is str and _TOKEN.fullmatch(name)
                and type(value) is str and len(value) <= 8192
                and all(c == "\t" or 32 <= ord(c) < 127 for c in value),
                "invalid-issuer-response")
        size += len(name) + len(value)
        result.setdefault(name.lower(), []).append(value.strip())
    require(size <= 32768, "invalid-issuer-response")
    for single in ("age", "date", "expires", "content-type", "content-encoding"):
        require(len(result.get(single, [])) <= 1, "invalid-issuer-response")
    require(result.get("content-encoding", ["identity"])[0].lower() == "identity",
            "invalid-issuer-response")
    if "content-type" in result:
        require(result["content-type"][0].split(";", 1)[0].strip().lower()
                in ("application/json", "application/jwk-set+json"), "invalid-issuer-response")
    return result


def _directive_parts(values):
    parts, current, quoted, escaped = [], [], False, False
    for character in ",".join(values) + ",":
        if character == "," and not quoted:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(character)
        if escaped:
            escaped = False
        elif quoted and character == "\\":
            escaped = True
        elif character == '"':
            quoted = not quoted
    require(not quoted and not escaped, "invalid-issuer-response")
    return parts


def _directives(values):
    result = {}
    for part in _directive_parts(values):
        if not part:
            continue
        name, separator, value = part.partition("=")
        name = name.strip().lower()
        require(_TOKEN.fullmatch(name) and name not in result, "invalid-issuer-response")
        value = value.strip() if separator else None
        if value is not None and value.startswith('"'):
            require(len(value) >= 2 and value.endswith('"'), "invalid-issuer-response")
            value = value[1:-1]
        result[name] = value
    return result


def _delta(value):
    require(type(value) is str and value.isascii() and value.isdigit(), "invalid-issuer-response")
    # Saturate rather than overflow an HTTP delta-seconds value (RFC 9111).
    value = value.lstrip("0") or "0"
    return min(int(value), 2**31) if len(value) <= 10 else 2**31


def _date(value):
    try:
        date = parsedate_to_datetime(value)
        require(date.tzinfo is not None, "invalid-issuer-response")
        stamp = date.timestamp()
        require(math.isfinite(stamp), "invalid-issuer-response")
        return stamp
    except Exception:
        raise BindingError("invalid-issuer-response") from None


def _freshness(headers, sent, received):
    wall, mono = received
    control = _directives(headers.get("cache-control", []))
    lifetime = 300
    if "max-age" in control:
        lifetime = _delta(control["max-age"])
    elif "expires" in headers:
        date = _date(headers["date"][0]) if "date" in headers else wall
        lifetime = _date(headers["expires"][0]) - date
    age = _delta(headers["age"][0]) if "age" in headers else 0
    apparent = max(0, wall - _date(headers["date"][0])) if "date" in headers else 0
    corrected = max(apparent, age + mono - sent[1])
    ttl = min(300, lifetime - corrected)
    expiry = math.floor(wall + ttl)
    require(ttl > 0 and integer(expiry) and wall < expiry, "issuer-keys-expired")
    reusable = not ({"no-store", "no-cache"} & set(control))
    if any(part.strip() == "*" for value in headers.get("vary", []) for part in value.split(",")):
        reusable = False
    return expiry, mono + ttl, reusable


def _keys(document):
    entries = document.get("keys")
    require(type(entries) is list and 0 < len(entries) <= 64, "invalid-issuer-response")
    result = {}
    for key in entries:
        require(type(key) is dict and not any(name in key for name in
                ("d", "p", "q", "dp", "dq", "qi", "oth")), "invalid-issuer-response")
        if (key.get("kty"), key.get("alg"), key.get("use")) != ("RSA", "RS256", "sig"):
            continue
        kid = key.get("kid")
        require(reference(kid) and kid not in result
                and key.get("key_ops", ["verify"]) == ["verify"], "invalid-issuer-response")
        try:
            modulus = int.from_bytes(decode64(key["n"]), "big")
            exponent = int.from_bytes(decode64(key["e"]), "big")
            require(2048 <= modulus.bit_length() <= 4096 and exponent == 65537,
                    "invalid-issuer-response")
        except Exception:
            raise BindingError("invalid-issuer-response") from None
        result[kid] = MappingProxyType({name: key[name] for name in ("kid", "kty", "alg", "use", "n", "e")})
    require(bool(result), "invalid-issuer-response")
    return MappingProxyType(result)


@dataclass(frozen=True)
class _Snapshot:
    keys: Mapping[str, Mapping[str, str]]
    expires_at: int
    deadline: float
    generation: int
    reusable: bool


class IssuerKeySource:
    """One source per issuer in a trusted embedding, shared across its verifiers.

    The source owns in-memory refresh state; do not reconstruct it per request.
    This is not a distributed rate limiter or a deployed-authentication boundary.
    Injected trusted transports must honor the passed monotonic deadline.
    """
    def __init__(self, *, transport=None, clock=time.time, monotonic=time.monotonic):
        self._transport = transport if transport is not None else HttpsTransport()
        require(callable(getattr(self._transport, "fetch", None))
                and callable(clock) and callable(monotonic), "invalid-issuer-configuration")
        self._clock, self._monotonic = clock, monotonic
        self._condition = Condition(RLock())
        self._last_sample = self._last_start = self._cache = None
        self._inflight, self._generation = False, 0

    def _sample(self, lower=0):
        with self._condition:
            try:
                wall, mono = self._clock(), self._monotonic()
                require(all(type(x) in (int, float) and math.isfinite(x) and x >= 0
                            for x in (wall, mono)) and lower <= wall <= 2**53 - 1,
                        "clock-unavailable")
                require(self._last_sample is None or all(
                    a <= b for a, b in zip(self._last_sample, (wall, mono))), "clock-unavailable")
            except Exception:
                raise BindingError("clock-unavailable") from None
            self._last_sample = wall, mono
            return wall, mono

    def _fetch(self, url, deadline):
        sent = self._sample()
        require(sent[1] < deadline, "issuer-fetch-unavailable")
        try:
            response = self._transport.fetch(url, deadline=deadline)
        except Exception:
            raise BindingError("issuer-unavailable") from None
        received = self._sample()
        require(received[1] < deadline, "issuer-fetch-unavailable")
        require(type(response) is FetchResponse and type(response.status) is int
                and response.status == 200, "invalid-issuer-response")
        headers = _headers(response.headers)
        value = _document(response.body)
        return value, _freshness(headers, sent, received)

    def _load(self, deadline, generation):
        metadata, discovery_life = self._fetch(DISCOVERY_URL, deadline)
        require(metadata.get("issuer") == ISSUER and metadata.get("jwks_uri") == JWKS_URL,
                "invalid-issuer-response")
        document, key_life = self._fetch(JWKS_URL, deadline)
        return _Snapshot(_keys(document), min(discovery_life[0], key_life[0]),
                         min(discovery_life[1], key_life[1]), generation,
                         discovery_life[2] and key_life[2])

    def _current(self, snapshot, lower):
        with self._condition:
            wall, mono = self._sample(lower)
            require(snapshot.generation == self._generation and not self._inflight,
                    "issuer-snapshot-changed")
            require(wall < snapshot.expires_at and mono < snapshot.deadline, "issuer-keys-expired")
            return math.floor(wall)

    def _for_key(self, kid, lower):
        wait_end = time.monotonic() + FETCH_SECONDS
        with self._condition:
            while True:
                wall, mono = self._sample(lower)
                cached = self._cache
                if (not self._inflight and cached is not None and wall < cached.expires_at
                        and mono < cached.deadline and kid in cached.keys):
                    return cached
                if not self._inflight:
                    break
                remaining = wait_end - time.monotonic()
                require(remaining > 0, "issuer-fetch-unavailable")
                self._condition.wait(remaining)
            require(self._last_start is None or mono >= self._last_start + 30,
                    "issuer-refresh-throttled")
            self._last_start, self._cache, self._inflight = mono, None, True
            self._generation += 1
            generation, deadline = self._generation, mono + FETCH_SECONDS
        try:
            snapshot = self._load(deadline, generation)
            with self._condition:
                wall, mono = self._sample(lower)
                require(wall < snapshot.expires_at and mono < snapshot.deadline
                        and mono < deadline, "issuer-keys-expired")
                self._cache = snapshot if snapshot.reusable else None
            require(kid in snapshot.keys, "unknown-issuer-key")
            return snapshot
        finally:
            with self._condition:
                self._inflight = False
                self._condition.notify_all()


class IssuerWorkloadVerifier:
    """Opt-in adapter over the accepted core; it creates no gate or signing authority."""
    issuer = ISSUER

    def __init__(self, *, audience, source):
        require(reference(audience) and isinstance(source, IssuerKeySource),
                "invalid-issuer-configuration")
        self.audience, self._source = audience, source

    def verify(self, token, expected, *, now):
        require(integer(now) and type(token) is str and len(token) <= 16384, "invalid-token")
        require(type(expected) is dict, "invalid-workload-policy")
        expected = dict(expected)
        require(set(expected) == CLAIMS | RUN_CLAIMS and all(reference(x) for x in expected.values()),
                "invalid-workload-policy")
        parts = token.split(".")
        require(len(parts) == 3, "invalid-token")
        header = decode_object(decode64(parts[0]))
        decode_object(decode64(parts[1]))
        require({"alg", "kid", "typ"} <= set(header) <= {"alg", "kid", "typ", "x5t"}
                and header["alg"] == "RS256" and header["typ"] == "JWT"
                and reference(header["kid"]), "unsupported-token")
        if "x5t" in header:
            require(type(header["x5t"]) is str and 0 < len(header["x5t"]) <= 128
                    and re.fullmatch(r"[A-Za-z0-9_-]+", header["x5t"]), "unsupported-token")
        snapshot = self._source._for_key(header["kid"], now)
        checked = self._source._current(snapshot, now)
        # Validate the external set, then project one key. The core's <=16 limit stays intact.
        projection = {"expires_at": snapshot.expires_at, "keys": [dict(snapshot.keys[header["kid"]])]}
        core = WorkloadVerifier(issuer=ISSUER, audience=self.audience, load_keys=lambda: projection)
        evidence = core.verify(token, expected, now=checked)
        after_crypto = self._source._current(snapshot, checked)
        require(after_crypto < evidence.valid_until, "inactive-token")
        return evidence
