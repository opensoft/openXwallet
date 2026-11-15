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


class ReadBudget:
    def __init__(self,decision):
        require(type(decision) is Decision,ERROR)
        self.decision=decision
        if not hasattr(decision,"_hosted_reads"):
            decision._hosted_reads={"counts":{name:0 for name in LIMITS},"correlation":0}
        self.state=decision._hosted_reads;self.check()

    def check(self):
        self.decision.now();correlation=self.decision.api_requests
        require(integer(correlation) and self.state["correlation"]<=correlation<=4,ERROR)
        self.state["correlation"]=correlation
        require(self.github_requests<=13,ERROR)

    @property
    def github_requests(self):
        return self.decision.api_requests+sum(self.state["counts"][k] for k in ("protection","source","control"))

    def consume(self,group):
        self.check();require(group in LIMITS and self.state["counts"][group]<LIMITS[group],ERROR)
        self.state["counts"][group]+=1;self.check()

    def count(self,group):return self.state["counts"][group]


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
            require(operation in ("hold","guest","issuer","state","initialization","plan","capability")
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
