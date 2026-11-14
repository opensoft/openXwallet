# GitHub bootstrap authentication source and operational handoff

Status: source accepted in #65; T012M handoff complete; T013 hosting/issuance/setup/dispatch unapproved
Updated: 2026-11-14
Owner boundary: factory grammar; adapter feature 017 implementation; no neutral API promotion

The factory-owned [design](github-bootstrap-proposal.md) was source-ratified in #1314 / adapter #64. Subsequent isolated T012H–K implementation and T012L review/acceptance landed in #65 at merge `366533bed77293b096b0a7dbda61399ff5dbafe5`, with tree equal to ratified head `ab34ff4ec4fe27d56c8fd09c99614785c23e760f`. [Evidence](evidence.md#2026-11-14-65-source-acceptance-and-t012m-handoff) records the owner decision, checks and scope. T012M reconciles accepted source here; it grants no live operation.

## Three independently established facts

1. A current independently approved static selection/case/window authorizes one dispatch.
2. The actual GitHub run/first attempt is unambiguously correlated with the consumed approved dispatch.
3. The phase-specific admission client/controller and every authority/readback callback are authenticated outside worker administration.

Accepted source implements these checks with actual local RSA/TLS and deterministic provider doubles. It does not supply deployed endpoints, credential issuers, live claims/API observations or administrative/OS independence. The earlier portable `isolated-fixture` profile remains loopback-only and cannot be relabeled operational. Default bindings still refuse before token access or environment outputs.

## Accepted broker and current provider correlation

`github_bootstrap/` supplies the separate verifier, selected token-request client, private bounded HTTPS child, initialized journal, broker, read-only provider, accepted graph checks, controller and readiness session. Constructor-supplied callbacks/endpoints are trusted hosting capabilities, not worker input. Callbacks must authenticate current authority/source/protection/materialization and enforce the passed deadline; post-call checks do not interrupt a hung arbitrary callback.

The broker journals the immutable approval commitment, exact request bytes, case/window/source/actor scope and one consumed attempt before credential resolution or external I/O. It rechecks source/current approval/window/revocation after TLS immediately before send, passes remaining I/O budgets into journal operations and checks the Decision after return. Concurrent clients, restarts, crash-before-I/O, cancellation and lost/insufficient response cannot retry/reset or free the consumed attempt. Late correlation persistence refuses success while retaining consumption.

The selected API version is `2026-03-10`: dispatch body has only `ref` and `inputs`; the source requires status 200 and numeric `workflow_run_id`. Exactly three inputs remain `accepted_commit`, `selection_digest`, `preauthorization_ref`; no legacy `return_run_details` flag is sent. A legacy/unexpected 204, missing/ambiguous response or changed source refuses. No newest-run search, inferred/predicted ID or response-URL fetch is supported. These versioned behaviors are source-tested from documented schemas, not live-provider qualified. See the [version-pinned workflow API](https://docs.github.com/en/rest/actions/workflows?apiVersion=2026-03-10#create-a-workflow-dispatch-event).

The controller independently checks the retained journal and signed purpose/phase identity against fixed API/repository run, first-attempt jobs, reusable source, actor and review facts. Explicit documented selected-main path representations are mapped with exact ref/SHA agreement, not arbitrary normalization. Current environment/protection, original-human reviewer eligibility and final run/authority corroboration repeat after blocking reads. At most four API reads and two 100-job pages are permitted per decision; exhausting the budget refuses. See [workflow runs](https://docs.github.com/en/rest/actions/workflow-runs#get-a-workflow-run) and [attempt jobs](https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run-attempt).

The broker alone may resolve the eventual repository-limited Actions-write credential; the controller/readers remain Actions-read. Provider permission is broader than one workflow invocation. T013 must select installation, effective scope, issuance/revocation, trusted resolver and administrators and explicitly accept that residual capability. The broker App actor cannot hide the original human; a human cannot approve their own App-dispatched run. Unknown outcomes remain consumed/indeterminate for separately scoped reconciliation/cancellation, never automatic redispatch.

## Accepted phases and still-unselected identity issuance

The opt-in profile is `openxfactory-github-bootstrap-internal-v1`. Its preflight job may obtain only the intended bootstrap-purpose identity under independently selected phase policy before the environment-bound job. The protected job repeats bootstrap admission through its distinct intrinsic phase route after environment approval. Bootstrap audience `urn:opensoft:openxfactory:bootstrap-admission:v1` is source accepted; actual complete subjects and the distinct protected-proof audience remain unselected deployment inputs.

The existing proof verifier retains every protected claim/environment requirement. Signature-valid audience-only and environment-only negatives, with known-good positives and crypto-sensitive controls, refuse before custody. A bootstrap token is admission identity, never dispatch, setup, signing or human approval authority. Job `id-token: write` is not audience-limited: T013 must review actual relying-party trusts for every unprotected identity and keep request capability/tokens outside worker access. Do not request a token merely to discover expected claims. The immutable-ID prefix observed in repository settings is not an approved complete subject.

The strict/reference profile stays separate. Adopting another preflight client identity route would need its own governed source decision; source acceptance of this opt-in route selects no stored secret, self-hosted runner or alternative control plane.

## Main-update residual exposure remains an owner decision

The API dispatch `ref: main` is not an atomic SHA pin. Before-send and final provider/source checks can withhold wallet authority, but cannot undo a created run or guarantee that changed code never started. Default live use therefore remains blocked. Accepted source admits only `coordinated` or `bounded-residual-exposure` policy values; neither is selected by this packet and an enum label implements no repository control.

For `coordinated`, the operator must specify the actual main-update coordination/control, accountable owner, covered source/window and fresh independent control readback. For `bounded-residual-exposure`, the owner must explicitly accept the precise possibility of unaccepted workflow code starting, time/source/credential limits, relying-party exposure and reconciliation/cancellation ownership. No freeze, repository-rule change, tag fallback or relaxed main restriction is authorized. If zero possibility of unaccepted workflow execution is required, this API-only route cannot satisfy it and needs an upstream design decision.

This refresh and any later source/documentation merge also change the possible executing SHA. Retained source acceptance does not approve a floating main ref or select an execution `accepted_commit`; reconcile and accept the actual final caller/reusable SHA and complete source set before any separately authorized dispatch.

## T013 handoff and remaining source/operational gates

[Operational inputs](operational-inputs.md), [decision record](t013-decision-record.md) and [scoped authority](scoped-authorization.md) contain the actionable decision categories. Accepted #65 need not be re-proposed as unimplemented. Remaining governed source integration must select and qualify actual bounded authenticated callbacks, controller/token transport/credential issuance and operational bindings, live qualifier/cleanup clients and protected-machine receipt promotion. No listener, App setup, credential provisioner, default activation switch or deployed host is supplied by #65.

T013 still needs the exact nonproduction target/parents/admins, original human/App actor/eligible reviewers, complete phase subjects/proof audience and relying-party policy, effective environment protection, seven runtime service identities/trust/issuance, initialized retained journal/authority/replay stores, independent scheduler/janitor/cleanup readback, source-update policy and bounded case/budget/window/resource scope. Only non-secret references belong in the packet; fixture IDs/keys are never operational selections.

Setup, one dispatch, actual run/attempt config/grant/lease binding and exact-generation cleanup require their separate explicit scope/authority. Accepted source supports only run attempt 1; reruns do not inherit authorization. Missing live facts remain blocked/not-performed. T001/T013/T014/T015 stay unchecked. No live token, write endpoint, setup or dispatch was tested; feedback remains deferred and neither historical blocked write is replayed.
