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
