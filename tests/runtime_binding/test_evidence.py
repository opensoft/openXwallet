"""Internal receipt grammar/privacy; supplied observations never confer authority."""
from dataclasses import asdict, replace
import json

import pytest

from workload_factory_binding.evidence import BindingError, canonical, digest
from workload_factory_binding_runtime.config import validate_config
from workload_factory_binding_runtime.evidence import CASES, CaseResult, build_receipt, safe_error
from workload_factory_binding_runtime.loaders import BoundService
from .composition_fixture import c
from .lifecycle_process_fixture import p
from .test_config import NOW, configuration, encoded, trust_for, validate
from .test_lifecycle import l


def observations(now=NOW):
    # Synthetic trusted-harness counts for schema tests, not real matrix evidence.
    return tuple(CaseResult(case, 1, 1, 0, 0, 0, now, digest({"case": case})) for case in CASES)


@pytest.fixture
def selected(configuration):
    return validate(configuration)


def receipt(selected, **changes):
    arguments = dict(scope="source-conformance", selected=selected, cases=observations(), started_at=NOW, now=NOW)
    arguments.update(changes)
    return build_receipt(**arguments)


def test_source_report_is_canonical_bound_and_never_machine_or_human_authority(selected):
    raw = receipt(selected)
    report = json.loads(raw)
    assert raw == canonical(report) and len(raw) <= 16384
    assert report["scope"] == "source-conformance" and report["status"] == "passed"
    assert set(report["results"]) == set(CASES)
    assert all(result["status"] == "passed" for result in report["results"].values())
    assert report["context"]["config_digest"] == selected.config_digest
    assert report["context"]["readback_digest"] == selected.readback_digest
    assert report["context"]["readback_principal_digest"] == selected.readback_principal_digest
    for field in ("protected_machine_qualified", "human_approval", "domain_effect", "consumer_dependency_lock"):
        assert report[field] is False
    assert set(report["live_gates"].values()) == {"not-performed"}
    assert report["cleanup"] == {"status": "not-required"}


@pytest.mark.parametrize("scope", ["protected-machine", "live", "", None, True])
def test_source_or_fixture_cannot_self_promote_to_protected_machine(selected, scope):
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$"):
        receipt(selected, scope=scope)


@pytest.mark.parametrize("case_id", CASES)
def test_each_missing_required_case_stays_not_performed_and_incomplete(selected, case_id):
    cases = tuple(c for c in observations() if c.case_id != case_id)
    report = json.loads(receipt(selected, cases=cases))
    assert report["status"] == "incomplete"
    assert report["results"][case_id] == {"status": "not-performed"}


def test_empty_case_collection_never_passes(selected):
    report = json.loads(receipt(selected, cases=()))
    assert report["status"] == "incomplete"
    assert all(v == {"status": "not-performed"} for v in report["results"].values())


@pytest.mark.parametrize("change", [dict(collected=0, passed=0), dict(passed=0), dict(passed=0, failures=1),
                                     dict(errors=1), dict(passed=0, skipped=1)])
def test_zero_collection_missing_reports_failures_errors_and_skips_never_pass(selected, change):
    cases = (replace(observations()[0], **change), *observations()[1:])
    report = json.loads(receipt(selected, cases=cases))
    assert report["status"] == "failed"
    assert report["results"]["I01"]["status"] == "failed"


@pytest.mark.parametrize("field", ["collected", "passed", "failures", "errors", "skipped"])
@pytest.mark.parametrize("value", [-1, True, 1000001])
def test_counts_are_bounded_integers(selected, field, value):
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$"):
        receipt(selected, cases=(replace(observations()[0], **{field: value}),))


@pytest.mark.parametrize("kind", ["duplicate", "unknown", "dictionary", "extra", "overcount", "future", "old", "digest"])
def test_wrong_case_identity_shape_time_or_artifact_refuses(selected, kind):
    case = observations()[0]
    cases = (case,)
    if kind == "duplicate":cases = (case, case)
    elif kind == "unknown":cases = (replace(case, case_id="P01"),)
    elif kind == "dictionary":cases = (asdict(case),)
    elif kind == "extra":cases = observations() + (case,)
    elif kind == "overcount":cases = (replace(case, failures=1),)
    elif kind == "future":cases = (replace(case, observed_at=NOW + 1),)
    elif kind == "old":cases = (replace(case, observed_at=NOW - 1),)
    elif kind == "digest":cases = (replace(case, artifact_digest="secret-canary"),)
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$") as caught:
        receipt(selected, cases=cases)
    assert "secret-canary" not in str(caught.value)


@pytest.mark.parametrize("change", [dict(started_at=NOW - 1), dict(started_at=NOW + 30, now=NOW + 30),
                                     dict(now=NOW - 1), dict(now=True)])
def test_receipt_cannot_reactivate_selection_or_regress_time(selected, change):
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$"):
        receipt(selected, **change)


def test_historical_receipt_does_not_extend_runtime_selection_validity(selected):
    report = json.loads(receipt(selected, now=NOW + 600))
    assert report["context"]["selection_valid_until"] == selected.valid_until < report["issued_at"]
    assert report["protected_machine_qualified"] is False


@pytest.mark.parametrize("change", [dict(config_digest="sha256:" + "0" * 64), dict(readback_digest="raw-secret"),
    dict(readback_principal_digest="raw-secret"), dict(readback_observed_at=NOW + 1),
    dict(readback_valid_until=NOW), dict(readback_valid_until=NOW + 61)])
def test_selected_configuration_and_readback_binding_cannot_be_replaced(selected, change):
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$"):
        receipt(replace(selected, **change))


def test_mutated_selection_and_unknown_members_are_not_copied(selected):
    candidate = json.loads(canonical(_selection(selected)))
    candidate["raw_token"] = "sensitive-workload-canary"
    bad = replace(selected, selection=candidate, config_digest=digest(candidate))
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$") as caught:
        receipt(bad)
    assert "sensitive-workload-canary" not in str(caught.value)


def _selection(selected):
    from workload_factory_binding_runtime.evidence import _plain
    return _plain(selected.selection)


def test_redaction_uses_closed_projection_even_for_secret_shaped_metadata(configuration):
    canary = "SensitiveCanary"
    configuration["case_ref"] = "case:" + canary
    configuration["sources"]["adapter"].update(repository="fixture/" + canary, path=canary + "/adapter.py")
    configuration["launch"]["sub"] = "subject:" + canary
    configuration["issuer"]["audience"] = "audience:" + canary
    configuration["authority"]["subject_ref"] = "subject:" + canary
    configuration["services"]["custody"]["credential_ref"] = "credential:" + canary
    trust, observed = trust_for(configuration)
    observed["principal_ref"] = "principal:" + canary
    trust = replace(trust, readback_principal=observed["principal_ref"])
    selected = validate_config(encoded(configuration), trust=trust)
    error = RuntimeError(canary, {"access_token": canary, "factor_response": canary, "browser_state": canary})
    raw = receipt(selected, error=error)
    assert canary.encode() not in raw
    report = json.loads(raw)
    assert report["error_code"] == "qualification-failed" and report["status"] == "failed"
    assert report["context"]["sources"]["adapter"]["repository_digest"] == digest("fixture/" + canary)


class UnprintableError(RuntimeError):
    def __str__(self):
        raise AssertionError("exception string must not be used")
    def __repr__(self):
        raise AssertionError("exception repr must not be used")


@pytest.mark.parametrize("error,code", [(UnprintableError("private"), "qualification-failed"),
    (BindingError("private-code"), "qualification-failed"), (BindingError("runtime-use-expired"), "runtime-use-expired"),
    (BindingError("runtime-use-expired", "secret"), "qualification-failed"),
    (KeyboardInterrupt("private"), "qualification-cancelled"), (SystemExit("private"), "qualification-cancelled")])
def test_fixed_errors_never_interpolate_exception_payload_or_traceback(selected, error, code):
    error.add_note("private-note")
    error.__cause__ = RuntimeError("private-cause")
    assert safe_error(error) == code
    raw = receipt(selected, error=error)
    assert b"private" not in raw and b"secret" not in raw
    assert json.loads(raw)["error_code"] == code


def test_missing_fixture_cleanup_never_passes(selected):
    report = json.loads(receipt(selected, scope="isolated-fixture"))
    assert report["status"] == "incomplete" and report["cleanup"] == {"status": "missing"}


def test_all_exact_sources_and_dependency_protection_digests_are_bound(selected):
    report = json.loads(receipt(selected))
    selection = _selection(selected)
    for role, original in selection["sources"].items():
        source = report["context"]["sources"][role]
        assert source == {"commit": original["commit"], "digest": original["digest"],
                          "repository_digest": digest(original["repository"]), "path_digest": digest(original["path"])}
    for field in ("dependency_digest", "composition_digest"):
        assert report["context"][field] == selection[field]
    assert report["context"]["protection_digest"] == digest(selection["protection"])


def test_source_scope_cannot_claim_fixture_cleanup(selected):
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$"):
        receipt(selected, cleanup=True)


def fixture_report(l, *, cleanup=None, **changes):
    c = l.c
    selected = validate_config(encoded(c.config), trust=c.trust)
    arguments = dict(scope="isolated-fixture", selected=selected, cases=observations(c.h.now),
                     started_at=c.h.now, now=c.h.now, plan=l.plan, cleanup=cleanup)
    arguments.update(changes)
    return json.loads(build_receipt(**arguments))


def test_verified_cleanup_receipt_binds_plan_attempt_and_independent_readback(l):
    verification = l.life.finalize("success")
    assert l.life.cleanup_verification == verification
    report = fixture_report(l, cleanup=verification)
    assert report["status"] == "passed" and report["cleanup"]["status"] == "verified"
    assert report["cleanup"]["plan_digest"] == l.plan.digest
    assert report["cleanup"]["readback_identity_digest"] == digest(asdict(l.readback_service.identity))
    assert l.plan.scope.case_ref not in json.dumps(report)
    assert l.plan.janitor.credential_ref not in json.dumps(report)


@pytest.mark.parametrize("field", ["plan_digest", "scope", "outcome", "observed_at", "checked_at", "valid_until",
                                  "readback_digest", "readback_identity_digest", "attempt_digest"])
def test_cleanup_checkpoint_must_match_exact_scope_plan_time_and_readback(l, field):
    verification = l.life.finalize("success")
    value = "invalid-secret"
    if field == "scope":value = replace(verification.scope, run_attempt="2")
    elif field == "observed_at":value = l.c.h.now + 1
    elif field == "checked_at":value = l.c.h.now - 1
    elif field == "valid_until":value = l.c.h.now
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$"):
        fixture_report(l, cleanup=replace(verification, **{field: value}))


@pytest.mark.parametrize("outcome,status", [("failure", "failed"), ("cancel", "cancelled")])
def test_cleaned_failure_or_cancellation_is_never_success(l, outcome, status):
    report = fixture_report(l, cleanup=l.life.finalize(outcome))
    assert report["status"] == status


def test_failed_retry_clears_old_cleanup_success(l):
    old = l.life.finalize("success")
    assert l.life.cleanup_verification == old
    l.readback_hook = lambda _attempt: None
    with pytest.raises(BindingError, match="^lifecycle-cleanup-unverified$"):
        l.life.finalize("failure")
    assert l.life.cleanup_verification is None
    assert fixture_report(l)["status"] == "incomplete"


def test_repeated_cleanup_uses_fresh_attempt_fingerprint(l):
    first = l.life.finalize("success")
    second = l.life.finalize("success")
    assert first.attempt_digest != second.attempt_digest
    assert first.readback_digest != second.readback_digest


def test_verified_cleanup_never_masks_operation_error(l):
    verification = l.life.finalize("success")
    report = fixture_report(l, cleanup=verification, error=RuntimeError("must-not-copy"))
    assert report["status"] == "failed"
    assert report["cleanup"]["status"] == "verified"
    assert report["error_code"] == "qualification-failed"


def test_cleanup_before_latest_case_observation_cannot_qualify(l):
    verification = l.life.finalize("success")
    with pytest.raises(BindingError, match="^invalid-qualification-evidence$"):
        fixture_report(l, cleanup=verification, cases=observations(l.c.h.now + 1), now=l.c.h.now + 1)


def test_older_cleanup_completion_cannot_overwrite_newer_attempt(l):
    original = l.life.readback
    newer = []
    class Reader:
        def read_cleanup(self, *args, **kwargs):
            record = original.target.read_cleanup(*args, **kwargs)
            if not newer:
                newer.append(None)
                newer[0] = l.life.finalize("failure")
            return record
    l.life.readback = BoundService(original.identity, Reader())
    older = l.life.finalize("success")
    assert older.outcome == "success"
    assert l.life.cleanup_verification == newer[0]
    assert l.life.cleanup_verification.outcome == "failure"


@pytest.mark.parametrize("outcome", ["success", "failure", "cancel"])
def test_actual_owning_proof_and_independent_cleanup_export_only_safe_receipt(p, outcome):
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    c = p.c
    selected = validate_config(encoded(c.config), trust=c.trust)
    started = c.h.now
    c.h.binding = TrustedKeyBinding(**asdict(c.h.binding))
    c.bridge = c.make(create_proof=create_proof, lifecycle=p.life)
    proof = {}
    error = None
    def operation():
        result = c.run()
        checked = verify_proof(result["proof"], expected_digest=c.h.challenge.digest, binding=c.h.binding, now=c.h.now)
        assert checked.subject_ref == c.h.binding.subject_ref and result["human_approval"] is False
        proof.update(result["proof"])
        if outcome == "failure":raise RuntimeError("sensitive-provider-canary")
        if outcome == "cancel":raise KeyboardInterrupt("sensitive-factor-canary")
        return result
    try:
        p.life.run(operation)
    except (BindingError, KeyboardInterrupt) as caught:
        error = caught
    assert proof and p.life.cleanup_verification is not None
    cases = (CaseResult("R01", 1, 1, 0, 0, 0, c.h.now, digest(proof)),)
    raw = build_receipt(scope="isolated-fixture", selected=selected, cases=cases, started_at=started,
                        now=c.h.now, plan=p.plan, cleanup=p.life.cleanup_verification, error=error)
    report = json.loads(raw)
    assert report["status"] == {"success": "incomplete", "failure": "failed", "cancel": "cancelled"}[outcome]
    assert report["cleanup"]["status"] == "verified"
    assert report["results"]["G03"] == {"status": "not-performed"}  # this test alone is not the entire G03 matrix
    for sensitive in (c.h.token.encode(), canonical(proof), b"sensitive-provider-canary", b"sensitive-factor-canary"):
        assert sensitive not in raw
    assert not (p.root / "credential.key").exists() and not (p.root / "temporary").exists()
    assert (p.root / "shared").exists() and c.h.ledger.path.exists()
