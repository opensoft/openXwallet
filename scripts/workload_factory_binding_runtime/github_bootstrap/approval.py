"""Trusted current operator projection, separate from tokens and worker input."""
from dataclasses import dataclass, asdict
from workload_factory_binding.evidence import decode_object, digest, integer, reference, require
from ..bootstrap import DispatchContext, selection_digest
from ..config import _handle
from ..workflow import REPOSITORY, CALLER, REUSABLE, REF
from . import ERROR
from .common import number
from .identity import IdentityPolicy, BASE_CLAIMS, BOOTSTRAP_AUDIENCE

@dataclass(frozen=True, repr=False)
class Approval:
    ref: str
    selection: bytes
    workflow_id: str
    initiating_user_id: str
    broker_actor_id: str
    bootstrap_subject: str
    approved_reviewer_user_ids: tuple
    source_update_policy: str
    revision: int
    not_before: int
    expires_at: int
    observed_at: int
    valid_until: int
    revoked: bool = False

    def __post_init__(self):
        _handle(self.ref)
        selection_digest(self.selection)
        c = self.configuration
        launch = c["launch"]
        require(all(number(x) for x in (self.workflow_id, self.initiating_user_id, self.broker_actor_id))
                and self.initiating_user_id != self.broker_actor_id
                and reference(self.bootstrap_subject) and self.bootstrap_subject != launch["sub"]
                and type(self.approved_reviewer_user_ids) is tuple and 0 < len(self.approved_reviewer_user_ids) <= 100
                and all(number(x) for x in self.approved_reviewer_user_ids)
                and len(set(self.approved_reviewer_user_ids)) == len(self.approved_reviewer_user_ids)
                and self.initiating_user_id not in self.approved_reviewer_user_ids
                and self.broker_actor_id not in self.approved_reviewer_user_ids
                and self.source_update_policy in ("coordinated", "bounded-residual-exposure")
                and all(integer(x) for x in (self.revision, self.not_before, self.expires_at, self.observed_at, self.valid_until))
                and self.revision > 0 and self.not_before < self.expires_at <= self.not_before + 3600
                and c["not_before"] <= self.not_before < self.expires_at <= c["expires_at"]
                and self.observed_at < self.valid_until <= self.observed_at + 60
                and type(self.revoked) is bool, ERROR)
        require(launch["repository"] == REPOSITORY and launch["ref"] == REF
                and launch["workflow_ref"] == REPOSITORY + "/" + CALLER + "@" + REF
                and launch["job_workflow_ref"] == REPOSITORY + "/" + REUSABLE + "@" + REF
                and launch["sha"] == launch["workflow_sha"] == launch["job_workflow_sha"] == c["sources"]["adapter"]["commit"]
                and c["issuer"]["audience"] != BOOTSTRAP_AUDIENCE, ERROR)

    @property
    def configuration(self):
        return decode_object(self.selection)["configuration"]

    @property
    def commitment(self):
        value = asdict(self)
        value["selection"] = decode_object(self.selection)
        # Fresh authenticated observation times and revocation are not a new approval.
        for k in ("observed_at", "valid_until", "revoked"):
            del value[k]
        return digest(value)

    @property
    def request(self):
        return {"ref": "main", "inputs": {"accepted_commit": self.configuration["launch"]["sha"],
            "selection_digest": selection_digest(self.selection), "preauthorization_ref": self.ref}}

    @property
    def journal_scope(self):
        config = self.configuration
        return {"case_ref": config["case_ref"], "repository": config["launch"]["repository"],
            "repository_id": config["launch"]["repository_id"], "workflow_id": self.workflow_id,
            "ref": config["launch"]["ref"], "accepted_commit": config["launch"]["sha"],
            "selection_digest": selection_digest(self.selection), "initiating_user_id": self.initiating_user_id,
            "broker_actor_id": self.broker_actor_id, "not_before": self.not_before, "expires_at": self.expires_at,
            "revision": self.revision, "source_update_policy": self.source_update_policy}

    def current(self, now):
        require(integer(now) and self.not_before <= now < min(self.expires_at, self.valid_until)
                and self.observed_at <= now and not self.revoked, ERROR)

    def context(self, run_id):
        require(number(run_id), ERROR)
        launch = self.configuration["launch"]
        return DispatchContext(**{k: launch[k] for k in ("repository", "repository_id", "ref", "sha", "workflow_ref", "workflow_sha")},
            event_name="workflow_dispatch", run_id=run_id, run_attempt="1", accepted_commit=launch["sha"],
            source_commit=launch["sha"], selection_digest=selection_digest(self.selection), preauthorization_ref=self.ref)

    def policy(self, run_id, phase):
        launch = self.configuration["launch"]
        expected = {k: launch[k] for k in BASE_CLAIMS - {"run_id", "run_attempt", "event_name"}}
        expected.update(run_id=run_id, run_attempt="1", event_name="workflow_dispatch")
        if phase == "preflight":
            expected["sub"] = self.bootstrap_subject
        elif phase == "protected":
            expected["environment"] = launch["environment"]
        return IdentityPolicy(phase, BOOTSTRAP_AUDIENCE, self.configuration["issuer"]["audience"], expected)
