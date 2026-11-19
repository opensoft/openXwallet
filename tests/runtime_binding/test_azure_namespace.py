"""Synthetic approved facts and a durable conditional Blob-port double; no cloud I/O."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
import copy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading

import pytest
from workload_factory_binding.evidence import BindingError, canonical
from workload_factory_binding_runtime.azure_composition import selection as s
from workload_factory_binding_runtime.azure_composition.namespace import INDEX, Namespace, Snapshot
from workload_factory_binding_runtime.github_bootstrap.common import Decision

NOW = 1000000
SUB = "11111111-1111-1111-1111-111111111111"
TENANT = "22222222-2222-2222-2222-222222222222"
PARENT = "/subscriptions/" + SUB + "/resourceGroups/pilot-qa"
TYPES = {
    "vm": ("Microsoft.Compute", "virtualMachines"),
    "os_disk": ("Microsoft.Compute", "disks"),
    "nic": ("Microsoft.Network", "networkInterfaces"),
    "public_ip": ("Microsoft.Network", "publicIPAddresses"),
    "vnet": ("Microsoft.Network", "virtualNetworks"),
    "nsg": ("Microsoft.Network", "networkSecurityGroups"),
}
PATHS = {kind: PARENT + "/providers/" + provider + "/" + typ + "/pilot-" + kind.replace("_", "-")
         for kind, (provider, typ) in TYPES.items()}
CREATED = {"incarnation_ref": "incarnation:one", "create_operation_ref": "create:one",
           "creation_readback_ref": "readback:create-one"}


def vector():
    deps = {"vm": [], "os_disk": [PATHS["vm"]], "nic": [PATHS["vm"]],
            "public_ip": [PATHS["nic"]], "vnet": [PATHS["nic"]],
            "nsg": [PATHS["nic"], PATHS["vnet"]]}
    resources = [{"resource_path": path, "kind": kind,
                  "dependency_paths": sorted(deps[kind], key=str.lower),
                  "resource_policy_ref": "policy:" + kind, "create_attempt_ref": "create:" + kind,
                  "disposition": "ephemeral"} for kind, path in PATHS.items()]
    return {"profile": s.ENVELOPE, "phase": "reservation", "deployment_ref": "deployment:one",
            "owner_scope_ref": "owner:one", "namespace_ref": "namespace:one",
            "namespace_generation_ref": "namespace-generation:one", "case_ref": "case:one",
            "source_roles_digest": "sha256:" + "a" * 64, "build_recipe_ref": "build:one",
            "target": {"tenant_id": TENANT, "subscription_id": SUB, "region": "westus",
                       "parent_paths": [PARENT]},
            "resources": sorted(resources, key=lambda r: r["resource_path"].lower()),
            "retained_scope_ref": "preserve:one", "window": {"not_before": NOW - 10,
            "not_after": NOW + 600}, "setup_authority_ref": "setup:one"}


def reserved(value=None):
    raw = canonical(vector() if value is None else value)
    return s.reservation(raw, approved=raw)


def deployed(r):
    v = r.value
    v.update(phase="provisioned", reservation_digest=r.digest,
             provisioning_readback_ref="readback:provisioning")
    v["resources"] = [{**x, **CREATED} for x in v["resources"]]
    raw = canonical(v)
    return s.provisioned(raw, reserved=r, authenticated_readback=raw)


def linked(d):
    raw = canonical({"profile": s.FINAL, "final_scope_ref": "final:one",
                     "deployment_ref": "deployment:one", "provisioned_envelope_digest": d.digest,
                     "selection_digest": "sha256:" + "b" * 64,
                     "configuration_digest": "sha256:" + "c" * 64,
                     "policy_digest": "sha256:" + "d" * 64,
                     "case_ref": "case:one", "source_commit": "a" * 40, "run_id": "765",
                     "run_attempt": "1", "lease_ref": "lease:one", "authority_ref": "run:one",
                     "observed_at": NOW, "expires_at": NOW + 60})
    return s.final_link(raw, deployed=d, authority=s.FinalAuthority(NOW, NOW + 60, raw))


def receipt(r, *, run=False):
    d = deployed(r) if run else None
    link = linked(d) if run else None
    results = [{"resource_path": x["resource_path"], "kind": x["kind"],
                "create_attempt_ref": x["create_attempt_ref"], "state": "not-created",
                "readback_ref": "readback:not-sent"} for x in r.value["resources"]]
    if run:
        results = [{**x, "state": "absent", "incarnation_ref": CREATED["incarnation_ref"],
                    "retirement_operation_ref": "retirement:one"} for x in results]
    value = {"profile": s.RETIREMENT, "phase": "run" if run else "setup",
             "deployment_ref": "deployment:one", "namespace_ref": "namespace:one",
             "owner_scope_ref": "owner:one", "reservation_digest": r.digest,
             "authority_ref": "run-cleanup:one" if run else "setup:one",
             "observer_ref": "observer:one", "observation_authority_ref": "observation:one",
             "observed_at": NOW, "expires_at": NOW + 60, "outcome": "complete",
             "resource_results": results, "preservation_digest": "sha256:" + "e" * 64}
    if run:
        value.update(provisioned_envelope_digest=d.digest, final_scope_ref="final:one")
    authority = s.RetirementAuthority(NOW, NOW + 60, NOW + 100,
        value["authority_ref"], "observation:one", "observer:one",
        value["preservation_digest"], True, True, canonical(results))
    return value, authority, d, link


def decision(now=NOW):
    return Decision(clock=lambda: now, monotonic=lambda: 10.0)


class Store:
    """Test-only SQLite-backed stand-in for authenticated Blob conditional writes."""
    def __init__(self, path, *, initialize=False, initial=None):
        self.path, self.events, self.fault, self.read_hook = path, [], None, None
        if initialize:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            with closing(sqlite3.connect(path)) as db:
                db.execute("CREATE TABLE blobs (name TEXT PRIMARY KEY, revision INTEGER, body BLOB)")
                db.execute("INSERT INTO blobs VALUES (?,1,?)", (INDEX, canonical(initial)))
                db.commit()

    def read(self, key, *, timeout):
        assert timeout > 0
        with closing(sqlite3.connect(self.path, timeout=5)) as db:
            row = db.execute("SELECT revision,body FROM blobs WHERE name=?", (key,)).fetchone()
        self.events.append(("read", key))
        if row is None:
            raise LookupError("private-storage-detail")
        value = Snapshot(str(row[0]), row[1])
        if self.read_hook:
            self.read_hook(key)
        return value

    def _mutate(self, key, raw, etag, op):
        self.events.append((op, key))
        if self.fault == (op, key, "before"):
            raise TimeoutError("private-before-send")
        with closing(sqlite3.connect(self.path, timeout=5)) as db:
            db.execute("BEGIN IMMEDIATE")
            if op == "create_only":
                db.execute("INSERT INTO blobs VALUES (?,1,?)", (key, raw))
            else:
                changed = db.execute("UPDATE blobs SET revision=revision+1,body=? "
                                     "WHERE name=? AND revision=?", (raw, key, int(etag)))
                if changed.rowcount != 1:
                    raise RuntimeError("private-etag-conflict")
            db.commit()
        if self.fault == (op, key, "after"):
            raise TimeoutError("private-response-lost-after-commit")
        return self.read(key, timeout=5)

    def create_only(self, key, raw, *, timeout):
        assert timeout > 0
        return self._mutate(key, raw, None, "create_only")

    def replace(self, key, raw, *, etag, timeout):
        assert timeout > 0
        return self._mutate(key, raw, etag, "replace")

    def remove(self, key):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DELETE FROM blobs WHERE name=?", (key,))
            db.commit()

    def corrupt(self, key, raw):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE blobs SET body=? WHERE name=?", (raw, key))
            db.commit()


def service(store, r):
    v = r.value
    return Namespace(store=store, namespace_ref=v["namespace_ref"],
                     generation_ref=v["namespace_generation_ref"],
                     owner_scope_ref=v["owner_scope_ref"],
                     resource_paths=tuple(x["resource_path"] for x in v["resources"]))


@pytest.fixture
def fixture(tmp_path):
    r = reserved()
    v = r.value
    initial = {"namespace_ref": v["namespace_ref"], "namespace_generation_ref":
               v["namespace_generation_ref"], "owner_scope_ref": v["owner_scope_ref"],
               "resource_keys": [s.arm_key(x["resource_path"]) for x in v["resources"]],
               "phase": "unused"}
    store = Store(tmp_path / "conditional.db", initialize=True, initial=initial)
    return r, store, service(store, r)


def reject(function, *args, **kwargs):
    with pytest.raises(BindingError) as error:
        function(*args, **kwargs)
    assert str(error.value) in {s.ERROR, "azure-namespace-refused"}
    assert error.value.__cause__ is None


def test_independent_closed_vectors_cover_all_record_phases():
    r = reserved()
    d = deployed(r)
    link = linked(d)
    assert link.value["provisioned_envelope_digest"] == d.digest
    assert not (set(r.value) & {"selection_digest", "configuration_digest", "run_id"})
    for run in (False, True):
        v, a, actual, final = receipt(r, run=run)
        out = s.retirement(canonical(v), reserved=r, authority=a, deployed=actual, linked=final)
        assert out.value["outcome"] == "complete"
    detached = r.value
    detached["target"]["region"] = "foreign"
    assert r.value["target"]["region"] == "westus"


@pytest.mark.parametrize("key", sorted(s.COMMON))
def test_missing_reservation_member_refuses_even_when_expected_matches(key):
    v = vector()
    del v[key]
    raw = canonical(v)
    reject(s.reservation, raw, approved=raw)


@pytest.mark.parametrize("key", ["incarnation_ref", "reservation_digest", "selection_digest",
    "configuration_digest", "policy_digest", "run_id", "run_attempt", "lease_ref",
    "final_scope_ref", "create_operation_ref"])
def test_unavailable_early_facts_refuse(key):
    v = vector()
    v[key] = "not-yet-available"
    raw = canonical(v)
    reject(s.reservation, raw, approved=raw)


@pytest.mark.parametrize("raw", [b'{}', b'{"profile":1,"profile":2}', b'\xef\xbb\xbf{}',
    b'{"x":NaN}', b'{"x":Infinity}', b'\xff', b'[]', b'null', b' {} ', b'{"z":1,"a":2}'])
def test_noncanonical_duplicate_or_nonobject_input_refuses(raw):
    reject(s.reservation, raw, approved=raw)


@pytest.mark.parametrize("value", [True, False, 0, -1, 1.0, "1000000", None, 2**53])
def test_epoch_types_and_bounds_refuse(value):
    v = vector()
    v["window"]["not_before"] = value
    raw = json.dumps(v, sort_keys=True, separators=(",", ":")).encode()
    reject(s.reservation, raw, approved=raw)


@pytest.mark.parametrize("change", ["foreign-owner", "foreign-source", "foreign-policy",
    "foreign-attempt", "omitted-resource", "reordered", "unapproved-retained-scope"])
def test_independently_approved_full_selection_cannot_be_rebound(change):
    v = vector()
    if change == "foreign-owner":
        v["owner_scope_ref"] = "owner:other"
    elif change == "foreign-source":
        v["source_roles_digest"] = "sha256:" + "b" * 64
    elif change == "foreign-policy":
        v["resources"][0]["resource_policy_ref"] = "policy:other"
    elif change == "foreign-attempt":
        v["resources"][0]["create_attempt_ref"] = "attempt:other"
    elif change == "omitted-resource":
        v["resources"].pop()
    elif change == "reordered":
        v["resources"].reverse()
    else:
        v["retained_scope_ref"] = "preserve:other"
    reject(s.reservation, canonical(v), approved=canonical(vector()))


@pytest.mark.parametrize("suffix", ["/", "//", "/.", "/..", "?x=1", "#x", "%2fextra",
    "\\extra", "/../x", "\n", " ", "/providers/Microsoft.Compute/virtualMachines/extra"])
def test_resource_path_aliases_and_nested_wrong_kind_refuse(suffix):
    v = vector()
    v["resources"][0]["resource_path"] += suffix
    raw = canonical(v)
    reject(s.reservation, raw, approved=raw)


@pytest.mark.parametrize("mutation", ["foreign-subscription", "parent-prefix", "duplicate-case",
    "wrong-provider", "wrong-kind", "foreign-dependency", "self-dependency",
    "cycle", "dependency-case-alias", "unsorted-parents", "retained-disposition"])
def test_resource_allowlist_parent_and_dependency_constraints(mutation):
    v = vector()
    x = v["resources"][0]
    if mutation == "foreign-subscription":
        x["resource_path"] = x["resource_path"].replace(SUB, TENANT)
    elif mutation == "parent-prefix":
        x["resource_path"] = x["resource_path"].replace("pilot-qa/", "pilot-qa-other/")
    elif mutation == "duplicate-case":
        v["resources"].append({**x, "resource_path": x["resource_path"].upper()})
    elif mutation == "wrong-provider":
        x["resource_path"] = x["resource_path"].replace("Microsoft.Compute", "Microsoft.Network")
    elif mutation == "wrong-kind":
        x["kind"] = "resource_group"
    elif mutation == "foreign-dependency":
        x["dependency_paths"] = [PATHS["vm"] + "-foreign"]
    elif mutation == "self-dependency":
        x["dependency_paths"] = [x["resource_path"]]
    elif mutation == "cycle":
        vm = next(y for y in v["resources"] if y["kind"] == "vm")
        vm["dependency_paths"] = [PATHS["os_disk"]]
    elif mutation == "dependency-case-alias":
        nic = next(y for y in v["resources"] if y["kind"] == "nic")
        nic["dependency_paths"] = [PATHS["vm"].upper()]
    elif mutation == "unsorted-parents":
        v["target"]["parent_paths"] *= 2
    else:
        x["disposition"] = "retained"
    raw = canonical(v)
    reject(s.reservation, raw, approved=raw)


@pytest.mark.parametrize("size", [0, 25, 24])
def test_resource_count_and_complete_document_cap(size):
    v = vector()
    long_name = "x" * 850 if size == 24 else "vm"
    v["resources"] = [{"resource_path": PARENT + "/providers/Microsoft.Compute/virtualMachines/"
                      + long_name + str(i).zfill(2), "kind": "vm", "dependency_paths": [],
                      "resource_policy_ref": "policy:vm", "create_attempt_ref": "attempt:" + str(i),
                      "disposition": "ephemeral"} for i in range(size)]
    raw = canonical(v)
    if size == 24:
        assert len(raw) > s.LIMIT
    reject(s.reservation, raw, approved=raw)


@pytest.mark.parametrize("mutation", ["omitted", "added", "owner", "policy", "attempt",
                                     "dependencies", "phase", "backward-link", "wrong-digest"])
def test_provisioning_preserves_exact_ordered_six_field_projection(mutation):
    r = reserved()
    v = deployed(r).value
    if mutation == "omitted":
        v["resources"].pop()
    elif mutation == "added":
        v["resources"].append(copy.deepcopy(v["resources"][0]))
    elif mutation == "owner":
        v["owner_scope_ref"] = "owner:other"
    elif mutation == "policy":
        v["resources"][0]["resource_policy_ref"] = "policy:other"
    elif mutation == "attempt":
        v["resources"][0]["create_attempt_ref"] = "attempt:other"
    elif mutation == "dependencies":
        v["resources"][0]["dependency_paths"] = []
    elif mutation == "phase":
        v["phase"] = "reservation"
    elif mutation == "backward-link":
        v["selection_digest"] = "sha256:" + "a" * 64
    else:
        v["reservation_digest"] = "sha256:" + "0" * 64
    raw = canonical(v)
    reject(s.provisioned, raw, reserved=r, authenticated_readback=raw)


@pytest.mark.parametrize("key,value", [("run_attempt", "2"), ("run_id", "0"),
    ("run_id", 765), ("source_commit", "A" * 40), ("observed_at", NOW + 1),
    ("expires_at", NOW), ("expires_at", NOW + 61),
    ("provisioned_envelope_digest", "sha256:" + "0" * 64),
    ("deployment_ref", "deployment:other"), ("case_ref", "case:other")])
def test_final_link_closed_actual_scope_and_earliest_deadline(key, value):
    d = deployed(reserved())
    v = linked(d).value
    v[key] = value
    raw = canonical(v)
    reject(s.final_link, raw, deployed=d, authority=s.FinalAuthority(NOW, NOW + 60, raw))


def test_final_selection_cannot_replace_independently_approved_full_bytes():
    d = deployed(reserved())
    original = linked(d).raw
    v = json.loads(original)
    v["configuration_digest"] = "sha256:" + "f" * 64
    reject(s.final_link, canonical(v), deployed=d,
           authority=s.FinalAuthority(NOW, NOW + 60, original))


@pytest.mark.parametrize("phase", [False, True], ids=["setup", "run"])
@pytest.mark.parametrize("mutation", ["extra", "missing", "unknown-result", "null-incarnation",
    "operation-without-incarnation", "wrong-attempt", "wrong-incarnation", "duplicate-result",
    "absent-without-operation", "extra-final-facts", "partial-link"])
def test_retirement_variants_refuse_unavailable_or_rebound_facts(phase, mutation):
    r = reserved()
    v, a, d, link = receipt(r, run=phase)
    first = v["resource_results"][0]
    if mutation == "extra":
        v["secret"] = "private"
    elif mutation == "missing":
        del v["observer_ref"]
    elif mutation == "unknown-result":
        first["state"] = "success"
    elif mutation == "null-incarnation":
        first["incarnation_ref"] = None
    elif mutation == "operation-without-incarnation":
        first.update(state="pending", reason="retirement-pending",
                     retirement_operation_ref="operation:one")
        first.pop("incarnation_ref", None)
    elif mutation == "wrong-attempt":
        first["create_attempt_ref"] = "attempt:other"
    elif mutation == "wrong-incarnation":
        first["incarnation_ref"] = "incarnation:other"
    elif mutation == "duplicate-result":
        v["resource_results"][1] = copy.deepcopy(first)
    elif mutation == "absent-without-operation":
        first["state"] = "absent"
        first.pop("retirement_operation_ref", None)
    elif mutation == "extra-final-facts":
        v["run_id"] = "765"
    else:
        if not phase:
            v["final_scope_ref"] = "final:one"
        else:
            link = s.Record(canonical({"profile": s.FINAL,
                "provisioned_envelope_digest": d.digest, "deployment_ref": "deployment:one",
                "case_ref": "case:one", "final_scope_ref": "final:one"}))
    # Keep this oracle in agreement to exercise grammar, not just byte mismatch.
    a = replace(a, authenticated_results=canonical(v["resource_results"]))
    reject(s.retirement, canonical(v), reserved=r, authority=a, deployed=d, linked=link)


@pytest.mark.parametrize("state,expected", [("pending", "pending"), ("indeterminate", "indeterminate"),
                                         ("failed", "failed")])
@pytest.mark.parametrize("known", [0, 1, 2])
def test_truthful_partial_setup_without_invented_run_or_provider_facts(state, expected, known):
    r = reserved()
    v, a, _, _ = receipt(r)
    first = v["resource_results"][0]
    first.update(state=state, reason="creation-uncertain")
    if known:
        first["incarnation_ref"] = "incarnation:one"
    if known == 2:
        first["retirement_operation_ref"] = "operation:original"
    v["outcome"] = expected
    a = replace(a, authenticated_results=canonical(v["resource_results"]))
    assert s.retirement(canonical(v), reserved=r, authority=a).value["outcome"] == expected


def test_current_read_only_late_observation_fails_without_renewal_or_mutation():
    r = reserved()
    v, a, _, _ = receipt(r)
    old_decision = decision()
    deadline = old_decision.deadline
    a = replace(a, now=NOW + 120, observation_deadline=NOW + 150,
                cleanup_deadline=NOW + 100)
    v.update(observed_at=NOW + 120, expires_at=NOW + 150, outcome="failed")
    result = s.retirement(canonical(v), reserved=r, authority=a)
    assert result.value["outcome"] == "failed"
    assert old_decision.deadline == deadline
    v["outcome"] = "complete"
    reject(s.retirement, canonical(v), reserved=r, authority=a)


@pytest.mark.parametrize("mutation", ["expired-observer", "future-observation", "wrong-observer",
    "wrong-observation-authority", "wrong-original-authority", "missing-preservation",
    "not-revoked", "boolean-lie", "unobserved-results"])
def test_retirement_requires_current_independent_observation_and_derived_outcome(mutation):
    r = reserved()
    v, a, _, _ = receipt(r)
    if mutation == "expired-observer":
        a = replace(a, observation_deadline=NOW)
    elif mutation == "future-observation":
        v["observed_at"] = NOW + 1
    elif mutation == "wrong-observer":
        v["observer_ref"] = "observer:worker"
    elif mutation == "wrong-observation-authority":
        v["observation_authority_ref"] = "observation:worker"
    elif mutation == "wrong-original-authority":
        v["authority_ref"] = "setup:worker"
    elif mutation == "missing-preservation":
        a = replace(a, preservation_observed=False)
    elif mutation == "not-revoked":
        a = replace(a, credentials_revoked=False)
    elif mutation == "boolean-lie":
        a = replace(a, credentials_revoked=1)
    else:
        a = replace(a, authenticated_results=canonical([]))
    reject(s.retirement, canonical(v), reserved=r, authority=a)


def test_conditional_reservation_admission_and_permanent_tombstone(fixture):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    path = PATHS["vm"]
    assert ns.read(r, path, decision=decision()).value["state"] == "reserved"
    ns.consume_create(r, path, attempt_ref="create:vm", decision=decision())
    ns.transition(r, path, state="admitted", observation_ref="observed:create",
                  creation=CREATED, decision=decision())
    ns.transition(r, path, state="retiring", observation_ref="observed:retire",
                  retirement_attempt_ref="retire:one", decision=decision())
    ns.transition(r, path, state="absent-tombstoned", observation_ref="observed:absent",
                  decision=decision())
    restarted = service(Store(store.path), r)
    assert restarted.read(r, path, decision=decision(NOW + 900)).value["state"] == "absent-tombstoned"
    catalog_before = store.read(INDEX, timeout=1).raw
    event_count = len(store.events)
    reject(restarted.reserve, r, approved=r.raw, decision=decision())
    assert store.read(INDEX, timeout=1).raw == catalog_before
    assert all(op == "read" for op, _ in store.events[event_count:])
    reject(restarted.consume_create, r, path, attempt_ref="create:vm", decision=decision())
    assert not hasattr(ns, "initialize")
    assert not hasattr(ns, "delete")


def test_all_resources_must_be_admitted_before_provisioned_form(fixture):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    d = deployed(r)
    reject(ns.provisioned, d.raw, reserved=r, authenticated_readback=d.raw, decision=decision())
    for resource in r.value["resources"]:
        path = resource["resource_path"]
        ns.consume_create(r, path, attempt_ref=resource["create_attempt_ref"], decision=decision())
        ns.transition(r, path, state="admitted", observation_ref="observed:create",
                      creation=CREATED, decision=decision())
    assert ns.provisioned(d.raw, reserved=r, authenticated_readback=d.raw,
                          decision=decision()).raw == d.raw
    altered = copy.deepcopy(d.value)
    altered["resources"][0]["incarnation_ref"] = "incarnation:replacement"
    raw = canonical(altered)
    reject(ns.provisioned, raw, reserved=r, authenticated_readback=raw, decision=decision())


@pytest.mark.parametrize("operation", ["reservation", "consume"])
def test_etag_concurrency_has_one_winner_without_write_retry(fixture, operation):
    r, store, ns = fixture
    path = PATHS["vm"]
    if operation == "consume":
        ns.reserve(r, approved=r.raw, decision=decision())
    target = INDEX if operation == "reservation" else s.arm_key(path)
    barrier, lock = threading.Barrier(12), threading.Lock()
    count = 0

    def hook(key):
        nonlocal count
        if key == target:
            with lock:
                count += 1
                wait = count <= 12
            if wait:
                barrier.wait(timeout=10)

    store.read_hook = hook

    def contender(_):
        try:
            if operation == "reservation":
                service(store, r).reserve(r, approved=r.raw, decision=decision())
            else:
                service(store, r).consume_create(r, path, attempt_ref="create:vm", decision=decision())
            return True
        except BindingError:
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = list(pool.map(contender, range(12)))
    store.read_hook = None
    assert outcomes.count(True) == 1
    assert store.read(target, timeout=1).raw
    assert not any(op in {"delete", "reset"} for op, _ in store.events)


@pytest.mark.parametrize("when", ["before", "after"])
def test_lost_consume_response_never_replays_provider_attempt(fixture, when):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    path, key = PATHS["vm"], s.arm_key(PATHS["vm"])
    store.fault = ("replace", key, when)
    reject(ns.consume_create, r, path, attempt_ref="create:vm", decision=decision())
    attempts = store.events.count(("replace", key))
    store.fault = None
    current = service(Store(store.path), r).read(r, path, decision=decision()).value
    if when == "after":
        assert current["state"] == "create-consumed"
        reject(ns.consume_create, r, path, attempt_ref="create:vm", decision=decision())
        assert store.events.count(("replace", key)) == attempts
    else:
        assert current["state"] == "reserved"
    # A rejected/ambiguous call supplies no permit for a provider send.


def test_real_process_death_after_durable_consume_cannot_reopen_attempt(fixture):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    source = str(Path(__file__).resolve().parents[2] / "scripts")
    code = """
import json,sqlite3,sys,os
from contextlib import closing
sys.path.insert(0,sys.argv[1])
from workload_factory_binding_runtime.azure_composition.namespace import Namespace,Snapshot
from workload_factory_binding_runtime.azure_composition.selection import reservation
from workload_factory_binding_runtime.github_bootstrap.common import Decision
class Port:
 def read(self,key,*,timeout):
  with closing(sqlite3.connect(sys.argv[2])) as d:
   x=d.execute('SELECT revision,body FROM blobs WHERE name=?',(key,)).fetchone()
  return Snapshot(str(x[0]),x[1])
 def replace(self,key,raw,*,etag,timeout):
  with closing(sqlite3.connect(sys.argv[2])) as d:
   changed=d.execute('UPDATE blobs SET revision=revision+1,body=? WHERE name=? AND revision=?',(raw,key,int(etag)))
   assert changed.rowcount==1
   d.commit()
  return self.read(key,timeout=timeout)
raw=sys.argv[3].encode();r=reservation(raw,approved=raw);v=r.value
n=Namespace(store=Port(),namespace_ref=v['namespace_ref'],generation_ref=v['namespace_generation_ref'],owner_scope_ref=v['owner_scope_ref'],resource_paths=tuple(x['resource_path'] for x in v['resources']))
n.consume_create(r,sys.argv[4],attempt_ref='create:vm',decision=Decision(clock=lambda:1000000,monotonic=lambda:10.0))
os._exit(23)
"""
    result = subprocess.run([sys.executable, "-I", "-B", "-c", code, source,
                             str(store.path), r.raw.decode(), PATHS["vm"]],
                            capture_output=True, timeout=15)
    assert result.returncode == 23, result.stderr.decode()
    restarted = service(Store(store.path), r)
    assert restarted.read(r, PATHS["vm"], decision=decision()).value["state"] == "create-consumed"
    reject(restarted.consume_create, r, PATHS["vm"], attempt_ref="create:vm", decision=decision())


def test_partial_reservation_crash_quarantines_complete_name_set(fixture):
    r, store, ns = fixture
    second = s.arm_key(r.value["resources"][1]["resource_path"])
    store.fault = ("create_only", second, "before")
    reject(ns.reserve, r, approved=r.raw, decision=decision())
    assert json.loads(store.read(INDEX, timeout=1).raw)["phase"] == "preparing"
    attempts = len([x for x in store.events if x[0] != "read"])
    store.fault = None
    reject(service(store, r).reserve, r, approved=r.raw, decision=decision())
    reject(ns.consume_create, r, PATHS["vm"], attempt_ref="create:vm", decision=decision())
    assert len([x for x in store.events if x[0] != "read"]) == attempts


@pytest.mark.parametrize("target", ["index", "resource"])
def test_missing_expected_state_never_initializes_or_frees_names(fixture, target):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    store.remove(INDEX if target == "index" else s.arm_key(PATHS["vm"]))
    events = len(store.events)
    reject(service(store, r).read, r, PATHS["vm"], decision=decision())
    reject(service(store, r).reserve, r, approved=r.raw, decision=decision())
    assert all(op == "read" for op, _ in store.events[events:])


@pytest.mark.parametrize("mutation", ["generation", "owner", "paths", "noncanonical", "extra"])
def test_initialized_namespace_identity_and_corruption_refuse(fixture, mutation):
    r, store, ns = fixture
    index = json.loads(store.read(INDEX, timeout=1).raw)
    if mutation == "generation":
        index["namespace_generation_ref"] = "namespace-generation:replacement"
    elif mutation == "owner":
        index["owner_scope_ref"] = "owner:other"
    elif mutation == "paths":
        index["resource_keys"].pop()
    elif mutation == "extra":
        index["reset"] = True
    raw = canonical(index)
    if mutation == "noncanonical":
        raw += b" "
    store.corrupt(INDEX, raw)
    reject(ns.reserve, r, approved=r.raw, decision=decision())


def test_expired_and_case_variant_consumption_do_not_send_or_renew(fixture):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    old = decision()
    deadline = old.deadline
    reject(ns.consume_create, r, PATHS["vm"].upper(), attempt_ref="create:vm", decision=old)
    assert old.deadline == deadline
    late = decision(NOW + 601)
    reject(ns.consume_create, r, PATHS["vm"], attempt_ref="create:vm", decision=late)
    reject(ns.consume_create, r, PATHS["vm"], attempt_ref="create:other", decision=decision())
    assert ns.read(r, PATHS["vm"], decision=decision()).value["state"] == "reserved"


def test_ambiguous_retirement_keeps_original_attempt_and_cannot_resend(fixture):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    path = PATHS["vm"]
    ns.consume_create(r, path, attempt_ref="create:vm", decision=decision())
    ns.transition(r, path, state="admitted", observation_ref="observed:create",
                  creation=CREATED, decision=decision())
    ns.transition(r, path, state="retiring", observation_ref="observed:retire",
                  retirement_attempt_ref="retire:one", decision=decision())
    ns.transition(r, path, state="quarantined", observation_ref="observed:uncertain",
                  decision=decision())
    reject(ns.transition, r, path, state="retiring", observation_ref="observed:retry",
           retirement_attempt_ref="retire:two", decision=decision())
    reject(ns.transition, r, path, state="admitted", observation_ref="observed:reset",
           creation=CREATED, decision=decision())
    assert ns.read(r, path, decision=decision()).value["retirement_attempt_ref"] == "retire:one"


def test_readback_generation_cannot_change_and_tombstone_cannot_be_released(fixture):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    path = PATHS["vm"]
    ns.consume_create(r, path, attempt_ref="create:vm", decision=decision())
    ns.transition(r, path, state="admitted", observation_ref="observed:create",
                  creation=CREATED, decision=decision())
    reject(ns.transition, r, path, state="quarantined", observation_ref="observed:changed",
           creation={**CREATED, "incarnation_ref": "incarnation:replacement"}, decision=decision())
    ns.transition(r, path, state="quarantined", observation_ref="observed:uncertain",
                  decision=decision())
    ns.transition(r, path, state="absent-tombstoned", observation_ref="observed:absent",
                  decision=decision())
    for state in ("reserved", "create-consumed", "admitted", "retiring"):
        reject(ns.transition, r, path, state=state, observation_ref="observed:retry",
               creation=CREATED, retirement_attempt_ref="retire:two", decision=decision())


def test_run_retirement_cannot_claim_provisioned_resources_were_never_created():
    r = reserved()
    v, a, d, link = receipt(r, run=True)
    for result in v["resource_results"]:
        result["state"] = "not-created"
        del result["incarnation_ref"]
        del result["retirement_operation_ref"]
    a = replace(a, authenticated_results=canonical(v["resource_results"]))
    reject(s.retirement, canonical(v), reserved=r, authority=a, deployed=d, linked=link)


def test_unconsumed_name_cannot_invent_creation_before_tombstoning(fixture):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    reject(ns.transition, r, PATHS["vm"], state="absent-tombstoned",
           observation_ref="observed:foreign", creation=CREATED, decision=decision())
    assert ns.read(r, PATHS["vm"], decision=decision()).value["state"] == "reserved"


@pytest.mark.parametrize("preservation,revoked", [(False, True), (True, False), (False, False)])
def test_incomplete_preservation_and_revocation_emit_honest_incomplete(preservation, revoked):
    r = reserved()
    v, a, _, _ = receipt(r)
    a = replace(a, preservation_observed=preservation, credentials_revoked=revoked)
    v["outcome"] = "incomplete"
    assert s.retirement(canonical(v), reserved=r, authority=a).value["outcome"] == "incomplete"


def test_cleanup_deadline_is_exclusive_even_with_current_read_only_observer():
    r = reserved()
    v, a, _, _ = receipt(r)
    a = replace(a, cleanup_deadline=NOW)
    reject(s.retirement, canonical(v), reserved=r, authority=a)
    v["outcome"] = "failed"
    assert s.retirement(canonical(v), reserved=r, authority=a).value["outcome"] == "failed"


def test_nested_storage_read_cannot_reset_original_decision_or_mutate_after_deadline(fixture):
    r, store, ns = fixture
    stamps = [NOW, 10.0]
    original = Decision(clock=lambda: stamps[0], monotonic=lambda: stamps[1])
    end = original.deadline

    def expire(_):
        stamps[0] += 11
        stamps[1] += 11

    store.read_hook = expire
    reject(ns.reserve, r, approved=r.raw, decision=original)
    assert original.deadline == end
    assert store.events == [("read", INDEX)]


@pytest.mark.parametrize("encoding", ["leading-space", "pretty", "unsorted"])
def test_valid_record_noncanonical_serializations_refuse(encoding):
    value = vector()
    if encoding == "leading-space":
        raw = b" " + canonical(value)
    elif encoding == "pretty":
        raw = json.dumps(value, sort_keys=True, indent=2).encode()
    else:
        raw = json.dumps(value, separators=(",", ":")).encode()
    reject(s.reservation, raw, approved=raw)


def test_namespace_setup_not_before_is_enforced_before_storage(fixture):
    r, store, ns = fixture
    reject(ns.reserve, r, approved=r.raw, decision=decision(NOW - 11))
    assert store.events == []


def change_admission_view(store, ns, r, resources, interleaving):
    first = resources[0]["resource_path"]
    if interleaving == "split-admission":
        ns.transition(r, first, state="retiring", observation_ref="observed:retire",
                      retirement_attempt_ref="retire:one", decision=decision())
        for resource in resources[1:]:
            ns.transition(r, resource["resource_path"], state="admitted",
                          observation_ref="observed:create", creation=CREATED, decision=decision())
    elif interleaving == "aba":
        # Restore identical bytes through legal transitions; only the revision changes.
        ns.transition(r, first, state="quarantined", observation_ref="observed:uncertain",
                      decision=decision())
        ns.transition(r, first, state="admitted", observation_ref="observed:create",
                      decision=decision())
    elif interleaving == "missing":
        store.remove(s.arm_key(first))
    else:
        value = json.loads(store.read(s.arm_key(first), timeout=1).raw)
        value["observation_ref"] = "observed:changed"
        store.corrupt(s.arm_key(first), canonical(value))


@pytest.mark.parametrize("interleaving", ["split-admission", "aba", "missing", "changed-bytes"])
def test_provisioned_requires_one_consistent_admitted_set(fixture, interleaving):
    r, store, ns = fixture
    ns.reserve(r, approved=r.raw, decision=decision())
    resources = r.value["resources"]
    first, last = resources[0]["resource_path"], resources[-1]["resource_path"]
    for resource in resources:
        path = resource["resource_path"]
        ns.consume_create(r, path, attempt_ref=resource["create_attempt_ref"], decision=decision())
        if interleaving != "split-admission" or path == first:
            ns.transition(r, path, state="admitted", observation_ref="observed:create",
                          creation=CREATED, decision=decision())
    d = deployed(r)
    mutations = []
    trigger = first if interleaving in ("split-admission", "aba") else last

    def change_after_snapshot(key):
        if key != s.arm_key(trigger):
            return
        store.read_hook = None
        change_admission_view(store, ns, r, resources, interleaving)
        mutations.extend(store.events)
        store.events.clear()

    store.read_hook = change_after_snapshot
    reject(ns.provisioned, d.raw, reserved=r, authenticated_readback=d.raw, decision=decision())
    assert mutations, "the deterministic concurrent change must actually run"
    assert all(op == "read" for op, _ in store.events)
    store.read_hook = None
    if interleaving == "split-admission":
        assert ns.read(r, first, decision=decision()).value["state"] == "retiring"
        assert all(ns.read(r, x["resource_path"], decision=decision()).value["state"] == "admitted"
                   for x in resources[1:])
