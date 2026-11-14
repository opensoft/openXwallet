# T013 owner decision packet

Status: PREPARATION ONLY; no operational choice accepted; every setup/dispatch stage NOT GRANTED
Updated: 2026-11-14
Governance: factory `prepare-protected-runtime-qualification`; adapter feature 017

The [GitHub bootstrap design](github-bootstrap-proposal.md) was accepted in factory #1314 / adapter #64 and implemented, reviewed and source-ratified in [adapter #65](https://github.com/opensoft/openXwallet/pull/65#issuecomment-6881983735) at `ab34ff4ec4fe27d56c8fd09c99614785c23e760f`. #65 merged as `366533bed77293b096b0a7dbda61399ff5dbafe5` with matching ratified/merged tree `669a1b431f17d360fcf827a749a756e863ec9ed8`. T012L is complete; this T012M refresh hands operational decisions to T013 without choosing them.

## What is now accepted

The portable authority and GitHub bootstrap source adapters are accepted within their isolated source/fixture scope. #65 provides actual RSA/loopback TLS, separate bootstrap/proof policy, durable dispatch-attempt journal, broker/provider correlation and phase-separated readiness. It passed 1,641 local full tests and 1,339 mandatory native cases without skips; all runnable ratified-head hosted checks passed with local expert closure. [Evidence](evidence.md#2026-11-14-65-source-acceptance-and-t012m-handoff) records the source decision and equal-tree landing. No separate merge-triggered adapter CI run was emitted at readback.

The accepted source does not supply selected hosting, live provider claims/API evidence, operational issuance/worker exclusion or a protected-machine receipt. T001 remains owner-controlled and unchecked; T013/T014/T015 remain unchecked. Existing default bindings refuse before token access/outputs.

## Proposed selections for review, not operative configuration

These names make the proposal reviewable. They are not assigned resource IDs,
issued grants, existing services or accepted choices. No credential value belongs
in this packet. Missing IDs and secrets must not be filled from fixture material.

| Decision | Concrete candidate | Status and acceptance needed |
| --- | --- | --- |
| Case | `case:codexfactory-possession-qa-001`; one machine possession qualification, no domain action | PROPOSED; owner must accept purpose/case and accountable operator |
| Qualification repository | Existing `opensoft/openXwallet`, repo ID `1347887821`, owner ID `638385` | OBSERVED; no change or appointment is authorized |
| Caller | Existing workflow ID `417795073`, `.github/workflows/protected-runtime-qualification.yml`, same-commit local reusable | OBSERVED; final executing main SHA must be accepted after all later hosting source changes |
| New protected environment | `wallet-mfa-pilot-qa`; preserve existing `copilot` | PROPOSED, not created; distinct reviewer/dispatcher, reviewer IDs, self-review prevention, no admin bypass and exact main restriction require owner approval/readback |
| Target shape | Dedicated disposable nonproduction Linux deployment; separate administration for trusted services and worker | PROPOSED; provider/parent IDs/region/host/namespace, owners, network boundaries, resource and spend ceilings are UNSELECTED; no existing bench or production cluster is implied |
| Static approval | Independent operator-approved closed selection and one opaque preauthorization for the accepted case/window | UNSELECTED; no static digest, time window, preauthorization or operation grant is issued |
| GitHub correlation | Accepted #65 broker/journal/controller source records numeric provider-returned run ID and corroborates first attempt/source/job/phase/review | SOURCE ACCEPTED IN ISOLATION; actual fixed-version response/claims, authenticated callback/hosting, credential and durable-state deployment remain UNSELECTED/UNQUALIFIED |
| Admission client | Accepted opt-in bootstrap-purpose OIDC before environment and distinct protected-phase repeat; existing proof verifier unchanged | SOURCE ACCEPTED; full phase subjects, endpoint/CA/transport, live relying-party policy and worker/admin exclusion remain UNSELECTED; strict/reference profile stays separate |
| Main-update policy | Accepted source enum `coordinated` or `bounded-residual-exposure` | UNSELECTED; owner must approve actual coordination controls or precise residual-start exposure and credential boundaries; a label does not prevent main movement |
| Broker/App and reviewer separation | Repository-scoped Actions-write broker, separate read-only controller, originating human distinct from App actor | UNSELECTED installation/effective permission/credential resolver/issuance/revocation refs and administrator; original human cannot approve their App-dispatched run |
| Wallet/authority services | Accepted owning registry/custody source plus existing seven runtime roles; separate bootstrap/approval/readback capabilities | UNSELECTED service/admin/credential/trust/image refs; reference process names or separate keys prove no deployed isolation |
| Replay and authority stores | Explicitly provisioned private retained stores, independently retained initialization receipts; no reset of active scopes | UNSELECTED parent/storage/initialization/retention/recovery refs; backup rollback protection is not claimed |
| Janitor/audit | Independent service owners, exact-generation run cleanup, retained/shared preservation, expiry after runner death | UNSELECTED owners, scheduler/lease/plan/retention refs and deployment evidence |
| Issuer | Accepted fixed GitHub issuer/discovery/JWKS transport | Audience, complete immutable-ID subject, exact claims and deployed source/measurement policy remain UNSELECTED; prefix alone is insufficient |

## Preparation sequence and evidence required

| Gate | Required reviewable result | Effect on authority |
| --- | --- | --- |
| P1: source acceptance | Accepted factory #1314 design and adapter #65 head/merge/tree, full/source matrix, exact-head CI and local review | Complete for the bounded GitHub bootstrap and portable source adapters; grants no live use |
| P2: source/target decisions | Owner selects target/admin boundaries and approves a separate factory-governed hosting/authentication/qualify/cleanup/receipt source proposal | Not granted by this packet; source implementation can be commissioned separately from setup |
| P3: remaining hosting integration | Authenticated bounded approval/source/environment/materialization callbacks, chosen endpoints/issuance and operational bindings, live qualification/cleanup clients and protected-receipt source promotion; isolated negatives first | Separate governed source review/acceptance still needed; accepted #65 is reused, fixture profile is never relabeled operational |
| P4: bounded setup decision | Exact existing parent IDs/new resource names, actions, actors, UTC window, expiry, budget/resource ceilings and rollback owner | Separate explicit SETUP ONLY approval required; no dispatch/signing authority |
| P5: setup readback | Assigned IDs, effective protections, approved images/sources, actual client issuance/scope, worker denial, initialized stores, independent scheduler/janitor/audit readiness | Prerequisite only; no inferred dispatch permission |
| P6: one dispatch decision | Exact current accepted main source, workflow ID, case/static digest/preauthorization, dispatcher and expiry; no automatic retry | Separate explicit one-dispatch approval required |
| P7: actual-run authority | Authenticated provider-returned run and attempt, independent full config/grant and full-config-bound plan/lease before admission | Only then may the separately approved existing-resource qualification proceed |
| P8: qualification/cleanup | Real issuer/P01 and deployed G02/G03/L01, bounded owning proof and independent cleanup/readback; human/domain gates separate | T014 remains not performed; no consumer acceptance or pin/lock promotion |

The accepted source still cannot eliminate the main-update race: the dispatch
API does not atomically pin main to a SHA. Post-response source verification can
refuse authority but cannot prevent already-started workflow code. A reviewed
coordination/control policy or explicit owner acceptance of bounded residual
exposure is mandatory before that route is selected; no rule change/freeze is
authorized by this packet.

The full action/resource decision remains in [scoped authorization](scoped-authorization.md).
No runnable setup or dispatch command, executable config, grant, image pin or
credential is produced here. P2/P3 cannot be skipped by provisioning reference
fixtures. Stages P4/P6 require distinct owner decisions; this instruction grants
neither. T013 is not complete merely because this decision packet is prepared.

## Owner response needed later

Choose the nonproduction target and its existing immutable parent references;
name the accountable setup/rollback, supervisor/gate/custody, bootstrap/controller,
state, janitor/audit administrators and distinct dispatcher/reviewer; set resource,
spend and time ceilings; and commission the separate source proposal needed for
P3. Provide only non-secret references. The new environment ID, initialization
receipts and effective issued scopes can only be read back after separately
authorized setup and must not be guessed now. Approval of this document alone is
not setup or dispatch approval.

Read-only inspection at `2026-11-14T18:11:54.230954+00:00` still finds only `copilot` (ID `20677426348`),
with no protection rules and admin bypass enabled; it is preserved and ineligible.
Both protected workflows have zero runs. Workflow token defaults remain read-only,
PR approval disabled; OIDC settings remain default/immutable-ID with prefix
`repo:opensoft@638385/openXwallet@1347887821`. No token was minted to inspect
claims, no App/credential/federation/permission was changed, and no write endpoint
was tested. Feedback stays deferred; neither historical blocked write was replayed.
