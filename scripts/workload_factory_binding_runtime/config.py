"""Internal operator configuration preflight; no worker or deployment entrypoint.

The embedding owns approval, authenticated readback and clocks outside the worker
boundary. Python objects are not an isolation mechanism. This module validates
their projection; it neither obtains provider evidence nor constructs a signer.
"""
from dataclasses import dataclass
import re
from types import MappingProxyType

from workload_factory_binding.evidence import (
    BindingError, CLAIMS, RUN_CLAIMS, decode_object, digest, integer, reference,
    require, valid_digest,
)
from ._https_worker import DISCOVERY_URL, ISSUER, JWKS_URL

PROFILE = "openxfactory-protected-runtime-internal-v1"
SOURCE_ROLES = frozenset(("factory_profile", "adapter", "wallet_contracts", "wallet_code",
                          "worker", "supervisor", "caller_workflow", "reusable_workflow"))
SERVICE_ROLES = frozenset(("records", "challenge", "registry", "custody", "supervisor",
                           "worker_channel", "janitor"))
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_HANDLE = re.compile(r"[a-z][a-z0-9_-]{0,31}:[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_PENDING = frozenset(("pending", "unselected", "latest", "head", "todo", "tbd", "unknown"))
_REF_PREFIXES = ("refs/heads/", "refs/tags/")


def _object(value, fields):
    require(type(value) is dict and set(value) == set(fields.split()), "invalid-runtime-config")


def _handle(value):
    require(type(value) is str and _HANDLE.fullmatch(value)
            and not (_PENDING & set(re.split(r"[:._-]", value.lower()))), "invalid-runtime-config")


def _selected(value):
    return reference(value) and not (_PENDING & set(re.split(r"[:/._@-]", value.lower())))


def _positive(value):
    require(type(value) is str and re.fullmatch(r"[1-9]\d{0,19}", value, flags=re.ASCII),
            "invalid-runtime-config")


def _sha(value):
    require(type(value) is str and _SHA.fullmatch(value) and value != "0" * 40,
            "invalid-runtime-config")


def _sources(value):
    require(type(value) is dict and set(value) == SOURCE_ROLES, "invalid-runtime-config")
    for source in value.values():
        _object(source, "repository commit path digest")
        require(_selected(source["repository"]) and _REPO.fullmatch(source["repository"]),
                "invalid-runtime-config")
        _sha(source["commit"])
        path = source["path"]
        require(type(path) is str and 0 < len(path) <= 256 and reference(path)
                and not any(p in ("", ".", "..") for p in path.split("/"))
                and "\\" not in path and ":" not in path, "invalid-runtime-config")
        require(valid_digest(source["digest"]), "invalid-runtime-config")


def _launch(value, sources):
    require(type(value) is dict and set(value) == CLAIMS | RUN_CLAIMS
            and all(_selected(v) for v in value.values()), "invalid-runtime-config")
    for name in ("repository_id", "repository_owner_id", "run_id", "run_attempt"):
        _positive(value[name])
    require(_REPO.fullmatch(value["repository"])
            and value["repository"].split("/")[0] == value["repository_owner"],
            "invalid-runtime-config")
    for claim in ("sha", "workflow_sha", "job_workflow_sha"):
        _sha(value[claim])
    require(value["ref"].startswith(_REF_PREFIXES), "invalid-runtime-config")
    for role, name, sha in (("caller_workflow", "workflow_ref", "workflow_sha"),
                            ("reusable_workflow", "job_workflow_ref", "job_workflow_sha")):
        source = sources[role]
        workflow, separator, selected_ref = value[name].partition("@")
        require(source["path"].startswith(".github/workflows/")
                and source["path"].endswith((".yml", ".yaml"))
                and separator and workflow == source["repository"] + "/" + source["path"]
                and (selected_ref == source["commit"]
                     or selected_ref.startswith(_REF_PREFIXES))
                and value[sha] == source["commit"], "invalid-runtime-config")
    require(sources["worker"]["repository"] == value["repository"]
            and sources["worker"]["commit"] == value["sha"]
            and sources["caller_workflow"]["repository"] == value["repository"],
            "invalid-runtime-config")


def _protection(value, claims):
    _object(value, "repository_id environment_id environment reviewer_ids prevent_self_review can_admins_bypass deployment_refs")
    _positive(value["environment_id"])
    require(value["repository_id"] == claims["repository_id"]
            and value["environment"] == claims["environment"]
            and value["prevent_self_review"] is True and value["can_admins_bypass"] is False,
            "invalid-runtime-config")
    reviewers = value["reviewer_ids"]
    require(type(reviewers) is list and 0 < len(reviewers) <= 6, "invalid-runtime-config")
    for reviewer in reviewers:
        _object(reviewer, "type id")
        require(reviewer["type"] in ("User", "Team"), "invalid-runtime-config")
        _positive(reviewer["id"])
    require(len({(x["type"], x["id"]) for x in reviewers}) == len(reviewers), "invalid-runtime-config")
    refs = value["deployment_refs"]
    require(type(refs) is list and 0 < len(refs) <= 32
            and all(reference(v) and v.startswith(_REF_PREFIXES) for v in refs)
            and len(set(refs)) == len(refs) and claims["ref"] in refs, "invalid-runtime-config")


def _services(value):
    require(type(value) is dict and set(value) == SERVICE_ROLES, "invalid-runtime-config")
    for service in value.values():
        _object(service, "service_ref principal_ref credential_ref trust_digest")
        for name in ("service_ref", "principal_ref", "credential_ref"):
            _handle(service[name])
        require(valid_digest(service["trust_digest"]), "invalid-runtime-config")


def _references(value, fields):
    _object(value, fields)
    for item in value.values():
        _handle(item)


def _configuration(value):
    _object(value, "profile revision not_before expires_at case_ref sources dependency_digest composition_digest issuer launch protection authority services state lifecycle")
    require(value["profile"] == PROFILE and integer(value["revision"]) and value["revision"] > 0
            and integer(value["not_before"]) and integer(value["expires_at"])
            and value["not_before"] < value["expires_at"], "invalid-runtime-config")
    _handle(value["case_ref"])
    _sources(value["sources"])
    for name in ("dependency_digest", "composition_digest"):
        require(valid_digest(value[name]), "invalid-runtime-config")
    issuer = value["issuer"]
    _object(issuer, "issuer discovery jwks audience")
    require(issuer["issuer"] == ISSUER and issuer["discovery"] == DISCOVERY_URL
            and issuer["jwks"] == JWKS_URL and _selected(issuer["audience"]), "invalid-runtime-config")
    _launch(value["launch"], value["sources"])
    _protection(value["protection"], value["launch"])
    authority = value["authority"]
    _object(authority, "policy_ref policy_revision policy_digest subject_ref wallet_ref key_ref custody_ref grant_ref")
    require(integer(authority["policy_revision"]) and authority["policy_revision"] > 0
            and valid_digest(authority["policy_digest"]), "invalid-runtime-config")
    for name in ("policy_ref", "subject_ref", "wallet_ref", "key_ref", "custody_ref", "grant_ref"):
        _handle(authority[name])
    _services(value["services"])
    _references(value["state"], "store_ref initialization_ref retention_ref recovery_ref")
    _references(value["lifecycle"], "lease_ref cleanup_ref receipt_retention_ref")


def _freeze(value):
    if type(value) is dict:
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, repr=False)
class RuntimeTrust:
    """Trusted embedding arguments, never deserialized from the configuration.

    load_readback authenticates its source and returns bounded JSON bytes. It must
    read actual source/protection/service selection independently of the candidate,
    not echo it. The principal and approval are selected outside worker control.
    Fresh runtime composition must repeat preflight, not retain this result.
    """
    approved_config_digest: str
    readback_principal: str
    load_readback: object
    clock: object


@dataclass(frozen=True, repr=False)
class ValidatedConfig:
    """Short-lived structural/source binding; no deployed qualification claim."""
    selection: object
    config_digest: str
    checked_at: int
    valid_until: int
    readback_digest: str
    readback_principal_digest: str
    readback_observed_at: int
    readback_valid_until: int


def _clock(trust):
    try:
        now = trust.clock()
        require(integer(now), "runtime-clock-unavailable")
        return now
    except Exception:
        raise BindingError("runtime-clock-unavailable") from None


def _readback(value, config, config_digest, principal, now):
    _object(value, "profile principal_ref case_ref config_digest launch sources dependency_digest composition_digest protection services state lifecycle observed_at expires_at")
    require(value["profile"] == PROFILE and value["principal_ref"] == principal
            and value["config_digest"] == config_digest, "runtime-readback-mismatch")
    for name in ("case_ref", "launch", "sources", "dependency_digest", "composition_digest",
                 "protection", "services", "state", "lifecycle"):
        require(digest(value[name]) == digest(config[name]), "runtime-readback-mismatch")
    issued, expires = value["observed_at"], value["expires_at"]
    require(integer(issued) and integer(expires) and issued <= now < expires <= issued + 60,
            "runtime-readback-expired")
    return expires


def validate_config(raw, *, trust):
    """Fail before trusted dependency construction; performs no network/file I/O.

    Only the embedding-provided readback callback can do I/O. Approval of canonical
    bytes is independent of the candidate; no `approved` flag or self-hash is read.
    Safe codes replace parser, readback and clock failures without payloads.
    """
    require(type(trust) is RuntimeTrust and valid_digest(trust.approved_config_digest)
            and callable(trust.load_readback) and callable(trust.clock), "invalid-runtime-trust")
    _handle(trust.readback_principal)
    try:
        config = decode_object(raw)
        _configuration(config)
        selected_digest = digest(config)
    except Exception:
        raise BindingError("invalid-runtime-config") from None
    require(selected_digest == trust.approved_config_digest, "runtime-config-unapproved")
    require(trust.readback_principal != config["services"]["worker_channel"]["principal_ref"],
            "runtime-readback-not-independent")
    before = _clock(trust)
    require(config["not_before"] <= before < config["expires_at"], "runtime-config-inactive")
    try:
        observed = decode_object(trust.load_readback())
    except Exception:
        raise BindingError("runtime-readback-unavailable") from None
    after = _clock(trust)
    require(before <= after < config["expires_at"], "runtime-config-inactive")
    deadline = _readback(observed, config, selected_digest, trust.readback_principal, after)
    return ValidatedConfig(_freeze(config), selected_digest, after,
                           min(config["expires_at"], deadline), digest(observed),
                           digest(trust.readback_principal), observed["observed_at"], deadline)
