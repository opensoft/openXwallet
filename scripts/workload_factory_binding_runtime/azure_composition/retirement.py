"""Source-selected P07 retirement, separate from runtime proof and old setup paths.

There is no initialization, credential acquisition, network client or entrypoint.
The embedding supplies independently authenticated, already selected service ports.
A counter or canonical record is not an authorization capability.
"""
from dataclasses import asdict, dataclass, fields, is_dataclass
from contextlib import contextmanager
from contextvars import ContextVar
import base64
import math
import os
import threading
import time
import uuid
from types import MappingProxyType

from workload_factory_binding.evidence import BindingError, canonical, digest
from . import selection

ERROR = "azure-retirement-refused"
PROFILE = "openxfactory-infrastructure-retirement-accounting-internal-v1"
POLICY_DIGEST = "sha256:21b62c2621f3d98e5358c1ba4c5b0345a0237d10cfa52e59bea122487688979e"
GRAPH_DIGEST = "sha256:1dd8bf9209211e2916e14308baad3ea8dbc6144ce90dbcbbb291c16a8d7ba830"
GROUPS = ("private", "arm", "namespace", "journal")
LIMITS = MappingProxyType({
    "registration": (128, 0, 128, 32, 1048576),
    "cleanup": (768, 160, 512, 128, 12582912),
    "observation": (192, 48, 128, 32, 3145728),
})
DURATIONS = MappingProxyType({"registration": 30, "cleanup": 300, "observation": 60})
_TRANSACTION = object()


def _check(condition):
    if not condition:
        raise BindingError(ERROR) from None


def _amount(value):
    _check(type(value) is int and value >= 0)


_ACTIVE_ACCOUNTS = ContextVar("retirement_active_accounts", default=())


class _Checkpoint:
    """Callback-free original-object/high-water guard across nested physical I/O."""
    def __init__(self, account, decision=None):
        self.account, self.decision = account, decision
        self.identity = (account._meter, account._counts, account._lock,
                         account._clock, account._monotonic, account._pool,
                         account._owner, account._pid)
        self.counts, self.bytes = account.counts, account.bytes_used
        self.wall, self.mono = account._last_wall, account._last_mono
        self.end, self.mono_end = account._deadline, account._monotonic_end
        self.deliveries = account._deliveries
        self.run = account._meter["run_transaction"]
        self.burned, self.ended = account._meter["burned"], account._ended
        self.observed_end = getattr(decision, "_observed_until", None)
        self.scope = None if decision is None or decision is account else (
            decision.reserved, decision.account, decision.grant, decision.facade,
            decision.cleanup_start, decision.cleanup_end)

    def check(self):
        a = self.account
        current = (a._meter, a._counts, a._lock, a._clock, a._monotonic,
                   a._pool, a._owner, a._pid)
        _check(all(left is right for left, right in zip(current[:5], self.identity[:5]))
               and current[5:] == self.identity[5:])
        _check(set(a._counts) == set(self.counts))
        for name, value in a._counts.items():
            _amount(value)
            _check(self.counts[name] <= value <= a.limits[GROUPS.index(name)])
        _amount(a._meter["bytes"])
        _check(type(a._meter["burned"]) is bool and type(a._ended) is bool
               and (not self.burned or a._meter["burned"])
               and (not self.ended or a._ended))
        _amount(a._deliveries)
        _check(a._meter["bytes"] >= self.bytes and a._deliveries >= self.deliveries
               and a._meter["run_transaction"] is self.run)
        if self.wall is not None:
            _check(type(a._last_wall) is int and a._last_wall >= self.wall)
        if self.mono is not None:
            _check(type(a._last_mono) in (int, float) and a._last_mono >= self.mono)
        if self.end is not None:
            _check(type(a._deadline) is int and type(a._monotonic_end) in (int, float)
                   and math.isfinite(a._monotonic_end)
                   and a._deadline <= self.end and a._monotonic_end <= self.mono_end)
        if self.observed_end is not None:
            _check(type(self.decision._observed_until) is int
                   and self.decision._observed_until <= self.observed_end)
        if self.scope is not None:
            d = self.decision
            _check((d.reserved, d.account, d.grant, d.facade,
                    d.cleanup_start, d.cleanup_end) == self.scope)


def _audit(account, *, retain=False):
    active = tuple(item for item in _ACTIVE_ACCOUNTS.get() if item.account._meter is account._meter)
    for checkpoint in active:
        checkpoint.check()
    if retain:
        for checkpoint in active:
            checkpoint.__init__(checkpoint.account, checkpoint.decision)


@contextmanager
def _checkpoint(account, decision=None):
    _audit(account)
    checkpoint = _Checkpoint(account, decision)
    token = _ACTIVE_ACCOUNTS.set((*_ACTIVE_ACCOUNTS.get(), checkpoint))
    try:
        yield
        _audit(account, retain=True)
    finally:
        _ACTIVE_ACCOUNTS.reset(token)


class _Account:
    """One prepaid process incarnation; no refund, transfer or configurable limits.

    All admission/debits serialize. The registration service, not this counter,
    establishes original single-use ownership. Physical ports enforce the exposed
    remaining byte limit while reading; received complete bytes are charged before
    validation/use. An oversize or expired result cannot fund another attempt.
    """
    def __init__(self, pool, *, owner, deadline, clock, monotonic=time.monotonic):
        _check(type(pool) is str and pool in LIMITS)
        selection.ref(owner)
        selection.epoch(deadline)
        self._pool, self._owner = pool, owner
        self._pid = os.getpid()
        self._lock = threading.RLock()
        self._clock, self._monotonic = clock, monotonic
        self._last_wall = self._last_mono = None
        self._meter = {"burned": False, "counts": dict.fromkeys(GROUPS, 0),
                       "bytes": 0, "run_transaction": False}
        self._counts = self._meter["counts"]
        self._deliveries = 0
        self._ended = False
        self._deadline = self._monotonic_end = None
        start = self.now()
        duration = DURATIONS[pool]
        self._started_at = start
        self._deadline = min(start + duration, deadline)
        self._monotonic_end = self._last_mono + min(duration, self._deadline - start)
        self.now()

    @property
    def pool(self):
        return self._pool

    @property
    def owner(self):
        return self._owner

    @property
    def limits(self):
        return LIMITS[self.pool]

    @property
    def deadline(self):
        return self._deadline

    @property
    def monotonic_end(self):
        return self._monotonic_end

    @property
    def counts(self):
        with self._lock:
            return dict(self._counts)

    @property
    def bytes_used(self):
        with self._lock:
            return self._meter["bytes"]

    @property
    def deliveries(self):
        with self._lock:
            return self._deliveries

    @classmethod
    def _later_registration(cls, original, *, key, deadline):
        _check(key is _TRANSACTION and type(original) is cls
               and original.pool == "registration")
        with original._lock:
            _check(os.getpid() == original._pid and not original._meter["burned"]
                   and not original._meter["run_transaction"])
            original._meter["run_transaction"] = True
            later = cls("registration", owner=original.owner, deadline=deadline,
                        clock=original._clock, monotonic=original._monotonic)
            later._meter, later._counts, later._lock = original._meter, original._counts, original._lock
            return later

    def clip(self, expiry):
        with self._lock:
            selection.epoch(expiry)
            now = self.now()
            self._deadline = min(self._deadline, expiry)
            self._monotonic_end = min(self._monotonic_end,
                                      self._last_mono + max(0, self._deadline - now))
            self.now()

    def __reduce__(self):
        raise TypeError("allocation-process-bound")

    def now(self):
        with self._lock:
            _check(not self._meter["burned"] and not self._ended and os.getpid() == self._pid)
            _audit(self)
            wall = mono = None
            clean_callbacks = False
            previous_wall, previous_mono = self._last_wall, self._last_mono
            try:
                with _checkpoint(self):
                    wall, mono = self._clock(), self._monotonic()
                clean_callbacks = True
                valid = (type(wall) is int and 0 < wall <= 9007199254740991
                         and type(mono) in (int, float) and math.isfinite(mono)
                         and mono >= 0
                         and (self._last_wall is None or wall >= self._last_wall)
                         and (self._last_mono is None or mono >= self._last_mono)
                         and (self._deadline is None or wall < self._deadline)
                         and (self._monotonic_end is None or mono < self._monotonic_end))
            except BaseException:
                valid = False
            if not valid:
                ordinary_expiry = (clean_callbacks and type(wall) is int
                                   and type(mono) in (int, float) and math.isfinite(mono)
                                   and type(previous_wall) is int
                                   and type(previous_mono) in (int, float)
                                   and type(self._deadline) is int
                                   and type(self._monotonic_end) in (int, float)
                                   and wall >= previous_wall and mono >= previous_mono
                                   and (wall >= self._deadline or mono >= self._monotonic_end))
                self._ended = True
                for checkpoint in _ACTIVE_ACCOUNTS.get():
                    if checkpoint.account is self:
                        checkpoint.ended = True
                if self.pool != "registration" or not ordinary_expiry:
                    self.burn()
                raise BindingError(ERROR) from None
            self._last_wall, self._last_mono = wall, mono
            _audit(self, retain=True)
            return wall

    def remaining(self):
        with self._lock:
            self.now()
            return min(10.0, self._deadline - self._last_wall,
                       self._monotonic_end - self._last_mono)

    def reply_limit(self, cap=1048576):
        with self._lock:
            self.now()
            _amount(cap)
            return min(cap, self.limits[4] - self._meter["bytes"])

    def charge(self, group, *, size=0):
        with self._lock:
            self.now()
            _amount(size)
            _check(type(group) is str and group in GROUPS)
            _check(self._counts[group] < self.limits[GROUPS.index(group)])
            _check(size <= self.limits[4] - self._meter["bytes"])
            self._counts[group] += 1
            self._meter["bytes"] += size
            _audit(self, retain=True)

    def receive(self, size):
        with self._lock:
            _amount(size)
            _check(os.getpid() == self._pid)
            # Actual observed bytes remain charged even for an oversized/late
            # result. They are never truncated to make a failed trace fit.
            self._meter["bytes"] += size
            _audit(self, retain=True)
            if self._meter["bytes"] > self.limits[4]:
                self.burn()
                raise BindingError(ERROR) from None
            self.now()

    def request_metadata(self, size):
        """A selected transport charges additional complete metadata before send."""
        with self._lock:
            self.now()
            _amount(size)
            _check(size <= self.limits[4] - self._meter["bytes"])
            self._meter["bytes"] += size
            _audit(self, retain=True)

    def admit_trigger(self):
        with self._lock:
            self.now()
            _check(self.pool == "cleanup" and self._deliveries < 4)
            self._deliveries += 1
            _audit(self, retain=True)
            return self._deliveries

    @property
    def account(self):
        return self

    def backend(self, group, function, *args, **kwargs):
        _check(group in ("namespace", "journal"))
        return _io(self, self, group, function, *args, private=False, **kwargs)

    def burn(self):
        with self._lock:
            self._meter["burned"] = True
            for checkpoint in _ACTIVE_ACCOUNTS.get():
                if checkpoint.identity[0] is self._meter:
                    checkpoint.burned = True


_CONTEXT = object()


def _wire(value):
    """Complete deterministic application frame, never retained in an audit."""
    if isinstance(value, bytes):
        return {"bytes": base64.b64encode(value).decode("ascii")}
    if is_dataclass(value):
        return _wire(asdict(value))
    if type(value) is dict:
        return {key: _wire(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_wire(item) for item in value]
    _check(value is None or type(value) in (str, int, bool))
    return value


@dataclass(frozen=True, repr=False)
class Grant:
    """A selected authority port's authenticated response; labels alone grant nothing."""
    reservation_digest: str
    namespace_generation_ref: str
    owner_scope_ref: str
    source_roles_digest: str
    retained_scope_ref: str
    authority_ref: str
    subject_ref: str
    owner_incarnation_ref: str
    purpose: str
    not_before: int
    not_after: int
    provenance_ref: str
    cleanup_not_before: int
    cleanup_deadline: int


def _grant(value, reserved, *, purpose, owner):
    _check(type(value) is Grant and value.purpose == purpose)
    before = reserved.value
    _check(value.reservation_digest == reserved.digest)
    for name in ("namespace_generation_ref", "owner_scope_ref", "source_roles_digest",
                 "retained_scope_ref"):
        _check(getattr(value, name) == before[name])
    for name in ("authority_ref", "subject_ref", "owner_incarnation_ref", "provenance_ref"):
        selection.ref(getattr(value, name))
    _check(value.owner_incarnation_ref == owner)
    selection.epoch(value.not_before)
    selection.epoch(value.not_after)
    selection.epoch(value.cleanup_not_before)
    selection.epoch(value.cleanup_deadline)
    _check(value.not_before < value.not_after
           and value.cleanup_not_before < value.cleanup_deadline)
    return value


class _Context:
    """Only the original source service constructs this after durable ownership.

    Existing provider ports accept the original context and bounded timeout. They
    must bound complete reads by reply_limit(), expose nested physical backend
    operations through backend(), and never hide retries/redirects/pagination.
    The source qualification independently compares those calls with port logs.
    """
    def __init__(self, *, key, reserved, account, grant, cleanup_end,
                 cleanup_start=None, facade=None):
        _check(key is _CONTEXT and type(reserved) is selection.Record)
        _check(type(account) is _Account and account.pool in LIMITS)
        _grant(grant, reserved, purpose=account.pool, owner=account.owner)
        account.clip(grant.not_after)
        selection.epoch(cleanup_end)
        _check(cleanup_end <= grant.cleanup_deadline)
        self.reserved, self.account, self.grant = reserved, account, grant
        self.cleanup_end, self.facade = cleanup_end, facade
        self.cleanup_start = account._started_at if cleanup_start is None else cleanup_start
        selection.epoch(self.cleanup_start)
        _check(self.cleanup_start < cleanup_end)
        self.started_at = account.now()
        self._observed_until = account.deadline
        self._polls = {}
        if account.pool == "cleanup":
            _check(account._started_at >= grant.cleanup_not_before)
        self.check(reserved)

    @property
    def deadline(self):
        return self.account.deadline

    def now(self):
        now = self.account.now()
        _check(self.grant.not_before <= now < self.grant.not_after)
        return now

    def remaining(self):
        now = self.now()
        return min(self.account.remaining(), self.grant.not_after - now)

    def reply_limit(self, cap=1048576):
        return self.account.reply_limit(cap)

    def check(self, reserved, *, write=False):
        self.now()
        _check(type(reserved) is selection.Record and reserved.raw == self.reserved.raw)
        if write:
            _check(self.account.pool == "cleanup"
                   and self.grant.cleanup_not_before <= self.now() < self.cleanup_end)
        return self

    def invoke(self, group, function, *args, private=True, **kwargs):
        self.check(self.reserved)
        return _io(self.account, self, group, function, *args, private=private, **kwargs)

    def backend(self, group, function, *args, **kwargs):
        _check(group in ("namespace", "journal"))
        return self.invoke(group, function, *args, private=False, **kwargs)

    def state(self, store, operation, *args, **kwargs):
        if self.facade is not None:
            return self.invoke("private", self.facade.exchange, operation, args,
                               kwargs)
        return self.backend("namespace", getattr(store, operation), *args, **kwargs)

    def poll(self, original_ref, method):
        key = (original_ref, method)
        count = self._polls.get(key, 0)
        _check(count < 3)
        self._polls[key] = count + 1


class _OperationPending(BindingError):
    def __init__(self):
        super().__init__("azure-retirement-operation-pending")


def _frame_size(value):
    """Canonical application-frame bytes without copying a hostile large body."""
    if type(value) is bytes:
        return 12 + 4 * ((len(value) + 2) // 3)
    if is_dataclass(value):
        return _frame_size({f.name: getattr(value, f.name) for f in fields(value)})
    if type(value) is dict:
        _check(all(type(key) is str for key in value))
        return 2 + max(0, len(value) - 1) + sum(
            len(canonical(key)) + 1 + _frame_size(item) for key, item in value.items())
    if type(value) in (tuple, list):
        return 2 + max(0, len(value) - 1) + sum(_frame_size(item) for item in value)
    _check(value is None or type(value) in (str, int, bool))
    return len(canonical(value))


def _io(account, decision, group, function, *args, private=True, **kwargs):
    failed = False
    value = None
    try:
        with _checkpoint(account, decision):
            request_size = _frame_size({"arguments": args, "metadata":
                                      {k: v for k, v in kwargs.items() if not callable(v)}})
            account.charge(group, size=request_size)
            timeout = decision.remaining()
            start = account._last_mono
            if private:
                value = function(*args, decision=decision, timeout=timeout, **kwargs)
            else:
                value = function(*args, timeout=timeout, **kwargs)
            _audit(account)
            account.receive(_frame_size(value))
            decision.now()
            _check(account._last_mono - start <= timeout)
    except BaseException:
        failed = True
    if failed:
        account.burn()
        raise BindingError(ERROR) from None
    return value


@dataclass(frozen=True, repr=False)
class Handoff:
    anchor_digest: str
    owner_incarnation_ref: str
    subject_ref: str
    provisioner_fence_ref: str
    activation_ref: str


@dataclass(frozen=True, repr=False)
class NoSend:
    reservation_digest: str
    resource_path: str
    attempt_ref: str
    operation: str
    provenance_ref: str
    incarnation_ref: str | None = None


@dataclass(frozen=True, repr=False)
class Deletion:
    operation: object
    terminal_ref: str | None


@dataclass(frozen=True, repr=False)
class RunFacts:
    deployed: bytes
    linked: bytes
    authority: object
    cleanup_authority_ref: str


@dataclass(frozen=True, repr=False)
class PreservedTarget:
    slot: str
    path: str
    baseline_digest: str


@dataclass(frozen=True, repr=False)
class Preservation:
    slot: str
    path: str
    body: bytes | None
    observed_at: int
    expires_at: int
    provenance_ref: str


@dataclass(frozen=True, repr=False)
class CredentialOutcome:
    handle_ref: str
    owner_scope_ref: str
    state: str
    observed_at: int
    expires_at: int
    provenance_ref: str


ARM_SLOTS = ("control-data-disk", "gate-data-disk", "measured-managed-image",
             "credential-vault", "redacted-evidence-storage", "watchdog-function",
             "watchdog-plan", "watchdog-storage", "watchdog-identity",
             "disposable-parent-RG", "retained-parent-RG", "watchdog-parent-RG")
STATE_SLOTS = ("permanent-namespace-catalog", "retained-registration/action-state",
               "retained-runtime-authority/replay-state")
ANCHOR_FIELDS = frozenset("""profile registration_ref reservation_digest
namespace_generation_ref source_roles_digest owner_scope_ref setup_cleanup_authority_ref
retained_scope_ref policy_digest registration_owner_incarnation_ref
registration_allocation_ref cleanup_allocation_ref observation_allocation_ref not_after""".split())
CLAIM_FIELDS = frozenset("""profile anchor_digest allocation_ref owner_incarnation_ref
trigger_ref cleanup_authority_ref started_at wall_end clock_domain_ref
monotonic_end_milliseconds""".split())
RUN_FIELDS = frozenset("""profile anchor_digest provisioned_envelope_digest
final_scope_ref run_cleanup_authority_ref""".split())


def _registration_ref(reserved):
    return "registration:" + reserved.digest[7:]


def _key(reserved, suffix):
    return PROFILE + ":" + _registration_ref(reserved) + ":" + suffix


def _snapshot(value):
    from .namespace import Snapshot
    _check(type(value) is Snapshot and type(value.etag) is str and 0 < len(value.etag) <= 160)
    selection.document(value.raw)
    return selection.Record(value.raw)


def _anchor(raw, reserved):
    value = selection.document(raw)
    selection.closed(value, ANCHOR_FIELDS)
    before = reserved.value
    _check(value["profile"] == PROFILE and value["policy_digest"] == POLICY_DIGEST
           and value["registration_ref"] == _registration_ref(reserved)
           and value["reservation_digest"] == reserved.digest)
    for name in ("namespace_generation_ref", "source_roles_digest", "owner_scope_ref",
                 "retained_scope_ref"):
        _check(value[name] == before[name])
    _check(value["setup_cleanup_authority_ref"] == before["setup_authority_ref"])
    for pool in LIMITS:
        _check(value[pool + "_allocation_ref"] == "allocation:" + pool + ":" + reserved.digest[7:])
    selection.ref(value["registration_owner_incarnation_ref"])
    selection.epoch(value["not_after"])
    _check(value["not_after"] <= before["window"]["not_after"])
    return selection.Record(raw)


def _claim(raw, anchor, cleanup_deadline, *, cleanup_not_before):
    value = selection.document(raw)
    selection.closed(value, CLAIM_FIELDS)
    _check(value["profile"] == PROFILE + ":cleanup-claim"
           and value["anchor_digest"] == anchor.digest
           and value["allocation_ref"] == anchor.value["cleanup_allocation_ref"]
           and value["owner_incarnation_ref"] == anchor.value["registration_owner_incarnation_ref"])
    for name in ("trigger_ref", "cleanup_authority_ref", "clock_domain_ref"):
        selection.ref(value[name])
    for name in ("started_at", "wall_end", "monotonic_end_milliseconds"):
        selection.epoch(value[name])
    _check(cleanup_not_before <= value["started_at"] < value["wall_end"]
           <= min(value["started_at"] + 300, cleanup_deadline))
    return selection.Record(raw)


class Reconciler:
    """An already selected external owner; no runtime entrypoint or state initializer.

    The embedding selects authenticated control/journal/provider ports. Control
    authorize() durably assigns the requested original pool/owner once before its
    response; its backend work uses decision.backend(). Handoff returns proof of
    durable provisioner exclusion and activation. Responses are never self-approved
    request flags. Original operation queries return immutable authenticated refs.
    Backend ports must expose every physical call, without hidden SDK retries.
    """
    def __init__(self, *, reserved, provider, journal, control, cleanup_deadline,
                 clock, monotonic=time.monotonic, facade=None):
        from .provider import Provider
        _check(type(reserved) is selection.Record and type(provider) is Provider)
        selection.reservation(reserved.raw, approved=reserved.raw)
        _check(provider._reserved.raw == reserved.raw
               and digest(reserved.value["resources"]) == GRAPH_DIGEST)
        selection.epoch(cleanup_deadline)
        self.reserved, self.provider = reserved, provider
        self.journal, self.control, self.facade = journal, control, facade
        self.cleanup_deadline, self.clock, self.monotonic = cleanup_deadline, clock, monotonic
        self.owner = "owner:" + uuid.uuid4().hex
        self._pid = os.getpid()
        self._lock = threading.RLock()
        self._registration = self._cleanup = None
        self._accounts = {}
        self._anchor = self._claim = self._run = self._handoff = None
        self._deployed = self._linked = None
        self._ran = False

    def _alive(self):
        _check(os.getpid() == self._pid)

    def _context(self, pool, *, purpose=None, account=None):
        transaction = purpose or pool
        _check(transaction not in self._accounts)
        if account is None:
            deadline = self.cleanup_deadline
            if pool == "registration":
                deadline = min(deadline, self.reserved.value["window"]["not_after"])
            account = _Account(pool, owner=self.owner, deadline=deadline,
                               clock=self.clock, monotonic=self.monotonic)
        # Preserve the original debited incarnation even if authorization ACK or
        # subsequent response validation fails. No second acquisition is funded.
        self._accounts[transaction] = account
        grant = _io(account, account, "private", self.control.authorize,
                    transaction, _registration_ref(self.reserved), self.reserved.digest,
                    self.owner, "allocation:" + pool + ":" + self.reserved.digest[7:])
        _grant(grant, self.reserved, purpose=pool, owner=self.owner)
        _check(grant.cleanup_deadline == self.cleanup_deadline)
        _check(grant.subject_ref == self.provider._writer)
        return _Context(key=_CONTEXT, reserved=self.reserved, account=account, grant=grant,
                        cleanup_end=min(account.deadline, grant.not_after), facade=self.facade)

    def _read(self, suffix, context):
        return _snapshot(context.backend("journal", self.journal.read, _key(self.reserved, suffix)))

    def _write_once(self, suffix, raw, context):
        selected = _snapshot(context.backend("journal", self.journal.create_only,
                                             _key(self.reserved, suffix), raw))
        _check(selected.raw == raw)
        verified = self._read(suffix, context)
        _check(verified.raw == raw)
        return verified

    def register(self):
        with self._lock:
            self._alive()
            if self._anchor is not None:
                _check(type(self._handoff) is Handoff)
                current = _anchor(self._read("anchor", self._registration).raw, self.reserved)
                _check(current.raw == self._anchor.raw)
                return current
            _check(self._registration is None)
            self._registration = self._context("registration")
            context = self._registration
            _check(context.grant.authority_ref == self.reserved.value["setup_authority_ref"])
            namespace = self.provider._namespace.cleanup_view(context)
            for resource in self.reserved.value["resources"]:
                namespace.read(self.reserved, resource["resource_path"], decision=context)
            before = self.reserved.value
            value = {"profile": PROFILE, "registration_ref": _registration_ref(self.reserved),
                     "reservation_digest": self.reserved.digest,
                     **{name: before[name] for name in ("namespace_generation_ref", "source_roles_digest",
                         "owner_scope_ref", "retained_scope_ref")},
                     "setup_cleanup_authority_ref": before["setup_authority_ref"],
                     "policy_digest": POLICY_DIGEST, "registration_owner_incarnation_ref": self.owner,
                     "not_after": min(before["window"]["not_after"], context.grant.not_after)}
            value.update({pool + "_allocation_ref": "allocation:" + pool + ":" + self.reserved.digest[7:]
                          for pool in LIMITS})
            self._anchor = _anchor(self._write_once("anchor", canonical(value), context).raw, self.reserved)
            handoff = context.invoke("private", self.control.handoff, self._anchor)
            _check(type(handoff) is Handoff and handoff.anchor_digest == self._anchor.digest
                   and handoff.owner_incarnation_ref == self.owner
                   and handoff.subject_ref == self.provider._writer)
            selection.ref(handoff.provisioner_fence_ref)
            selection.ref(handoff.activation_ref)
            self._handoff = handoff
            return self._anchor


    def register_run(self):
        with self._lock:
            self._alive()
            _check(self._anchor is not None and type(self._handoff) is Handoff
                   and self._run is None and self._cleanup is None)
            account = _Account._later_registration(self._registration.account,
                       key=_TRANSACTION, deadline=self.cleanup_deadline)
            context = self._context("registration", purpose="registration-run", account=account)
            facts = context.invoke("private", self.control.run_facts, _registration_ref(self.reserved))
            _check(type(facts) is RunFacts and type(facts.authority) is selection.FinalAuthority)
            deployed = selection.provisioned(facts.deployed, reserved=self.reserved,
                                              authenticated_readback=facts.deployed)
            linked = selection.final_link(facts.linked, deployed=deployed, authority=facts.authority)
            self.provider._namespace.cleanup_view(context).provisioned(
                deployed.raw, reserved=self.reserved, authenticated_readback=deployed.raw, decision=context)
            selection.ref(facts.cleanup_authority_ref)
            value = {"profile": PROFILE + ":run-binding", "anchor_digest": self._anchor.digest,
                     "provisioned_envelope_digest": deployed.digest,
                     "final_scope_ref": linked.value["final_scope_ref"],
                     "run_cleanup_authority_ref": facts.cleanup_authority_ref}
            selection.closed(value, RUN_FIELDS)
            self._run = self._write_once("run-binding", canonical(value), context)
            self._deployed, self._linked = deployed, linked
            return self._run

    def cleanup(self, trigger_ref):
        """Return the durable original claim, never a completion attestation."""
        with self._lock:
            self._alive()
            selection.ref(trigger_ref)
            _check(self._anchor is not None and type(self._handoff) is Handoff)
            if self._cleanup is None:
                self._cleanup = self._context("cleanup")
            context = self._cleanup
            delivery = context.account.admit_trigger()
            if self._claim is not None:
                current = _claim(self._read("cleanup-claim", context).raw,
                                 self._anchor, self.cleanup_deadline,
                                 cleanup_not_before=context.grant.cleanup_not_before)
                _check(current.raw == self._claim.raw)
                return current
            _check(delivery == 1 and not self._ran)
            expected_authority = (self._run.value["run_cleanup_authority_ref"] if self._run
                                  else self._anchor.value["setup_cleanup_authority_ref"])
            _check(context.grant.authority_ref == expected_authority)
            value = {"profile": PROFILE + ":cleanup-claim", "anchor_digest": self._anchor.digest,
                     "allocation_ref": self._anchor.value["cleanup_allocation_ref"],
                     "owner_incarnation_ref": self.owner, "trigger_ref": trigger_ref,
                     "cleanup_authority_ref": expected_authority,
                     "started_at": context.account._started_at,
                     "wall_end": min(context.account.deadline, self.cleanup_deadline),
                     "clock_domain_ref": "clock-domain:" + uuid.uuid4().hex,
                     "monotonic_end_milliseconds": int(context.account.monotonic_end * 1000)}
            self._claim = _claim(self._write_once("cleanup-claim", canonical(value), context).raw,
                                 self._anchor, self.cleanup_deadline,
                                 cleanup_not_before=context.grant.cleanup_not_before)
            context.cleanup_start = self._claim.value["started_at"]
            context.cleanup_end = self._claim.value["wall_end"]
            self._ran = True
            admission = context.invoke("private", self.control.close_write_run,
                                        _registration_ref(self.reserved), self._claim)
            _check(type(admission) is Handoff and admission.anchor_digest == self._anchor.digest
                   and admission.owner_incarnation_ref == self.owner
                   and admission.subject_ref == self.provider._writer)
            selection.ref(admission.provisioner_fence_ref)
            selection.ref(admission.activation_ref)
            self._execute(context)
            return self._claim

    def _execute(self, context):
        service = self.provider.cleanup_view(context)
        remaining = {item["resource_path"]: item for item in self.reserved.value["resources"]}
        done = set()
        while remaining:
            progressed = False
            for path in tuple(remaining):
                resource = remaining[path]
                if not set(resource["dependency_paths"]) <= done:
                    continue
                if self._retire(service, path, context):
                    done.add(path)
                    del remaining[path]
                    progressed = True
            if not progressed:
                break

    def _creation(self, path, context):
        return context.invoke("private", self.control.original_creation,
                              _registration_ref(self.reserved), path)

    def _deletion(self, path, attempt, context):
        return context.invoke("private", self.control.original_deletion,
                              _registration_ref(self.reserved), path, attempt)

    def _retire(self, service, path, context):
        from .provider import Generation, Operation
        current = service._namespace.read(self.reserved, path, decision=context).value
        if current["state"] == "absent-tombstoned":
            return True
        origin = self._creation(path, context)
        if type(origin) is NoSend:
            _no_send(origin, self.reserved, path, current["create_attempt_ref"], "create")
            _check(self._run is None and current["state"] == "reserved")
            service._fence(path, context, retiring=True)
            observed = service._exchange(service._request("GET", service._policy(path),
                        "observe:retirement-absence", context), context)
            _check(observed.status == 404)
            service._namespace.transition(self.reserved, path, state="absent-tombstoned",
                    observation_ref=observed.receipt_ref, decision=context)
            return True
        if type(origin) is Operation:
            try:
                service._terminal(origin, "PUT", context)
            except _OperationPending:
                pass
            return False
        _check(type(origin) is Generation and origin.path == path)
        if "creation" not in current:
            service.recover_generation(origin, decision=context)
            current = service._namespace.read(self.reserved, path, decision=context).value
        if "retirement_attempt_ref" in current:
            recorded = self._deletion(path, current["retirement_attempt_ref"], context)
            if type(recorded) is not Deletion:
                return False
            _check(type(recorded.operation) is Operation)
            service.deletion_complete(recorded.operation, origin, decision=context)
            return True
        attempt = "retirement:" + digest({"claim_digest": self._claim.digest,
                                                    "resource_path": path})[7:]
        recorded = self._deletion(path, attempt, context)
        if type(recorded) is NoSend:
            _no_send(recorded, self.reserved, path, attempt, "delete", origin.identity_ref)
            service._generation(origin, context)
            service._fence(path, context, retiring=True)
            observed = service._exchange(service._request("GET", service._policy(path),
                        "observe:retirement-absence", context), context)
            _check(observed.status == 404)
            service._namespace.transition(self.reserved, path, state="retiring",
                    observation_ref=observed.receipt_ref, retirement_attempt_ref=attempt, decision=context)
            service._namespace.transition(self.reserved, path, state="absent-tombstoned",
                    observation_ref=observed.receipt_ref, decision=context)
            return True
        _check(recorded is None)
        operation = service.retire(origin, attempt_ref=attempt, decision=context)
        service.deletion_complete(operation, origin, decision=context)
        return True


def _no_send(value, reserved, path, attempt, operation, incarnation=None):
    _check(type(value) is NoSend and value.reservation_digest == reserved.digest
           and value.resource_path == path and value.attempt_ref == attempt
           and value.operation == operation and value.incarnation_ref == incarnation)
    selection.ref(value.provenance_ref)


def _current(stamp, expiry, context):
    selection.epoch(stamp)
    selection.epoch(expiry)
    _check(stamp <= context.now() < expiry <= stamp + 60)
    context._observed_until = min(context._observed_until, expiry)


class Observer:
    """A separately selected current reader; never closes admission or mutates resources.

    The journal client permits reads and two create-only observation evidence slots,
    never namespace updates or claim replacement. Provider/control/preservation
    clients authenticate independently of the mutator's reports. No new credential
    revocation or signing capability is supplied. The source embedding, not request
    data, selects these clients and the independently approved observation window.
    """
    def __init__(self, *, reserved, provider, journal, control, preservation,
                 cleanup_deadline, observation_deadline, clock, monotonic=time.monotonic,
                 facade=None):
        from .provider import Provider
        _check(type(reserved) is selection.Record and type(provider) is Provider)
        selection.reservation(reserved.raw, approved=reserved.raw)
        _check(provider._reserved.raw == reserved.raw
               and digest(reserved.value["resources"]) == GRAPH_DIGEST)
        selection.epoch(cleanup_deadline)
        selection.epoch(observation_deadline)
        self.reserved, self.provider = reserved, provider
        self.journal, self.control, self.preservation = journal, control, preservation
        self.cleanup_deadline, self.observation_deadline = cleanup_deadline, observation_deadline
        self.clock, self.monotonic, self.facade = clock, monotonic, facade
        self.owner = "observer-owner:" + uuid.uuid4().hex
        self._pid = os.getpid()
        self._lock = threading.RLock()
        self._spent = False
        self._context = None

    def _read(self, suffix, context, *, optional=False):
        method = self.journal.lookup if optional else self.journal.read
        value = context.backend("journal", method, _key(self.reserved, suffix))
        if value is None:
            _check(optional)
            return None
        return _snapshot(value)

    def _write_once(self, suffix, raw, context):
        selection.document(raw)
        written = _snapshot(context.backend("journal", self.journal.create_only,
                                            _key(self.reserved, suffix), raw))
        _check(written.raw == raw)
        checked = self._read(suffix, context)
        _check(checked.raw == raw)
        return checked

    def observe(self):
        with self._lock:
            _check(os.getpid() == self._pid and not self._spent)
            self._spent = True
            account = _Account("observation", owner=self.owner, deadline=self.observation_deadline,
                               clock=self.clock, monotonic=self.monotonic)
            grant = _io(account, account, "private", self.control.authorize,
                        "observation", _registration_ref(self.reserved), self.reserved.digest,
                        self.owner, "allocation:observation:" + self.reserved.digest[7:])
            _grant(grant, self.reserved, purpose="observation", owner=self.owner)
            _check(grant.cleanup_deadline == self.cleanup_deadline
                   and grant.subject_ref != self.provider._writer)
            context = _Context(key=_CONTEXT, reserved=self.reserved, account=account, grant=grant,
                               cleanup_start=grant.cleanup_not_before,
                               cleanup_end=grant.cleanup_deadline, facade=self.facade)
            self._context = context
            anchor = _anchor(self._read("anchor", context).raw, self.reserved)
            _check(anchor.value["registration_owner_incarnation_ref"] != self.owner)
            original_claim = self._read("cleanup-claim", context, optional=True)
            if original_claim is not None:
                original_claim = _claim(original_claim.raw, anchor, self.cleanup_deadline,
                                        cleanup_not_before=grant.cleanup_not_before)
                context.cleanup_start = original_claim.value["started_at"]
                context.cleanup_end = original_claim.value["wall_end"]
            phase = context.invoke("private", self.control.phase, _registration_ref(self.reserved))
            _check(phase in ("setup", "run"))
            deployed = linked = None
            authority_ref = anchor.value["setup_cleanup_authority_ref"]
            if phase == "run":
                binding = self._read("run-binding", context)
                selection.closed(binding.value, RUN_FIELDS)
                _check(binding.value["profile"] == PROFILE + ":run-binding"
                       and binding.value["anchor_digest"] == anchor.digest)
                facts = context.invoke("private", self.control.run_facts, _registration_ref(self.reserved))
                _check(type(facts) is RunFacts and type(facts.authority) is selection.FinalAuthority)
                deployed = selection.provisioned(facts.deployed, reserved=self.reserved,
                                                  authenticated_readback=facts.deployed)
                linked = selection.final_link(facts.linked, deployed=deployed, authority=facts.authority)
                _check(binding.value["provisioned_envelope_digest"] == deployed.digest
                       and binding.value["final_scope_ref"] == linked.value["final_scope_ref"]
                       and binding.value["run_cleanup_authority_ref"] == facts.cleanup_authority_ref)
                authority_ref = facts.cleanup_authority_ref
            if original_claim is not None:
                _check(original_claim.value["cleanup_authority_ref"] == authority_ref)
            service = self.provider.cleanup_view(context)
            snapshots = service._namespace.read_set(self.reserved, decision=context)
            results = [self._resource(resource, snapshot.value, service, context, phase, original_claim)
                       for resource, snapshot in zip(self.reserved.value["resources"], snapshots)]
            preservation, preserved = self._preserved(context)
            credentials, revoked = self._credentials(context)
            observed_at = context.now()
            _check(observed_at < context._observed_until)
            audit = {"profile": PROFILE + ":observation-assessment", "anchor_digest": anchor.digest,
                     "phase": phase, "observer_ref": grant.subject_ref,
                     "observation_authority_ref": grant.authority_ref, "observed_at": observed_at,
                     "resource_results": results, "preservation": preservation,
                     "credential_outcomes": credentials}
            if original_claim is not None:
                audit["claim_digest"] = original_claim.digest
            assessment = self._write_once("observation-assessment", canonical(audit), context)
            expires = min(observed_at + 60, context.deadline, grant.not_after, context._observed_until)
            authority = selection.RetirementAuthority(
                context.now(), expires, context.cleanup_end, authority_ref,
                grant.authority_ref, grant.subject_ref, digest(preservation),
                preserved, revoked, canonical(results))
            value = {"profile": selection.RETIREMENT, "phase": phase,
                     "deployment_ref": self.reserved.value["deployment_ref"],
                     "namespace_ref": self.reserved.value["namespace_ref"],
                     "owner_scope_ref": self.reserved.value["owner_scope_ref"],
                     "reservation_digest": self.reserved.digest, "authority_ref": authority_ref,
                     "observer_ref": grant.subject_ref, "observation_authority_ref": grant.authority_ref,
                     "observed_at": observed_at, "expires_at": expires,
                     "resource_results": results, "preservation_digest": authority.preservation_digest,
                     "outcome": selection._retirement_outcome(authority, {item["state"] for item in results})}
            if phase == "run":
                value.update(provisioned_envelope_digest=deployed.digest,
                             final_scope_ref=linked.value["final_scope_ref"])
            result = selection.retirement(canonical(value), reserved=self.reserved,
                                            authority=authority, deployed=deployed, linked=linked)
            self._write_once("observation-result", result.raw, context)
            # The two independently acknowledged records bind exactly these facts;
            # digest equality by itself never supplied authentication.
            _check(assessment.value["resource_results"] == result.value["resource_results"])
            context.check(self.reserved)
            _check(context.now() < result.value["expires_at"] <= context._observed_until)
            _check(result.value["outcome"] == "failed" or context.now() < context.cleanup_end)
            return result


    def _fence(self, service, path, context):
        from .provider import Fence
        value = context.invoke("private", service._fencing.read, path)
        before = self.reserved.value
        _check(type(value) is Fence
               and (value.reservation_digest, value.generation_ref, value.resource_path)
               == (self.reserved.digest, before["namespace_generation_ref"], path)
               and value.writer_ref == self.provider._writer)
        _current(value.observed_at, value.expires_at, context)
        return (value.ordinary_writers == (self.provider._writer,)
                and value.outstanding_operations == ()
                and value.admission_ref == self.provider._admission)

    def _resource(self, resource, state, service, context, phase, claim):
        from .provider import Generation, Operation, _identity
        path = resource["resource_path"]
        origin = context.invoke("private", self.control.original_creation,
                                  _registration_ref(self.reserved), path)
        fence_current = self._fence(service, path, context)
        policy = service._policy(path)
        current = service._exchange(service._request("GET", policy, "observe:retirement-current", context),
                                    context)
        _check(current.status in (200, 404))
        result = {"resource_path": path, "kind": resource["kind"],
                  "create_attempt_ref": resource["create_attempt_ref"],
                  "readback_ref": current.receipt_ref}
        if type(origin) is NoSend:
            _no_send(origin, self.reserved, path, resource["create_attempt_ref"], "create")
            _check(phase == "setup" and "creation" not in state)
            if fence_current and current.status == 404:
                if state["state"] == "absent-tombstoned":
                    return {**result, "state": "not-created"}
                return {**result, "state": "pending", "reason": "retirement-pending"}
            return {**result, "state": "indeterminate", "reason": "creation-uncertain"}
        if type(origin) is Operation:
            initial = service._receipt(origin.receipt_ref, context, active=False)
            _check(initial.request.method == "PUT" and path in dict(initial.request.claims))
            reason = "creation-pending" if initial.reply.status == 202 else "creation-uncertain"
            return {**result, "state": "pending" if reason == "creation-pending" else "indeterminate",
                    "reason": reason}
        _check(type(origin) is Generation and origin.path == path and state["state"] != "reserved")
        service.prefetch_receipts(tuple(dict.fromkeys((origin.creation_receipt,
                origin.terminal_receipt, origin.readback_receipt))), decision=context)
        service._generation_history(origin, context)
        if "creation" in state:
            _check(state["creation"] == {"incarnation_ref": origin.identity_ref,
                    "create_operation_ref": origin.creation_receipt,
                    "creation_readback_ref": origin.readback_receipt})
        result["incarnation_ref"] = origin.identity_ref
        if current.status == 200:
            identity = _identity(current, policy)[2]
            if identity != origin.identity:
                return {**result, "state": "failed", "reason": "identity-mismatch"}
            # Legitimate partial detachments are still present, not terminal
            # absence. Destructive eligibility retains the provider's exact model.
            return {**result, "state": "pending", "reason": "retirement-pending"}
        if not fence_current:
            return {**result, "state": "indeterminate", "reason": "authority-missing"}
        attempt = state.get("retirement_attempt_ref")
        if attempt is None and claim is not None:
            attempt = "retirement:" + digest({"claim_digest": claim.digest,
                                                        "resource_path": path})[7:]
        deletion = context.invoke("private", self.control.original_deletion,
                                   _registration_ref(self.reserved), path, attempt)
        if type(deletion) is NoSend:
            _no_send(deletion, self.reserved, path,
                     attempt if attempt is not None else deletion.attempt_ref,
                     "delete", origin.identity_ref)
            return {**result, "state": "absent" if state["state"] == "absent-tombstoned" else "pending",
                    **({} if state["state"] == "absent-tombstoned" else {"reason":"retirement-pending"}),
                    "retirement_operation_ref": deletion.provenance_ref}
        if type(deletion) is not Deletion or deletion.terminal_ref is None:
            return {**result, "state": "indeterminate", "reason": "retirement-uncertain"}
        _check(type(deletion.operation) is Operation and deletion.operation.path == path)
        service.prefetch_receipts(tuple(dict.fromkeys((deletion.operation.receipt_ref,
                                                      deletion.terminal_ref))), decision=context)
        initial = service._receipt(deletion.operation.receipt_ref, context, active=False)
        _check(initial.request.method == "DELETE" and initial.request.attempt_ref == attempt)
        terminal = service.recorded_terminal_state(deletion.operation, deletion.terminal_ref,
                                                    method="DELETE", decision=context)
        if terminal in ("InProgress", "Running", "Accepted"):
            return {**result, "state": "pending", "reason": "retirement-pending"}
        if terminal in ("Failed", "Canceled"):
            return {**result, "state": "failed", "reason": "retirement-uncertain"}
        _check(terminal == "Succeeded")
        return {**result, "state": "absent" if state["state"] == "absent-tombstoned" else "pending",
                **({} if state["state"] == "absent-tombstoned" else {"reason":"retirement-pending"}),
                "retirement_operation_ref": deletion.operation.receipt_ref}

    def _preserved(self, context):
        targets = context.invoke("private", self.control.preservation_scope,
                                  self.reserved.value["retained_scope_ref"])
        _check(type(targets) is tuple and all(type(t) is PreservedTarget for t in targets))
        expected = set(ARM_SLOTS + STATE_SLOTS)
        _check(len(targets) == len(expected) and {t.slot for t in targets} == expected)
        _check(len({t.path for t in targets}) == len(targets))
        result = []
        preserved = True
        ephemeral = {selection.arm_key(x["resource_path"]) for x in self.reserved.value["resources"]}
        for target in targets:
            _check(type(target.path) is str and 0 < len(target.path) <= 1024)
            selection.digest(target.baseline_digest)
            if target.slot in ARM_SLOTS:
                _check(selection.arm_key(target.path) not in ephemeral)
                value = context.invoke("arm", self.preservation.read_arm, target)
            else:
                value = context.invoke("namespace", self.preservation.read_state, target)
            _check(type(value) is Preservation and value.slot == target.slot
                   and value.path == target.path
                   and (value.body is None or (type(value.body) is bytes and len(value.body) <= 1048576)))
            _current(value.observed_at, value.expires_at, context)
            selection.ref(value.provenance_ref)
            item = {"slot": target.slot, "baseline_digest": target.baseline_digest,
                    "observation_ref": value.provenance_ref,
                    "observed_at": value.observed_at, "expires_at": value.expires_at}
            if value.body is None:
                preserved = False
                item["state"] = "unavailable"
            else:
                current_digest = selection.byte_digest(value.body)
                preserved = preserved and current_digest == target.baseline_digest
                item["current_digest"] = current_digest
            result.append(item)
        return result, preserved

    def _credentials(self, context):
        registered = context.invoke("private", self.control.registered_handles,
                                     _registration_ref(self.reserved))
        actual = context.invoke("private", self.control.issued_handles,
                                 _registration_ref(self.reserved))
        for values in (registered, actual):
            _check(type(values) is tuple and len(values) <= 16 and len(set(values)) == len(values))
            for handle in values:
                selection.ref(handle)
        _check(set(registered) == set(actual))
        result = []
        revoked = True
        for handle in registered:
            value = context.invoke("private", self.control.credential_outcome,
                                     _registration_ref(self.reserved), handle)
            _check(type(value) is CredentialOutcome and value.handle_ref == handle
                   and value.owner_scope_ref == self.reserved.value["owner_scope_ref"]
                   and value.state in ("revoked", "active", "unknown"))
            _current(value.observed_at, value.expires_at, context)
            selection.ref(value.provenance_ref)
            revoked = revoked and value.state == "revoked"
            result.append({"handle_ref": handle, "state": value.state,
                           "observation_ref": value.provenance_ref,
                           "observed_at": value.observed_at, "expires_at": value.expires_at})
        return result, revoked
