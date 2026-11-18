"""Selected read-only capabilities and one shared non-renewing observation budget.

Provider/authority administration remains trusted; snapshots are source facts,
not live qualification or an atomic provider transaction.
"""
from dataclasses import dataclass,asdict
import secrets
from urllib.parse import urlsplit
from workload_factory_binding.evidence import BindingError,canonical,digest,integer,require,valid_digest
from ..config import _handle
from ..github_bootstrap.common import Decision,SHA,number,document
from ..github_bootstrap.broker import VERSION
from .private_http import PrivateHttps,Response

ERROR="hosted-readback-refused"
PROFILE="openxfactory-current-observation-internal-v1"
LIMITS={"protection":3,"source":4,"control":2,"arm":24,"key":3,"private":12}
JSON_TYPE="application/json"


def _ledger(decision, *, finalization=False, staging=False, qualification=False):
    return {"counts": dict.fromkeys(LIMITS, 0), "members": {decision: 0},
            "finalization": finalization, "staging": staging, "qualification": qualification, "stage_observations": 0, "protection_observations": 0}


def start_finalization(decision):
    """Trusted operation entrypoint only; never a field in worker input."""
    require(type(decision) is Decision and not hasattr(decision, "_hosted_reads")
            and decision.api_requests == 0, ERROR)
    decision.now()
    decision._hosted_reads = _ledger(decision, finalization=True)
    ReadBudget(decision).check()


def start_staging(decision):
    """Trusted protected-stage entry; one original decision, never a late upgrade."""
    require(type(decision) is Decision and not hasattr(decision, "_hosted_reads")
            and decision.api_requests == 0, ERROR)
    decision.now()
    decision._hosted_reads = _ledger(decision, staging=True)
    ReadBudget(decision).check()


def start_qualification(decision):
    """Source-accepted trusted entry before lifecycle construction or first I/O.

    One original Decision owns private39. It cannot upgrade an existing ledger,
    consume a different phase's authority, join a member or renew either clock.
    """
    require(type(decision) is Decision and not hasattr(decision, "_hosted_reads")
            and decision.api_requests == 0, ERROR)
    decision.now()
    decision._hosted_reads = _ledger(decision, qualification=True)
    ReadBudget(decision).check()


class ReadBudget:
    def __init__(self, decision):
        require(type(decision) is Decision, ERROR)
        self.decision = decision
        if not hasattr(decision, "_hosted_reads"):
            decision._hosted_reads = _ledger(decision)
        self.state = decision._hosted_reads
        self.check()

    def check(self):
        members = self.state["members"]
        require(self.decision in members and 1 <= len(members) <= (1 if self.state["staging"] or self.state["qualification"] else 2), ERROR)
        correlation_limit = 8 if self.state["staging"] else 4
        for member, highwater in tuple(members.items()):
            member.now()
            count = member.api_requests
            require(integer(count) and highwater <= count <= correlation_limit, ERROR)
            members[member] = count
        require(sum(members.values()) <= correlation_limit, ERROR)
        expiry = min(member.deadline for member in members)
        for member in members:
            member.clip(expiry)
        requests = self.github_requests
        if self.state["staging"]:
            request_limit = 26
        elif self.state["finalization"]:
            request_limit = 28
        else:
            request_limit = 13
        require(requests <= request_limit, ERROR)

    @property
    def github_requests(self):
        return sum(member.api_requests for member in self.state["members"]) + sum(
            self.state["counts"][name] for name in ("protection", "source", "control"))

    def join(self, independent):
        """Keep an independent clock/observer, sharing consumed enclosing authority."""
        self.check()
        require(not self.state["staging"] and not self.state["qualification"], ERROR)
        require(type(independent) is Decision and not hasattr(independent, "_hosted_reads")
                and independent.api_requests == 0 and len(self.state["members"]) == 1, ERROR)
        remaining = min(member.remaining() for member in self.state["members"])
        independent.now()
        independent.end = min(independent.end, independent.last_mono + remaining)
        self.state["members"][independent] = 0
        independent._hosted_reads = self.state
        ReadBudget(independent).check()

    def consume_correlation(self):
        self.check()
        require(sum(self.state["members"].values()) < (8 if self.state["staging"] else 4), ERROR)
        self.decision.api_requests += 1
        self.check()

    def begin_staging_observation(self):
        self.check()
        require(self.state["staging"] and self.state["stage_observations"] < 2, ERROR)
        self.state["stage_observations"] += 1

    def begin_protection(self):
        self.check()
        if self.state["staging"]:
            require(self.state["protection_observations"] < 2, ERROR)
        if self.state["finalization"]:
            require(self.state["protection_observations"] < 6, ERROR)
        self.state["protection_observations"] += 1

    def consume(self, group):
        self.check()
        require(group in LIMITS, ERROR)
        if self.state["staging"]:
            limit = {"protection": 6, "source": 8, "control": 4, "private": 16}.get(group, LIMITS[group])
        elif group == "protection" and self.state["finalization"]:
            limit = 18
        elif group == "private" and self.state["qualification"]:
            limit = 39
        else:
            limit = LIMITS[group]
        require(self.state["counts"][group] < limit, ERROR)
        self.state["counts"][group] += 1
        self.check()

    def count(self, group):
        return self.state["counts"][group]


@dataclass(frozen=True,repr=False)
class ReadScope:
    case_ref:str
    plan_digest:str
    source_commit:str
    run_id:str
    run_attempt:str

    def record(self):
        _handle(self.case_ref)
        require(valid_digest(self.plan_digest) and type(self.source_commit) is str
            and SHA.fullmatch(self.source_commit) and self.source_commit!="0"*40
            and number(self.run_id) and self.run_attempt=="1",ERROR)
        return asdict(self)


@dataclass(frozen=True,repr=False)
class Snapshot:
    principal_ref:str
    raw:bytes
    observed_at:int
    expires_at:int
    _decision:object

    def data(self):
        self._decision.now();return document(self.raw,65536)
    @property
    def digest(self):return digest(self.data())


def current_times(value,*,before,decision):
    now=decision.now()
    require(integer(value.get("observed_at")) and integer(value.get("expires_at"))
        and before<=value["observed_at"]<=now<value["expires_at"]<=value["observed_at"]+60,ERROR)
    decision.clip(value["expires_at"])


class RequestReader:
    """Existing selected bearer only. Never resolves ambient identity or issues tokens."""
    def __init__(self,*,credential,transport=None):
        require(callable(credential),ERROR);self.credential=credential
        self.transport=transport if transport is not None else PrivateHttps()

    def get(self,url,*,group,decision):
        try:
            ReadBudget(decision).consume(group)
            token=self.credential(deadline=decision.deadline);decision.now()
            require(type(token) is str and 0<len(token)<=8192 and all(32<ord(c)<127 for c in token),ERROR)
            response=self.transport.exchange("GET",url,headers={"Authorization":"Bearer "+token,
                "Accept":"application/vnd.github+json" if url.startswith("https://api.github.com/") else JSON_TYPE,
                "Accept-Encoding":"identity","Cache-Control":"no-cache","User-Agent":"openXwallet-current-readback",
                "X-GitHub-Api-Version":VERSION},decision=decision,before_send=lambda:ReadBudget(decision).check())
            ReadBudget(decision).check()
            require(type(response) is Response and response.status==200,ERROR)
            value=document(response.body,1048576);ReadBudget(decision).check();return value
        except Exception:raise BindingError(ERROR) from None


class ObservationClient:
    """Pinned mTLS selected fact source; the request sends no candidate facts.

    A server/authority must derive actual observations under its selected trusted
    administration. This client supplies no listener, setup or control operation.
    """
    def __init__(self,*,origin,principal_ref,scope,transport):
        _handle(principal_ref);require(type(scope) is ReadScope,ERROR);scope.record()
        parsed=urlsplit(origin)
        require(parsed.scheme=="https" and parsed.hostname and not parsed.path and not parsed.query and not parsed.fragment
            and parsed.username is None and parsed.password is None and type(transport) is PrivateHttps
            and transport.observation_origin==origin and valid_digest(transport.server_certificate_digest)
            and all(x is not None for x in (transport.ca,transport.cert,transport.key)),ERROR)
        self.origin,self.principal,self.scope,self.transport=origin,principal_ref,scope,transport
        self.scope_digest=digest(scope.record())
        self.endpoint_binding=(origin,principal_ref,transport.server_certificate_digest,transport.materials())

    def read(self,operation,reference,*,decision):
        try:
            require(operation in ("hold","guest","issuer","state","initialization","plan","capability","stage-grant","stage-lease")
                and digest(self.scope.record())==self.scope_digest
                and self.endpoint_binding==(self.origin,self.principal,self.transport.server_certificate_digest,self.transport.materials())
                and self.transport.observation_origin==self.origin,ERROR);_handle(reference)
            ReadBudget(decision).consume("private");before=decision.now();nonce=secrets.token_hex(32)
            request=canonical({"profile":PROFILE,"operation":operation,"reference":reference,"nonce":nonce})
            response=self.transport.exchange("POST",self.origin+"/readback",headers={"Content-Type":JSON_TYPE,"Accept":JSON_TYPE},
                body=request,decision=decision,before_send=lambda:ReadBudget(decision).check())
            ReadBudget(decision).check();require(type(response) is Response and response.status==200,ERROR)
            value=document(response.body,65536)
            require(type(value) is dict and set(value)==set("profile principal_ref operation reference nonce scope facts observed_at expires_at".split())
                and value["profile"]==PROFILE and value["principal_ref"]==self.principal
                and value["operation"]==operation and value["reference"]==reference and value["nonce"]==nonce
                and canonical(value["scope"])==canonical(self.scope.record()) and type(value["facts"]) is dict,ERROR)
            current_times(value,before=before,decision=decision)
            return Snapshot(self.principal,canonical(value["facts"]),value["observed_at"],decision.deadline,decision)
        except Exception:raise BindingError(ERROR) from None


class DecisionRead:
    """Explicit opt-in callback preserving the admission caller's actual Decision."""
    def __init__(self,reader):
        require(callable(reader),ERROR);self.reader=reader

    def __call__(self,*arguments,decision):
        ReadBudget(decision).check();result=self.reader(*arguments,decision=decision)
        ReadBudget(decision).check();return result
