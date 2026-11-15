"""Exact-version RSA App issuance. No ambient identity, retry, dispatch or activation."""
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib
import re
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from workload_factory_binding.evidence import BindingError,byte_digest,canonical,digest,encode64,decode64,integer,require,valid_digest
from ..config import _handle
from ..github_bootstrap.common import document
from ..github_bootstrap.broker import API,VERSION
from ..workflow import REPOSITORY
from .nonces import ERROR,NonceLedger
from .private_http import Response
BEARER = "Bearer "
JSON_TYPE = "application/json"

@dataclass(frozen=True,repr=False)
class AppSelection:
    client_id:str
    app_id:int
    installation_id:int
    repository_id:int
    owner_id:int
    role:str
    key_uri:str
    public_key:object
    enrollment_digest:str

@dataclass(frozen=True,repr=False)
class IssuanceCurrent:
    principal_ref:str
    selection_digest:str
    ref:str
    nonce:str
    active:bool
    observed_at:int
    expires_at:int


def permissions(role):
    require(role in ("broker","reader","source-reader"),ERROR)
    return {"actions":"write" if role=="broker" else "read","metadata":"read",**({"contents":"read"} if role=="source-reader" else {})}


def selection_record(value):
    require(type(value) is AppSelection and type(value.client_id) is str
        and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}",value.client_id)
        and all(integer(v) and 0<v<=2**53-1 for v in (value.app_id,value.installation_id,value.repository_id,value.owner_id))
        and type(value.key_uri) is str and re.fullmatch(r"https://[a-z0-9-]{3,24}\.vault\.azure\.net/keys/[A-Za-z0-9-]{1,127}/[0-9a-f]{32}",value.key_uri)
        and valid_digest(value.enrollment_digest)
        and isinstance(value.public_key,rsa.RSAPublicKey) and 2048<=value.public_key.key_size<=4096,ERROR)
    return {"client_id":value.client_id,"app_id":value.app_id,"installation_id":value.installation_id,
        "repository_id":value.repository_id,"owner_id":value.owner_id,"repository":REPOSITORY,
        "role":value.role,"enrollment_digest":value.enrollment_digest,"permissions":permissions(value.role),"key_uri":value.key_uri,
        "public_key_digest":byte_digest(value.public_key.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo))}


@dataclass(frozen=True,repr=False)
class IssuedToken:
    # Private capability: only authenticated role delivery/retirement may expose it.
    credential:str
    role:str
    expires_at:int | None
    use_until:int
    ref:str
    selection_digest:str
    ledger:object
    _decision:object

    def readback(self):
        return {"role":self.role,"ref":self.ref,"selection_digest":self.selection_digest,
            "token_digest":byte_digest(self.credential.encode()),"expires_at":self.expires_at,"use_until":self.use_until}


class InstallationIssuer:
    def __init__(self,*,selection,ledger,transport,vault_credential,read_current,current_principal):
        self.record=selection_record(selection);_handle(current_principal)
        require(type(ledger) is NonceLedger and all(callable(x) for x in (vault_credential,read_current))
                and callable(getattr(transport,"exchange",None)),ERROR)
        self.selection,self.selection_digest=selection,digest(self.record)
        self.ledger,self.transport=ledger,transport
        self.vault_credential,self.read_current,self.principal=vault_credential,read_current,current_principal
        self._pending={}

    def current(self,ref,nonce,decision):
        require(selection_record(self.selection)==self.record and digest(self.record)==self.selection_digest,ERROR)
        before=decision.now();value=self.read_current(ref,deadline=decision.deadline);now=decision.now()
        require(type(value) is IssuanceCurrent and value.principal_ref==self.principal
            and value.selection_digest==self.selection_digest and value.ref==ref and value.nonce==nonce
            and value.active is True and integer(value.observed_at) and integer(value.expires_at)
            and before<=value.observed_at<=now<value.expires_at<=value.observed_at+60,ERROR)
        decision.clip(value.expires_at)

    def issue(self,ref,nonce,*,decision):
        try:
            self.current(ref,nonce,decision)
            self.ledger.reserve(ref,nonce,digest({"selection":self.selection_digest,"ref":ref,"nonce":nonce}),decision=decision)
            check=lambda:self.current(ref,nonce,decision)
            now=decision.now();header=encode64(canonical({"alg":"RS256","typ":"JWT"}))
            claims=encode64(canonical({"iss":self.selection.client_id,"iat":now-60,"exp":min(now+60,decision.deadline)}))
            signing=(header+"."+claims).encode()
            credential=self.vault_credential(deadline=decision.deadline);check()
            require(type(credential) is str and 0<len(credential)<=8192 and all(32<ord(c)<127 for c in credential),ERROR)
            raw=self.transport.exchange("POST",self.selection.key_uri+"/sign?api-version=2025-07-01",
                headers={"Authorization":BEARER+credential,"Content-Type":JSON_TYPE,"Accept":JSON_TYPE,"Accept-Encoding":"identity"},
                body=canonical({"alg":"RS256","value":encode64(hashlib.sha256(signing).digest())}),decision=decision,before_send=check)
            check();require(type(raw) is Response and raw.status==200,ERROR);signed=document(raw.body,65536)
            require(type(signed) is dict and signed.get("kid")==self.selection.key_uri,ERROR)
            signature=decode64(signed["value"]);self.selection.public_key.verify(signature,signing,padding.PKCS1v15(),hashes.SHA256())
            jwt=header+"."+claims+"."+encode64(signature)
            def request(method,path,bearer=jwt,body=b"",*,validate_after=True):
                check();r=self.transport.exchange(method,API+path,headers={"Authorization":BEARER+bearer,
                    "Accept":"application/vnd.github+json","Content-Type":JSON_TYPE,"User-Agent":"openXwallet-hosted-issuer",
                    "Accept-Encoding":"identity","X-GitHub-Api-Version":VERSION},body=body,decision=decision,before_send=check)
                if validate_after:check()
                require(type(r) is Response,ERROR);return r
            r=request("GET","/app");require(r.status==200,ERROR);app=document(r.body,65536)
            require(type(app) is dict and type(app.get("id")) is int and app["id"]==self.selection.app_id
                    and app.get("client_id")==self.selection.client_id,ERROR)
            install_path="/app/installations/"+str(self.selection.installation_id)
            r=request("GET",install_path);require(r.status==200,ERROR);install=document(r.body,65536)
            require(type(install) is dict and type(install.get("id")) is int and install["id"]==self.selection.installation_id
                    and type(install.get("app_id")) is int and install["app_id"]==self.selection.app_id
                    and type(install.get("account")) is dict and type(install["account"].get("id")) is int
                    and install["account"]["id"]==self.selection.owner_id and install["account"].get("login")==REPOSITORY.split("/")[0]
                    and install.get("repository_selection")=="selected" and "suspended_at" in install and install["suspended_at"] is None
                    and install.get("permissions")==self.record["permissions"],ERROR)
            r=request("POST",install_path+"/access_tokens",body=canonical({"repository_ids":[self.selection.repository_id],"permissions":self.record["permissions"]}),validate_after=False)
            require(r.status==201,ERROR);value=document(r.body,65536);token=value.get("token")
            require(type(token) is str and 0<len(token)<=8192 and all(32<ord(c)<127 for c in token),ERROR)
            # Keep the returned private cleanup handle even when subsequent checks refuse.
            cap=IssuedToken(token,self.selection.role,None,decision.deadline,ref,self.selection_digest,self.ledger,decision)
            self._pending[ref]=cap
            check()
            self.ledger.transition(ref,("consumed",),"consumed",decision=decision,token_digest=byte_digest(token.encode()))
            require(value.get("repository_selection")=="selected" and value.get("permissions")==self.record["permissions"],ERROR)
            expiry=value.get("expires_at");require(type(expiry) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",expiry,re.ASCII),ERROR)
            expiry=int(datetime.strptime(expiry,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
            require(decision.now()<expiry<=decision.now()+3600,ERROR)
            r=request("GET","/installation/repositories?per_page=2&page=1",bearer=token)
            require(r.status==200,ERROR);repos=document(r.body,65536)
            require(type(repos) is dict and type(repos.get("total_count")) is int and repos["total_count"]==1
                    and type(repos.get("repositories")) is list and len(repos["repositories"])==1
                    and type(repos["repositories"][0].get("id")) is int
                    and repos["repositories"][0]["id"]==self.selection.repository_id
                    and repos["repositories"][0].get("full_name")==REPOSITORY,ERROR)
            check();cap=IssuedToken(token,self.selection.role,expiry,min(expiry,decision.deadline),ref,self.selection_digest,self.ledger,decision)
            self._pending[ref]=cap;self.ledger.transition(ref,("consumed",),"issued",decision=decision)
            decision.now();return cap
        except Exception:raise BindingError(ERROR) from None

    def resolve(self,ref,nonce,*,decision):
        """Current, non-renewing private credential seam for trusted role brokers."""
        try:
            require(ref in self._pending,ERROR);cap=self._pending[ref]
            require(cap.expires_at is not None and decision.now()<min(cap.use_until,cap.expires_at)
                    and cap._decision.now()<cap.use_until,ERROR)
            decision.clip(min(cap.use_until,cap.expires_at));self.current(ref,nonce,decision)
            row=self.ledger.state(ref,decision=decision)
            require(row["state"]=="issued" and row["token_digest"]==byte_digest(cap.credential.encode()),ERROR)
            self.current(ref,nonce,decision);cap._decision.clip(decision.deadline)
            return cap.credential
        except Exception:raise BindingError(ERROR) from None

    def pending(self,ref):
        """Trusted cleanup capability only; never a readiness/worker endpoint."""
        require(ref in self._pending,ERROR);return self._pending[ref]


class InstallationRetirer:
    def __init__(self,*,writer,observer):
        require(writer is not observer and all(callable(getattr(x,"exchange",None)) for x in (writer,observer)),ERROR)
        self.writer,self.observer=writer,observer

    def request(self,transport,method,cap,decision):
        return transport.exchange(method,API+("/installation/token" if method=="DELETE" else "/installation/repositories?per_page=2&page=1"),
            headers={"Authorization":BEARER+cap.credential,"Accept":"application/vnd.github+json","Accept-Encoding":"identity",
                     "User-Agent":"openXwallet-hosted-retirement","X-GitHub-Api-Version":VERSION},decision=decision)

    def retire(self,capability,*,decision):
        try:
            require(type(capability) is IssuedToken and type(capability.ledger) is NonceLedger,ERROR)
            capability.ledger.transition(capability.ref,("consumed","issued"),"retiring",decision=decision)
            response=self.request(self.writer,"DELETE",capability,decision);decision.now()
            require(type(response) is Response and response.status==204 and response.body==b"",ERROR)
            return self.reconcile(capability,decision=decision)
        except Exception:raise BindingError(ERROR) from None

    def reconcile(self,capability,*,decision):
        try:
            require(type(capability) is IssuedToken and capability.ledger.state(capability.ref,decision=decision)["state"]=="retiring",ERROR)
            response=self.request(self.observer,"GET",capability,decision);decision.now()
            require(type(response) is Response and response.status==401,ERROR)
            capability.ledger.transition(capability.ref,("retiring",),"retired",decision=decision)
            return {**capability.readback(),"state":"retired"}
        except Exception:raise BindingError(ERROR) from None


class RoleDelivery:
    """Private mTLS issuer port: role is intrinsic, never selected by request JSON."""
    def __init__(self,*,enrollment,issuer):
        from .enrollment import EnrollmentAuthority
        require(type(enrollment) is EnrollmentAuthority and type(issuer) is InstallationIssuer
                and enrollment.selection.role==issuer.selection.role
                and issuer.selection.enrollment_digest==enrollment.selection_digest,ERROR)
        self.enrollment,self.issuer=enrollment,issuer

    def deliver(self,raw,*,channel,decision):
        from .nonces import Unavailable
        try:
            self.enrollment.authorize(channel=channel,role=self.issuer.selection.role,decision=decision)
            value=document(raw,16384)
            require(type(value) is dict and set(value)=={"ref","nonce"},ERROR)
            # After peer authentication, issuer failure does not establish a
            # peer denial. Keep unavailable distinct in the private hosting port.
            try:self.issuer.issue(value["ref"],value["nonce"],decision=decision)
            except Exception:raise Unavailable(ERROR) from None
            self.enrollment.authorize(channel=channel,role=self.issuer.selection.role,decision=decision)
            try:token=self.issuer.resolve(value["ref"],value["nonce"],decision=decision)
            except Exception:raise Unavailable(ERROR) from None
            return {"credential":token,"role":self.issuer.selection.role}
        except Unavailable:raise
        except Exception:raise BindingError(ERROR) from None
