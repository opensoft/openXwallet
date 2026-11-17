"""Selected ARM/key observations and pinned private guest/issuer/state readers.

No RunCommand, mutation, initialization, signing, token mint or discovery occurs.
Managed identity is a host fact; it does not establish process isolation.
"""
from dataclasses import dataclass,asdict,replace
import re
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from workload_factory_binding.evidence import BindingError,byte_digest,canonical,digest,integer,require,valid_digest,decode64
from ..config import _handle
from ..github_bootstrap.common import document,number
from .issuance import permissions
from .readback import ERROR,ObservationClient,RequestReader,Snapshot

ARM="https://management.azure.com"
VERSIONS={"virtualMachines":"2025-04-01&$expand=instanceView","images":"2026-03-01","disks":"2026-03-02",
    "networkInterfaces":"2026-01-01","virtualNetworks":"2026-01-01","networkSecurityGroups":"2026-01-01","publicIPAddresses":"2026-01-01"}
RESOURCE=re.compile(r"/subscriptions/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}/resourceGroups/[A-Za-z0-9_.()-]{1,90}/providers/Microsoft\.(Compute|Network)/([A-Za-z]+)/[A-Za-z0-9_.-]{1,80}(/subnets/[A-Za-z0-9_.-]{1,80})?")


def resource(value,kind):
    require(type(value) is str and RESOURCE.fullmatch(value) and RESOURCE.fullmatch(value)[2]==kind,ERROR)
    require(RESOURCE.fullmatch(value)[1]==("Compute" if kind in ("virtualMachines","images","disks") else "Network"),ERROR)
    return value


@dataclass(frozen=True,repr=False)
class DeploymentSelection:
    vm_id:str
    incarnation_id:str
    image_id:str
    disk_ids:tuple
    nic_id:str
    subnet_id:str
    nsg_id:str
    role:str
    identity_digest:str
    model_digest:str
    storage_digest:str
    network_digest:str
    public_ip_id:str | None=None

    def record(self):
        for value,kind in [(self.vm_id,"virtualMachines"),(self.image_id,"images"),(self.nic_id,"networkInterfaces"),
                           (self.subnet_id,"virtualNetworks"),(self.nsg_id,"networkSecurityGroups")]:resource(value,kind)
        require(type(self.disk_ids) is tuple and 1<=len(self.disk_ids)<=2 and len(set(self.disk_ids))==len(self.disk_ids)
            and self.role in ("control","gate","worker") and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",self.incarnation_id)
            and all(valid_digest(v) for v in (self.identity_digest,self.model_digest,self.storage_digest,self.network_digest)),ERROR)
        for value in self.disk_ids:resource(value,"disks")
        if self.public_ip_id is not None:resource(self.public_ip_id,"publicIPAddresses")
        require(self.role!="worker" or self.public_ip_id is None,ERROR)
        return asdict(self)


class DeploymentReader:
    def __init__(self,*,selection,reader,principal_ref):
        require(type(selection) is DeploymentSelection and type(reader) is RequestReader,ERROR);_handle(principal_ref)
        self.selection,self.reader,self.principal=selection,reader,principal_ref
        self.record=canonical(selection.record())

    def get(self,identifier,kind,decision):
        value=self.reader.get(ARM+resource(identifier,kind)+"?api-version="+VERSIONS[kind],group="arm",decision=decision)
        require(type(value) is dict and value.get("id")==identifier and type(value.get("properties")) is dict
            and value["properties"].get("provisioningState")=="Succeeded" and "nextLink" not in value,ERROR)
        return value

    @staticmethod
    def _validated_identity(vm,s):
        identity=vm.get("identity");require(type(identity) is dict and digest(identity)==s.identity_digest,ERROR)
        if s.role=="worker":require(identity=={"type":"None"},ERROR)
        else:
            require(identity.get("type")=="UserAssigned" and set(identity)=={"type","userAssignedIdentities"}
                and type(identity["userAssignedIdentities"]) is dict and 0<len(identity["userAssignedIdentities"])<=3,ERROR)
            for entry in identity["userAssignedIdentities"].values():
                require(type(entry) is dict and set(entry)=={"clientId","principalId"}
                    and all(type(v) is str and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",v) for v in entry.values()),ERROR)
        return identity

    def _read_network(self,s,decision):
        nic=self.get(s.nic_id,"networkInterfaces",decision);subnet=self.get(s.subnet_id,"virtualNetworks",decision)
        nsg=self.get(s.nsg_id,"networkSecurityGroups",decision);np=nic["properties"];sp=subnet["properties"]
        require(np.get("virtualMachine")=={"id":s.vm_id} and type(np.get("ipConfigurations")) is list
            and len(np["ipConfigurations"])==1 and np.get("enableIPForwarding") is False
            and sp.get("networkSecurityGroup")=={"id":s.nsg_id}
            and ("networkSecurityGroup" not in np or np["networkSecurityGroup"]=={"id":s.nsg_id}),ERROR)
        ip=np["ipConfigurations"][0]["properties"]
        require(ip.get("subnet")=={"id":s.subnet_id} and type(ip.get("privateIPAddress")) is str
            and (ip.get("publicIPAddress") if s.public_ip_id is not None else "publicIPAddress" not in ip)
            and type(nsg["properties"].get("securityRules")) is list
            and type(nsg["properties"].get("defaultSecurityRules")) is list,ERROR)
        network={"nic":np,"subnet":sp,"nsg":nsg["properties"]}
        if s.public_ip_id is not None:
            require(ip["publicIPAddress"]=={"id":s.public_ip_id},ERROR)
            network["public_ip"]=self.get(s.public_ip_id,"publicIPAddresses",decision)["properties"]
        return network

    def read(self,*,decision):
        try:
            before=decision.now();s=self.selection;require(canonical(s.record())==self.record,ERROR)
            vm=self.get(s.vm_id,"virtualMachines",decision);p=vm["properties"]
            require(p.get("vmId")==s.incarnation_id and type(p.get("instanceView")) is dict
                and type(p["instanceView"].get("statuses")) is list
                and any(x.get("code")=="PowerState/running" for x in p["instanceView"]["statuses"] if type(x) is dict),ERROR)
            identity=self._validated_identity(vm,s)
            model={k:v for k,v in p.items() if k!="instanceView"};require(digest(model)==s.model_digest,ERROR)
            storage=p.get("storageProfile");require(type(storage) is dict and storage.get("imageReference")=={"id":s.image_id}
                and type(storage.get("osDisk")) is dict and type(storage["osDisk"].get("managedDisk")) is dict
                and storage["osDisk"]["managedDisk"].get("id")==s.disk_ids[0]
                and type(storage.get("dataDisks")) is list,ERROR)
            managed=storage["osDisk"]["managedDisk"]
            require("storageAccountType" not in managed or (type(managed["storageAccountType"]) is str
                and re.fullmatch(r"(?a:\w{1,64})",managed["storageAccountType"])),ERROR)
            network_profile=p.get("networkProfile")
            require(tuple(x["managedDisk"]["id"] for x in storage["dataDisks"])==s.disk_ids[1:]
                and type(network_profile) is dict and type(network_profile.get("networkInterfaces")) is list
                and len(network_profile["networkInterfaces"])==1,ERROR)
            link=network_profile["networkInterfaces"][0]
            require(type(link) is dict and link.get("id")==s.nic_id,ERROR)
            if "properties" in link:
                extra=link["properties"]
                require(type(extra) is dict and ("primary" not in extra or type(extra["primary"]) is bool)
                    and ("deleteOption" not in extra or extra["deleteOption"] in ("Delete","Detach")),ERROR)
            image=self.get(s.image_id,"images",decision);disks=[self.get(v,"disks",decision) for v in s.disk_ids]
            require(all(x.get("managedBy")==s.vm_id and x["properties"].get("diskState")=="Attached" for x in disks),ERROR)
            store={"image":image["properties"],"disks":[x["properties"] for x in disks]}
            require(digest(store)==s.storage_digest,ERROR)
            network=self._read_network(s,decision)
            require(digest(network)==s.network_digest,ERROR);decision.now()
            facts={"vm_id":vm["id"],"incarnation_id":p["vmId"],"identity":identity,"model_digest":digest(model),
                "storage_digest":digest(store),"network_digest":digest(network),"image_id":storage["imageReference"]["id"]}
            return Snapshot(self.principal,canonical(facts),before,decision.deadline,decision)
        except Exception:raise BindingError(ERROR) from None


class IssuerReader:
    def __init__(self,*,client,reader,key_uri,public_key_digest,issuer_ref,role,repository_id,enrollment_digest):
        require(type(client) is ObservationClient and type(reader) is RequestReader and valid_digest(public_key_digest)
            and valid_digest(enrollment_digest) and re.fullmatch(r"https://[a-z0-9-]{3,24}\.vault\.azure\.net/keys/[A-Za-z0-9-]{1,127}/[0-9a-f]{32}",key_uri),ERROR)
        _handle(issuer_ref);permissions(role);require(number(repository_id),ERROR)
        self.client,self.reader,self.uri=client,reader,key_uri
        self.expected={"issuer_ref":issuer_ref,"key_uri":key_uri,"public_key_digest":public_key_digest,"role":role,
            "repository_id":repository_id,"permissions":permissions(role),"enrollment_digest":enrollment_digest}
        self.commitment=digest(self.expected)

    def read(self,reference,*,decision):
        try:
            require(digest(self.expected)==self.commitment and self.uri==self.expected["key_uri"],ERROR)
            value=self.reader.get(self.uri+"?api-version=2025-07-01",group="key",decision=decision)
            key,attributes=value.get("key"),value.get("attributes")
            require(type(key) is dict and key.get("kid")==self.uri and key.get("kty")=="RSA"
                and type(key.get("key_ops")) is list and len(key["key_ops"])==2 and set(key["key_ops"])=={"sign","verify"} and not any(v in key for v in ("d","p","q","dp","dq","qi"))
                and type(attributes) is dict and attributes.get("enabled") is True
                and integer(attributes.get("nbf")) and integer(attributes.get("exp"))
                and attributes["nbf"]<=decision.now()<attributes["exp"],ERROR)
            require(type(key.get("n")) is str and 340<=len(key["n"])<=684 and type(key.get("e")) is str and 1<=len(key["e"])<=12,ERROR)
            modulus,exponent=decode64(key["n"]),decode64(key["e"])
            require(256<=len(modulus)<=512 and 0<len(exponent)<=8,ERROR)
            public=rsa.RSAPublicNumbers(int.from_bytes(exponent,"big"),int.from_bytes(modulus,"big")).public_key()
            require(2048<=public.key_size<=4096 and byte_digest(public.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo))==self.expected["public_key_digest"],ERROR)
            decision.clip(attributes["exp"]);result=self.client.read("issuer",reference,decision=decision);facts=result.data()
            require(set(facts)==set(self.expected)|{"credential_digest","credential_expires_at","state"}
                and all(canonical(facts[k])==canonical(v) for k,v in self.expected.items())
                and valid_digest(facts["credential_digest"]) and facts["state"]=="active"
                and integer(facts["credential_expires_at"]) and decision.now()<facts["credential_expires_at"],ERROR)
            decision.clip(facts["credential_expires_at"]);return replace(result,expires_at=decision.deadline)
        except Exception:raise BindingError(ERROR) from None


class GuestReader:
    def __init__(self,*,client,expected):
        require(type(client) is ObservationClient and type(expected) is dict
            and set(expected)==set("host_id incarnation_id boot_id source_digest uid policy_digest artifacts_digest".split()),ERROR)
        require(integer(expected["uid"]) and expected["uid"]>0 and all(valid_digest(expected[k]) for k in ("source_digest","policy_digest","artifacts_digest")),ERROR)
        self.client,self.raw=client,canonical(expected)

    def read(self,reference,*,decision):
        try:
            result=self.client.read("guest",reference,decision=decision);facts=result.data();expected=document(self.raw)
            require(set(facts)==set(expected)|{"process","denials","positive_controls"}
                and all(canonical(facts[k])==canonical(v) for k,v in expected.items()),ERROR)
            process=facts["process"];ops={"imds","resolver","sign","control","policy_write"}
            require(type(process) is dict and set(process)=={"pid","start_time","uid","capabilities"}
                and all(integer(process[k]) and 0<process[k]<=2**63-1 for k in ("pid","start_time","uid"))
                and process["uid"]==facts["uid"] and process["capabilities"]==[]
                and facts["denials"]==dict.fromkeys(ops, "denied") and facts["positive_controls"]==dict.fromkeys(ops, "ok"),ERROR)
            return result
        except Exception:raise BindingError(ERROR) from None


class StateReader:
    def __init__(self,*,current,initialization,selection):
        require(type(current) is ObservationClient and type(initialization) is ObservationClient
            and current.principal!=initialization.principal
            and current.transport.server_certificate_digest!=initialization.transport.server_certificate_digest
            and current.origin!=initialization.origin and current.scope==initialization.scope
            and type(selection) is dict and set(selection)==set("store_ref initialization_ref retention_ref recovery_ref".split()),ERROR)
        for value in selection.values():_handle(value)
        self.current,self.initialization,self.raw=current,initialization,canonical(selection)

    def read(self,*,decision):
        try:
            from ..github_bootstrap.common import document
            selection=document(self.raw);receipt=self.initialization.read("initialization",selection["initialization_ref"],decision=decision)
            initial=receipt.data();require(set(initial)=={"selection","identity","state"} and initial["selection"]==selection and initial["state"]=="valid",ERROR)
            identity=initial["identity"];require(type(identity) is dict and set(identity)==set("directory_device directory_inode database_device database_inode".split())
                and all(integer(v) and v>0 for v in identity.values()),ERROR)
            current=self.current.read("state",selection["store_ref"],decision=decision);facts=current.data()
            require(set(facts)==set("selection identity initialization_digest status private links journal_mode integrity schema".split())
                and facts["selection"]==selection and facts["identity"]==identity and facts["initialization_digest"]==receipt.digest
                and facts["status"]=="active-no-restore" and facts["private"] is True and type(facts["links"]) is int and facts["links"]==1
                and facts["journal_mode"]=="delete" and facts["integrity"]=="ok" and facts["schema"]=="owning-replay-ledger-v1",ERROR)
            # Re-observe independent current receipt/revocation after the guest/store read.
            final=self.initialization.read("initialization",selection["initialization_ref"],decision=decision)
            require(final.digest==receipt.digest,ERROR);return replace(current,expires_at=decision.deadline)
        except Exception:raise BindingError(ERROR) from None


class PlanFactReader:
    """Current consumed-plan facts from the pinned operator/journal source.

    The authority must derive these from its actual current retained records and
    qualified providers. This client neither constructs a full config nor makes
    a v2 plan into a v1 approval. Returned source facts still meet admission's
    independent complete-byte/claim checks.
    """
    def __init__(self,*,client):
        require(type(client) is ObservationClient,ERROR);self.client=client

    def read(self,reference,*,decision):
        try:
            from .admission import PlanFacts
            value=self.client.read("plan",reference,decision=decision);facts=value.data()
            fields=set(PlanFacts.__dataclass_fields__)-{"principal_ref","observed_at","expires_at"}
            scope=self.client.scope
            require(set(facts)==fields and facts["preauthorization_ref"]==reference
                and facts["plan_digest"]==scope.plan_digest and facts["case_ref"]==scope.case_ref
                and facts["accepted_commit"]==scope.source_commit and facts["state"]=="consumed-current"
                and type(facts["launch"]) is dict and facts["launch"].get("run_id")==scope.run_id
                and facts["launch"].get("run_attempt")==scope.run_attempt
                and all(facts["launch"].get(k)==scope.source_commit for k in ("sha","workflow_sha","job_workflow_sha"))
                and all(valid_digest(facts[k]) for k in ("hosting_selection_digest","protection_digest","scheduler_capability_digest")),ERROR)
            _handle(facts["source_hold_ref"])
            return PlanFacts(principal_ref=value.principal_ref,**facts,observed_at=value.observed_at,expires_at=decision.deadline)
        except Exception:raise BindingError(ERROR) from None
