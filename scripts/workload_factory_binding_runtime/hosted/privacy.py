"""Per-run pre-report privacy observations over actual projection and safe errors.

No file/network I/O, logger, plugin, secret lookup or report emission. Synthetic
private canaries exercise success/failure/cancellation redaction independently of
the captured operation; only their input/output digests enter the H12 artifact.
"""
from workload_factory_binding.evidence import BindingError, byte_digest, canonical, digest, require, valid_digest
from ..evidence import safe_error
from .evidence import _proof


def observe_privacy(projection):
    require(type(projection) is dict and set(projection) == {"config_digest", "proof", "cleanup_digest"}
            and valid_digest(projection["config_digest"])
            and (projection["cleanup_digest"] is None or valid_digest(projection["cleanup_digest"])),
            "protected-report-refused")
    _proof(projection["proof"])
    raw = canonical(projection)
    require(len(raw) <= 4096, "protected-report-refused")
    observations = []
    for surface in ("provider", "token", "pem", "proof", "challenge", "path"):
        canary = "private-" + surface + "-canary:" + byte_digest(raw)
        errors = (RuntimeError(canary), BindingError(canary), KeyboardInterrupt(canary),
                  SystemExit(canary), GeneratorExit(canary), BindingError("runtime-service-unavailable"))
        for error in errors:
            error.__cause__ = ValueError(canary)
            error.__context__ = ValueError(canary)
            error.add_note(canary)
            expected = ("runtime-service-unavailable" if type(error) is BindingError and error.args == ("runtime-service-unavailable",)
                        else "qualification-failed" if isinstance(error, Exception) else "qualification-cancelled")
            actual = safe_error(error)
            require(type(actual) is str and actual == expected, "protected-report-refused")
            observations.append({"input_digest": digest({"surface": surface, "canary": canary,
                "error_type": type(error).__name__, "args": True, "notes": True, "cause": True, "context": True}),
                "output_digest": digest({"error_code": actual})})
            require(canary.encode() not in raw, "protected-report-refused")
    return digest({"pre_report_projection_digest": byte_digest(raw), "privacy_controls": observations})
