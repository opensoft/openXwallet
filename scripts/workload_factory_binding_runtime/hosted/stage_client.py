"""Fixed intrinsic public admission/private host routes; selected source endpoints."""
from dataclasses import asdict
import secrets
import re
from workload_factory_binding.evidence import BindingError,canonical,digest,integer,require,valid_digest
from ..config import _handle
from .private_http import PrivateHttps,Response
from ..github_bootstrap.common import document,Decision
from ..github_bootstrap.client import TokenClient
from ..github_bootstrap.identity import BOOTSTRAP_AUDIENCE
from .readback import ReadBudget
from .stage_store import ERROR
from .stage_controller import StageAdmission

PROFILE="openxfactory-hosted-channel-internal-v1"


class Channel:
    def __init__(self,*,origin,principal,transport,private):
        _handle(principal);require(type(transport) is PrivateHttps
            and (transport.agent_origin if private else transport.admission_origin)==origin,ERROR)
        self.origin,self.principal,self.transport,self.private=origin,principal,transport,private
        self.binding=(origin,principal,transport.server_certificate_digest,transport.materials())

    def current(self):
        require(self.binding==(self.origin,self.principal,self.transport.server_certificate_digest,self.transport.materials())
            and (self.transport.agent_origin if self.private else self.transport.admission_origin)==self.origin,ERROR)

    def call(self,path,value,*,decision,token=None,before_send=lambda:None):
        self.current()
        if self.private:ReadBudget(decision).consume("private")
        nonce=secrets.token_hex(32);body={"profile":PROFILE,"nonce":nonce,"deadline":decision.deadline,"arguments":value}
        headers={"Content-Type":"application/json","Accept":"application/json"}
        if not self.private:
            require(type(token) is str and 0<len(token)<=16377 and all(32<ord(x)<127 for x in token),ERROR)
            headers["Authorization"]="Bearer "+token
        before=decision.now()
        def check():ReadBudget(decision).check();before_send();ReadBudget(decision).check()
        response=self.transport.exchange("POST",self.origin+path,headers=headers,body=canonical(body),decision=decision,before_send=check)
        self.current();require(type(response) is Response and response.status==200,ERROR);value=document(response.body)
        require(type(value) is dict and set(value)=={"profile","principal_ref","nonce","operation","facts","observed_at","expires_at"}
            and value["profile"]==PROFILE and value["principal_ref"]==self.principal and value["nonce"]==nonce
            and value["operation"]==path and type(value["facts"]) is dict and integer(value["observed_at"])
            and integer(value["expires_at"]) and before<=value["observed_at"]<=decision.now()<value["expires_at"]<=value["observed_at"]+60,ERROR)
        decision.clip(value["expires_at"]);return value["facts"]


class HostClient:
    def __init__(self,*,channel,scope):
        require(type(channel) is Channel and channel.private and type(scope) is dict,ERROR)
        self.channel,self.raw=channel,canonical(scope);self.unit_binding=None;self.generation_binding=None

    def _read(self,operation,ref,decision,unit_digest=None,before_send=lambda:None):
        scope=document(self.raw);require(ref==scope["launch_ref"],ERROR)
        arguments={"launch_ref":ref,"scope_digest":digest(scope)}
        if unit_digest is not None:require(valid_digest(unit_digest),ERROR);arguments["unit_digest"]=unit_digest
        value=self.channel.call("/stage/"+operation,arguments,decision=decision,before_send=before_send)
        require(set(value)=={"scope_digest","state","unit","generation"} and value["scope_digest"]==digest(scope)
            and value["state"] in ("reserved","registered","start-consumed","running","indeterminate","refused","stopped"),ERROR)
        unit=value["unit"]
        if unit is not None:
            require(type(unit) is dict and set(unit)==set("manager_kind unit_ref invocation_ref scope_digest host_ref incarnation_ref boot_id manager_pid manager_start".split())
                and unit["manager_kind"]=="reference-posix-session-v1" and unit["scope_digest"]==digest(scope)
                and all(unit[k]==scope[k] for k in ("host_ref","incarnation_ref","boot_id"))
                and all(type(unit[k]) is int and unit[k]>0 for k in ("manager_pid","manager_start")),ERROR)
            _handle(unit["unit_ref"]);_handle(unit["invocation_ref"])
            require(unit["unit_ref"]=="unit:"+digest(scope).split(":")[1],ERROR)
            raw_unit=canonical(unit)
            require(self.unit_binding is None or self.unit_binding==raw_unit,ERROR)
            self.unit_binding=raw_unit
        if value["state"]=="running":
            generation=value["generation"]
            require(unit is not None and type(generation) is dict and set(generation)==set("unit_digest pid start_time session_id boot_id uid policy_digest cgroup_digest".split())
                and generation["unit_digest"]==digest(unit) and generation["boot_id"]==scope["boot_id"]
                and all(type(generation[k]) is int and generation[k]>0 for k in ("pid","start_time","session_id","uid"))
                and generation["uid"]==scope["worker_uid"] and generation["session_id"]==generation["pid"] and valid_digest(generation["policy_digest"])
                and generation["policy_digest"]==scope["hosting_selection_digest"] and valid_digest(generation["cgroup_digest"]),ERROR)
            raw_generation=canonical(generation)
            require(self.generation_binding is None or self.generation_binding==raw_generation,ERROR)
            self.generation_binding=raw_generation
        return value

    def register(self,ref,*,decision):return self._read("register",ref,decision)
    def start(self,ref,unit_digest,*,decision,before_send):return self._read("start",ref,decision,unit_digest,before_send)
    def status(self,ref,*,decision):return self._read("status",ref,decision)


class AdmissionClient:
    def __init__(self,*,channel,phase):
        require(type(channel) is Channel and not channel.private and phase in ("preflight","protected"),ERROR)
        self.channel,self.phase=channel,phase
        self.path="/v2/plan" if phase=="preflight" else "/v2/protected"
        self.binding=(channel,phase,self.path)

    def read(self,context,token,*,decision):
        require(self.binding==(self.channel,self.phase,self.path),ERROR)
        inputs={k:getattr(context,k) for k in ("accepted_commit","selection_digest","preauthorization_ref")}
        value=self.channel.call(self.path,inputs,decision=decision,token=token)
        require(set(value)==set(StageAdmission.__dataclass_fields__) and value["profile"]=="openxfactory-hosted-admission-internal-v2"
            and value["phase"]==self.phase and value["plan_digest"]==context.selection_digest
            and value["state"] in (("plan-ready",) if self.phase=="preflight" else ("registered","start-consumed","running","reserved","indeterminate","refused","stopped"))
            and integer(value["valid_until"]) and decision.now()<value["valid_until"]<=decision.deadline,ERROR)
        _handle(value["case_ref"]);_handle(value["launch_ref"])
        require(type(value["environment"]) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,100}",value["environment"]),ERROR)
        decision.clip(value["valid_until"]);return StageAdmission(**value)


def probe_worker_denial(*,channel,scope,decision):
    """Actual valid worker peer refusal only; outage/malformed requests never pass."""
    require(type(channel) is Channel and channel.private,ERROR)
    channel.current();ReadBudget(decision).consume("private")
    body={"profile":PROFILE,"nonce":secrets.token_hex(32),"deadline":decision.deadline,
          "arguments":{"launch_ref":scope["launch_ref"],"scope_digest":digest(scope)}}
    response=channel.transport.exchange("POST",channel.origin+"/stage/register",headers={"Content-Type":"application/json","Accept":"application/json"},
        body=canonical(body),decision=decision,before_send=lambda:ReadBudget(decision).check())
    channel.current();require(type(response) is Response and response.status==403 and document(response.body)=={"error":"hosted-stage-denied"},ERROR)
    return {"outcome":"denied","server_ref":channel.principal,"scope_digest":digest(scope)}
