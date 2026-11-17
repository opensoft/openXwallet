"""Governed finalization allocation; no expanded ordinary admission authority."""
import pytest
from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.hosted.readback import ReadBudget,start_finalization
from .test_hosted_readback import clock,decision


def pair():
    state=clock();root=decision(state);start_finalization(root)
    other_state=clock();own=decision(other_state);ReadBudget(root).join(own)
    return state,root,other_state,own


def test_finalization_members_share_limits_and_no_new_correlation_budget():
    state,root,other_state,own=pair()
    for i in range(18):ReadBudget(root if i%2 else own).consume("protection")
    for name,limit in [("source",4),("control",2)]:
        for _ in range(limit):ReadBudget(own).consume(name)
    root.api_requests=2;own.api_requests=2
    assert ReadBudget(root).github_requests==ReadBudget(own).github_requests==28
    assert ReadBudget(root).state is ReadBudget(own).state
    consume_target = ReadBudget(own)
    with pytest.raises(BindingError):consume_target.consume("protection")
    own.api_requests+=1
    # Reconstruction itself must refuse the invalid joined correlation.
    with pytest.raises(BindingError):ReadBudget(root)


@pytest.mark.parametrize("member",[0,1])
def test_joined_member_correlation_highwater_cannot_regress(member):
    _,root,_,own=pair();selected=(root,own)[member]
    selected.api_requests=2;ReadBudget(own).check();selected.api_requests=1
    with pytest.raises(BindingError):ReadBudget(root)


@pytest.mark.parametrize("member",[0,1])
@pytest.mark.parametrize("change",["wall-expiry","wall-regression","monotonic-expiry","monotonic-regression"])
def test_either_original_clock_remains_authoritative(member,change):
    state,root,other_state,own=pair();selected=(state,other_state)[member]
    if change=="wall-expiry":selected.now+=10
    elif change=="wall-regression":selected.now-=1
    elif change=="monotonic-expiry":selected.mono+=10
    else:selected.mono=-1
    with pytest.raises(BindingError):ReadBudget(own if member==0 else root)


def test_earliest_expiry_is_propagated_to_both_original_decisions():
    _,root,_,own=pair();own.clip(1004);ReadBudget(root).check()
    assert root.deadline==own.deadline==1004


def test_snapshot_limit_refuses_seventh_even_when_read_budget_remains():
    _,root,_,own=pair()
    for i in range(6):ReadBudget(root if i%2 else own).begin_protection()
    begin_protection_target = ReadBudget(root)
    with pytest.raises(BindingError):begin_protection_target.begin_protection()
    assert ReadBudget(root).count("protection")==0


@pytest.mark.parametrize("change",["late-upgrade","third-member","existing-ledger","spent-correlation"])
def test_unapproved_budget_reconstruction_or_late_upgrade_refuses(change):
    state=clock();root=decision(state)
    if change=="late-upgrade":
        ReadBudget(root).consume("protection")
        with pytest.raises(BindingError):start_finalization(root)
        assert ReadBudget(root).count("protection")==1
    else:
        start_finalization(root);own=decision(clock())
        if change=="third-member":
            ReadBudget(root).join(own);own=decision(clock())
        elif change=="existing-ledger":ReadBudget(own)
        else:own.api_requests=1
        join_target = ReadBudget(root)
        with pytest.raises(BindingError):join_target.join(own)


@pytest.mark.parametrize("group,limit",[("arm",24),("key",3),("private",12)])
def test_finalization_keeps_non_github_limits_unchanged(group,limit):
    _,root,_,own=pair()
    for i in range(limit):ReadBudget(root if i%2 else own).consume(group)
    consume_target = ReadBudget(own)
    with pytest.raises(BindingError):consume_target.consume(group)


@pytest.mark.parametrize("spent",range(5))
def test_correlation_reader_refuses_fifth_shared_request_before_credential_or_io(spent):
    from workload_factory_binding_runtime.github_bootstrap.provider import ProviderReader
    from workload_factory_binding_runtime.github_bootstrap.https import Response
    _,root,_,own=pair();root.api_requests=spent;ReadBudget(root).check();calls=[];credentials=[]
    class Transport:
        def exchange(self,*args,**kwargs):calls.append(args);return Response(200,b"{}")
    def credential(**kwargs):credentials.append(True);return "token:fixture"
    reads=ProviderReader(credential=credential,transport=Transport()).decision("opensoft/openXwallet",own)
    for _ in range(4-spent):reads.run("789")
    with pytest.raises(BindingError):reads.run("789")
    assert len(calls)==len(credentials)==4-spent
    assert root.api_requests+own.api_requests==4


@pytest.mark.parametrize("initiator",[0,1])
@pytest.mark.parametrize("change",["wall-expiry","wall-regression","monotonic-expiry","monotonic-regression"])
def test_joined_peer_clock_refuses_after_tls_before_application_send(initiator,change):
    from workload_factory_binding_runtime.github_bootstrap.provider import ProviderReader
    from workload_factory_binding_runtime.github_bootstrap.https import Response
    state,root,other_state,own=pair();peer=(other_state,state)[initiator];sent=[]
    class Transport:
        def exchange(self,*args,**kwargs):
            if change=="wall-expiry":peer.now+=10
            elif change=="wall-regression":peer.now-=1
            elif change=="monotonic-expiry":peer.mono+=10
            else:peer.mono=-1
            kwargs["before_send"]()
            sent.append(True);return Response(200,b"{}")
    reader=ProviderReader(credential=lambda **_:"token:fixture",transport=Transport())
    run_target = reader.decision("opensoft/openXwallet",(root,own)[initiator])
    with pytest.raises(BindingError):run_target.run("789")
    assert sent==[]


def test_ordinary_provider_transport_contract_is_unchanged_without_hosted_ledger():
    from workload_factory_binding_runtime.github_bootstrap.provider import ProviderReader
    from workload_factory_binding_runtime.github_bootstrap.https import Response
    class Transport:
        def exchange(self,method,url,*,headers,decision):return Response(200,b"{}")
    use=decision(clock());reader=ProviderReader(credential=lambda **_:"token:fixture",transport=Transport())
    assert reader.decision("opensoft/openXwallet",use).run("789")=={}
    assert not hasattr(use,"_hosted_reads")
