# T012S staging lease and final cleanup takeover plan

Status: prepared source plan; implementation not commissioned
Date: 2026-11-15
Feature: 017-protected-runtime-qualification
Sole executable list: tasks.md, T012S and T012S01-T012S07

## Commission and immutable source basis

Brett Heap source-ratified factory #1326 at dc159da61860 with adapter #71 at
74b4af51322b, directed ordered landing when green, then preparation of T012S.
Factory merged first as 0503c7bf36ea47c5c2b492bdf24ca11eed87347d; its tree equals
the predicted integration with main 5b636c767fcc. Adapter merged normally as
7042b295bc7229748e5b415e5f9ddb3f96a2467e, preserving the accepted tree exactly.
The factory missing-review exception applies because actor and author are both
brettheap; no failed required check was bypassed. The optional approval bootstrap
failure stays separately documented. Exact records are linked in evidence.md.

This is preparation under accepted factory changes `add-protected-runtime-hosting-issuance`,
`fix-hosted-protection-read-budget` and `fix-hosted-staging-refresh-budget`.
The original hosting/issuance source decision was factory #1317 with adapter #67.
No new factory capability or neutral contract is proposed here. A material change
to these accepted boundaries must return upstream before implementation. T012S
remains unchecked. T012T-V, T001/T013-T015, setup/dispatch and live qualification
remain separate gates. Feedback is deferred; no blocked/denied write is replayed.

## Purpose and source-only result

Connect the already acknowledged staging cleanup slot to a durable independent
scheduler, janitor and audit plane, then hand responsibility to one immutable
full-config-bound RunPlan for the identical generation. Launch and cleanup must
remain owned through every crash/lost-response boundary. A later isolated source
candidate may qualify local process/TLS/journal behavior; it cannot qualify deployed
systemd/cgroups, real provider credentials, infrastructure retirement or survival
of total control-host loss.

## Phase 0 research and current implementation gaps

Audit-table source paths are relative to scripts/workload_factory_binding_runtime/.

| Existing source | Reuse | Gap for T012S |
| --- | --- | --- |
| hosted/stage_controller.py | register_cleanup callback followed by independent StageAuthority acknowledgement before start; one durable consumed attempt | Actual durable registration service, scheduled cleanup and final takeover are not supplied |
| hosted/staging.py | Independent grant/lease observers with pinned origins/principals and exact stage scope | The acknowledgement is an observation, not an implemented janitor/scheduler |
| hosted/stage_store.py | Explicit init, private inode-bound store, retained rows/high-water clock, immutable unit/generation and six status decisions | No final-plan/takeover/scheduled-cleanup journal; strict current schema must not silently migrate/reset |
| hosted/host_agent.py | Recorded manager slot before start, real PID/start/session/boot/cgroup observations and parent-death fencing | close() is in-process convenience; status() requires live launch authority and cannot be the expired-run cleanup capability |
| hosted/finalization.py | Complete canonical configuration/policy derivation and independently accepted FinalizationBinding | Finalization alone grants no final lease, cleanup takeover or proof readiness |
| lifecycle.py | RunPlan/RunScope, frozen cleanup plans, independent RunJanitor/RunLifecycle/readback and cleanup clock | Hosted registration, durable attempt fencing and stage-to-final ownership linkage must be supplied |
| state.py | Identity-bound initialized replay/state access | Preserve its inode/schema/consumed state; never recycle it as a lifecycle journal or cleanup target |

Decision: add a separately initialized retained hosted lifecycle journal and selected
private adapters around these interfaces. Keep StageStore's accepted schema and
all default entrypoints unchanged. Append bindings and tombstones rather than
rewriting active stage or final plans. Opening never initializes a missing store.
Unsupported/corrupt/replaced/rolled-back state refuses. No automatic schema migration
or active-scope backup rollback is commissioned.

Rejected alternatives: finally-only cleanup cannot survive runner death; overwriting
a stage with a final plan loses provenance; using HostAgent.status after expiry
requires authority that should already have ended; a fresh launch ref or lease
renewal violates the consumed-attempt boundary; the same janitor's success response
cannot independently prove removal; read-then-delete cannot manufacture provider
conditional-generation semantics.

## Technical context and governing checks

Use existing Python, SQLite durability/locking, pinned private mTLS transports,
Linux process observations and source-selected dependency construction. The root
has no authored .specify/memory/constitution.md; the template is not a constitution
and this preparation neither creates one nor claims a constitution adoption/check.
Repo AGENTS.md, shared OpenSpec/Speckit mechanics and the accepted source decisions
remain controlling. Consumers pin; no owning neutral API or pin is edited.

Reuse the existing data-model and interface decisions in hosting-issuance-model.md
and contracts/hosting-issuance.md, refined only by the internal lifecycle mapping
below. No worker-supplied URL/path/resource, new runtime service-role string,
public route, activation flag or protected workflow change is in scope.

## Internal data model and responsibility transitions

These are planned private source records, not newly published wire contracts.
Each record has a closed bounded canonical representation, authenticated selected
writer/readback provenance, case/accepted-source/actual run-attempt/plan binding,
observed time/expiry and retained initialization identity.

| Record | Required binding | Durable rule |
| --- | --- | --- |
| Stage registration | Existing stage scope, cleanup ref, authenticated manager unit/invocation/boot and preallocated artifact/credential references; scheduler/janitor/auditor refs and fixed cleanup window | Acknowledge only after committed registration is independently readable; no final-config placeholder |
| Generation binding | Registration digest plus observed PID/start/session/cgroup, unit and exact resource generations | Append once after actual observation; a missing PID never permits replacement launch; retain pre-start unit responsibility |
| Final plan link | Accepted complete configuration/policy and FinalizationBinding, existing RunPlan digest/scope, stage/registration and same generation/resource-retention manifest | New immutable record; no destructive stage promotion or arbitrary hash acceptance |
| Takeover acknowledgement | Exact stage/final digests, same unit/generation/resources and independently observed durable final scheduler responsibility | Stage release requires this readback; unknown result leaves stage responsibility active |
| Cleanup attempt and audit | Fixed owner/scope/plan, per-resource generation, consumed action ref, fresh independent attempt-bound observation of absence/revocation/preservation | Retain attempted/unknown/completed state; absence of a reply is never permission to resend or report success |

Responsibility: registered-stage -> generation-bound-stage -> final-prepared ->
independently-acknowledged-final -> stage-released tombstone. Before the final
acknowledgement stage remains responsible. Overlap is permitted; a gap is not.
Concurrent stage/final schedulers share a durable per-resource fence so ownership
overlap never produces two destructive actions. A lost reply is indeterminate;
only same-reference read/reconciliation is automatic, with no replacement/renewal.
Late acknowledgements cannot release an expired/mismatched ownership generation.

All final lifecycle lease/cleanup/receipt handles remain the preallocated static
configuration-template values. No fifth late configuration field, arbitrary
host-selected reference or alternative cleanup root is allowed.

The final RunScope uses the real full-config digest; it differs from stage scope.
Do not simply relabel a ManagedResource.owner_scope_digest. The ownership registry
must independently corroborate the immutable stage-to-final link and actual resource
generation before final RunJanitor readback can authenticate that scope. Preserve
every run/retained/shared classification. Existing replay, dispatch, nonce, stage,
registration/takeover tombstones and evidence-retention state remain retained.

## Phase 1 integration and authority order

The task order lives only in tasks.md. The architecture is:

1. The selected registration adapter durably registers the unit/cleanup scope;
   independent acknowledgement remains mandatory before T012R's one start.
2. The independent scheduler consumes only retained acknowledged registrations.
   Its janitor can stop/revoke/remove exactly registered run generations after
   success, failure, cancel or expiry, without live worker/gate/config access.
3. Measured finalization supplies actual accepted complete bytes. Register a new
   immutable full-config RunPlan and final lease for that same generation.
4. A separately authenticated audit proves durable final scheduler registration
   and exact ownership. Retain stage cleanup until that acknowledgement is current.
5. After durable stage-release tombstone, final cleanup retains responsibility;
   unchanged full admission/proof still requires its independent current operation,
   custody, state and lifecycle authority. A takeover acknowledgement grants none.
6. Cleanup uses the original frozen plan plus separately bounded cleanup authority.
   It verifies run-resource absence/credential revocation and retained/shared
   preservation independently before reporting success. Missing readback refuses.

The scheduler, cleanup actor and audit reader must have separate actual identities/
capabilities from worker, gate and one another where independence is required.
Transport-selected principals, not request-body labels, establish identity. A
portable source fixture must use real separate processes and TLS roles; shared
Python objects alone do not establish that boundary.

## Deadlines, bounded recovery and conditional cleanup

All live operation checkpoints preserve their original wall/monotonic Decision,
earliest case/grant/hold/lease expiry and shared read ledger. Accepted allocations
stay ordinary3/13/private12, staging2-observations/26/private16, and finalization
6-observations/18-protection/28/private12. No third staging observation, budget join,
reset, deadline extension or implicit profile upgrade is allowed. Prove the later
path fits these limits; a conflict returns to governed factory/adapter amendment.

Existing staging recovery remains at most six read-only decisions within sixty
seconds and earlier scope expiry, persisted across reconstruction. Scheduler work
uses separately registered cleanup authority/clock and fixed cleanup_timeout <=60
seconds per attempt; it cannot renew the launch grant, proof window or run lease.
Expiry ends run/proof use but does not erase cleanup responsibility. Cleanup must
not acquire authority by copying an expired StageLaunchGrant or configuration.
An expired cleanup capability leaves cleanup unverified and requires an explicit
remedial authority decision; no silent retry loop or auto-renewal is permitted.

Consume each destructive action durably before I/O. Repeated scheduler ticks may
reconcile a known attempt/readback, not resend an ambiguous mutation. Use actual
generation-conditional process/credential controls and protected serialized owned
file resources. PID/name/path matching followed by an unguarded delete is insufficient.
The backend must provide and qualify its generation/ownership fence; unsupported
conditional provider operations stay unsupported. Never delete a whole resource
group or infer infrastructure retirement from process/file/credential cleanup.

A selected external watchdog outside all three proposed hosts is still required
for total control-host loss and automatic infrastructure expiry. This preparation
selects no watchdog, cloud resource, service account or provider. Isolated missing/
unsupported-capability tests must refuse those claims; source fixture survival of
runner death does not qualify control-host-loss cleanup or 24-hour VM expiry.

## Verification and publication boundary

See [acceptance design](hosting-lifecycle-acceptance.md) for H05/H11 controls and
interruption coverage, and [scoped consistency review](hosting-lifecycle-analysis.md)
for requirement/task coverage and source-preparation limits.
Preserve all 1,898 required baseline nodes, fingerprints/anchors and actual owning
proof positives. Measure new collection only after implementation, then review
explicit H05/H11 anchors/counts/fingerprints; no guessed or mutable expected counts.
Mandatory native conformance retains zero missing/deselected/skipped/xfail/XPASS or
non-passing cases. Run full ordered gates separately, then audit actual process,
credential and filesystem generations before removing exact fixture roots.

This preparation changes documents only and claims no new T012S test or runtime
result. A later owner commission is needed to implement T012S in isolation. Its
source candidate must then receive CI/local Codex review and source acceptance.
T012T-V, T013 selections/authorization, live T014 and consumer/human T015 remain
separate. No setup, dispatch, provider write, live factor/credential or feedback
submission is performed by planning or isolated source testing.
