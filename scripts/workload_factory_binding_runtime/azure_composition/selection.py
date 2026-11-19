"""Closed P3 records only; parsing is neither authentication nor operational authority.

Callers supply independently authenticated selections/readbacks. The deployment
entrypoint remains unconnected; no provider or credential operation lives here.
"""
from dataclasses import dataclass, field
import re

from workload_factory_binding.evidence import (
    BindingError, byte_digest, canonical, decode_object, require,
)

ERROR = "azure-composition-refused"
LIMIT = 16384
REF = re.compile(r"[A-Za-z][A-Za-z0-9:._/-]{0,159}\Z", re.ASCII)
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)
UUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z", re.ASCII)
COMMIT = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
RUN = re.compile(r"[1-9][0-9]{0,19}\Z", re.ASCII)
ENVELOPE = "openxfactory-azure-deployment-envelope-internal-v1"
FINAL = "openxfactory-azure-final-scope-link-internal-v1"
RETIREMENT = "openxfactory-azure-retirement-receipt-internal-v1"
COMMON = frozenset("""profile phase deployment_ref owner_scope_ref namespace_ref
namespace_generation_ref case_ref source_roles_digest build_recipe_ref target
resources retained_scope_ref window setup_authority_ref""".split())
RESOURCE = frozenset("""resource_path kind dependency_paths resource_policy_ref
create_attempt_ref disposition""".split())
CREATION = frozenset("incarnation_ref create_operation_ref creation_readback_ref".split())
KINDS = {
    "vm": ("microsoft.compute", "virtualmachines"),
    "os_disk": ("microsoft.compute", "disks"),
    "nic": ("microsoft.network", "networkinterfaces"),
    "public_ip": ("microsoft.network", "publicipaddresses"),
    "vnet": ("microsoft.network", "virtualnetworks"),
    "nsg": ("microsoft.network", "networksecuritygroups"),
}
# Edges describe retirement prerequisites, not ARM creation dependencies.
DEPENDENCIES = {
    "vm": set(), "os_disk": {"vm"}, "nic": {"vm"}, "public_ip": {"nic"},
    "vnet": {"nic"}, "nsg": {"nic", "vnet"},
}
REASONS = frozenset("""creation-pending creation-uncertain retirement-pending
retirement-uncertain readback-unavailable identity-mismatch authority-missing
dependency-mismatch""".split())


def check(condition):
    require(condition, ERROR)


def closed(value, keys):
    check(type(value) is dict and set(value) == set(keys))


def ref(value):
    check(type(value) is str and REF.fullmatch(value) is not None)


def digest(value):
    check(type(value) is str and DIGEST.fullmatch(value) is not None)


def epoch(value):
    check(type(value) is int and 1 <= value <= 9007199254740991)


def document(raw):
    try:
        check(type(raw) is bytes and 0 < len(raw) <= LIMIT)
        value = decode_object(raw)
        check(canonical(value) == raw)
        return value
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise BindingError(ERROR) from None


def arm_key(path):
    check(type(path) is str and 0 < len(path) <= 1024)
    check(path.startswith("/") and not path.endswith("/"))
    check(all(33 <= ord(c) <= 126 and c not in "?#%\\" for c in path))
    parts = path[1:].split("/")
    check(all(p and p not in {".", ".."} for p in parts))
    check(len(parts) >= 4 and len(parts) % 2 == 0)
    check(parts[0].lower() == "subscriptions" and parts[2].lower() == "resourcegroups")
    check(UUID.fullmatch(parts[1].lower()) is not None)
    if len(parts) > 4:
        check(parts[4].lower() == "providers" and len(parts) >= 6)
    return path.lower()


def paths(value, *, minimum=0, maximum=24):
    check(type(value) is list and minimum <= len(value) <= maximum)
    keys = [arm_key(p) for p in value]
    check(keys == sorted(set(keys)))
    return keys


@dataclass(frozen=True)
class Record:
    raw: bytes = field(repr=False)

    @property
    def value(self):
        return document(self.raw)

    @property
    def digest(self):
        return byte_digest(self.raw)


def _envelope(value, phase):
    keys = COMMON if phase == "reservation" else COMMON | {
        "reservation_digest", "provisioning_readback_ref"}
    closed(value, keys)
    check(value["profile"] == ENVELOPE and value["phase"] == phase)
    for key in keys:
        if key.endswith("_ref"):
            ref(value[key])
        elif key.endswith("_digest"):
            digest(value[key])
    target = value["target"]
    closed(target, "tenant_id subscription_id region parent_paths".split())
    for name in ("tenant_id", "subscription_id"):
        check(type(target[name]) is str and UUID.fullmatch(target[name]) is not None)
    check(target["region"] == "westus")
    parents = paths(target["parent_paths"], minimum=1, maximum=8)
    for parent in parents:
        check(parent.split("/")[2] == target["subscription_id"])
    window = value["window"]
    closed(window, ("not_before", "not_after"))
    for stamp in window.values():
        epoch(stamp)
    check(0 < window["not_after"] - window["not_before"] <= 86400)
    resources = value["resources"]
    check(type(resources) is list and 1 <= len(resources) <= 24)
    selected = {}
    ordered = []
    for resource in resources:
        closed(resource, RESOURCE if phase == "reservation" else RESOURCE | CREATION)
        check(type(resource["kind"]) is str and resource["kind"] in KINDS)
        key = arm_key(resource["resource_path"])
        parts = key[1:].split("/")
        check(len(parts) == 8 and tuple(parts[5:7]) == KINDS[resource["kind"]])
        check(parts[1] == target["subscription_id"])
        check(any(parts[:len(p[1:].split("/"))] == p[1:].split("/") for p in parents))
        check(resource["disposition"] == "ephemeral")
        for name in ("resource_policy_ref", "create_attempt_ref"):
            ref(resource[name])
        if phase == "provisioned":
            for name in CREATION:
                ref(resource[name])
        dependency_keys = paths(resource["dependency_paths"], maximum=23)
        check(key not in dependency_keys)
        check(key not in selected)
        selected[key] = resource
        ordered.append(key)
    check(ordered == sorted(ordered))
    for key, resource in selected.items():
        for dependency in resource["dependency_paths"]:
            other = selected.get(arm_key(dependency))
            check(other is not None)
            check(other["kind"] in DEPENDENCIES[resource["kind"]])
            # Freeze the independently selected wire spelling as well as its key.
            check(dependency == other["resource_path"])
    visiting, done = set(), set()

    def visit(key):
        check(key not in visiting)
        if key in done:
            return
        visiting.add(key)
        for dependency in selected[key]["dependency_paths"]:
            visit(arm_key(dependency))
        visiting.remove(key)
        done.add(key)

    for key in selected:
        visit(key)


def reservation(raw, *, approved):
    value = document(raw)
    _envelope(value, "reservation")
    check(type(approved) is bytes and raw == approved)
    return Record(raw)


def provisioned(raw, *, reserved, authenticated_readback):
    check(type(reserved) is Record)
    before = reserved.value
    _envelope(before, "reservation")
    value = document(raw)
    _envelope(value, "provisioned")
    check(type(authenticated_readback) is bytes and raw == authenticated_readback)
    check(value["reservation_digest"] == reserved.digest)
    check({k: value[k] for k in COMMON - {"phase", "resources"}}
          == {k: before[k] for k in COMMON - {"phase", "resources"}})
    check([{k: resource[k] for k in RESOURCE} for resource in value["resources"]]
          == before["resources"])
    return Record(raw)


@dataclass(frozen=True)
class FinalAuthority:
    """Facts resolved outside this parser from actual accepted run/full authority."""
    now: int
    deadline: int
    expected: bytes = field(repr=False)


def _final(value):
    closed(value, """profile final_scope_ref deployment_ref provisioned_envelope_digest
selection_digest configuration_digest policy_digest case_ref source_commit run_id
run_attempt lease_ref authority_ref observed_at expires_at""".split())
    check(value["profile"] == FINAL)
    for key, item in value.items():
        if key.endswith("_ref"):
            ref(item)
        elif key.endswith("_digest"):
            digest(item)
    check(type(value["source_commit"]) is str
          and COMMIT.fullmatch(value["source_commit"]) is not None)
    check(type(value["run_id"]) is str and RUN.fullmatch(value["run_id"]) is not None)
    check(value["run_attempt"] == "1")
    epoch(value["observed_at"])
    epoch(value["expires_at"])
    check(0 < value["expires_at"] - value["observed_at"] <= 60)


def final_link(raw, *, deployed, authority):
    check(type(deployed) is Record and type(authority) is FinalAuthority)
    envelope = deployed.value
    _envelope(envelope, "provisioned")
    value = document(raw)
    _final(value)
    epoch(authority.now)
    epoch(authority.deadline)
    check(value["observed_at"] <= authority.now < value["expires_at"] <= authority.deadline)
    check(value["deployment_ref"] == envelope["deployment_ref"]
          and value["case_ref"] == envelope["case_ref"]
          and value["provisioned_envelope_digest"] == deployed.digest)
    check(type(authority.expected) is bytes and raw == authority.expected)
    return Record(raw)


@dataclass(frozen=True)
class RetirementAuthority:
    """Authenticated observation assessment, not reconstructed from receipt claims.

    No mutation callback or renewed cleanup/proof Decision is accepted here.
    """
    now: int
    observation_deadline: int
    cleanup_deadline: int
    authority_ref: str
    observation_authority_ref: str
    observer_ref: str
    preservation_digest: str
    preservation_observed: bool
    credentials_revoked: bool
    authenticated_results: bytes = field(repr=False)


def retirement(raw, *, reserved, authority, deployed=None, linked=None):
    check(type(reserved) is Record and type(authority) is RetirementAuthority)
    before = reserved.value
    _envelope(before, "reservation")
    value = document(raw)
    base = set("""profile phase deployment_ref namespace_ref owner_scope_ref
reservation_digest authority_ref observer_ref observation_authority_ref observed_at
expires_at outcome resource_results preservation_digest""".split())
    phase = value.get("phase")
    check(phase in ("setup", "run"))
    closed(value, base if phase == "setup" else base | {
        "provisioned_envelope_digest", "final_scope_ref"})
    check(value["profile"] == RETIREMENT)
    for key, item in value.items():
        if key.endswith("_ref"):
            ref(item)
        elif key.endswith("_digest"):
            digest(item)
    for key in ("deployment_ref", "namespace_ref", "owner_scope_ref"):
        check(value[key] == before[key])
    check(value["reservation_digest"] == reserved.digest)
    for key in ("authority_ref", "observation_authority_ref", "observer_ref"):
        ref(getattr(authority, key))
        check(value[key] == getattr(authority, key))
    digest(authority.preservation_digest)
    check(value["preservation_digest"] == authority.preservation_digest)
    check(type(authority.preservation_observed) is bool
          and type(authority.credentials_revoked) is bool)
    for stamp in (authority.now, authority.observation_deadline,
                  authority.cleanup_deadline, value["observed_at"], value["expires_at"]):
        epoch(stamp)
    check(value["observed_at"] <= authority.now < value["expires_at"]
          <= min(value["observed_at"] + 60, authority.observation_deadline))
    if phase == "setup":
        check(deployed is None and linked is None)
        check(authority.authority_ref == before["setup_authority_ref"])
    else:
        check(type(deployed) is Record and type(linked) is Record)
        after, link = deployed.value, linked.value
        provisioned(deployed.raw, reserved=reserved, authenticated_readback=deployed.raw)
        _final(link)
        check(after["reservation_digest"] == reserved.digest)
        check(after["deployment_ref"] == before["deployment_ref"])
        check(value["provisioned_envelope_digest"] == deployed.digest)
        check(link.get("profile") == FINAL
              and link.get("provisioned_envelope_digest") == deployed.digest
              and link.get("deployment_ref") == before["deployment_ref"]
              and link.get("case_ref") == before["case_ref"]
              and value["final_scope_ref"] == link.get("final_scope_ref"))
    results = value["resource_results"]
    check(type(authority.authenticated_results) is bytes
          and canonical(results) == authority.authenticated_results)
    check(type(results) is list and len(results) == len(before["resources"]))
    states = set()
    for resource, result in zip(before["resources"], results):
        check(type(result) is dict)
        state = result.get("state")
        if phase == "run":
            check(state != "not-created")
        common = {"resource_path", "kind", "create_attempt_ref", "state", "readback_ref"}
        known = {"incarnation_ref", "retirement_operation_ref"}
        if state == "not-created":
            closed(result, common)
        elif state == "absent":
            closed(result, common | known)
        else:
            check(state in ("failed", "pending", "indeterminate"))
            extra = set(result) - common - {"reason"}
            check(extra in (set(), {"incarnation_ref"}, known))
            closed(result, common | {"reason"} | extra)
            check(type(result["reason"]) is str and result["reason"] in REASONS)
        for key in ("resource_path", "kind", "create_attempt_ref"):
            check(result[key] == resource[key])
        for key, item in result.items():
            if key.endswith("_ref"):
                ref(item)
        if phase == "run" and "incarnation_ref" in result:
            expected_resource = next(r for r in after["resources"]
                                     if r["resource_path"] == result["resource_path"])
            check(result["incarnation_ref"] == expected_resource["incarnation_ref"])
        states.add(state)
    if authority.now >= authority.cleanup_deadline or "failed" in states:
        outcome = "failed"
    elif "indeterminate" in states:
        outcome = "indeterminate"
    elif "pending" in states:
        outcome = "pending"
    elif not (authority.preservation_observed and authority.credentials_revoked):
        outcome = "incomplete"
    else:
        outcome = "complete"
    check(value["outcome"] == outcome)
    return Record(raw)
