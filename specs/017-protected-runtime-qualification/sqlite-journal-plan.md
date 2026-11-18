# SQLite staging journal correction — isolated source plan

Date: 2026-11-18. Existing feature017; implementation-only correction to the
specified private initialized durable store and unique concurrent reservation.
Brett Heap source-ratified #91 at cf2c0eee65fc55c1606be4c19f4b61eda2185fab,
then commissioned this fix and testing in isolation. #91 merged normally as
bd1b0d8b6ec249f7ed37932a552e5674d046a912 with the exact accepted tree.

## Scope and authority

The factory's accepted hosting/issuance/staging composition and T012R durable
single-winner behavior remain unchanged. Shared workflow permits an
implementation-only fix under the existing Speckit feature without a new
OpenSpec decision. No schema, contract, neutral source/pin, workflow, runtime
activation, clock/read/deadline budget, service role or operating policy changes.
The sole executable task is T012VJ in tasks.md. T012V's historical owner act stays
complete; T001/T013/T014/T015 remain unchecked. New source is an isolated
candidate, not ratified or commissioned for publication/landing by this act.
Setup/dispatch remain unauthorized, feedback deferred, blocked writes forbidden.

## Cause and correction

PR91's first source-CI native attempt refused a constructor in its eight-thread
reservation case. The suppressed provider exception does not prove its precise
cause. A real SQLite DELETE-mode COMMIT deliberately interleaved between the old
exists/lstat observations reproduces FileNotFoundError for a retired journal,
with unchanged directory/database identity. Natural repetition alone does not
cover that schedule. Failed attempts remain nonqualifying historical evidence.

Reuse the existing github_bootstrap/journal.py optional-sidecar snapshot pattern:
one lstat per optional sidecar, accepting only FileNotFoundError as absence.
Every observed snapshot retains regular-file/one-link/owner/private permissions;
observed WAL/SHM or unsafe journal metadata refuses. Add a bounded final
main-identity validation/comparison so loss, replacement or unsafe main metadata
during sidecar inspection still refuses, without creating/restoring state.
Validate captured unsafe snapshots even when they disappear afterward. No retry,
sleep, broad OSError catch, stat-followed symlink or weakened concurrency oracle.
This does not make all filesystem activity atomic against arbitrary later change.

## Verification and acceptance

A new isolated regression module forces a real SQLite writer COMMIT immediately
before the sidecar lstat during construction, reservation and read, then verifies
actual durable reuse. Controls cover a valid active private journal, all observed
unsafe sidecar forms, non-ENOENT lookup errors, main directory/database
loss/replacement/permission changes and unsafe snapshots removed after lookup.
Keep the existing eight-thread exactly-one-winner and other stage tests intact.
The deterministic retirement cases must fail on the unmodified source and pass
only after the correction. Add the measured new module count/digest and H03
anchors while retaining every old mandatory node, fingerprint and anchor.

Run targeted regressions and conformance self-tests, then the ordered seven
repository gates/full suite and required native matrix under the existing
unprivileged loopback-only boundary with explicit accepted owning source.
Freeze input hashes before qualification, audit exact fixture ownership and
preservation independently, and remove only owned temporary roots/containers.
Keep earlier failures/diagnostics separate from final exact-source evidence.
Actual post-merge CI for #91 is independently observed; no operational evidence
or protected-machine qualification is inferred from any source result.

## Accepted main #92 integration

Main #92 at `22bc7bdf6298c043377528c0c289ca26e51cbb07` landed during isolated
qualification. It refactors existing CLI/qualification/probe exception and
resource retirement paths and clarifies existing deadline assertions. Its exact
head `6e3b6e043e8f4ede3c2958cf6bd918a8f345b133` has hosted checks and local expert
review evidence. It changes no pins, workflows, source corpus or clock/read limits.
Consume that accepted baseline under the owner's instruction to integrate
incoming changes as needed. The staging-store correction, 48 new regressions and
matrix bytes remain identical to local runtime `61e06e3244937fae8806b1e29cdfdd24aaac9df9`.

The prior 221 focused passes, 2,859 full cases plus 11 subtests and seven ordered
gates remain historical exact-source evidence. Its first native attempt had two
protected-stage setup refusals before target cleanup/cancellation assertions and
was interrupted for diagnosis, adding a pytest teardown KeyError; it is incomplete
and nonqualifying. Safe source/fixture metadata and XML are retained. Two focused
native-equivalent cases pass without source, assertion or budget changes, with
8.25s/8.50s protected-stage responses; the original transport cause is unproven.
The unchanged full-native retry was stopped as superseded by accepted #92, not
promoted to a result. All those namespaces and fixtures were audited/removed.

Fresh integrated collection, full/native qualification and cleanup are required.
Use explicit offline npm cache mode for pinned CLI bootstrap; content addresses,
strict checks and network isolation remain enforced. Existing T012VJ is still
the sole correction task and stays unchecked until these checks pass. No new
profile, source acceptance, publication, setup/dispatch or live grant is inferred.
Feedback deferred; blocked writes unreplayed.

## Isolated correction result

Frozen integrated runtime `c32ac5147fd504426483681a11dc8b60f4aac0fc` (tree `aea5589f55910b9b9e978b18ffb4e2db80a0c946`), based on accepted
main `22bc7bdf6298c043377528c0c289ca26e51cbb07`, passes all seven ordered local gates, 2,859 full cases plus
11 subtests and all 2,437 mandatory native cases, with zero failures/errors/skips.
Full execution took 1762.350s and native execution 1301.731s.
All 387 tracked input hashes matched before and after qualification. The later
five-document reconciliation preserves every other input; its head is distinct
from the runtime head. All previous 2,811 full and 2,389 native identities/order,
module fingerprints and case anchors remain; 48 measured new cases extend H03
to 145 nodes. All 221 integrated targeted controls pass.
Three deterministic real SQLite journal-retirement controls fail on the old
runtime at construction/reservation/read and pass on the correction. An earlier
unchanged-value update created no journal and is retained as an invalid control.

Both qualifying containers use loopback-only networking and read-only source.
Processes have no supplementary groups/capabilities and cannot regain them.
Full execution has no active trace/profiler/coverage collector. Native bootstrap
independently verifies its clean environment and privilege boundary. Independent
post-namespace audits verify 27329
generation observations, 854 lifecycle journals,
262 helper receipts and ten actual
preservation cases, with no attributable live process or initial qualifying
teardown failure. The three current qualification fixture roots, audit-control
root and three named containers are absent. Historical failed/diagnostic and
superseded namespaces/roots are separately audited and absent. Reports remain
outside the repository; credentials/raw provider payloads are not published.

The owner source-ratified #91 at cf2c0eee65fc55c1606be4c19f4b61eda2185fab.
It landed normally as bd1b0d8b6ec249f7ed37932a552e5674d046a912 with accepted tree
7c6c4a709c8dd4f4676b8a3dabaa2d666d529a9a. Its [post-merge run](https://github.com/opensoft/openXwallet/actions/runs/44294729187)
passes all five jobs, 2,811 full cases plus 11 subtests and 2,389 native cases.
The [public post-merge receipt](https://github.com/opensoft/openXwallet/pull/91#issuecomment-6978259963) verifies all six original
Sonar conditions and the original manual baseline. Incoming accepted main #92
was integrated before this fresh qualification, without changing the SQLite
correction/tests/matrix bytes. Its independent [post-merge run](https://github.com/opensoft/openXwallet/actions/runs/44307509886)
also passes all five jobs, the same baseline full/native corpus and all six
original Sonar conditions (86.3% new coverage; A ratings; no new duplication;
100% reviewed new hotspots). These hosted runs cover their merged sources,
not the new local correction. No job cap or quality gate was relaxed.

Earlier runtime 61e06e3244937fae8806b1e29cdfdd24aaac9df9 remains historical.
Its 221 focused controls and full seven-gate run pass. Its first native attempt
had two protected-stage transport setup refusals before target cleanup-window
or cancellation assertions, then was interrupted for diagnosis: 1,546 completed
passes, two failures and an additional pytest teardown KeyError; incomplete and
nonqualifying. Two focused native-equivalent diagnostics pass unchanged, with
8.25s/8.50s protected-stage responses, but do not prove the original transport
cause. The unchanged full-native retry was stopped as superseded by accepted
main #92 (exit137), not promoted to a passing or independent failing matrix.
The fresh integrated run above supplies complete native evidence and does not
establish that every historical transport issue is fixed.

The original external cleanup reader blocked on an intentional FIFO negative
fixture. It was interrupted without a passing audit. The corrected read-only
reader checks known unsafe sidecars before SQLite access, refuses unexpected
special sidecars and explicitly closes connections. Guard controls pass;
complete audits were repeated. No product code or test oracle changed for this
reader repair. All original failure/diagnostic records remain separate.

T012VJ is complete only in isolation. Publication, hosted CI of this fix, local
expert review and owner source acceptance remain later gates. The original
provider exception remains unproven; this source race is reproduced/corrected
under a controlled real SQLite schedule. Main identity and every observed unsafe
sidecar still refuse; no arbitrary later filesystem atomicity is claimed. No
schema/transaction, neutral pin, workflow, budget, deadline or default activation
changes. T001/T013/T014/T015 remain unchecked. Setup/dispatch unauthorized,
feedback deferred, blocked writes unreplayed. No live provider qualification,
token mint, protected-machine acceptance or operational grant is inferred.

## SQLite correction publication and accepted main #93

Brett commissions the SQLite journal correction PR, hosted CI, local Codex expert
review, finding resolution and presentation for source ratification. This supplies
no merge, source acceptance or operational grant. Integrate accepted main #93
`dbbbafab8cb5ab093360b5e12044a7a35b156cc5`, which consumes neutral root
`8be8a2a6af125058ffe956cafbf1e62858d82dd9` for the reviewed decimal worktree
selector repair. Neutral code/spec and explicit qualification owner stay unchanged.
The SQLite runtime, new test module and matrix bytes remain identical to the
completed c32ac514 qualification. Earlier exact-source receipts remain historical;
fresh integrated full/native qualification, cleanup, hosted CI and nine local
Codex expert roles are required for this publication head and recorded on its PR.
Feature017 T012VJ remains the sole correction task; T001/T013-T015 stay unchecked.
Setup/dispatch unauthorized, feedback deferred, blocked writes unreplayed.

## Publication S9073 assertion correction

The first #94 hosted run 44355407295 at 9f462857c5e1176ae591087bc4fdcfab961e38f7
passes all five jobs and all six original conditions (100% new coverage), but
direct analysis c30c54cd-0576-4b92-8c6d-c0b619a181b9 retains four S9073 findings:
AaHv1OauqAoMpLQXSFXl, AaHv1OauqAoMpLQXSFXm, AaHv1OauqAoMpLQXSFXn and
AaHv1OauqAoMpLQXSFXo. That head is not presented for ratification. Split those
four composite assertions, retaining every condition, fixture, test identity,
matrix fingerprint and runtime byte. No rule suppression or scan/gate change.
This remains existing T012VJ publication finding resolution under the owner
commission. Earlier exact-source qualification and review remain historical;
fresh exact-source full/native, cleanup, local Codex follow-up and hosted CI/
analysis readback are required. T001/T013-T015/setup/dispatch stay ungranted;
feedback deferred, blocked writes unreplayed.
