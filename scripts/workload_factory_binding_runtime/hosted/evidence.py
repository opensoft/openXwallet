"""Pure closed protected report projection; no transport, sink or operation authority.

The public emitter accepts only the qualifier's authenticated operational result.
Private encoder vectors are grammar tests, never operational artifacts. Existing
source/fixture evidence and its count vocabulary are deliberately unchanged.
"""
from dataclasses import asdict, dataclass

from workload_factory_binding.evidence import BindingError, canonical, digest, integer, require, valid_digest
from ..evidence import _context, _cleanup

PROFILE = "openxfactory-protected-runtime-report-internal-v1"
SCOPE = "protected-machine"
CASES = ("I01", "I02", "I03", "I04", "I05", "G01", "G02", "G03", "S01", "L01", "R01",
         *(f"H{i:02d}" for i in range(1, 13)), "P01", "deployed-G02", "deployed-G03", "deployed-L01")
LIVE_CASES = ("P01", "deployed-G02", "deployed-G03", "deployed-L01")
PROOF_FIELDS = ("accepted_proof_digest", "verification_digest", "replay_refusal_digest",
                "audience_barrier_digest", "environment_barrier_digest", "worker_denial_digest")
ERRORS = ("qualification-failed", "qualification-cancelled", "qualification-incomplete", "protected-report-refused")
MAX_BYTES = 16384


@dataclass(frozen=True, repr=False)
class CaseObservation:
    case_id: str
    observed_at: int
    artifact_digest: str
    status: str


def _digest(value):
    return valid_digest(value) and value != "sha256:" + "0" * 64


def _results(cases, started, now):
    require(type(cases) is tuple and len(cases) <= len(CASES), "protected-report-refused")
    result = {name: {"status": "not-performed"} for name in CASES}
    seen = set()
    for case in cases:
        require(type(case) is CaseObservation and type(case.case_id) is str and case.case_id in CASES
                and case.case_id not in seen and case.status in ("passed", "failed")
                and integer(case.observed_at) and started <= case.observed_at <= now
                and _digest(case.artifact_digest), "protected-report-refused")
        seen.add(case.case_id)
        result[case.case_id] = {"status": case.status, "observed_at": case.observed_at,
                                "artifact_digest": case.artifact_digest}
    return result


def _proof(value):
    require(type(value) is dict, "protected-report-refused")
    status = value.get("status")
    if status in ("not-performed", "failed"):
        require(set(value) == {"status"}, "protected-report-refused")
    else:
        require(status == "verified" and set(value) == {"status", *PROOF_FIELDS}
                and all(_digest(value[n]) for n in PROOF_FIELDS), "protected-report-refused")
    return dict(value)


def _project(*, selected, cases, proof, plan, cleanup, phase_provenance_digest,
             generation_digest, issuance_digest, started_at, now, operation_floor,
             outcome, error_code=None):
    """Private pure grammar seam. Its vectors have no protected emission route."""
    try:
        require(outcome in ("success", "failure", "cancel", "incomplete")
                and (error_code is None or type(error_code) is str and error_code in ERRORS)
                and integer(operation_floor) and started_at <= operation_floor <= now
                and all(_digest(d) for d in (phase_provenance_digest, generation_digest, issuance_digest)),
                "protected-report-refused")
        selection, context = _context(selected, started_at, now)
        # Reuse the historical context grammar, not v1's all-case cleanup floor.
        results, checked_proof = _results(cases, started_at, now), _proof(proof)
        cleaned = _cleanup(selection, selected, plan, cleanup, operation_floor, now)
        if cleaned["status"] == "verified":
            require(all(_digest(cleaned[n]) for n in ("plan_digest", "scope_digest", "readback_digest",
                        "readback_identity_digest", "attempt_digest")), "protected-report-refused")
            if now >= cleaned["valid_until"]:
                cleaned = {"status": "unverified"}
        values = tuple(r["status"] for r in results.values())
        status = "passed"
        if outcome == "cancel" or cleaned.get("outcome") == "cancel" or error_code == "qualification-cancelled":
            status = "cancelled"
        elif (outcome == "failure" or cleaned.get("outcome") == "failure" or "failed" in values
              or checked_proof["status"] == "failed" or error_code in ("qualification-failed", "protected-report-refused")):
            status = "failed"
        elif (outcome == "incomplete" or "not-performed" in values or checked_proof["status"] != "verified"
              or cleaned.get("status") != "verified" or cleaned.get("outcome") != "success"
              or error_code == "qualification-incomplete"):
            status = "incomplete"
        code = {"passed": None, "failed": "qualification-failed", "cancelled": "qualification-cancelled",
                "incomplete": "qualification-incomplete"}[status]
        if error_code == "protected-report-refused" and status == "failed":
            code = error_code
        report = {"profile": PROFILE, "scope": SCOPE, "status": status, "started_at": started_at,
            "issued_at": now, "context": context, "phase_provenance_digest": phase_provenance_digest,
            "generation_digest": generation_digest, "issuance_digest": issuance_digest,
            "proof": checked_proof, "cleanup": cleaned, "results": results, "error_code": code,
            "protected_machine_qualified": status == "passed", "human_approval": False,
            "domain_effect": False, "consumer_dependency_lock": False}
        raw = canonical(report)
        require(len(raw) <= MAX_BYTES, "protected-report-refused")
        return raw
    except Exception:
        raise BindingError("protected-report-refused") from None


def build_receipt(run, *, now):
    """Emit only a captured authenticated operational run, never a caller label.

    Checks the qualifier's immutable, internally captured origin. This function
    performs no I/O and cannot launch, finalize, renew or retry anything.
    """
    from .qualification import QualificationResult, _RESULT_SEAL
    require(type(run) is QualificationResult and run._seal is _RESULT_SEAL
            and run._operational_origin is _RESULT_SEAL, "protected-report-refused")
    return _project(**run._projection(now))
