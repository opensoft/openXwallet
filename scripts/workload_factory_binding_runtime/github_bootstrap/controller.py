"""Correlate verified identity with independent journal, provider and protection facts."""
from dataclasses import dataclass
from workload_factory_binding.evidence import BindingError, digest, integer, require
from ..workflow import EnvironmentReadback, CALLER, REUSABLE, REF
from ..bootstrap import validate_dispatch_context
from . import ERROR
from .approval import Approval
from .graph import validate_graph
from .identity import BootstrapVerifier

@dataclass(frozen=True, repr=False)
class Correlation:
    approval: Approval
    run_id: str
    phase: str
    valid_until: int

def _run_binding(run, approval, run_id):
    launch = approval.configuration["launch"]
    require(type(run) is dict and type(run.get("id")) is int and str(run["id"]) == run_id
            and type(run.get("run_attempt")) is int and run["run_attempt"] == 1
            and type(run.get("workflow_id")) is int and str(run["workflow_id"]) == approval.workflow_id
            and run.get("head_sha") == launch["sha"] and run.get("head_branch") == "main"
            and run.get("path") == CALLER and run.get("event") == "workflow_dispatch"
            and run.get("status") == "in_progress"
            and type(run.get("repository")) is dict
            and run["repository"].get("full_name") == launch["repository"]
            and type(run["repository"].get("id")) is int and str(run["repository"]["id"]) == launch["repository_id"]
            and type(run.get("head_repository")) is dict
            and run["head_repository"].get("full_name") == launch["repository"]
            and type(run["head_repository"].get("id")) is int
            and str(run["head_repository"]["id"]) == launch["repository_id"]
            and run["repository"]["owner"]["login"] == launch["repository_owner"]
            and type(run["repository"]["owner"]["id"]) is int
            and str(run["repository"]["owner"]["id"]) == launch["repository_owner_id"]
            and all(type(run.get(k)) is dict and type(run[k].get("id")) is int
            and str(run[k]["id"]) == approval.broker_actor_id for k in ("actor", "triggering_actor")), ERROR)
    referenced = run.get("referenced_workflows")
    require(type(referenced) is list and 0 < len(referenced) <= 32, ERROR)
    matching = [r for r in referenced if type(r) is dict
        and r.get("path") == launch["repository"] + "/" + REUSABLE + "@" + REF]
    require(len(matching) == 1 and matching[0].get("sha") == launch["job_workflow_sha"], ERROR)
    return (run["id"], run["run_attempt"], run["workflow_id"], run["head_sha"], run["head_branch"],
        run["path"], run["event"], run["status"], run["repository"]["id"], run["repository"]["full_name"],
        run["repository"]["owner"]["id"], run["repository"]["owner"]["login"],
        run["head_repository"]["id"], run["head_repository"]["full_name"],
        run["actor"]["id"], run["triggering_actor"]["id"], matching[0]["path"], matching[0]["sha"])

class Controller:
    """Authenticated operator capabilities are constructor dependencies, never request fields.

    Hosting must authenticate the approval/journal/environment providers and isolate
    them from workers. This source adapter does not deploy that boundary.
    """
    def __init__(self, *, phase, journal, read_approval, verifier, provider,
                 load_graph, read_environment, environment_principal):
        require(phase in ("preflight", "protected") and type(verifier) is BootstrapVerifier, ERROR)
        self.phase, self.journal, self.read_approval = phase, journal, read_approval
        self.verifier, self.provider, self.load_graph = verifier, provider, load_graph
        self.read_environment, self.environment_principal = read_environment, environment_principal

    def correlate(self, ref, token, context, *, decision):
        try:
            validate_dispatch_context(context)
            before = decision.now()
            approval = self.read_approval(ref, deadline=decision.deadline)
            require(type(approval) is Approval and approval.ref == ref and approval.observed_at >= before, ERROR)
            approval.current(decision.now())
            decision.clip(min(approval.valid_until, approval.expires_at))
            run_id = self.journal.read(approval)
            require(run_id is not None and context == approval.context(run_id), ERROR)
            policy = approval.policy(run_id, self.phase)
            identity = self.verifier.verify(token, policy, now=decision.now())
            decision.clip(identity.valid_until)
            validate_graph(self.load_graph(deadline=decision.deadline), approval)
            decision.now()
            reads = self.provider.decision(context.repository, decision)
            run = reads.run(run_id)
            c, launch = approval.configuration, approval.configuration["launch"]
            binding = _run_binding(run, approval, run_id)
            jobs = reads.jobs(run_id, "1")
            expected_name = "invoke / " + ("admission" if self.phase == "preflight" else "protected-qualification")
            eligible = [j for j in jobs if j.get("name") == expected_name]
            require(len(eligible) == 1 and eligible[0].get("status") == "in_progress"
                    and eligible[0].get("head_sha") == launch["sha"]
                    and type(eligible[0].get("run_id")) is int and str(eligible[0]["run_id"]) == run_id, ERROR)
            if self.phase == "protected":
                reviews = reads.reviews(run_id)
                relevant = []
                for review in reviews:
                    require(type(review) is dict and type(review.get("environments")) is list, ERROR)
                    for env in review["environments"]:
                        require(type(env) is dict, ERROR)
                        if str(env.get("id")) == c["protection"]["environment_id"]:
                            require(type(env.get("id")) is int and env.get("name") == launch["environment"], ERROR)
                            relevant.append(review)
                require(relevant and all(x.get("state") == "approved" and type(x.get("user")) is dict
                    and type(x["user"].get("id")) is int and x["user"].get("type") == "User"
                    and str(x["user"]["id"]) in approval.approved_reviewer_user_ids
                    and str(x["user"]["id"]) != approval.initiating_user_id for x in relevant), ERROR)
            before = decision.now()
            environment = self.read_environment(launch["environment"], deadline=decision.deadline)
            require(type(environment) is EnvironmentReadback and environment.exists is True
                    and environment.principal_ref == self.environment_principal
                    and integer(environment.observed_at) and integer(environment.expires_at)
                    and before <= environment.observed_at <= decision.now() < environment.expires_at <= environment.observed_at + 60
                    and digest(environment.protection) == digest(c["protection"]), ERROR)
            decision.clip(environment.expires_at)
            # Re-observe the current attempt/source after jobs, reviews and protection I/O.
            # Exhausting the four-request budget refuses instead of using older facts.
            latest = reads.run(run_id)
            require(_run_binding(latest, approval, run_id) == binding, ERROR)
            return self.recheck(Correlation(approval, run_id, self.phase, decision.deadline), decision=decision)
        except Exception:
            raise BindingError(ERROR) from None

    def recheck(self, correlation, *, decision):
        try:
            require(type(correlation) is Correlation and correlation.phase == self.phase, ERROR)
            decision.clip(correlation.valid_until)
            before = decision.now()
            current = self.read_approval(correlation.approval.ref, deadline=decision.deadline)
            require(type(current) is Approval and current.commitment == correlation.approval.commitment
                    and current.observed_at >= before, ERROR)
            current.current(decision.now())
            decision.clip(min(current.valid_until, current.expires_at))
            require(self.journal.read(current) == correlation.run_id, ERROR)
            decision.now()
            return Correlation(current, correlation.run_id, self.phase, decision.deadline)
        except Exception:
            raise BindingError(ERROR) from None
