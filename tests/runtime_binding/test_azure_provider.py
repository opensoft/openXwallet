"""Isolated P03 authenticated-port and durable SQLite journal controls; no Azure I/O."""
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict, replace
import copy
import json
import os
from pathlib import Path
import select
import signal
import socket
import sqlite3
import time
import uuid

import pytest
from workload_factory_binding.evidence import BindingError, canonical, digest
from workload_factory_binding_runtime.azure_composition import provider as p
from workload_factory_binding_runtime.hosted.readback import ReadBudget
from . import test_azure_namespace as n

NOW = n.NOW
IMAGE = n.PARENT + "/providers/Microsoft.Compute/images/measured"
IDENTITIES = {kind: str(uuid.UUID(int=i + 1)) for i, kind in enumerate(n.PATHS)}
WRITER, ADMISSION = "writer:sole", "admission:closed"

# Independent literal provider oracle; never derive these from the product tables.
OWN_FIELDS = {"vm": "vmId", "os_disk": "uniqueId", "nic": "resourceGuid",
    "public_ip": "resourceGuid", "vnet": "resourceGuid", "nsg": "resourceGuid"}
API_VERSIONS = {"vm": "2025-04-01", "os_disk": "2025-01-02", "nic": "2026-01-01",
    "public_ip": "2026-01-01", "vnet": "2026-01-01", "nsg": "2026-01-01"}
RESOURCE_TYPES = {"vm": "Microsoft.Compute/virtualMachines", "os_disk": "Microsoft.Compute/disks",
    "nic": "Microsoft.Network/networkInterfaces", "public_ip": "Microsoft.Network/publicIPAddresses",
    "vnet": "Microsoft.Network/virtualNetworks", "nsg": "Microsoft.Network/networkSecurityGroups"}



def projections():
    vm = {"storageProfile": {"imageReference": {"id": IMAGE},
        "osDisk": {"name": n.PATHS["os_disk"].split("/")[-1], "createOption": "FromImage",
                   "deleteOption": "Detach", "managedDisk": {"id": n.PATHS["os_disk"]}},
        "dataDisks": []},
        "networkProfile": {"networkInterfaces": [{"id": n.PATHS["nic"],
            "properties": {"primary": True, "deleteOption": "Detach"}}]}}
    config = {"name": "ip", "properties": {"subnet": {"id": n.PATHS["vnet"] + "/subnets/pilot"},
        "privateIPAddress": "10.0.0.4", "publicIPAddress": {"id": n.PATHS["public_ip"],
        "properties": {"deleteOption": "Detach"}}}}
    live = {"vm": vm, "os_disk": {"diskState": "Attached", "managedBy": n.PATHS["vm"]},
        "nic": {"virtualMachine": {"id": n.PATHS["vm"]}, "enableIPForwarding": False,
                "ipConfigurations": [config]},
        "public_ip": {"ipConfiguration": {"id": n.PATHS["nic"] + "/ipConfigurations/ip"}},
        "vnet": {"subnets": [{"id": n.PATHS["vnet"] + "/subnets/pilot",
            "properties": {"ipConfigurations": [{"id": n.PATHS["nic"] + "/ipConfigurations/ip"}],
                           "delegations": []}}], "virtualNetworkPeerings": []},
        "nsg": {"networkInterfaces": [{"id": n.PATHS["nic"]}],
                "subnets": [{"id": n.PATHS["vnet"] + "/subnets/pilot"}], "securityRules": []}}
    detached = copy.deepcopy(live)
    detached["os_disk"] = {"diskState": "Unattached"}
    detached["nic"].pop("virtualMachine")
    detached["public_ip"] = {}
    detached["vnet"]["subnets"][0]["properties"]["ipConfigurations"] = []
    detached["nsg"].update(networkInterfaces=[], subnets=[])
    return live, detached


def policies(r):
    live, detached = projections()
    result = []
    for resource in r.value["resources"]:
        kind = resource["kind"]
        props = copy.deepcopy(live[kind])
        if kind == "os_disk":
            props = {"creationData": {"createOption": "Empty"}, "diskSizeGB": 64}
        props.pop("virtualMachine", None)
        result.append(p.Policy(resource["resource_path"], kind, resource["resource_policy_ref"],
            canonical({"location": "westus", "properties": props}),
            canonical(live[kind]), canonical(detached[kind])))
    return tuple(result)


class Ports:
    """Test-only durable provider/receipt double with explicit caller deadlines."""
    def __init__(self, path, r, policies, *, initialize=False):
        self.path, self.r, self.policies = path, r, {x.path: x for x in policies}
        self.writers, self.outstanding, self.admission = (WRITER,), (), ADMISSION
        self.before_send = self.after_read = None
        self.fault = self.async_kind = None
        self.status = "Succeeded"
        self.reply_mutation = self.receipt_mutation = None
        self.decisions = []
        if initialize:
            path.touch(mode=0o600, exist_ok=False)
            with closing(sqlite3.connect(path)) as db:
                db.executescript("CREATE TABLE resources(path TEXT PRIMARY KEY,body BLOB);"
                    "CREATE TABLE receipts(ref TEXT PRIMARY KEY,body BLOB);"
                    "CREATE TABLE sends(n INTEGER PRIMARY KEY,method TEXT,path TEXT);")
                db.commit()

    def put_model(self, path, *, detached=False, mutation=None):
        policy = self.policies[path]
        props = json.loads(policy.detached if detached else policy.present)
        root = {k: props.pop(k) for k in ("managedBy", "managedByExtended") if k in props}
        value = {"id": path, "type": RESOURCE_TYPES[policy.kind],
                 "location": "westus", "properties": {"provisioningState": "Succeeded",
                 OWN_FIELDS[policy.kind]: IDENTITIES[policy.kind], **props}, **root}
        if mutation:
            mutation(value)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT OR REPLACE INTO resources VALUES (?,?)", (path, canonical(value)))
            db.commit()
        return value

    def body(self, path):
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute("SELECT body FROM resources WHERE path=?", (path,)).fetchone()
        return None if row is None else row[0]

    def sends(self, method):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT path FROM sends WHERE method=? ORDER BY n", (method,)).fetchall()

    def check(self, decision, timeout):
        assert 0 < timeout <= decision.remaining()
        self.decisions.append(decision)

    def exchange(self, request, *, decision, timeout, before_send):
        self.check(decision, timeout)
        if self.before_send:
            self.before_send(request)
        before_send()
        if self.fault == "before-send":
            raise TimeoutError("private-before")
        if self.fault == "process-before":
            os._exit(23)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO sends(method,path) VALUES (?,?)", (request.method, request.path))
            db.commit()
        body, status, identity_ref, locator = self._respond(request)
        reply = p.Reply(status, body, "receipt:" + uuid.uuid4().hex, identity_ref, locator)
        if self.reply_mutation:
            reply = self.reply_mutation(request, reply)
        raw_request, raw_reply = asdict(request), asdict(reply)
        raw_request["body"] = base64.b64encode(request.body).decode()
        raw_reply["body"] = base64.b64encode(reply.body).decode()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO receipts VALUES (?,?)", (reply.receipt_ref,
                canonical({"request": raw_request, "reply": raw_reply})))
            db.commit()
        if self.fault == "process-after":
            os._exit(23)
        if self.fault == "lost-reply" and request.method in ("PUT", "DELETE"):
            raise TimeoutError("private-result-lost")
        if self.after_read and request.method == "GET":
            self.after_read(request)
        return reply

    def _respond(self, request):
        policy = self.policies[request.path]
        assert request.url.endswith("?api-version=" + API_VERSIONS[policy.kind])
        locator = None
        identity_ref = "incarnation:" + policy.kind
        if "/locations/" in request.url:
            body, status, identity_ref = canonical({"status": self.status, "name": "op-1"}), 200, None
        elif request.method == "PUT":
            for path, _ in request.claims:
                self.put_model(path)
            body, status = self.body(request.path), 201
            if self.async_kind == policy.kind:
                locator = (p.ARM + "/subscriptions/" + n.SUB + "/providers/" +
                    RESOURCE_TYPES[policy.kind].split("/")[0] + "/locations/westus/operations/op-1?api-version=" +
                    API_VERSIONS[policy.kind])
                body, status, identity_ref = canonical({"properties": {"provisioningState": "Creating"}}), 202, None
        elif request.method == "DELETE":
            with closing(sqlite3.connect(self.path)) as db:
                db.execute("DELETE FROM resources WHERE path=?", (request.path,))
                db.commit()
            body, status, identity_ref = b"", 204, None
            if self.async_kind == policy.kind:
                locator = (p.ARM + "/subscriptions/" + n.SUB + "/providers/" +
                    RESOURCE_TYPES[policy.kind].split("/")[0] + "/locations/westus/operations/op-1?api-version=" +
                    API_VERSIONS[policy.kind])
                body, status = canonical({}), 202
        else:
            body = self.body(request.path)
            status = 404 if body is None else 200
            body = canonical({}) if body is None else body
            if status == 404:
                identity_ref = None
        return body, status, identity_ref, locator

    def read(self, reference, *, decision, timeout):
        self.check(decision, timeout)
        # Same object implements two independently selected ports in this fixture.
        if reference.startswith("/"):
            return p.Fence(self.r.digest, self.r.value["namespace_generation_ref"], reference,
                WRITER, self.writers, self.outstanding, self.admission, decision.now(), decision.now() + 60)
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute("SELECT body FROM receipts WHERE ref=?", (reference,)).fetchone()
        if row is None:
            raise LookupError("private-missing-receipt")
        value = json.loads(row[0])
        request, reply = value["request"], value["reply"]
        request["body"] = base64.b64decode(request["body"])
        request["headers"] = tuple(tuple(x) for x in request["headers"])
        request["claims"] = tuple(tuple(x) for x in request["claims"])
        reply["body"] = base64.b64decode(reply["body"])
        result = p.Receipt(p.Request(**request), p.Reply(**reply))
        return self.receipt_mutation(result) if self.receipt_mutation else result


@pytest.fixture
def fx(tmp_path):
    r = n.reserved()
    value = r.value
    store = n.Store(tmp_path / "namespace.db", initialize=True, initial={
        "namespace_ref": value["namespace_ref"], "namespace_generation_ref": value["namespace_generation_ref"],
        "owner_scope_ref": value["owner_scope_ref"],
        "resource_keys": [p.arm_key(x["resource_path"]) for x in value["resources"]], "phase": "unused"})
    ns = n.service(store, r)
    ps = policies(r)
    port = Ports(tmp_path / "provider.db", r, ps, initialize=True)
    ns.reserve(r, approved=r.raw, decision=n.decision())
    def service():
        return p.Provider(reserved=r, namespace=ns, policies=ps, port=port, receipts=port,
            fencing=port, writer_ref=WRITER, admission_ref=ADMISSION, retained_paths=(IMAGE,))
    return r, ns, store, ps, port, service


def refused(function, *args, **kwargs):
    with pytest.raises(BindingError) as error:
        function(*args, **kwargs)
    assert str(error.value) == p.ERROR
    assert error.value.__cause__ is None


@pytest.mark.parametrize("kind", list(n.PATHS))
def test_documented_kind_positive_has_own_identity_and_original_decision(fx, kind):
    _, _, _, _, port, make = fx
    port.put_model(n.PATHS[kind])
    decision = n.decision()
    reply, identity = make().observe(n.PATHS[kind], decision=decision)
    assert identity == IDENTITIES[kind]
    assert reply.identity_ref == "incarnation:" + kind
    assert all(x is decision for x in port.decisions)
    assert len(port.sends("GET")) == 1
    assert ReadBudget(decision).count("arm") == 1


@pytest.mark.parametrize("kind", list(n.PATHS))
@pytest.mark.parametrize("field", ["id", "type", "location", "missing-identity", "identity-type",
    "state", "missing-policy", "foreign-policy", "extra-policy", "nextLink"])
def test_each_kind_single_provider_fact_mutation_refuses(fx, kind, field):
    _, _, _, _, port, make = fx
    def mutate(v):
        if field == "id":
            v["id"] += "-other"
        elif field == "type":
            v["type"] = "Microsoft.Network/wrong"
        elif field == "location":
            v["location"] = "other"
        elif field == "missing-identity":
            del v["properties"][OWN_FIELDS[kind]]
        elif field == "identity-type":
            v["properties"][OWN_FIELDS[kind]] = 7
        elif field == "state":
            v["properties"]["provisioningState"] = "Updating"
        elif field == "missing-policy":
            v["properties"].pop(next(k for k in v["properties"] if k not in (OWN_FIELDS[kind], "provisioningState")), None)
        elif field == "foreign-policy":
            v["properties"][next(k for k in v["properties"] if k not in (OWN_FIELDS[kind], "provisioningState"))] = "foreign"
        elif field == "extra-policy":
            v["properties"]["unknownAssociation"] = {"id": "foreign"}
        else:
            v["nextLink"] = "https://private.invalid/token"
    port.put_model(n.PATHS[kind], mutation=mutate)
    refused(make().observe, n.PATHS[kind], decision=n.decision())
    assert port.sends("PUT") == []


def test_one_vm_send_consumes_vm_and_implicit_os_disk_before_send(fx):
    r, ns, _, _, port, make = fx
    def inspect(request):
        if request.method == "PUT":
            for kind in ("vm", "os_disk"):
                assert ns.read(r, n.PATHS[kind], decision=n.decision()).value["state"] == "create-consumed"
    port.before_send = inspect
    decision = n.decision()
    service = make()
    operation = service.create(n.PATHS["vm"], decision=decision)
    generation = service.admit(operation, decision=decision)
    assert generation.identity == IDENTITIES["vm"]
    assert generation.children[0].path == n.PATHS["os_disk"]
    assert len(port.sends("PUT")) == 1
    for kind in ("vm", "os_disk"):
        assert ns.read(r, n.PATHS[kind], decision=n.decision()).value["state"] == "admitted"
    assert ReadBudget(decision).count("private") <= 12
    refused(make().create, n.PATHS["os_disk"], decision=n.decision())
    assert len(port.sends("PUT")) == 1


@pytest.mark.parametrize("kind", ["nic", "public_ip", "vnet", "nsg", "os_disk"])
def test_single_kind_creation_correlates_durable_request_and_current_generation(fx, kind):
    _, _, _, _, port, make = fx
    service, decision = make(), n.decision()
    operation = service.create(n.PATHS[kind], decision=decision)
    generation = service.admit(operation, decision=decision)
    assert generation.identity == IDENTITIES[kind]
    assert generation.creation_receipt == operation.receipt_ref
    with closing(sqlite3.connect(port.path)) as db:
        assert db.execute("SELECT count(*) FROM receipts").fetchone()[0] >= 3
    refused(make().create, n.PATHS[kind], decision=n.decision())
    assert len(port.sends("PUT")) == 1


@pytest.mark.parametrize("fault", ["before-send", "lost-reply"])
def test_uncertain_send_or_reply_never_replays_after_service_reconstruction(fx, fault):
    r, ns, _, _, port, make = fx
    # Fault only the mutation, leaving authenticated unused-path preflight available.
    original = port.exchange
    def exchange(request, **kwargs):
        port.fault = fault if request.method == "PUT" else None
        return original(request, **kwargs)
    port.exchange = exchange
    refused(make().create, n.PATHS["vm"], decision=n.decision())
    port.fault = None
    port.exchange = original
    assert ns.read(r, n.PATHS["vm"], decision=n.decision()).value["state"] == "create-consumed"
    before = len(port.sends("PUT"))
    refused(make().create, n.PATHS["vm"], decision=n.decision())
    assert len(port.sends("PUT")) == before


def test_concurrent_creation_has_one_durable_send(fx):
    _, _, _, _, port, make = fx
    def contender(_):
        try:
            make().create(n.PATHS["public_ip"], decision=n.decision())
            return True
        except BindingError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        result = list(pool.map(contender, range(8)))
    assert result.count(True) == 1
    assert len(port.sends("PUT")) == 1


@pytest.mark.parametrize("status", ["Running", "Failed", "Canceled", "Succeeded"])
def test_original_async_operation_is_bounded_and_pending_is_not_admitted(fx, status):
    r, ns, _, _, port, make = fx
    port.async_kind, port.status = "public_ip", status
    service, decision = make(), n.decision()
    operation = service.create(n.PATHS["public_ip"], decision=decision)
    if status == "Succeeded":
        assert service.admit(operation, decision=decision).identity == IDENTITIES["public_ip"]
    else:
        refused(service.admit, operation, decision=decision)
        assert ns.read(r, operation.path, decision=n.decision()).value["state"] == "create-consumed"
    assert len(port.sends("PUT")) == 1


@pytest.mark.parametrize("url", ["http://management.azure.com/x", "https://evil.invalid/x",
    "https://management.azure.com@evil.invalid/x", "https://management.azure.com:443/x",
    "https://management.azure.com/subscriptions/foreign/providers/microsoft.compute/locations/westus/operations/op?api-version=2025-04-01",
    "https://management.azure.com/subscriptions/" + n.SUB + "/providers/microsoft.compute/locations/westus/operations/op?api-version=2026-03-01",
    "https://management.azure.com/subscriptions/" + n.SUB + "/providers/microsoft.compute/locations/westus/operations/op?api-version=2025-04-01&api-version=2025-04-01",
    "https://management.azure.com/subscriptions/" + n.SUB + "/providers/microsoft.compute/locations/../operations/op?api-version=2025-04-01"])
def test_unsupported_original_operation_locator_refuses_without_following_it(fx, url):
    _, _, _, _, port, make = fx
    port.async_kind = "vm"
    port.reply_mutation = lambda request, reply: replace(reply, locator=url) if request.method == "PUT" else reply
    refused(make().create, n.PATHS["vm"], decision=n.decision())
    assert len(port.sends("GET")) == 2
    assert len(port.sends("PUT")) == 1


@pytest.mark.parametrize("mutation", ["writers", "pending", "admission", "late"])
def test_current_fence_mutation_prevents_retirement_send(fx, mutation):
    _, _, _, _, port, make = fx
    service, decision = make(), n.decision()
    generation = service.admit(service.create(n.PATHS["vm"], decision=decision), decision=decision)
    if mutation == "writers":
        port.writers = (WRITER, "writer:foreign")
    elif mutation == "pending":
        port.outstanding = ("operation:pending",)
    elif mutation == "admission":
        port.admission = "admission:open"
    else:
        original = port.read
        port.read = lambda reference, **kw: replace(original(reference, **kw), expires_at=NOW)
    refused(make().retire, generation, attempt_ref="retire:one", decision=n.decision())
    assert port.sends("DELETE") == []


def test_hostile_writer_between_get_and_delete_invalidates_fence(fx):
    _, _, _, _, port, make = fx
    service, decision = make(), n.decision()
    generation = service.admit(service.create(n.PATHS["vm"], decision=decision), decision=decision)
    port.before_send = lambda request: setattr(port, "writers", (WRITER, "writer:bypass")) if request.method == "DELETE" else None
    refused(make().retire, generation, attempt_ref="retire:one", decision=n.decision())
    assert port.sends("DELETE") == []


def test_delete_is_not_completion_and_lost_reply_is_permanently_consumed(fx):
    r, ns, _, _, port, make = fx
    service, decision = make(), n.decision()
    generation = service.admit(service.create(n.PATHS["vm"], decision=decision), decision=decision)
    retirement = make()
    operation = retirement.retire(generation, attempt_ref="retire:one", decision=n.decision())
    assert ns.read(r, generation.path, decision=n.decision()).value["state"] == "retiring"
    retirement.deletion_complete(operation, generation, decision=n.decision())
    assert ns.read(r, generation.path, decision=n.decision()).value["state"] == "absent-tombstoned"
    refused(make().retire, generation, attempt_ref="retire:two", decision=n.decision())
    assert len(port.sends("DELETE")) == 1


def test_retirement_uses_historic_creation_without_renewing_its_authority(fx):
    _, _, _, _, port, make = fx
    service, decision = make(), n.decision()
    generation = service.admit(service.create(n.PATHS["vm"], decision=decision), decision=decision)
    later = n.decision(NOW + 20)
    # Fence source supplies its separately current authenticated observation.
    make().retire(generation, attempt_ref="retire:later", decision=later)
    assert later.deadline <= NOW + 30
    assert len(port.sends("DELETE")) == 1


def test_same_tags_and_path_with_replacement_guid_never_retires(fx):
    _, _, _, _, port, make = fx
    service, decision = make(), n.decision()
    generation = service.admit(service.create(n.PATHS["vm"], decision=decision), decision=decision)
    port.put_model(generation.path, mutation=lambda v: v["properties"].update(vmId=str(uuid.UUID(int=999))))
    refused(make().retire, generation, attempt_ref="retire:one", decision=n.decision())
    assert port.sends("DELETE") == []


def test_receipt_substitution_refuses_and_exception_repr_never_exports_payload(fx):
    _, _, _, _, port, make = fx
    port.put_model(n.PATHS["vm"])
    port.receipt_mutation = lambda value: replace(value, request=replace(value.request, url="https://private.invalid/secret"))
    refused(make().observe, n.PATHS["vm"], decision=n.decision())
    assert "private" not in repr(p.Reply(200, b"private-secret", "private:ref"))


def test_original_deadline_prevents_late_admission_and_new_send(fx):
    _, _, _, _, port, make = fx
    service = make()
    operation = service.create(n.PATHS["vm"], decision=n.decision())
    refused(make().admit, operation, decision=n.decision(NOW + 10))
    assert len(port.sends("PUT")) == 1


def test_real_local_blocked_read_obeys_original_timeout_and_never_sends(fx):
    _, _, _, ps, port, _ = fx
    left, right = socket.socketpair()
    def blocked(reference, *, decision, timeout):
        assert select.select([left], [], [], timeout)[0] == []
        raise TimeoutError("private-socket")
    try:
        decision = p.Decision(clock=lambda: NOW)
        decision.end = decision.last_mono + .1
        service = p.Provider(reserved=port.r, namespace=fx[1], policies=ps, port=port,
            receipts=port, fencing=type("FencePort", (), {"read": staticmethod(blocked)})(),
            writer_ref=WRITER, admission_ref=ADMISSION, retained_paths=(IMAGE,))
        started = time.monotonic()
        refused(service.create, n.PATHS["vm"], decision=decision)
        assert time.monotonic() - started < 1
        assert port.sends("PUT") == []
    finally:
        left.close()
        right.close()


from .readback_fixture import rb


def layout(rb, role):
    model = rb.arm[rb.ids["vm"]]
    props = model["properties"]
    props["storageProfile"]["osDisk"]["deleteOption"] = "Detach"
    rb.arm[rb.ids["disk"]]["properties"]["uniqueId"] = IDENTITIES["os_disk"]
    ids = (rb.ids["disk"],)
    if role != "worker":
        data = rb.ids["disk"] + "-retained"
        rb.arm[data] = {"id": data, "managedBy": rb.ids["vm"],
            "properties": {"provisioningState": "Succeeded", "diskState": "Attached",
                "uniqueId": str(uuid.UUID(int=444))}}
        props["storageProfile"]["dataDisks"] = [{"lun": 0, "createOption": "Attach",
            "deleteOption": "Detach", "managedDisk": {"id": data}}]
        ids += (data,)
        model["identity"] = {"type": "UserAssigned", "userAssignedIdentities": {
            n.PARENT + "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/trusted": {
                "clientId": str(uuid.UUID(int=31)), "principalId": str(uuid.UUID(int=32))}}}
    rb.deployment = replace(rb.deployment, role=role, disk_ids=ids,
        identity_digest=digest(model["identity"]),
        model_digest=digest({k: v for k, v in props.items() if k != "instanceView"}),
        storage_digest=digest({"image": rb.arm[rb.ids["image"]]["properties"],
            "disks": [rb.arm[x]["properties"] for x in ids]}))
    build = canonical({"image_id": rb.ids["image"], "build_recipe_ref": "build:measured",
        "source_roles_digest": "sha256:" + "a" * 64, "image_measurement_digest": "sha256:" + "b" * 64})
    def response(path):
        return p.Reply(200, canonical(rb.arm[path]), "readback:fixture")
    return [rb.deployment, response(rb.ids["vm"]), response(rb.ids["image"]),
            tuple(response(x) for x in ids), build]


@pytest.mark.parametrize("role", ["control", "gate", "worker"])
def test_real_legacy_reader_accepts_measured_image_and_first_pilot_disk_layout(rb, role):
    selection, vm, image, disks, build = layout(rb, role)
    actual = rb.deployment_reader().read(decision=rb.use()).data()
    assert actual["image_id"] == selection.image_id
    identities = p.compatible_layout(selection, vm, image, disks,
        approved_build=build, authenticated_build=build)
    assert len(identities) == (1 if role == "worker" else 2)
    assert len(set(identities)) == len(identities)


_LAYOUT_MUTATIONS = {
    "wrong-disk": lambda v, i, ds: ds[-1].update(id=ds[-1]["id"] + "-other"),
    "other-attachment": lambda v, i, ds: ds[-1].update(managedBy=ds[-1]["managedBy"] + "-foreign"),
    "missing-disk-guid": lambda v, i, ds: ds[-1]["properties"].pop("uniqueId"),
    "same-disk-guid": lambda v, i, ds: ds[-1]["properties"].update(uniqueId=ds[0]["properties"]["uniqueId"]),
    "bool-lun": lambda v, i, ds: v["properties"]["storageProfile"]["dataDisks"][0].update(lun=False),
    "wrong-lun": lambda v, i, ds: v["properties"]["storageProfile"]["dataDisks"][0].update(lun=1),
    "delete-os": lambda v, i, ds: v["properties"]["storageProfile"]["osDisk"].update(deleteOption="Delete"),
    "delete-data": lambda v, i, ds: v["properties"]["storageProfile"]["dataDisks"][0].update(deleteOption="Delete"),
    "delete-nic": lambda v, i, ds: v["properties"]["networkProfile"]["networkInterfaces"][0]["properties"].update(deleteOption="Delete"),
    "missing-detach": lambda v, i, ds: v["properties"]["storageProfile"]["osDisk"].pop("deleteOption"),
}


@pytest.mark.parametrize("mutation", ["marketplace", "mutable-image", "other-image", "wrong-build",
    "unmeasured-build", "extra-disk", "wrong-disk", "other-attachment", "missing-disk-guid",
    "same-disk-guid", "bool-lun", "wrong-lun", "delete-os", "delete-data", "delete-nic",
    "missing-detach", "worker-data", "incomplete-disks", "pending-image", "pending-disk"])
def test_image_and_retained_disk_single_mutations_refuse(rb, mutation):
    selection, vm, image, disks, build = layout(rb, "gate")
    v, i, ds = json.loads(vm.body), json.loads(image.body), [json.loads(x.body) for x in disks]
    authenticated = build
    if mutation == "marketplace":
        v["properties"]["storageProfile"]["imageReference"] = {"publisher": "Canonical", "version": "latest"}
    elif mutation == "mutable-image":
        v["properties"]["storageProfile"]["imageReference"]["id"] += "/latest"
    elif mutation == "other-image":
        i["id"] += "-other"
    elif mutation == "wrong-build":
        authenticated = canonical({**json.loads(build), "source_roles_digest": "sha256:" + "f" * 64})
    elif mutation == "unmeasured-build":
        build = authenticated = canonical({k: x for k, x in json.loads(build).items() if k != "image_measurement_digest"})
    elif mutation == "extra-disk":
        selection = replace(selection, disk_ids=selection.disk_ids + (selection.disk_ids[-1] + "-extra",))
    elif mutation in _LAYOUT_MUTATIONS:
        _LAYOUT_MUTATIONS[mutation](v, i, ds)
    elif mutation == "worker-data":
        selection = replace(selection, role="worker")
    elif mutation == "incomplete-disks":
        ds.pop()
    elif mutation == "pending-image":
        i["properties"]["provisioningState"] = "Creating"
    else:
        ds[-1]["properties"]["provisioningState"] = "Updating"
    refused(p.compatible_layout, selection, replace(vm, body=canonical(v)),
        replace(image, body=canonical(i)),
        tuple(replace(disks[min(j, len(disks)-1)], body=canonical(d)) for j, d in enumerate(ds)),
        approved_build=build, authenticated_build=authenticated)


def test_expanded_public_ip_detach_is_validated_separately_and_not_stripped(rb, fx):
    _, _, _, _, port, make = fx
    port.put_model(n.PATHS["nic"])
    observed, _ = make().observe(n.PATHS["nic"], decision=n.decision())
    actual = json.loads(observed.body)["properties"]["ipConfigurations"][0]["properties"]["publicIPAddress"]
    assert actual["properties"] == {"deleteOption": "Detach"}
    # The existing reader deliberately retains its exact id-only link contract.
    selection, _, _, _, _ = layout(rb, "control")
    pip = rb.ids["nic"].replace("networkInterfaces/nic-001", "publicIPAddresses/control")
    nic = rb.arm[rb.ids["nic"]]["properties"]
    nic["ipConfigurations"][0]["properties"]["publicIPAddress"] = {"id": pip, "properties": {"deleteOption": "Detach"}}
    rb.deployment = replace(selection, public_ip_id=pip,
        network_digest=digest({"nic": nic, "subnet": rb.arm[rb.ids["subnet"]]["properties"],
            "nsg": rb.arm[rb.ids["nsg"]]["properties"], "public_ip": {}}))
    with pytest.raises(BindingError):
        rb.deployment_reader().read(decision=rb.use())
    assert nic["ipConfigurations"][0]["properties"]["publicIPAddress"]["properties"] == {"deleteOption": "Detach"}


@pytest.mark.parametrize("when", ["process-before", "process-after"])
def test_actual_process_death_leaves_consumption_and_never_replays(fx, when):
    r, ns, _, _, port, make = fx
    identity_path = port.path.parent / "child-generation.json"
    pid = os.fork()
    if pid == 0:
        try:
            stat = Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()
            identity_path.write_text(json.dumps({"pid": os.getpid(), "start_time": stat[19]}))
            original = port.exchange
            def exchange(request, **kwargs):
                port.fault = when if request.method == "PUT" else None
                return original(request, **kwargs)
            port.exchange = exchange
            make().create(n.PATHS["public_ip"], decision=n.decision())
        except BaseException:
            os._exit(24)
        os._exit(25)
    end = time.monotonic() + 15
    status = None
    try:
        while time.monotonic() < end:
            actual, value = os.waitpid(pid, os.WNOHANG)
            if actual:
                status = value
                break
            time.sleep(.01)
        assert status is not None
        assert os.waitstatus_to_exitcode(status) == 23
    finally:
        if status is None:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
    generation = json.loads(identity_path.read_text())
    (port.path.parent / "helper-cleanup.json").write_text(json.dumps({
        "generations": [generation], "matching_alive": []}))
    assert ns.read(r, n.PATHS["public_ip"], decision=n.decision()).value["state"] == "create-consumed"
    count = len(port.sends("PUT"))
    assert count == (1 if when == "process-after" else 0)
    refused(make().create, n.PATHS["public_ip"], decision=n.decision())
    assert len(port.sends("PUT")) == count


def all_generations(make):
    service, decision = make(), n.decision()
    vm = service.admit(service.create(n.PATHS["vm"], decision=decision), decision=decision)
    result = {"vm": vm, "os_disk": vm.children[0]}
    for kind in ("nic", "public_ip", "vnet", "nsg"):
        service, decision = make(), n.decision()
        result[kind] = service.admit(service.create(n.PATHS[kind], decision=decision), decision=decision)
    return result


def test_all_six_kinds_retire_in_approved_order_and_preserve_excluded_image(fx):
    r, ns, _, _, port, make = fx
    generations = all_generations(make)
    retained = IMAGE
    with closing(sqlite3.connect(port.path)) as db:
        db.execute("INSERT INTO resources VALUES (?,?)", (retained, canonical({"retained": True})))
        db.commit()
    for kind in ("vm", "os_disk", "nic", "public_ip", "vnet", "nsg"):
        port.put_model(n.PATHS[kind], detached=True)
        service, decision = make(), n.decision()
        op = service.retire(generations[kind], attempt_ref="retire:" + kind, decision=decision)
        service.deletion_complete(op, generations[kind], decision=decision)
        assert ReadBudget(decision).count("private") <= 12
        assert ns.read(r, n.PATHS[kind], decision=n.decision()).value["state"] == "absent-tombstoned"
    assert port.body(retained) == canonical({"retained": True})
    assert [path for (path,) in port.sends("DELETE")] == [n.PATHS[k] for k in ("vm", "os_disk", "nic", "public_ip", "vnet", "nsg")]


@pytest.mark.parametrize("kind", ["os_disk", "nic", "public_ip", "vnet", "nsg"])
def test_unsatisfied_retirement_dependency_never_sends_delete(fx, kind):
    _, _, _, _, port, make = fx
    generations = all_generations(make)
    port.put_model(n.PATHS[kind], detached=True)
    refused(make().retire, generations[kind], attempt_ref="retire:blocked", decision=n.decision())
    assert port.sends("DELETE") == []


def test_lost_delete_reply_and_missing_receipt_never_reset_retirement(fx):
    r, ns, _, _, port, make = fx
    service, decision = make(), n.decision()
    vm = service.admit(service.create(n.PATHS["vm"], decision=decision), decision=decision)
    original = port.exchange
    def exchange(request, **kwargs):
        port.fault = "lost-reply" if request.method == "DELETE" else None
        return original(request, **kwargs)
    port.exchange = exchange
    refused(make().retire, vm, attempt_ref="retire:one", decision=n.decision())
    port.exchange, port.fault = original, None
    assert ns.read(r, vm.path, decision=n.decision()).value["state"] == "retiring"
    before = len(port.sends("DELETE"))
    with closing(sqlite3.connect(port.path)) as db:
        db.execute("DELETE FROM receipts")
        db.commit()
    refused(make().retire, vm, attempt_ref="retire:two", decision=n.decision())
    assert len(port.sends("DELETE")) == before == 1


@pytest.mark.parametrize("change", ["missing-policy", "wrong-path", "wrong-kind", "wrong-policy-ref",
    "body-extra", "wrong-region", "early-guid", "delete-option", "marketplace-image",
    "missing-os-claim", "retained-target", "duplicate-retained", "too-many-retained", "network-retained"])
def test_unapproved_or_unsafe_policy_refuses_before_any_provider_call(fx, change):
    r, ns, _, policies, port, _ = fx
    ps, retained = list(policies), (IMAGE,)
    index = next(i for i, item in enumerate(ps) if item.kind == "vm")
    body = json.loads(ps[index].create_body)
    if change == "missing-policy":
        ps.pop()
    elif change == "wrong-path":
        ps[0] = replace(ps[0], path=ps[0].path + "-foreign")
    elif change == "wrong-kind":
        ps[0] = replace(ps[0], kind="unknown")
    elif change == "wrong-policy-ref":
        ps[0] = replace(ps[0], policy_ref="policy:foreign")
    elif change == "body-extra":
        body["unselected"] = True
    elif change == "wrong-region":
        body["location"] = "elsewhere"
    elif change == "early-guid":
        body["properties"]["vmId"] = IDENTITIES["vm"]
    elif change == "delete-option":
        body["properties"]["storageProfile"]["osDisk"]["deleteOption"] = "Delete"
    elif change == "marketplace-image":
        body["properties"]["storageProfile"]["imageReference"] = {"publisher": "Canonical"}
    elif change == "missing-os-claim":
        body["properties"]["storageProfile"]["osDisk"]["name"] = "other-name"
    elif change == "retained-target":
        retained += (n.PATHS["os_disk"],)
    elif change == "duplicate-retained":
        retained += (IMAGE.upper(),)
    elif change == "too-many-retained":
        retained += tuple(n.PARENT + "/providers/Microsoft.Compute/disks/retained-" + str(i) for i in range(3))
    else:
        retained += (n.PATHS["nic"],)
    if change not in ("missing-policy", "wrong-path", "wrong-kind", "wrong-policy-ref"):
        ps[index] = replace(ps[index], create_body=canonical(body))
    refused(p.Provider, reserved=r, namespace=ns, policies=tuple(ps), port=port, receipts=port,
        fencing=port, writer_ref=WRITER, admission_ref=ADMISSION, retained_paths=retained)
    assert port.sends("PUT") == []
    assert port.sends("GET") == []


@pytest.mark.parametrize("raw", [b"[]", b"null", b'{"id":1,"id":2}', b"\xff",
    b'{"x":NaN}', b"x" * 1048577])
def test_malformed_or_oversized_authenticated_body_refuses(fx, raw):
    _, _, _, _, port, make = fx
    port.put_model(n.PATHS["public_ip"])
    port.reply_mutation = lambda request, reply: replace(reply, body=raw)
    refused(make().observe, n.PATHS["public_ip"], decision=n.decision())


@pytest.mark.parametrize("change", ["reference", "kind", "scope", "future", "expired", "body", "claims"])
def test_independent_durable_receipt_mismatch_never_admits(fx, change):
    r, ns, _, _, port, make = fx
    original = port.exchange
    def exchange(request, **kwargs):
        result = original(request, **kwargs)
        if request.method == "PUT":
            def corrupt(value):
                if change == "reference":
                    return replace(value, reply=replace(value.reply, receipt_ref="receipt:other"))
                changes = {"kind": {"kind": "unknown"}, "scope": {"reservation_digest": "sha256:" + "f" * 64},
                    "future": {"not_before": NOW + 1}, "expired": {"expires_at": NOW},
                    "body": {"body": b"{}"}, "claims": {"claims": ()}}
                return replace(value, request=replace(value.request, **changes[change]))
            port.receipt_mutation = corrupt
        return result
    port.exchange = exchange
    refused(make().create, n.PATHS["public_ip"], decision=n.decision())
    assert ns.read(r, n.PATHS["public_ip"], decision=n.decision()).value["state"] == "create-consumed"
    assert len(port.sends("PUT")) == 1


@pytest.mark.parametrize("change", ["wrong-name", "next-page", "nonterminal", "wrong-status-code"])
def test_terminal_operation_status_requires_original_correlated_success(fx, change):
    r, ns, _, _, port, make = fx
    port.async_kind = "public_ip"
    service, decision = make(), n.decision()
    operation = service.create(n.PATHS["public_ip"], decision=decision)
    def alter(request, reply):
        if "/locations/" not in request.url:
            return reply
        body = json.loads(reply.body)
        if change == "wrong-name":
            body["name"] = "other-operation"
        elif change == "next-page":
            body["nextLink"] = "https://foreign.invalid/private"
        elif change == "nonterminal":
            body["status"] = "Updating"
        else:
            return replace(reply, status=202)
        return replace(reply, body=canonical(body))
    port.reply_mutation = alter
    refused(service.admit, operation, decision=decision)
    assert ns.read(r, operation.path, decision=n.decision()).value["state"] == "create-consumed"
    assert len(port.sends("PUT")) == 1


@pytest.mark.parametrize("private,arm", [(12, 0), (0, 24)])
def test_exhausted_original_budget_prevents_uncharged_continuation(fx, private, arm):
    _, _, _, _, port, make = fx
    port.put_model(n.PATHS["public_ip"])
    decision = n.decision()
    budget = ReadBudget(decision)
    for _ in range(private):
        budget.consume("private")
    for _ in range(arm):
        budget.consume("arm")
    refused(make().observe, n.PATHS["public_ip"], decision=decision)
    assert ReadBudget(decision).count("private") == private
    assert len(port.sends("GET")) == (1 if private else 0)


def test_private_shared_disk_is_not_accepted_even_when_other_layout_facts_match(rb):
    selection, vm, image, disks, build = layout(rb, "gate")
    value = json.loads(disks[-1].body)
    value["managedByExtended"] = [selection.vm_id, selection.vm_id + "-foreign"]
    value["properties"]["maxShares"] = 2
    changed = disks[:-1] + (replace(disks[-1], body=canonical(value)),)
    refused(p.compatible_layout, selection, vm, image, changed,
        approved_build=build, authenticated_build=build)


@pytest.mark.parametrize("create_option", ["Attach", "Empty"])
def test_vm_can_attach_one_selected_retained_disk_but_never_create_it(fx, create_option):
    r, ns, _, policies, port, _ = fx
    retained = n.PARENT + "/providers/Microsoft.Compute/disks/retained-control"
    ps = list(policies)
    index = next(i for i, item in enumerate(ps) if item.kind == "vm")
    body, live, detached = (json.loads(x) for x in
        (ps[index].create_body, ps[index].present, ps[index].detached))
    disk = {"lun": 0, "managedDisk": {"id": retained}, "deleteOption": "Detach", "createOption": create_option}
    for value in (body["properties"], live, detached):
        value["storageProfile"]["dataDisks"] = [copy.deepcopy(disk)]
    ps[index] = replace(ps[index], create_body=canonical(body), present=canonical(live), detached=canonical(detached))
    port.policies = {x.path: x for x in ps}
    def construct():
        return p.Provider(reserved=r, namespace=ns, policies=tuple(ps), port=port, receipts=port,
            fencing=port, writer_ref=WRITER, admission_ref=ADMISSION, retained_paths=(IMAGE, retained))
    if create_option == "Empty":
        refused(construct)
        assert port.sends("PUT") == []
    else:
        service, decision = construct(), n.decision()
        generation = service.admit(service.create(n.PATHS["vm"], decision=decision), decision=decision)
        assert generation.children[0].path == n.PATHS["os_disk"]
        assert all(path != retained for (path,) in port.sends("PUT"))
        assert ReadBudget(decision).count("private") <= 12


def test_original_async_create_and_pending_delete_reconcile_without_a_second_mutation(fx):
    r, ns, _, _, port, make = fx
    port.async_kind = "vm"
    service, create_decision = make(), n.decision()
    generation = service.admit(service.create(n.PATHS["vm"], decision=create_decision), decision=create_decision)
    cleanup, cleanup_decision = make(), n.decision()
    operation = cleanup.retire(generation, attempt_ref="retire:async", decision=cleanup_decision)
    port.status = "Running"
    refused(cleanup.deletion_complete, operation, generation, decision=cleanup_decision)
    assert ns.read(r, generation.path, decision=n.decision()).value["state"] == "retiring"
    port.status = "Succeeded"
    cleanup.deletion_complete(operation, generation, decision=cleanup_decision)
    assert len(port.sends("DELETE")) == 1
    assert ns.read(r, generation.path, decision=n.decision()).value["state"] == "absent-tombstoned"


def test_http204_without_independent_absence_does_not_complete_retirement(fx):
    r, ns, _, _, port, make = fx
    creator, decision = make(), n.decision()
    generation = creator.admit(creator.create(n.PATHS["vm"], decision=decision), decision=decision)
    cleanup, cleanup_decision = make(), n.decision()
    operation = cleanup.retire(generation, attempt_ref="retire:one", decision=cleanup_decision)
    port.put_model(generation.path)
    refused(cleanup.deletion_complete, operation, generation, decision=cleanup_decision)
    assert ns.read(r, generation.path, decision=n.decision()).value["state"] == "retiring"
    assert len(port.sends("DELETE")) == 1


@pytest.mark.parametrize("method", ["observe", "create"])
def test_lost_namespace_refuses_before_any_provider_observation_or_mutation(fx, method):
    _, _, store, _, port, make = fx
    store.remove(n.INDEX)
    refused(getattr(make(), method), n.PATHS["vm"], decision=n.decision())
    assert port.sends("GET") == []
    assert port.sends("PUT") == []


def test_authenticated_poll_cannot_claim_success_with_an_error(fx):
    _, _, _, _, port, make = fx
    port.async_kind = "public_ip"
    service, decision = make(), n.decision()
    operation = service.create(n.PATHS["public_ip"], decision=decision)
    port.reply_mutation = lambda req, reply: replace(reply,
        body=canonical({"status": "Succeeded", "error": {"code": "Contradiction"}})) if "/locations/" in req.url else reply
    refused(service.admit, operation, decision=decision)
    assert len(port.sends("PUT")) == 1


def test_private_nic_without_a_public_ip_is_an_available_positive(fx):
    r, ns, _, policies, port, _ = fx
    ps = list(policies)
    index = next(i for i, item in enumerate(ps) if item.kind == "nic")
    values = [json.loads(x) for x in (ps[index].create_body, ps[index].present, ps[index].detached)]
    for value in (values[0]["properties"], *values[1:]):
        value["ipConfigurations"][0]["properties"].pop("publicIPAddress")
    ps[index] = replace(ps[index], create_body=canonical(values[0]), present=canonical(values[1]), detached=canonical(values[2]))
    port.policies = {x.path: x for x in ps}
    port.put_model(n.PATHS["nic"])
    service = p.Provider(reserved=r, namespace=ns, policies=tuple(ps), port=port, receipts=port,
        fencing=port, writer_ref=WRITER, admission_ref=ADMISSION, retained_paths=(IMAGE,))
    observed, identity = service.observe(n.PATHS["nic"], decision=n.decision())
    assert identity == IDENTITIES["nic"]
    assert "publicIPAddress" not in json.loads(observed.body)["properties"]["ipConfigurations"][0]["properties"]


def test_documented_status_only_original_operation_response_is_available(fx):
    _, _, _, _, port, make = fx
    port.async_kind = "public_ip"
    service, decision = make(), n.decision()
    operation = service.create(n.PATHS["public_ip"], decision=decision)
    port.reply_mutation = lambda req, reply: replace(reply, body=canonical({"status": "Succeeded"})) if "/locations/" in req.url else reply
    generation = service.admit(operation, decision=decision)
    assert generation.identity == IDENTITIES["public_ip"]
    assert len(port.sends("PUT")) == 1


@pytest.mark.parametrize("status", [204, 400, 500])
@pytest.mark.parametrize("phase", ["admit", "retire"])
def test_original_async_creation_http_error_never_becomes_success(fx, status, phase):
    _, _, _, _, port, make = fx
    port.async_kind, port.status = "public_ip", "Succeeded"
    service, decision = make(), n.decision()
    operation = service.create(n.PATHS["public_ip"], decision=decision)
    generation = service.admit(operation, decision=decision) if phase == "retire" else None
    port.receipt_mutation = lambda value: replace(value, reply=replace(value.reply, status=status)) if value.request.method == "PUT" else value
    if phase == "admit":
        refused(make().admit, operation, decision=n.decision())
    else:
        refused(make().retire, generation, attempt_ref="retire:bad-http", decision=n.decision())
    assert port.sends("DELETE") == []
