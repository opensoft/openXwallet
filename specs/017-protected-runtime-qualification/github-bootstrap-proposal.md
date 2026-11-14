# Real GitHub bootstrap authentication source proposal

Status: source design accepted in #1314/#64; isolated T012H–K implementation candidate; no operational authority
Date: 2026-11-14
Factory owner: `openspec/changes/add-github-bootstrap-authentication/`
Sole implementation list: feature 017 tasks T012G-M; T012G records actual acceptance/commissioning, T012L/M remain pending

## Accepted preparation baseline

Brett source-ratified adapter #63 at `54dd1e1d4dc68b377cfa45024eb2be96c13f8bcc`
and directed landing when green, then preparation of this real-GitHub proposal.
It merged normally as `be41830acd16a197041e3aabb0281208b185d8ee` on
2026-11-14 at 13:49:16 UTC. Independently read merged tree
`2f3b5745b779a4bf9bdf11590b097988f4e501d0` equals the ratified tree. All runnable
exact-head checks passed and no review threads/requested changes were present.
The owner record is on [#63](https://github.com/opensoft/openXwallet/pull/63#issuecomment-6878228159).
Its ten Markdown files and this subsequent source proposal supply no operation.

## Recommended decision

The factory proposal recommends purpose-specific GitHub OIDC identity in the
future admission job, paired with independent broker/API run correlation. This
explicitly amends the earlier no-preflight-OIDC expectation for a newly accepted
opt-in internal profile. It does not weaken the existing proof verifier, relabel
fixture observations, or change the current default/CLI. No workflow is edited
and no token is minted by preparing this proposal.

The proposed admission audience is
`urn:opensoft:openxfactory:bootstrap-admission:v1`, requiring explicit later
acceptance and distinct protected-proof audience/complete subjects. Operator
policy, signed caller/reusable/source/run claims, independent dispatch journal
and current API observations must all agree. Audience alone is not a role.
Unprotected admission and post-environment repeat have separate trusted phase/
subject policies; ambiguous job class refuses. GitHub's job permission can request other audiences; the proposed audience
constant does not restrict issuer capability. Owned relying-party trusts for an
unprotected identity therefore require explicit operator review. Tokens/request
capability remain outside worker access and never enter logs/artifacts. A valid bootstrap token
cannot authorize setup, dispatch, approval, proof/custody or human consent.
Planned tests isolate each barrier with a successful signed proof-token control:
change only audience to bootstrap with protected claims intact, and separately
remove only environment with proof audience intact; both refuse before custody.
A provider-shaped unprotected proof-audience token is an additional negative,
not a substitute that could mask removal of one policy check.

GitHub documents job-scoped token-request permissions and reusable-workflow
identity; see [permissions](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-cloud-providers),
[claim reference](https://docs.github.com/en/actions/reference/security/oidc) and
[called workflow identity](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows).
Documentation is not actual claim observation. The immutable-ID prefix previously
read from repository settings is not an approved complete subject.

## Planned source slice and required controls

The existing feature plan and T012G-M own future implementation. Planned relative
areas are `scripts/workload_factory_binding_runtime/github_bootstrap/`, the existing
preparation entrypoint/bindings and caller/reusable workflow, and corresponding
`tests/runtime_binding/test_github_bootstrap*.py` plus fixed matrix contract.
These are planned paths, not new executable artifacts. No neutral API/pin,
published contract, dependency lock or additional runtime service role is created.

The factory design covers: independently selected HTTPS identity; separate
bootstrap verifier using fixed issuer transport while preserving proof claims;
durable pre-I/O attempt consumption outside the job; Actions-write broker versus
read-only controller; provider-returned run correlation with no newest-run fallback (dispatch API
`2026-03-10`, body `ref`/`inputs`, 200 run ID; no legacy `return_run_details` flag);
coarse credential scope; actual phase/source/attempt corroboration; originator versus
App actor approval separation; current revocation/earliest expiry; and retained
state/independent cleanup. Missing facts, cache expiry, redirects, ambiguity and
source movement refuse. No retry/reset follows a lost dispatch response. A reserved winner must recheck
current approval/window/revocation after blocking work immediately before send;
expiry or revocation causes zero requests while retaining consumption.

The main-ref race remains explicit: detection can withhold wallet authority but
cannot guarantee changed workflow code never starts. Default live use is blocked
until the owner accepts source-update coordination or bounded residual exposure
and credential controls; atomic prevention requires another upstream design.
The provider-write endpoint is not tested and its documented run-ID response is
not operationally qualified here.

## Owner decisions and sequence

First accept or reject bootstrap-only admission OIDC, the purpose/phase and trusted
orchestration/worker boundary, and the factory's proposed bounds; explicitly
commission the bounded source slice if accepted. If strict no-preflight-OIDC is
retained, a separate client identity/issuance design is required, not an automatic
stored-secret or self-hosted-runner fallback.

Source implementation/isolated qualification would still grant no token mint,
setup or dispatch. T013 must later select actual target/admin identities,
issuer subjects/audiences, Apps/credential scopes, protection/reviewers, storage,
janitor and main-update exposure policy, then obtain separate bounded setup and
one-dispatch decisions. Broker App identity cannot hide the originating human
from independent-review checks. Environment approval is not domain human consent.
T001/T013/T014/T015 remain unchecked. Feedback stays deferred and neither
historical blocked write is replayed.

## Subsequent source acceptance and bounded realization

Brett source-ratified factory #1314 at `94bf0f43704f` and adapter #64 at
`ff9bd72278a5`, directed ordered landing, and explicitly commissioned isolated
T012H–K. [Evidence](evidence.md#2026-11-14-github-bootstrap-source-ratification-and-isolated-commission)
records exact accepted/merge/tree identities. The preceding proposal text is its
accepted preparation baseline; it is not evidence that this subsequent implementation
candidate is accepted, deployed or selected. See the current [plan](plan.md).
