# T013P07: bounded external infrastructure retirement

Status: preparation only; isolated implementation requires a later commission
Date: 2026-11-23, America/La_Paz
Feature: 017-protected-runtime-qualification
Sole implementation row: [tasks.md](tasks.md), T013P07
Scope: first codeXfactory machine pilot; no operational grant

## Authority and qualified parent

Brett Heap source-ratified [openXwallet #103](https://github.com/opensoft/openXwallet/pull/103)
at `6796cccfc5912d9ddcf05a8cc5c694e67cb88c33` and directed normal landing,
independent main verification, then T013P07 preparation. Normal squash merge
`4b64db85fc28881656ef7e73c0c4a1dd760c9078` has the identical tree
`5bec465200373c2f83bc7cbbbda40dd4d944958a`.

[Main CI](https://github.com/opensoft/openXwallet/actions/runs/45135684248)
passes all five effective jobs. Its four source jobs pass 3,581 full parent cases
plus 11 subtests and all 3,159 mandatory native cases, with zero failures, errors
or skips. Attempt 1 failed before Sonar analysis because the pinned scanner
binary download returned HTTP403. A retry of only that failed job succeeded;
the source jobs and their original execution timestamps/artifacts were retained.
No source, scanner, profile, threshold, permission or job-cap change was used.
The main analysis is `0460e2be-23a2-403e-bfde-0a33f7fcb24f` at that merge.
All six unchanged conditions pass: coverage 87.5%, duplication 0.1%, hotspot
review 100% and all three ratings 1. The original August 27 manual baseline remains.
The [parent receipt](p3-retirement-parent-main-qualification.json) records the
final source/artifact/readback checks. It is an as-of historical source record,
not a runtime evidence profile, operational input or permanent freshness guarantee.
The earlier [P06 parent receipt](p3-parent-main-qualification.json) remains unchanged.

This prepares the existing row; it does not implement or complete it. P08/P09,
T001/T013/T014/T015, operational role confirmation, consumer058 T002 and independent
human/domain acceptance remain separate. Setup/dispatch are unauthorized;
feedback is deferred and historical blocked writes remain unreplayed.

T013P07 is a source task. The separate operational phase P7 is later actual-run
final-scope authority. Completing a source task cannot execute that operational phase.

## Outcome and ownership

Prepare an independently administered reconciler whose registration, permanent
namespace and original-operation records survive loss of control/gate/worker.
It closes write/run admission, retires only enumerated ephemeral generations,
and obtains independently authenticated absence, credential revocation and
retained/shared preservation observations. It produces the factory-owned setup
or run retirement receipt, separately from existing runtime cleanup evidence.
Overall deployed acceptance requires both scopes; neither substitutes for the other.

The accepted factory [R07/R09/R10 requirements](https://github.com/opensoft/openXfactory/blob/c2dfbbcc6fa6965fcde18661bddca1dac7128d47/openspec/changes/add-protected-runtime-azure-composition/specs/protected-runtime-azure-composition/spec.md)
and [closed composition boundary](https://github.com/opensoft/openXfactory/blob/c2dfbbcc6fa6965fcde18661bddca1dac7128d47/openspec/changes/add-protected-runtime-azure-composition/supporting-docs/composition-boundary.md)
remain authoritative, with R11/R12 for bounds and qualification. That boundary's
blob `52772772d47bbdd91bdd377d39aa4663c0fac627` is unchanged at accepted factory
#1359 `15d6328ba428`. This plan refines internal source wiring; it creates no
neutral contract, new receipt field, public endpoint, manual input or service role.
The [P3 acceptance matrix](p3-azure-composition-acceptance.md) remains the traceability
owner; [tasks.md](tasks.md) remains the only implementation list.

## Existing ports and trust

| Existing surface | Preserved use and limitation |
| --- | --- |
| `selection.reservation`, `provisioned`, `final_link` | Canonical closed immutable records; parsing/constructing a Record authenticates no service or authority |
| `Namespace` / `Snapshot` | Authenticated linearizable conditional state, non-reused ETags, consumed attempts and permanent tombstones; no initialization, reset, restore, deletion or repair of missing state |
| `Provider`, `Generation`, `Operation`, immutable receipts and fencing ports | Own incarnation/API/dependency checks and original-operation reconciliation; public dataclass construction is not provenance |
| `selection.retirement` / `RetirementAuthority` | Pure closed projection and derived outcome from independent current assessments; request flags or a matching digest cannot authenticate those assessments |
| Existing runtime lifecycle and private credential retirement | Separate actual process/credential cleanup and refusal readback; no VM-as-process, disk-as-file or old-report extension |
| Original `Decision` and `ReadBudget` | Earliest wall/monotonic expiry and retained consumption; nested callbacks, retries, triggers or reports cannot replace or reset them |

The future trusted source constructor selects registration, namespace, provider,
receipt, admission/fence and independent observation capabilities. It supplies
already initialized service/state references and the exact approved source/case/
owner/generation scope. Workers, request bodies, environment variables, files and
plugins cannot select or self-approve them. Actual service identities, endpoints,
RBAC exclusions, UTC windows and retained-state initialization remain later owner gates.

## Eligibility before dependent implementation

Two existing seams must be resolved explicitly before claiming a complete P07 positive.
These are source compatibility gates, not permission to bypass an old refusal.

**Cleanup authority versus setup scope.** `Namespace._setup`/`transition` and
`Provider._request`/`_terminal`/`observe`/`deletion_complete` currently clip mutations
and provider requests to the frozen reservation's setup window. Their present
per-resource semantics do not establish setup-expiry or later run cleanup.
Use narrowly additive, source-selected cleanup-capability paths in the owning
`namespace.py` and `provider.py` if needed to realize the already accepted separate
setup-rollback/run-cleanup authority. Bind the original registration, exact reserved
set/incarnations, consumed attempts, original cleanup deadline and current fence.
Preserve every existing setup-window refusal. Never rewrite a reservation/window,
reconstruct a broader Record, borrow creation consumption as delete authority,
change a parser/profile, or enter a new runtime phase as a fallback.
A separately current read-only observer needs an actual read-only path; calling
an expired setup-bound Provider method cannot establish that capability.

**Complete-graph budget fit.** The accepted P03 six-kind control
`test_all_six_kinds_retire_in_approved_order_and_preserve_excluded_image` creates
a fresh Decision for each resource. It proves those per-kind semantics, not a
whole P07 registration/reconciliation/receipt fitting one original phase budget.
Before dependent code, account for the complete first-pilot graph and every nested
registration/state/provider/fence/receipt/audit call, original clocks, body caps
and counters. Demonstrate a fitting substantive positive. Do not obtain a pass
by starting fresh per-resource/timer Decisions, upgrading to another phase's
private budget, omitting observations, inventing aggregate provenance or treating
unmetered backend calls as free. A partial graph does not qualify the full selected case.

An additive implementation of already accepted internal authority semantics stays
with its owning adapter row. If the unchanged contracts, phases, supported provider
semantics or caps cannot express the complete positive, retain the measured blocker
and prepare the governed factory/adapter amendment before dependent implementation.
Preparation and a later isolated commission cannot waive this eligibility gate.
No such amendment, new cap or unsupported provider capability is accepted here.

## Registration, triggers and retained state

Registration must durably bind the exact canonical reservation and independently
approved setup rollback/expiry scope before its acknowledgement can permit any
future lifecycle ownership handoff. A provisioned envelope and actual P7 final
link may be registered later only as their genuine immutable same-deployment
facts become available. Do not put static/full/run facts or guessed incarnations
in reservation-only state; do not create a backwards digest commitment.

The external service owns its authenticated durable registration and conditional
trigger/action state independently of the three hosts. Only that service has
raw backend write credentials. No product initializer, missing-state repair,
namespace extension, overwrite/delete or garbage collector is introduced.
The test harness may initialize explicitly owned synthetic storage doubles;
that is not initialization of a live service or a retained runtime ledger.

Concurrent abort/expiry/control-loss/timer deliveries must converge on the same
registered ownership and original resource attempt. A durable conditional claim
precedes any destructive send. A timer firing or scheduling acknowledgement is
not cleanup authority or completion. Duplicate deliveries cannot invent a new
retirement attempt, retry a consumed send or reopen a permanent name.

Preserve crash boundaries before/after durable claim, before/after the sole send,
after provider effect but before response/receipt, and before namespace acknowledgement.
Reconstruction uses retained authenticated original records. Missing/ambiguous
state quarantines scope; it cannot be reconstructed from caller memory or a fixture
pass flag. If bounded continuation of original authority cannot be proven, refuse
mutation and retain an honest incomplete result. Current separately authorized
read-only reconciliation may inspect original operations; it cannot renew a
cleanup/proof Decision, reset consumed scope or trigger another mutation.

## Per-kind retirement and preservation

First close write/run admission and prove the exact controller fence, sole ordinary
writer, no pending create/update and the original admitted incarnation. Tags,
numeric addresses and resource names are not generation identity. A legal bypass
writer or replacement between observation and send invalidates eligibility;
never pretend that a GUID check makes Azure deletion atomic or adds an undocumented CAS.

Reuse the accepted provider table and supported API checks: VM `vmId` with
Compute 2025-04-01; ephemeral OS disk `uniqueId` with Compute 2025-01-02; NIC/public-IP/
VNet/NSG own `resourceGuid` with Network 2026-01-01. Source doubles cannot establish
live API support; no automatic version fallback is allowed.
Retire selected VMs first; each OS disk/NIC follows its required VM absence;
public IP and VNet follow their required NICs; NSG follows the cleared NIC/VNet
associations. Independently check each dependency and own generation at the
relevant boundary, including explicit Detach and only the approved subnet/association set.

Never target an RG, standalone subnet, force/cascade operation, foreign/shared
resource, retained data disk, image, vault, storage, watchdog identity/state or
evidence store. Preserve the two retained control/gate data disks and accepted
image/old reader bounds; no P07 widening of the S1 host/disk selection.
Terminal deletion plus independent current absence is required. HTTP202/204,
a timer schedule, a namespace label or a bare404 cannot substitute for it.
The accepted already-absent/no-send case needs an authenticated controller
no-send/absence record, not an invented provider operation identifier.
Permanent namespace tombstones and consumed attempts survive cleanup and evidence expiry.

## Closed receipt and late observation

| Phase/fact | Required projection |
| --- | --- |
| Partial setup, setup failure/expiry or predispatch abort before actual P7 | Setup variant binds original reservation/setup-cleanup authority; final link, provisioned digest and run/static/full facts remain absent |
| Actual run after P7 | Run variant additionally binds the genuine provisioned digest/final-scope link and original registered run/attempt/lease cleanup scope |
| Never-created resource | `not-created` only with authenticated proof that creation was never permitted/sent or definitively ended without effect; no incarnation or operation invented |
| Known absent generation | Exact actual incarnation and original retirement or authenticated no-send outcome; independent absence and no pending create/replacement |
| Unknown, pending or refused fact | Use the existing closed pending/indeterminate/failed union and exact reason; only genuinely known optional refs, never null placeholders |

Emit exactly one result per original reserved ephemeral resource, in reservation
order, with exact set equality and canonical complete bytes at the existing 16 KiB
cap. Keep original path spelling and the accepted case-folded namespace key rules;
reject aliases, duplicates, unknown keys or a rebound owner/source/generation.
A run receipt cannot claim provisioned resources were never created.

An independent, current authenticated observer derives the outcome from actual
resource results, revocation and retained/shared preservation, not caller booleans.
Missing preservation uses its actual incomplete-observation projection; a digest
is not a successful observation. Missing runtime cleanup or infrastructure outcome
keeps overall deployment acceptance incomplete.

Keep original mutation/cleanup authority separate from the separately current
read-only observation capability. A late current observer may report failure
without any new mutation: completion observed at or after the original exclusive
cleanup deadline is failed even if resources are now absent. The old proof/cleanup
clocks, counters and consumed scopes remain expired. An observation-only Decision,
if required by the selected reader, is not a reconstructed cleanup/proof grant and
cannot be joined to renew one. When observation authority is absent/expired,
refuse receipt emission and fail qualification visibly; never invent an authenticated
failure origin or run admission/deletion solely to make the report complete.

## Acceptance controls for a later commission

Every refusal begins with a working authenticated-port positive and changes one
bound fact. An outage does not prove denial, absence or worker exclusion.
This table refines the existing task and factory matrix; it is not a new task list.

| Trace | Positive control | Independent refusal / failure control |
| --- | --- | --- |
| R07 setup | Reservation-only partial setup/predispatch cleanup, no final-run facts | Invented provisioned/link/incarnation/LRO, missing/extra/reordered target, phase/hash-cycle substitution |
| R07 run | Actual same-deployment provisioned/link/run/attempt/lease registration | Rebound source/case/owner/authority/generation or a never-created provisioned resource |
| R09 scope | Separate bounded cleanup authority while original creation remains expired | Rewritten window, creation-as-delete grant, setup/run authority substitution or missing closed admission |
| R09 identity/order | All six supported kinds and exact dependency retirement, retained controls intact | Wrong API/type/own GUID, same tags/new generation, foreign association, retained/alias/RG/subnet/cascade/force target |
| R09 fencing | Authenticated sole writer/no outstanding writes before the sole send | Hostile ordinary writer, stale fence, replacement, pending create/update or unsupported generation precondition |
| R10 triggers | Durable one-winner registration/action claim across concurrent triggers | Duplicate timer/abort/expiry, lost acknowledgement or restart causing a second send/attempt |
| R10 original create | Genuine terminal original creation or proven never-sent/no-effect | Pending original create, response loss or bare404 relabeled not-created/complete |
| R10 original delete | Original terminal operation plus independent absence | HTTP202/204 alone, wrong locator/operation, lost receipt/effect or late materialization; no resend |
| R10 control loss | Separate service/state survives actual fixture control/gate/worker process loss | Missing service/state/audit, failed timer or dead runtime used as proof of infrastructure absence |
| R10 independent outcome | Actual exact-set absence, credential revocation and retained/shared preservation | Worker/runtime pass flag, self-reported booleans, missing/refused/foreign observer or false preservation digest |
| R10 late observation | Current read-only authority emits failed late result with zero mutations and unchanged expired scope | Observation expiry refuses emission; receipt building renews a lease/Decision/budget or invokes admission/delete |
| R11 bounds/privacy | Complete selected graph fits original budgets, clocks and complete-byte caps | Nested uncharged I/O, callback resets, pagination/poll reset, partial positive, dropped bytes, raw token/URL/key/payload or exception-canary leak |
| R12 compatibility | All prior source/default-refusal/parser/profile/report/matrix behavior retained | Flag/env/plugin activation, new role/input, old-report relabel, missing/skipped/xfail/deselected cases or source fakes relabeled live |

Use real local crypto/loopback TLS/kernel/process controls where they establish
actual provenance, cancellation, survival or privacy. Authenticated provider/storage
ports use independently observable durable doubles and real call/effect/attempt
logs; do not replace intended failures with an unavailable fixture. Cross-process
reconstruction and independent teardown must inspect retained generations and
preserved controls. Source isolation is not Azure Functions deployment, effective
RBAC proof or live external-watchdog qualification.

## Future source ownership and qualification

The existing row proposes `azure_composition/retirement.py` and substantive
`tests/runtime_binding/test_azure_retirement.py`. Its narrowly additive cleanup
paths, if eligible and needed, belong in the existing owning `namespace.py` and
`provider.py`, with their compatibility regressions preserved. Record those
concrete paths in the same row when implementation is explicitly commissioned;
do not create another task list or quietly modify a neutral/shared owner.
Only measured collection metadata belongs in `tests/runtime_binding/matrix_contract.py`.
P08 owns source entrypoint/deployment packaging and workflow integration; it is
not part of P07. No new Azure SDK, dependency, listener or ambient activation is selected.

The source baseline is 3,581 full parents plus 11 subtests, 3,159 native cases and
130 canonical P06 cases. Preserve every old node ID/order, per-module fingerprint
and anchor prefix; measure additions only after implementation. A focused new
module pass cannot replace the seven ordered repository gates, full/native
qualification, exact-source hosted CI, local review and independent fixture cleanup.
A source correction requires renewed applicable qualification; interrupted or
failed runs remain diagnostic. Known handles retire, unknown effects remain honest.

For this preparation, run the six existing fast offline pin/syntax/plain-strict/
OpenSpec gates, feature prerequisites, relative-link and scope/checkbox audits,
and verify all runtime/test/matrix/profile/workflow/pin/dependency bytes unchanged.
No hours-long runtime rerun is required for documentation-only changes after
verified main CI. Independent local coverage/source audit and preparation checks
are recorded in [evidence.md](evidence.md); no P07 runtime result is claimed.
The next possible commission is isolated P07 work beginning with the two eligibility
gates. Preparation alone grants neither implementation nor setup/dispatch.
