"""One separately authorized request attempt, with durable pre-I/O consumption."""
from dataclasses import dataclass
from workload_factory_binding.evidence import BindingError, canonical, integer, reference, require
from . import ERROR
from .approval import Approval
from .common import document, number
from .https import Https, Response

API = "https://api.github.com"
VERSION = "2026-03-10"

@dataclass(frozen=True, repr=False)
class SourceReadback:
    principal_ref: str
    sha: str
    observed_at: int
    expires_at: int

class DispatchBroker:
    """Trusted operator embedding only. No token, worker or CLI entrypoint grants dispatch."""
    def __init__(self, *, journal, read_approval, read_source, source_principal, credential, transport=None):
        self.journal, self.read_approval, self.read_source = journal, read_approval, read_source
        require(reference(source_principal), ERROR)
        self.source_principal = source_principal
        self.credential = credential
        self.transport = transport if transport is not None else Https()

    def dispatch(self, ref, *, decision):
        try:
            approval = self.read_approval(ref, deadline=decision.deadline)
            require(type(approval) is Approval and approval.ref == ref, ERROR)
            approval.current(decision.now())
            decision.clip(min(approval.expires_at, approval.valid_until))
            def checkpoint():
                before_source = decision.now()
                source = self.read_source(deadline=decision.deadline)
                require(type(source) is SourceReadback and source.principal_ref == self.source_principal
                        and source.sha == approval.configuration["launch"]["sha"]
                        and integer(source.observed_at) and integer(source.expires_at)
                        and before_source <= source.observed_at <= decision.now() < source.expires_at <= source.observed_at + 60, ERROR)
                decision.clip(source.expires_at)
                before = decision.now()
                current = self.read_approval(ref, deadline=decision.deadline)
                require(type(current) is Approval and current.commitment == approval.commitment
                        and current.observed_at >= before, ERROR)
                current.current(decision.now())
                decision.clip(min(current.expires_at, current.valid_until))
            checkpoint()
            request = approval.request
            self.journal.reserve(approval, request)
            # Any exception from this point retains the consumed attempt, including cancellation.
            credential = self.credential(deadline=decision.deadline)
            require(reference(credential) and len(credential) <= 8192, ERROR)
            decision.now()
            response = self.transport.exchange("POST", API + "/repos/" + approval.configuration["launch"]["repository"]
                + "/actions/workflows/" + approval.workflow_id + "/dispatches", headers={
                "Authorization": "Bearer " + credential, "Accept": "application/vnd.github+json",
                "Content-Type": "application/json", "Accept-Encoding": "identity", "X-GitHub-Api-Version": VERSION},
                body=canonical(request), decision=decision, before_send=checkpoint)
            decision.now()
            require(type(response) is Response and response.status == 200, ERROR)
            value = document(response.body, 65536)
            require(type(value) is dict and type(value.get("workflow_run_id")) is int
                    and number(str(value["workflow_run_id"])), ERROR)
            checkpoint()
            run_id = str(value["workflow_run_id"])
            self.journal.record_run(approval, run_id)
            return run_id  # Response URLs are deliberately never used or retained.
        except Exception:
            raise BindingError(ERROR) from None
