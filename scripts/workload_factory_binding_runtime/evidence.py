"""Closed, redacted source/fixture reports; no approval or protected-run authority.

Only trusted hosting supplies selected configuration and observed case results.
These Python types do not authenticate a host or verify supplied test observations.
There is no worker input, resolver, provider call, filesystem sink or public API.
"""
from dataclasses import asdict, dataclass

from workload_factory_binding.evidence import (
    BindingError, canonical, digest, integer, require, valid_digest,
)
from .config import SOURCE_ROLES, ValidatedConfig
from .lifecycle import CleanupVerification, RunPlan, RunScope, _plan
from .loaders import ServiceIdentity

PROFILE = "openxfactory-runtime-evidence-internal-v1"
CASES = ("I01", "I02", "I03", "I04", "I05", "G01", "G02", "G03", "S01", "L01", "R01")
SCOPES = ("source-conformance", "isolated-fixture")
_CODES = frozenset(("qualification-failed", "qualification-cancelled", "invalid-qualification-evidence",
                    "workflow-context-mismatch", "workflow-input-unavailable", "workflow-admission-refused",
                    "workflow-operational-host-unselected", "workflow-live-qualification-not-performed",
                    "qualification-cleanup-mismatch", "lifecycle-cleanup-unverified", "lifecycle-operation-failed",
                    "runtime-config-unavailable", "runtime-service-unavailable", "runtime-use-expired",
                    "runtime-clock-unavailable", "issuer-keys-unavailable", "workload-unverified"))
_COUNTS = ("collected", "passed", "failures", "errors", "skipped")


def safe_error(error):
    """Never call exception str/repr or retain args, causes, notes or tracebacks."""
    if isinstance(error, BaseException) and not isinstance(error, Exception):
        return "qualification-cancelled"
    if type(error) is BindingError and len(error.args) == 1:
        code = error.args[0]
        if type(code) is str and code in _CODES:
            return code
    return "qualification-failed"


@dataclass(frozen=True, repr=False)
class CaseResult:
    """Trusted harness observations; no caller-provided pass/qualified boolean."""
    case_id: str
    collected: int
    passed: int
    failures: int
    errors: int
    skipped: int
    observed_at: int
    artifact_digest: str


def _plain(value):
    # ValidatedConfig is deeply immutable. Copy only its ordinary JSON shape.
    if hasattr(value, "items"):
        return {key: _plain(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_plain(item) for item in value]
    return value


def _context(selected, started_at, now):
    require(type(selected) is ValidatedConfig and integer(started_at) and integer(now)
            and integer(selected.checked_at) and integer(selected.valid_until)
            and integer(selected.readback_observed_at) and integer(selected.readback_valid_until)
            and selected.readback_observed_at <= selected.checked_at < selected.readback_valid_until
            <= selected.readback_observed_at + 60 and selected.valid_until <= selected.readback_valid_until
            and valid_digest(selected.readback_digest) and valid_digest(selected.readback_principal_digest)
            and selected.checked_at <= started_at < selected.valid_until and started_at <= now,
            "invalid-qualification-evidence")
    selection = _plain(selected.selection)
    require(valid_digest(selected.config_digest) and digest(selection) == selected.config_digest,
            "invalid-qualification-evidence")
    # Recheck the closed grammar, including exact source/run syntax, without
    # provider I/O or claiming that historical selection is currently active.
    from .config import _configuration
    _configuration(selection)
    sources = {role: {"repository_digest": digest(source["repository"]), "commit": source["commit"],
                      "path_digest": digest(source["path"]), "digest": source["digest"]}
               for role, source in selection["sources"].items()}
    require(set(sources) == SOURCE_ROLES, "invalid-qualification-evidence")
    context = {"config_digest": selected.config_digest, "case_digest": digest(selection["case_ref"]),
               "run_id": selection["launch"]["run_id"], "run_attempt": selection["launch"]["run_attempt"],
               "sources": sources, "dependency_digest": selection["dependency_digest"],
               "composition_digest": selection["composition_digest"],
               "protection_digest": digest(selection["protection"]),
               "launch_digest": digest(selection["launch"]), "services_digest": digest(selection["services"]),
               "authority_digest": digest(selection["authority"]), "issuer_digest": digest(selection["issuer"]),
               "state_digest": digest(selection["state"]), "lifecycle_digest": digest(selection["lifecycle"]),
               "selection_checked_at": selected.checked_at, "selection_valid_until": selected.valid_until,
               "readback_digest": selected.readback_digest, "readback_principal_digest": selected.readback_principal_digest,
               "readback_observed_at": selected.readback_observed_at, "readback_valid_until": selected.readback_valid_until}
    return selection, context


def _results(cases, started_at, now):
    require(type(cases) is tuple and len(cases) <= len(CASES), "invalid-qualification-evidence")
    results = {}
    for case in cases:
        require(type(case) is CaseResult and type(case.case_id) is str and case.case_id in CASES
                and case.case_id not in results and integer(case.observed_at)
                and started_at <= case.observed_at <= now and valid_digest(case.artifact_digest),
                "invalid-qualification-evidence")
        counts = {name: getattr(case, name) for name in _COUNTS}
        require(all(integer(value) and value <= 1000000 for value in counts.values())
                and case.passed + case.failures + case.skipped <= case.collected,
                "invalid-qualification-evidence")
        status = ("passed" if case.collected > 0 and case.passed == case.collected
                  and not (case.failures or case.errors or case.skipped) else "failed")
        results[case.case_id] = {"status": status, **counts, "observed_at": case.observed_at,
                                 "artifact_digest": case.artifact_digest}
    return {case: results.get(case, {"status": "not-performed"}) for case in CASES}


def _cleanup(selection, selected, plan, verification, started_at, now):
    if verification is None:
        return {"status": "missing"}
    require(type(plan) is RunPlan and type(verification) is CleanupVerification,
            "qualification-cleanup-mismatch")
    _plan(plan)
    expected = RunScope(selected.config_digest, selection["case_ref"], selection["launch"]["run_id"],
                        selection["launch"]["run_attempt"], **selection["lifecycle"])
    require(plan.scope == expected and verification.scope == expected and verification.plan_digest == plan.digest
            and plan.retained_state_ref == selection["state"]["store_ref"]
            and plan.janitor == ServiceIdentity(**selection["services"]["janitor"])
            and selection["not_before"] <= plan.issued_at < plan.expires_at <= selection["expires_at"]
            and verification.outcome in ("success", "failure", "cancel")
            and all(integer(v) for v in (verification.observed_at, verification.checked_at, verification.valid_until))
            and started_at <= verification.observed_at <= verification.checked_at <= now
            and verification.checked_at < verification.valid_until <= verification.observed_at + 60
            and all(valid_digest(getattr(verification, field)) for field in
                    ("readback_digest", "readback_identity_digest", "attempt_digest")),
            "qualification-cleanup-mismatch")
    return {"status": "verified", "plan_digest": plan.digest, "scope_digest": digest(asdict(expected)),
            **{field: getattr(verification, field) for field in ("outcome", "observed_at", "checked_at", "valid_until",
                                                               "readback_digest", "readback_identity_digest", "attempt_digest")}}


def build_receipt(*, scope, selected, cases, started_at, now, plan=None, cleanup=None, error=None):
    """Return bounded canonical JSON bytes, omitting raw evidence by construction.

    This reports trusted harness observations, not a signed possession receipt.
    It cannot select protected-machine scope or grant any acceptance/authority.
    A config snapshot records the historical selected identities; it is never
    reactivated by receipt creation. Hosting measures/authenticates those inputs.
    """
    try:
        require(type(scope) is str and scope in SCOPES, "invalid-qualification-evidence")
        selection, context = _context(selected, started_at, now)
        results = _results(cases, started_at, now)
        if scope == "source-conformance":
            require(plan is None and cleanup is None, "qualification-cleanup-mismatch")
            cleaned = {"status": "not-required"}
        else:
            floor = max((case.observed_at for case in cases), default=started_at)
            cleaned = _cleanup(selection, selected, plan, cleanup, floor, now)
        code = None if error is None else safe_error(error)
        outcome = cleaned.get("outcome")
        status = "passed"
        if code == "qualification-cancelled" or outcome == "cancel":
            status = "cancelled"
        elif code is not None or outcome == "failure" or any(r["status"] == "failed" for r in results.values()):
            status = "failed"
        elif cleaned["status"] == "missing" or any(r["status"] == "not-performed" for r in results.values()):
            status = "incomplete"
        report = {"profile": PROFILE, "scope": scope, "status": status, "started_at": started_at,
                  "issued_at": now, "context": context, "results": results, "cleanup": cleaned,
                  "error_code": code, "protected_machine_qualified": False, "human_approval": False,
                  "domain_effect": False, "consumer_dependency_lock": False,
                  "live_gates": dict.fromkeys(("P01", "deployed-G02", "deployed-G03", "deployed-L01"), "not-performed")}
        raw = canonical(report)
        require(len(raw) <= 16384, "invalid-qualification-evidence")
        return raw
    except Exception:
        raise BindingError("invalid-qualification-evidence") from None
