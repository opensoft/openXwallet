# Actual GitHub bootstrap authentication preparation

Status: FUTURE SOURCE DESIGN OPTION; no implementation, hosting, credential or dispatch authorized
Updated: 2026-11-14
Owner boundary: factory grammar; adapter feature 017 implementation; no neutral API promotion

The subsequent factory-owned [real authentication proposal](github-bootstrap-proposal.md)
now recommends an explicit bootstrap-only OIDC amendment as a separate source
choice. This accepted preparation's strict no-preflight-OIDC basis remains the
current default until a new profile is ratified/commissioned and implemented.
Do not infer that GitHub technically requires an environment to issue any OIDC
identity; the protected proof identity class and current policy are the constraint.

## Three different facts must be established

1. An independently approved static selection/case/window authorizes one dispatch.
2. The actual GitHub run/attempt is unambiguously correlated with that approved dispatch.
3. The admission client and controller are independently authenticated, outside worker administration.

The accepted portable reference supplies durable atomic binding and real local
mTLS/signatures over simulated context. It does not establish facts 2/3 for GitHub.
The reference profile is fixed to `isolated-fixture` and loopback; neither its
profile nor test launcher may be relabeled or deployed as operational acceptance.
The default operational factory remains unselected and refuses before outputs/OIDC.

## Proposed correlation route for a separately commissioned source proposal

Version correction in the subsequent real-authentication proposal: the selected
`2026-03-10` dispatch schema has only `ref` and `inputs`, returning 200 with the
run ID by default. The earlier preparation mixed the older `2022-11-28` optional
`return_run_details`/204 behavior with a newer version header. Do not carry that
flag into the proposed 2026 request. This corrects documentation only; no endpoint
behavior has been tested and no dispatch is authorized. The endpoint requires
repository Actions write for a selected fine-grained credential; see the
[version-pinned workflow API](https://docs.github.com/en/rest/actions/workflows?apiVersion=2026-03-10#create-a-workflow-dispatch-event).

A future selected trusted dispatch broker could journal the approved static
selection digest, case, preauthorization, exact repository/workflow/main source,
actor and bounded window **before** dispatch. Under a durable store lock it must
atomically compare-and-set that approved preauthorization to dispatch-pending/
consumed **before any external request**. Only the reservation winner may make
at most one dispatch attempt after the separate one-dispatch owner decision;
concurrent callers, restarts and crashes cannot send again. A crash before I/O
may leave no run and still consumes this attempt; retain pending/indeterminate
state for separately authorized reconciliation, never automatic release/reset.
The winner could require the selected 2026 response and durably bind its run ID
to that journal entry. The API body contains `ref` and the three configured workflow
inputs; accepted caller inputs remain exactly `accepted_commit`, `selection_digest`
and `preauthorization_ref`. Never use client-supplied run URLs as fetch targets.

The API's main branch `ref` is not an atomic pin to an accepted SHA. Recheck the
selected main source before a separately authorized attempt and corroborate the
returned run's actual source afterward. Any intervening source/ref drift refuses
authority/qualification and requires owner reconciliation; do not redispatch or
claim that a successful API response proves accepted source. Only independent
readback can clear the authority source gate, and it cannot undo a provider-created
run or guarantee that changed workflow code never started. This residual race is
an unresolved source/operational acceptance gate: the next owner-approved proposal
must define reviewed main-update coordination/control or explicitly accepted
residual exposure and credential boundaries. No source freeze, repository rule
change, tag fallback or relaxed main restriction is selected here. If acceptance
requires atomic prevention of any unaccepted workflow execution, this API-only
route is insufficient and must remain blocked for an upstream design decision.

A separately administered controller would then corroborate the returned numeric
run ID through the fixed selected GitHub API/repository and attempt-specific
run/job metadata. Fine-grained workflow-run and job reads require Actions read;
public visibility alone does not authenticate an admission caller. See
[workflow-run API](https://docs.github.com/en/rest/actions/workflow-runs#get-a-workflow-run)
and [attempt-specific jobs](https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run-attempt).
The broker's write capability must not be held by the reader, controller or worker.
Repository Actions write is a provider permission broader than one workflow
invocation; broker policy does not narrow the actual GitHub credential. The
credential boundary, repository-only selection, allowed broker operations and
accepted residual capability require explicit source/operator review. Actual App
installation IDs, effective permissions, issuance and revocation are future
reviewed selections, not existing grants.

## Required verifier and failure behavior

- Authenticate the broker journal/controller/readback channel independently of request bodies. Bind immutable repo/owner IDs, selected workflow ID/path, event `workflow_dispatch`, main ref, accepted source SHA, independently selected actor/dispatcher and exact run/attempt. Do not silently normalize changed names, refs or subjects.
- Corroborate each required field from its authoritative source and record provenance. The implementation proposal must map exact API response fields and missing-field behavior. A public run record or signed copy of worker environment variables does not prove an approved dispatch or authentic client.
- A legacy/unexpected 204 response is insufficient for this version-pinned route. Missing/malformed/mismatched response, unsupported API behavior or ambiguity refuses; do not select the newest run from a list, infer identity from time/title, predict an ID, trust worker outputs or fall back to matching only source/actor.
- A timeout/lost response after the dispatch request may mean GitHub created a run. Retain dispatch-pending/indeterminate state and prohibit automatic retry/unbind/reset. Escalate to the named reconciliation owner. Manual attribution/cancellation needs separately authorized scope; this packet authorizes neither. Do not claim the API offers an idempotency key or exactly-once dispatch.
- Observe no run/attempt as approved until its independent journal correlation is authenticated. Atomic authority binding, immutable static projection, current revocation and earliest deadlines remain required. A rerun/changed attempt needs a new decision and cannot inherit prior authority.
- Require a new owner-approved operational source profile and implementation proposal; preserve the accepted fixture profile, neutral pins/APIs and seven runtime service roles. Bounded canonical signatures may carry controller observations only after actual observation authentication and issuance are qualified.

## Strict-profile admission identity and the proposed alternative

The API-returned ID does **not** authenticate the job making a bootstrap request.
Preflight runs before the protected proof identity class is released; the current
accepted profile does not permit a preflight OIDC request. Do not
request an id-token to discover context, place signer credentials in admission,
trust a worker hash, or assume a general repository token proves a run identity.
If strict no-preflight-OIDC is retained, a source proposal must select and test
independent admission-client issuance/delivery, service identity, run/case/static
scope, expiry, revocation, worker exclusion and administrative control. Repository
secrets, self-hosted admission identities or another control plane are not selected.
The newly proposed mode instead uses bootstrap-purpose GitHub OIDC after explicit
owner source acceptance/commissioning; it does not require inventing a stored
pre-OIDC credential for that mode. Actual audiences/subjects, trusted token-request
transport and worker exclusion remain independent qualification gates. No new mode
is implemented or selected by this preparation.
Different principal strings or certificates alone do not establish this boundary.

The existing real-workload OIDC verifier remains a later proof-gate input, with
fixed issuer endpoints and independently selected expected claims. Observed
immutable-ID subject prefix is configuration only, not an approved full subject
or audience. No federation or broad provider permission is selected by this plan.

## Required isolated evidence before any operational decision

The separate source feature should cover documented 200 parsing/correlation;
204/malformed/mismatched repo/workflow/source/event/actor/run/attempt refusal;
fixed endpoint and URL/redirect rejection; durable pre-I/O reservation with at
most one external dispatch attempt under concurrent brokers, crash-before-I/O
consumption and no reset/retry; main/source movement refusal; duplicate journal binding;
restart/revocation and lost-response consumption; reader/controller/worker access
denial with positive controls; actual client authentication and credential scope;
strict/default no-OIDC/no-output refusal; proposed-mode bootstrap-only identity
before readiness with no outputs until verified admission and no protected-proof
identity before environment approval; full config/lease/source/protection continuity;
and independent cleanup after failure/cancellation/runner death preserving state.
These are source acceptance criteria, not an added duplicate implementation list.

Documentation was checked on 2026-11-14; the documented API version is
`2026-03-10`. Endpoint behavior and permissions still need source tests and
separately authorized live corroboration. No workflow was dispatched, no API
write was tested, and no implementation/credential/setup action follows from this
preparation. T013/T014/T015 and setup/dispatch authorization remain incomplete.
