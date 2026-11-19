# T013 Scoped Authorization Draft

Current decision candidate: [T013-S1 S01-S12](hosting-issuance-selections.md),
2026-11-19 UTC, at accepted #95/main `05790f37383c`. It is a proposed design basis,
not completed P2 or P3 and not a scoped setup/dispatch/run/cleanup grant. The owner
has not accepted these selections or appointed the nominees. Every NOT GRANTED
stage below remains unchanged; source selection, actual window/expiry, deployment
composition, effective protections and provider-safe retirement remain gates.

Status: T012V/T012VJ source accepted through #94; every operational stage NOT GRANTED
Updated: 2026-11-18
Selections: [operational inputs](operational-inputs.md)
Accepted bootstrap source: [bootstrap record](workflow-bootstrap.md)

Brett Heap source-ratified [openXwallet #94](https://github.com/opensoft/openXwallet/pull/94#issuecomment-6991564275) at `b1430cedbf555afbfbe0a6de8a41e9208cfc145a`
and directed landing when green, independent post-merge verification, then this
T013 refresh. It merged normally as `255035a41761a88293e565573a319dc112a48522` on `2026-11-18T21:03:25Z`,
with tree `f40947b61c1a9a8a073b1ffe40fc9f042c20daad` exactly equal to the ratified tree.
The [source qualification](https://github.com/opensoft/openXwallet/pull/94#issuecomment-6989959898) and [independent main receipt](https://github.com/opensoft/openXwallet/pull/94#issuecomment-6993081869)
remain separate. T012V/T012VJ are accepted source; T001/T013/T014/T015 remain
unchecked. No operational `accepted_commit`, deployment, principal,
credential, appointment or grant is selected by this source act or its later
documentation descendant.

The hosted source is implemented and accepted in isolation: static-v2 plans,
phase-limited admission, bounded authenticated clients, staging, measured final
bytes, one-use registration, lifecycle cleanup and origin-bound evidence. It
preserves legacy v1/default behavior and all neutral APIs. For the proposed hosted
pilot, independently approve `openxfactory-dispatch-selection-internal-v2` with
`openxfactory-hosted-canonical-finalization-v2`; the preserved static-v1/full-runtime-v1
readers are not substitutes for that measured finalization. Three input names,
seven runtime services and eight source roles remain unchanged.

Actual authenticated deployed composition, principals/keys/endpoints, state and
external watchdog remain unselected. Concrete activation source requires separate
review if needed. Default `workflow.operational_bindings()` unconditionally
refuses before outputs/OIDC; no environment flag, fixture or edited document can
activate it. Source acceptance and this refresh grant none of the four stages below.

## Decision record to complete

Before setup, select intended target, final accepted source, administrators,
names/actions, resource limits, budget/window and policies. Record only non-secret
references. Resource IDs/receipts that can exist only after authorized creation
are post-setup readback obligations; they block dispatch, not an exact scoped
create decision. Unselected scope blocks the corresponding decision.

| Decision | Prepared bound | Required owner/operator selection |
| --- | --- | --- |
| Purpose/case | First codeXfactory pilot; machine possession qualification | Exact case ID and accountable owner |
| Final source | Accepted factory/adapter/hosted source through #94 | Eight operational source roles/commits/paths/digests, deployed image/launch measurements and concrete authenticated composition/activation acceptance; exact executing workflow SHA remains unselected |
| Target | Dedicated disposable nonproduction Linux deployment | Exact provider/account or tenant/subscription, existing parent IDs, host/cluster, region and namespace/resource-group scope |
| Administrators | Worker cannot administer supervisor, custody, bootstrap/operation grants, readback or cleanup | Named independent principals, control-plane owners, credential/trust refs and effective access evidence |
| Environment | Proposed new `wallet-mfa-pilot-qa` in repo ID `1347887821` | Before setup: approved name and create scope, 1–6 reviewer IDs, distinct dispatcher, prevent self-review, no admin bypass, exact `refs/heads/main` deployment restriction; after setup: actual ID and complete effective protection readback |
| Bootstrap/controller | Source-accepted `openxfactory-github-bootstrap-internal-v1`; preflight bootstrap-purpose OIDC before environment, protected-phase repeat afterward | Actual separately configured phase subjects, trusted endpoint/CA/token-request transport, bounded authenticated callbacks, journal/authority administrator/principal/credential refs, current revocation/readback and deployed worker exclusion |
| Broker/App/originator | Durable dispatch-attempt consumption precedes credential/send; first attempt only | Repository-limited installation and effective Actions-write scope, separate read-only identity, credential resolver/issuance/revocation owner, original human and broker actor IDs; distinct eligible reviewer identities |
| Main-update control | Source accepts `coordinated` or `bounded-residual-exposure` values | Explicit owner selection and actual coordination evidence or bounded residual-start exposure with credential/relying-party boundaries; no automatic freeze/rule/tag change |
| Selection/authorization | Separate independent static approval and actual-run full approval | Decision issuer, case/time window, static digest, preauthorization ref and revocation path; then actual-run config digest and operation grant |
| Services | Exactly seven runtime roles; independently authenticated current records/challenge | Per-service principal/credential/trust refs; separate bootstrap, environment, authorization, scheduler and cleanup readback clients |
| Issuer/subject | Fixed GitHub endpoints; accepted bootstrap-purpose audience; observed immutable-ID settings/prefix | Actual preflight/protected subjects/claims, distinct protected proof audience and relying-party acceptance/exclusion readback; job token-request permission can request other audiences |
| State | Explicitly initialized private retained replay store | Store/initialization/retention/recovery refs, provisioning owner, initialization receipt and preservation/access policy |
| Lifecycle | Bounded lease and independent registered janitor/scheduler/readback | Exact plan/scope, principals, generation/ownership allowlist, deadlines and receipt retention; runner death/expiry readback |
| Setup limit | Smallest bounded pilot; preserve unrelated/shared resources | Exact create/update actions and parent/name allowlist, resource limits, spend ceiling, UTC start/end/expiry and setup rollback owner |
| Dispatch limit | One manual caller/local-reusable invocation at exact accepted `main` source | Named dispatcher, case, final accepted workflow SHA, static digest and independent preauthorization; no automatic retry |
| Evidence/acceptance | Source conformance precedes real protected qualification | Source-accepted live qualification/cleanup clients and protected receipt promotion, actual P01/deployed G02/G03/L01, and separate consumer/human/domain acceptance |

No new App, federation, credential, grant or provider permission is authorized
by naming its future role. Credential references never contain credentials,
tokens, private keys or factor seeds. The read-only subject settings inspection
did not mint a workload token and does not approve a subject/audience. Preserve
the existing `copilot` environment and current provider configuration.

## Staged future authorization

1. **Setup only — NOT GRANTED.** After the source/client and target decisions
   above are complete, authorize a named operator to create/configure only the
   enumerated nonproduction resources during the approved window/budget. Bind
   new creates to exact parent identity/name; refuse an unexpected existing
   resource and record assigned immutable IDs. Scope setup rollback/cleanup and
   its independent owner before setup begins. Read back actual protection,
   source/administration, initialized state and independent scheduler/janitor/
   readback service readiness. The actual run-bound plan/lease is registered
   after run assignment and before admission; setup readiness does not invent
   that run identity. Setup grants neither workflow dispatch nor signing use.
2. **One bootstrap dispatch — NOT GRANTED.** After authorized setup readback
   and accepted actual hosting/authentication clients, independently approve the
   complete hosted static-v2 plan under `openxfactory-dispatch-selection-internal-v2`
   and one preauthorization. Use only manual inputs `accepted_commit`,
   `selection_digest`, `preauthorization_ref` at the exact accepted workflow
   source. The accepted broker and hosted source still need selected/qualified deployment,
   retained journal, authenticated callbacks and credential issuance. It must
   first durably reserve/consume the dispatch attempt against the selected
   preauthorization under an atomic compare-and-set; only that winner may send one request. A crash before
   I/O or lost response leaves pending/indeterminate scope, never an automatic
   reset/retry. The reference authority alone does not implement this operational
   dispatch phase. No PR/fork trigger, floating source, second dispatch, automatic retry
   or token-for-discovery is covered. Reconcile exact source if `main` has moved.
   Bootstrap-only identity is acquired by the accepted preflight phase after
   run assignment, before environment-bound proof identity. The bootstrap token
   authenticates admission only; it cannot authorize this dispatch stage. An
   unverified worker context or prior job output supplies neither identity nor grant.
3. **Actual run/attempt authority — NOT GRANTED.** After GitHub assigns the
   run, the independent authority authenticates/corroborates it and binds the
   already-reserved dispatch scope to the actual run/attempt, without freeing or
   reissuing that attempt. It atomically binds the runtime preauthorization and
   approves the final full runtime config/grant for the
   exact selection/source/repository/case/run/attempt. Independently register and
   read back that full-config-bound run plan, active lease and cleanup generation
   scope before admission can return readiness. The hosted static-v2 plan commits exact configuration/policy/measurement
   templates and closed derivation rules. Only assigned launch run ID/attempt,
   measured composition digest and derived authority policy digest are finalized;
   no other selection or time-window change is implied. Approve only `qualify-existing-resources` and one bounded owning
   proof, with the accepted qualification/cancellation cases expressly named.
   If more runs are needed, enumerate their separate scope and decisions. A
   rerun/changed attempt never inherits authority. Full fresh environment,
   protection, grant, scheduler and active lease checks retain the earliest
   deadline, and bootstrap/admission repeat after environment approval.
4. **Cleanup/readback — NOT GRANTED.** Bind deletion/revocation to the approved
   exact ownership/generation allowlist. An independently administered janitor
   remains able to expire/reconcile and read back cleanup after hard runner
   death or proof/config expiry. Remove only approved run-owned ephemeral
   resources; preserve replay state, retained evidence and shared resources.
   A changed target, generation or cleanup scope requires a new decision.
   Missing readback leaves qualification incomplete and escalates to the named
   cleanup owner. A runner `always()` step alone cannot establish this result.

None of these stages is approved by copying the draft, approving source or
saying "go ahead" without the exact selected scope. This document supplies no
executable config, grant or runnable setup/dispatch commands. Do not dispatch
the historical #59 interface, predict IDs, mutate immutable inputs, reuse prior
grants or bypass admission to obtain missing runtime facts.

## Exclusions and remaining owner act

No production deployment, tenant-wide policy change, standing broad credential,
wildcard deletion, bench restart/rebuild, consumer pin/lock promotion, domain
read/apply/marker action, human factor enrollment/approval simulation or release
acceptance is covered. Feedback/support stays deferred; neither historical
blocked write may be replayed.

T013 stays unchecked until every operational category has approved non-secret
references and independent readback, and actual scoped setup/dispatch authority
is recorded. T014 execution/protected receipt promotion and T015 consumer
acceptance remain separate. Environment review does not establish independent
domain human approval.

The next owner decisions are the actual nonproduction target, administrative
owners, distinct dispatcher/reviewer, actual bootstrap/controller hosting, issuance and source-update policy
and resource/budget/window limits. They can commission the required source
integrations without authorizing setup or dispatch. Bootstrap and hosted algorithm source acceptance
is complete; actual deployed composition/activation, live hosting/authentication and
operational decisions remain open.

## Current readback and source-only boundary

Read-only GitHub refresh at `2026-11-18T22:09:57.469950+00:00` confirms only ineligible `copilot`,
no protected workflow runs, read-only token defaults and unchanged default/
immutable-ID subject settings. See [operational inputs](operational-inputs.md).
The [#94 source decision](evidence.md#2026-11-18-94-source-acceptance-and-t013-refresh) completes the staging-journal source handoff,
not T013 or an approved executing `accepted_commit`. Source-CI permission to keep
integrating incoming changes is not acceptance of an operational main-update
policy. Earlier qualification checkpoints remain historical. All four stages
remain NOT GRANTED; feedback deferred and blocked writes unreplayed.

Ordinary source-CI reruns supply no protected-operation authority. The accepted
operational broker still permits only its separately approved first run attempt;
no retry/reset, grant, dispatch selection or source-update policy is inherited
from source verification. Default operational_bindings() still refuses
workflow-operational-host-unselected before outputs/OIDC. Setup, one dispatch,
actual-run authority and cleanup/readback remain separately NOT GRANTED.
