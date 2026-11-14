# T013 Scoped Authorization Draft

Status: T012M reconciled after #65 source landing; every operational stage NOT GRANTED
Updated: 2026-11-14
Selections: [operational inputs](operational-inputs.md)
Accepted bootstrap source: [bootstrap record](workflow-bootstrap.md)

Brett source-ratified adapter #65 at `ab34ff4ec4fe27d56c8fd09c99614785c23e760f`, directed landing when green, and commissioned T012M/T013 documentation. It landed as `366533bed77293b096b0a7dbda61399ff5dbafe5` with equal ratified/merged tree `669a1b431f17d360fcf827a749a756e863ec9ed8`. Factory #1314's accepted source design is unchanged. The [owner/landing evidence](evidence.md#2026-11-14-65-source-acceptance-and-t012m-handoff) records the exact act and source checks.

This closes T012L source acceptance and supplies T012M's handoff, with no operational selection or grant. The [selection packet](operational-inputs.md), [T013 decisions](t013-decision-record.md) and [authentication handoff](bootstrap-authentication-plan.md) identify remaining target/administration, client issuance, actual provider evidence and source-update choices. Accepted bootstrap-only preflight OIDC is separate from protected proof identity; it is not permission to request a live token. Default bindings still refuse before token access/outputs. Hosting and qualify/cleanup/receipt integration remain unselected.

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
   complete static selection under `openxfactory-dispatch-selection-internal-v1`
   and one preauthorization. Use only manual inputs `accepted_commit`,
   `selection_digest`, `preauthorization_ref` at the exact accepted workflow
   source. The accepted #65 broker source still needs selected/qualified hosting,
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
owners, distinct dispatcher/reviewer, actual bootstrap/controller hosting, issuance and source-update policy
and resource/budget/window limits. They can commission the required source
integrations without authorizing setup or dispatch. Source bootstrap acceptance
is complete; live hosting/authentication and operational decisions remain open.
