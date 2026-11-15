"""Closed static-v2 plans, built before run or process assignment."""
from dataclasses import dataclass
from pathlib import PurePosixPath
from uuid import UUID
from workload_factory_binding.evidence import (BindingError, CLAIMS, canonical, digest,
    integer, require, valid_digest)
from workload_factory_binding.gate import _policy_template
from ..config import _configuration_template, _handle, _object
from ..github_bootstrap.common import document
from . import ERROR

PROFILE = "openxfactory-dispatch-selection-internal-v2"
DERIVATION = "openxfactory-hosted-canonical-finalization-v2"
MAX_PLAN_BYTES = 65536


def path_spec(value):
    _object(value, "root_ref path")
    _handle(value["root_ref"])
    path = value["path"]
    require(type(path) is str and 0 < len(path) <= 256 and "\\" not in path
            and ":" not in path and not PurePosixPath(path).is_absolute()
            and all(p not in ("", ".", "..") for p in path.split("/")), ERROR)


def template_digest(value):
    return digest({k: value[k] for k in
                   ("configuration_template", "policy_template", "measurement_plan")})


def validate_shape(value, now):
    _object(value, "profile configuration_template policy_template measurement_plan derivation_rules staging_policy hosting_selection_digest source_hold_ref")
    require(value["profile"] == PROFILE and value["derivation_rules"] == DERIVATION
            and valid_digest(value["hosting_selection_digest"]), ERROR)
    _handle(value["source_hold_ref"])
    c, p, m, s = (value[k] for k in ("configuration_template", "policy_template", "measurement_plan", "staging_policy"))
    _configuration_template(c)
    _policy_template(p, now)
    a = c["authority"]
    require(p["policy_ref"] == a["policy_ref"] and p["revision"] == a["policy_revision"]
            and p["grant_ref"] == a["grant_ref"]
            and all(p["binding"][k] == a[k] for k in ("subject_ref", "wallet_ref", "key_ref", "custody_ref"))
            and p["claims"] == c["launch"]
            and c["protection"]["deployment_refs"] == ["refs/heads/main"]
            and c["not_before"] <= now < c["expires_at"], ERROR)
    _object(m, "executable executable_digest worker configuration cwd artifacts uid capabilities")
    for k in ("executable", "worker", "configuration", "cwd"):
        path_spec(m[k])
    require(valid_digest(m["executable_digest"]) and integer(m["uid"]) and m["uid"] > 0
            and m["capabilities"] == [] and type(m["capabilities"]) is list
            and type(m["artifacts"]) is dict and 3 <= len(m["artifacts"]) <= 32
            and {"worker", "supervisor", "measurement_module"} <= set(m["artifacts"]), ERROR)
    for name, item in m["artifacts"].items():
        _handle("artifact:" + name)
        _object(item, "root_ref path digest")
        path_spec({k: item[k] for k in ("root_ref", "path")})
        require(valid_digest(item["digest"]), ERROR)
    require({k: m["artifacts"]["worker"][k] for k in ("root_ref", "path")} == m["worker"]
            and all(m["artifacts"][role]["digest"] == c["sources"][role]["digest"]
                    for role in ("worker", "supervisor")), ERROR)
    _object(s, "launch_ref host_ref incarnation_ref boot_id cleanup_ref scheduler_capability_digest template_digest max_status_reads status_window_seconds")
    for k in ("launch_ref", "host_ref", "incarnation_ref", "cleanup_ref"):
        _handle(s[k])
    require(type(s["boot_id"]) is str and len(s["boot_id"]) == 36
            and str(UUID(s["boot_id"])) == s["boot_id"] and UUID(s["boot_id"]).version == 4
            and s["cleanup_ref"] == c["lifecycle"]["cleanup_ref"]
            and valid_digest(s["scheduler_capability_digest"])
            and s["template_digest"] == template_digest(value)
            and type(s["max_status_reads"]) is int and s["max_status_reads"] == 6
            and type(s["status_window_seconds"]) is int and s["status_window_seconds"] == 60, ERROR)


@dataclass(frozen=True, repr=False)
class StaticPlan:
    raw: bytes
    digest: str
    valid_until: int

    def value(self):
        # A new bounded copy prevents mutable caller data escaping into decisions.
        return document(self.raw, MAX_PLAN_BYTES)


def validate_plan(raw, *, approved_digest, now):
    try:
        require(integer(now) and valid_digest(approved_digest), ERROR)
        value = document(raw, MAX_PLAN_BYTES)
        validate_shape(value, now)
        require(digest(value) == approved_digest, ERROR)
        return StaticPlan(canonical(value), approved_digest,
                          min(value["configuration_template"]["expires_at"], value["policy_template"]["expires_at"]))
    except Exception:
        raise BindingError(ERROR) from None
