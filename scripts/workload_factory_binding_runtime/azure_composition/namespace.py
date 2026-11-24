"""One-shot namespace semantics over an injected authenticated conditional store.

The embedding alone owns storage credentials. There is no store initialization,
delete, garbage collection, retry or provider operation. The initial catalog is
an out-of-band setup fact. Tests use a durable conditional-storage double.
"""
from dataclasses import dataclass, field

from workload_factory_binding.evidence import BindingError, canonical
from .selection import (
    CREATION, RESOURCE, Record, arm_key, check, closed, document, ref,
    reservation, provisioned,
)

ERROR = "azure-namespace-refused"
INDEX = "namespace-index-v1"
IDENTITY = {"namespace_ref", "namespace_generation_ref", "owner_scope_ref", "resource_keys"}
STATES = {"reserved", "create-consumed", "pending", "quarantined",
          "admitted", "retiring", "absent-tombstoned"}
EDGES = {
    "reserved": {"absent-tombstoned"},
    "create-consumed": {"pending", "quarantined", "admitted", "absent-tombstoned"},
    "pending": {"quarantined", "admitted", "absent-tombstoned"},
    "quarantined": {"admitted", "retiring", "absent-tombstoned"},
    "admitted": {"retiring", "quarantined"},
    "retiring": {"quarantined", "absent-tombstoned"},
    "absent-tombstoned": set(),
}


@dataclass(frozen=True)
class Snapshot:
    etag: str = field(repr=False)
    raw: bytes = field(repr=False)


class Namespace:
    """Internal service, supplied only trusted storage/clock/approved scope.

    Store port: read(key, timeout=), create_only(key, raw, timeout=) and
    replace(key, raw, etag=, timeout=), each returning a linearizable authenticated Snapshot.
    Per-key ETags change on every mutation and are never reused.
    A conflict or uncertain result refuses after at most one read-only reload.
    The original Decision is passed in; this class never allocates or renews one.
    """
    def __init__(self, *, store, namespace_ref, generation_ref, owner_scope_ref,
                 resource_paths):
        for value in (namespace_ref, generation_ref, owner_scope_ref):
            ref(value)
        check(type(resource_paths) is tuple and 1 <= len(resource_paths) <= 24)
        keys = tuple(arm_key(p) for p in resource_paths)
        check(keys == tuple(sorted(set(keys))))
        self._store = store
        self._identity = {
            "namespace_ref": namespace_ref,
            "namespace_generation_ref": generation_ref,
            "owner_scope_ref": owner_scope_ref,
            "resource_keys": list(keys),
        }

    def cleanup_view(self, context):
        """Source-selected P07 view; ordinary setup methods retain their clipping."""
        return _RetirementNamespace(self, context)

    def _call(self, operation, decision, *args, **kwargs):
        try:
            value = getattr(self._store, operation)(
                *args, timeout=decision.remaining(), **kwargs)
            decision.remaining()
            check(type(value) is Snapshot)
            check(type(value.etag) is str and 0 < len(value.etag) <= 160)
            document(value.raw)
            return value
        except Exception:
            raise BindingError(ERROR) from None

    def _write(self, operation, key, raw, decision, **kwargs):
        try:
            return self._call(operation, decision, key, raw, **kwargs)
        except BindingError:
            # Reconciliation only: a possibly committed mutation is never resent.
            try:
                self._call("read", decision, key)
            except BindingError:
                pass
            raise BindingError(ERROR) from None

    def _index(self, decision):
        snap = self._call("read", decision, INDEX)
        value = document(snap.raw)
        phase = value.get("phase")
        check(phase in ("unused", "preparing", "ready"))
        closed(value, IDENTITY | {"phase"} if phase == "unused"
               else IDENTITY | {"phase", "reservation_digest"})
        check({k: value[k] for k in IDENTITY} == self._identity)
        return snap, value

    def _bound(self, reserved, decision):
        check(type(reserved) is Record)
        # Public Record construction is not validation/provenance.
        reservation(reserved.raw, approved=reserved.raw)
        before = reserved.value
        for name in ("namespace_ref", "namespace_generation_ref", "owner_scope_ref"):
            check(before[name] == self._identity[name])
        check([arm_key(r["resource_path"]) for r in before["resources"]]
              == self._identity["resource_keys"])
        _, index = self._index(decision)
        check(index["phase"] == "ready" and index["reservation_digest"] == reserved.digest)
        return before

    def _current(self, reserved, path, decision):
        before = self._bound(reserved, decision)
        resource, key = self._selected_resource(before, path)
        snap = self._call("read", decision, key)
        return self._checked_current(reserved, resource, snap)

    @staticmethod
    def _selected_resource(before, path):
        key = arm_key(path)
        resource = next((r for r in before["resources"]
                         if arm_key(r["resource_path"]) == key), None)
        check(resource is not None and resource["resource_path"] == path)
        return resource, key

    def _checked_current(self, reserved, resource, snap):
        value = document(snap.raw)
        state = value.get("state")
        check(type(state) is str and state in STATES)
        expected = RESOURCE | {"reservation_digest", "state"}
        if state not in ("reserved", "create-consumed"):
            expected |= {"observation_ref"}
        if "creation" in value:
            expected |= {"creation"}
            closed(value["creation"], CREATION)
            for item in value["creation"].values():
                ref(item)
        if "retirement_attempt_ref" in value:
            expected |= {"retirement_attempt_ref"}
            ref(value["retirement_attempt_ref"])
            check("creation" in value)
        closed(value, expected)
        check({k: value[k] for k in RESOURCE} == resource)
        check(value["reservation_digest"] == reserved.digest)
        if "observation_ref" in value:
            ref(value["observation_ref"])
        if state in ("reserved", "create-consumed"):
            check("creation" not in value and "retirement_attempt_ref" not in value)
        if state in ("admitted", "retiring"):
            check("creation" in value)
        if state == "admitted":
            check("retirement_attempt_ref" not in value)
        if state == "retiring":
            check("retirement_attempt_ref" in value)
        return snap, value

    @staticmethod
    def _setup(reserved, decision):
        window = reserved.value["window"]
        now = decision.now()
        check(window["not_before"] <= now < window["not_after"])
        # Clip the existing clock once to the original setup scope, never renew.
        decision.clip(window["not_after"])

    def reserve(self, reserved, *, approved, decision):
        """Consume the entire approved name set before any create-only blob write."""
        try:
            check(type(reserved) is Record)
            reservation(reserved.raw, approved=approved)
            self._setup(reserved, decision)
            value = reserved.value
            for name in ("namespace_ref", "namespace_generation_ref", "owner_scope_ref"):
                check(value[name] == self._identity[name])
            check([arm_key(r["resource_path"]) for r in value["resources"]]
                  == self._identity["resource_keys"])
            snap, index = self._index(decision)
            check(index["phase"] == "unused")
            preparing = {**index, "phase": "preparing", "reservation_digest": reserved.digest}
            claimed = self._write("replace", INDEX, canonical(preparing), decision, etag=snap.etag)
            check(claimed.raw == canonical(preparing))
            for resource in value["resources"]:
                raw = canonical({**resource, "reservation_digest": reserved.digest,
                                 "state": "reserved"})
                created = self._write("create_only", arm_key(resource["resource_path"]),
                                      raw, decision)
                check(created.raw == raw)
            ready = canonical({**preparing, "phase": "ready"})
            result = self._write("replace", INDEX, ready, decision, etag=claimed.etag)
            check(result.raw == ready)
        except Exception:
            raise BindingError(ERROR) from None

    def read(self, reserved, path, *, decision):
        """No creation/repair on missing expected state, even after restart/expiry."""
        try:
            return Record(self._current(reserved, path, decision)[0].raw)
        except Exception:
            raise BindingError(ERROR) from None

    def consume_create(self, reserved, path, *, attempt_ref, decision):
        """Only a successful durable CAS may precede a future provider send."""
        try:
            self._setup(reserved, decision)
            snap, value = self._current(reserved, path, decision)
            check(value["state"] == "reserved" and value["create_attempt_ref"] == attempt_ref)
            raw = canonical({**value, "state": "create-consumed"})
            result = self._write("replace", arm_key(path), raw, decision, etag=snap.etag)
            check(result.raw == raw)
            return Record(result.raw)
        except Exception:
            raise BindingError(ERROR) from None

    def transition(self, reserved, path, *, state, observation_ref, decision,
                   creation=None, retirement_attempt_ref=None):
        """Trusted provider/watchdog adapters supply authenticated observation refs.

        This internal storage method does not authenticate provider facts, grant a
        retirement send or emit a qualification receipt. Those are later slices.
        """
        try:
            self._setup(reserved, decision)
            ref(observation_ref)
            snap, value = self._current(reserved, path, decision)
            check(type(state) is str and state in EDGES[value["state"]])
            if "retirement_attempt_ref" in value:
                check(state in ("quarantined", "absent-tombstoned"))
            if value["state"] == "reserved":
                check(creation is None)
            if creation is not None:
                closed(creation, CREATION)
                for item in creation.values():
                    ref(item)
                check("creation" not in value or value["creation"] == creation)
            updated = {**value, "state": state, "observation_ref": observation_ref}
            if creation is not None:
                updated["creation"] = dict(creation)
            if state in ("admitted", "retiring"):
                check("creation" in updated)
            if state == "retiring":
                ref(retirement_attempt_ref)
                check("retirement_attempt_ref" not in value)
                updated["retirement_attempt_ref"] = retirement_attempt_ref
            else:
                check(retirement_attempt_ref is None)
            raw = canonical(updated)
            result = self._write("replace", arm_key(path), raw, decision, etag=snap.etag)
            check(result.raw == raw)
            return Record(result.raw)
        except Exception:
            raise BindingError(ERROR) from None

    def provisioned(self, raw, *, reserved, authenticated_readback, decision):
        """A provisioned form additionally requires every namespace entry admitted."""
        try:
            result = provisioned(raw, reserved=reserved,
                                 authenticated_readback=authenticated_readback)
            snapshots = []
            for resource in result.value["resources"]:
                path = resource["resource_path"]
                snap, current = self._current(reserved, path, decision)
                check(current["state"] == "admitted")
                check(current["creation"] == {k: resource[k] for k in CREATION})
                snapshots.append((arm_key(path), snap))
            # Non-reused revisions make the unchanged read intervals overlap:
            # the whole admitted set existed between the two read passes.
            for key, original in snapshots:
                current = self._call("read", decision, key)
                check(current == original)
            return result
        except Exception:
            raise BindingError(ERROR) from None


class _RetirementNamespace(Namespace):
    def __init__(self, original, context):
        from .retirement import _Context
        check(type(original) is Namespace and type(context) is _Context)
        context.check(context.reserved)
        self._store, self._identity = original._store, dict(original._identity)
        self._context = context

    def reserve(self, *args, **kwargs):
        raise BindingError(ERROR) from None

    def consume_create(self, *args, **kwargs):
        raise BindingError(ERROR) from None

    def provisioned(self, raw, *, reserved, authenticated_readback, decision):
        check(decision is self._context and self._context.account.pool == "registration"
              and self._context.account._meter["run_transaction"])
        return super().provisioned(raw, reserved=reserved,
                                  authenticated_readback=authenticated_readback, decision=decision)

    def _setup(self, reserved, decision):
        check(decision is self._context)
        self._context.check(reserved, write=True)

    def _call(self, operation, decision, *args, **kwargs):
        failed = False
        value = None
        try:
            check(decision is self._context and operation in ("read", "read_many", "replace"))
            self._context.check(self._context.reserved, write=operation == "replace")
            value = self._context.state(self._store, operation, *args, **kwargs)
            snapshots = value if operation == "read_many" else (value,)
            check(type(snapshots) is tuple)
            for selected in snapshots:
                check(type(selected) is Snapshot and type(selected.etag) is str
                      and 0 < len(selected.etag) <= 160)
                document(selected.raw)
        except BaseException:
            failed = True
        if failed:
            raise BindingError(ERROR) from None
        return value

    def transition(self, reserved, path, *, state, **kwargs):
        check(state in ("admitted", "retiring", "quarantined", "absent-tombstoned"))
        return super().transition(reserved, path, state=state, **kwargs)


    def read_set(self, reserved, *, decision):
        """Independent read-only exact set inside one non-reused catalog interval."""
        check(decision is self._context and self._context.account.pool == "observation")
        first, _ = self._index(decision)
        before = self._bound(reserved, decision)
        selected = [self._selected_resource(before, item["resource_path"])
                    for item in before["resources"]]
        keys = tuple(key for _, key in selected)
        snapshots = self._call("read_many", decision, keys)
        check(type(snapshots) is tuple and len(snapshots) == len(selected))
        records = []
        for (resource, _), snap in zip(selected, snapshots):
            self._checked_current(reserved, resource, snap)
            records.append(Record(snap.raw))
        last, _ = self._index(decision)
        check(last == first)
        return tuple(records)
