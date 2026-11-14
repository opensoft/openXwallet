# T013 Scoped Authorization Draft

Status: prepared after portable-reference source landing; every operational stage NOT GRANTED
Updated: 2026-11-14
Selections: [operational inputs](operational-inputs.md)
Accepted bootstrap source: [bootstrap record](workflow-bootstrap.md)

The source-only ratification of factory #1311 at
`6dadf188a0afa22e3c205561299f6045a9c95359` with adapter #60 at
`78e7bbeabca250073d5896154ccc99bb163116cc` is recorded. Their accepted merge
baselines are factory `f2fb60f04c8229f4343e25a0155418f2f737d73a` and adapter
`61fbe41f7e08e831e0b15c2c97ea6ff386f587f3`, each with its ratified tree.
Factory post-merge source CI is verified in the [selection packet](operational-inputs.md).
This resolves the earlier source-input circularity; it grants no operation.

The 2026-11-14 instruction ratifies factory #1312 and adapter #61/#62 for
source acceptance only and authorizes ordered landing plus T013 preparation.
The [source acceptance record](evidence.md#2026-11-14-source-ratification-and-ordered-landing)
names the exact heads, merges and equal trees. The
[T013 decision packet](t013-decision-record.md) separates proposed selections,
source prerequisites, setup and dispatch decisions. The
[authentication preparation](bootstrap-authentication-plan.md) is a future
source design option, not a selected operational integration.
It explicitly keeps setup and dispatch unauthorized. All operative stages below
are **NOT GRANTED**. Portable reference services are now source accepted in isolation; actual
hosting/authentication integrations and administration remain unselected.
The current CLI still refuses before environment outputs/OIDC.

## Decision record to complete

Before setup, select intended target, final accepted source, administrators,
names/actions, resource limits, budget/window and policies. Record only non-secret
references. Resource IDs/receipts that can exist only after authorized creation
are post-setup readback obligations; they block dispatch, not an exact scoped
create decision. Unselected scope blocks the corresponding decision.

| Decision | Prepared bound | Required owner/operator selection |
| --- | --- | --- |
| Purpose/case | First codeXfactory pilot; machine possession qualification | Exact case ID and accountable owner |
| Final source | Accepted factory/adapter bootstrap baselines above | Eight source roles, immutable commits/relative paths/content digests, dependencies/composition, owning service sources and accepted hosting/qualify/cleanup/receipt integrations |
| Target | Dedicated disposable nonproduction Linux deployment | Exact provider/account or tenant/subscription, existing parent IDs, host/cluster, region and namespace/resource-group scope |
| Administrators | Worker cannot administer supervisor, custody, bootstrap/operation grants, readback or cleanup | Named independent principals, control-plane owners, credential/trust refs and effective access evidence |
| Environment | Proposed new `wallet-mfa-pilot-qa` in repo ID `1347887821` | Before setup: approved name and create scope, 1–6 reviewer IDs, distinct dispatcher, prevent self-review, no admin bypass, exact `refs/heads/main` deployment restriction; after setup: actual ID and complete effective protection readback |
| Bootstrap authority | Static approval precedes actual-run binding; no pre-admission OIDC dependency | Source-accepted authentication/client design, authority administrator/principal/credential/trust refs, authenticated actual GitHub context, atomic one-preauthorization/one-run-attempt consumption and revocation/readback |
| Selection/authorization | Separate independent static approval and actual-run full approval | Decision issuer, case/time window, static digest, preauthorization ref and revocation path; then actual-run config digest and operation grant |
| Services | Exactly seven runtime roles; independently authenticated current records/challenge | Per-service principal/credential/trust refs; separate bootstrap, environment, authorization, scheduler and cleanup readback clients |
| Issuer/subject | Fixed GitHub endpoints; observed immutable-ID subject settings/prefix in selection packet | Explicit audience and complete configured subject/claims; fresh independent corroboration, no guessed name-only subject |
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
   complete static selection under `openxfactory-dispatch-selection-internal-v1`
   and one preauthorization. Use only manual inputs `accepted_commit`,
   `selection_digest`, `preauthorization_ref` at the exact accepted workflow
   source. A future separately source-approved broker must first durably reserve/
   consume the dispatch attempt against the selected preauthorization under an
   atomic compare-and-set; only that winner may send one request. A crash before
   I/O or lost response leaves pending/indeterminate scope, never an automatic
   reset/retry. The reference authority alone does not implement this operational
   dispatch phase. No PR/fork trigger, floating source, second dispatch, automatic retry
   or token-for-discovery is covered. Reconcile exact source if `main` has moved.
   Bootstrap authentication must work before environment selection/OIDC; an
   unverified worker context or prior job output cannot authorize this stage.
3. **Actual run/attempt authority — NOT GRANTED.** After GitHub assigns the
   run, the independent authority authenticates/corroborates it and binds the
   already-reserved dispatch scope to the actual run/attempt, without freeing or
   reissuing that attempt. It atomically binds the runtime preauthorization and
   approves the final full runtime config/grant for the
   exact selection/source/repository/case/run/attempt. Independently register and
   read back that full-config-bound run plan, active lease and cleanup generation
   scope before admission can return readiness. Static commitment omits
   only launch run ID/attempt; no other selection or time-window change is
   implied. Approve only `qualify-existing-resources` and one bounded owning
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
owners, distinct dispatcher/reviewer, bootstrap authentication/authority design
and resource/budget/window limits. They can commission the required source
integrations without authorizing setup or dispatch. Source bootstrap acceptance
is complete; live hosting/authentication and operational decisions remain open.
