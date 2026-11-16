"""Independent same-user reference processes; no deployed admin isolation claim."""
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import ipaddress
import json
import multiprocessing
import os
from pathlib import Path
import secrets
import subprocess
from threading import Thread
import time
from types import SimpleNamespace
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from workload_factory_binding.evidence import BindingError, canonical, digest
from workload_factory_binding_runtime.github_bootstrap.common import Decision, document
from workload_factory_binding_runtime.hosted.lifecycle_store import LifecycleStore
from workload_factory_binding_runtime.hosted.lifecycle import (HostedLifecycle, PosixResources,
    FileResource, TokenResource, RegisteredStageReadback, process_instance, run_plan)
from workload_factory_binding_runtime.hosted.lifecycle_service import (LifecycleServer, LifecycleClient,
    CleanupRegistration, IndependentScheduler, FinalLifecyclePorts, PRIMARY, AUDIT)
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
from workload_factory_binding_runtime.hosted.readback import ObservationClient, DecisionRead, ReadBudget
from workload_factory_binding_runtime.hosted.staging import StageAuthority
from workload_factory_binding_runtime.hosted.issuance import InstallationRetirer
from workload_factory_binding_runtime.hosted.finalization import FinalizedPlan, FinalizationBinding, FinalizationBindings, FinalAuthority, finalize
from workload_factory_binding_runtime.hosted.measurement import MeasurementBindings, LaunchObservation
from workload_factory_binding_runtime.launch import ProcessLaunch
from workload_factory_binding_runtime.lifecycle import RunPlan, RunScope, RunLifecycle
from workload_factory_binding_runtime.loaders import ServiceIdentity, BoundService
from factory_binding.test_owner_integration import private_write


def pki(root):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "isolated lifecycle CA")])
    now = datetime.now(timezone.utc)
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
          .not_valid_after(now + timedelta(hours=1)).add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
          .sign(key, hashes.SHA256()))
    ca_file = root / "ca.pem"
    private_write(ca_file, ca.public_bytes(serialization.Encoding.PEM))
    certs = {}
    for role in ("server", "controller", "janitor", "observer", "worker"):
        leaf = ec.generate_private_key(ec.SECP256R1())
        builder = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, role)]))
            .issuer_name(name).public_key(leaf.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(hours=1))
            .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH if role == "server"
                else x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]), False))
        if role == "server":
            builder = builder.add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
        certificate = builder.sign(key, hashes.SHA256())
        cert, private = root / role / "cert.pem", root / role / "key.pem"
        private_write(cert, certificate.public_bytes(serialization.Encoding.PEM))
        private_write(private, leaf.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        certs[role] = (cert, private, "sha256:" + certificate.fingerprint(hashes.SHA256()).hex())
    return ca_file, certs


def track_helpers(path):
    original = subprocess.Popen
    class Tracked(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if any(str(x).endswith("/hosted/_credential_io.py") for x in self.args):
                instance, _ = process_instance(self.pid)
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                try:
                    os.write(fd, canonical({"pid": self.pid, "instance_ref": instance}) + b"\n")
                    os.fsync(fd)
                finally:
                    os.close(fd)
    subprocess.Popen = Tracked


def final_file(path):
    value = document(path.read_bytes())
    return (FinalizedPlan(canonical(value["configuration"]), canonical(value["policy"]),
                          FinalizationBinding(**value["binding"])), run_plan(value["plan"]))


def server_role(life, mode, principal, ca, certs, clock, scope, path, connection, root, excess=False):
    track_helpers(root / (mode + "-helpers.jsonl"))
    if mode == "primary":
        original_cleanup = life.cleanup
        def cleanup(*args, **kwargs):
            try:
                return original_cleanup(*args, **kwargs)
            except Exception as error:
                import traceback
                # Private fixture-only frame names; never serialize locals,
                # request bodies, headers or credential material.
                frames = [{"file": Path(f.filename).name, "line": f.lineno, "name": f.name}
                          for f in traceback.extract_tb(error.__traceback__)]
                with (root / "cleanup-errors.jsonl").open("a") as stream:
                    stream.write(json.dumps({"type": type(error).__name__, "frames": frames}) + "\n")
                raise
        life.cleanup = cleanup
        for method_name in ("observe", "cleanup"):
            selected_method = getattr(life.resources, method_name)
            def resource_operation(*args, _selected=selected_method, _name=method_name, **kwargs):
                try:
                    return _selected(*args, **kwargs)
                except Exception as error:
                    import traceback
                    frames = [{"file": Path(f.filename).name, "line": f.lineno, "name": f.name}
                              for f in traceback.extract_tb(error.__traceback__)]
                    with (root / "resource-errors.jsonl").open("a") as stream:
                        stream.write(json.dumps({"operation": _name, "type": type(error).__name__, "frames": frames}) + "\n")
                    raise
            setattr(life.resources, method_name, resource_operation)
    if mode == "primary":
        permissions = {certs["controller"][2]: PRIMARY, certs["janitor"][2]: frozenset({"cleanup", "status"})}
        if excess:
            permissions[certs["worker"][2]] = frozenset({"status"})
    else:
        permissions = {certs["controller"][2]: AUDIT - {"stage-lease"},
                       certs["observer"][2]: frozenset({"stage-lease", "cleanup-audit"})}
    server = LifecycleServer(lifecycle=life, mode=mode, principal=principal, cert_file=str(certs["server"][0]),
        key_file=str(certs["server"][1]), ca_file=str(ca), permissions=permissions,
        clock=lambda: clock.value, monotonic=time.monotonic, observation_scope=scope,
        load_final=lambda _ref, **_kwargs: final_file(path))
    connection.send(server.server_port)
    def stop():
        try:
            connection.recv()
        except EOFError:
            pass
        server.shutdown()
    thread = Thread(target=stop, daemon=True)
    thread.start()
    try:
        server.serve_forever(poll_interval=.02)
    finally:
        server.server_close()
        connection.close()


def scheduler_role(intake, clock, connection, root):
    track_helpers(root / "scheduler-helpers.jsonl")
    configuration = connection.recv()
    if configuration is None or configuration == "stop":
        return
    client = LifecycleClient(**configuration)
    scheduler = IndependentScheduler(intake=intake, client=client, clock=lambda: clock.value, monotonic=time.monotonic)
    connection.send("ready")
    while True:
        if connection.poll(.2):
            message = connection.recv()
            if message == "stop":
                return
            if message == "tick":
                try:
                    connection.send(scheduler.tick())
                except BindingError:
                    connection.send("refused")
        else:
            try:
                scheduler.tick()
            except BindingError:
                pass  # consumed cleanup requests are only reconciled, never resent


@pytest.fixture
def lh(stage, provider, tmp_path, request):
    root = tmp_path / "lifecycle"
    root.mkdir(mode=0o700)
    ctx = multiprocessing.get_context("fork")
    clock = ctx.RawValue("q", stage.v.h.now)
    provider.now = stage.v.h.now
    issuer = provider.issuer()
    issue_use = Decision(clock=lambda: provider.now, monotonic=time.monotonic)
    issuer.issue(provider.ref, provider.nonce, decision=issue_use)
    token = issuer.pending(provider.ref)
    stores = {}
    for kind in ("primary", "scheduler", "audit"):
        directory, witness = root / kind, root / (kind + "-witness")
        identity = LifecycleStore.initialize(directory, witness, kind=kind)
        stores[kind] = LifecycleStore(directory, witness, identity=identity, kind=kind)
    scheduler_parent, scheduler_child = ctx.Pipe()
    scheduler_process = ctx.Process(target=scheduler_role, args=(stores["scheduler"], clock, scheduler_child, root))
    scheduler_process.start()
    processes, pipes = [scheduler_process], [scheduler_parent]
    request.addfinalizer(lambda: cleanup_services(stage, root, processes, pipes))
    scheduler_start = int(process_instance(scheduler_process.pid)[0].split(":")[2])
    config = stage.v.selected.value()["configuration_template"]
    janitor = ServiceIdentity(**config["services"]["janitor"])
    auditor = ServiceIdentity("service:lifecycle-audit", "principal:lifecycle-audit", "credential:lifecycle-audit", digest({"audit": "isolated"}))
    shared, temporary = root / "shared", root / "temporary"
    shared.write_bytes(b"retained shared generation")
    temporary.write_bytes(b"owned temporary generation")
    selected = [FileResource(config["state"]["store_ref"], stage.v.h.ledger.path, "retained"),
        FileResource("resource:shared", shared, "shared"), FileResource("resource:temporary", temporary, "run"),
        FileResource("resource:worker-source", stage.v.paths["worker"], "run"),
        FileResource("resource:worker-configuration", stage.spec.paths["configuration"], "run")]
    for kind, store in stores.items():
        selected.append(FileResource("resource:" + kind + "-journal", store.directory / "lifecycle.sqlite", "retained"))
        selected.append(FileResource("resource:" + kind + "-witness", store.witness / "00000000.witness", "retained"))
    resources = PosixResources(files=tuple(selected), worker_ref="resource:hosted-worker",
        tokens=(TokenResource("resource:issued-capability", token, InstallationRetirer(writer=provider.routed(), observer=provider.routed())),))
    life = HostedLifecycle(plan=stage.v.selected, context=stage.v.context, policy=stage.policy,
        host_store=stage.agent.store, store=stores["primary"], intake=stores["scheduler"], audit_store=stores["audit"],
        resources=resources, janitor=janitor, auditor=auditor, host_pid_namespace=stage.agent.pid_namespace,
        scheduler={"principal_ref": "principal:lifecycle-scheduler", "pid": scheduler_process.pid,
            "start_time": scheduler_start, "boot_id": stage.scope["boot_id"]},
        final_authority_principal="principal:final-authority", cleanup_until=config["expires_at"] + 30)
    final_path = root / "accepted-final.json"
    primary_pki, audit_pki = pki(root / "primary-pki"), pki(root / "audit-pki")
    clients, origins = {}, {}
    mode = getattr(request, "param", None)
    for role, material, principal in (("primary", primary_pki, janitor.principal_ref), ("audit", audit_pki, auditor.principal_ref)):
        parent, child = ctx.Pipe()
        ca, certs = material
        process = ctx.Process(target=server_role, args=(life, role, principal, ca, certs, clock, stage.rb.scope,
            final_path, child, root, mode == "excess-worker"))
        process.start()
        processes.append(process)
        pipes.append(parent)
        assert parent.poll(8)
        origin = "https://127.0.0.1:" + str(parent.recv())
        origins[role] = origin
        def client(peer="controller", origin=origin, ca=ca, certs=certs, principal=principal):
            cert = certs[peer]
            return LifecycleClient(origin=origin, principal=principal, scope=stage.scope,
                transport=PrivateHttps(ca_file=str(ca), certificate=str(cert[0]), private_key=str(cert[1]),
                    lifecycle_origin=origin, server_certificate_digest=certs["server"][2]))
        clients[role] = client
    scheduler_client = clients["primary"]("janitor")
    scheduler_parent.send({"origin": scheduler_client.origin, "principal": scheduler_client.principal,
                           "scope": stage.scope, "transport": scheduler_client.transport})
    assert scheduler_parent.poll(8) and scheduler_parent.recv() == "ready"
    ca, certs = audit_pki
    observation = ObservationClient(origin=origins["audit"], principal_ref=auditor.principal_ref, scope=stage.rb.scope,
        transport=PrivateHttps(ca_file=str(ca), certificate=str(certs["observer"][0]), private_key=str(certs["observer"][1]),
            observation_origin=origins["audit"], server_certificate_digest=certs["server"][2]))
    authority = StageAuthority(grant=stage.authority.grant, lease=observation, grant_ref=stage.authority.ref)
    stage.agent.authority = authority
    stage.controller.authority = authority
    stage.controller.register_cleanup = CleanupRegistration(clients["primary"](), clients["audit"]())
    result = SimpleNamespace(stage=stage, root=root, life=life, clock=clock, provider=provider, issuer=issuer,
        token=token, stores=stores, processes=processes, pipes=pipes, primary=clients["primary"], audit=clients["audit"],
        shared=shared, temporary=temporary, final_path=final_path)
    result.use = lambda: Decision(clock=lambda: clock.value, monotonic=time.monotonic)
    def advance(value):
        clock.value = value
        stage.v.h.now = stage.rb.now = provider.now = value
    result.advance = advance
    def launch(*, full=False, bind=True):
        if full:
            result.launched = stage.protected.read(stage.v.context, stage.v.token, decision=result.use())
        else:
            # Lifecycle component controls reuse the already selected private
            # host/grant capability. The separate full path below exercises
            # actual public approval/source correlation and its original budget.
            decision = result.use()
            unit = stage.host.register(stage.scope["launch_ref"], decision=decision)["unit"]
            ReadBudget(decision).consume("private")
            stage.controller.register_cleanup.register(stage.scope, unit, decision=decision)
            lease = stage.agent.authority.acknowledged(stage.scope, unit, decision=decision)
            def current():
                stage.agent.authority.launch_grant(stage.scope, decision=decision)
                assert stage.agent.authority.acknowledged(stage.scope, unit, decision=decision) == lease
            value = stage.host.start(stage.scope["launch_ref"], digest(unit), decision=decision, before_send=current)
            result.launched = SimpleNamespace(state=value["state"])
        if bind:
            result.primary().call("generation", decision=result.use())
        return result.launched
    result.launch = launch
    def register_only():
        unit = stage.host.register(stage.scope["launch_ref"], decision=result.use())["unit"]
        result.primary().call("register", unit_digest=digest(unit), decision=result.use())
        result.audit().call("ack-stage", decision=result.use())
        return unit
    result.register = register_only
    def finalized():
        v, spec = stage.v, stage.spec
        process = stage.agent.children[stage.scope["launch_ref"]]
        def observer(principal):
            def read(ref, *, deadline):
                measured = ProcessLaunch.capture(process, executable=spec.paths["executable"],
                    executable_digest=spec.m["executable_digest"], worker=spec.paths["worker"],
                    configuration_file=spec.paths["configuration"], cwd=spec.paths["cwd"], artifacts=spec.artifacts)
                unit = life.state(decision=result.use())["registration"]["unit"]
                return LaunchObservation(principal, ref, stage.scope["host_ref"], stage.scope["incarnation_ref"],
                    stage.scope["boot_id"], unit["invocation_ref"], measured, clock.value, clock.value + 20)
            return read
        selected = stage.controller.protected
        read_stage = DecisionRead(RegisteredStageReadback(life).read)
        bindings = FinalizationBindings(selected, MeasurementBindings("principal:launch-observer", dict(spec.roots),
            observer("principal:launch-observer")), life.auditor.principal_ref, read_stage, life.final_authority_principal)
        frozen_raw = bytes(v.raw)
        authority = FinalAuthority(replace(bindings, plan=replace(selected, load_plan=lambda: frozen_raw),
            measurement=MeasurementBindings("principal:authority-observer", dict(spec.roots), observer("principal:authority-observer"))))
        value = finalize(v.context, v.token, bindings=bindings, authority=authority)
        config = document(value.configuration)
        state = life.state(decision=result.use())
        scope = RunScope(value.binding.config_digest, config["case_ref"], config["launch"]["run_id"],
            config["launch"]["run_attempt"], **config["lifecycle"])
        plan = RunPlan("plan:hosted-final", scope, janitor, life.resources_for(state), clock.value,
            min(value.binding.expires_at, state["registration"]["expires_at"]), 30, config["state"]["store_ref"])
        result.finalized, result.plan = value, plan
        private_write(final_path, canonical({"configuration": config, "policy": document(value.policy),
                                            "binding": asdict(value.binding), "plan": asdict(plan)}))
        return value, plan
    result.finalize = finalized
    def takeover():
        result.primary().call("prepare", decision=result.use())
        result.audit().call("ack-final", decision=result.use())
        return result.primary().call("release", decision=result.use())
    result.takeover = takeover
    def runtime():
        ports = FinalLifecyclePorts(primary=result.primary(), audit=result.audit("observer"), operation=result.use(),
            plan_ref=result.plan.ref, clock=lambda: clock.value, monotonic=time.monotonic)
        # Actual final-authority output is retained separately from the runtime
        # candidate. The operator reader observes that immutable source record.
        def readback():
            actual, _plan = final_file(final_path)
            selected = document(actual.configuration)
            value = {name: selected[name] for name in ("case_ref", "launch", "sources", "dependency_digest",
                "composition_digest", "protection", "services", "state", "lifecycle")}
            value.update(profile=selected["profile"], principal_ref=stage.v.c.trust.readback_principal,
                config_digest=actual.binding.config_digest, observed_at=clock.value,
                expires_at=min(actual.binding.expires_at, clock.value + 10))
            return canonical(value)
        trust = replace(stage.v.c.trust, approved_config_digest=result.finalized.binding.config_digest,
                        load_readback=readback)
        return RunLifecycle(plan=result.plan, load_config=lambda:result.finalized.configuration, runtime_trust=trust,
            janitor=BoundService(janitor, ports), readback=BoundService(auditor, ports), cleanup_clock=lambda:clock.value)
    result.runtime = runtime
    (root / "lifecycle-processes.json").write_bytes(canonical({"generations": [
        {"pid": p.pid, "instance_ref": process_instance(p.pid)[0]} for p in processes]}))
    try:
        yield result
    finally:
        pass  # request finalizer also covers setup failures


def cleanup_services(stage, root, processes, pipes):
    for process, connection in zip(processes, pipes):
        if process.is_alive():
            try:
                connection.send("stop")
            except (BrokenPipeError, EOFError):
                pass
        process.join(timeout=12)
        if process.is_alive():
            process.kill()
            process.join(timeout=3)
        assert not process.is_alive()
        connection.close()
    stage.agent.close()
    records = []
    for path in root.glob("*-helpers.jsonl"):
        records.extend(json.loads(line) for line in path.read_text().splitlines())
    end = time.monotonic() + 12
    while any(process_instance(r["pid"])[0] == r["instance_ref"] for r in records) and time.monotonic() < end:
        time.sleep(.02)
    alive = [r for r in records if process_instance(r["pid"])[0] == r["instance_ref"]]
    (root / "helper-cleanup.json").write_bytes(canonical({"generations": records, "matching_alive": alive}))
    assert not alive
