"""Test-only protected registration, janitor and independent readback processes.

Private OS pipe capabilities select peer identities outside request bodies. These
same-user fixtures do not establish deployed OS/admin isolation or a public API.
"""
from dataclasses import asdict
import json
import multiprocessing
from multiprocessing.connection import wait
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import BindingError, decode_object, digest
from workload_factory_binding_runtime.lifecycle import (
    CleanupReadback, JanitorPeer, LeaseReadback, ManagedResource, ResourceReadback,
    RunJanitor, RunLifecycle, RunPlan, RunResource, RunScope,
)
from workload_factory_binding_runtime.loaders import BoundService, ServiceIdentity
from .test_config import encoded

MAX_FRAME = 16384


def _write(path, value):
    staging = path.with_suffix(".new")
    fd = os.open(staging, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(encoded(value))
    staging.replace(path)


def _read(path):
    return decode_object(path.read_bytes())


def _plan(value):
    value = dict(value)
    value["scope"] = RunScope(**value["scope"])
    value["janitor"] = ServiceIdentity(**value["janitor"])
    value["resources"] = tuple(RunResource(**r) for r in value["resources"])
    return RunPlan(**value)


def _file_instance(path):
    info = path.stat()
    return f"file:{info.st_dev}:{info.st_ino}"


def _process_instance(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return f"process:{pid}:{fields[19]}"
    except FileNotFoundError:
        return None


class _Provider:
    def __init__(self, root, state_path, scope, clock):
        self.root, self.state_path, self.scope, self.clock = root, state_path, scope, clock
        self.worker = subprocess.Popen([sys.executable, "-I", "-B", "-c", "import time; time.sleep(300)"],
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self._initialize(root, state_path, scope)
        except BaseException:
            self.stop_worker()
            raise

    def _initialize(self, root, state_path, scope):
        self.mode = "normal"
        self.paths = {"resource:credential": root / "credential.key", "resource:temporary": root / "temporary",
                      "resource:shared": root / "shared", state_path[0]: Path(state_path[1])}
        for ref, path in self.paths.items():
            if ref != state_path[0]:
                path.write_bytes(b"synthetic isolated resource")
                path.chmod(0o600)
        self.inventory = (
            RunResource("resource:worker", _process_instance(self.worker.pid), "process", "run"),
            RunResource("resource:credential", _file_instance(self.paths["resource:credential"]), "credential", "run"),
            RunResource("resource:temporary", _file_instance(self.paths["resource:temporary"]), "file", "run"),
            RunResource(state_path[0], _file_instance(self.paths[state_path[0]]), "file", "retained"),
            RunResource("resource:shared", _file_instance(self.paths["resource:shared"]), "file", "shared"),
        )
        _write(root / "ownership.json", {"pid": self.worker.pid, "resources": [asdict(r) for r in self.inventory],
                                         "owner": digest(asdict(scope)),
                                         "paths": {ref: str(path) for ref, path in self.paths.items()}})
        _write(root / "lease.json", {"status": "active", "revoked": False})

    def register(self, plan):
        assert plan.resources == self.inventory and plan.scope == self.scope
        _write(self.root / "plan.json", asdict(plan))

    def plan(self, ref, *, deadline):
        plan = _plan(_read(self.root / "plan.json"))
        assert plan.ref == ref
        return plan

    def lease(self, ref, *, deadline):
        plan = self.plan(ref, deadline=deadline)
        return LeaseReadback(plan.digest, plan.scope, _read(self.root / "lease.json")["status"],
                             plan.issued_at, plan.expires_at, self.clock.value, self.clock.value + 30)

    def resource(self, ref, *, deadline):
        ownership = _read(self.root / "ownership.json")
        resource = next(RunResource(**r) for r in ownership["resources"] if r["ref"] == ref)
        if resource.kind == "process":
            current = _process_instance(ownership["pid"])
        else:
            path = Path(ownership["paths"][ref])
            current = _file_instance(path) if path.exists() else None
        if current is not None:
            resource = RunResource(resource.ref, current, resource.kind, resource.retention)
        return ManagedResource(resource, ownership["owner"])

    def close(self, ref, *, deadline):
        value = _read(self.root / "lease.json")
        value["status"] = "closed"
        _write(self.root / "lease.json", value)

    def cleanup(self, expected, *, deadline):
        assert self.resource(expected.resource.ref, deadline=deadline) == expected
        resource = expected.resource
        if self.mode == "skip-file" and resource.ref == "resource:temporary":
            return  # deliberate excess-trust mutation: independent audit must catch it
        if resource.kind == "process":
            self.stop_worker()
        else:
            if resource.kind == "credential":
                value = _read(self.root / "lease.json")
                value["revoked"] = True
                _write(self.root / "lease.json", value)
            self.paths[resource.ref].unlink(missing_ok=True)

    def stop_worker(self):
        if self.worker.poll() is None:
            self.worker.terminate()
            try:
                self.worker.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.worker.kill()
                self.worker.wait(timeout=2)


def _controller(root, state_path, scope, identity, clock, admin, gate, worker):
    provider = _Provider(root, state_path, scope, clock)
    peer = JanitorPeer(identity.principal_ref, identity.credential_ref)
    janitor = None
    channels = {admin: "admin", gate: "gate", worker: "worker"}
    try:
        running = True
        while running:
            for connection in wait(list(channels), timeout=0.02):
                try:
                    body = decode_object(connection.recv_bytes(MAX_FRAME))
                    method, role = body["method"], channels[connection]
                    if role == "admin":
                        if method == "inventory":
                            value = [asdict(r) for r in provider.inventory]
                        elif method == "register":
                            selected = _plan(body["plan"])
                            provider.register(selected)
                            janitor = RunJanitor(plan=selected, allowed_gate=peer, load_plan=provider.plan,
                                                 load_lease=provider.lease, load_resource=provider.resource,
                                                 close_lease=provider.close, cleanup=provider.cleanup,
                                                 clock=lambda: clock.value)
                            value = True
                        elif method == "mode":
                            provider.mode, value = body["mode"], True
                        elif method == "stop":
                            running, value = False, True
                        else:
                            raise BindingError("fixture-admin-denied")
                    else:
                        authenticated = peer if role == "gate" else JanitorPeer("principal:worker", "credential:worker")
                        # Body-supplied peer/owner fields are never used for authorization.
                        if method == "read_lease":
                            value = asdict(janitor.read_lease(body["ref"], peer=authenticated, deadline=body["deadline"]))
                        elif method == "finalize":
                            janitor.finalize(body["ref"], peer=authenticated, deadline=body["deadline"])
                            value = True
                        elif method == "credential":
                            janitor._peer(authenticated)
                            lease = janitor.read_lease(body["ref"], peer=authenticated, deadline=body["deadline"])
                            if (lease.status != "active" or clock.value >= lease.expires_at
                                    or _read(root / "lease.json")["revoked"]
                                    or not provider.paths["resource:credential"].exists()):
                                raise BindingError("fixture-credential-denied")
                            value = True
                        else:
                            raise BindingError("janitor-peer-denied")
                    response = {"value": value}
                except (EOFError, OSError):
                    connection.close()
                    del channels[connection]
                    continue
                except Exception as error:
                    response = {"error": str(error) if isinstance(error, BindingError) else "fixture-service-failed"}
                connection.send_bytes(encoded(response))
            if (root / "plan.json").exists():
                plan = _plan(_read(root / "plan.json"))
                if clock.value >= plan.expires_at:
                    try:
                        janitor.sweep(plan.ref, deadline=clock.value + plan.cleanup_timeout)
                    except BindingError:
                        pass  # retry on the next independent scheduler tick
    finally:
        provider.stop_worker()
        for connection in channels:
            connection.close()


def _audit(root, clock, connection):
    while True:
        try:
            body = decode_object(connection.recv_bytes(MAX_FRAME))
            if body["method"] == "stop":
                connection.send_bytes(encoded({"value": True}))
                return
            if body["method"] != "read_cleanup":
                raise BindingError("fixture-readback-denied")
            plan, ownership = _plan(_read(root / "plan.json")), _read(root / "ownership.json")
            if body["ref"] != plan.ref:
                raise BindingError("fixture-readback-denied")
            lease, resources = _read(root / "lease.json"), []
            for value in ownership["resources"]:
                resource = RunResource(**value)
                if resource.kind == "process":
                    current = _process_instance(ownership["pid"])
                else:
                    path = Path(ownership["paths"][resource.ref])
                    current = _file_instance(path) if path.exists() else None
                resources.append(ResourceReadback(resource.ref, current or resource.instance_ref, current is not None,
                                                   lease["revoked"] if resource.kind == "credential" else False))
            result = CleanupReadback(plan.digest, plan.scope, lease["status"], tuple(resources),
                                     clock.value, clock.value + 30, body["attempt_ref"])
            response = {"value": asdict(result)}
        except EOFError:
            return
        except Exception:
            response = {"error": "fixture-readback-failed"}
        connection.send_bytes(encoded(response))


class RPC:
    def __init__(self, connection, clock):
        self.connection, self.clock = connection, clock
    def request(self, method, **body):
        self.connection.send_bytes(encoded({"method": method, **body}))
        timeout = min(4, max(0, body.get("deadline", self.clock() + 4) - self.clock()))
        if not self.connection.poll(timeout):
            raise BindingError("fixture-rpc-unavailable")
        reply = decode_object(self.connection.recv_bytes(MAX_FRAME))
        if "error" in reply:
            raise BindingError(reply["error"])
        return reply["value"]
    def read_lease(self, ref, *, deadline):
        value = self.request("read_lease", ref=ref, deadline=deadline)
        value["scope"] = RunScope(**value["scope"])
        return LeaseReadback(**value)
    def finalize(self, ref, *, deadline):
        self.request("finalize", ref=ref, deadline=deadline)
    def read_cleanup(self, ref, *, deadline, attempt_ref="cleanup-attempt:probe"):
        value = self.request("read_cleanup", ref=ref, deadline=deadline, attempt_ref=attempt_ref)
        value["scope"] = RunScope(**value["scope"])
        value["resources"] = tuple(ResourceReadback(**r) for r in value["resources"])
        return CleanupReadback(**value)


@pytest.fixture
def p(c, tmp_path):
    context = multiprocessing.get_context("fork")
    root = tmp_path / "protected-registration"
    root.mkdir(mode=0o700)
    clock = context.Value("q", c.h.now)
    pairs = [context.Pipe() for _ in range(4)]
    admin, gate, worker, audit = [RPC(pair[0], lambda: clock.value) for pair in pairs]
    scope = RunScope(digest(c.config), c.config["case_ref"], c.config["launch"]["run_id"],
                     c.config["launch"]["run_attempt"], **c.config["lifecycle"])
    identity = ServiceIdentity(**c.config["services"]["janitor"])
    controller = context.Process(target=_controller, args=(root, (c.config["state"]["store_ref"], str(c.h.ledger.path)),
                                                          scope, identity, clock, pairs[0][1], pairs[1][1], pairs[2][1]))
    reader = context.Process(target=_audit, args=(root, clock, pairs[3][1]))
    processes = [controller, reader]
    try:
        controller.start()
        inventory = tuple(RunResource(**r) for r in admin.request("inventory"))
        plan = RunPlan("plan:process-fixture", scope, identity, inventory, c.h.now - 1, c.h.now + 60, 10,
                       c.config["state"]["store_ref"])
        admin.request("register", plan=asdict(plan))
        reader.start()
        readback_identity = ServiceIdentity("service:independent-audit", "principal:independent-audit",
                                           "credential:audit-readonly", "sha256:" + "e" * 64)
        life = RunLifecycle(plan=plan, load_config=lambda: encoded(c.config), runtime_trust=c.trust,
                            janitor=BoundService(identity, gate), readback=BoundService(readback_identity, audit),
                            cleanup_clock=lambda: clock.value)
        c.bridge = c.make(lifecycle=life)
        signing = c.h.sign
        def gated_sign(message):
            gate.request("credential", ref=plan.ref, deadline=c.h.now + 10)
            return signing(message)
        c.h.sign = gated_sign
        yield SimpleNamespace(c=c, root=root, clock=clock, admin=admin, gate=gate, worker=worker,
                              audit=audit, plan=plan, life=life, processes=processes)
    finally:
        for endpoint, process in [(admin, controller), (audit, reader)]:
            if process.pid is not None and process.is_alive():
                try:
                    endpoint.request("stop")
                except (BindingError, OSError, EOFError):
                    pass
            if process.pid is not None:
                process.join(timeout=6)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=3)
                assert not process.is_alive()
                process.close()
        for pair in pairs:
            for connection in pair:
                connection.close()
