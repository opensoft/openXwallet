"""Actual controlled process measurement and existing observation integration."""
from copy import deepcopy
from dataclasses import asdict, replace
import os

import pytest

from workload_factory_binding.evidence import BindingError, canonical, verify_observation
from workload_factory_binding_runtime.supervisor import SupervisorPeer, SupervisedBridge
from workload_factory_binding_runtime import supervisor as module
from .supervisor_fixture import s, c, configuration


def test_controlled_live_launch_yields_existing_observation_and_one_proof(s):
    observation = s.observe()
    verify_observation(observation, policy=s.h.policy, request=s.h.request, token=s.h.token,
                       challenge=s.h.challenge, claims=s.h.claims, now=s.h.now)
    result = s.supervised_run()
    assert result["assurance"] == "possession"
    assert result["human_approval"] is False
    assert s.h.calls == 1


@pytest.mark.parametrize("member", ["worker", "supervisor"])
def test_changed_selected_source_refuses(s, member, tmp_path):
    if member == "worker":
        s.worker.write_text("print('different actual worker')\n")
    else:
        alternate = tmp_path / "different-supervisor.py"
        alternate.write_text("different source")
        s.observer = s.make_observer(launch=replace(s.plan, artifacts={"worker": s.worker, "supervisor": alternate}))
    with pytest.raises(BindingError):
        s.observe()
    assert s.h.calls == 0


@pytest.mark.parametrize("field", ["binding", "services", "launch", "sources", "dependency_digest"])
def test_actual_worker_configuration_binding_cannot_be_self_reported(s, field):
    actual = deepcopy(s.worker_config)
    actual[field] = "changed"
    s.configuration_file.write_bytes(canonical(actual))
    with pytest.raises(BindingError):
        s.observe()
    assert s.h.calls == 0


def test_exited_or_reused_process_identity_refuses(s):
    s.process.terminate()
    s.process.wait(timeout=5)
    with pytest.raises(BindingError):
        s.observe()


def test_other_process_generation_refuses(s):
    s.observer = s.make_observer(launch=replace(s.plan, start_time=s.plan.start_time + 1))
    with pytest.raises(BindingError):
        s.observe()


def test_wrong_actual_executable_digest_refuses(s):
    s.observer = s.make_observer(launch=replace(s.plan, executable_digest="sha256:" + "f" * 64))
    with pytest.raises(BindingError):
        s.observe()


@pytest.mark.parametrize("field,value", [("principal_ref", "principal:worker_channel"),
    ("credential_ref", "credential:worker_channel"), ("issued_at", 9999999999), ("expires_at", 0)])
def test_worker_or_expired_peer_cannot_obtain_supervisor_signature(s, field, value):
    peer = replace(s.peer, **{field: value})
    payload, deadline = s.payload(), s.h.now + 30
    with pytest.raises(BindingError):
        s.observer.observe(payload, peer=peer, deadline=deadline)


@pytest.mark.parametrize("field", ["policy", "private_key", "artifacts", "configuration", "pid", "measurement"])
def test_worker_cannot_select_policy_key_paths_or_measurement(s, field):
    payload = s.payload()
    payload[field] = {"approved": True}
    with pytest.raises(BindingError):
        s.observer.observe(payload, peer=s.peer, deadline=s.h.now + 30)


def test_observation_key_must_match_selected_policy(s):
    from cryptography.hazmat.primitives.asymmetric import ed25519
    s.observer = s.make_observer(private_key=ed25519.Ed25519PrivateKey.generate())
    with pytest.raises(BindingError):
        s.observe()


def test_actual_command_line_and_cwd_are_measured(s, tmp_path):
    changed = replace(s.plan, cwd=tmp_path / "different-working-directory")
    s.observer = s.make_observer(launch=changed)
    with pytest.raises(BindingError):
        s.observe()


def test_symlink_configuration_is_not_measurement(s):
    actual = s.configuration_file.with_name("other.json")
    s.configuration_file.rename(actual)
    s.configuration_file.symlink_to(actual)
    with pytest.raises(BindingError):
        s.observe()


def test_selected_connector_identity_required(s):
    wrong = replace(s.supervisor, identity=replace(s.supervisor.identity, trust_digest="sha256:" + "f" * 64))
    bridge = SupervisedBridge(bridge=s.bridge, supervisor=wrong)
    with pytest.raises(BindingError):
        bridge.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert s.h.calls == 0


def test_replayed_observation_for_another_token_refuses_before_custody(s):
    observed = s.observe()
    class Replay:
        def observe(self, _payload, *, deadline):
            return canonical(observed)
    s.h.claims["jti"] = "token:another"
    s.h.reset_evidence()
    bridge = SupervisedBridge(bridge=s.bridge, supervisor=replace(s.supervisor, target=Replay()))
    with pytest.raises(BindingError):
        bridge.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert s.h.calls == 0


def test_denied_peer_cannot_reach_trusted_configuration_loader(s):
    calls = []
    def forbidden():
        calls.append(True)
        raise RuntimeError("protected configuration")
    observer = s.make_observer(load_config=forbidden)
    worker = SupervisorPeer("principal:worker_channel", "credential:worker_channel", s.h.now - 1, s.h.now + 30)
    payload = s.payload()
    deadline = s.h.now + 30
    with pytest.raises(BindingError, match="^supervisor-peer-denied$"):
        observer.observe(payload, peer=worker, deadline=deadline)
    assert calls == []


def test_gate_access_policy_must_match_approved_service_selection(s):
    observer = s.make_observer(allowed_gate=("principal:unapproved", "credential:unapproved"))
    peer = SupervisorPeer("principal:unapproved", "credential:unapproved", s.h.now - 1, s.h.now + 30)
    payload = s.payload()
    deadline = s.h.now + 30
    with pytest.raises(BindingError):
        observer.observe(payload, peer=peer, deadline=deadline)


@pytest.mark.parametrize("raw", [b"{}", b'{"a":NaN}', b'{"a":1,"a":2}', b" " * 16385])
def test_invalid_or_oversized_actual_configuration_refuses(s, raw):
    s.configuration_file.write_bytes(raw)
    with pytest.raises(BindingError):
        s.observe()


def test_fifo_configuration_does_not_block_measurement(s):
    s.configuration_file.unlink()
    os.mkfifo(s.configuration_file)
    with pytest.raises(BindingError):
        s.observe()


def test_large_source_is_bounded_before_observation(s):
    s.worker.write_bytes(b"x" * (1024 * 1024 + 1))
    with pytest.raises(BindingError):
        s.observe()


def test_expiry_during_measurement_emits_no_observation(s, monkeypatch):
    original = module.ProcessLaunch.measure
    def delayed(plan, *args, **kwargs):
        result = original(plan, *args, **kwargs)
        s.h.now += 30
        return result
    monkeypatch.setattr(module.ProcessLaunch, "measure", delayed)
    with pytest.raises(BindingError):
        s.observe()
    assert s.h.calls == 0


@pytest.mark.parametrize("drift", ["source", "process", "policy", "protection"])
def test_drift_after_observation_signing_is_rechecked(s, monkeypatch, drift):
    original = module.observation_payload
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        if drift == "source":
            s.worker.write_text("changed after measurement")
        elif drift == "process":
            s.process.terminate()
            s.process.wait(timeout=5)
        elif drift == "policy":
            s.records.value["revision"] += 1
        else:
            s.readback["protection"]["can_admins_bypass"] = True
        return result
    monkeypatch.setattr(module, "observation_payload", changed)
    with pytest.raises(BindingError):
        s.observe()
    assert s.h.calls == 0


@pytest.mark.parametrize("raw", [b"[]", b'{"payload":1,"payload":2}', b" " * 16385])
def test_malformed_supervisor_response_cannot_reach_custody(s, raw):
    class Malformed:
        def observe(self, _payload, *, deadline):
            return raw
    supervised = SupervisedBridge(bridge=s.bridge, supervisor=replace(s.supervisor, target=Malformed()))
    with pytest.raises(BindingError):
        supervised.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert s.h.calls == 0


def test_remote_observation_cannot_extend_local_deadline(s):
    observation = s.observe()
    s.context = replace(s.context, expires_at=s.h.now + 10)
    class TooLong:
        def observe(self, _payload, *, deadline):
            return canonical(observation)
    supervised = SupervisedBridge(bridge=s.bridge, supervisor=replace(s.supervisor, target=TooLong()))
    with pytest.raises(BindingError, match="^supervisor-deadline-mismatch$"):
        supervised.sign(s.h.challenge.id, s.h.request, s.h.token)
    assert s.h.calls == 0


def test_owning_proof_verifier_accepts_measured_supervised_result(s):
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    s.h.binding = TrustedKeyBinding(**asdict(s.h.binding))
    bridge = s.make(create_proof=create_proof)
    supervised = SupervisedBridge(bridge=bridge, supervisor=s.supervisor)
    result = supervised.sign(s.h.challenge.id, s.h.request, s.h.token)
    checked = verify_proof(result["proof"], expected_digest=s.h.challenge.digest, binding=s.h.binding, now=s.h.now)
    assert checked.subject_ref == s.h.binding.subject_ref
    assert result["human_approval"] is False


def test_observer_rejects_clock_regression_across_config_preflight(s):
    now = s.h.now
    samples = iter([now, now, now + 10] + [now + 5] * 10)
    trust = replace(s.trust, clock=lambda: next(samples))
    observer = s.make_observer(trust=trust)
    peer, deadline = s.peer, now + 30
    with pytest.raises(BindingError, match="^supervisor-clock-unavailable$"):
        module._ObservationUse(observer, peer, deadline)
