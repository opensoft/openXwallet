"""Isolated accepted P07 accounting and external retirement controls; no Azure I/O."""
from concurrent.futures import ThreadPoolExecutor
import os
import pickle
import time

import pytest
from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.azure_composition import retirement as r


class Clock:
    def __init__(self):
        self.wall = 1000000
        self.mono = 100.0

    def account(self, pool="cleanup"):
        return r._Account(pool, owner="owner:original", deadline=self.wall + 1000,
                          clock=lambda: self.wall, monotonic=lambda: self.mono)


@pytest.mark.parametrize("pool,limits,seconds", [
    ("registration", (128, 0, 128, 32, 1048576), 30),
    ("cleanup", (768, 160, 512, 128, 12582912), 300),
    ("observation", (192, 48, 128, 32, 3145728), 60),
])
def test_fixed_original_pool_and_clock(pool, limits, seconds):
    clock = Clock()
    account = clock.account(pool)
    assert tuple(account.limits) == limits
    assert account.deadline == clock.wall + seconds
    assert account.monotonic_end == clock.mono + seconds
    with pytest.raises(TypeError):
        r.LIMITS[pool] = limits


@pytest.mark.parametrize("group,cap", [("private", 768), ("arm", 160),
                                       ("namespace", 512), ("journal", 128)])
def test_each_class_refuses_before_the_first_over_budget_effect(group, cap):
    account = Clock().account()
    effects = []
    for _ in range(cap):
        account.charge(group)
        effects.append(group)
    with pytest.raises(BindingError, match=r.ERROR):
        account.charge(group)
    assert len(effects) == cap
    assert account.counts[group] == cap
    assert all(value == 0 for key, value in account.counts.items() if key != group)


def test_concurrent_debits_are_one_serial_original_account():
    account = Clock().account()
    def attempt(_):
        try:
            account.charge("private")
            return True
        except BindingError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(attempt, range(900)))
    assert sum(outcomes) == 768
    assert account.counts["private"] == 768


@pytest.mark.parametrize("change", ["wall-expiry", "monotonic-expiry", "wall-regression",
                                     "monotonic-regression", "nan", "infinite"])
def test_original_clock_never_renews_or_accepts_regression(change):
    clock = Clock()
    account = clock.account()
    if change == "wall-expiry":
        clock.wall += 300
    elif change == "monotonic-expiry":
        clock.mono += 300
    elif change == "wall-regression":
        clock.wall -= 1
    elif change == "monotonic-regression":
        clock.mono -= 1
    elif change == "nan":
        clock.mono = float("nan")
    else:
        clock.mono = float("inf")
    with pytest.raises(BindingError, match=r.ERROR):
        account.charge("private")
    assert account.counts["private"] == 0


def test_complete_bytes_are_not_truncated_or_refunded():
    account = Clock().account()
    account.charge("namespace", size=account.limits[4])
    with pytest.raises(BindingError, match=r.ERROR):
        account.receive(1)
    assert account.bytes_used == account.limits[4] + 1
    assert account.counts["namespace"] == 1


@pytest.mark.parametrize("bad", [True, -1, 1.5, "1"])
def test_invalid_byte_amount_refuses_before_any_call(bad):
    account = Clock().account()
    with pytest.raises(BindingError, match=r.ERROR):
        account.charge("private", size=bad)
    assert account.counts["private"] == 0


def test_trigger_admission_is_bounded_before_duplicate_work():
    account = Clock().account()
    assert [account.admit_trigger() for _ in range(4)] == [1, 2, 3, 4]
    with pytest.raises(BindingError, match=r.ERROR):
        account.admit_trigger()
    assert account.deliveries == 4
    assert not any(account.counts.values())


def test_lost_owner_burns_without_transfer_or_serialization():
    account = Clock().account()
    account.burn()
    with pytest.raises(BindingError, match=r.ERROR):
        account.charge("arm")
    with pytest.raises(TypeError):
        pickle.dumps(account)
    assert account.counts["arm"] == 0


def test_fork_does_not_inherit_mutation_allocation():
    account = Clock().account()
    pid = os.fork()
    if pid == 0:
        try:
            account.charge("arm")
        except BindingError:
            os._exit(0)
        os._exit(9)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert account.counts["arm"] == 0


def test_per_call_timeout_clips_to_original_absolute_and_monotonic_limits():
    clock = Clock()
    account = clock.account()
    assert account.remaining() == 10
    clock.wall = account.deadline - 2
    assert 0 < account.remaining() <= 2


def test_separate_observer_account_does_not_restore_burned_cleanup():
    clock = Clock()
    cleanup = clock.account()
    cleanup.charge("arm")
    cleanup.burn()
    observer = clock.account("observation")
    observer.charge("arm")
    with pytest.raises(BindingError, match=r.ERROR):
        cleanup.charge("arm")
    assert cleanup.counts["arm"] == 1
    assert observer.counts["arm"] == 1


from . import test_azure_provider as provider_fixture
from . import test_azure_namespace as namespace_fixture
from workload_factory_binding_runtime.azure_composition import provider as provider_module


def context(reserved, clock, *, pool="cleanup", cleanup_end=None):
    value = reserved.value
    account = clock.account(pool)
    grant = r.Grant(reserved.digest, value["namespace_generation_ref"],
                    value["owner_scope_ref"], value["source_roles_digest"],
                    value["retained_scope_ref"], value["setup_authority_ref"],
                    provider_fixture.WRITER, account.owner, pool, clock.wall - 1,
                    clock.wall + 1000, "grant:independent-authenticated", clock.wall - 2, clock.wall + 1000)
    return r._Context(key=r._CONTEXT, reserved=reserved, account=account, grant=grant,
                      cleanup_end=cleanup_end or account.deadline)


@pytest.fixture
def admitted(provider_fixture_fx):
    reserved, namespace, store, policies, port, make = provider_fixture_fx
    service = make()
    operation = service.create(namespace_fixture.PATHS["vm"], decision=namespace_fixture.decision())
    generation = service.admit(operation, decision=namespace_fixture.decision())
    port.put_model(generation.path, detached=True)
    return reserved, namespace, store, port, service, generation


@pytest.fixture
def provider_fixture_fx(tmp_path):
    return provider_fixture.fx.__wrapped__(tmp_path)


def test_new_account_fields_cannot_be_rebound_to_a_larger_pool():
    account = Clock().account("registration")
    with pytest.raises(AttributeError):
        account.pool = "cleanup"
    with pytest.raises(AttributeError):
        account.owner = "owner:replacement"


def test_cleanup_after_setup_expiry_preserves_old_refusal_and_one_original_account(admitted):
    reserved, _, store, port, original, generation = admitted
    clock = Clock()
    clock.wall = reserved.value["window"]["not_after"] + 1
    with pytest.raises(BindingError):
        original.retire(generation, attempt_ref="retire:old-refused",
                        decision=namespace_fixture.decision(clock.wall))
    assert port.sends("DELETE") == []
    selected = context(reserved, clock)
    service = original.cleanup_view(selected)
    operation = service.retire(generation, attempt_ref="retire:original", decision=selected)
    final = service.deletion_complete(operation, generation, decision=selected)
    assert final.startswith("receipt:")
    assert port.sends("DELETE") == [(generation.path,)]
    assert selected.account.counts["arm"] == 3
    assert selected.account.counts["namespace"] > 0
    assert selected.account.counts["private"] > 0
    assert selected.account.bytes_used > 0
    assert all(d is selected for d in port.decisions if getattr(d, "account", None) is selected.account)
    assert store.read(provider_module.arm_key(generation.path), timeout=1).raw


def test_current_read_only_context_cannot_create_admit_or_retire(admitted):
    reserved, _, _, port, original, generation = admitted
    clock = Clock()
    clock.wall = reserved.value["window"]["not_after"] + 1
    observer = context(reserved, clock, pool="observation")
    service = original.cleanup_view(observer)
    for call in (lambda: service.create(generation.path, decision=observer),
                 lambda: service.admit(provider_module.Operation(generation.path, "receipt:none"), decision=observer),
                 lambda: service.retire(generation, attempt_ref="retire:forbidden", decision=observer)):
        with pytest.raises(BindingError):
            call()
    assert port.sends("DELETE") == []
    assert not any(observer.account.counts.values())
    observed, identity = service.observe(generation.path, decision=observer, retiring=True)
    assert observed.status == 200
    assert identity == generation.identity


def test_namespace_cleanup_view_cannot_reserve_or_consume_creation(admitted):
    reserved, original, _, _, _, _ = admitted
    selected = context(reserved, Clock())
    namespace = original.cleanup_view(selected)
    with pytest.raises(BindingError):
        namespace.reserve(reserved, approved=reserved.raw, decision=selected)
    with pytest.raises(BindingError):
        namespace.consume_create(reserved, namespace_fixture.PATHS["nic"],
                                 attempt_ref="create:nic", decision=selected)
    assert not any(selected.account.counts.values())


def test_a_different_context_cannot_spend_an_existing_cleanup_view(admitted):
    reserved, _, _, port, original, generation = admitted
    selected = context(reserved, Clock())
    unrelated = context(reserved, Clock())
    service = original.cleanup_view(selected)
    with pytest.raises(BindingError):
        service.observe(generation.path, decision=unrelated)
    assert port.sends("DELETE") == []
    assert not any(unrelated.account.counts.values())


def test_genuine_later_registration_has_one_new_clock_and_the_original_meter():
    clock = Clock()
    original = clock.account("registration")
    original.charge("private", size=30)
    original.charge("journal")
    clock.wall += 31
    clock.mono += 31
    with pytest.raises(BindingError):
        original.remaining()
    later = r._Account._later_registration(original, key=r._TRANSACTION,
                                           deadline=clock.wall + 600)
    assert later.deadline == clock.wall + 30
    assert later.counts == original.counts
    assert later.bytes_used == 30
    later.charge("private", size=10)
    assert original.counts["private"] == 2
    assert original.bytes_used == 40
    with pytest.raises(BindingError):
        r._Account._later_registration(original, key=r._TRANSACTION,
                                       deadline=clock.wall + 600)


def test_later_transaction_cannot_transfer_a_mutation_or_burned_allocation():
    clock = Clock()
    cleanup = clock.account()
    with pytest.raises(BindingError):
        r._Account._later_registration(cleanup, key=r._TRANSACTION,
                                       deadline=clock.wall + 600)
    original = clock.account("registration")
    original.burn()
    with pytest.raises(BindingError):
        r._Account._later_registration(original, key=r._TRANSACTION,
                                       deadline=clock.wall + 600)


@pytest.mark.parametrize("value", [None, False, 123, "a\n\"b", b"", b"xyz", b"xy", b"x",
                                    {"a": [1, b"abc"], "escaped\"": None}])
def test_complete_frame_size_matches_real_canonical_encoding(value):
    from workload_factory_binding.evidence import canonical
    assert r._frame_size(value) == len(canonical(r._wire(value)))


def test_late_reply_bytes_remain_in_the_failed_actual_trace():
    clock = Clock()
    account = clock.account()
    clock.wall = account.deadline
    with pytest.raises(BindingError):
        account.receive(17)
    assert account.bytes_used == 17


# Independent first-pilot oracle. These prospective IDs are source fixtures, never
# cloud targets; all effects below live in the explicitly owned SQLite doubles.
import base64
from contextlib import closing
from dataclasses import asdict, replace
import copy
import hashlib
import json
import sqlite3
from pathlib import Path
import uuid
from urllib.parse import urlsplit
from workload_factory_binding.evidence import canonical, digest
from workload_factory_binding_runtime.azure_composition import selection as selection_module
from workload_factory_binding_runtime.azure_composition.namespace import Namespace, Snapshot, INDEX

PILOT_SUB = "297b2389-33bf-48c8-8deb-0b92838431e4"
PILOT_PARENT = "/subscriptions/" + PILOT_SUB + "/resourceGroups/rg-opensoft-wallet-mfa-qa"
PILOT_ROLES = ("control", "gate", "worker")
OWNER_WRITER = "writer:external-retirement"
PROVISIONER_WRITER = "writer:original-provisioner"


def pilot_resources():
    kinds = {"vm": ("Microsoft.Compute", "virtualMachines", "vm"),
             "os_disk": ("Microsoft.Compute", "disks", "osdisk"),
             "nic": ("Microsoft.Network", "networkInterfaces", "nic"),
             "public_ip": ("Microsoft.Network", "publicIPAddresses", "pip"),
             "vnet": ("Microsoft.Network", "virtualNetworks", "vnet"),
             "nsg": ("Microsoft.Network", "networkSecurityGroups", "nsg")}
    def path(kind, role=""):
        provider, resource_type, prefix = kinds[kind]
        suffix = "-" + role if role else ""
        return (PILOT_PARENT + "/providers/" + provider + "/" + resource_type + "/"
                + prefix + "-wallet-mfa" + suffix + "-qa-01")
    result = []
    for kind in kinds:
        roles = PILOT_ROLES if kind in ("vm", "os_disk", "nic", "nsg") else ("",)
        if kind == "public_ip":
            roles = ("control",)
        for role in roles:
            dependencies = []
            if kind in ("os_disk", "nic"):
                dependencies = [path("vm", role)]
            elif kind == "public_ip":
                dependencies = [path("nic", "control")]
            elif kind == "vnet":
                dependencies = [path("nic", item) for item in PILOT_ROLES]
            elif kind == "nsg":
                dependencies = [path("nic", role), path("vnet")]
            result.append({"resource_path": path(kind, role), "kind": kind,
                           "dependency_paths": sorted(dependencies, key=str.lower),
                           "resource_policy_ref": "policy:" + kind + ":" + (role or "pilot"),
                           "create_attempt_ref": "create:" + kind + ":" + (role or "pilot"),
                           "disposition": "ephemeral"})
    return sorted(result, key=lambda item: item["resource_path"].lower())


class FixtureProtocolError(ValueError):
    pass


_FIXTURE_ERRORS = []


def fixture_require(condition):
    if not condition:
        _FIXTURE_ERRORS.append("fixture-protocol-refused")
        raise FixtureProtocolError("fixture-protocol-refused")


@pytest.fixture(autouse=True)
def fixture_protocol_health():
    before = len(_FIXTURE_ERRORS)
    yield
    assert len(_FIXTURE_ERRORS) == before, "unexpected fixture protocol failure cannot prove product refusal"


def existing_db(path, *, readonly=False):
    return sqlite3.connect(Path(path).as_uri()+("?mode=ro" if readonly else "?mode=rw"),uri=True)


class ReadLimit(ValueError):
    def __init__(self, observed):
        self.observed = observed
        super().__init__("synthetic-response-limit")


def bounded_rows(db, table, key_column, keys, limit, *, max_record=1048576):
    """One selected backend read: metadata first, bounded incremental bodies.

    The embedded durable server performs no external calls. Its local SQLite
    metadata/blob operations are bounded implementation work inside that one
    selected backend API; they are not represented as extra network RPCs.
    """
    if not 0 < len(keys) <= 64 or len(set(keys)) != len(keys) or limit <= 0:
        raise ValueError("synthetic-bounded-read-shape")
    if (table,key_column) not in (("blobs","name"),("receipts","ref"),("resources","path")):
        raise ValueError("synthetic-bounded-read-source")
    placeholders=",".join("?" for _ in keys)
    revision="revision" if table=="blobs" else "0"
    if not db.in_transaction:db.execute("BEGIN")
    metadata=db.execute("SELECT rowid,"+key_column+","+revision+",length(body) FROM "
                        +table+" WHERE "+key_column+" IN ("+placeholders+")",keys).fetchmany(len(keys)+1)
    if len(metadata)>len(keys):
        raise ValueError("synthetic-bounded-read-count")
    if any(type(row[3]) is not int or row[3]<0 for row in metadata):
        raise ValueError("synthetic-bounded-read-length")
    if sum(row[3] for row in metadata)>limit or any(row[3]>max_record for row in metadata):
        raise ReadLimit(audit_size({"error":"response-limit"}))
    result=[]
    remaining=limit
    for rowid,key,version,size in metadata:
        with db.blobopen(table,"body",rowid,readonly=True) as blob:
            if len(blob)!=size:
                raise ValueError("synthetic-bounded-read-snapshot")
            body=blob.read(min(size,remaining))
        if len(body)!=size:
            raise ValueError("synthetic-bounded-read-incomplete")
        remaining-=len(body)
        result.append((key,version,size,body))
    return result


class AtomicStore(namespace_fixture.Store):
    """Existing owned service state. Runtime access never creates a missing file.

    A successful conditional write returns its actual committed write ACK, not an
    unmetered extra read. Every data read/write is independently visible in events.
    """
    def __init__(self, path, *, initial=None, initialize=True):
        if not initialize:
            self.path,self.events,self.fault,self.read_hook=path,[],None,None
            if not path.is_file():raise LookupError("synthetic-existing-store-missing")
            return
        super().__init__(path, initialize=True, initial=initial)
        with closing(sqlite3.connect(path)) as db:
            db.execute("CREATE TABLE sequence(n INTEGER)")
            db.execute("INSERT INTO sequence VALUES(1)")
            db.commit()

    def connection(self):
        return sqlite3.connect("file:" + str(self.path) + "?mode=rw", uri=True, timeout=5)

    def lookup(self, key, *, timeout):
        fixture_require(timeout > 0)
        self.events.append(("read", key))
        with closing(self.connection()) as db:
            row = db.execute("SELECT revision,body FROM blobs WHERE name=?", (key,)).fetchone()
        if self.read_hook:
            self.read_hook(key)
        return None if row is None else Snapshot(str(row[0]), row[1])

    def read(self, key, *, timeout):
        result = self.lookup(key, timeout=timeout)
        if result is None:
            raise LookupError("synthetic-state-missing")
        return result

    def read_many(self, keys, *, timeout):
        fixture_require(type(keys) is tuple and 0 < len(keys) <= 64)
        self.events.append(("read_many", keys))
        placeholders = ",".join("?" for _ in keys)
        with closing(self.connection()) as db:
            rows = db.execute("SELECT name,revision,body FROM blobs WHERE name IN (" + placeholders + ")", keys).fetchall()
        values = {row[0]: Snapshot(str(row[1]), row[2]) for row in rows}
        if set(values) != set(keys):
            raise LookupError("synthetic-batch-missing")
        return tuple(values[key] for key in keys)

    def read_limited(self, operation, keys, *, limit, timeout):
        many = operation == "read_many"
        selected = keys if many else (keys,)
        # Canonical base64 envelope overhead is reserved before reading raw bodies.
        raw_limit = max(0, (limit - 256 * len(selected)) * 3 // 4)
        with closing(self.connection()) as db:
            rows = bounded_rows(db, "blobs", "name", selected, min(raw_limit,16384 * len(selected)),max_record=16384)
        values = {row[0]:Snapshot(str(row[1]),row[3]) for row in rows}
        if operation == "lookup" and not values:
            return None
        if set(values) != set(selected):
            raise LookupError("synthetic-bounded-read-missing")
        snapshots = tuple(values[key] for key in selected)
        return snapshots if many else snapshots[0]

    def _mutate(self, key, raw, etag, op):
        self.events.append((op, key))
        if self.fault == (op, key, "before"):
            raise TimeoutError("synthetic-before-write")
        with closing(self.connection()) as db:
            db.execute("BEGIN IMMEDIATE")
            revision = db.execute("UPDATE sequence SET n=n+1 RETURNING n").fetchone()[0]
            if op == "create_only":
                db.execute("INSERT INTO blobs VALUES (?,?,?)", (key, revision, raw))
            else:
                changed = db.execute("UPDATE blobs SET revision=?,body=? WHERE name=? AND revision=?",
                                     (revision, raw, key, int(etag)))
                if changed.rowcount != 1:
                    raise RuntimeError("synthetic-conflict")
            db.commit()
        if self.fault == (op, key, "after"):
            raise TimeoutError("synthetic-write-ack-lost")
        return Snapshot(str(revision), raw)


def pilot_policies(reserved):
    resources = reserved.value["resources"]
    paths = {(x["kind"], x["resource_policy_ref"].split(":")[-1]): x["resource_path"] for x in resources}
    image = PILOT_PARENT + "/providers/Microsoft.Compute/images/measured"
    disks = {role: PILOT_PARENT + "/providers/Microsoft.Compute/disks/retained-" + role
             for role in ("control", "gate")}
    vnet = paths[("vnet", "pilot")]
    result = []
    for resource in resources:
        kind = resource["kind"]
        role = resource["resource_policy_ref"].split(":")[-1]
        if kind == "vm":
            data = []
            if role in disks:
                data = [{"lun": 0, "createOption": "Attach", "deleteOption": "Detach",
                         "managedDisk": {"id": disks[role]}}]
            live = {"storageProfile": {"imageReference": {"id": image},
                    "osDisk": {"name": paths[("os_disk", role)].split("/")[-1],
                               "createOption": "FromImage", "deleteOption": "Detach",
                               "managedDisk": {"id": paths[("os_disk", role)]}}, "dataDisks": data},
                    "networkProfile": {"networkInterfaces": [{"id": paths[("nic", role)],
                                       "properties": {"primary": True, "deleteOption": "Detach"}}]}}
            detached, create = copy.deepcopy(live), copy.deepcopy(live)
        elif kind == "os_disk":
            live = {"diskState": "Attached", "managedBy": paths[("vm", role)]}
            detached = {"diskState": "Unattached"}
            create = {"creationData": {"createOption": "Empty"}, "diskSizeGB": 64}
        elif kind == "nic":
            ip = {"subnet": {"id": vnet + "/subnets/" + role}, "privateIPAddress": "10.33.0.4"}
            if role == "control":
                ip["publicIPAddress"] = {"id": paths[("public_ip", "control")],
                                         "properties": {"deleteOption": "Detach"}}
            live = {"virtualMachine": {"id": paths[("vm", role)]}, "enableIPForwarding": False,
                    "ipConfigurations": [{"name": "ip", "properties": ip}]}
            detached = copy.deepcopy(live)
            detached.pop("virtualMachine")
            create = copy.deepcopy(detached)
        elif kind == "public_ip":
            live = {"ipConfiguration": {"id": paths[("nic", "control")] + "/ipConfigurations/ip"}}
            detached = {}
            create = {}
        elif kind == "vnet":
            live = {"subnets": [{"id": vnet + "/subnets/" + item,
                    "properties": {"ipConfigurations": [{"id": paths[("nic", item)] + "/ipConfigurations/ip"}],
                                   "delegations": []}} for item in PILOT_ROLES], "virtualNetworkPeerings": []}
            detached = copy.deepcopy(live)
            for subnet in detached["subnets"]:
                subnet["properties"]["ipConfigurations"] = []
            create = copy.deepcopy(live)
        else:
            live = {"networkInterfaces": [{"id": paths[("nic", role)]}],
                    "subnets": [{"id": vnet + "/subnets/" + role}], "securityRules": []}
            detached = {"networkInterfaces": [], "subnets": [], "securityRules": []}
            create = copy.deepcopy(live)
        result.append(provider_module.Policy(resource["resource_path"], kind, resource["resource_policy_ref"],
                      canonical({"location": "westus", "properties": create}), canonical(live), canonical(detached)))
    return tuple(result), (image, disks["control"], disks["gate"])


def audit_wire(value):
    """Independent encoded bytes, not the runtime's size estimator or encoder."""
    import dataclasses
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    if isinstance(value, bytes):
        return {"bytes": base64.b64encode(value).decode("ascii")}
    if isinstance(value, dict):
        return {key:audit_wire(item) for key,item in value.items()}
    if isinstance(value, (tuple, list)):
        return [audit_wire(item) for item in value]
    return value


def audit_size(value):
    return len(json.dumps(audit_wire(value), sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8"))


def measured_port(pilot, function):
    def call(*args, **kwargs):
        decision = kwargs.get("decision")
        pool = decision.account.pool if decision is not None and hasattr(decision, "account") else pilot.pool
        metadata = {name:value for name,value in kwargs.items()
                    if name not in ("decision", "timeout") and not callable(value)}
        size = audit_size({"arguments":args, "metadata":metadata})
        value = function(*args, **kwargs)
        pilot.wire_bytes[pool] = pilot.wire_bytes.get(pool, 0) + size + audit_size(value)
        return value
    return call


class PilotFacade:
    """Selected private namespace API with independently logged physical backend I/O."""
    def __init__(self, pilot):
        self.pilot = pilot

    def exchange(self, operation, args, kwargs, *, decision, timeout):
        self.pilot.event(decision, "private", "namespace:" + operation)
        return self.pilot.backend(decision, "namespace", getattr(self.pilot.store, operation),
                                  *args, **kwargs)


class PilotPorts(provider_fixture.Ports):
    def __init__(self, pilot, *, initialize=True):
        super().__init__(pilot.root / "provider.db", pilot.reserved, pilot.policies, initialize=initialize)
        self.pilot = pilot
        self.ids = {path: str(uuid.UUID(int=index + 100))
                    for index, path in enumerate(self.policies)}
        self.active_writer = PROVISIONER_WRITER
        self.deleted = []
        if initialize:
            with closing(existing_db(self.path)) as db:
                db.execute("CREATE TABLE operations(path TEXT,attempt TEXT,method TEXT,ref TEXT,url TEXT,locator TEXT,PRIMARY KEY(ref))")
                db.execute("CREATE INDEX exact_operation ON operations(path,attempt,method)")
                db.commit()
        elif not self.path.is_file():
            raise LookupError("synthetic-existing-provider-missing")

    def body(self, path):
        limit=getattr(self,"_response_cap",1048576)
        with closing(existing_db(self.path,readonly=True)) as db:
            rows=bounded_rows(db,"resources","path",(path,),limit)
        return None if not rows else rows[0][3]

    def sends(self, method):
        with closing(existing_db(self.path,readonly=True)) as db:
            return db.execute("SELECT path FROM sends WHERE method=? ORDER BY n",(method,)).fetchall()

    def put_model(self, path, *, detached=False, mutation=None):
        def own(value):
            policy = self.policies[path]
            value["properties"][provider_fixture.OWN_FIELDS[policy.kind]] = self.ids[path]
            if mutation:
                mutation(value)
        return super().put_model(path, detached=detached, mutation=own)

    def _respond(self, request):
        policy = self.policies[request.path]
        version = provider_fixture.API_VERSIONS[policy.kind]
        fixture_require(request.url.endswith("?api-version=" + version))
        identity = "incarnation:" + self.ids[request.path]
        if "/locations/" in request.url:
            op = urlsplit(request.url).path.rsplit("/", 1)[-1]
            return canonical({"status": self.status, "name": op}), 200, None, None
        if request.method == "PUT":
            for path, _ in request.claims:
                self.put_model(path)
            body, status, locator = self.body(request.path), 201, None
        elif request.method == "DELETE":
            before=self.body(request.path)
            if policy.kind=="vm" and before is not None:
                model=json.loads(before)
                for disk in model["properties"]["storageProfile"]["dataDisks"]:
                    if disk.get("deleteOption")=="Delete":
                        with closing(existing_db(self.path)) as db:
                            db.execute("DELETE FROM resources WHERE path=?",(disk["managedDisk"]["id"],))
                            db.commit()
            # The server enforces detach prerequisites independently of the client.
            resource = next(x for x in self.r.value["resources"] if x["resource_path"] == request.path)
            fixture_require(all(self.body(path) is None for path in resource["dependency_paths"]))
            with closing(existing_db(self.path)) as db:
                db.execute("DELETE FROM resources WHERE path=?", (request.path,))
                db.commit()
            self.deleted.append(request.path)
            self.detach(request.path)
            body, status, locator, identity = b"", 204, None, None
        else:
            body = self.body(request.path)
            return (canonical({}), 404, None, None) if body is None else (body, 200, identity, None)
        if self.async_kind == policy.kind:
            op = "op-" + hashlib.sha256((request.path + request.method + request.attempt_ref).encode()).hexdigest()[:20]
            locator = (provider_module.ARM + "/subscriptions/" + PILOT_SUB + "/providers/"
                       + provider_fixture.RESOURCE_TYPES[policy.kind].split("/")[0]
                       + "/locations/westus/operations/" + op + "?api-version=" + version)
            return canonical({"properties": {"provisioningState": "Creating"}}) if request.method == "PUT" else canonical({}), 202, None, locator
        return body, status, identity, locator

    def detach(self, deleted):
        for path, policy in self.policies.items():
            raw = self.body(path)
            if raw is None:
                continue
            value = json.loads(raw)
            props = value["properties"]
            if value.get("managedBy") == deleted:
                value.pop("managedBy")
                props["diskState"] = "Unattached"
            if props.get("virtualMachine", {}).get("id") == deleted:
                props.pop("virtualMachine")
            if props.get("ipConfiguration", {}).get("id", "").startswith(deleted + "/"):
                props.pop("ipConfiguration")
            for subnet in props.get("subnets", []):
                if "properties" in subnet:
                    subnet["properties"]["ipConfigurations"] = [x for x in subnet["properties"]["ipConfigurations"]
                        if not x["id"].startswith(deleted + "/")]
            if policy.kind == "nsg":
                props["networkInterfaces"] = [x for x in props["networkInterfaces"] if x["id"] != deleted]
                props["subnets"] = [x for x in props["subnets"] if not x["id"].startswith(deleted + "/")]
            with closing(existing_db(self.path)) as db:
                db.execute("UPDATE resources SET body=? WHERE path=?", (canonical(value), path))
                db.commit()

    def exchange_for(self, principal, request, *, decision, timeout, before_send):
        fixture_require(0 < timeout <= 10)
        self.pilot.event(decision, "arm", request.method)
        self._response_cap=decision.reply_limit() if hasattr(decision,"reply_limit") else 1048576
        if hasattr(decision,"account"):
            header=audit_size({"arm_body_limit":self._response_cap})
            decision.account.request_metadata(header)
            pool=decision.account.pool
            self.pilot.wire_bytes[pool]=self.pilot.wire_bytes.get(pool,0)+header
        if request.method == "PUT":
            if principal != PROVISIONER_WRITER or principal != self.active_writer:
                raise PermissionError("synthetic-create-denied")
        if request.method == "DELETE":
            if (principal != OWNER_WRITER or principal != self.active_writer
                    or not hasattr(decision, "account") or decision.account.pool != "cleanup"):
                raise PermissionError("synthetic-retirement-denied")
        if self.before_send:
            self.before_send(request)
        before_send()
        if self.fault == "before-send" and request.method in ("PUT", "DELETE"):
            raise TimeoutError("synthetic-before-send")
        with closing(existing_db(self.path)) as db:
            db.execute("INSERT INTO sends(method,path) VALUES (?,?)", (request.method, request.path))
            db.commit()
        body, status, identity, locator = self._respond(request)
        reply = provider_module.Reply(status, body, "receipt:" + uuid.uuid4().hex, identity, locator)
        if self.reply_mutation:
            reply = self.reply_mutation(request, reply)
        encoded = canonical(r._wire(provider_module.Receipt(request, reply)))
        self.pilot.backend(decision, "namespace", self._write_receipt, reply.receipt_ref, encoded)
        if self.fault == "lost-reply" and request.method in ("PUT", "DELETE"):
            raise TimeoutError("synthetic-result-lost")
        hook=getattr(self.pilot,"after_effect",None)
        if hook is not None and request.method=="DELETE":hook()
        return reply

    def _write_receipt(self, reference, body, *, timeout):
        with closing(existing_db(self.path)) as db:
            db.execute("INSERT INTO receipts VALUES (?,?)", (reference, body))
            value = json.loads(body);request,reply=value["request"],value["reply"]
            db.execute("INSERT INTO operations VALUES (?,?,?,?,?,?)",
                       (request["path"],request["attempt_ref"],request["method"],reference,request["url"],reply["locator"]))
            db.commit()
        return reference

    def _receipt(self, reference, *, timeout, limit=1048576):
        values = self.receipt_batch((reference,), timeout=timeout, limit=limit)
        return values[0]

    def decode_receipt(self, raw):
        value = json.loads(raw)
        request, reply = value["request"], value["reply"]
        request["body"] = base64.b64decode(request["body"]["bytes"])
        request["headers"] = tuple(tuple(x) for x in request["headers"])
        request["claims"] = tuple(tuple(x) for x in request["claims"])
        reply["body"] = base64.b64decode(reply["body"]["bytes"])
        result = provider_module.Receipt(provider_module.Request(**request), provider_module.Reply(**reply))
        return self.receipt_mutation(result) if self.receipt_mutation else result

    def receipt_batch(self, references, *, timeout, limit=1048576):
        overhead = 2 + max(0,len(references)-1)
        with closing(existing_db(self.path)) as db:
            rows = bounded_rows(db,"receipts","ref",references,limit-overhead)
        values = {row[0]:self.decode_receipt(row[3]) for row in rows}
        if set(values) != set(references):
            raise LookupError("synthetic-receipt-batch-missing")
        return tuple(values[reference] for reference in references)

    def read_for(self, principal, reference, *, decision, timeout):
        self.pilot.event(decision, "private", "fence" if reference.startswith("/") else "receipt")
        if reference.startswith("/"):
            state = self.pilot.control_state(decision)
            writer = OWNER_WRITER if state["handed"] else PROVISIONER_WRITER
            now = decision.now()
            admission = provider_fixture.ADMISSION if state["closed"] else "admission:open"
            return provider_module.Fence(self.r.digest, self.r.value["namespace_generation_ref"], reference,
                    writer, (writer,), (), admission, now, now + 60)
        return self.pilot.backend(decision, "namespace", self._receipt, reference)


class PilotProviderClient:
    def __init__(self, pilot, principal, key):
        self.pilot, self.principal, self.key = pilot, principal, key

    def authenticate(self):
        if self.pilot.key_hashes.get(self.principal) != hashlib.sha256(self.key).hexdigest():
            raise PermissionError("synthetic-principal-denied")

    def exchange(self, request, **kwargs):
        self.authenticate()
        return self.pilot.port.exchange_for(self.principal, request, **kwargs)

    def read_many(self, references, *, decision, timeout):
        self.authenticate()
        self.pilot.event(decision, "private", "receipt-batch")
        return self.pilot.backend(decision, "namespace", self.pilot.port.receipt_batch, references)

    def read(self, reference, **kwargs):
        self.authenticate()
        return self.pilot.port.read_for(self.principal, reference, **kwargs)


class PilotJournal:
    def __init__(self, pilot, principal):
        self.pilot, self.principal = pilot, principal

    def _call(self, method, key, raw=None, *, timeout):
        pool = "observation" if self.principal == "observer" else self.pilot.pool
        account = self.pilot.local_accounts[pool]
        limit = account.reply_limit()
        header = audit_size({"max_response_bytes":limit})
        account.request_metadata(header)
        self.pilot.wire_bytes[pool] = self.pilot.wire_bytes.get(pool,0) + header
        self.pilot.events.append((pool,"journal",method))
        args = (key,) if raw is None else (key,raw)
        request_size = audit_size({"arguments":args,"metadata":{}})
        self.pilot.wire_bytes[pool] += request_size
        try:
            if method in ("read","lookup"):
                value = self.pilot.journal.read_limited(method,key,limit=limit,timeout=timeout)
            else:
                if audit_size(Snapshot("9"*160,raw)) > limit:
                    raise ReadLimit(0)
                value = self.pilot.journal.create_only(key,raw,timeout=timeout)
            size = audit_size(value)
            if size > limit:raise ReadLimit(size)
        except ReadLimit as error:
            account.receive(error.observed)
            self.pilot.wire_bytes[pool] += error.observed
            raise
        self.pilot.wire_bytes[pool] += size
        return value

    def read(self, key, *, timeout):
        return self._call("read",key,timeout=timeout)

    def lookup(self, key, *, timeout):
        return self._call("lookup",key,timeout=timeout)

    def create_only(self, key, raw, *, timeout):
        allowed = ("observation-assessment","observation-result") if self.principal == "observer" else ("anchor","run-binding","cleanup-claim")
        if not any(key == r._key(self.pilot.reserved,name) for name in allowed):
            raise PermissionError("synthetic-slot-denied")
        return self._call("create_only",key,raw,timeout=timeout)


class PilotControl:
    """Test service checks an actual selected credential before reading durable state."""
    def __init__(self, pilot, principal, key):
        self.pilot, self.principal, self.key = pilot, principal, key

    def check(self, decision, operation, *, writer=False):
        if self.pilot.key_hashes.get(self.principal) != hashlib.sha256(self.key).hexdigest():
            raise PermissionError("synthetic-credential-denied")
        if writer and self.principal != OWNER_WRITER:
            raise PermissionError("synthetic-mutator-denied")
        self.pilot.event(decision, "private", operation)

    def authorize(self, purpose, registration, reservation_digest, owner, allocation, *, decision, timeout):
        self.check(decision, "authorize")
        pool = "registration" if purpose == "registration-run" else purpose
        if pool == "observation":
            if self.principal != "reader:independent-observer":
                raise PermissionError("synthetic-observer-denied")
        elif self.principal != OWNER_WRITER:
            raise PermissionError("synthetic-owner-denied")
        fixture_require(registration == r._registration_ref(self.pilot.reserved))
        fixture_require(reservation_digest == self.pilot.reserved.digest)
        fixture_require(allocation == "allocation:" + pool + ":" + reservation_digest[7:])
        snapshot = self.pilot.backend(decision, "namespace", self.pilot.state.read, "control")
        state = json.loads(snapshot.raw)
        if purpose in state["pools"]:
            raise PermissionError("synthetic-original-allocation-spent")
        if purpose == "registration-run":
            fixture_require(state["pools"].get("registration") == owner and state["phase"] == "run")
        if pool == "cleanup":
            fixture_require(state["handed"] and state["pools"].get("registration") == owner)
        state["pools"][purpose] = owner
        self.pilot.backend(decision, "namespace", self.pilot.state.replace,
                           "control", canonical(state), etag=snapshot.etag)
        before = self.pilot.reserved.value
        now = decision.now()
        self.pilot.local_accounts[pool] = decision.account
        authority = ("observe:independent" if pool == "observation" else
                     "run-cleanup:actual" if pool == "cleanup" and state["phase"] == "run" else before["setup_authority_ref"])
        return r.Grant(reservation_digest, before["namespace_generation_ref"], before["owner_scope_ref"],
                       before["source_roles_digest"], before["retained_scope_ref"], authority,
                       self.principal, owner, pool, now, min(now + 600, self.pilot.observe_end if pool == "observation" else self.pilot.cleanup_end),
                       "grant:" + uuid.uuid4().hex, self.pilot.cleanup_start, self.pilot.cleanup_end)

    def handoff(self, anchor, *, decision, timeout):
        self.check(decision, "handoff", writer=True)
        fixture_require(self.pilot.backend(decision, "journal", self.pilot.journal.read, r._key(self.pilot.reserved, "anchor")).raw == anchor.raw)
        snapshot = self.pilot.backend(decision, "namespace", self.pilot.state.read, "control")
        state = json.loads(snapshot.raw)
        fixture_require(not state["handed"] and state["pools"]["registration"] == anchor.value["registration_owner_incarnation_ref"])
        state["handed"] = True
        self.pilot.backend(decision, "namespace", self.pilot.state.replace, "control", canonical(state), etag=snapshot.etag)
        self.pilot.port.active_writer = OWNER_WRITER
        return r.Handoff(anchor.digest, anchor.value["registration_owner_incarnation_ref"], OWNER_WRITER,
                         "fence:durable-exclusion", "activation:external")

    def close_write_run(self, registration, claim, *, decision, timeout):
        self.check(decision, "close-write-run", writer=True)
        state = self.pilot.control_state(decision)
        fixture_require(state["handed"] and state["pools"]["cleanup"] == claim.value["owner_incarnation_ref"])
        snapshot = self.pilot.backend(decision, "namespace", self.pilot.state.read, "control")
        state["closed"] = True
        self.pilot.backend(decision, "namespace", self.pilot.state.replace, "control", canonical(state), etag=snapshot.etag)
        return r.Handoff(claim.value["anchor_digest"], claim.value["owner_incarnation_ref"], OWNER_WRITER,
                         "fence:durable-exclusion", "activation:external")

    def phase(self, registration, *, decision, timeout):
        self.check(decision, "phase")
        return self.pilot.control_state(decision)["phase"]

    def run_facts(self, registration, *, decision, timeout):
        self.check(decision, "run-facts")
        facts = self.pilot.backend(decision, "namespace", self.pilot.state.read, "run-facts")
        value = json.loads(facts.raw)
        fixture_require(value["phase"] == "run")
        deployed, linked = base64.b64decode(value["deployed"]), base64.b64decode(value["linked"])
        return r.RunFacts(deployed, linked, selection_module.FinalAuthority(value["observed_at"], value["expires_at"], linked), "run-cleanup:actual")

    def original_creation(self, registration, path, *, decision, timeout):
        self.check(decision, "original-creation")
        value = self.pilot.backend(decision, "namespace", self.pilot.state.read, "creation:" + path)
        value = json.loads(value.raw)
        if value["type"] == "generation":
            return provider_module.Generation(**value["value"])
        if value["type"] == "operation":
            return provider_module.Operation(**value["value"])
        resource = next(x for x in self.pilot.reserved.value["resources"] if x["resource_path"] == path)
        return r.NoSend(self.pilot.reserved.digest, path, resource["create_attempt_ref"], "create", "no-send:" + value["ref"])

    def original_deletion(self, registration, path, attempt, *, decision, timeout):
        self.check(decision, "original-deletion")
        # One independently logged read of the selected controller's immutable send ledger.
        return self.pilot.backend(decision, "namespace", self.pilot.deletion_fact, path, attempt)

    def registered_handles(self, registration, *, decision, timeout):
        self.check(decision, "registered-handles")
        return tuple(self.pilot.control_state(decision)["registered_handles"])

    def issued_handles(self, registration, *, decision, timeout):
        self.check(decision, "issued-handles")
        return tuple(self.pilot.control_state(decision)["issued_handles"])

    def credential_outcome(self, registration, handle, *, decision, timeout):
        self.check(decision, "credential-outcome")
        value = json.loads(self.pilot.backend(decision, "namespace", self.pilot.state.read, "handle:" + handle).raw)
        now = decision.now()
        return r.CredentialOutcome(handle, value["owner"], value["state"], now, now + 60, value["ref"])

    def preservation_scope(self, retained, *, decision, timeout):
        self.check(decision, "preservation-scope")
        value = self.pilot.backend(decision, "namespace", self.pilot.state.read, "preservation-baselines")
        return tuple(r.PreservedTarget(**x) for x in json.loads(value.raw))


class PreservedStore:
    """Test administration of the actual excluded provider/catalog/state objects."""
    def __init__(self, pilot, paths):
        self.pilot, self.paths = pilot, dict(paths)

    def _store(self, slot):
        if slot == "permanent-namespace-catalog":
            return self.pilot.store, INDEX
        if slot == "retained-registration/action-state":
            return self.pilot.journal, INDEX
        if slot == "retained-runtime-authority/replay-state":
            return self.pilot.state, INDEX
        return None, self.paths[slot]

    def get(self, slot, *, limit=1048576):
        store, path = self._store(slot)
        if store is not None:
            value = store.read_limited("lookup",path,limit=limit,timeout=1)
            return None if value is None else value.raw
        with closing(existing_db(self.pilot.port.path)) as db:
            rows = bounded_rows(db,"resources","path",(path,),max(0,(limit-1024)*3//4))
        return None if not rows else rows[0][3]

    def __setitem__(self, slot, body):
        store, path = self._store(slot)
        if store is not None:
            before = store.read(path, timeout=1)
            store.replace(path, body, etag=before.etag, timeout=1)
        else:
            with closing(existing_db(self.pilot.port.path)) as db:
                db.execute("UPDATE resources SET body=? WHERE path=?", (body, path))
                db.commit()

    def pop(self, slot):
        before = self.get(slot)
        store, path = self._store(slot)
        if store is not None:
            store.remove(path)
        else:
            with closing(existing_db(self.pilot.port.path)) as db:
                db.execute("DELETE FROM resources WHERE path=?", (path,))
                db.commit()
        return before


class PilotPreservation:
    def __init__(self, pilot):
        self.pilot = pilot

    def read_arm(self, target, *, decision, timeout):
        self.pilot.event(decision, "arm", "preservation")
        limit = self.limit(decision)
        value = self.current(target,decision,limit=limit)
        size = audit_size({"arguments":(target,), "metadata":{}}) + audit_size(value)
        self.pilot.wire_bytes[decision.account.pool] = self.pilot.wire_bytes.get(decision.account.pool, 0) + size
        return value

    def read_state(self, target, *, decision, timeout):
        self.pilot.event(decision, "namespace", "preservation")
        limit = self.limit(decision)
        value = self.current(target,decision,limit=limit)
        size = audit_size({"arguments":(target,), "metadata":{}}) + audit_size(value)
        self.pilot.wire_bytes[decision.account.pool] = self.pilot.wire_bytes.get(decision.account.pool, 0) + size
        return value

    def limit(self, decision):
        limit = decision.reply_limit()
        header = audit_size({"max_response_bytes":limit})
        decision.account.request_metadata(header)
        pool = decision.account.pool
        self.pilot.wire_bytes[pool] = self.pilot.wire_bytes.get(pool,0) + header
        return limit

    def current(self, target, decision, *, limit=1048576):
        if self.pilot.preserved.paths[target.slot] != target.path:
            raise ValueError("synthetic-preservation-target-mismatch")
        value = self.pilot.preserved.get(target.slot,limit=limit)
        now = decision.now()
        return r.Preservation(target.slot, target.path, value, now, now + 60,
                              "preservation:" + str((r.ARM_SLOTS + r.STATE_SLOTS).index(target.slot)))


class Pilot:
    def __init__(self, root, *, created=True, handles=16, setup_seconds=600, cleanup_seconds=600):
        self.root = root
        self.start = int(time.time())
        self.clock = lambda: int(time.time())
        self.cleanup_start = self.start
        self.cleanup_end = self.start + cleanup_seconds
        self.observe_end = self.start + 900
        value = namespace_fixture.vector()
        value["target"].update(subscription_id=PILOT_SUB, parent_paths=[PILOT_PARENT])
        value["resources"] = pilot_resources()
        value["window"] = {"not_before": self.start - 10, "not_after": self.start + setup_seconds}
        self.reserved = namespace_fixture.reserved(value)
        fixture_require(digest(value["resources"]) == "sha256:1dd8bf9209211e2916e14308baad3ea8dbc6144ce90dbcbbb291c16a8d7ba830")
        self.policies, self.retained = pilot_policies(self.reserved)
        initial = {name: value[name] for name in ("namespace_ref", "namespace_generation_ref", "owner_scope_ref")}
        initial.update(resource_keys=[provider_module.arm_key(x["resource_path"]) for x in value["resources"]], phase="unused")
        self.store = AtomicStore(root / "namespace.db", initial=initial)
        self.journal = AtomicStore(root / "journal.db", initial={"owned": "journal"})
        self.state = AtomicStore(root / "controller.db", initial={"owned": "control"})
        self.keys = {principal: os.urandom(32) for principal in (OWNER_WRITER, PROVISIONER_WRITER, "reader:independent-observer", "worker:runtime")}
        self.key_hashes={name:hashlib.sha256(key).hexdigest() for name,key in self.keys.items()}
        self.events, self.pool, self.wire_bytes = [], "setup-fixture", {}
        self.local_accounts = {}
        state = {"handed": False, "closed": False, "phase": "setup", "pools": {},
                 "registered_handles": ["handle:" + str(i) for i in range(handles)],
                 "issued_handles": ["handle:" + str(i) for i in range(handles)]}
        self.state.create_only("control", canonical(state), timeout=1)
        for handle in state["issued_handles"]:
            self.state.create_only("handle:" + handle, canonical({"owner": value["owner_scope_ref"], "state": "active", "ref": "issuance:" + handle}), timeout=1)
        self.namespace = namespace_fixture.service(self.store, self.reserved)
        self.namespace.reserve(self.reserved, approved=self.reserved.raw, decision=self.decision())
        self.port = PilotPorts(self)
        self.generations = {}
        creator = self.provider(PROVISIONER_WRITER)
        if created:
            for item in value["resources"]:
                if item["kind"] == "os_disk":
                    continue
                operation = creator.create(item["resource_path"], decision=self.decision())
                generation = creator.admit(operation, decision=self.decision())
                self.generations[generation.path] = replace(generation, children=())
                for child in generation.children:
                    self.generations[child.path] = child
        for item in value["resources"]:
            generation = self.generations.get(item["resource_path"])
            original = {"type": "generation", "value": asdict(generation)} if generation else {"type": "no-send", "ref": item["create_attempt_ref"]}
            self.state.create_only("creation:" + item["resource_path"], canonical(original), timeout=1)
        group = "/subscriptions/" + PILOT_SUB + "/resourceGroups/"
        retained_parent = group + "rg-wallet-retained-fixture"
        watchdog_parent = group + "rg-wallet-watchdog-fixture"
        paths = {
            "control-data-disk":self.retained[1], "gate-data-disk":self.retained[2],
            "measured-managed-image":self.retained[0],
            "credential-vault":retained_parent + "/providers/Microsoft.KeyVault/vaults/credentials",
            "redacted-evidence-storage":retained_parent + "/providers/Microsoft.Storage/storageAccounts/evidence",
            "watchdog-function":watchdog_parent + "/providers/Microsoft.Web/sites/watchdog",
            "watchdog-plan":watchdog_parent + "/providers/Microsoft.Web/serverfarms/watchdog",
            "watchdog-storage":watchdog_parent + "/providers/Microsoft.Storage/storageAccounts/watchdog",
            "watchdog-identity":watchdog_parent + "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/watchdog",
            "disposable-parent-RG":PILOT_PARENT, "retained-parent-RG":retained_parent,
            "watchdog-parent-RG":watchdog_parent,
            "permanent-namespace-catalog":"namespace-index:" + value["namespace_ref"],
            "retained-registration/action-state":"retained-journal:original",
            "retained-runtime-authority/replay-state":"retained-control:original"}
        for slot in r.ARM_SLOTS:
            body = canonical({"id":paths[slot], "original_object_id":str(uuid.uuid4()),
                              "content_digest":digest({"retained":slot})})
            with closing(sqlite3.connect(self.port.path)) as db:
                db.execute("INSERT INTO resources VALUES (?,?)", (paths[slot],body))
                db.commit()
        self.preserved = PreservedStore(self, paths)
        targets = [{"slot":slot,"path":path,"baseline_digest":selection_module.byte_digest(self.preserved.get(slot))}
                   for slot,path in paths.items()]
        self.state.create_only("preservation-baselines", canonical(targets), timeout=1)
        self.facade = PilotFacade(self)
        self.facade.exchange = measured_port(self, self.facade.exchange)
        self.actor = r.Reconciler(reserved=self.reserved, provider=self.provider(OWNER_WRITER),
                journal=PilotJournal(self, "owner"), control=self.control(OWNER_WRITER),
                cleanup_deadline=self.cleanup_end, clock=self.clock, facade=self.facade)

    def decision(self):
        from workload_factory_binding_runtime.github_bootstrap.common import Decision
        return Decision(clock=self.clock)

    def provider(self, principal):
        port = PilotProviderClient(self, principal, self.keys[principal])
        for name in ("read", "read_many", "exchange"):
            setattr(port, name, measured_port(self, getattr(port, name)))
        return provider_module.Provider(reserved=self.reserved, namespace=self.namespace, policies=self.policies,
                port=port, receipts=port, fencing=port, writer_ref=OWNER_WRITER if principal == "reader:independent-observer" else principal,
                admission_ref=provider_fixture.ADMISSION, retained_paths=self.retained)

    def control(self, principal):
        client = PilotControl(self, principal, self.keys[principal])
        for name in ("authorize", "handoff", "close_write_run", "phase", "run_facts",
                     "original_creation", "original_deletion", "registered_handles", "issued_handles",
                     "credential_outcome", "preservation_scope"):
            setattr(client, name, measured_port(self, getattr(client, name)))
        return client

    def event(self, decision, group, operation):
        pool = decision.account.pool if hasattr(decision, "account") else self.pool
        self.events.append((pool, group, operation))

    def backend(self, decision, group, function, *args, **kwargs):
        def physical(*values, timeout, **metadata):
            self.event(decision, group, function.__name__)
            pool = decision.account.pool if hasattr(decision,"account") else self.pool
            size = audit_size({"arguments":values,"metadata":metadata})
            self.wire_bytes[pool] = self.wire_bytes.get(pool,0) + size
            limit = decision.reply_limit() if hasattr(decision,"reply_limit") else 1048576
            if hasattr(decision,"account"):
                header = audit_size({"max_response_bytes":limit})
                decision.account.request_metadata(header)
                self.wire_bytes[pool] += header
            owner = getattr(function,"__self__",None)
            try:
                if isinstance(owner,AtomicStore) and function.__name__ in ("read","lookup","read_many"):
                    result = owner.read_limited(function.__name__,values[0],limit=limit,timeout=timeout)
                elif owner is self.port and function.__name__ in ("_receipt","receipt_batch"):
                    result = function(*values,limit=limit,timeout=timeout,**metadata)
                else:
                    result = function(*values,timeout=timeout,**metadata)
                encoded = audit_size(result)
                if encoded > limit:
                    raise ReadLimit(encoded)
            except ReadLimit as error:
                self.wire_bytes[pool] += error.observed
                if hasattr(decision,"account"):decision.account.receive(error.observed)
                raise
            self.wire_bytes[pool] += encoded
            return result
        return decision.backend(group,physical,*args,**kwargs) if hasattr(decision,"backend") else physical(*args,timeout=decision.remaining(),**kwargs)

    def control_state(self, decision):
        return json.loads(self.backend(decision, "namespace", self.state.read, "control").raw)

    def deletion_fact(self, path, attempt, *, timeout):
        with closing(sqlite3.connect(self.port.path)) as db:
            rows = db.execute("SELECT ref,locator FROM operations WHERE path=? AND attempt=? AND method='DELETE' LIMIT 2",
                              (path,attempt)).fetchmany(2)
            if len(rows) > 1:
                raise ValueError("synthetic-multiple-original-deletes")
            if not rows:return None
            reference,locator = rows[0]
            terminal = reference
            if locator:
                row = db.execute("SELECT ref FROM operations WHERE path=? AND attempt=? AND method='GET' AND url=? ORDER BY rowid DESC LIMIT 1",
                                 (path,attempt,locator)).fetchone()
                terminal = None if row is None else row[0]
        return r.Deletion(provider_module.Operation(path,reference),terminal)

    def original_runtime_cleanup(self):
        # Original runtime owns revocation. P07 receives only read-only outcomes.
        state = json.loads(self.state.read("control", timeout=1).raw)
        for handle in state["issued_handles"]:
            key = "handle:" + handle
            before = self.state.read(key, timeout=1)
            value = json.loads(before.raw)
            fixture_require(value["state"] == "active")
            value.update(state="revoked", ref="cleanup:" + handle)
            self.state.replace(key, canonical(value), etag=before.etag, timeout=1)

    def register_actual_run(self):
        values = self.reserved.value
        values.update(phase="provisioned", reservation_digest=self.reserved.digest,
                      provisioning_readback_ref="readback:actual-admitted-set")
        resources = []
        for item in values["resources"]:
            state = self.namespace.read(self.reserved, item["resource_path"], decision=self.decision()).value
            fixture_require(state["state"] == "admitted")
            resources.append({**item, **state["creation"]})
        values["resources"] = resources
        deployed = canonical(values)
        d = selection_module.provisioned(deployed, reserved=self.reserved, authenticated_readback=deployed)
        linked = namespace_fixture.linked(d).value
        now = self.clock()
        linked.update(observed_at=now, expires_at=now + 60)
        raw = canonical(linked)
        final = selection_module.final_link(raw, deployed=d, authority=selection_module.FinalAuthority(now, now + 60, raw))
        before = self.state.read("control", timeout=1)
        state = json.loads(before.raw);state["phase"] = "run"
        self.state.replace("control", canonical(state), etag=before.etag, timeout=1)
        self.state.create_only("run-facts", canonical({"phase": "run", "deployed": base64.b64encode(deployed).decode(),
            "linked": base64.b64encode(final.raw).decode(), "observed_at": now, "expires_at": now + 60}), timeout=1)
        self.pool = "registration"
        return self.actor.register_run()

    def observer(self):
        return r.Observer(reserved=self.reserved, provider=self.provider("reader:independent-observer"),
                journal=PilotJournal(self, "observer"), control=self.control("reader:independent-observer"),
                preservation=PilotPreservation(self), cleanup_deadline=self.cleanup_end,
                observation_deadline=self.observe_end, clock=self.clock, facade=self.facade)

    def register(self):
        self.pool = "registration"
        return self.actor.register()

    def cleanup(self, trigger="trigger:abort"):
        self.pool = "cleanup"
        return self.actor.cleanup(trigger)

    def observe(self):
        self.pool = "observation"
        self.last_observer = self.observer()
        return self.last_observer.observe()

    def profile(self):
        return {"root":str(self.root),"reserved":base64.b64encode(self.reserved.raw).decode(),
                "key_hashes":dict(self.key_hashes),"cleanup_start":self.cleanup_start,
                "cleanup_end":self.cleanup_end,"observe_end":self.observe_end,
                "preserved_paths":self.preserved.paths,
                "files":{name:[(self.root/name).stat().st_dev,(self.root/name).stat().st_ino]
                         for name in ("namespace.db","journal.db","controller.db","provider.db")}}

    @classmethod
    def reopen(cls, profile, *, principal, key):
        self=cls.__new__(cls)
        self.root=Path(profile["root"])
        for name,expected in profile["files"].items():
            actual=(self.root/name).stat()
            if [actual.st_dev,actual.st_ino] != expected:
                raise ValueError("synthetic-retained-store-identity")
        self.reserved=selection_module.reservation(base64.b64decode(profile["reserved"]),
                                    approved=base64.b64decode(profile["reserved"]))
        self.clock=lambda:int(time.time())
        self.cleanup_start,self.cleanup_end,self.observe_end=(profile[name] for name in ("cleanup_start","cleanup_end","observe_end"))
        self.keys,self.key_hashes={principal:key},dict(profile["key_hashes"])
        self.events,self.wire_bytes,self.local_accounts,self.pool=[],{},{}, "observation"
        self.store=AtomicStore(self.root/"namespace.db",initialize=False)
        self.journal=AtomicStore(self.root/"journal.db",initialize=False)
        self.state=AtomicStore(self.root/"controller.db",initialize=False)
        self.namespace=namespace_fixture.service(self.store,self.reserved)
        self.policies,self.retained=pilot_policies(self.reserved)
        self.port=PilotPorts(self,initialize=False)
        self.port.active_writer=OWNER_WRITER
        self.preserved=PreservedStore(self,profile["preserved_paths"])
        self.facade=PilotFacade(self)
        self.facade.exchange=measured_port(self,self.facade.exchange)
        self.actor=None
        return self

    def assert_account(self, account):
        for group in ("private", "arm", "namespace", "journal"):
            physical = sum(pool == account.pool and kind == group for pool, kind, _ in self.events)
            fixture_require(physical == account.counts[group])
        fixture_require(account.bytes_used == self.wire_bytes[account.pool])
        fixture_require(account.bytes_used > 0)
        fixture_require(account.bytes_used <= account.limits[4])
        fixture_require(account.now() < account.deadline)


@pytest.mark.parametrize("created", [False, True], ids=["reservation-only", "all14-created"])
def test_complete_pilot_retirement_uses_real_clocks_and_actual_graph(tmp_path, created):
    pilot = Pilot(tmp_path, created=created)
    assert len(pilot.reserved.value["resources"]) == 14
    assert sum(len(x["dependency_paths"]) for x in pilot.reserved.value["resources"]) == 16
    anchor = pilot.register()
    assert anchor.value["policy_digest"] == "sha256:21b62c2621f3d98e5358c1ba4c5b0345a0237d10cfa52e59bea122487688979e"
    pilot.cleanup()
    pilot.original_runtime_cleanup()
    result = pilot.observe()
    assert result.value["phase"] == "setup"
    assert result.value["outcome"] == "complete"
    assert len(result.raw) <= 16384
    assert {x["state"] for x in result.value["resource_results"]} == ({"absent"} if created else {"not-created"})
    assert len(pilot.port.sends("DELETE")) == (14 if created else 0)
    assert all(pilot.port.body(x["resource_path"]) is None for x in pilot.reserved.value["resources"])
    for account in (pilot.actor._registration.account, pilot.actor._cleanup.account, pilot.last_observer._context.account):
        pilot.assert_account(account)


@pytest.mark.parametrize("change", ["counter-refund", "replace-counter", "bytes-refund", "deadline-renewal", "clock-replacement", "nested-refund"])
def test_callback_cannot_refund_or_replace_the_original_account(change):
    account = Clock().account()
    account.charge("private", size=19)
    def private(*, decision, timeout):
        if change == "counter-refund":
            account._counts["private"] -= 1
        elif change == "replace-counter":
            account._meter["counts"] = dict(account._counts)
            account._counts = account._meter["counts"]
        elif change == "bytes-refund":
            account._meter["bytes"] = 0
        elif change == "deadline-renewal":
            account._deadline += 1
        elif change == "clock-replacement":
            account._clock = lambda: 1000000
        else:
            account.backend("namespace", lambda *, timeout: None)
            account._counts["namespace"] = 0
        return None
    with pytest.raises(BindingError, match=r.ERROR):
        r._io(account, account, "private", private)
    with pytest.raises(BindingError):
        account.charge("arm")


def test_actual_same_deployment_run_registration_and_receipt(tmp_path):
    pilot = Pilot(tmp_path)
    pilot.register()
    initial_counts = pilot.actor._registration.account.counts
    bound = pilot.register_actual_run()
    assert bound.value["run_cleanup_authority_ref"] == "run-cleanup:actual"
    assert pilot.actor._registration.account.counts["private"] > initial_counts["private"]
    assert pilot.actor._registration.account._meter["run_transaction"]
    pilot.cleanup("trigger:run-expiry")
    pilot.original_runtime_cleanup()
    result = pilot.observe()
    assert result.value["phase"] == "run"
    assert result.value["authority_ref"] == "run-cleanup:actual"
    assert result.value["outcome"] == "complete"
    assert len(result.value["resource_results"]) == 14
    assert result.value["provisioned_envelope_digest"] == bound.value["provisioned_envelope_digest"]
    for account in (pilot.actor._registration.account, pilot.actor._cleanup.account, pilot.last_observer._context.account):
        pilot.assert_account(account)


def test_real_setup_expiry_does_not_renew_creation_but_external_cleanup_works(tmp_path):
    pilot = Pilot(tmp_path, setup_seconds=15)
    pilot.register()
    end = pilot.reserved.value["window"]["not_after"]
    while int(time.time()) < end:
        time.sleep(.02)
    count = len(pilot.port.sends("PUT"))
    generation = next(iter(pilot.generations.values()))
    with pytest.raises(BindingError):
        pilot.provider(PROVISIONER_WRITER).retire(generation, attempt_ref="retirement:expired-setup", decision=pilot.decision())
    assert len(pilot.port.sends("PUT")) == count
    assert pilot.port.sends("DELETE") == []
    pilot.cleanup()
    pilot.original_runtime_cleanup()
    assert pilot.observe().value["outcome"] == "complete"


def test_concurrent_duplicate_triggers_share_one_claim_and_no_second_effect(tmp_path):
    pilot = Pilot(tmp_path)
    pilot.register()
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims = list(pool.map(lambda number: pilot.cleanup("trigger:" + str(number)), range(4)))
    assert len({claim.raw for claim in claims}) == 1
    assert len(pilot.port.sends("DELETE")) == 14
    account = pilot.actor._cleanup.account
    before = account.counts
    with pytest.raises(BindingError):
        pilot.cleanup("trigger:fifth")
    assert account.counts == before
    assert len(pilot.port.sends("DELETE")) == 14


@pytest.mark.parametrize("fault", ["before-send", "lost-reply"])
def test_ambiguous_delete_never_replays_and_independent_reader_stays_truthful(tmp_path, fault):
    pilot = Pilot(tmp_path)
    pilot.register()
    pilot.port.fault = fault
    with pytest.raises(BindingError):
        pilot.cleanup()
    pilot.port.fault = None
    before = len(pilot.port.sends("DELETE"))
    with pytest.raises(BindingError):
        pilot.cleanup("trigger:duplicate")
    assert len(pilot.port.sends("DELETE")) == before
    pilot.original_runtime_cleanup()
    result = pilot.observe()
    assert result.value["outcome"] != "complete"
    assert len(result.value["resource_results"]) == 14
    assert len(pilot.port.sends("DELETE")) == before
    assert before == (0 if fault == "before-send" else 1)


@pytest.mark.parametrize("point", ["before", "after"])
def test_lost_cleanup_claim_ack_refuses_mutation_and_is_not_a_second_allocation(tmp_path, point):
    pilot = Pilot(tmp_path)
    pilot.register()
    key = r._key(pilot.reserved, "cleanup-claim")
    pilot.journal.fault = ("create_only", key, point)
    with pytest.raises(BindingError):
        pilot.cleanup()
    pilot.journal.fault = None
    assert pilot.port.sends("DELETE") == []
    assert (pilot.journal.lookup(key, timeout=1) is not None) == (point == "after")
    with pytest.raises(BindingError):
        pilot.cleanup("trigger:no-renewal")
    pilot.original_runtime_cleanup()
    assert pilot.observe().value["outcome"] == "pending"


@pytest.mark.parametrize("slot", r.ARM_SLOTS + r.STATE_SLOTS)
def test_each_actual_preservation_change_prevents_complete(tmp_path, slot):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    pilot.preserved[slot] = canonical({"actual": "changed"})
    if slot == "permanent-namespace-catalog":
        with pytest.raises(BindingError):pilot.observe()
        return
    result = pilot.observe()
    assert result.value["outcome"] == "incomplete"
    assert len(result.value["resource_results"]) == 14
    assert pilot.port.sends("DELETE") == []


@pytest.mark.parametrize("state", ["active", "unknown"])
def test_actual_missing_runtime_credential_cleanup_prevents_complete(tmp_path, state):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    key = "handle:handle:7";before = pilot.state.read(key, timeout=1)
    value = json.loads(before.raw);value["state"] = state
    pilot.state.replace(key, canonical(value), etag=before.etag, timeout=1)
    assert pilot.observe().value["outcome"] == "incomplete"


def test_missing_actual_issued_handle_refuses_instead_of_omitting_it(tmp_path):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    before = pilot.state.read("control", timeout=1);value = json.loads(before.raw)
    value["registered_handles"].pop()
    pilot.state.replace("control", canonical(value), etag=before.etag, timeout=1)
    with pytest.raises(BindingError):pilot.observe()
    assert pilot.journal.lookup(r._key(pilot.reserved, "observation-result"), timeout=1) is None


def test_read_only_observer_and_worker_are_denied_real_write_methods(tmp_path):
    pilot = Pilot(tmp_path, created=False)
    pilot.register()
    resource = pilot.reserved.value["resources"][0]
    request = provider_module.Request("DELETE", provider_module.ARM + resource["resource_path"] + "?api-version=" + provider_fixture.API_VERSIONS[resource["kind"]],
        b"", (), pilot.reserved.digest, resource["resource_path"], resource["kind"], "retirement:forbidden", pilot.clock(), pilot.clock() + 10)
    for principal in ("reader:independent-observer", "worker:runtime", PROVISIONER_WRITER):
        client = PilotProviderClient(pilot, principal, pilot.keys[principal])
        with pytest.raises(PermissionError):
            client.exchange(request, decision=pilot.decision(), timeout=1, before_send=lambda:None)
        healthy = replace(request, method="GET", attempt_ref="observe:healthy")
        assert client.exchange(healthy, decision=pilot.decision(), timeout=1, before_send=lambda:None).status == 404
    assert pilot.port.sends("DELETE") == []


@pytest.mark.parametrize("change", ["truncated", "reordered", "foreign"])
def test_exact_batch_read_never_omits_or_rebinds_namespace_entries(tmp_path, change):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    original = pilot.store.read_many
    def changed(keys, *, timeout):
        rows = original(keys, timeout=timeout)
        if change == "truncated":return rows[:-1]
        if change == "reordered":return tuple(reversed(rows))
        return (replace(rows[0], raw=canonical({"foreign": True})),) + rows[1:]
    pilot.store.read_many = changed
    with pytest.raises(BindingError):pilot.observe()


@pytest.mark.parametrize("termination", [SystemExit, KeyboardInterrupt, GeneratorExit, BaseException])
def test_private_direct_termination_cannot_leak_payload_or_context(tmp_path, termination):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    observer = pilot.observer()
    marker = "PRIVATE-CANARY-token-url-key-body"
    def unavailable(*args, **kwargs):raise termination(marker)
    observer.control.phase = unavailable
    with pytest.raises(BindingError) as caught:observer.observe()
    error = caught.value
    assert marker not in str(error)
    assert error.__cause__ is None
    assert error.__context__ is None
    with closing(sqlite3.connect(pilot.journal.path)) as db:
        assert all(marker.encode() not in row[0] for row in db.execute("SELECT body FROM blobs"))



def test_current_late_observer_reports_failed_without_renewing_cleanup(tmp_path):
    pilot = Pilot(tmp_path, created=False, cleanup_seconds=4)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    original = pilot.actor._cleanup.account
    counts, end, mono = original.counts, original.deadline, original.monotonic_end
    while int(time.time()) < end:
        time.sleep(.02)
    with pytest.raises(BindingError):original.charge("arm")
    result = pilot.observe()
    assert result.value["outcome"] == "failed"
    assert original.counts == counts
    assert original.deadline == end
    assert original.monotonic_end == mono
    assert pilot.port.sends("DELETE") == []


def test_spent_or_expired_observer_cannot_emit_or_acquire_another_pool(tmp_path):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    first = pilot.observe()
    assert first.value["outcome"] == "complete"
    before = pilot.last_observer._context.account.counts
    with pytest.raises(BindingError):pilot.last_observer.observe()
    assert pilot.last_observer._context.account.counts == before
    with pytest.raises(BindingError):pilot.observe()
    assert len(pilot.port.sends("DELETE")) == 0


def test_current_replacement_guid_is_failed_without_a_second_delete(tmp_path):
    pilot = Pilot(tmp_path)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    path = next(iter(pilot.generations))
    pilot.port.put_model(path, mutation=lambda value:value["properties"].update({provider_fixture.OWN_FIELDS[pilot.port.policies[path].kind]:str(uuid.uuid4())}))
    before = len(pilot.port.sends("DELETE"))
    result = pilot.observe()
    assert result.value["outcome"] == "failed"
    assert any(x.get("reason") == "identity-mismatch" for x in result.value["resource_results"])
    assert len(pilot.port.sends("DELETE")) == before


def test_lost_mutation_owner_has_no_transfer_but_original_current_reader_survives(tmp_path):
    pilot = Pilot(tmp_path, created=False)
    pilot.register()
    original = pilot.actor._registration.account
    original.burn()
    replacement = r.Reconciler(reserved=pilot.reserved, provider=pilot.provider(OWNER_WRITER),
            journal=PilotJournal(pilot, "owner"), control=pilot.control(OWNER_WRITER),
            cleanup_deadline=pilot.cleanup_end, clock=pilot.clock, facade=pilot.facade)
    with pytest.raises(BindingError):replacement.register()
    assert replacement.owner != pilot.actor.owner
    assert pilot.port.sends("DELETE") == []
    pilot.original_runtime_cleanup()
    result = pilot.observe()
    assert result.value["outcome"] == "indeterminate"
    assert {x["state"] for x in result.value["resource_results"]} == {"indeterminate"}
    with pytest.raises(BindingError):original.charge("private")


def test_async_original_operations_use_at_most_three_polls_and_reader_never_repolls(tmp_path):
    pilot = Pilot(tmp_path)
    pilot.register()
    pilot.port.async_kind = "vm"
    pilot.cleanup();pilot.original_runtime_cleanup()
    before = list(pilot.port.sends("GET"))
    with closing(sqlite3.connect(pilot.port.path)) as db:
        old = [json.loads(row[0]) for row in db.execute("SELECT body FROM receipts")]
    original_polls = [x for x in old if "/locations/" in x["request"]["url"]]
    assert len(original_polls) == 3
    assert all(x["request"]["method"] == "GET" for x in original_polls)
    result = pilot.observe()
    assert result.value["outcome"] == "complete"
    with closing(sqlite3.connect(pilot.port.path)) as db:
        current = [json.loads(row[0]) for row in db.execute("SELECT body FROM receipts")]
    assert sum("/locations/" in x["request"]["url"] for x in current) == len(original_polls)
    assert len(pilot.port.sends("GET")) == len(before) + 14
    assert len(pilot.port.sends("DELETE")) == 14
    pilot.assert_account(pilot.last_observer._context.account)


from .test_azure_issuance import composed
from .test_hosted_enrollment import enrollment
from .test_hosted_issuance import provider


def test_actual_mtls_issuance_and_original_runtime_retirement_feed_separate_observer(composed, tmp_path):
    c = composed
    peer = c.enrolled()
    assert c.call(c.worker, "/private", c.body).status == 403
    issued = c.call(peer, "/private", c.body)
    assert issued.status == 200
    cap = c.actor.pending(c.p.ref)
    assert c.p.active[cap.credential]
    retired = c.cleanup(cap).retire()
    assert retired["state"] == "retired"
    assert not c.p.active[cap.credential]
    root = tmp_path / "infrastructure";root.mkdir()
    pilot = Pilot(root, created=False, handles=0)
    handle = "handle:actual-runtime"
    before = pilot.state.read("control", timeout=1);state = json.loads(before.raw)
    state.update(registered_handles=[handle], issued_handles=[handle])
    pilot.state.replace("control", canonical(state), etag=before.etag, timeout=1)
    pilot.register();pilot.cleanup()
    observer = pilot.observer()
    def read_original_state(*, timeout):
        with closing(sqlite3.connect((cap.ledger.directory / "issuance.sqlite").as_uri() + "?mode=ro", uri=True)) as db:
            return tuple(db.execute("SELECT state,token_digest FROM attempts WHERE ref=?", (cap.ref,)).fetchone())
    def original_outcome(registration, selected_handle, *, decision, timeout):
        pilot.event(decision, "private", "original-runtime-outcome")
        assert selected_handle == handle
        actual, token_digest = pilot.backend(decision, "namespace", read_original_state)
        assert token_digest == retired["token_digest"]
        return r.CredentialOutcome(handle, pilot.reserved.value["owner_scope_ref"],
            "revoked" if actual == "retired" else "unknown", decision.now(), decision.now() + 60, "runtime-cleanup:actual")
    observer.control.credential_outcome = original_outcome
    before_calls = list(c.p.calls)
    pilot.pool = "observation"
    result = observer.observe()
    assert result.value["outcome"] == "complete"
    assert c.p.calls == before_calls  # P07 observes; no signing/minting/revoking API added.
    assert cap.credential.encode() not in result.raw
    with closing(sqlite3.connect(pilot.journal.path)) as db:
        assert all(cap.credential.encode() not in row[0] for row in db.execute("SELECT body FROM blobs"))


def test_external_owner_survives_three_actual_authenticated_client_process_losses(tmp_path):
    import hmac
    import signal
    import subprocess
    import sys
    import select
    pilot = Pilot(tmp_path)
    anchor = pilot.register()
    owner_pid = os.getpid()
    clients = []
    script = """
import hashlib,hmac,json,sys
config=json.loads(sys.stdin.readline())
for operation in ['read-registration','delete-resource']:
 body=json.dumps({'principal':config['principal'],'operation':operation,'registration':config['registration']},sort_keys=True,separators=(',',':'))
 signature=hmac.new(bytes.fromhex(config['key']),body.encode(),hashlib.sha256).hexdigest()
 print(json.dumps({'body':body,'signature':signature}),flush=True)
 response=json.loads(sys.stdin.readline())
 assert response['status']==(200 if operation=='read-registration' else 403)
print('ready',flush=True)
sys.stdin.readline()
"""
    try:
        for role in ("control", "gate", "worker"):
            principal = "runtime:" + role
            key = os.urandom(32)
            pilot.keys[principal] = key
            pilot.key_hashes[principal] = hashlib.sha256(key).hexdigest()
            process = subprocess.Popen([sys.executable, "-I", "-B", "-c", script], stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, close_fds=True)
            clients.append(process)
            config = {"principal":principal,"key":key.hex(),"registration":r._registration_ref(pilot.reserved)}
            process.stdin.write(json.dumps(config) + "\n");process.stdin.flush()
            for operation in ("read-registration", "delete-resource"):
                assert select.select([process.stdout], [], [], 5)[0]
                packet = json.loads(process.stdout.readline())
                assert hmac.compare_digest(packet["signature"], hmac.new(key,packet["body"].encode(),hashlib.sha256).hexdigest())
                request = json.loads(packet["body"])
                assert request == {"principal":principal,"operation":operation,"registration":config["registration"]}
                client = PilotProviderClient(pilot, principal, key)
                resource = next(x for x in pilot.reserved.value["resources"] if x["kind"] == "vm")
                request = provider_module.Request("GET" if operation == "read-registration" else "DELETE",
                    provider_module.ARM + resource["resource_path"] + "?api-version=2025-04-01",
                    b"", (), pilot.reserved.digest, resource["resource_path"], "vm",
                    "client:health-or-denial", pilot.clock(), pilot.clock() + 10)
                try:
                    reply = client.exchange(request, decision=pilot.decision(), timeout=1, before_send=lambda:None)
                    status = reply.status
                except PermissionError:
                    status = 403
                if operation == "read-registration":
                    assert status == 200
                    pilot.state.create_only("runtime-client:" + role, canonical({
                        "pid":process.pid,"principal":principal,"health_readback_ref":reply.receipt_ref}), timeout=1)
                else:
                    assert status == 403
                process.stdin.write(json.dumps({"status":status}) + "\n");process.stdin.flush()
            assert select.select([process.stdout], [], [], 5)[0]
            assert process.stdout.readline().strip() == "ready"
        assert len({p.pid for p in clients}) == 3
        for process in clients:
            process.kill()
            assert process.wait(timeout=5) == -signal.SIGKILL
            assert not Path("/proc", str(process.pid)).exists()
        assert os.getpid() == owner_pid
        pilot.cleanup("trigger:control-loss");pilot.original_runtime_cleanup()
        observed=fresh_process_observation(pilot)
        assert observed["pid"] != owner_pid
        assert observed["receipt"]["outcome"] == "complete"
        assert len(pilot.port.sends("DELETE")) == 14
    finally:
        for process in clients:
            if process.poll() is None:
                process.kill();process.wait(timeout=5)
            process.stdin.close();process.stdout.close();process.stderr.close()


def test_original_read_only_receipt_batch_rejects_truncation_before_cache_use(tmp_path):
    pilot = Pilot(tmp_path)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    original = pilot.port.receipt_batch
    def truncated(references, *, timeout):return original(references, timeout=timeout)[:-1]
    pilot.port.receipt_batch = truncated
    with pytest.raises(BindingError):pilot.observe()
    assert pilot.journal.lookup(r._key(pilot.reserved, "observation-result"), timeout=1) is None


def test_original_delete_poll_bound_is_not_restarted_by_another_trigger(tmp_path):
    pilot = Pilot(tmp_path)
    pilot.register();pilot.port.async_kind = "vm";pilot.port.status = "Running"
    with pytest.raises(BindingError):pilot.cleanup()
    with closing(sqlite3.connect(pilot.port.path)) as db:
        values = [json.loads(row[0]) for row in db.execute("SELECT body FROM receipts")]
    assert sum("/locations/" in x["request"]["url"] for x in values) == 3
    sends = len(pilot.port.sends("GET"))
    assert pilot.cleanup("trigger:again").raw == pilot.actor._claim.raw
    assert len(pilot.port.sends("GET")) == sends
    assert len(pilot.port.sends("DELETE")) == 1
    pilot.original_runtime_cleanup()
    assert pilot.observe().value["outcome"] == "pending"



def test_mutator_principal_cannot_be_relabelled_as_the_independent_observer(tmp_path):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    observer = pilot.observer()
    original = observer.control.authorize
    def relabel(*args, **kwargs):return replace(original(*args, **kwargs), subject_ref=OWNER_WRITER)
    observer.control.authorize = relabel
    with pytest.raises(BindingError):observer.observe()
    assert pilot.journal.lookup(r._key(pilot.reserved, "observation-result"), timeout=1) is None
    assert pilot.port.sends("DELETE") == []



def test_failed_handoff_cannot_become_registration_success_on_retry(tmp_path):
    pilot = Pilot(tmp_path, created=False)
    called = []
    def invalid(anchor, *, decision, timeout):
        called.append(True)
        return r.Handoff("sha256:" + "0" * 64, pilot.actor.owner, OWNER_WRITER,
                         "fence:wrong", "activation:wrong")
    pilot.actor.control.handoff = invalid
    for call in (pilot.register, pilot.register, pilot.cleanup, pilot.actor.register_run):
        with pytest.raises(BindingError):call()
    assert called == [True]
    state = json.loads(pilot.state.read("control", timeout=1).raw)
    assert not state["handed"]
    assert "cleanup" not in state["pools"]
    assert pilot.port.sends("DELETE") == []


def test_frozen_delete_request_expiry_is_checked_at_the_actual_send(admitted):
    reserved, _, _, port, original, generation = admitted
    clock = Clock();clock.wall = reserved.value["window"]["not_after"] + 1
    selected = context(reserved, clock)
    original_read = port.read
    def short_fence(reference, **kwargs):
        value = original_read(reference, **kwargs)
        return replace(value, expires_at=clock.wall + 1) if type(value) is provider_module.Fence else value
    port.read = short_fence
    def cross_frozen_end(request):
        if request.method == "DELETE":
            clock.wall += 2;clock.mono += 2
    port.before_send = cross_frozen_end
    service = original.cleanup_view(selected)
    with pytest.raises(BindingError):
        service.retire(generation, attempt_ref="retirement:expired-wire", decision=selected)
    assert port.sends("DELETE") == []
    with pytest.raises(BindingError):
        service.retire(generation, attempt_ref="retirement:no-second-send", decision=selected)
    assert port.sends("DELETE") == []


@pytest.mark.parametrize("termination", [SystemExit, KeyboardInterrupt, GeneratorExit])
@pytest.mark.parametrize("clock_kind", ["wall", "monotonic"])
def test_private_clock_termination_is_closed_without_payload_or_context(termination, clock_kind):
    marker = "PRIVATE-CLOCK-CANARY"
    def unavailable():raise termination(marker)
    with pytest.raises(BindingError) as caught:
        r._Account("cleanup", owner="owner:original", deadline=2000000,
                   clock=unavailable if clock_kind == "wall" else lambda:1000000,
                   monotonic=unavailable if clock_kind == "monotonic" else lambda:100.)
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert marker not in str(caught.value)


def test_expired_supporting_assessment_cannot_become_current_complete_receipt(tmp_path):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    observer = pilot.observer()
    wall = pilot.clock()
    clock = Clock();clock.wall = wall
    observer.clock = lambda:clock.wall
    observer.monotonic = lambda:clock.mono
    original = observer.preservation.current
    def short(target, decision, **kwargs):return replace(original(target, decision, **kwargs), expires_at=decision.now() + 1)
    observer.preservation.current = short
    original_registered = observer.control.registered_handles
    def later(*args, **kwargs):
        clock.wall += 2;clock.mono += 2
        return original_registered(*args, **kwargs)
    observer.control.registered_handles = later
    with pytest.raises(BindingError):observer.observe()
    assert pilot.journal.lookup(r._key(pilot.reserved, "observation-result"), timeout=1) is None


def test_authenticated_current_missing_preservation_is_incomplete_not_success(tmp_path):
    pilot = Pilot(tmp_path, created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    pilot.preserved.pop("watchdog-storage")
    result = pilot.observe()
    assert result.value["outcome"] == "incomplete"
    assessment = json.loads(pilot.journal.read(r._key(pilot.reserved, "observation-assessment"), timeout=1).raw)
    missing = next(x for x in assessment["preservation"] if x["slot"] == "watchdog-storage")
    assert missing["state"] == "unavailable"
    assert "current_digest" not in missing


@pytest.mark.parametrize("point", ["before", "after"])
def test_independent_observer_requires_actual_terminal_tombstone_not_write_ack(tmp_path, point):
    pilot = Pilot(tmp_path)
    pilot.register()
    target = [x for x in pilot.reserved.value["resources"] if x["kind"] == "nsg"][-1]["resource_path"]
    key = provider_module.arm_key(target)
    original = pilot.store.replace
    def boundary(selected, raw, **kwargs):
        if selected == key and json.loads(raw)["state"] == "absent-tombstoned":
            pilot.store.fault = ("replace", selected, point)
        return original(selected, raw, **kwargs)
    pilot.store.replace = boundary
    with pytest.raises(BindingError):pilot.cleanup()
    pilot.store.fault = None
    pilot.original_runtime_cleanup()
    result = pilot.observe()
    assert result.value["outcome"] == ("pending" if point == "before" else "complete")
    actual = pilot.store.read(key, timeout=1)
    assert json.loads(actual.raw)["state"] == ("retiring" if point == "before" else "absent-tombstoned")
    assert len(pilot.port.sends("DELETE")) == 14



@pytest.mark.parametrize("pool", ["registration", "cleanup"])
def test_failed_original_authorization_retains_one_account_and_never_reacquires(tmp_path, pool):
    pilot = Pilot(tmp_path, created=False)
    if pool == "cleanup":pilot.register()
    original = pilot.actor.control.authorize
    attempts = []
    def invalid(*args, **kwargs):
        attempts.append(kwargs["decision"])
        return replace(original(*args, **kwargs), subject_ref="writer:foreign")
    pilot.actor.control.authorize = invalid
    method = pilot.register if pool == "registration" else pilot.cleanup
    for _ in range(3):
        with pytest.raises(BindingError):method()
    assert len(attempts) == 1
    assert pilot.actor._accounts[pool] is attempts[0]
    assert attempts[0].counts["private"] == 1
    assert pilot.port.sends("DELETE") == []


def test_approved_future_cleanup_start_refuses_before_claim_or_admission(tmp_path):
    pilot = Pilot(tmp_path)
    pilot.register()
    original = pilot.actor.control.authorize
    def future(purpose, *args, **kwargs):
        grant = original(purpose, *args, **kwargs)
        return replace(grant, cleanup_not_before=kwargs["decision"].now() + 60) if purpose == "cleanup" else grant
    pilot.actor.control.authorize = future
    with pytest.raises(BindingError):pilot.cleanup()
    assert pilot.journal.lookup(r._key(pilot.reserved, "cleanup-claim"), timeout=1) is None
    assert not json.loads(pilot.state.read("control", timeout=1).raw)["closed"]
    assert pilot.port.sends("DELETE") == []


@pytest.mark.parametrize("status", [403, 500])
def test_original_async_delete_error_cannot_become_success_from_a_locator(tmp_path, status):
    pilot = Pilot(tmp_path)
    pilot.register();pilot.port.async_kind = "vm";pilot.cleanup();pilot.original_runtime_cleanup()
    def invalid(receipt):
        if receipt.request.method == "DELETE" and receipt.reply.locator:
            return replace(receipt, reply=replace(receipt.reply, status=status))
        return receipt
    pilot.port.receipt_mutation = invalid
    with pytest.raises(BindingError):pilot.observe()
    assert pilot.journal.lookup(r._key(pilot.reserved, "observation-result"), timeout=1) is None



def test_nested_failure_burn_cannot_be_erased_by_its_enclosing_callback():
    account = Clock().account()
    def failed(*, timeout):raise TimeoutError("private-backend-failure")
    def enclosing(*, decision, timeout):
        with pytest.raises(BindingError):account.backend("namespace", failed)
        account._meter["burned"] = False
        return None
    with pytest.raises(BindingError):r._io(account, account, "private", enclosing)
    with pytest.raises(BindingError):account.charge("arm")


@pytest.mark.parametrize("field", ["_last_wall", "_last_mono"])
def test_invalid_clock_history_is_sanitized_and_terminal(field):
    state = Clock()
    account = state.account()
    original = account._clock
    def corrupt():
        setattr(account, field, None)
        return state.wall
    account._clock = corrupt
    with pytest.raises(BindingError) as caught:account.now()
    assert caught.value.__context__ is None
    account._clock = original
    account._last_wall, account._last_mono = state.wall, state.mono
    with pytest.raises(BindingError):account.charge("arm")



@pytest.mark.parametrize("change", ["http-error","foreign-operation","extra-field","locator"])
def test_each_pending_poll_must_authenticate_the_original_operation_before_retry(tmp_path, change):
    pilot = Pilot(tmp_path)
    pilot.register();pilot.port.async_kind="vm";pilot.port.status="Running"
    def changed(request,reply):
        if "/locations/" not in request.url:return reply
        body=json.loads(reply.body)
        if change=="http-error":return replace(reply,status=500)
        if change=="foreign-operation":body["name"]="op-foreign"
        elif change=="extra-field":body["unapproved"]=True
        else:return replace(reply,locator=request.url)
        return replace(reply,body=canonical(body))
    pilot.port.reply_mutation=changed
    with pytest.raises(BindingError):pilot.cleanup()
    with closing(sqlite3.connect(pilot.port.path)) as db:
        values=[json.loads(row[0]) for row in db.execute("SELECT body FROM receipts")]
    assert sum("/locations/" in x["request"]["url"] for x in values)==1
    assert len(pilot.port.sends("DELETE"))==1


def test_unrelated_large_receipt_archive_cannot_increase_original_operation_reads(tmp_path):
    pilot = Pilot(tmp_path)
    pilot.register()
    with closing(sqlite3.connect(pilot.port.path)) as db:
        for number in range(20):
            db.execute("INSERT INTO receipts VALUES (?,?)",("unrelated:"+str(number),canonical({"unrelated":"x"*65536})))
        db.commit()
    pilot.cleanup();pilot.original_runtime_cleanup()
    result=pilot.observe()
    assert result.value["outcome"]=="complete"
    pilot.assert_account(pilot.actor._cleanup.account)
    pilot.assert_account(pilot.last_observer._context.account)


def test_physical_namespace_oversize_is_bounded_and_cannot_satisfy_refusal_by_fixture_error(tmp_path):
    pilot=Pilot(tmp_path,created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    key=provider_module.arm_key(pilot.reserved.value["resources"][0]["resource_path"])
    pilot.store.corrupt(key,b"x"*1048577)
    with pytest.raises(BindingError):pilot.observe()
    assert pilot.journal.lookup(r._key(pilot.reserved,"observation-result"),timeout=1) is None



def fresh_process_observation(pilot):
    import subprocess
    import sys
    root=Path(__file__).resolve().parents[2]
    script="""
from pathlib import Path
import sys,json,os
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'scripts'),str(root/'tests')]
from runtime_binding.test_azure_retirement import Pilot
packet=json.loads(sys.stdin.read())
pilot=Pilot.reopen(packet['profile'],principal='reader:independent-observer',key=bytes.fromhex(packet['key']))
result=pilot.observe()
pilot.assert_account(pilot.last_observer._context.account)
print(json.dumps({'pid':os.getpid(),'receipt':result.value,'counts':pilot.last_observer._context.account.counts}))
"""
    packet={"profile":pilot.profile(),"key":pilot.keys["reader:independent-observer"].hex()}
    result=subprocess.run([sys.executable,"-I","-B","-c",script,str(root)],input=json.dumps(packet),
                          capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr[-2000:]
    return json.loads(result.stdout)


@pytest.mark.parametrize("checkpoint",["after-claim","after-effect-before-ack"])
def test_actual_mutation_owner_process_loss_cannot_transfer_and_fresh_reader_is_truthful(tmp_path, checkpoint):
    import select
    import signal
    import subprocess
    import sys
    pilot=Pilot(tmp_path)
    profile=pilot.profile()
    script="""
from pathlib import Path
import sys,json,os
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'scripts'),str(root/'tests')]
from runtime_binding.test_azure_retirement import Pilot,PilotJournal,OWNER_WRITER,r
packet=json.loads(sys.stdin.readline())
pilot=Pilot.reopen(packet['profile'],principal=OWNER_WRITER,key=bytes.fromhex(packet['key']))
pilot.pool='registration'
pilot.actor=r.Reconciler(reserved=pilot.reserved,provider=pilot.provider(OWNER_WRITER),
 journal=PilotJournal(pilot,'owner'),control=pilot.control(OWNER_WRITER),cleanup_deadline=pilot.cleanup_end,
 clock=pilot.clock,facade=pilot.facade)
pilot.register()
def checkpoint():
 print('checkpoint-ready',flush=True);sys.stdin.readline()
if packet['checkpoint']=='after-claim':
 original=pilot.actor.control.original_creation
 def pause(*args,**kwargs):
  checkpoint();return original(*args,**kwargs)
 pilot.actor.control.original_creation=pause
else:pilot.after_effect=checkpoint
pilot.cleanup()
"""
    packet={"profile":profile,"key":pilot.keys[OWNER_WRITER].hex(),"checkpoint":checkpoint}
    process=subprocess.Popen([sys.executable,"-I","-B","-c",script,str(Path(__file__).resolve().parents[2])],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,close_fds=True)
    try:
        process.stdin.write(json.dumps(packet)+chr(10));process.stdin.flush()
        assert select.select([process.stdout],[],[],20)[0]
        assert process.stdout.readline().strip()=="checkpoint-ready"
        claim=pilot.journal.read(r._key(pilot.reserved,"cleanup-claim"),timeout=1)
        original_owner=json.loads(claim.raw)["owner_incarnation_ref"]
        process.kill()
        assert process.wait(timeout=5)==-signal.SIGKILL
        assert not Path("/proc",str(process.pid)).exists()
        assert pilot.actor.owner != original_owner
        with pytest.raises(BindingError):pilot.register()
        before=len(pilot.port.sends("DELETE"))
        pilot.original_runtime_cleanup()
        observed=fresh_process_observation(pilot)
        assert observed["pid"] != process.pid
        assert observed["receipt"]["outcome"]=="pending"
        assert len(observed["receipt"]["resource_results"])==14
        assert len(pilot.port.sends("DELETE"))==before
        assert before==(0 if checkpoint=="after-claim" else 1)
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=5)
        process.stdin.close();process.stdout.close();process.stderr.close()



@pytest.mark.parametrize("limit",[64,1024])
def test_bounded_reader_rejects_oversize_metadata_before_any_blob_materialization(limit):
    class Tracked(sqlite3.Connection):
        opened=0
        def blobopen(self,*args,**kwargs):
            self.opened+=1
            return super().blobopen(*args,**kwargs)
    with closing(sqlite3.connect(":memory:",factory=Tracked)) as db:
        db.execute("CREATE TABLE receipts(ref TEXT PRIMARY KEY,body BLOB)")
        for number in range(8):
            db.execute("INSERT INTO receipts VALUES (?,?)",("large:"+str(number),b"x"*262144))
        db.commit()
        with pytest.raises(ReadLimit):
            bounded_rows(db,"receipts","ref",tuple("large:"+str(n) for n in range(8)),limit)
        assert db.opened==0
        db.rollback()
        rows=bounded_rows(db,"receipts","ref",("large:0",),262144)
        assert len(rows)==1
        assert len(rows[0][3])==262144
        assert db.opened==1



@pytest.mark.parametrize("name",["namespace.db","journal.db","controller.db","provider.db"])
def test_missing_selected_retained_service_state_is_never_reinitialized(tmp_path,name):
    pilot=Pilot(tmp_path,created=False)
    pilot.register();pilot.cleanup();pilot.original_runtime_cleanup()
    selected=tmp_path/name
    selected.unlink()
    with pytest.raises(BindingError):pilot.observe()
    assert not selected.exists()
