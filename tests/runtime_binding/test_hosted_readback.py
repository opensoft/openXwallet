"""T012Q independent current facts, fixed scopes and non-renewing read budgets."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from workload_factory_binding.evidence import BindingError,canonical,digest
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.readback import ReadBudget,ReadScope,ObservationClient
from workload_factory_binding_runtime.hosted.github_readback import GithubReadbacks,ProtectedReadbacks
from workload_factory_binding_runtime.hosted.platform_readback import DeploymentSelection,DeploymentReader,IssuerReader,GuestReader,StateReader
from .hosted_fixture import child_generations
from .readback_fixture import rb,ROOT,GITHUB
from copy import deepcopy
from pathlib import Path
import os
import sqlite3
from workload_factory_binding_runtime.github_bootstrap.graph import GraphSource
from workload_factory_binding_runtime.hosted.readback import ERROR,Snapshot
from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
from workload_factory_binding_runtime.state import inspect_initialized_state


def clock():return SimpleNamespace(now=1000,mono=0.)
def decision(s):return Decision(clock=lambda:s.now,monotonic=lambda:s.mono)


@pytest.mark.parametrize("group,limit",[("protection",3),("source",4),("control",2)])
def test_read_groups_share_one_deadline_and_cannot_reset_by_new_client(group,limit):
    s=clock();use=decision(s)
    for _ in range(limit):ReadBudget(use).consume(group)
    consume_target = ReadBudget(use)
    with pytest.raises(BindingError):consume_target.consume(group)
    assert use.api_requests==0


def test_correlation_budget_is_included_in_the_thirteen_request_ceiling():
    s=clock();use=decision(s);use.api_requests=4
    for group,limit in [("protection",3),("source",4),("control",2)]:
        for _ in range(limit):ReadBudget(use).consume(group)
    assert ReadBudget(use).github_requests==13
    consume_target = ReadBudget(use)
    with pytest.raises(BindingError):consume_target.consume("source")


@pytest.mark.parametrize("change",["wall","monotonic","regression"])
def test_shared_decision_expiry_or_regression_refuses_before_new_read(change):
    s=clock();use=decision(s);ReadBudget(use).consume("source")
    if change=="wall":s.now+=10
    elif change=="monotonic":s.mono+=10
    else:s.now-=1
    # An invalid original decision must be refused before a new read client exists.
    with pytest.raises(BindingError):ReadBudget(use)



def test_actual_tls_current_source_protection_control_and_snapshot_copy(rb):
    use=rb.use();github=rb.github();source=github.source(rb.main_sha,decision=use)
    environment=github.environment("qa",decision=use)
    identifier=github.begin_control(42,decision=use);control=github.finish_control(identifier,decision=use)
    assert type(source.graph) is GraphSource
    assert source.graph.caller==(ROOT/".github/workflows/protected-runtime-qualification.yml").read_bytes()
    assert environment.protection["deployment_refs"]==["refs/heads/main"]
    assert control.digest==digest(rb.rule)
    copy=control.data();copy["enforcement"]="disabled"
    assert control.data()["enforcement"]=="active"
    assert ReadBudget(use).github_requests==8
    assert all(method=="GET" for method,path in rb.calls)


@pytest.mark.parametrize("change",["missing-bypass","bypass","self-review","reviewer","reviewer-type","duplicate-reviewer","unknown-rule","missing-branch-type","tag","wildcard","extra-policy","missing-policy","policy-count","protected-all","environment-id"])
def test_each_current_protection_mutation_refuses_independently(rb,change):
    if change=="missing-bypass":rb.environment.pop("can_admins_bypass")
    elif change=="bypass":rb.environment["can_admins_bypass"]=True
    elif change=="self-review":rb.environment["protection_rules"][0]["prevent_self_review"]=False
    elif change=="reviewer":rb.environment["protection_rules"][0]["reviewers"]=[]
    elif change=="reviewer-type":rb.environment["protection_rules"][0]["reviewers"][0]["type"]="Bot"
    elif change=="duplicate-reviewer":rb.environment["protection_rules"][0]["reviewers"]*=2
    elif change=="unknown-rule":rb.environment["protection_rules"].append({"type":"unrecognized"})
    elif change=="missing-branch-type":rb.policies["branch_policies"][0].pop("type")
    elif change=="tag":rb.policies["branch_policies"][0]["type"]="tag"
    elif change=="wildcard":rb.policies["branch_policies"][0]["name"]="*"
    elif change=="extra-policy":rb.policies["branch_policies"].append({"id":12,"name":"dev","type":"branch"});rb.policies["total_count"]=2
    elif change=="missing-policy":rb.policies["branch_policies"]=[]
    elif change=="policy-count":rb.policies["total_count"]=33
    elif change=="protected-all":rb.environment["deployment_branch_policy"]={"protected_branches":True,"custom_branch_policies":False}
    else:rb.environment["id"]=True
    github=rb.github();use=rb.use()
    with pytest.raises(BindingError):github.environment("qa",decision=use)
    assert ReadBudget(use).count("protection")<=3


@pytest.mark.parametrize("change",["main-sha","main-ref","main-type","blob-hash","blob-path","blob-size","blob-encoding","blob-target","last-main"])
def test_source_uses_fixed_commit_bytes_and_rechecks_current_main(rb,change):
    original_calls=[]
    def mutate(path,value):
        if "/git/ref/" in path:
            original_calls.append(True)
            if change=="main-sha" or change=="last-main" and len(original_calls)==2:value["object"]["sha"]="b"*40
            elif change=="main-ref":value["ref"]="refs/tags/main"
            elif change=="main-type":value["object"]["type"]="tag"
        elif "/contents/" in path:
            if change=="blob-hash":value["sha"]="b"*40
            elif change=="blob-path":value["path"]="worker.yml"
            elif change=="blob-size":value["size"]+=1
            elif change=="blob-encoding":value["encoding"]="none"
            elif change=="blob-target":value["target"]="unselected"
    rb.mutate=mutate;github=rb.github();use=rb.use()
    with pytest.raises(BindingError):github.source(rb.main_sha,decision=use)
    assert all("forbidden.invalid" not in path for _,path in rb.calls)
    assert ReadBudget(use).count("source")<=4


def test_source_observation_cannot_move_to_a_fresh_budget(rb):
    github=rb.github();use=rb.use();value=github.begin_source(rb.main_sha,decision=use);fresh=rb.use()
    with pytest.raises(BindingError):github.finish_source(value,decision=fresh)
    assert ReadBudget(use).count("source")==3
    assert ReadBudget(fresh).count("source")==0


@pytest.mark.parametrize("change",["extra-set","wrong-set","tag","include","exclude","bypass","rule","merge-permission","inactive","missing-rules"])
def test_current_source_update_controls_are_complete_and_bounded(rb,change):
    if change=="extra-set":rb.rulesets*=2
    elif change=="wrong-set":rb.rulesets[0]["id"]=43
    elif change=="tag":rb.rule["target"]="tag"
    elif change=="include":rb.rule["conditions"]["ref_name"]["include"]=["~ALL"]
    elif change=="exclude":rb.rule["conditions"]["ref_name"]["exclude"]=["refs/heads/main"]
    elif change=="bypass":rb.rule["bypass_actors"]=[{"actor_id":1,"actor_type":"Integration","bypass_mode":"exempt"}]
    elif change=="rule":rb.rule["rules"].append({"type":"unsupported"})
    elif change=="merge-permission":rb.rule["rules"][0]["parameters"]["update_allows_fetch_and_merge"]=True
    elif change=="inactive":rb.rule["enforcement"]="disabled"
    else:rb.rule.pop("rules")
    github=rb.github();use=rb.use()
    if change in ("extra-set", "wrong-set"):
        with pytest.raises(BindingError):
            github.begin_control(42,decision=use)
    else:
        identifier=github.begin_control(42,decision=use)
        with pytest.raises(BindingError):
            github.finish_control(identifier,decision=use)
    assert ReadBudget(use).count("control")<=2


def test_pinned_mtls_source_authenticates_allowed_and_explicitly_denies_worker(rb):
    use=rb.use();client=rb.client();result=client.read("hold","hold:fixture",decision=use)
    assert result.data()["owner_ref"]=="principal:hold-owner"
    worker=rb.client(peer="worker");use=rb.use()
    with pytest.raises(BindingError,match="^"+ERROR+"$"):worker.read("hold","hold:fixture",decision=use)
    assert rb.calls[-1][0]=="POST"


def test_wrong_observer_certificate_pin_refuses_before_application_data(rb):
    client=rb.client(pin="sha256:"+"f"*64);use=rb.use()
    with pytest.raises(BindingError,match="^"+ERROR+"$"):client.read("hold","hold:fixture",decision=use)
    assert rb.calls==[]


@pytest.mark.parametrize("change",["nonce","principal","case","plan","source","run","attempt","future","stale","overlong","extra","operation","reference"])
def test_authenticated_observation_still_requires_current_exact_scope(rb,change):
    def mutate(value):
        if change=="nonce":value["nonce"]="f"*64
        elif change=="principal":value["principal_ref"]="principal:worker"
        elif change in ("case","plan","source","run","attempt"):
            key={"case":"case_ref","plan":"plan_digest","source":"source_commit","run":"run_id","attempt":"run_attempt"}[change]
            value["scope"][key]="changed"
        elif change=="future":value["observed_at"]+=1
        elif change=="stale":value["observed_at"]-=61
        elif change=="overlong":value["expires_at"]+=61
        elif change=="extra":value["raw_token"]="private-response-canary"
        elif change=="operation":value["operation"]="control"
        else:value["reference"]="hold:other"
    rb.private_mutate=mutate;client=rb.client();use=rb.use()
    with pytest.raises(BindingError,match="^"+ERROR+"$") as caught:client.read("hold","hold:fixture",decision=use)
    assert "private" not in str(caught.value)


def test_current_snapshot_retains_original_monotonic_expiry(rb):
    use=rb.use();value=rb.client().read("hold","hold:fixture",decision=use)
    rb.mono+=10
    with pytest.raises(BindingError):value.data()


def test_observer_material_cannot_change_under_the_old_selection(rb):
    client=rb.client();client.transport.server_certificate_digest="sha256:"+"f"*64;use=rb.use()
    with pytest.raises(BindingError):client.read("hold","hold:fixture",decision=use)
    assert rb.calls==[]


def test_arm_reads_actual_linked_model_image_disk_nic_subnet_and_network(rb):
    use=rb.use();value=rb.deployment_reader().read(decision=use).data()
    assert value["vm_id"]==rb.ids["vm"]
    assert value["identity"]=={"type":"None"}
    assert ReadBudget(use).count("arm")==6
    assert len(rb.calls)==6
    assert all(method=="GET" and "runCommand" not in path for method,path in rb.calls)


@pytest.mark.parametrize("change",["vmid","assigned-worker-identity","wrong-image","wrong-disk","wrong-nic","wrong-subnet","ip-forwarding","network-rule","disk-owner","disk-detached","public-ip","not-running","provisioning","unknown-page"])
def test_each_independent_arm_observation_differs_from_the_fixed_candidate(rb,change):
    frozen=rb.deployment
    vm=rb.arm[rb.ids["vm"]];nic=rb.arm[rb.ids["nic"]]["properties"]
    if change=="vmid":vm["properties"]["vmId"]="33333333-3333-4333-8333-333333333333"
    elif change=="assigned-worker-identity":vm["identity"]={"type":"SystemAssigned","principalId":"unselected"}
    elif change=="wrong-image":vm["properties"]["storageProfile"]["imageReference"]["id"]=rb.ids["image"]+"other"
    elif change=="wrong-disk":vm["properties"]["storageProfile"]["osDisk"]["managedDisk"]["id"]=rb.ids["disk"]+"other"
    elif change=="wrong-nic":vm["properties"]["networkProfile"]["networkInterfaces"][0]["id"]=rb.ids["nic"]+"other"
    elif change=="wrong-subnet":nic["ipConfigurations"][0]["properties"]["subnet"]["id"]=rb.ids["subnet"]+"other"
    elif change=="ip-forwarding":nic["enableIPForwarding"]=True
    elif change=="network-rule":rb.arm[rb.ids["nsg"]]["properties"]["securityRules"].append({"access":"Allow","sourceAddressPrefix":"*"})
    elif change=="disk-owner":rb.arm[rb.ids["disk"]]["managedBy"]=rb.ids["vm"]+"other"
    elif change=="disk-detached":rb.arm[rb.ids["disk"]]["properties"]["diskState"]="Unattached"
    elif change=="public-ip":nic["ipConfigurations"][0]["properties"]["publicIPAddress"]={"id":"unselected"}
    elif change=="not-running":vm["properties"]["instanceView"]["statuses"]=[{"code":"PowerState/stopped"}]
    elif change=="provisioning":vm["properties"]["provisioningState"]="Failed"
    else:vm["nextLink"]="https://forbidden.invalid"
    reader=rb.deployment_reader();use=rb.use()
    with pytest.raises(BindingError):reader.read(decision=use)
    assert rb.deployment is frozen
    assert ReadBudget(use).count("arm")<=6


def test_exact_version_public_rsa_and_current_private_issuance_agree(rb):
    use=rb.use();value=rb.issuer_reader().read("issuance:fixture",decision=use)
    assert value.data()["public_key_digest"]==rb.issuer_expected["public_key_digest"]
    assert ReadBudget(use).count("key")==1
    assert not any("/sign" in path or "/access_tokens" in path for _,path in rb.calls)


@pytest.mark.parametrize("change",["key-version","algorithm","disabled","not-yet-valid","expired","key-ops","public-key","private-key","role","permissions","repository","enrollment","revoked","token-expired"])
def test_each_issuer_provider_or_current_scope_change_refuses(rb,change):
    key,attributes=rb.keydata["key"],rb.keydata["attributes"]
    if change=="key-version":key["kid"]+="other"
    elif change=="algorithm":key["kty"]="EC"
    elif change=="disabled":attributes["enabled"]=False
    elif change=="not-yet-valid":attributes["nbf"]=rb.now+1
    elif change=="expired":attributes["exp"]=rb.now
    elif change=="key-ops":key["key_ops"].append("decrypt")
    elif change=="public-key":key["e"]="Aw"
    elif change=="private-key":key["d"]="private-canary"
    elif change=="role":rb.issuer["role"]="broker"
    elif change=="permissions":rb.issuer["permissions"]["actions"]="write"
    elif change=="repository":rb.issuer["repository_id"]="999"
    elif change=="enrollment":rb.issuer["enrollment_digest"]="sha256:"+"f"*64
    elif change=="revoked":rb.issuer["state"]="revoked"
    else:rb.issuer["credential_expires_at"]=rb.now
    reader=rb.issuer_reader();use=rb.use()
    with pytest.raises(BindingError,match="^"+ERROR+"$"):reader.read("issuance:fixture",decision=use)


def test_key_expiry_clips_all_later_observation_deadlines(rb):
    rb.keydata["attributes"]["exp"]=rb.now+2;use=rb.use();value=rb.issuer_reader().read("issuance:fixture",decision=use)
    assert use.deadline==rb.now+2
    assert value.expires_at==rb.now+2


def test_guest_source_reads_real_process_and_kernel_authorized_denial_controls(rb):
    use=rb.use();value=rb.guest_reader().read("guest:fixture",decision=use).data()
    assert value["process"]["pid"]==rb.process.pid
    assert value["process"]["uid"]==os.getuid()
    assert value["process"]["capabilities"]==[]
    assert set(value["denials"].values())=={"denied"}


@pytest.mark.parametrize("change",["exposed-port","outage","uid","host","incarnation","source","policy","artifacts","capabilities","pid"])
def test_guest_current_mutations_never_become_a_worker_denial(rb,change):
    if change=="exposed-port":rb.guest_grant=True
    elif change=="outage":rb.guest_outage=True
    else:
        def mutate(value):
            facts=value["facts"]
            if change=="uid":facts["process"]["uid"]+=1
            elif change=="capabilities":facts["process"]["capabilities"]=["CAP_SYS_ADMIN"]
            elif change=="pid":facts["process"]["pid"]=True
            else:facts[{"host":"host_id","incarnation":"incarnation_id","source":"source_digest","policy":"policy_digest","artifacts":"artifacts_digest"}[change]]="changed"
        rb.private_mutate=mutate
    reader=rb.guest_reader();use=rb.use()
    with pytest.raises(BindingError):reader.read("guest:fixture",decision=use)


def test_independent_current_initialization_and_actual_existing_store_agree(rb):
    use=rb.use();facts=rb.state_reader().read(decision=use).data()
    assert facts["identity"]==rb.initial["identity"]
    assert facts["initialization_digest"]==digest(rb.initial)
    assert facts["integrity"]=="ok"
    assert inspect_initialized_state(rb.store.directory)
    assert len(rb.calls)==3


@pytest.mark.parametrize("change",["missing","replacement","permissions","schema","restored","init-revoked","init-changed-after-read","wrong-receipt","selection"])
def test_actual_state_and_independent_initialization_mutations_refuse_without_repair(rb,change):
    database=rb.store.directory/"reservations.sqlite"
    if change=="missing":database.unlink()
    elif change=="replacement":
        replacement=database.with_name("replacement.sqlite");replacement.write_bytes(database.read_bytes());replacement.chmod(0o600);replacement.replace(database)
    elif change=="permissions":database.chmod(0o644)
    elif change=="schema":
        with sqlite3.connect(database) as db:db.execute("DROP TABLE reservations")
    elif change=="restored":rb.recovery="restored"
    elif change=="init-revoked":rb.initial["state"]="revoked"
    elif change=="init-changed-after-read":
        def mutate(value):
            if value["operation"]=="state":rb.initial["state"]="revoked"
        rb.private_mutate=mutate
    else:
        def mutate(value):
            if value["operation"]=="state":
                if change=="wrong-receipt":value["facts"]["initialization_digest"]="sha256:"+"f"*64
                else:value["facts"]["selection"]["retention_ref"]="retention:other"
        rb.private_mutate=mutate
    existed=database.exists();raw=database.read_bytes() if existed else None;reader=rb.state_reader();use=rb.use()
    with pytest.raises(BindingError):reader.read(decision=use)
    assert database.exists()==existed
    if existed:assert database.read_bytes()==raw


def test_same_peer_labels_cannot_supply_independent_initialization(rb):
    current=rb.client();same=rb.client();selection=rb.state_selection
    with pytest.raises(BindingError):StateReader(current=current,initialization=same,selection=selection)


@pytest.mark.parametrize("change",["source-file","policy-file","dead-process","guest-incarnation"])
def test_guest_facts_are_measured_again_instead_of_echoing_the_candidate(rb,change):
    selected=rb.guest_reader();use=rb.use();original=bytes(selected.raw)
    if change=="source-file":rb.guest_source.write_bytes(rb.guest_source.read_bytes()+b"\n# changed after approval\n")
    elif change=="policy-file":rb.guest_policy.write_bytes(canonical({"privilege":"exposed"}))
    elif change=="dead-process":rb.guest_process.terminate();rb.guest_process.wait(timeout=3)
    else:rb.guest_incarnation="33333333-3333-4333-8333-333333333333"
    with pytest.raises(BindingError):selected.read("guest:fixture",decision=use)
    assert selected.raw==original



def test_existing_correlation_counter_cannot_regress_under_new_clients():
    state=clock();use=decision(state);use.api_requests=4;ReadBudget(use).consume("control")
    use.api_requests=0
    # An invalid original decision must be refused before a new read client exists.
    with pytest.raises(BindingError):ReadBudget(use)


@pytest.mark.parametrize("group,limit",[("arm",24),("key",3),("private",12)])
def test_non_github_readers_have_fixed_shared_operation_bounds(group,limit):
    state=clock();use=decision(state)
    for _ in range(limit):ReadBudget(use).consume(group)
    consume_target = ReadBudget(use)
    with pytest.raises(BindingError):consume_target.consume(group)


@pytest.mark.parametrize("where",["credential","tls-checkpoint","response"])
def test_blocking_read_work_cannot_renew_the_parent_deadline(rb,where):
    original=rb.reader.credential
    if where=="credential":
        def late(**kwargs):rb.now+=10;return original(**kwargs)
        rb.reader.credential=late
    else:
        original_exchange=rb.reader.transport.exchange
        def exchange(*args,**kwargs):
            checkpoint=kwargs["before_send"]
            if where=="tls-checkpoint":
                def expired():rb.mono+=10;checkpoint()
                kwargs["before_send"]=expired
            response=original_exchange(*args,**kwargs)
            if where=="response":rb.now+=10
            return response
        rb.reader.transport.exchange=exchange
    selected=rb.github();use=rb.use()
    with pytest.raises(BindingError):selected.source(rb.main_sha,decision=use)
    if where in ("credential","tls-checkpoint"):assert rb.calls==[]


@pytest.mark.parametrize("part",["n","e"])
def test_public_key_metadata_is_bounded_before_crypto_construction(rb,part):
    rb.keydata["key"][part]="A"*800000;reader=rb.issuer_reader();use=rb.use()
    with pytest.raises(BindingError):reader.read("issuance:fixture",decision=use)
    assert not any(method=="POST" for method,path in rb.calls)


@pytest.mark.parametrize("change",["wall","monotonic","regression"])
def test_actual_tls_shared_correlation_refuses_before_application_data(rb,change):
    from workload_factory_binding_runtime.hosted.readback import start_finalization
    from workload_factory_binding_runtime.github_bootstrap.provider import ProviderReader
    from workload_factory_binding_runtime.github_bootstrap.https import Response
    from types import SimpleNamespace
    peer=SimpleNamespace(now=rb.now,mono=0.)
    root=Decision(clock=lambda:peer.now,monotonic=lambda:peer.mono);start_finalization(root)
    own=rb.use();ReadBudget(root).join(own);transport=rb.routed()
    class ActualTransport:
        def exchange(self,*args,**kwargs):
            check=kwargs["before_send"]
            def expired():
                if change=="wall":peer.now+=10
                elif change=="monotonic":peer.mono+=10
                else:peer.now-=1
                check()
            kwargs["before_send"]=expired
            reply=transport.exchange(*args,**kwargs);return Response(reply.status,reply.body)
    selected=ProviderReader(credential=lambda **_:"token:fixture",transport=ActualTransport())
    run_target = selected.decision("opensoft/openXwallet",own)
    with pytest.raises(BindingError):run_target.run("789")
    assert rb.calls==[]


@pytest.mark.parametrize("field",["disk-storage-type","nic-primary","nic-delete-option"])
def test_approved_provider_reference_metadata_is_retained_and_drift_refuses(rb,field):
    reader=rb.deployment_reader();vm=rb.arm[rb.ids["vm"]]["properties"]
    assert vm["storageProfile"]["osDisk"]["managedDisk"]["storageAccountType"]=="Standard_LRS"
    assert vm["networkProfile"]["networkInterfaces"][0]["properties"]=={"primary":True,"deleteOption":"Detach"}
    reader.read(decision=rb.use())
    if field=="disk-storage-type":vm["storageProfile"]["osDisk"]["managedDisk"]["storageAccountType"]="Premium_LRS"
    else:vm["networkProfile"]["networkInterfaces"][0]["properties"][{"nic-primary":"primary","nic-delete-option":"deleteOption"}[field]]=False if field=="nic-primary" else "Delete"
    read_decision = rb.use()
    with pytest.raises(BindingError):reader.read(decision=read_decision)


@pytest.mark.parametrize("field",["disk-storage-type","nic-primary","nic-delete-option"])
def test_approved_model_hash_cannot_replace_typed_reference_metadata(rb,field):
    vm=rb.arm[rb.ids["vm"]]["properties"]
    if field=="disk-storage-type":vm["storageProfile"]["osDisk"]["managedDisk"]["storageAccountType"]=True
    else:vm["networkProfile"]["networkInterfaces"][0]["properties"][{"nic-primary":"primary","nic-delete-option":"deleteOption"}[field]]="true" if field=="nic-primary" else True
    selection=replace(rb.deployment,model_digest=digest({k:v for k,v in vm.items() if k!="instanceView"}))
    from workload_factory_binding_runtime.hosted.platform_readback import DeploymentReader
    reader=DeploymentReader(selection=selection,reader=rb.reader,principal_ref="principal:arm-reader")
    read_decision = rb.use()
    with pytest.raises(BindingError):reader.read(decision=read_decision)
