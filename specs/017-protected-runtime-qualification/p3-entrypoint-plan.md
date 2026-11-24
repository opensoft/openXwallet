# T013P08 source-selected companion and packaging subplan

Status: prepared subplan after accepted P07 and verified main source CI.
P08 implementation is not commissioned.
Date: 2026-11-24, America/La_Paz

## Parent source and authority

Brett Heap source-ratified openXwallet #105 at
f087ef06f13c77e45d319406cf84a14d14b34264 and directed landing when green,
independent main CI verification, then preparation of existing T013P08. Normal
merge 2b1608513339f8fe09045f4e872cd5e61d86c200 has the identical ratified tree
d29040759a212b26f8f65a876d152bcff7a33160.

The [independent main source run](https://github.com/opensoft/openXwallet/actions/runs/45464492415)
now passes all five effective jobs at this exact merge. The [parent receipt](p3-entrypoint-parent-main-qualification.json)
records 3,731 full parents plus 11 subtests, all 3,309 native cases, the disjoint
3,730+1 coverage partition, all 103 production files and six unchanged Sonar
conditions. Fresh GitHub/Sonar readback agrees on the merge; the original August
27 manual baseline remains intact. This is an as-of check, not a permanence claim.

The original coverage job failed one P05 healthy initial measurement read before
its namespace mutation; its cause remains unknown. One explicitly approved
coverage/dependent-analysis retry passed at unchanged source, tests and bounds.
Original passing source artifacts were retained. No additional retry is inferred.

Only P08 preparation is commissioned. The sole executable task list remains
[tasks.md](tasks.md). P08/P09 implementation, T001/T013/T014/T015, role appointments,
setup, dispatch and independent human/consumer acceptance remain separate.
Feedback is deferred; historical blocked writes remain unreplayed.

## Scope and normative basis

Compose accepted P03-P07 capabilities through an explicit reviewed companion
source path for the first codeXfactory pilot. The fixed issuance/admission target
remains opensoft/openXwallet; the consumer name does not broaden that target.

Factory R02 permits a separate source-selected reviewed and exact-source-accepted
route while preserving neutral APIs, three manual inputs, seven runtime services,
eight source roles, old static/full/report grammars and unconditional original
refusal. R03 requires real owning-kernel observations, independently corroborated
complete canonical configuration/policy and unchanged full admission. R07 requires
separate runtime and infrastructure outcomes. R11 preserves all original budgets,
clocks and body caps. R12 preserves the source/live/consumer distinction.

Canonical references are the accepted factory composition spec, the
[P3 plan](p3-azure-composition-plan.md), [interfaces](contracts/p3-azure-composition.md),
[research](p3-azure-composition-research.md), [model](p3-azure-composition-data-model.md)
and [acceptance matrix](p3-azure-composition-acceptance.md). This subplan refines
implementation within those boundaries; it adds no serialized contract.

Use the current accepted P07 [accounting subplan](p3-retirement-accounting-plan.md)
and [implementation record](p3-retirement-implementation.md) for infrastructure
registration, cleanup and observation. Factory #1365 with adapter #104 accepted
openxfactory-infrastructure-retirement-accounting-internal-v1, commitment
sha256:21b62c2621f3d98e5358c1ba4c5b0345a0237d10cfa52e59bea122487688979e.
Every pool keeps that accepted original owner, allocation, clock and debit policy.

## Technical context and research decisions

There is deliberately no feature 017 local constitution. Follow repository AGENTS,
the accepted factory requirements and the existing shared workflow; do not import
the unrelated usage-control constitution or create a replacement constitution.

| Decision | Actual source constraint | Selected source design |
| --- | --- | --- |
| Separate companion | Old scripts/prepare-protected-runtime.py calls unconditional workflow.operational_bindings refusal | Add reviewed scripts/prepare-azure-protected-runtime.py and azure_composition/entrypoint.py; retain old CLI and default refusal |
| Closed graph selection | github_bootstrap/graph.py PREPARE fixes the old command; Controller, staging and GitHub readback select its validators | Separate closed companion validation selected only through trusted source construction; preserve old validators/default semantics |
| Genuine remote handoff | P05 RemoteFinalizer returns sealed VerifiedRemote, without full admission | Add a narrowly trusted owner-module handoff and independent authorizer that legitimately produce existing FinalizationBinding/FinalizedPlan |
| Owning-kernel lifecycle | HostedLifecycle.prepare_final checks the actual registered seven-field generation | Reuse existing LifecycleServer load_final callback and prepare operation beside the worker kernel |
| Existing proof and report | admit_finalized and Qualifier require exact existing types and actual authorities | Delegate unchanged full admission, RuntimeBridge, Qualifier and protected report builder after all checks |
| Independent infrastructure result | P07 Reconciler/Observer retain original separate scopes and pools | Register actual run only when its authenticated final-scope facts exist; require both runtime cleanup and separate infrastructure receipt |
| Immutable packaging | deploy/qa-wallet-mfa is absent; ephemeral creation is consume-before-send | Package reviewed artifacts and launch wiring; preserve the namespace/provider/reconciler path for all fourteen ephemeral resources |

The source choices are resolved for planning. Concrete live endpoints, IDs,
credentials, role confirmations, exclusions, image build, state initialization,
pricing and UTC windows remain explicit later operator gates.

## First implementation eligibility gates

These gates belong to existing T013P08. They have not been executed during
preparation. A partial P05 positive or old report does not close either gate.

### Gate A: closed source route and admission graph

Prove the companion route can be selected by its accepted source while old
entrypoints retain their exact refusal behavior. Keep the existing caller and
reusable workflow filenames, relative same-commit use, immutable actions,
checkout source, two job classes, phase order, protected environment, job-scoped
OIDC, five/fifteen-minute caps and unconditional cleanup step.

Keep exactly accepted_commit, selection_digest and preauthorization_ref as the
three manual inputs. Runtime roles remain records, challenge, registry, custody,
supervisor, worker_channel and janitor. Source roles remain factory_profile,
adapter, wallet_contracts, wallet_code, worker, supervisor, caller_workflow and
reusable_workflow.

The future reusable route may select only the literal reviewed Azure companion
command. Propagate that source choice through github_bootstrap/graph.py,
github_bootstrap/controller.py, hosted/staging.py and hosted/github_readback.py,
and all affected authenticated callers. Preserve old graph validators. A shared
private structural helper is acceptable only with distinct fixed old/new command
policies. An arbitrary path, callback string, boolean/profile selector, added
input, environment switch, data file or plugin registry cannot choose a route.

Test actual authenticated source/phase paths, including old/new cross-route and
mixed-command refusal, same-commit mismatches and unchanged old default behavior.
Production companion construction remains unselected/refusing before outputs or
OIDC until its separate concrete hosting and operational decisions are approved.

### Gate B: complete-byte handoff to unchanged full qualification

Use a selected RemoteFinalizer to obtain its current exact opaque VerifiedRemote.
The new consumption operation is owned by azure_composition/remote_evidence.py,
which owns the result seal and existing shared-ledger/binding guard. It must bind
the selected finalizer, private complete bytes, seven-field generation,
provenance, original decision and frozen bindings. Independently corroborate actual plan/case/source/run/attempt,
authority principal, complete final bytes and current actual-run authorization.
Do not countersign candidate fields or convert caller-built JSON/dictionaries.

Retain one original attempt/consumption state before possible authority I/O.
Recheck scope/bindings before and after blocking work. Gate B must identify and
verify the exact original staging_policy.launch_ref, retained store identity and
HostedLifecycle registration/final-plan state it reuses. The existing
HostedLifecycle.prepare_final appends final-plan only after its actual checks;
constructor success itself supplies no authority. A private one-shot capability
must not be represented as durable cross-process exactly-once state. Loss of the
original capability or an ambiguous original attempt refuses rather than
reconstructing a new approval. If existing retained references cannot provide the
required semantics, the gate fails for a governed amendment. No new journal
grammar, initialization, restore, rollback or replay grant is supplied here.

Only after those checks may the trusted producer construct the existing exact
FinalizationBinding and FinalizedPlan. Bind the authenticated generation digest,
complete configuration/policy digests, authority principal, plan/case/source/run/
attempt, observation time and clipped expiry. The existing 60-second binding ceiling
and every earlier authority deadline remain bounds. The producer authority must
match the independently selected final authority and the actual
HostedLifecycle.final_authority_principal. A new private helper/accessor
may expose a sealed consumption operation; direct use of loose private fields is
not an authenticated handoff.

The generation projection already agrees across the local and remote code:
launch_ref, host_ref, incarnation_ref, boot_id, invocation_ref, pid and start_time.
LifecycleServer's existing load_final callback and prepare operation must reach
register_finalized_lifecycle and HostedLifecycle.prepare_final on the real owning
kernel. Its actual registered generation, current resources, templates, authority,
plan and scope checks remain intact. A remote PID never becomes a local
ProcessLaunch/LaunchObservation/MeasurementBindings stand-in.

Construct the existing exact QualificationBindings, RuntimeBridge and Qualifier,
then delegate through the unchanged qualification path. Its existing
admit_finalized call precedes proof; do not add an unaccounted standalone
admission pass. Keep all old full admission, proof, replay, barrier, worker denial
and operational-origin checks. Keep the
accepted static/full/report fields unchanged. A new report/profile or loosened
exact-type check is not an implementation shortcut.

All handoff/authority work, including physical nested I/O, stays on its original
finalization Decision and shared ledger. A separately approved original
qualification Decision cannot renew expired finalization or pay finalization
work. Retain bridge.lifecycle is workflow.lifecycle; with FinalLifecyclePorts,
bindings.decision must be the exact ports.operation object. Matching clock
values or constructing an equivalent new Decision does not satisfy that identity. P07 cleanup and observation retain their accepted disjoint original pools.
A complete connected positive must fit all existing caps before proceeding to
package integration; do not guess call counts or omit observations.

## Future source footprint

The sole T013P08 row owns the companion CLI/module, reviewed package/workflow
route and substantive test_azure_entrypoint.py coverage. Reconcile its proposed
paths with the actual sealed-result and graph consumers: remote_evidence.py owns
the proposed consumption operation; graph.py, controller.py, hosted/staging.py
and hosted/github_readback.py own the closed authenticated route seams. Retain
applicable test_azure_measurement.py controls and all old workflow identities.
Update matrix_contract.py only from actual new case collection and fingerprints;
preserve every old identity, fingerprint and anchor.
Constructing existing FinalizationBinding/FinalizedPlan does not inherently
require changing their definitions or hosted/finalization.py. Existing lifecycle
RPC operations and owning-kernel checks remain the integration seam. This is a
file footprint for that row, not an additional executable task list.

## Connected ordering and cleanup

The source route validates the existing DispatchContext and exact source before
selecting capabilities. Preflight and protected-admission use the accepted
phase-specific RunnerCapture/AdmissionClient flow; ready/environment outputs
follow successful independent admission. Protected approval requires fresh
protected admission. Source selection supplies no setup or proof authority.

Qualification uses pre-existing approved/initialized hosting and namespace state,
then the trusted complete-byte handoff, original lifecycle preparation, unchanged
full admission and owning proof/qualification. Register the P07 actual-run link
only after independently authenticated actual-run/final-scope facts exist, and
before operations requiring that run cleanup scope. Partial setup/expiry/abort
retains its original setup-cleanup authority without fabricated final-run facts.

The cleanup phase reconciles the original runtime reference through the accepted
audit-only route; it does not resend a possibly consumed cleanup mutation. P07's
separate observer provides its own infrastructure receipt. Preserve both existing
artifacts independently; do not add cloud fields to old RunPlan/report or invent
an aggregate public profile. Pending, incomplete, late or unavailable evidence
prevents overall deployment acceptance. The external watchdog remains necessary
when the runner cannot execute its cleanup step.

## Reviewed packaging boundary

Future deploy/qa-wallet-mfa packaging contains immutable reviewed source/service
artifacts, deterministic checksums and explicit launch/ownership wiring under
existing adapter/worker/supervisor source selections. Source installation,
service activation, image building and retained-state initialization remain
separate acts. No filled operational parameter, credential, grant or state-reset
file is generated from nominees or source acceptance.

Retain reference-posix-session-v1 workload-manager semantics. Packaging a trusted
service does not replace the workload manager with systemd/cgroup semantics.
Protected local helpers stay on the owning worker kernel and exclude workload UID.

The fourteen-resource ephemeral graph must still reserve/consume before its sole
provider send and retire through the accepted per-kind original-operation path.
A bulk ARM/Bicep deployment would bypass that ownership model. Retained foundation
setup and service installation need their own operator-approved scope and remain
outside ephemeral creation/retirement. Preserve the twelve retained ARM objects,
three retained state objects and all permanent namespace tombstones.

Inventory each required port as actual source, isolated reference capability or
unselected live service. A missing concrete adapter is not made implemented by
naming a role/reference. Real provider SDK behavior, effective Azure exclusion,
service independence and actual deployment remain later live qualification gates.

## Verification and amendment boundary

Use real local process/kernel/TLS/crypto/retained-state controls with isolated
provider/storage ports. First demonstrate the full connected positive through
both eligibility gates and both cleanup scopes. Then independently vary complete
bytes, source/plan/case/run/attempt, generation, authority, stale/consumed approval,
changed bindings, missing original registration and deadline/body/call exhaustion.
Keep a genuine healthy service positive beside corresponding valid worker denial.

Preserve every prior full/native identity, module fingerprint and anchor. Measure
new counts after implementation; do not forecast case totals. Validate package
content and graph through real consumer paths rather than permissive string
matching or test-only type overrides. No source result is promoted to deployed,
protected human-factor or consumer acceptance.

If the complete handoff needs a changed serialized profile, role/input/claim,
local exact type, response cap, budget or new authority semantics, stop at that
eligibility failure and prepare a governed factory/adapter amendment. The accepted
R02 route itself requires no amendment merely for new internal source wiring.

Preparation validation checks source/contract pins, YAML, plain/strict house
validation, pinned OpenSpec corpus, feature prerequisites, relative links, scope
and checkbox consistency, and unchanged runtime/tests/matrix/workflow/lock blobs.
It executes no new runtime test or live request. P08 and P09 stay unchecked.