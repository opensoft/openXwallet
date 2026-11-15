"""T012P provider protocol controls; all endpoints are isolated fixture TLS."""
from dataclasses import replace
from datetime import datetime, timezone
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import ssl
from threading import Thread
import time
from types import SimpleNamespace

import pytest
from .hosted_fixture import child_generations
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from workload_factory_binding.evidence import BindingError, canonical, digest, encode64, decode64
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.nonces import NonceLedger, ERROR
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps, Response
from workload_factory_binding_runtime.hosted.issuance import AppSelection, IssuanceCurrent, InstallationIssuer, InstallationRetirer
from factory_binding.test_owner_integration import make_pki


def decision(state):
    return Decision(clock=lambda: state.now, monotonic=lambda: state.mono)


@pytest.fixture
def provider(tmp_path):
    ca, server, gate, worker = make_pki(tmp_path / "pki")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    s = SimpleNamespace(now=int(time.time()), mono=0., key=key, active={}, calls=[], changes={}, ca=ca,
        gate=gate, worker=worker, api_requests=0)
    s.install_permissions={"actions":"write","metadata":"read"};s.token_permissions=dict(s.install_permissions)
    s.selection = AppSelection("Iv1.fixture", 77, 88, 11, 22, "broker",
        "https://fixture-vault.vault.azure.net/keys/app-key/" + "a" * 32, key.public_key(), digest({"enrollment":"provider-fixture-approved"}))
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args): pass
        def do_GET(self): self.handle_request()
        def do_POST(self): self.handle_request()
        def do_DELETE(self): self.handle_request()
        def handle_request(self):
            peer = hashlib.sha256(self.connection.getpeercert(binary_form=True)).hexdigest()
            if peer != gate[2]:
                self.reply(403, {"error": "denied"}); return
            n = int(self.headers.get("Content-Length", "0")); raw = self.rfile.read(n) if n else b""
            value = json.loads(raw) if raw else None
            s.calls.append((self.command, self.path))
            if self.path.startswith("/keys/"):
                assert self.headers["Authorization"] == "Bearer fixture-vault-credential"
                assert value["alg"] == "RS256"
                signature = key.sign(decode64(value["value"]), padding.PKCS1v15(), utils.Prehashed(hashes.SHA256()))
                if s.changes.get("signature"): signature = b"x" * 256
                kid = s.selection.key_uri + ("-wrong" if s.changes.get("key-version") else "")
                self.reply(200, {"kid": kid, "value": encode64(signature)}); return
            s.api_requests += 1
            auth = self.headers.get("Authorization", "").removeprefix("Bearer ")
            if self.path in ("/app", "/app/installations/88", "/app/installations/88/access_tokens"):
                a,b,c = auth.split(".")
                key.public_key().verify(decode64(c), (a+"."+b).encode(), padding.PKCS1v15(), hashes.SHA256())
                claims = json.loads(decode64(b)); assert claims["iss"] == "Iv1.fixture"
                assert claims["iat"] == s.now - 60
                assert s.now < claims["exp"] <= s.now + 600
            if self.path == "/app": self.reply(200, {"id": 78 if s.changes.get("app") else 77, "client_id": "Iv1.fixture"})
            elif self.path == "/app/installations/88":
                self.reply(200, {"id": 89 if s.changes.get("installation") else 88, "app_id": 77,
                    "account": {"id": 22, "login": "opensoft"}, "repository_selection": "selected",
                    "suspended_at": None, "permissions": dict(s.install_permissions)})
            elif self.path == "/app/installations/88/access_tokens":
                assert value == {"repository_ids": [11], "permissions": s.install_permissions}
                token = "fixture-token-" + secrets.token_hex(16); s.active[token] = True
                permissions = dict(s.token_permissions)
                if s.changes.get("permissions"): permissions["contents"] = "write"
                expiry = s.now if s.changes.get("expired") else s.now + (7200 if s.changes.get("expiry") else 3600)
                self.reply(201, {"token": token, "permissions": permissions, "repository_selection": "selected",
                    "expires_at": datetime.fromtimestamp(expiry, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
            elif self.path == "/installation/repositories?per_page=2&page=1":
                if not s.active.get(auth): self.reply(401, {"error": "bad credentials"})
                else: self.reply(200, {"total_count": 2 if s.changes.get("repository") else 1,
                    "repositories": [{"id": 12 if s.changes.get("repo-id") else 11, "full_name": "opensoft/openXwallet"}]})
            elif self.path == "/installation/token":
                if not s.changes.get("still-active"): s.active[auth] = False
                self.reply(503 if s.changes.get("retirement-outage") else 204, None)
            elif self.path == "/fixture/empty": self.reply(204,None)
            else: self.reply(404,{"error":"not found"})
        def reply(self,status,value):
            raw = canonical(value) if value is not None else b""
            self.send_response(status); self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    server_instance=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(server[0]),str(server[1]));ctx.load_verify_locations(cafile=str(ca));ctx.verify_mode=ssl.CERT_REQUIRED
    server_instance.socket=ctx.wrap_socket(server_instance.socket,server_side=True)
    thread=Thread(target=server_instance.serve_forever,daemon=True);thread.start()
    s.endpoint="https://127.0.0.1:"+str(server_instance.server_port)
    def transport(peer=gate): return PrivateHttps(ca_file=str(ca),certificate=str(peer[0]),private_key=str(peer[1]))
    s.transport=transport
    class Routed:
        def __init__(self): self.http=transport()
        def exchange(self,method,url,**kwargs):
            assert url.startswith(("https://api.github.com/", "https://fixture-vault.vault.azure.net/"))
            from urllib.parse import urlsplit
            u=urlsplit(url);return self.http.exchange(method,s.endpoint+u.path+("?"+u.query if u.query else ""),**kwargs)
    s.routed=Routed
    s.nonce=secrets.token_hex(32);s.ref="issuance:fixture"
    s.current=None
    def issuer():
        identity=NonceLedger.initialize(tmp_path/"issuance-state")
        ledger=NonceLedger(tmp_path/"issuance-state",identity=identity)
        def current(ref,*,deadline):
            return s.current if s.current is not None else IssuanceCurrent("principal:issuer-approval", issue.selection_digest,
                s.ref,s.nonce,True,s.now,s.now+30)
        issue=InstallationIssuer(selection=s.selection,ledger=ledger,transport=Routed(),
            vault_credential=lambda **_: "fixture-vault-credential", read_current=current,current_principal="principal:issuer-approval")
        s.ledger=ledger;return issue
    s.issuer=issuer
    try: yield s
    finally:
        server_instance.shutdown();server_instance.server_close();thread.join(timeout=5);assert not thread.is_alive()


def test_actual_mutual_tls_positive_and_empty_retirement_response(provider):
    s=provider
    result=s.transport().exchange("DELETE",s.endpoint+"/fixture/empty",headers={},decision=decision(s))
    assert result.status==204
    assert result.body==b""


def test_valid_worker_tls_certificate_is_explicitly_denied(provider):
    s=provider
    response=s.transport(s.worker).exchange("DELETE",s.endpoint+"/fixture/empty",headers={},decision=decision(s))
    assert response.status==403
    assert json.loads(response.body)=={"error":"denied"}


def test_nonce_store_requires_explicit_initialization_and_persists_consumption(tmp_path):
    s=SimpleNamespace(now=1000,mono=0.)
    with pytest.raises(BindingError): NonceLedger(tmp_path/"missing",identity=(0,0,0,0))
    identity=NonceLedger.initialize(tmp_path/"nonces")
    ledger=NonceLedger(tmp_path/"nonces",identity=identity)
    ledger.reserve("issue:one","1"*64,digest({"request":1}),decision=decision(s))
    reopened=NonceLedger(tmp_path/"nonces",identity=identity)
    with pytest.raises(BindingError): reopened.reserve("issue:one","2"*64,digest({"request":2}),decision=decision(s))
    with pytest.raises(BindingError): reopened.reserve("issue:two","1"*64,digest({"request":2}),decision=decision(s))
    assert reopened.state("issue:one",decision=decision(s))["state"]=="consumed"


def test_real_rsa_app_jwt_exact_installation_and_returned_scope(provider):
    s=provider;issue=s.issuer();cap=issue.issue(s.ref,s.nonce,decision=decision(s))
    assert cap.role=="broker"
    assert cap.expires_at==s.now+3600
    assert cap.use_until<=s.now+10
    assert cap.readback()["token_digest"]=="sha256:"+hashlib.sha256(cap.credential.encode()).hexdigest()
    assert "fixture-token" not in repr(cap)
    assert "credential" not in cap.readback()
    assert len(s.active)==1
    assert s.ledger.state(s.ref,decision=decision(s))["state"]=="issued"
    with pytest.raises(BindingError):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert len(s.active)==1


@pytest.mark.parametrize("change",["signature","key-version","app","installation","permissions","expired","expiry","repository","repo-id"])
def test_independent_provider_mutations_refuse_without_widening_scope(provider,change):
    s=provider;s.changes[change]=True;issue=s.issuer()
    with pytest.raises(BindingError,match="^"+ERROR+"$"):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert s.ledger.state(s.ref,decision=decision(s))["state"]!="issued"
    if change in ("signature","key-version"):assert s.api_requests==0


@pytest.mark.parametrize("change",["revoked","nonce","principal","selection","late"])
def test_current_approval_is_independent_of_request(provider,change):
    s=provider;issue=s.issuer()
    value=IssuanceCurrent("principal:issuer-approval",issue.selection_digest,s.ref,s.nonce,True,s.now,s.now+30)
    if change=="revoked":value=replace(value,active=False)
    elif change=="nonce":value=replace(value,nonce="f"*64)
    elif change=="principal":value=replace(value,principal_ref="principal:worker")
    elif change=="selection":value=replace(value,selection_digest=digest({"wrong":True}))
    else:value=replace(value,expires_at=s.now)
    s.current=value
    with pytest.raises(BindingError):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert s.calls==[]


def test_separate_retirement_observer_requires_actual_token_refusal(provider):
    s=provider;issue=s.issuer();cap=issue.issue(s.ref,s.nonce,decision=decision(s))
    retired=InstallationRetirer(writer=s.routed(),observer=s.routed()).retire(cap,decision=decision(s))
    assert retired["state"]=="retired"
    assert not s.active[cap.credential]
    assert s.ledger.state(s.ref,decision=decision(s))["state"]=="retired"
    assert "fixture-token" not in json.dumps(retired)


@pytest.mark.parametrize("change",["still-active","retirement-outage"])
def test_retirement_uncertainty_never_counts_as_cleanup(provider,change):
    s=provider;cap=s.issuer().issue(s.ref,s.nonce,decision=decision(s));s.changes[change]=True
    with pytest.raises(BindingError):InstallationRetirer(writer=s.routed(),observer=s.routed()).retire(cap,decision=decision(s))
    assert s.ledger.state(s.ref,decision=decision(s))["state"]!="retired"


def test_reader_cannot_request_broker_actions_write(provider):
    s=provider;s.selection=replace(s.selection,role="reader");issue=s.issuer()
    with pytest.raises(BindingError):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert not s.active



def test_lost_issuance_response_is_consumed_and_never_minted_again(provider):
    s=provider;issue=s.issuer();original=issue.transport
    class Lost:
        def exchange(self,method,url,**kwargs):
            response=original.exchange(method,url,**kwargs)
            if url.endswith("/access_tokens"):raise TimeoutError("private-issuance-canary")
            return response
    issue.transport=Lost()
    with pytest.raises(BindingError,match="^"+ERROR+"$"):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert len(s.active)==1
    assert s.ledger.state(s.ref,decision=decision(s))["state"]=="consumed"
    with pytest.raises(BindingError):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert len(s.active)==1


def test_lost_retirement_response_reconciles_read_only_without_second_delete(provider):
    s=provider;cap=s.issuer().issue(s.ref,s.nonce,decision=decision(s));original=s.routed()
    class Lost:
        def exchange(self,method,url,**kwargs):
            response=original.exchange(method,url,**kwargs)
            if method=="DELETE":raise TimeoutError("private-retirement-canary")
            return response
    retire=InstallationRetirer(writer=Lost(),observer=s.routed())
    with pytest.raises(BindingError):retire.retire(cap,decision=decision(s))
    with pytest.raises(BindingError):retire.retire(cap,decision=decision(s))
    assert s.ledger.state(s.ref,decision=decision(s))["state"]=="retiring"
    assert retire.reconcile(cap,decision=decision(s))["state"]=="retired"
    assert sum(method=="DELETE" for method,path in s.calls)==1


@pytest.mark.parametrize("which",["ca_file","certificate","private_key"])
def test_private_transport_material_is_checked_before_contact(provider,which,tmp_path):
    s=provider;bad=tmp_path/"missing"
    options={"ca_file":str(s.ca),"certificate":str(s.gate[0]),"private_key":str(s.gate[1]),which:str(bad)}
    with pytest.raises(BindingError):PrivateHttps(**options).exchange("GET",s.endpoint+"/app",headers={},decision=decision(s))
    assert s.calls==[]


@pytest.mark.parametrize("change",["expired","monotonic","revoked"])
def test_late_approval_change_before_provider_send_refuses(provider,change):
    s=provider;issue=s.issuer();original=issue.vault_credential
    def credential(**kwargs):
        value=original(**kwargs)
        if change=="expired":s.now+=11
        elif change=="monotonic":s.mono+=11
        else:s.current=IssuanceCurrent("principal:issuer-approval",issue.selection_digest,s.ref,s.nonce,False,s.now,s.now+30)
        return value
    issue.vault_credential=credential
    with pytest.raises(BindingError):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert s.calls==[]



def test_kernel_credential_capability_feeds_real_fixed_provider_flow(provider):
    from workload_factory_binding_runtime.hosted.credential import CredentialBroker,KernelPrincipal,credential_channels
    s=provider;issue=s.issuer();parent=decision(s);resolutions=[]
    def resolve(**_):resolutions.append(True);return b"fixture-vault-credential"
    service=CredentialBroker(principals=(KernelPrincipal.current("issuer"),),capabilities={"resolver":(("issuer",),resolve)})
    def credential(*,deadline):
        assert deadline<=parent.deadline
        server,client=credential_channels();thread=Thread(target=lambda:service.serve_once(server,decision=parent));thread.start()
        try:
            client.send(canonical({"role":"issuer","operation":"resolver"}));client.settimeout(3)
            response=json.loads(client.recv(65537));assert response["status"]=="ok"
            return base64.b64decode(response["value"]).decode()
        finally:server.close();client.close();thread.join(timeout=5);assert not thread.is_alive()
    issue.vault_credential=credential
    cap=issue.issue(s.ref,s.nonce,decision=parent)
    assert s.active[cap.credential]
    assert resolutions==[True]


@pytest.mark.parametrize("change",["clock","identity","permissions","symlink","hardlink","missing"])
def test_nonce_store_corruption_or_replacement_never_resets_consumption(tmp_path,change):
    s=SimpleNamespace(now=1000,mono=0.);root=tmp_path/"state";identity=NonceLedger.initialize(root);ledger=NonceLedger(root,identity=identity)
    ledger.reserve("issuance:one","1"*64,digest({"one":True}),decision=decision(s))
    database=root/"issuance.sqlite"
    if change=="clock":s.now-=1
    elif change=="identity":
        raw=database.read_bytes();database.rename(root/"retained.sqlite");database.write_bytes(raw);database.chmod(0o600)
    elif change=="permissions":database.chmod(0o644)
    elif change=="symlink":database.rename(root/"retained.sqlite");database.symlink_to(root/"retained.sqlite")
    elif change=="hardlink":os.link(database,root/"extra-link")
    else:database.rename(root/"retained.sqlite")
    with pytest.raises(BindingError):ledger.state("issuance:one",decision=decision(s))
    if change in ("identity","symlink","missing"):assert (root/"retained.sqlite").exists()
    else:assert database.exists()


def test_concurrent_nonce_reservations_have_one_durable_winner(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    root=tmp_path/"state";identity=NonceLedger.initialize(root)
    def reserve(index):
        s=SimpleNamespace(now=1000,mono=0.)
        try:NonceLedger(root,identity=identity).reserve("issuance:one","1"*64,digest({"index":index}),decision=decision(s));return True
        except BindingError:return False
    with ThreadPoolExecutor(max_workers=4) as pool:outcomes=list(pool.map(reserve,range(4)))
    assert outcomes.count(True)==1
    assert NonceLedger(root,identity=identity).state("issuance:one",decision=decision(SimpleNamespace(now=1000,mono=0.)))["state"]=="consumed"



@pytest.mark.parametrize("change",["wall-expiry","monotonic-expiry","revoked","retired"])
def test_issued_credential_use_does_not_renew_earlier_authority(provider,change):
    s=provider;issue=s.issuer();cap=issue.issue(s.ref,s.nonce,decision=decision(s))
    assert issue.resolve(s.ref,s.nonce,decision=decision(s))==cap.credential
    if change=="wall-expiry":s.now+=11
    elif change=="monotonic-expiry":s.mono+=11
    elif change=="revoked":s.current=IssuanceCurrent("principal:issuer-approval",issue.selection_digest,s.ref,s.nonce,False,s.now,s.now+30)
    else:InstallationRetirer(writer=s.routed(),observer=s.routed()).retire(cap,decision=decision(s))
    with pytest.raises(BindingError):issue.resolve(s.ref,s.nonce,decision=decision(s))



def test_fresh_caller_clock_cannot_hide_original_issuance_clock_regression(provider):
    s=provider;issue=s.issuer();cap=issue.issue(s.ref,s.nonce,decision=decision(s));s.mono=-1
    caller=Decision(clock=lambda:s.now,monotonic=lambda:0.)
    with pytest.raises(BindingError):issue.resolve(s.ref,s.nonce,decision=caller)



@pytest.mark.parametrize("role,expected",[("reader",{"actions":"read","metadata":"read"}),
    ("source-reader",{"actions":"read","metadata":"read","contents":"read"})])
def test_real_reader_roles_receive_only_their_exact_permissions(provider,role,expected):
    s=provider;s.selection=replace(s.selection,role=role);s.install_permissions=dict(expected);s.token_permissions=dict(expected)
    issue=s.issuer();cap=issue.issue(s.ref,s.nonce,decision=decision(s))
    assert cap.role==role
    assert issue.resolve(s.ref,s.nonce,decision=decision(s))==cap.credential


def test_reader_returned_write_scope_is_refused_and_privately_retired(provider):
    s=provider;s.selection=replace(s.selection,role="reader");s.install_permissions={"actions":"read","metadata":"read"}
    issue=s.issuer()
    with pytest.raises(BindingError):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert len(s.active)==1
    cap=issue.pending(s.ref);assert cap.expires_at is None
    with pytest.raises(BindingError):issue.resolve(s.ref,s.nonce,decision=decision(s))
    assert InstallationRetirer(writer=s.routed(),observer=s.routed()).retire(cap,decision=decision(s))["state"]=="retired"


@pytest.mark.parametrize("change",["revoked","expired"])
def test_returned_token_is_retained_for_cleanup_when_authority_changes_after_mint(provider,change):
    s=provider;issue=s.issuer();original=issue.transport
    class ChangeAfterMint:
        def exchange(self,method,url,**kwargs):
            result=original.exchange(method,url,**kwargs)
            if url.endswith("/access_tokens"):
                if change=="revoked":s.current=IssuanceCurrent("principal:issuer-approval",issue.selection_digest,s.ref,s.nonce,False,s.now,s.now+30)
                else:s.now+=11
            return result
    issue.transport=ChangeAfterMint()
    with pytest.raises(BindingError):issue.issue(s.ref,s.nonce,decision=decision(s))
    cap=issue.pending(s.ref)
    assert cap.expires_at is None
    assert InstallationRetirer(writer=s.routed(),observer=s.routed()).retire(cap,decision=decision(s))["state"]=="retired"
    assert len(s.active)==1



def test_role_configuration_change_cannot_reuse_the_old_approval(provider):
    s=provider;issue=s.issuer();issue.selection=replace(issue.selection,role="reader")
    with pytest.raises(BindingError):issue.issue(s.ref,s.nonce,decision=decision(s))
    assert s.calls==[]
