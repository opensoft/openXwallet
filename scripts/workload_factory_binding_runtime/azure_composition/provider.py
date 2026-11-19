"""Internal P03 provider semantics over independently selected authenticated ports.

No credential acquisition, network client, initialization, watchdog or route is
provided. Ports own authentication and durable private receipts; response fields
and public dataclass construction are not provenance. Public reports stay separate.
"""
from dataclasses import dataclass, replace
from urllib.parse import urlsplit
import re
import threading
import weakref

from workload_factory_binding.evidence import BindingError, canonical, digest
from ..github_bootstrap.common import Decision, document as decoded
from ..hosted.readback import ReadBudget
from .namespace import Namespace
from .selection import Record, arm_key, check, closed, document, ref, UUID, KINDS, reservation

ERROR = "azure-provider-refused"
ARM = "https://management.azure.com"
VM_VERSION = "2025-04-01"
DISK_VERSION = "2025-01-02"
NETWORK_VERSION = "2026-01-01"
VERSIONS = dict.fromkeys(KINDS, NETWORK_VERSION)
VERSIONS.update(vm=VM_VERSION, os_disk=DISK_VERSION)
IDENTITIES = dict.fromkeys(KINDS, "resourceGuid")
IDENTITIES.update(vm="vmId", os_disk="uniqueId")
DETACH = "Detach"


@dataclass(frozen=True, repr=False)
class Policy:
    """Independently approved complete model projections, not caller assertions."""
    path: str
    kind: str
    policy_ref: str
    create_body: bytes
    present: bytes
    detached: bytes


@dataclass(frozen=True, repr=False)
class Request:
    method: str
    url: str
    body: bytes
    headers: tuple
    reservation_digest: str
    path: str
    kind: str
    attempt_ref: str
    not_before: int
    expires_at: int
    claims: tuple = ()


@dataclass(frozen=True, repr=False)
class Reply:
    status: int
    body: bytes
    receipt_ref: str
    identity_ref: str | None = None
    locator: str | None = None


@dataclass(frozen=True, repr=False)
class Receipt:
    request: Request
    reply: Reply


@dataclass(frozen=True, repr=False)
class Fence:
    reservation_digest: str
    generation_ref: str
    resource_path: str
    writer_ref: str
    ordinary_writers: tuple
    outstanding_operations: tuple
    admission_ref: str
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class Generation:
    path: str
    identity: str
    creation_receipt: str
    readback_receipt: str
    identity_ref: str
    terminal_receipt: str
    children: tuple = ()


@dataclass(frozen=True, repr=False)
class Operation:
    path: str
    receipt_ref: str


def _guid(value):
    check(type(value) is str and UUID.fullmatch(value) is not None)


def _object(raw):
    value = decoded(raw, 1048576)
    check(type(value) is dict and "nextLink" not in value)
    return value


def _detach_vm(value):
    storage = value["storageProfile"]
    check(type(storage) is dict and type(storage["osDisk"]) is dict)
    check(storage["osDisk"].get("deleteOption") == DETACH)
    disks = storage.get("dataDisks")
    check(type(disks) is list and len(disks) <= 1)
    check(all(type(d) is dict and d.get("deleteOption") == DETACH for d in disks))
    links = value["networkProfile"]["networkInterfaces"]
    check(type(links) is list and len(links) == 1)
    check(links[0]["properties"].get("deleteOption") == DETACH)


def _detach_nic(value):
    configs = value["ipConfigurations"]
    check(type(configs) is list and len(configs) == 1)
    public = configs[0]["properties"].get("publicIPAddress")
    if public is not None:
        closed(public, {"id", "properties"})
        closed(public["properties"], {"deleteOption"})
        arm_key(public["id"])
        check(public["properties"]["deleteOption"] == DETACH)


def _retirement_model(kind, value):
    if kind == "os_disk":
        check(value.get("diskState") == "Unattached")
        check(value.get("managedBy") is None and not value.get("managedByExtended"))
    elif kind == "nic":
        check(value.get("virtualMachine") is None)
    elif kind == "public_ip":
        check(value.get("ipConfiguration") is None and not value.get("natGateway"))
    elif kind == "vnet":
        for name in ("virtualNetworkPeerings", "privateEndpoints"):
            check(value.get(name, []) == [])
        for subnet in value["subnets"]:
            p = subnet["properties"]
            for name in ("ipConfigurations", "privateEndpoints", "delegations",
                         "serviceAssociationLinks", "resourceNavigationLinks"):
                check(p.get(name, []) == [])
    elif kind == "nsg":
        check(value.get("networkInterfaces", []) == [] and value.get("subnets", []) == [])


def _identity(reply, policy):
    check(reply.status in (200, 201))
    value = _object(reply.body)
    check(value.get("id") == policy.path and value.get("location") == "westus")
    check(type(value.get("type")) is str
          and value["type"].lower() == "/".join(KINDS[policy.kind]))
    props = value["properties"]
    check(type(props) is dict and props.get("provisioningState") == "Succeeded")
    identity = props[IDENTITIES[policy.kind]]
    _guid(identity)
    ref(reply.identity_ref)
    return value, props, identity


def _model(reply, policy, *, retiring=False):
    check(reply.status == 200)
    value, props, identity = _identity(reply, policy)
    projection = {k: v for k, v in props.items()
                  if k not in {IDENTITIES[policy.kind], "provisioningState"}}
    # Attachment metadata lives at the resource root for disks.
    if policy.kind == "os_disk":
        projection.update({k: value[k] for k in ("managedBy", "managedByExtended") if k in value})
    check(canonical(projection) == (policy.detached if retiring else policy.present))
    if policy.kind == "vm":
        _detach_vm(props)
    if policy.kind == "nic":
        _detach_nic(props)
    if retiring:
        _retirement_model(policy.kind, projection)
    return identity


def _locator(url, *, path, kind):
    """Only documented provider operation routes, never an arbitrary bearer URL."""
    check(type(url) is str and 0 < len(url) <= 4096)
    check(all(32 < ord(c) < 127 for c in url) and "%" not in url and "\\" not in url)
    u = urlsplit(url)
    check(u.scheme == "https" and u.netloc == "management.azure.com"
          and not u.fragment and not u.username and not u.password)
    provider = KINDS[kind][0]
    subscription = path.split("/")[2]
    # ARM operation locations are not necessarily resource-ID-prefixed.
    prefix = "/subscriptions/" + subscription + "/providers/" + provider + "/locations/"
    check(u.path.lower().startswith(prefix))
    tail = u.path[len(prefix):].split("/")
    check(len(tail) == 3 and tail[1] in ("operations", "operationStatuses", "operationResults"))
    check(all(re.fullmatch(r"[A-Za-z0-9_-]{1,160}", x, re.ASCII) for x in (tail[0], tail[2])))
    check(u.query == "api-version=" + VERSIONS[kind])
    return url


def _succeeded(reply, url):
    check(reply.status == 200 and reply.locator is None)
    status = _object(reply.body)
    check(set(status) <= {"status", "name", "id", "startTime", "endTime", "percentComplete", "properties", "error"})
    check(status.get("status") == "Succeeded" and status.get("error") is None)
    if "name" in status:
        check(status["name"] == urlsplit(url).path.split("/")[-1])
    if "id" in status:
        check(status["id"] == urlsplit(url).path)


class Provider:
    """Trusted port methods exchange(request, decision, timeout, before_send),
    receipt(ref, decision, timeout) and fence(path, decision, timeout).

    Every exchange has one durable immutable receipt before returning. The
    independent receipt reader must resolve the exact original request/response.
    Fence observations come from the selected independent controller, not Azure
    tags or a worker. Privileged administrators remain explicitly trusted.
    """
    def __init__(self, *, reserved, namespace, policies, port, receipts, fencing,
                 writer_ref, admission_ref, retained_paths=()):
        try:
            check(type(reserved) is Record and type(namespace) is Namespace)
            reservation(reserved.raw, approved=reserved.raw)
            ref(writer_ref)
            ref(admission_ref)
            check(type(policies) is tuple and type(retained_paths) is tuple)
            expected = reserved.value["resources"]
            check(len(policies) == len(expected))
            self._policies = {}
            retained = {arm_key(p) for p in retained_paths}
            check(len(retained) == len(retained_paths))
            for resource, policy in zip(expected, policies):
                check(type(policy) is Policy)
                check((policy.path, policy.kind, policy.policy_ref) ==
                      (resource["resource_path"], resource["kind"], resource["resource_policy_ref"]))
                check(arm_key(policy.path) not in retained)
                for raw in (policy.create_body, policy.present, policy.detached):
                    document(raw)
                self._policies[policy.path] = policy
            self._reserved, self._namespace = reserved, namespace
            self._port, self._receipts, self._fencing = port, receipts, fencing
            self._writer, self._admission = writer_ref, admission_ref
            self._caches = weakref.WeakKeyDictionary()
            self._cache_lock = threading.RLock()
            self._retained = retained
            check(sum(p.kind == "vm" for p in policies) <= 3)
            check(sum("/providers/microsoft.compute/disks/" in p for p in retained) <= 2)
            check(all("/providers/microsoft.compute/" in p and
                      p.split("/")[-2] in ("disks", "images") for p in retained))
            for policy in policies:
                self._validate_payload(policy)
            data_paths = [arm_key(d["managedDisk"]["id"]) for p in policies if p.kind == "vm"
                          for d in document(p.create_body)["properties"]["storageProfile"]["dataDisks"]]
            check(len(data_paths) <= 2 and len(set(data_paths)) == len(data_paths))
        except Exception:
            raise BindingError(ERROR) from None

    def _claims(self, path):
        policy = self._policy(path)
        targets = []
        if policy.kind == "vm":
            os_disk = document(policy.present)["storageProfile"]["osDisk"]["managedDisk"]["id"]
            targets.append(os_disk)
        targets.append(path)
        resources = {r["resource_path"]: r for r in self._reserved.value["resources"]}
        return tuple((p, resources[p]["create_attempt_ref"]) for p in targets)

    def _validate_payload(self, policy):
        body = document(policy.create_body)
        check(type(body) is dict and set(body) <= {"location", "properties", "identity"}
              and body.get("location") == "westus" and type(body.get("properties")) is dict)
        props = body["properties"]
        check(IDENTITIES[policy.kind] not in props and "provisioningState" not in props)
        if policy.kind == "vm":
            _detach_vm(props)
            storage = props["storageProfile"]
            closed(storage["imageReference"], {"id"})
            image = storage["imageReference"]["id"]
            check(arm_key(image) in self._retained and "/providers/microsoft.compute/images/" in arm_key(image))
            os_path = document(policy.present)["storageProfile"]["osDisk"]["managedDisk"]["id"]
            check(self._policy(os_path).kind == "os_disk"
                  and storage["osDisk"].get("name") == os_path.split("/")[-1]
                  and storage["osDisk"].get("createOption") == "FromImage")
            for disk in storage["dataDisks"]:
                check(disk.get("createOption") == "Attach" and arm_key(disk["managedDisk"]["id"]) in self._retained)
            for nic in props["networkProfile"]["networkInterfaces"]:
                check(self._policy(nic["id"]).kind == "nic")
        if policy.kind == "nic":
            _detach_nic(props)
        if policy.kind == "os_disk":
            check(props.get("creationData", {}).get("createOption") in ("Empty", "FromImage"))

    def _call(self, group, function, decision, *args, **kwargs):
        ReadBudget(decision).consume(group)
        value = function(*args, decision=decision, timeout=decision.remaining(), **kwargs)
        decision.remaining()
        return value

    def _policy(self, path):
        check(path in self._policies)
        return self._policies[path]

    def _receipt(self, reference, decision, *, active=True):
        ref(reference)
        with self._cache_lock:
            cache = self._caches.setdefault(decision, {})
            value = cache.get(reference)
        if value is None:
            value = self._call("private", self._receipts.read, decision, reference)
        check(type(value) is Receipt and type(value.request) is Request and type(value.reply) is Reply)
        check(value.reply.receipt_ref == reference)
        request = value.request
        policy = self._policy(request.path)
        check(request.kind == policy.kind and request.reservation_digest == self._reserved.digest)
        check(request.method in ("GET", "PUT", "DELETE"))
        ref(request.attempt_ref)
        check(request.body == (policy.create_body if request.method == "PUT" else b""))
        check(request.headers == ((("If-None-Match", "*"),)
              if request.method == "PUT" and policy.kind == "vm" else ()))
        check(request.claims == (self._claims(request.path) if request.method == "PUT" else ()))
        if request.method == "GET" and request.url != ARM + request.path + "?api-version=" + VERSIONS[policy.kind]:
            _locator(request.url, path=request.path, kind=policy.kind)
        else:
            check(request.url == ARM + request.path + "?api-version=" + VERSIONS[policy.kind])
        window = self._reserved.value["window"]
        check(type(request.not_before) is int and type(request.expires_at) is int
              and window["not_before"] <= request.not_before < request.expires_at <= window["not_after"]
              and request.not_before <= decision.now())
        if active:
            decision.clip(request.expires_at)
        with self._cache_lock:
            check(reference not in cache or cache[reference] == value)
            cache[reference] = value
        return value

    def _exchange(self, request, decision, guard=lambda: None):
        guard()
        decision.remaining()
        request = replace(request, expires_at=min(request.expires_at, decision.deadline))

        def before_send():
            guard()
            decision.remaining()
            # A later fence may shorten authority again. Do not send the frozen
            # request with a longer durable expiry, or retry a consumed attempt.
            check(request.expires_at <= decision.deadline)

        reply = self._call("arm", self._port.exchange, decision, request, before_send=before_send)
        check(type(reply) is Reply and type(reply.status) is int)
        check(type(reply.body) is bytes and len(reply.body) <= 1048576)
        stored = self._receipt(reply.receipt_ref, decision)
        check(stored == Receipt(request, reply))
        return reply

    def _request(self, method, policy, attempt, decision, *, url=None):
        check(type(decision) is Decision)
        window = self._reserved.value["window"]
        now = decision.now()
        check(window["not_before"] <= now < window["not_after"])
        decision.clip(window["not_after"])
        ref(attempt)
        headers = (("If-None-Match", "*"),) if method == "PUT" and policy.kind == "vm" else ()
        return Request(method, url or ARM + policy.path + "?api-version=" + VERSIONS[policy.kind],
                       policy.create_body if method == "PUT" else b"", headers,
                       self._reserved.digest, policy.path, policy.kind, attempt, now, decision.deadline,
                       self._claims(policy.path) if method == "PUT" else ())

    def _fence(self, path, decision, *, retiring=False):
        value = self._call("private", self._fencing.read, decision, path)
        check(type(value) is Fence)
        expected = self._reserved.value
        check((value.reservation_digest, value.generation_ref, value.resource_path, value.writer_ref)
              == (self._reserved.digest, expected["namespace_generation_ref"], path, self._writer))
        check(value.ordinary_writers == (self._writer,) and value.outstanding_operations == ())
        check(type(value.observed_at) is int and type(value.expires_at) is int
              and value.observed_at <= decision.now() < value.expires_at <= value.observed_at + 60)
        if retiring:
            check(value.admission_ref == self._admission)
        decision.clip(value.expires_at)

    def observe(self, path, *, decision, retiring=False):
        try:
            policy = self._policy(path)
            self._namespace.read(self._reserved, path, decision=decision)
            reply = self._exchange(self._request("GET", policy, "observe:current", decision), decision)
            return reply, _model(reply, policy, retiring=retiring)
        except Exception:
            raise BindingError(ERROR) from None

    def create(self, path, *, decision):
        try:
            policy = self._policy(path)
            resource = next(r for r in self._reserved.value["resources"] if r["resource_path"] == path)
            request = self._request("PUT", policy, resource["create_attempt_ref"], decision)
            for claim_path, _ in request.claims:
                current = self._namespace.read(self._reserved, claim_path, decision=decision).value
                check(current["state"] == "reserved")
                self._fence(claim_path, decision)
                claim_policy = self._policy(claim_path)
                absent = self._exchange(self._request("GET", claim_policy, "observe:unused", decision), decision)
                check(absent.status == 404)
            # Consume every implicitly created resource before the sole send.
            for claim_path, attempt in request.claims:
                self._namespace.consume_create(self._reserved, claim_path,
                    attempt_ref=attempt, decision=decision)
            reply = self._exchange(request, decision, lambda: self._fence(path, decision))
            check(reply.status in (200, 201, 202))
            if reply.locator is not None:
                _locator(reply.locator, path=path, kind=policy.kind)
            return Operation(path, reply.receipt_ref)
        except Exception:
            raise BindingError(ERROR) from None

    def _terminal(self, operation, method, decision):
        check(type(operation) is Operation)
        original = self._receipt(operation.receipt_ref, decision)
        request, reply = original.request, original.reply
        check(request.method == method and request.path == operation.path)
        policy = self._policy(operation.path)
        check(reply.status in ((200, 201, 202) if method == "PUT" else (200, 202, 204)))
        expected = self._request(method, policy, request.attempt_ref, decision)
        check((request.url, request.body, request.headers, request.claims) ==
              (expected.url, expected.body, expected.headers, expected.claims))
        if reply.locator is None:
            check(reply.status in ((200, 201) if method == "PUT" else (200, 204)))
            if method == "PUT":
                check(_object(reply.body)["properties"].get("provisioningState") == "Succeeded")
        else:
            url = _locator(reply.locator, path=operation.path, kind=policy.kind)
            poll = self._exchange(self._request("GET", policy, request.attempt_ref,
                                               decision, url=url), decision)
            _succeeded(poll, url)
            return request, reply, poll.receipt_ref
        return request, reply, reply.receipt_ref

    def admit(self, operation, *, decision):
        try:
            request, original, terminal = self._terminal(operation, "PUT", decision)
            current = self._namespace.read(self._reserved, operation.path, decision=decision).value
            check(current["state"] in ("create-consumed", "pending", "quarantined")
                  and current["create_attempt_ref"] == request.attempt_ref)
            observed = []
            for path, attempt in request.claims:
                claim = self._namespace.read(self._reserved, path, decision=decision).value
                check(claim["state"] in ("create-consumed", "pending", "quarantined")
                      and claim["create_attempt_ref"] == attempt)
                reply, identity = self.observe(path, decision=decision)
                observed.append((path, reply, identity))
            if original.locator is None:
                check(_identity(original, self._policy(operation.path))[2] == observed[-1][2])
            self._fence(operation.path, decision)
            generations = []
            for path, reply, identity in observed:
                creation = {"incarnation_ref": reply.identity_ref,
                            "create_operation_ref": operation.receipt_ref,
                            "creation_readback_ref": reply.receipt_ref}
                self._namespace.transition(self._reserved, path, state="admitted",
                    observation_ref=reply.receipt_ref, creation=creation, decision=decision)
                generations.append(Generation(path, identity, operation.receipt_ref,
                    reply.receipt_ref, reply.identity_ref, terminal))
            parent = generations[-1]
            return replace(parent, children=tuple(generations[:-1]))
        except Exception:
            raise BindingError(ERROR) from None

    def _generation(self, generation, decision):
        check(type(generation) is Generation)
        original = self._receipt(generation.creation_receipt, decision, active=False)
        policy = self._policy(original.request.path)
        resource = next(r for r in self._reserved.value["resources"] if r["resource_path"] == generation.path)
        check(original.reply.status in (200, 201, 202))
        check(original.request.method == "PUT" and (generation.path, resource["create_attempt_ref"]) in original.request.claims
              and original.request.claims == self._claims(original.request.path)
              and original.request.url == ARM + original.request.path + "?api-version=" + VERSIONS[policy.kind]
              and original.request.body == policy.create_body
              and original.request.headers == ((("If-None-Match", "*"),) if policy.kind == "vm" else ()))
        terminal = self._receipt(generation.terminal_receipt, decision, active=False)
        if original.reply.locator is None:
            check(terminal == original and original.reply.status in (200, 201))
            original_identity = _identity(original.reply, policy)[2]
            if original.request.path == generation.path:
                check(original_identity == generation.identity)
        else:
            url = _locator(original.reply.locator, path=original.request.path, kind=policy.kind)
            check(terminal.request.method == "GET" and terminal.request.url == url
                  and terminal.request.path == original.request.path
                  and terminal.request.attempt_ref == original.request.attempt_ref
                  and terminal.request.expires_at <= original.request.expires_at)
            _succeeded(terminal.reply, url)
        recorded = self._receipt(generation.readback_receipt, decision, active=False)
        check(recorded.request.expires_at <= original.request.expires_at)
        check(recorded.request.method == "GET" and recorded.request.path == generation.path)
        check(recorded.request.url == ARM + generation.path + "?api-version=" + VERSIONS[self._policy(generation.path).kind])
        check(_model(recorded.reply, self._policy(generation.path)) == generation.identity)
        check(recorded.reply.identity_ref == generation.identity_ref)
        current = self._namespace.read(self._reserved, generation.path, decision=decision).value
        check(current["creation"] == {"incarnation_ref": generation.identity_ref,
              "create_operation_ref": generation.creation_receipt,
              "creation_readback_ref": generation.readback_receipt})
        return current

    def _dependencies(self, path, decision):
        resource = next(r for r in self._reserved.value["resources"] if r["resource_path"] == path)
        for dependency in resource["dependency_paths"]:
            state = self._namespace.read(self._reserved, dependency, decision=decision).value
            check(state["state"] == "absent-tombstoned")
            policy = self._policy(dependency)
            absent = self._exchange(self._request("GET", policy, "observe:absent", decision), decision)
            check(absent.status == 404)

    def retire(self, generation, *, attempt_ref, decision):
        try:
            current = self._generation(generation, decision)
            check(current["state"] in ("admitted", "quarantined") and "retirement_attempt_ref" not in current)
            self._dependencies(generation.path, decision)
            self._fence(generation.path, decision, retiring=True)
            observed, identity = self.observe(generation.path, decision=decision, retiring=True)
            check(identity == generation.identity)
            self._namespace.transition(self._reserved, generation.path, state="retiring",
                observation_ref=observed.receipt_ref, retirement_attempt_ref=attempt_ref, decision=decision)
            policy = self._policy(generation.path)
            reply = self._exchange(self._request("DELETE", policy, attempt_ref, decision), decision,
                                   lambda: self._fence(generation.path, decision, retiring=True))
            check(reply.status in (200, 202, 204))
            if reply.locator is not None:
                _locator(reply.locator, path=generation.path, kind=policy.kind)
            return Operation(generation.path, reply.receipt_ref)
        except Exception:
            raise BindingError(ERROR) from None


    def deletion_complete(self, operation, generation, *, decision):
        """One-resource reconciliation only; no watchdog or overall receipt."""
        try:
            request, _, _ = self._terminal(operation, "DELETE", decision)
            check(operation.path == generation.path)
            current = self._generation(generation, decision)
            check(current["state"] == "retiring" and current["retirement_attempt_ref"] == request.attempt_ref)
            self._fence(operation.path, decision, retiring=True)
            policy = self._policy(operation.path)
            observed = self._exchange(self._request("GET", policy, request.attempt_ref, decision), decision)
            check(observed.status == 404)
            self._namespace.transition(self._reserved, operation.path, state="absent-tombstoned",
                observation_ref=observed.receipt_ref, decision=decision)
            return observed.receipt_ref
        except Exception:
            raise BindingError(ERROR) from None


def compatible_layout(selection, vm, image, disks, *, approved_build, authenticated_build):
    """Pure compatibility checks; authentication of supplied facts is external.

    The original DeploymentReader remains unchanged and is exercised separately.
    This function does not create/import/select an actual image or initialize disks.
    """
    try:
        from ..hosted.platform_readback import DeploymentSelection
        check(type(selection) is DeploymentSelection)
        selection.record()
        build = document(approved_build)
        closed(build, {"image_id", "build_recipe_ref", "source_roles_digest", "image_measurement_digest"})
        check(type(authenticated_build) is bytes and authenticated_build == approved_build)
        check(build["image_id"] == selection.image_id)
        ref(build["build_recipe_ref"])
        from .selection import digest as validate_digest
        for name in ("source_roles_digest", "image_measurement_digest"):
            validate_digest(build[name])
        check(type(vm) is Reply and type(image) is Reply and type(disks) is tuple)
        model, artifact = _object(vm.body), _object(image.body)
        check(vm.status == image.status == 200 and artifact["id"] == selection.image_id
              and model["id"] == selection.vm_id)
        check(model["properties"]["vmId"] == selection.incarnation_id)
        check(selection.role != "worker" or len(selection.disk_ids) == 1)
        check(artifact["properties"]["provisioningState"] == "Succeeded")
        storage = model["properties"]["storageProfile"]
        check(storage["imageReference"] == {"id": selection.image_id})
        check(storage["osDisk"]["managedDisk"]["id"] == selection.disk_ids[0])
        check(tuple(x["managedDisk"]["id"] for x in storage["dataDisks"]) == selection.disk_ids[1:])
        check(all(type(x.get("lun")) is int and x["lun"] == 0 for x in storage["dataDisks"]))
        check(len(disks) == len(selection.disk_ids))
        identities = []
        disk_properties = []
        for path, observed in zip(selection.disk_ids, disks):
            check(type(observed) is Reply and observed.status == 200)
            value = _object(observed.body)
            check(value["id"] == path and value.get("managedBy") == selection.vm_id
                  and value["properties"].get("diskState") == "Attached"
                  and value["properties"].get("provisioningState") == "Succeeded")
            _guid(value["properties"]["uniqueId"])
            check(value.get("managedByExtended") in (None, []))
            shares = value["properties"].get("maxShares")
            check(shares is None or (type(shares) is int and shares == 1))
            check(value["properties"].get("shareInfo", []) == [])
            identities.append(value["properties"]["uniqueId"])
            disk_properties.append(value["properties"])
        check(digest({"image": artifact["properties"], "disks": disk_properties}) == selection.storage_digest)
        check(len(set(identities)) == len(identities))
        _detach_vm(model["properties"])
        return tuple(identities)
    except Exception:
        raise BindingError(ERROR) from None
