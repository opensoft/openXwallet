"""Controller-owned launch fixture; same-user scope is deliberately explicit."""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
from pathlib import Path
import select
import subprocess
import sys

import pytest

from workload_factory_binding.evidence import artifact_digest, byte_digest, canonical, digest
from workload_factory_binding_runtime import supervisor as module
from workload_factory_binding_runtime.loaders import BoundService, ServiceIdentity
from workload_factory_binding_runtime.supervisor import (
    ProcessLaunch, SupervisorObserver, SupervisorPeer, SupervisedBridge, worker_configuration,
)
from .composition_fixture import c, configuration


@pytest.fixture
def s(c, tmp_path):
    worker = tmp_path / "controlled-worker.py"
    worker.write_bytes(Path(__file__).with_name("supervisor_worker.py").read_bytes())
    configuration_file = tmp_path / "worker.json"
    executable = Path(sys.executable).resolve()
    artifacts = {"worker": worker, "supervisor": Path(module.__file__).resolve()}
    for role, path in artifacts.items():
        c.config["sources"][role]["digest"] = byte_digest(path.read_bytes())
    actual_config = worker_configuration(c.config, c.h.policy)
    configuration_file.write_bytes(canonical(actual_config))
    process = subprocess.Popen([str(executable), "-I", "-B", str(worker), str(configuration_file)],
                               cwd=tmp_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
    try:
        assert select.select([process.stdout], [], [], 5)[0], "fixture worker readiness timeout"
        assert process.stdout.readline() == b"ready\n"
        plan = ProcessLaunch.capture(process, executable=executable,
                                     executable_digest="sha256:" + hashlib.sha256(executable.read_bytes()).hexdigest(),
                                     worker=worker, configuration_file=configuration_file, cwd=tmp_path,
                                     artifacts=artifacts)
        c.h.policy["composition_digest"] = artifact_digest(dict(plan.artifacts), plan.expected_configuration(actual_config))
        c.config["composition_digest"] = c.h.policy["composition_digest"]
        c.h.artifacts, c.h.configuration = dict(plan.artifacts), plan.expected_configuration(actual_config)
        c.h.reset_evidence()
        c.reselect_policy()
        c.worker_config, c.worker, c.configuration_file = actual_config, worker, configuration_file
        c.process, c.plan = process, plan
        selected = c.config["services"]["supervisor"]
        c.peer = SupervisorPeer(selected["principal_ref"], selected["credential_ref"], c.h.now - 1, c.h.now + 30)
        c.supervisor_source = type(c.r.source)(transport=c.r.transport, clock=c.r.clock.wall,
                                             monotonic=lambda: c.r.clock.mono)

        def observer(**overrides):
            arguments = dict(load_config=lambda: canonical(c.config), trust=c.trust,
                             services={name: c.services[name] for name in ("records", "challenge")},
                             issuer_source=c.supervisor_source, launch=plan, private_key=c.h.supervisor,
                             allowed_gate=(c.peer.principal_ref, c.peer.credential_ref))
            arguments.update(overrides)
            return SupervisorObserver(**arguments)
        c.observer = observer()
        c.make_observer = observer
        c.payload = lambda: {"challenge_id": c.h.challenge.id, "request": deepcopy(c.h.request), "token": c.h.token}
        c.observe = lambda: c.observer.observe(c.payload(), peer=c.peer, deadline=c.h.now + 30)

        class Connector:
            def observe(self, payload, *, deadline):
                return canonical(c.observer.observe(payload, peer=c.peer, deadline=deadline))
        c.supervisor = BoundService(ServiceIdentity(**c.config["services"]["supervisor"]), Connector())
        c.supervised = SupervisedBridge(bridge=c.bridge, supervisor=c.supervisor)
        c.supervised_run = lambda: c.supervised.sign(c.h.challenge.id, c.h.request, c.h.token)
        yield c
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream:
                stream.close()
        assert process.poll() is not None
