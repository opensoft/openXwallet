"""Current independent provider doubles and actual TLS/process/store observations.

All Azure/GitHub identities below are fixture data. No public provider is called.
"""
from copy import deepcopy
from dataclasses import asdict
import base64
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import os
from pathlib import Path
import select
import sqlite3
import ssl
import subprocess
import sys
from threading import Thread
import time
from types import SimpleNamespace
from urllib.parse import urlsplit
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from workload_factory_binding.evidence import BindingError,byte_digest,canonical,digest,encode64
from workload_factory_binding.ledger import ReplayLedger
from workload_factory_binding_runtime.state import inspect_initialized_state
from workload_factory_binding_runtime.github_bootstrap.common import Decision,document
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps,Response
from workload_factory_binding_runtime.hosted.readback import PROFILE,ReadScope,RequestReader,ObservationClient
from workload_factory_binding_runtime.hosted.github_readback import GithubReadbacks
from workload_factory_binding_runtime.hosted.platform_readback import DeploymentSelection,DeploymentReader,IssuerReader,GuestReader,StateReader
from factory_binding.test_owner_integration import make_pki
from .test_hosted_credentials import parent_call,worker_call

ROOT=Path(__file__).resolve().parents[2]
GITHUB="/repos/opensoft/openXwallet"
VMROOT="/subscriptions/11111111-1111-4111-8111-111111111111/resourceGroups/fixture/providers/"


@pytest.fixture
def rb(tmp_path,request):
    s=SimpleNamespace(now=int(time.time()),mono=0.,calls=[],hook=None,mutate=None,private_mutate=None,
        scope=ReadScope("case:fixture",digest({"plan":"fixture"}),"a"*40,"789","1"),peer="gate",guest_grant=False,guest_outage=False)
    s.use=lambda:Decision(clock=lambda:s.now,monotonic=lambda:s.mono)
    s.main_sha=s.scope.source_commit
    s.environment={"id":101,"name":"qa", "can_admins_bypass":False,
        "deployment_branch_policy":{"protected_branches":False,"custom_branch_policies":True},
        "protection_rules":[{"type":"required_reviewers","prevent_self_review":True,"reviewers":[{"type":"User","reviewer":{"id":99}}]},{"type":"branch_policy"}]}
    s.policies={"total_count":1,"branch_policies":[{"id":11,"name":"main","type":"branch"}]}
    s.rule={"id":42,"source_type":"Repository","source":"opensoft/openXwallet","target":"branch","enforcement":"active",
        "conditions":{"ref_name":{"include":["refs/heads/main"],"exclude":[]}},"bypass_actors":[],
        "rules":[{"type":"update","parameters":{"update_allows_fetch_and_merge":False}},{"type":"deletion"}]}
    s.rulesets=[{"id":42,"source_type":"Repository","source":"opensoft/openXwallet","enforcement":"active"}]
    s.hold={"source_sha":s.main_sha,"owner_ref":"principal:hold-owner","control_id":42,"control_digest":digest(s.rule),
        "state":"active","not_before":s.now-1,"expires_at":s.now+60}
    s.contents={}
    for name in ("protected-runtime-qualification.yml","protected-runtime-qualification-run.yml"):
        path=".github/workflows/"+name;raw=(ROOT/path).read_bytes()
        s.contents[path]={"type":"file","path":path,"encoding":"base64","content":base64.b64encode(raw).decode(),"size":len(raw),
            "sha":hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw,usedforsecurity=False).hexdigest(),"download_url":"https://forbidden.invalid/unused"}
    s.state_selection={k:k.replace("_ref","")+":fixture" for k in ("store_ref","initialization_ref","retention_ref","recovery_ref")}
    s.store=ReplayLedger(tmp_path/"store")
    s.initial={"selection":deepcopy(s.state_selection),"identity":asdict(inspect_initialized_state(s.store.directory)),"state":"valid"}
    s.recovery="active-no-restore"
    worker=tmp_path/"readback_worker.py";worker.write_bytes(Path(__file__).with_name("readback_worker.py").read_bytes())
    s.guest_source=worker;s.guest_policy=tmp_path/"guest-policy.json";s.guest_policy.write_bytes(canonical({"privilege":"fixture-kernel-port"}));s.guest_policy.chmod(0o600)
    s.guest_artifact=Path(sys.executable).resolve()
    s.process=subprocess.Popen([sys.executable,"-I","-B",str(worker)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        env={"PATH":os.defpath,"LANG":"C.UTF-8"})
    def stop_guest():
        if s.process.poll() is None:s.process.terminate()
        try:s.process.wait(timeout=3)
        except subprocess.TimeoutExpired:s.process.kill();s.process.wait(timeout=3)
        for stream in (s.process.stdin,s.process.stdout):
            if not stream.closed:stream.close()
    request.addfinalizer(stop_guest)
    assert select.select([s.process.stdout],[],[],3)[0]
    assert s.process.stdout.readline()==b"ready\n"
    s.guest_process=s.process
    s.guest_expected={"host_id":VMROOT+"Microsoft.Compute/virtualMachines/worker","incarnation_id":"22222222-2222-4222-8222-222222222222",
        "boot_id":Path("/proc/sys/kernel/random/boot_id").read_text().strip(),"source_digest":byte_digest(worker.read_bytes()),
        "uid":os.getuid(),"policy_digest":digest({"privilege":"fixture-kernel-port"}),"artifacts_digest":digest({"worker":byte_digest(worker.read_bytes()),"python":byte_digest(s.guest_artifact.read_bytes())})}
    s.guest_host=s.guest_expected["host_id"];s.guest_incarnation=s.guest_expected["incarnation_id"]
    s.key=rsa.generate_private_key(public_exponent=65537,key_size=2048);numbers=s.key.public_key().public_numbers()
    s.key_uri="https://fixture-vault.vault.azure.net/keys/app-key/"+"a"*32
    s.keydata={"key":{"kid":s.key_uri,"kty":"RSA","key_ops":["sign","verify"],"n":encode64(numbers.n.to_bytes(256,"big")),"e":encode64(numbers.e.to_bytes(3,"big"))},
        "attributes":{"enabled":True,"nbf":s.now-1,"exp":s.now+100}}
    s.issuer_expected={"issuer_ref":"issuer:fixture","key_uri":s.key_uri,"public_key_digest":byte_digest(s.key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)),
        "role":"reader","repository_id":"123","permissions":{"actions":"read","metadata":"read"},"enrollment_digest":digest({"enrollment":"fixture"})}
    s.issuer={**s.issuer_expected,"credential_digest":digest({"credential":"fixture-only"}),"credential_expires_at":s.now+40,"state":"active"}
    ids={"vm":s.guest_expected["host_id"],"image":VMROOT+"Microsoft.Compute/images/image-001","disk":VMROOT+"Microsoft.Compute/disks/os-001",
        "nic":VMROOT+"Microsoft.Network/networkInterfaces/nic-001","subnet":VMROOT+"Microsoft.Network/virtualNetworks/vnet-001/subnets/worker",
        "nsg":VMROOT+"Microsoft.Network/networkSecurityGroups/worker"};s.ids=ids
    vmprops={"vmId":s.guest_expected["incarnation_id"],"provisioningState":"Succeeded","hardwareProfile":{"vmSize":"fixture-size"},
        "storageProfile":{"imageReference":{"id":ids["image"]},"osDisk":{"managedDisk":{"id":ids["disk"],"storageAccountType":"Standard_LRS"}},"dataDisks":[]},
        "networkProfile":{"networkInterfaces":[{"id":ids["nic"],"properties":{"primary":True,"deleteOption":"Detach"}}]},"instanceView":{"statuses":[{"code":"PowerState/running"}]}}
    def model(id,props,**extra):return {"id":id,"properties":{"provisioningState":"Succeeded",**props},**extra}
    s.arm={ids["vm"]:model(ids["vm"],vmprops,identity={"type":"None"}),ids["image"]:model(ids["image"],{"storageProfile":{"osDisk":{"osType":"Linux","osState":"Generalized"}}}),
        ids["disk"]:model(ids["disk"],{"diskState":"Attached","encryption":{"type":"EncryptionAtRestWithPlatformKey"}},managedBy=ids["vm"]),
        ids["nic"]:model(ids["nic"],{"virtualMachine":{"id":ids["vm"]},"enableIPForwarding":False,"ipConfigurations":[{"properties":{"subnet":{"id":ids["subnet"]},"privateIPAddress":"10.0.0.4"}}]}),
        ids["subnet"]:model(ids["subnet"],{"networkSecurityGroup":{"id":ids["nsg"]},"addressPrefix":"10.0.0.0/24"}),
        ids["nsg"]:model(ids["nsg"],{"securityRules":[],"defaultSecurityRules":[]})}
    s.deployment=DeploymentSelection(ids["vm"],s.guest_expected["incarnation_id"],ids["image"],(ids["disk"],),ids["nic"],ids["subnet"],ids["nsg"],"worker",
        digest(s.arm[ids["vm"]]["identity"]),digest({k:v for k,v in s.arm[ids["vm"]]["properties"].items() if k!="instanceView"}),
        digest({"image":s.arm[ids["image"]]["properties"],"disks":[s.arm[ids["disk"]]["properties"]]}),
        digest({k:s.arm[ids[k]]["properties"] for k in ("nic","subnet","nsg")}))
    servers=[]
    def private_facts(operation):
        if operation=="stage-grant":return deepcopy(s.stage_grant)
        if operation=="stage-lease":return document(s.stage_lease_path.read_bytes())
        if operation=="plan":return document(s.plan_fact_path.read_bytes()) if hasattr(s,"plan_fact_path") else deepcopy(s.planfacts)
        if operation=="hold":return deepcopy(s.hold)
        if operation=="issuer":return deepcopy(s.issuer)
        if operation=="initialization":return deepcopy(s.initial)
        if operation=="state":
            actual=inspect_initialized_state(s.store.directory)
            with sqlite3.connect((s.store.directory/"reservations.sqlite").as_uri()+"?mode=ro",uri=True) as db:
                journal=db.execute("PRAGMA journal_mode").fetchone()[0];integrity=db.execute("PRAGMA integrity_check(1)").fetchone()[0]
            info=(s.store.directory/"reservations.sqlite").stat()
            return {"selection":deepcopy(s.state_selection),"identity":asdict(actual),"initialization_digest":digest(s.initial),"status":s.recovery,
                "private":not bool(info.st_mode&0o077),"links":info.st_nlink,"journal_mode":journal,"integrity":integrity,"schema":"owning-replay-ledger-v1"}
        if operation=="guest":
            fields=(Path("/proc")/str(s.guest_process.pid)/"stat").read_text().rsplit(")",1)[1].split()
            status={k:v for line in (Path("/proc")/str(s.guest_process.pid)/"status").read_text().splitlines() if ":" in line for k,v in [line.split(":",1)]}
            capabilities=[] if all(int(status[k],16)==0 for k in ("CapInh","CapPrm","CapEff","CapAmb")) else ["present"]
            denials={};allowed={}
            for target,op in [("imds","imds"),("resolver","resolver"),("sign","sign"),("control","control"),("policy_write","policy")]:
                parent_call(op);allowed[target]="ok";denials[target]=worker_call(op,grant_worker=s.guest_grant,outage=s.guest_outage)
            current={"host_id":s.guest_host,"incarnation_id":s.guest_incarnation,"boot_id":Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                "source_digest":byte_digest(s.guest_source.read_bytes()),"uid":int(status["Uid"].split()[0]),"policy_digest":digest(document(s.guest_policy.read_bytes())),
                "artifacts_digest":digest({"worker":byte_digest(s.guest_source.read_bytes()),"python":byte_digest(s.guest_artifact.read_bytes())})}
            return {**current,"process":{"pid":s.guest_process.pid,"start_time":int(fields[19]),"uid":int(status["Uid"].split()[0]),"capabilities":capabilities},
                "denials":denials,"positive_controls":allowed}
        raise ValueError
    s.private_facts=private_facts
    def public(path):
        u=urlsplit(path)
        if u.path==GITHUB+"/git/ref/heads/main":return {"ref":"refs/heads/main","object":{"type":"commit","sha":s.main_sha}}
        if u.path.startswith(GITHUB+"/contents/"):return deepcopy(s.contents[u.path.split("/contents/",1)[1]])
        if u.path==GITHUB+"/environments/"+s.environment["name"]:return deepcopy(s.environment)
        if u.path.endswith("/deployment-branch-policies"):return deepcopy(s.policies)
        if u.path==GITHUB+"/rulesets":return deepcopy(s.rulesets)
        if u.path==GITHUB+"/rulesets/42":return deepcopy(s.rule)
        if u.path.startswith("/keys/"):return deepcopy(s.keydata)
        if u.path in s.arm:return deepcopy(s.arm[u.path])
        if hasattr(s,"g"):
            if "/jobs" in u.path:
                page=int(u.query.rsplit("=",1)[1]);return {"total_count":len(s.g.jobs),"jobs":deepcopy(s.g.jobs[(page-1)*100:page*100])}
            if u.path.endswith("/approvals"):return deepcopy(s.g.reviews)
            if "/actions/runs/" in u.path:return deepcopy(s.g.run)
        raise KeyError
    def serve(label):
        root=tmp_path/label;ca,server,gate,worker=make_pki(root)
        principal="principal:initialization-source" if label=="initialization" else "principal:readback-source"
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_GET(self):self.handle_read()
            def do_POST(self):self.handle_read()
            def handle_read(self):
                try:
                    peer=hashlib.sha256(self.connection.getpeercert(binary_form=True)).hexdigest()
                    if peer!=gate[2]:self.reply(403,{"error":"denied"});return
                    s.calls.append((self.command,self.path))
                    if s.hook:s.hook(self.command,self.path)
                    if self.command=="POST":
                        if self.path!="/readback":raise ValueError
                        length=int(self.headers.get("Content-Length","0"))
                        if not 0<length<=65536:raise ValueError
                        import json
                        request=json.loads(self.rfile.read(length))
                        if set(request)!={"profile","operation","reference","nonce"} or request["profile"]!=PROFILE:raise ValueError
                        facts=private_facts(request["operation"])
                        value={**request,"principal_ref":principal,"scope":s.scope.record(),"facts":facts,"observed_at":s.now,"expires_at":s.now+30}
                        if s.private_mutate:s.private_mutate(value)
                    else:
                        if self.headers.get("Authorization")!="Bearer fixture-reader":self.reply(403,{"error":"denied"});return
                        value=public(self.path)
                        if s.mutate:s.mutate(self.path,value)
                    self.reply(200,value)
                except Exception:self.reply(503,{"error":"observation-unavailable"})
            def reply(self,status,value):
                raw=canonical(value);self.send_response(status);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
        http=ThreadingHTTPServer(("127.0.0.1",0),Handler);ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(str(server[0]),str(server[1]));ctx.load_verify_locations(cafile=str(ca));ctx.verify_mode=ssl.CERT_REQUIRED
        http.socket=ctx.wrap_socket(http.socket,server_side=True);thread=Thread(target=lambda:http.serve_forever(poll_interval=.02),daemon=True);thread.start();servers.append((http,thread))
        def stop_server():
            if thread.is_alive():http.shutdown()
            http.server_close();thread.join(timeout=5);assert not thread.is_alive()
        request.addfinalizer(stop_server)
        origin="https://127.0.0.1:"+str(http.server_port)
        pin=byte_digest(x509.load_pem_x509_certificate(server[0].read_bytes()).public_bytes(serialization.Encoding.DER))
        return SimpleNamespace(origin=origin,ca=ca,gate=gate,worker=worker,pin=pin,principal=principal)
    s.primary=serve("provider");s.secondary=serve("initialization")
    def transport(endpoint=None,*,observation=False,peer="gate",pin=None):
        selected=endpoint or s.primary;material=getattr(selected,peer)
        options={"observation_origin":selected.origin,"server_certificate_digest":pin or selected.pin} if observation else {"fixture_origin":selected.origin}
        return PrivateHttps(ca_file=str(selected.ca),certificate=str(material[0]),private_key=str(material[1]),**options)
    s.transport=transport
    class Routed:
        def exchange(self,method,url,**kwargs):
            u=urlsplit(url)
            if u.netloc not in ("api.github.com","management.azure.com","fixture-vault.vault.azure.net"):raise BindingError("fixture-route-refused")
            return transport().exchange(method,s.primary.origin+u.path+("?"+u.query if u.query else ""),**kwargs)
    s.reader=RequestReader(credential=lambda **_:"fixture-reader",transport=Routed());s.routed=Routed
    s.github=lambda:GithubReadbacks(reader=s.reader,principal_ref=s.primary.principal,repository_id="123")
    def client(endpoint=None,*,peer="gate",pin=None):
        selected=endpoint or s.primary
        return ObservationClient(origin=selected.origin,principal_ref=selected.principal,scope=s.scope,transport=transport(selected,observation=True,peer=peer,pin=pin))
    s.client=client
    s.deployment_reader=lambda:DeploymentReader(selection=s.deployment,reader=s.reader,principal_ref="principal:arm-reader")
    s.issuer_reader=lambda:IssuerReader(client=client(),reader=s.reader,**{k:v for k,v in s.issuer_expected.items() if k!="permissions"})
    s.guest_reader=lambda:GuestReader(client=client(),expected=s.guest_expected)
    s.state_reader=lambda:StateReader(current=client(),initialization=client(s.secondary),selection=s.state_selection)
    try:yield s
    finally:
        for server,thread in servers:server.shutdown();server.server_close();thread.join(timeout=5);assert not thread.is_alive()
        if s.process.poll() is None:s.process.terminate()
        try:s.process.communicate(timeout=3)
        except subprocess.TimeoutExpired:s.process.kill();s.process.communicate()
        assert s.process.poll() is not None
