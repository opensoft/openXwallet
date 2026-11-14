"""Closed data and one bounded, non-regressing decision clock."""
import json
import math
import re
import time
from workload_factory_binding.evidence import BindingError, canonical, integer, require
from . import ERROR

NUMBER = re.compile(r"[1-9][0-9]{0,15}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")

def number(value):
    return type(value) is str and NUMBER.fullmatch(value) is not None and int(value) <= 2**53 - 1

def closed(value, fields):
    require(type(value) is dict and set(value) == set(fields.split()), ERROR)

def document(raw, limit=65536):
    require(type(raw) is bytes and 0 < len(raw) <= limit, ERROR)
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, ERROR)
            result[key] = value
        return result
    def constant(_):
        raise ValueError
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
        canonical(value)
        return value
    except Exception:
        raise BindingError(ERROR) from None

class Decision:
    def __init__(self, *, clock, monotonic=time.monotonic, deadline=None):
        require(deadline is None or integer(deadline), ERROR)
        self.clock, self.monotonic = clock, monotonic
        self.last = self.last_mono = None
        self.api_requests = 0
        self.deadline = deadline
        start = self.now()
        self.deadline = min(start + 10, deadline) if deadline is not None else start + 10
        self.end = self.last_mono + 10

    def now(self):
        try:
            now, mono = self.clock(), self.monotonic()
            require(integer(now) and type(mono) in (int, float) and math.isfinite(mono) and mono >= 0
                    and (self.last is None or now >= self.last)
                    and (self.last_mono is None or mono >= self.last_mono)
                    and (self.deadline is None or now < self.deadline)
                    and (not hasattr(self, "end") or mono < self.end), ERROR)
            self.last, self.last_mono = now, mono
            return now
        except Exception:
            raise BindingError(ERROR) from None

    def clip(self, expiry):
        require(integer(expiry), ERROR)
        self.deadline = min(self.deadline, expiry)
        self.now()
