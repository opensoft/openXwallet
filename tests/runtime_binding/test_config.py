"""Internal grammar and trusted readback vectors; synthetic, never live evidence."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from workload_factory_binding.evidence import BindingError, digest
from workload_factory_binding_runtime import DISCOVERY_URL, ISSUER, JWKS_URL
from workload_factory_binding_runtime.config import (
    PROFILE, SERVICE_ROLES, SOURCE_ROLES, RuntimeTrust, validate_config,
)
from factory_binding.conftest import jwt

NOW = 1800000000
DIGEST = "sha256:" + "a" * 64


def encoded(value):
    return json.dumps(value, separators=(",", ":")).encode()


@pytest.fixture
def configuration():
    sources = {name: {"repository": "fixture/pilot", "commit": "b" * 40,
                      "path": "src/" + name, "digest": DIGEST} for name in SOURCE_ROLES}
    sources["caller_workflow"]["path"] = ".github/workflows/caller.yml"
    sources["reusable_workflow"]["path"] = ".github/workflows/reusable.yml"
    launch = {
        "repository": "fixture/pilot", "repository_id": "123", "repository_owner": "fixture",
        "repository_owner_id": "456", "environment": "qualification",
        "sub": "repo:fixture/pilot:environment:qualification", "ref": "refs/heads/main",
        "sha": "b" * 40, "workflow_sha": "b" * 40, "job_workflow_sha": "b" * 40,
        "workflow_ref": "fixture/pilot/.github/workflows/caller.yml@" + "b" * 40,
        "job_workflow_ref": "fixture/pilot/.github/workflows/reusable.yml@" + "b" * 40,
        "run_id": "789", "run_attempt": "1",
    }
    return {
        "profile": PROFILE, "revision": 1, "not_before": NOW - 1, "expires_at": NOW + 120,
        "case_ref": "case:synthetic-config", "sources": sources, "dependency_digest": DIGEST,
        "composition_digest": DIGEST,
        "issuer": {"issuer": ISSUER, "discovery": DISCOVERY_URL, "jwks": JWKS_URL,
                   "audience": "factory:qa"}, "launch": launch,
        "protection": {"repository_id": "123", "environment_id": "101",
                       "environment": "qualification", "reviewer_ids": [{"type": "Team", "id": "12"}],
                       "prevent_self_review": True, "can_admins_bypass": False,
                       "deployment_refs": ["refs/heads/main"]},
        "authority": {"policy_ref": "policy:pilot", "policy_revision": 1, "policy_digest": DIGEST,
                      "subject_ref": "agent:pilot", "wallet_ref": "wallet:pilot", "key_ref": "key:pilot",
                      "custody_ref": "custody:pilot", "grant_ref": "grant:pilot"},
        "services": {role: {"service_ref": "service:" + role, "principal_ref": "principal:" + role,
                            "credential_ref": "credential:" + role, "trust_digest": DIGEST}
                     for role in SERVICE_ROLES},
        "state": {"store_ref": "store:pilot", "initialization_ref": "init:pilot",
                  "retention_ref": "retention:pilot", "recovery_ref": "recovery:pilot"},
        "lifecycle": {"lease_ref": "lease:pilot", "cleanup_ref": "cleanup:pilot",
                      "receipt_retention_ref": "retention:receipt"},
    }


def trust_for(configuration):
    approved = digest(configuration)
    observed = {name: deepcopy(configuration.get(name)) for name in (
        "case_ref", "launch", "sources", "dependency_digest", "composition_digest",
        "protection", "services", "state", "lifecycle")}
    observed.update(profile=PROFILE, principal_ref="principal:operator", config_digest=approved,
                    observed_at=NOW - 1, expires_at=NOW + 30)
    trust = RuntimeTrust(approved, "principal:operator", lambda: encoded(observed), lambda: NOW)
    return trust, observed


def validate(configuration, trust=None):
    return validate_config(encoded(configuration), trust=trust or trust_for(configuration)[0])


def test_valid_selection_is_immutable_short_lived_and_separate_from_worker(configuration):
    result = validate(configuration)
    assert result.config_digest == digest(configuration)
    assert result.checked_at == NOW
    assert result.valid_until == NOW + 30
    assert dict(result.selection["launch"]) == configuration["launch"]
    with pytest.raises(TypeError):
        result.selection["launch"]["sha"] = "c" * 40
    with pytest.raises(TypeError):
        result.selection["protection"]["reviewer_ids"][0]["id"] = "99"
    configuration["launch"]["sha"] = "c" * 40
    assert result.selection["launch"]["sha"] == "b" * 40


@pytest.mark.parametrize("field", ["profile", "revision", "not_before", "expires_at", "case_ref", "sources",
    "dependency_digest", "composition_digest", "issuer", "launch", "protection", "authority", "services", "state", "lifecycle"])
def test_every_group_is_mandatory(configuration, field):
    del configuration[field]
    with pytest.raises(BindingError, match="^invalid-runtime-config$"):
        validate(configuration)


@pytest.mark.parametrize("role", sorted(SOURCE_ROLES))
def test_each_source_required(configuration, role):
    del configuration["sources"][role]
    with pytest.raises(BindingError):
        validate(configuration)


@pytest.mark.parametrize("role", sorted(SERVICE_ROLES))
def test_each_service_required(configuration, role):
    del configuration["services"][role]
    with pytest.raises(BindingError):
        validate(configuration)


@pytest.mark.parametrize("path,value", [
    (("revision",), True), (("revision",), 0), (("profile",), "approved"),
    (("case_ref",), "case:pending"), (("sources", "adapter", "commit"), "main"),
    (("sources", "adapter", "commit"), "0" * 40), (("sources", "adapter", "commit"), "B" * 40),
    (("sources", "adapter", "path"), "../source.py"), (("sources", "adapter", "path"), "/source.py"),
    (("sources", "adapter", "path"), "C:\\source.py"),
    (("sources", "adapter", "repository"), "pending/repo"),
    (("dependency_digest",), "sha256:pending"), (("composition_digest",), None),
    (("issuer", "jwks"), "https://worker.invalid/keys"), (("issuer", "discovery"), JWKS_URL),
    (("issuer", "issuer"), "https://worker.invalid"), (("issuer", "audience"), "pending"),
    (("launch", "sub"), "pending"), (("launch", "run_id"), "0001"),
    (("launch", "run_attempt"), True), (("launch", "repository_id"), "0"),
    (("launch", "sha"), "c" * 40), (("launch", "workflow_sha"), "c" * 40),
    (("launch", "job_workflow_sha"), "c" * 40),
    (("launch", "workflow_ref"), "fixture/pilot/.github/workflows/caller.yml@main"),
    (("launch", "repository_owner"), "other"), (("launch", "ref"), "refs/heads/*"),
    (("protection", "environment_id"), "pending"), (("protection", "repository_id"), "999"),
    (("protection", "environment"), "other"), (("protection", "reviewer_ids"), []),
    (("protection", "reviewer_ids"), [{"type": "User", "id": "0"}]),
    (("protection", "prevent_self_review"), 1), (("protection", "can_admins_bypass"), True),
    (("protection", "deployment_refs"), ["refs/heads/other"]),
    (("protection", "deployment_refs"), ["refs/heads/main", "refs/heads/main"]),
    (("services", "custody", "service_ref"), "https://worker.invalid"),
    (("services", "custody", "credential_ref"), "credential:pending"),
    (("services", "registry", "trust_digest"), None), (("authority", "policy_revision"), True),
    (("authority", "policy_digest"), "latest"), (("state", "store_ref"), "../state"),
    (("state", "initialization_ref"), "init:unknown"), (("lifecycle", "cleanup_ref"), "pending"),
])
def test_invalid_or_floating_selections_refuse_even_with_matching_approval(configuration, path, value):
    target = configuration
    for name in path[:-1]:
        target = target[name]
    target[path[-1]] = value
    with pytest.raises(BindingError, match="^invalid-runtime-config$"):
        validate(configuration)


@pytest.mark.parametrize("group", [None, "issuer", "launch", "protection", "authority", "state", "lifecycle"])
def test_worker_overrides_and_extra_fields_refuse(configuration, group):
    target = configuration if group is None else configuration[group]
    target["worker_authenticated"] = True
    with pytest.raises(BindingError):
        validate(configuration)


def test_approval_is_external_not_a_self_hash_or_flag(configuration):
    trust, _ = trust_for(configuration)
    configuration["case_ref"] = "case:changed"
    calls = []
    trust = replace(trust, load_readback=lambda: calls.append(True))
    with pytest.raises(BindingError, match="^runtime-config-unapproved$"):
        validate(configuration, trust)
    assert calls == []


@pytest.mark.parametrize("field", ["case_ref", "launch", "sources", "dependency_digest", "composition_digest",
                                   "protection", "services", "state", "lifecycle", "principal_ref", "config_digest"])
def test_each_independent_readback_binding_refuses_when_changed(configuration, field):
    trust, observed = trust_for(configuration)
    observed[field] = "changed"
    with pytest.raises(BindingError, match="^runtime-readback-mismatch$"):
        validate(configuration, trust)


def test_readback_cannot_claim_boolean_protection_with_numeric_one(configuration):
    trust, observed = trust_for(configuration)
    observed["protection"]["prevent_self_review"] = 1
    with pytest.raises(BindingError, match="^runtime-readback-mismatch$"):
        validate(configuration, trust)


@pytest.mark.parametrize("field,value", [("observed_at", NOW + 1), ("observed_at", NOW - 61),
    ("observed_at", True), ("expires_at", NOW), ("expires_at", NOW + 60)])
def test_readback_time_is_fresh_and_bounded(configuration, field, value):
    trust, observed = trust_for(configuration)
    observed[field] = value
    with pytest.raises(BindingError, match="^runtime-readback-expired$"):
        validate(configuration, trust)


def test_clock_rechecked_after_blocking_readback(configuration):
    trust, _ = trust_for(configuration)
    samples = iter([NOW, NOW + 30])
    with pytest.raises(BindingError, match="^runtime-readback-expired$"):
        validate(configuration, replace(trust, clock=lambda: next(samples)))


@pytest.mark.parametrize("samples", [[NOW, NOW - 1], [NOW, NOW + 120], [NOW + 120], [NOW - 2]])
def test_config_expiry_or_clock_regression_refuses(configuration, samples):
    trust, _ = trust_for(configuration)
    stamps = iter(samples)
    with pytest.raises(BindingError, match="^runtime-config-inactive$"):
        validate(configuration, replace(trust, clock=lambda: next(stamps)))


@pytest.mark.parametrize("value", [True, -1, float("nan"), NOW + .5, None])
def test_invalid_clock_refuses(configuration, value):
    trust, _ = trust_for(configuration)
    with pytest.raises(BindingError, match="^runtime-clock-unavailable$"):
        validate(configuration, replace(trust, clock=lambda: value))


def test_readback_is_not_the_worker_principal(configuration):
    trust, _ = trust_for(configuration)
    with pytest.raises(BindingError, match="^runtime-readback-not-independent$"):
        validate(configuration, replace(trust, readback_principal="principal:worker_channel"))


@pytest.mark.parametrize("raw", [b'{"profile":1,"profile":2}', b"[]", b"null", b"{\"x\":NaN}",
    b"\xff", b"{" + b" " * 16384 + b"}", b"[" * 1000, "{}"])
def test_malformed_duplicate_oversized_config_has_fixed_error(configuration, raw):
    with pytest.raises(BindingError, match="^invalid-runtime-config$"):
        validate_config(raw, trust=trust_for(configuration)[0])


def test_sensitive_readback_exception_is_redacted(configuration):
    trust, _ = trust_for(configuration)
    def fail():
        raise RuntimeError("private-token-must-not-escape")
    with pytest.raises(BindingError, match="^runtime-readback-unavailable$") as caught:
        validate(configuration, replace(trust, load_readback=fail))
    assert "private-token" not in str(caught.value)
    assert "private-token" not in repr(trust)


@pytest.mark.parametrize("raw", [b'{"profile":1,"profile":2}', b"[]", b"{}", b"{\"x\":NaN}",
    b" " * 16385, True])
def test_invalid_readback_refuses(configuration, raw):
    trust, _ = trust_for(configuration)
    with pytest.raises(BindingError):
        validate(configuration, replace(trust, load_readback=lambda: raw))


def test_worker_dictionary_cannot_construct_trust(configuration):
    with pytest.raises(BindingError, match="^invalid-runtime-trust$"):
        validate_config(encoded(configuration), trust={"approved": True})


def test_readback_repeated_for_each_preflight(configuration):
    trust, observed = trust_for(configuration)
    validate(configuration, trust)
    observed["launch"]["run_attempt"] = "2"
    with pytest.raises(BindingError, match="^runtime-readback-mismatch$"):
        validate(configuration, trust)


def test_exact_workflow_branch_ref_also_requires_independent_commit_pin(configuration):
    configuration["launch"]["workflow_ref"] = "fixture/pilot/.github/workflows/caller.yml@refs/heads/main"
    assert validate(configuration).selection["launch"]["workflow_sha"] == "b" * 40
    configuration["launch"]["workflow_sha"] = "c" * 40
    with pytest.raises(BindingError, match="^invalid-runtime-config$"):
        validate(configuration)


def test_selected_claims_feed_unchanged_signed_issuer_verifier(configuration, r):
    r.h.now = NOW
    selected = validate(configuration)
    claims = dict(selected.selection["launch"])
    token = jwt(r.h.issuer_key, {**claims, "iss": ISSUER, "aud": "factory:qa", "jti": "fixture:config",
                               "iat": NOW, "nbf": NOW, "exp": NOW + 60})
    evidence = r.verifier.verify(token, claims, now=selected.checked_at)
    assert evidence.claims["sub"] == configuration["launch"]["sub"]
    assert evidence.valid_until == NOW + 60


@pytest.mark.parametrize("name", ["repository", "repository_id", "repository_owner", "repository_owner_id",
    "environment", "sub", "ref", "sha", "workflow_ref", "workflow_sha", "job_workflow_ref",
    "job_workflow_sha", "run_id", "run_attempt"])
def test_each_signed_launch_claim_must_match_approved_selection(configuration, r, name):
    r.h.now = NOW
    selected = validate(configuration)
    claims = dict(selected.selection["launch"])
    changed = {**claims, name: "changed", "iss": ISSUER, "aud": "factory:qa", "jti": "fixture:config",
               "iat": NOW, "nbf": NOW, "exp": NOW + 60}
    with pytest.raises(BindingError, match="^workload-mismatch$"):
        r.verifier.verify(jwt(r.h.issuer_key, changed), claims, now=selected.checked_at)


@pytest.mark.parametrize("field", ["repository", "commit", "path", "digest"])
def test_changed_measured_source_refuses(configuration, field):
    trust, observed = trust_for(configuration)
    observed["sources"]["adapter"][field] = "changed"
    with pytest.raises(BindingError, match="^runtime-readback-mismatch$"):
        validate(configuration, trust)


@pytest.mark.parametrize("field", ["repository_id", "environment_id", "environment", "reviewer_ids",
                                   "prevent_self_review", "can_admins_bypass", "deployment_refs"])
def test_each_changed_protection_setting_refuses(configuration, field):
    trust, observed = trust_for(configuration)
    observed["protection"][field] = None
    with pytest.raises(BindingError, match="^runtime-readback-mismatch$"):
        validate(configuration, trust)


def test_config_expiry_shortens_readback_deadline(configuration):
    configuration["expires_at"] = NOW + 5
    assert validate(configuration).valid_until == NOW + 5


def test_canonical_approval_is_independent_of_json_spacing(configuration):
    trust, _ = trust_for(configuration)
    raw = json.dumps(configuration, indent=2, sort_keys=True).encode()
    assert validate_config(raw, trust=trust).config_digest == digest(configuration)
