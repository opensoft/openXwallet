# T012S staging lease and final cleanup takeover plan

Status: isolated source candidate qualified; source acceptance and operational qualification separate
Date: 2026-11-15
Feature: 017-protected-runtime-qualification
Sole executable list: tasks.md, T012S and T012S01-T012S07

## Preparation commission and immutable source basis

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

## T012S as-built isolated source candidate

Brett subsequently commissioned T012S implementation/testing in isolation. This
supersedes preparation-only statements above without granting source acceptance,
publication, setup, dispatch or T012T-V. The factory post-merge CI readback is a
separate evidence gate; local results never substitute for it.

The opt-in hosted/lifecycle_store.py journal has explicit initialization, private
inode/schema checks, a chained append-only event log, separate retained commit
witness and high-water clock. It refuses missing/replaced/corrupt/rolled-back
state. A crash between database commit and witness publication is indeterminate;
there is no automatic repair, migration, restore or new registration fallback.
The witness is not protection against an administrator restoring both stores.

hosted/lifecycle.py freezes registered resources and the manager/actual worker
generation. The local reference also binds the producer and cleanup roles to the
same actual Linux PID namespace. Pre-start independent acknowledgement observes
the durable scheduler intake and selected scheduler process. Each subsequent staging
lease observation also rechecks that same scheduler generation before permitting start. Finalization derives
actual accepted configuration/policy; final preparation binds every static byte,
RunScope, generation, retention class and manifest. A distinct audit acknowledgement
and current scheduler observation precede the retained stage-release tombstone.
Final active-lease observations also recheck that selected scheduler generation;
closed-lease cleanup stays independently available when that scheduler dies.
Existing RunJanitor/RunLifecycle own the final lease/cleanup decision; their generic
implementations and the replay-state schema are unchanged.

hosted/lifecycle_service.py supplies explicit pinned-mTLS private registration,
cleanup and separate audit ports. The worker has no authority. Existing staging
constructs CleanupRegistration only when explicitly selected, retaining the original
Decision and shared private16 ledger. Finalization selects RegisteredStageReadback
as a local retained primary/audit-store capability under its original Decision;
it adds no relayed RPC and fits private12. A remote-only topology that adds calls
must return to a governed budget amendment; it cannot reset/join the ledger.
Nothing imports into an automatically activated service or protected dispatch.

The independent scheduler durably consumes one cleanup request before I/O. Every
resource action is separately claimed before mutation. A lost/unknown result is
read-only reconciliation, never another destructive send. Process cleanup uses
PIDFDs and observed start identity; HostAgent reaps only its own children so a
zombie cannot count as absent. Selected private-file writers share an ownership
fence, and credential cleanup uses the existing capability/retirement ledger.
An independent fresh attempt-bound audit must observe actual absence/revocation
and retained/shared generations. Unknown unpersisted generation, failed action or
missing audit stays owned/closed and unverified; none permits a replacement child.

The fixture runs three distinct local scheduler/primary/audit processes with
separate TLS identities, actual sandboxed inert workers, retained SQLite journals,
and a local credential-issuer/retirement service. It tests real runner os._exit
outside finally at four takeover boundaries. Same-user reference processes are
not deployed OS administration isolation. Total control-host loss, external
watchdogs, automatic VM expiry, cloud resource retirement and real GitHub App
credentials remain unqualified. Host-root and trusted writers bypassing the file
fence are trusted. No provider setup, protected dispatch or real credential is used.

## Publication correction boundary

PR #75 adds measured source corrections within T012S: durable run-file anchors,
retained/shared inode handles, a private provider epoch retained by the selected
source keeper, alias/control-root rejection, exact persisted-dead/prestart cleanup,
read-only primary-registration discovery after interrupted intake delivery, and
wall plus monotonic cleanup deadline narrowing. Run files share the initialized
anchor filesystem. A fresh path-only provider cannot reopen a prior epoch.
Missing anchors/retirement records, unknown consumed generations and replacement
resources stay preserved and unverified; no repair, mutation retry or new launch
is inferred. Scheduler reconcile-only ticks require a separate fresh audit.
The selected manifest permits at most three tokens under the unchanged private12
final cleanup limit. Source correction testing adds a deterministic process-exit
ESRCH control. The new measured collection is 105 lifecycle / 2,003 native / 2,308
full cases; corrected qualification passes as recorded in evidence.md.
Historical preparation and initial-review paragraphs predate these corrections;
evidence.md records the corrected qualification results.
