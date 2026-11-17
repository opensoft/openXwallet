"""Explicit hosted registration, immutable takeover and generation-fenced cleanup.

This reference implementation supports selected Linux process/private-file and
existing issuer retirement capabilities. It supplies no infrastructure retirement,
public route, operational resolver or control-host-loss watchdog.
"""
from dataclasses import asdict, dataclass
from copy import deepcopy
import os
from pathlib import Path
import select
import secrets
import signal
import stat
import time
from types import MappingProxyType
from workload_factory_binding.evidence import BindingError, byte_digest, canonical, digest, integer, require, valid_digest
from ..config import _handle
from ..github_bootstrap.common import Decision, document
from ..lifecycle import (RunPlan, RunScope, RunResource, ManagedResource, ResourceReadback,
    LeaseReadback, CleanupReadback, RunJanitor, JanitorPeer, _plan)
from ..loaders import ServiceIdentity
from .plan import StaticPlan
from .staging import StagePolicy, scope_of
from .stage_store import StageStore
from .lifecycle_store import LifecycleStore, ERROR
from .file_pins import FilePins
from .issuance import InstallationRetirer, IssuedToken
from .private_http import Response
from .readback import ReadBudget
from .finalization import FinalizedPlan, FinalizationBinding


def _closed(value, names):
    require(type(value) is dict and set(value) == set(names.split()), ERROR)


def _copy(value):
    return document(canonical(value))


def run_plan(value):
    _closed(value, "ref scope janitor resources issued_at expires_at cleanup_timeout retained_state_ref")
    _closed(value["scope"], "config_digest case_ref run_id run_attempt lease_ref cleanup_ref receipt_retention_ref")
    _closed(value["janitor"], "service_ref principal_ref credential_ref trust_digest")
    require(type(value["resources"]) is list, ERROR)
    resources = []
    for resource in value["resources"]:
        _closed(resource, "ref instance_ref kind retention")
        resources.append(RunResource(**resource))
    result = RunPlan(**{**value, "scope": RunScope(**value["scope"]),
                        "janitor": ServiceIdentity(**value["janitor"]), "resources": tuple(resources)})
    _plan(result)
    return result


def pid_namespace():
    info = Path("/proc/self/ns/pid").stat()
    return info.st_dev, info.st_ino


def process_instance(pid):
    try:
        raw = (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
        return f"process:{pid}:{raw[19]}", raw[0]
    except (FileNotFoundError, ProcessLookupError):
        return None, None


@dataclass(frozen=True, repr=False)
class FileResource:
    ref: str
    path: Path
    retention: str


@dataclass(frozen=True, repr=False)
class TokenResource:
    ref: str
    capability: IssuedToken
    retirement: InstallationRetirer


class PosixResources:
    """Source-selected private resources; request bodies never select paths.

    File writers must share the selected private-directory ownership fence. The
    worker is excluded by its inherited sandbox. Host-root and privileged writers
    bypassing that fence remain trusted; this is not conditional cloud deletion.
    """
    def __init__(self, *, files, worker_ref, pins, tokens=()):
        _handle(worker_ref)
        require(type(files) is tuple and type(tokens) is tuple and 1 <= len(files) + len(tokens) < 64
                and len(tokens) <= 3, ERROR)  # final cleanup costs four private reads/token; limit stays12
        selected, roots, paths = {}, {}, set()
        for value in files:
            require(type(value) is FileResource and value.retention in ("run", "retained", "shared"), ERROR)
            _handle(value.ref)
            path = Path(value.path).absolute()
            require(path.resolve() == path and value.ref not in selected and path not in paths, ERROR)
            paths.add(path)
            parent = path.parent.lstat()
            require(stat.S_ISDIR(parent.st_mode) and parent.st_uid == os.geteuid() and not parent.st_mode & 0o077, ERROR)
            roots[value.ref] = (parent.st_dev, parent.st_ino)
            selected[value.ref] = FileResource(value.ref, path, value.retention)
        for value in tokens:
            require(type(value) is TokenResource and value.ref not in selected
                    and type(value.capability) is IssuedToken and type(value.retirement) is InstallationRetirer, ERROR)
            _handle(value.ref)
            selected[value.ref] = value
        token_instances = [digest(value.capability.readback()) for value in tokens]
        require(len(set(token_instances)) == len(token_instances) and worker_ref not in selected, ERROR)
        self.selected, self.roots = MappingProxyType(selected), MappingProxyType(roots)
        self.worker_ref = worker_ref
        self.pid_namespace = pid_namespace()
        self.epoch = secrets.token_hex(32)
        self.files = FilePins(selected={k: v for k, v in selected.items() if type(v) is FileResource},
                              roots=roots, store=pins, epoch=self.epoch)

    def close(self):
        self.files.close()

    def current_namespace(self):
        require(self.pid_namespace == pid_namespace() and not self.files.closed, ERROR)

    def inventory(self, *, decision, initialize=False):
        self.current_namespace()
        result = []
        for ref, value in self.selected.items():
            if type(value) is FileResource:
                instance = self.files.inventory(ref, decision=decision, initialize=initialize)
                require(instance is not None, ERROR)
                result.append(RunResource(ref, instance, "file", value.retention))
            else:
                result.append(RunResource(ref, "credential:" + digest(value.capability.readback()).split(":")[1], "credential", "run"))
        require(len({r.instance_ref for r in result}) == len(result), ERROR)
        return tuple(result)

    def observe(self, expected, *, decision):
        self.current_namespace()
        require(type(expected) is RunResource, ERROR)
        decision.now()
        if expected.ref == self.worker_ref:
            require(expected.kind == "process" and expected.retention == "run", ERROR)
            pieces = expected.instance_ref.split(":")
            require(len(pieces) == 3 and pieces[0] == "process" and pieces[1].isdigit() and pieces[2].isdigit(), ERROR)
            current, state = process_instance(int(pieces[1]))
            return ResourceReadback(expected.ref, current or expected.instance_ref,
                                    current is not None, False)
        require(expected.ref in self.selected, ERROR)
        value = self.selected[expected.ref]
        if type(value) is FileResource:
            require(expected.kind == "file" and expected.retention == value.retention, ERROR)
            current, present = self.files.observe(expected.ref, expected.instance_ref, decision=decision)
            return ResourceReadback(expected.ref, current, present, False)
        actual = "credential:" + digest(value.capability.readback()).split(":")[1]
        require(expected.kind == "credential" and expected.retention == "run" and actual == expected.instance_ref, ERROR)
        ReadBudget(decision).consume("private")
        response = value.retirement.request(value.retirement.observer, "GET", value.capability, decision)
        decision.now()
        require(type(response) is Response and response.status in (200, 401), ERROR)
        status = value.capability.ledger.state(value.capability.ref, decision=decision)["state"]
        revoked = response.status == 401 and status in ("retiring", "retired")
        require(response.status == 200 or revoked, ERROR)
        return ResourceReadback(expected.ref, actual, not revoked, revoked)

    def cleanup(self, expected, *, decision, claim=None):
        self.current_namespace()
        require(type(expected) is RunResource and expected.retention == "run"
                and (claim is None or expected.kind == "file" and callable(claim)), ERROR)
        decision.now()
        if expected.ref == self.worker_ref:
            _, pid, start = expected.instance_ref.split(":")
            pid = int(pid)
            try:
                fd = os.pidfd_open(pid)
            except ProcessLookupError:
                return
            try:
                current, state = process_instance(pid)
                require(current == expected.instance_ref or current is None, ERROR)
                if current is None or state in ("Z", "X"):
                    return
                decision.now()
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                require(select.select([fd], [], [], min(2, decision.remaining()))[0], ERROR)
                end = time.monotonic() + min(2, decision.remaining())
                while process_instance(pid)[0] is not None:
                    require(time.monotonic() < end, ERROR)
                    decision.now()
                    time.sleep(.005)
                decision.now()
            finally:
                os.close(fd)
            return
        require(expected.ref in self.selected, ERROR)
        value = self.selected[expected.ref]
        if type(value) is FileResource:
            require(value.retention == "run" and expected.kind == "file", ERROR)
            self.files.retire(expected.ref, expected.instance_ref, decision=decision, claim=claim)
        else:
            require(expected.kind == "credential" and expected.instance_ref ==
                    "credential:" + digest(value.capability.readback()).split(":")[1], ERROR)
            ReadBudget(decision).consume("private")
            ReadBudget(decision).consume("private")
            value.retirement.retire(value.capability, decision=decision)


def _state(events):
    result = {"registration": None, "generation": None, "final": None, "released": False,
              "closed": False, "actions": {}, "release": None, "prestart_closed": None}
    for event in events:
        kind, value = event["kind"], event["data"]
        if kind in ("clock", "file-retired"):
            continue
        if kind == "registration":
            require(result["registration"] is None, ERROR)
            result["registration"] = value
        elif kind == "generation":
            require(result["registration"] is not None and result["generation"] is None and result["final"] is None
                    and result["prestart_closed"] is None, ERROR)
            result["generation"] = value
        elif kind == "prestart-closed":
            _closed(value, "registration_digest unit_digest")
            require(result["registration"] is not None and result["closed"] and result["generation"] is None
                    and result["prestart_closed"] is None and result["final"] is None
                    and value["registration_digest"] == digest(result["registration"])
                    and value["unit_digest"] == digest(result["registration"]["unit"]), ERROR)
            result["prestart_closed"] = value
        elif kind == "final-plan":
            require(result["generation"] is not None and result["final"] is None and not result["closed"], ERROR)
            result["final"] = value
        elif kind == "stage-release":
            require(result["final"] is not None and not result["released"] and not result["closed"]
                    and not result["actions"], ERROR)
            result["released"] = True
            result["release"] = value
        elif kind == "lease-closed":
            require(result["registration"] is not None and not result["closed"], ERROR)
            result["closed"] = True
        elif kind == "action-claimed":
            require(result["closed"] and value["key"] not in result["actions"], ERROR)
            result["actions"][value["key"]] = value
        else:
            raise BindingError(ERROR)
    return result


class HostedLifecycle:
    """Trusted source construction; primary operations are private capabilities."""
    def __init__(self, *, plan, context, policy, host_store, store, intake, audit_store,
                 resources, janitor, auditor, scheduler, host_pid_namespace,
                 final_authority_principal, cleanup_until, cleanup_timeout=30, retained_roots=()):
        require(type(plan) is StaticPlan and type(policy) is StagePolicy
                and type(host_store) is StageStore and host_store.kind == "host"
                and all(type(x) is LifecycleStore for x in (store, intake, audit_store))
                and (store.kind, intake.kind, audit_store.kind) == ("primary", "scheduler", "audit")
                and type(resources) is PosixResources and type(janitor) is ServiceIdentity
                and type(auditor) is ServiceIdentity and type(scheduler) is dict, ERROR)
        _closed(scheduler, "principal_ref pid start_time boot_id")
        _handle(final_authority_principal)
        for identity in (janitor, auditor):
            for field in ("service_ref", "principal_ref", "credential_ref"):
                _handle(getattr(identity, field))
            require(valid_digest(identity.trust_digest), ERROR)
        config = plan.value()["configuration_template"]
        require(asdict(janitor) == config["services"]["janitor"] and janitor.principal_ref != auditor.principal_ref
                and janitor.credential_ref != auditor.credential_ref
                and config["services"]["worker_channel"]["principal_ref"] not in
                    (janitor.principal_ref, auditor.principal_ref, scheduler["principal_ref"])
                and config["services"]["worker_channel"]["credential_ref"] not in (janitor.credential_ref, auditor.credential_ref)
                and len({janitor.principal_ref, auditor.principal_ref, scheduler["principal_ref"]}) == 3
                and integer(cleanup_until) and cleanup_until <= config["expires_at"] + 60
                and integer(cleanup_timeout) and 1 <= cleanup_timeout <= 60, ERROR)
        _closed(scheduler, "principal_ref pid start_time boot_id")
        _handle(scheduler["principal_ref"])
        require(scheduler["boot_id"] == scope_of(plan, context, policy)["boot_id"]
                and type(scheduler["pid"]) is int and scheduler["pid"] > 0
                and type(scheduler["start_time"]) is int and scheduler["start_time"] > 0, ERROR)
        require(type(host_pid_namespace) is tuple and host_pid_namespace == resources.pid_namespace == pid_namespace(), ERROR)
        require(resources.files.store.directory == store.directory and resources.files.store.identity == store.identity
                and type(retained_roots) is tuple, ERROR)
        protected = (host_store.directory, store.directory, store.witness, intake.directory, intake.witness,
                     audit_store.directory, audit_store.witness, *map(Path, retained_roots))
        require(all(root.resolve() == root and root.is_dir() for root in protected), ERROR)
        for value in resources.selected.values():
            if type(value) is FileResource and value.retention == "run":
                require(not any(value.path.is_relative_to(root) for root in protected), ERROR)
        state_resource = resources.selected.get(config["state"]["store_ref"])
        require(type(state_resource) is FileResource and state_resource.retention == "retained", ERROR)
        self.host_pid_namespace = host_pid_namespace
        self.plan, self.context, self.policy, self.host_store = plan, context, policy, host_store
        self.store, self.intake, self.audit_store, self.resources = store, intake, audit_store, resources
        self.scope_raw = canonical(scope_of(plan, context, policy))
        self.janitor, self.auditor, self.scheduler = janitor, auditor, canonical(scheduler)
        self.cleanup_until, self.cleanup_timeout = cleanup_until, cleanup_timeout
        self.final_authority_principal = final_authority_principal

    @property
    def scope(self):
        return document(self.scope_raw)

    def state(self, *, decision):
        require(self.host_pid_namespace == self.resources.pid_namespace == pid_namespace(), ERROR)
        value = _state(self.store.events(decision=decision))
        registration = value["registration"]
        if registration is not None:
            require(canonical(registration["scope"]) == self.scope_raw
                    and registration["accepted_commit"] == self.context.accepted_commit
                    and registration["pid_namespace"] == list(self.host_pid_namespace)
                    and registration["resource_epoch"] == self.resources.epoch, ERROR)
        return value

    def _registration(self, ref, decision):
        require(ref == self.scope["launch_ref"], ERROR)
        state = self.state(decision=decision)
        require(state["registration"] is not None, ERROR)
        return state

    def register(self, ref, unit_digest, *, decision):
        require(ref == self.scope["launch_ref"], ERROR)
        require(self.state(decision=decision)["registration"] is None, ERROR)
        row = self.host_store.read(ref, decision=decision)
        unit = row["unit"]
        require(row["state"] == "registered" and canonical(row["scope"]) == self.scope_raw
                and type(unit) is dict and digest(unit) == unit_digest
                and unit["scope_digest"] == digest(self.scope), ERROR)
        actual, state = process_instance(unit["manager_pid"])
        require(actual == f"process:{unit['manager_pid']}:{unit['manager_start']}" and state not in ("Z", "X"), ERROR)
        files = self.resources.inventory(decision=decision, initialize=True)
        retained = self.plan.value()["configuration_template"]["state"]["store_ref"]
        require(any(r.ref == retained and r.kind == "file" and r.retention == "retained" for r in files), ERROR)
        now = decision.now()
        expiry = min(row["deadline"], self.plan.valid_until)
        require(now < expiry < self.cleanup_until, ERROR)
        decision.clip(expiry)
        value = {"scope": self.scope, "accepted_commit": self.context.accepted_commit,
                 "unit": unit, "pid_namespace": list(self.host_pid_namespace), "resource_epoch": self.resources.epoch, "resources": [asdict(r) for r in files], "worker_ref": self.resources.worker_ref,
                 "issued_at": now, "expires_at": expiry, "cleanup_until": self.cleanup_until,
                 "cleanup_timeout": self.cleanup_timeout, "retained_state_ref": retained,
                 "janitor": asdict(self.janitor), "auditor": asdict(self.auditor), "scheduler": document(self.scheduler)}
        def save(events, append):
            require(_state(events)["registration"] is None, ERROR)
            append("registration", value)
        self.store.mutate(save, decision=decision)
        self.intake.record("stage-intake", {"registration_digest": digest(value), "expires_at": expiry}, decision=decision)
        return {"registration_digest": digest(value)}

    def scheduler_current(self, *, decision):
        decision.now()
        selected = document(self.scheduler)
        actual, state = process_instance(selected["pid"])
        require(actual == f"process:{selected['pid']}:{selected['start_time']}" and state not in ("Z", "X")
                and selected["boot_id"] == Path("/proc/sys/kernel/random/boot_id").read_text().strip(), ERROR)

    def acknowledge_stage(self, ref, *, decision):
        value = self._registration(ref, decision)["registration"]
        self.scheduler_current(decision=decision)
        host = self.host_store.read(ref, decision=decision)
        require(host["state"] == "registered" and canonical(host["unit"]) == canonical(value["unit"])
                and canonical(host["scope"]) == self.scope_raw
                and [asdict(r) for r in self.resources.inventory(decision=decision)] == value["resources"], ERROR)
        records = self.intake.events(decision=decision)
        require(any(e["kind"] == "stage-intake" and e["data"] ==
                    {"registration_digest": digest(value), "expires_at": value["expires_at"]} for e in records)
                and decision.now() < value["expires_at"], ERROR)
        decision.clip(value["expires_at"])
        acknowledgement = {"scope_digest": digest(self.scope), "unit_digest": digest(value["unit"]),
                           "state": "acknowledged", "expires_at": value["expires_at"],
                           "registration_digest": digest(value)}
        def save(events, append):
            existing = [e["data"] for e in events if e["kind"] == "stage-ack"]
            require(not existing or existing == [acknowledgement], ERROR)
            if not existing:
                append("stage-ack", acknowledgement)
        self.audit_store.mutate(save, decision=decision)
        return acknowledgement

    def stage_lease(self, ref, *, decision):
        state = self._registration(self.scope["launch_ref"], decision)
        self.scheduler_current(decision=decision)
        require(ref == self.scope["cleanup_ref"] and not state["closed"] and not state["released"], ERROR)
        registration = state["registration"]
        records = [e["data"] for e in self.audit_store.events(decision=decision) if e["kind"] == "stage-ack"]
        require(len(records) == 1 and records[0]["registration_digest"] == digest(registration)
                and decision.now() < registration["expires_at"], ERROR)
        decision.clip(registration["expires_at"])
        return {k: records[0][k] for k in ("scope_digest", "unit_digest", "state", "expires_at")}

    def bind_generation(self, ref, *, decision, cleanup=False):
        state = self._registration(ref, decision)
        reg = state["registration"]
        require(decision.now() < (reg["cleanup_until"] if cleanup else reg["expires_at"]), ERROR)
        decision.clip(reg["cleanup_until"] if cleanup else reg["expires_at"])
        if state["generation"] is not None:
            return state["generation"]
        if cleanup and state["prestart_closed"] is not None:
            return None
        row = self.host_store.read(ref, decision=decision)
        require(canonical(row["unit"]) == canonical(reg["unit"]) and canonical(row["scope"]) == self.scope_raw, ERROR)
        generation = row["generation"]
        if cleanup and row["state"] == "registered" and generation is None:
            # Lease closure precedes this observation. A later host start must
            # consume its attempt then reread that closed lease before Popen.
            require(state["closed"], ERROR)
            def prestart(events, append):
                current = _state(events)
                require(current["closed"] and current["generation"] is None, ERROR)
                if current["prestart_closed"] is None:
                    append("prestart-closed", {"registration_digest": digest(reg), "unit_digest": digest(reg["unit"])})
            self.store.mutate(prestart, decision=decision)
            return None
        require(row["state"] == "running" and type(generation) is dict, ERROR)
        _closed(generation, "unit_digest pid start_time session_id boot_id uid policy_digest cgroup_digest")
        require(generation["unit_digest"] == digest(reg["unit"])
                and generation["boot_id"] == self.scope["boot_id"] and generation["uid"] == self.scope["worker_uid"]
                and all(type(generation[k]) is int and generation[k] > 0 for k in ("pid", "start_time", "session_id", "uid"))
                and generation["session_id"] == generation["pid"]
                and generation["policy_digest"] == self.scope["hosting_selection_digest"]
                and valid_digest(generation["cgroup_digest"]), ERROR)
        expected = f"process:{generation['pid']}:{generation['start_time']}"
        current, process_state = process_instance(generation["pid"])
        if not (cleanup and (current is None or current == expected and process_state in ("Z", "X"))):
            require(current == expected and process_state not in ("Z", "X"), ERROR)
            try:
                require(os.getsid(generation["pid"]) == generation["session_id"]
                        and byte_digest((Path("/proc") / str(generation["pid"]) / "cgroup").read_bytes()) == generation["cgroup_digest"], ERROR)
            except (FileNotFoundError, ProcessLookupError):
                require(cleanup and process_instance(generation["pid"])[0] is None, ERROR)
        # This is the exact generation already persisted by the authenticated
        # host, never an invented PID or a replacement process observation.
        value = {"generation": generation, "resource": asdict(RunResource(reg["worker_ref"], expected, "process", "run"))}
        def save(events, append):
            current = _state(events)
            require(current["prestart_closed"] is None, ERROR)
            if current["generation"] is None:
                append("generation", value)
            else:
                require(current["generation"] == value, ERROR)
        self.store.mutate(save, decision=decision)
        return value

    def resources_for(self, state):
        require(state["registration"] is not None
                and (state["generation"] is not None or state["closed"] and state["prestart_closed"] is not None), ERROR)
        selected = tuple(RunResource(**r) for r in state["registration"]["resources"])
        return selected + ((RunResource(**state["generation"]["resource"]),) if state["generation"] is not None else ())

    def prepare_final(self, ref, finalized, plan, *, decision):
        require(type(finalized) is FinalizedPlan and type(finalized.binding) is FinalizationBinding
                and type(plan) is RunPlan, ERROR)
        _plan(plan)
        state = self._registration(ref, decision)
        reg = state["registration"]
        require(not state["closed"] and not state["released"] and state["final"] is None, ERROR)
        config, policy = document(finalized.configuration, 16384), document(finalized.policy, 16384)
        bound = finalized.binding
        generation = state["generation"]["generation"]
        projected = {k: self.scope[k] for k in ("launch_ref", "host_ref", "incarnation_ref", "boot_id")}
        projected.update(invocation_ref=reg["unit"]["invocation_ref"], pid=generation["pid"], start_time=generation["start_time"])
        require(bound.principal_ref == self.final_authority_principal and bound.plan_digest == self.plan.digest
                and bound.case_ref == self.scope["case_ref"] and bound.source_commit == self.scope["source_commit"]
                and bound.run_id == self.scope["run_id"] and bound.run_attempt == self.scope["run_attempt"]
                and bound.generation_digest == digest(projected) and bound.config_digest == digest(config)
                and bound.policy_digest == digest(policy) and integer(bound.observed_at) and integer(bound.expires_at)
                and bound.observed_at <= decision.now() < bound.expires_at <= bound.observed_at + 60, ERROR)
        template = self.plan.value()["configuration_template"]
        expected_config = deepcopy(template)
        expected_config["launch"].update(run_id=self.scope["run_id"], run_attempt=self.scope["run_attempt"])
        expected_config["composition_digest"] = config["composition_digest"]
        expected_config["authority"]["policy_digest"] = digest(policy)
        expected_policy = self.plan.value()["policy_template"]
        expected_policy["composition_digest"] = config["composition_digest"]
        require(canonical(config) == canonical(expected_config) and canonical(policy) == canonical(expected_policy), ERROR)
        decision.clip(min(reg["expires_at"], bound.expires_at, config["expires_at"]))
        expected = RunScope(bound.config_digest, self.scope["case_ref"], self.scope["run_id"], self.scope["run_attempt"], **config["lifecycle"])
        template = self.plan.value()["configuration_template"]
        require(config["lifecycle"] == template["lifecycle"] and plan.scope == expected
                and plan.janitor == self.janitor and plan.resources == self.resources_for(state)
                and plan.retained_state_ref == reg["retained_state_ref"]
                and reg["issued_at"] <= plan.issued_at <= decision.now() < plan.expires_at
                <= min(reg["expires_at"], bound.expires_at, config["expires_at"])
                and plan.cleanup_timeout <= reg["cleanup_timeout"], ERROR)
        for resource in plan.resources:
            actual = self.resources.observe(resource, decision=decision)
            require(actual.instance_ref == resource.instance_ref and actual.present and not actual.revoked, ERROR)
        value = {"plan": asdict(plan), "binding": asdict(bound), "configuration": config, "policy": policy,
                 "registration_digest": digest(reg), "generation_digest": digest(state["generation"])}
        def save(events, append):
            current = _state(events)
            require(not current["closed"] and current["final"] is None and not current["actions"], ERROR)
            append("final-plan", value)
        self.store.mutate(save, decision=decision)
        self.intake.record("final-intake", {"plan_digest": plan.digest, "registration_digest": digest(reg),
                                           "expires_at": plan.expires_at}, decision=decision)
        return {"plan_digest": plan.digest}

    def acknowledge_final(self, ref, *, decision):
        state = self._registration(ref, decision)
        require(state["final"] is not None and not state["closed"], ERROR)
        self.scheduler_current(decision=decision)
        plan = run_plan(state["final"]["plan"])
        require(decision.now() < plan.expires_at and any(e["kind"] == "final-intake" and e["data"] ==
            {"plan_digest": plan.digest, "registration_digest": digest(state["registration"]), "expires_at": plan.expires_at}
            for e in self.intake.events(decision=decision)), ERROR)
        for resource in plan.resources:
            actual = self.resources.observe(resource, decision=decision)
            require(actual.instance_ref == resource.instance_ref and actual.present and not actual.revoked, ERROR)
        decision.clip(plan.expires_at)
        current = self._registration(ref, decision)
        require(not current["closed"] and canonical(current["final"]) == canonical(state["final"])
                and canonical(current["generation"]) == canonical(state["generation"]), ERROR)
        acknowledgement = {"registration_digest": digest(state["registration"]), "plan_digest": plan.digest,
            "generation_digest": digest(state["generation"]), "observed_at": decision.now(),
            "expires_at": min(plan.expires_at, decision.deadline), "principal_ref": self.auditor.principal_ref}
        def save(events, append):
            require(not any(e["kind"] == "takeover-ack" for e in events), ERROR)
            append("takeover-ack", acknowledgement)
        self.audit_store.mutate(save, decision=decision)
        return acknowledgement

    def release_stage(self, ref, *, decision):
        state = self._registration(ref, decision)
        final = state["final"]
        if final is None:
            raise BindingError(ERROR)
        require(not state["closed"] and not state["released"], ERROR)
        plan = run_plan(final["plan"])
        records = [e["data"] for e in self.audit_store.events(decision=decision) if e["kind"] == "takeover-ack"]
        require(len(records) == 1, ERROR)
        ack = records[0]
        require(ack["principal_ref"] == self.auditor.principal_ref and ack["plan_digest"] == plan.digest
                and ack["registration_digest"] == digest(state["registration"])
                and ack["generation_digest"] == digest(state["generation"])
                and ack["observed_at"] <= decision.now() < min(ack["expires_at"], plan.expires_at), ERROR)
        self.scheduler_current(decision=decision)
        decision.clip(min(ack["expires_at"], plan.expires_at))
        def save(events, append):
            current = _state(events)
            require(not current["released"] and not current["closed"] and not current["actions"], ERROR)
            append("stage-release", {"acknowledgement_digest": digest(ack), "plan_digest": plan.digest})
        self.store.mutate(save, decision=decision)
        return {"state": "final-owned", "plan_digest": plan.digest}

    def final_lease(self, ref, *, decision):
        state = self._registration(self.scope["launch_ref"], decision)
        require(state["released"] and state["final"] is not None, ERROR)
        plan = run_plan(state["final"]["plan"])
        require(ref == plan.ref and decision.now() < state["registration"]["cleanup_until"], ERROR)
        if not state["closed"]:
            self.scheduler_current(decision=decision)
        return LeaseReadback(plan.digest, plan.scope, "closed" if state["closed"] else "active",
                             plan.issued_at, plan.expires_at, decision.now(), min(decision.deadline, state["registration"]["cleanup_until"]))

    def managed_resource(self, ref, *, decision):
        state = self._registration(self.scope["launch_ref"], decision)
        require(state["released"] and state["final"] is not None, ERROR)
        plan = run_plan(state["final"]["plan"])
        acks = [e["data"] for e in self.audit_store.events(decision=decision) if e["kind"] == "takeover-ack"]
        require(len(acks) == 1 and digest(acks[0]) == state["release"]["acknowledgement_digest"]
                and acks[0]["plan_digest"] == plan.digest
                and acks[0]["registration_digest"] == digest(state["registration"])
                and acks[0]["generation_digest"] == digest(state["generation"]), ERROR)
        selected = next((r for r in plan.resources if r.ref == ref), None)
        require(selected is not None, ERROR)
        actual = self.resources.observe(selected, decision=decision)
        resource = RunResource(selected.ref, actual.instance_ref, selected.kind, selected.retention)
        return ManagedResource(resource, digest(asdict(plan.scope)))

    def _claim(self, resource, decision):
        key = digest(asdict(resource))
        def claim(events, append):
            state = _state(events)
            require(state["closed"], ERROR)
            if key in state["actions"]:
                return False
            append("action-claimed", {"key": key, "resource": asdict(resource),
                   "owner": "final" if state["released"] else "stage"})
            return True
        return self.store.mutate(claim, decision=decision)

    @staticmethod
    def narrow(decision, deadline):
        decision.clip(deadline)
        decision.end = min(decision.end, decision.last_mono + decision.deadline - decision.last)
        decision.now()

    def cleanup(self, ref, outcome, *, decision):
        require(outcome in ("success", "failure", "cancel", "expired"), ERROR)
        state = self._registration(ref, decision)
        reg = state["registration"]
        require(decision.now() < reg["cleanup_until"], ERROR)
        timeout = reg["cleanup_timeout"]
        if state["released"]:
            timeout = min(timeout, run_plan(state["final"]["plan"]).cleanup_timeout)
        self.narrow(decision, min(reg["cleanup_until"], decision.now() + timeout))
        if outcome == "expired":
            expiry = run_plan(state["final"]["plan"]).expires_at if state["released"] else reg["expires_at"]
            require(decision.now() >= expiry, ERROR)
        def close(events, append):
            if not _state(events)["closed"]:
                append("lease-closed", {"outcome": outcome})
        self.store.mutate(close, decision=decision)
        if state["generation"] is None and state["prestart_closed"] is None:
            self.bind_generation(ref, decision=decision, cleanup=True)
        state = self._registration(ref, decision)
        selected = self.resources_for(state)
        def remove(resource):
            actual = self.resources.observe(resource, decision=decision)
            require(actual.instance_ref == resource.instance_ref, ERROR)
            if not actual.present:
                require(resource.kind != "credential" or actual.revoked, ERROR)
                return
            if resource.kind == "file":
                # Claim only under the backend's exact-generation file fence.
                self.resources.cleanup(resource, decision=decision, claim=lambda: self._claim(resource, decision))
            else:
                require(self._claim(resource, decision), ERROR)
                self.resources.cleanup(resource, decision=decision)
        if state["released"]:
            plan = run_plan(state["final"]["plan"])
            peer = JanitorPeer(self.janitor.principal_ref, self.janitor.credential_ref)
            def bounded(action, *args, deadline):
                self.narrow(decision, deadline)
                return action(*args)
            janitor = RunJanitor(plan=plan, allowed_gate=peer,
                load_plan=lambda _ref, *, deadline: bounded(lambda: plan, deadline=deadline),
                load_lease=lambda _ref, *, deadline: bounded(lambda: self.final_lease(plan.ref, decision=decision), deadline=deadline),
                load_resource=lambda ref, *, deadline: bounded(lambda: self.managed_resource(ref, decision=decision), deadline=deadline),
                close_lease=lambda _ref, *, deadline: bounded(lambda: None, deadline=deadline),
                cleanup=lambda managed, *, deadline: bounded(remove, managed.resource, deadline=deadline), clock=decision.clock)
            janitor.finalize(plan.ref, peer=peer, deadline=min(decision.deadline, reg["cleanup_until"]))
        else:
            failed = False
            for resource in selected:
                if resource.retention != "run":
                    continue
                try:
                    remove(resource)
                except Exception:
                    failed = True
            require(not failed, ERROR)
        decision.now()
        return {"state": "cleanup-requested", "owner": "final" if state["released"] else "stage"}

    def audit_cleanup(self, ref, attempt_ref, *, decision):
        _handle(attempt_ref)
        state = self._registration(ref, decision)
        reg = state["registration"]
        require(state["closed"] and decision.now() < reg["cleanup_until"], ERROR)
        timeout = reg["cleanup_timeout"]
        if state["released"]:
            timeout = min(timeout, run_plan(state["final"]["plan"]).cleanup_timeout)
        self.narrow(decision, min(reg["cleanup_until"], decision.now() + timeout))
        resources = self.resources_for(state)
        actual = tuple(self.resources.observe(r, decision=decision) for r in resources)
        for expected, observed in zip(resources, actual):
            require(expected.ref == observed.ref and expected.instance_ref == observed.instance_ref, ERROR)
            if expected.retention == "run":
                require(not observed.present and (expected.kind != "credential" or observed.revoked), ERROR)
            else:
                require(observed.present and not observed.revoked, ERROR)
        if state["released"]:
            plan = run_plan(state["final"]["plan"])
            record = CleanupReadback(plan.digest, plan.scope, "closed", actual, decision.now(),
                                    min(decision.deadline, reg["cleanup_until"]), attempt_ref)
            value = {"kind": "final", "record": asdict(record)}
        else:
            value = {"kind": "stage", "registration_digest": digest(reg), "scope_digest": digest(self.scope),
                     "resources": [asdict(r) for r in actual], "attempt_ref": attempt_ref,
                     "observed_at": decision.now(), "expires_at": min(decision.deadline, reg["cleanup_until"])}
        self.audit_store.record("cleanup-audit", {"attempt_ref": attempt_ref, "readback_digest": digest(value)}, decision=decision)
        return value

    def require_infrastructure(self, *_args, **_kwargs):
        raise BindingError("hosted-lifecycle-infrastructure-unsupported")


class RegisteredStageReadback:
    """Local selected retained-store capability; no relayed/private network call.

    Both the independent acknowledgement and primary ownership journal are read
    fresh under the caller Decision. A remote-only topology needs a separately
    governed budget if its added RPCs cannot fit the accepted finalizer profile.
    """
    def __init__(self, lifecycle):
        require(type(lifecycle) is HostedLifecycle, ERROR)
        self.lifecycle = lifecycle

    def read(self, ref, *, decision):
        from .finalization import StagingReadback
        life = self.lifecycle
        state = life._registration(ref, decision)
        generation_record = state["generation"]
        if generation_record is None:
            raise BindingError(ERROR)
        require(not state["closed"], ERROR)
        ack = life.stage_lease(life.scope["cleanup_ref"], decision=decision)
        reg, generation = state["registration"], generation_record["generation"]
        projected = {k: life.scope[k] for k in ("launch_ref", "host_ref", "incarnation_ref", "boot_id")}
        projected.update(invocation_ref=reg["unit"]["invocation_ref"], pid=generation["pid"], start_time=generation["start_time"])
        require(ack["scope_digest"] == digest(life.scope) and ack["unit_digest"] == digest(reg["unit"]), ERROR)
        return StagingReadback(life.auditor.principal_ref, life.plan.digest, life.scope["case_ref"],
            life.scope["run_id"], life.scope["run_attempt"], ref, life.scope["cleanup_ref"], projected,
            "cleanup-acknowledged", decision.now(), min(ack["expires_at"], decision.deadline))
