"""Fixed repository observations; no provider write, returned URL or policy fallback."""
from dataclasses import dataclass
import base64
import hashlib
import re
from urllib.parse import quote
from workload_factory_binding.evidence import BindingError,canonical,digest,integer,require,valid_digest
from ..config import _handle
from ..workflow import EnvironmentReadback,REPOSITORY,CALLER,REUSABLE,REF
from ..github_bootstrap.common import SHA,number
from ..github_bootstrap.graph import GraphSource
from ..github_bootstrap.controller import Controller
from .readback import ERROR,ReadBudget,RequestReader,Snapshot,ObservationClient

ROOT="https://api.github.com/repos/"+REPOSITORY


def positive(value):
    require(type(value) is int and number(str(value)),ERROR);return str(value)


@dataclass(frozen=True,repr=False)
class SourceObservation:
    principal_ref:str
    graph:GraphSource
    observed_at:int
    expires_at:int
    _decision:object


class GithubReadbacks:
    def __init__(self,*,reader,principal_ref,repository_id):
        require(type(reader) is RequestReader and number(repository_id),ERROR);_handle(principal_ref)
        self.reader,self.principal,self.repository_id=reader,principal_ref,repository_id

    def get(self,path,group,decision):return self.reader.get(ROOT+path,group=group,decision=decision)

    def main(self,*,decision):
        value=self.get("/git/ref/heads/main","source",decision)
        require(type(value) is dict and value.get("ref")==REF and type(value.get("object")) is dict
            and value["object"].get("type")=="commit" and type(value["object"].get("sha")) is str
            and SHA.fullmatch(value["object"]["sha"]) and value["object"]["sha"]!="0"*40,ERROR)
        return value["object"]["sha"]

    def begin_source(self,commit,*,decision):
        try:
            before=decision.now();require(type(commit) is str and SHA.fullmatch(commit),ERROR)
            require(self.main(decision=decision)==commit,ERROR);raws=[]
            for path in (CALLER,REUSABLE):
                value=self.get("/contents/"+path+"?ref="+commit,"source",decision)
                require(type(value) is dict and value.get("type")=="file" and value.get("path")==path
                    and value.get("encoding")=="base64" and type(value.get("content")) is str
                    and len(value["content"])<=90000 and type(value.get("size")) is int and 0<value["size"]<=65536
                    and "submodule_git_url" not in value and "target" not in value,ERROR)
                encoded=value["content"].replace("\n","")
                raw=base64.b64decode(encoded,validate=True);require(len(raw)==value["size"],ERROR)
                blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw,usedforsecurity=False).hexdigest()
                require(value.get("sha")==blob,ERROR);raws.append(raw)
            return SourceObservation(self.principal,GraphSource(commit,*raws),before,decision.deadline,decision)
        except Exception:raise BindingError(ERROR) from None

    def finish_source(self,source,*,decision):
        require(type(source) is SourceObservation and source.principal_ref==self.principal and source._decision is decision,ERROR)
        decision.clip(source.expires_at)
        require(self.main(decision=decision)==source.graph.commit,ERROR);return source

    def source(self,commit,*,decision):return self.finish_source(self.begin_source(commit,decision=decision),decision=decision)

    def environment(self,name,*,decision):
        try:
            require(type(name) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,100}",name),ERROR)
            ReadBudget(decision).begin_protection()
            before=decision.now();path="/environments/"+quote(name,safe="")
            env=self.get(path,"protection",decision)
            require(type(env) is dict and env.get("name")==name and env.get("can_admins_bypass") is False,ERROR)
            environment_id=positive(env.get("id"));policy=env.get("deployment_branch_policy")
            require(type(policy) is dict and set(policy)=={"protected_branches","custom_branch_policies"}
                and policy["protected_branches"] is False and policy["custom_branch_policies"] is True,ERROR)
            rules=env.get("protection_rules")
            require(type(rules) is list and len(rules)==2 and all(type(x) is dict for x in rules)
                and sorted(x.get("type","") for x in rules)==["branch_policy","required_reviewers"],ERROR)
            review=next(x for x in rules if x["type"]=="required_reviewers")
            require(review.get("prevent_self_review") is True and type(review.get("reviewers")) is list and 0<len(review["reviewers"])<=6,ERROR)
            reviewers=[]
            for item in review["reviewers"]:
                require(type(item) is dict and item.get("type") in ("User","Team") and type(item.get("reviewer")) is dict,ERROR)
                reviewers.append({"type":item["type"],"id":positive(item["reviewer"].get("id"))})
            require(len({(x["type"],x["id"]) for x in reviewers})==len(reviewers),ERROR)
            policies=[];total=None
            for page in (1,2):
                value=self.get(path+"/deployment-branch-policies?per_page=32&page="+str(page),"protection",decision)
                require(type(value) is dict and type(value.get("total_count")) is int and 0<value["total_count"]<=32
                    and type(value.get("branch_policies")) is list and 0<len(value["branch_policies"])<=32
                    and (total is None or total==value["total_count"]),ERROR)
                total=value["total_count"];policies.extend(value["branch_policies"])
                require(len(policies)<=total,ERROR)
                if len(policies)==total:break
            require(len(policies)==total==1,ERROR);branch=policies[0]
            require(type(branch) is dict and branch.get("type")=="branch" and branch.get("name")=="main",ERROR);positive(branch.get("id"))
            projection={"repository_id":self.repository_id,"environment_id":environment_id,"environment":env["name"],
                "reviewer_ids":reviewers,"prevent_self_review":review["prevent_self_review"],"can_admins_bypass":env["can_admins_bypass"],"deployment_refs":[REF]}
            decision.now();return EnvironmentReadback(self.principal,True,projection,before,decision.deadline)
        except Exception:raise BindingError(ERROR) from None

    def begin_control(self,identifier,*,decision):
        positive(identifier)
        value=self.get("/rulesets?includes_parents=true&per_page=32&page=1","control",decision)
        require(type(value) is list and len(value)==1 and type(value[0]) is dict
            and value[0].get("id")==identifier and type(value[0].get("id")) is int
            and value[0].get("source_type")=="Repository" and value[0].get("source")==REPOSITORY
            and value[0].get("enforcement")=="active",ERROR)
        return identifier

    def finish_control(self,identifier,*,decision):
        try:
            before=decision.now();value=self.get("/rulesets/"+positive(identifier)+"?includes_parents=true","control",decision)
            require(type(value) is dict and value.get("id")==identifier and type(value.get("id")) is int
                and value.get("source_type")=="Repository" and value.get("source")==REPOSITORY
                and value.get("target")=="branch" and value.get("enforcement")=="active"
                and value.get("conditions")=={"ref_name":{"include":[REF],"exclude":[]}},ERROR)
            actors=value.get("bypass_actors");rules=value.get("rules")
            require(type(actors) is list and len(actors)<=6 and type(rules) is list and 0<len(rules)<=32,ERROR)
            for actor in actors:
                require(type(actor) is dict and set(actor)=={"actor_id","actor_type","bypass_mode"}
                    and actor["actor_type"] in ("Team","Integration","RepositoryRole") and actor["bypass_mode"]=="always",ERROR);positive(actor["actor_id"])
            require(len({(a["actor_type"],a["actor_id"]) for a in actors})==len(actors),ERROR)
            require(all(type(r) is dict and r.get("type") in ("update","deletion","non_fast_forward") for r in rules)
                and len({r["type"] for r in rules})==len(rules) and any(r["type"]=="update" for r in rules),ERROR)
            for rule in rules:
                expected={"type":"update","parameters":{"update_allows_fetch_and_merge":False}} if rule["type"]=="update" else {"type":rule["type"]}
                require(canonical(rule)==canonical(expected),ERROR)
            facts={k:value[k] for k in ("id","source_type","source","target","enforcement","conditions","bypass_actors","rules")}
            return Snapshot(self.principal,canonical(facts),before,decision.deadline,decision)
        except Exception:raise BindingError(ERROR) from None


@dataclass(frozen=True,repr=False)
class ProtectedObservation:
    correlation:object
    source:SourceObservation
    environment:EnvironmentReadback
    control:Snapshot
    hold:Snapshot
    valid_until:int


class ProtectedReadbacks:
    """Read-only composition over the accepted correlation engine; no v1/v2 coercion.

    Its controller already selects its approval/phase/identity/journal. A v2 plan
    is not fabricated as a full v1 approval. Later hosting selects phase wiring.
    """
    def __init__(self,*,controller,github,hold,hold_ref,hold_owner):
        require(type(controller) is Controller and type(github) is GithubReadbacks and type(hold) is ObservationClient,ERROR)
        _handle(hold_ref);_handle(hold_owner);self.controller,self.github,self.hold,self.ref=controller,github,hold,hold_ref
        self.owner=hold_owner

    def _hold(self,decision):
        result=self.hold.read("hold",self.ref,decision=decision);value=result.data()
        require(set(value)==set("source_sha owner_ref control_id control_digest state not_before expires_at".split())
            and value["source_sha"]==self.hold.scope.source_commit and value["owner_ref"]==self.owner and value["state"]=="active"
            and valid_digest(value["control_digest"]) and integer(value["not_before"]) and integer(value["expires_at"])
            and value["not_before"]<=decision.now()<value["expires_at"],ERROR)
        _handle(value["owner_ref"]);positive(value["control_id"]);decision.clip(value["expires_at"]);return result

    def correlate(self,ref,token,context,*,decision):
        try:
            scope=self.hold.scope
            require(context.selection_digest==scope.plan_digest and context.source_commit==scope.source_commit
                and context.run_id==scope.run_id and context.run_attempt==scope.run_attempt,ERROR)
            hold=self._hold(decision);identifier=self.github.begin_control(hold.data()["control_id"],decision=decision)
            source=self.github.begin_source(scope.source_commit,decision=decision);environments=[]
            def environment(name,*,deadline):
                require(deadline<=decision.deadline,ERROR)
                result=self.github.environment(name,decision=decision);environments.append(result);return result
            parent=self.controller
            selected=Controller(phase=parent.phase,journal=parent.journal,read_approval=parent.read_approval,
                verifier=parent.verifier,provider=parent.provider,load_graph=lambda **_:source.graph,
                read_environment=environment,environment_principal=self.github.principal)
            correlated=selected.correlate(ref,token,context,decision=decision)
            self.github.finish_source(source,decision=decision)
            control=self.github.finish_control(identifier,decision=decision)
            require(control.digest==hold.data()["control_digest"],ERROR)
            final=self._hold(decision);require(final.digest==hold.digest,ERROR)
            ReadBudget(decision).check();decision.clip(correlated.valid_until)
            require(len(environments)==1 and correlated.approval.configuration["case_ref"]==scope.case_ref,ERROR)
            return ProtectedObservation(correlated,source,environments[0],control,final,decision.deadline)
        except Exception:raise BindingError(ERROR) from None
