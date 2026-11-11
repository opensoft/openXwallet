from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa

from workload_factory_binding import BindingError, ReplayLedger
from workload_factory_binding.evidence import (
    CLAIMS, OBS_CONTEXT, canonical, encode64, observe_artifacts,
)
from .conftest import jwt


def refused(h):
    with pytest.raises(BindingError):
        h.run()
    assert h.calls == 0


def test_permitted(h):
    result = h.run()
    assert h.calls == 1
    assert result["proof"]["unit_digest"] == h.challenge.digest
    assert result["authority"]["actor_ref"] == "agent:qa"
    assert result["authority"]["grant_chain"] == ["grant:child", "grant:root"]
    assert result["human_approval"] is False


@pytest.mark.parametrize("claim", sorted(CLAIMS | {"run_id", "run_attempt", "iss", "aud"}))
def test_each_workload_claim_is_bound(h, claim):
    h.claims[claim] = "other"
    h.reset_evidence()
    refused(h)


@pytest.mark.parametrize("claim", sorted(CLAIMS | {"run_id", "run_attempt", "jti", "iat", "nbf", "exp"}))
def test_missing_claim(h, claim):
    del h.claims[claim]
    h.reset_evidence()
    refused(h)


@pytest.mark.parametrize("updates", [
    {"exp": 1794400000}, {"iat": 1794400001}, {"nbf": 1794400001},
    {"exp": 1794400301}, {"iat": True}, {"nbf": "1794400000"},
    {"exp": None}, {"jti": "*"}, {"aud": ["factory:qa"]},
])
def test_token_times_and_types(h, updates):
    h.claims.update(updates)
    h.reset_evidence()
    refused(h)


def test_untrusted_signature(h):
    h.token = jwt(rsa.generate_private_key(public_exponent=65537, key_size=2048), h.claims)
    refused(h)


@pytest.mark.parametrize("header", [
    {"alg": "none", "typ": "JWT", "kid": "fixture-issuer"},
    {"alg": "HS256", "typ": "JWT", "kid": "fixture-issuer"},
    {"alg": "RS256", "typ": "JWT", "kid": "missing"},
    {"alg": "RS256", "typ": "JWT", "kid": "fixture-issuer", "jku": "https://fixture.invalid/keys"},
])
def test_header_refusal(h, header):
    h.token = jwt(h.issuer_key, h.claims, header)
    refused(h)


def test_duplicate_claim(h):
    raw = canonical(h.claims)
    h.token = jwt(h.issuer_key, h.claims, raw_claims=raw[:-1] + b',"jti":"another"}')
    refused(h)


@pytest.mark.parametrize("mutation", [
    lambda h: h.keys.update(expires_at=h.now),
    lambda h: h.keys["keys"].append(deepcopy(h.keys["keys"][0])),
    lambda h: h.keys["keys"][0].update(kty="EC"),
    lambda h: h.keys["keys"][0].update(use="enc"),
    lambda h: h.keys["keys"][0].update(key_ops=["sign"]),
    lambda h: h.keys["keys"][0].update(d="private"),
    lambda h: h.keys["keys"].clear(),
])
def test_bad_current_issuer_snapshot(h, mutation):
    mutation(h)
    refused(h)


@pytest.mark.parametrize("field", ["binding_ref", "wallet_ref", "key_ref", "subject_ref", "custody_ref"])
def test_current_registry_identity(h, field):
    h.binding = replace(h.binding, **{field: "other:value"})
    refused(h)


@pytest.mark.parametrize("updates", [{"revision": 2}, {"revoked": True}, {"expires_at": 0},
                                     {"public_key": b"x" * 32}, {"not_before": 1794400001}])
def test_current_registry_state(h, updates):
    h.binding = replace(h.binding, **updates)
    refused(h)


@pytest.mark.parametrize("where,updates", [
    ("grant:root", {"state": "revoked"}),
    ("grant:child", {"state": "revoked"}),
    ("grant:root", {"expires_at": "2020-01-01T00:00:00Z"}),
    ("grant:child", {"expires_at": "2030-01-01T00:00:00Z"}),
    ("grant:child", {"parent_grant_ref": "missing"}),
    ("grant:root", {"parent_grant_ref": "grant:child"}),
    ("grant:root", {"audience": {"wallet_ref": "other", "holder_ref": "agent:qa"}}),
    ("grant:child", {"issued_at": "2020-01-01T00:00:00Z"}),
])
def test_chain_refusals(h, where, updates):
    h.policy["grants"][where].update(updates)
    refused(h)


@pytest.mark.parametrize("field,value", [
    ("acts", ["prove", "extra"]), ("objects", ["object:qa", "object:extra"]),
    ("authority_tier", "approve"), ("objects", []), ("acts", ["*"]),
    ("approval_posture", {"hermes_approval_required_before_apply": False,
                         "authority_agents_may_approve": False,
                         "human_escalation_required_for": []}),
])
def test_non_widening_scope(h, field, value):
    h.policy["grants"]["grant:child"]["scope"][field] = value
    refused(h)


@pytest.mark.parametrize("change", [
    lambda h: h.request.update(act="approve"),
    lambda h: h.request.update(object_ref="object:other"),
    lambda h: h.request.update(run_attempt="2"),
    lambda h: h.request.update(extra="ignored"),
    lambda h: h.policy.update(expires_at=h.now),
    lambda h: h.policy["wallet"].update(state="revoked"),
    lambda h: h.policy["wallet"]["holder"].update(holder_class="human"),
    lambda h: h.policy["wallet"]["custody"].update(model="software"),
    lambda h: h.policy.update(revision=2),
    lambda h: h.policy["claims"].update(repository_id="*"),
    lambda h: h.policy.update(composition_digest="sha256:" + "f" * 64),
])
def test_policy_request_and_wallet(h, change):
    change(h)
    refused(h)


@pytest.mark.parametrize("field,value", [
    ("token_digest", "sha256:" + "0" * 64),
    ("challenge_digest", "sha256:" + "0" * 64),
    ("request_digest", "sha256:" + "0" * 64),
    ("composition_digest", "sha256:" + "0" * 64),
    ("policy_revision", 2), ("run_id", "other"),
    ("key_ref", "key:other"), ("grant_ref", "grant:other"),
    ("issued_at", 1794400001), ("expires_at", 1794400000),
    ("expires_at", 1794400061),
])
def test_observation_binding(h, field, value):
    h.observation["payload"][field] = value
    # Re-sign so this tests binding/time rather than just signature corruption.
    h.observation["signature"] = encode64(h.supervisor.sign(
        OBS_CONTEXT + canonical(h.observation["payload"])))
    refused(h)


def test_untrusted_supervisor(h):
    h.observation["signature"] = encode64(ed25519.Ed25519PrivateKey.generate().sign(
        OBS_CONTEXT + canonical(h.observation["payload"])))
    refused(h)


def test_self_supervision_refused(h):
    h.policy["supervisor_public_key"] = encode64(h.binding.public_key)
    h.supervisor = h.wallet_key
    h.reset_evidence()
    refused(h)


def test_observer_reads_file(h):
    h.artifact.write_text("changed\n")
    with pytest.raises(BindingError, match="composition-mismatch"):
        h.reset_evidence()
    assert h.calls == 0


def test_observer_refuses_symlink(h):
    target = h.directory / "target"
    target.write_text("target")
    h.artifact.unlink()
    h.artifact.symlink_to(target)
    with pytest.raises(BindingError):
        h.reset_evidence()


def test_restart_replay(h):
    h.run()
    h.ledger = ReplayLedger(h.directory / "ledger")
    h.gate = h.make_gate()
    with pytest.raises(BindingError, match="replay-refused"):
        h.run()
    assert h.calls == 1


@pytest.mark.parametrize("reuse", ["token", "challenge"])
def test_both_replay_identities_reserved(h, reuse):
    h.run()
    if reuse == "challenge":
        h.claims["jti"] = "token:2"
        h.reset_evidence()
    else:
        h.challenge = replace(h.challenge, id="challenge:2")
        h.observation = observe_artifacts(
            policy=h.policy, request=h.request, token=h.token, challenge=h.challenge,
            artifacts=h.artifacts, configuration=h.configuration, private_key=h.supervisor,
            now=h.now, expires_at=h.now + 60)
    with pytest.raises(BindingError, match="replay-refused"):
        h.run()
    assert h.calls == 1


def test_concurrent_replay(h):
    def attempt(_):
        try:
            return h.run()["human_approval"]
        except BindingError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, range(4)))
    assert results.count(False) == 1
    assert results.count("replay-refused") == 3
    assert h.calls == 1


def test_sign_failure_consumed(h):
    h.fail_signing = True
    with pytest.raises(BindingError, match="signer-unavailable"):
        h.run()
    h.fail_signing = False
    with pytest.raises(BindingError, match="replay-refused"):
        h.run()
    assert h.calls == 1


def test_revocation_during_sign_no_output(h):
    h.on_sign = lambda: h.policy["grants"]["grant:root"].update(state="revoked")
    with pytest.raises(BindingError, match="inactive-grant"):
        h.run()
    assert h.calls == 1


def test_state_outage_no_sign(h):
    h.ledger.path.unlink()
    refused(h)


def test_private_state(h, tmp_path):
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir(mode=0o755)
    with pytest.raises(BindingError, match="unsafe-state"):
        ReplayLedger(unsafe)
    assert h.ledger.path.stat().st_mode & 0o077 == 0


def test_loader_outage_no_sign(h):
    def unavailable():
        raise RuntimeError("not exposed")
    h.gate = h.make_gate(load_policy=unavailable)
    with pytest.raises(BindingError, match="trusted-input-unavailable"):
        h.run()
    assert h.calls == 0


@pytest.mark.parametrize("field,value", [
    ("distinct_holder_constraint_refs", ["separation:required"]),
    ("unknown_constraint", True),
])
def test_unsupported_grant_constraints_refuse(h, field, value):
    h.policy["grants"]["grant:child"][field] = value
    refused(h)


def test_wallet_public_key_must_match_registry(h):
    from .conftest import multibase
    h.policy["wallet"]["key_reference"]["public_key_multibase"] = multibase(b"x" * 32)
    refused(h)


def test_boolean_observation_revision_refused(h):
    h.observation["payload"]["policy_revision"] = True
    h.observation["signature"] = encode64(h.supervisor.sign(
        OBS_CONTEXT + canonical(h.observation["payload"])))
    refused(h)


def test_operator_records_pass_pinned_canonical_validator(h, tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    import yaml

    sample = tmp_path / "operator-records"
    sample.mkdir()
    (sample / "records.yaml").write_text(yaml.safe_dump_all(
        [h.policy["wallet"], *h.policy["grants"].values()], sort_keys=True))
    entrypoint = Path(__file__).resolve().parents[2] / "scripts/validate-openxwallet.py"
    result = subprocess.run([sys.executable, str(entrypoint), str(sample), "--strict"],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout
    assert "0 error(s), 0 warning(s)" in result.stdout
