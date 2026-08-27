# Feature Specification: wallet-v1.1 — the sweep prunes nested repositories, and the register read says so

**Feature Branch**: `013-nested-repo-prune-register-note`

**Created**: 2026-08-26

**Status**: Draft

**Input**: User description: "wallet-v1.1: the validator's sweep prunes nested repositories (a `.git` file or directory below the scan root) so a consumer running the pinned validator from its own root never re-adjudicates the pinned openXwallet tree, and the register reader emits a durable happy-path NOTE naming the register it read — realizes P2b (tasks.md group 4) of ratified openxFactory change split-openxwallet-repo"

## Governing authority

This feature realizes **P2b** — group 4 of the ratified openxFactory change
`split-openxwallet-repo` (`openspec/changes/split-openxwallet-repo/tasks.md`
§4.1–§4.7, at openxFactory main `f9457d6f`). Its two behaviours are decided
upstream by that change's `design.md` **D4** (the nested-repository prune) and
**D3** (the durable register-read NOTE), and its council constraint is
`clarifications.md` **N4** ("Mechanism for excluding the `openXwallet/` gitlink
from the consumer gate's sweep"). Nothing here re-opens those decisions; this
spec states them as this repository's requirements so they are testable here.

Scope boundaries fixed by the governing change and NOT negotiable in this
feature:

- **§4.8 (tag `wallet-v1.1`) is `[OPERATOR]`** — out of scope. The tag follows
  the human merge.
- **§4.9 (a green LedgerxFactory estate run) is `[LedgerxFactory]`** — out of
  scope here; it is that repository's evidence against the tag.
- **§4.10 (rollback)** is recorded in this spec's Assumptions, not implemented.
- **The eight digested contract artifacts are untouched.** `wallet-v1.0` is the
  byte-identical pure move and the byte-identity floor is proven against IT;
  `wallet-v1.1` is one auditable additive-minor diff on top whose only change is
  validator BEHAVIOUR plus tests and bookkeeping.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A consumer's required check stops re-adjudicating the pinned product (Priority: P1)

A consumer repository pins openXwallet as a nested repository and runs the
pinned conformance validator over its OWN checkout root, because the validator's
register reader resolves the register relative to the scan target and therefore
only works when the target IS the consumer's root. Today that sweep walks
straight into the nested repository and adjudicates the product's own carried
YAML — its OpenSpec instance, its Speckit evidence, its syntax-gate fixtures,
its canonical custody registry — as if those were live records of the consumer.
After this feature the sweep prunes any nested repository below the scan root, so
the consumer's required check adjudicates only the consumer's own records.

**Why this priority**: The hazard sits inside a check that is REQUIRED on a
default branch. A required check that adjudicates the wrong tree either red-lines
a legitimate pull request or, worse, passes on the wrong corpus. It is closed
before the check starts running, not after.

**Independent Test**: Point the validator at a directory tree that contains a
nested repository holding a wallet record, and at the same record placed outside
any nested repository. The nested copy is not adjudicated; the outside copy is.

**Acceptance Scenarios**:

1. **Given** a scan root containing a subdirectory that carries a `.git` FILE
   (the shape a submodule checkout has), **When** the validator sweeps that root,
   **Then** no YAML below that subdirectory is adjudicated, and a note names the
   pruned path.
2. **Given** a scan root containing a subdirectory that carries a `.git`
   DIRECTORY (the shape an independent clone has), **When** the validator sweeps
   that root, **Then** no YAML below that subdirectory is adjudicated.
3. **Given** the same wallet record placed in the scan root OUTSIDE any nested
   repository, **When** the validator sweeps that root, **Then** the record IS
   adjudicated — the prune is a nested-repository rule, not a blanket exclusion.
4. **Given** a scan root that itself carries a `.git` entry (the ordinary case:
   a repository scanning itself), **When** the validator sweeps it, **Then**
   nothing is pruned on account of the root's own `.git`.
5. **Given** a run over a tree with no nested repository at all, **When** the
   validator sweeps it, **Then** no prune note is emitted and the adjudicated
   record set is byte-for-byte the set the previous version adjudicated.

---

### User Story 2 - The reader leaves durable positive evidence that it opened the register (Priority: P1)

An auditor reading a required check's log must be able to tell a run that opened
the intake register from a run that opened nothing. Today the reader is silent on
success: the only output naming the register path is a failure finding, and the
absent-register note names no path at all — so "the register was read" can only
be inferred from a conjunction of absences. After this feature a successful read
says so, once, naming the register it read and how many rows it read.

**Why this priority**: The consumer gate's positive-proof test (upstream D3,
landing at P3) rests on this line. Without it, the only available proof of a
register read is an argument from silence, and a green check that opened no
register is indistinguishable from a green check that opened the right one.

**Independent Test**: Run the validator over a tree carrying a valid register,
grant, wallet and attestation; the note appears, names the register's path
relative to the scan root, carries the row count, and the run exits 0 under
`--strict`.

**Acceptance Scenarios**:

1. **Given** a scan root carrying a register that parses and whose rows resolve,
   **When** the validator sweeps it, **Then** exactly one note names the
   register's path relative to the scan root together with the number of rows
   read.
2. **Given** that same run invoked with `--strict`, **When** it completes,
   **Then** it exits 0 — the line is a NOTE and never a warning, because a
   consumer runs `--strict` and a warning would red-line it.
3. **Given** a scan root with NO register and no review-class grants, **When**
   the validator sweeps it, **Then** the ratified "no intake register at this
   tree; nothing to read" note is emitted unchanged and the new note is absent.
4. **Given** a scan root whose register exists but is malformed, **When** the
   validator sweeps it, **Then** the existing `register-*` finding codes and
   their messages are unchanged.

---

### User Story 3 - Nothing a live consumer keys on moves (Priority: P1)

A consumer repository pins this validator's finding-code STRINGS and runs it with
`--strict`; another pins its exact command line in a test. A behavioural change
that renamed a code, promoted a note to a warning, or added a flag to the command
line would break a required check in a repository that never asked for the
change.

**Why this priority**: It is the constraint that makes the other two shippable as
an additive MINOR rather than a major. It is stated as its own story because it
is independently testable and independently breakable.

**Independent Test**: Adjudicate the packaged corpus before and after the change
and compare the finding sets; inspect the command-line surface for new options.

**Acceptance Scenarios**:

1. **Given** the packaged conformance corpus (17 positives, 36 negatives — 32
   core plus 4 profile), **When** it is adjudicated by the previous version and
   by this one, **Then** the two finding sets are identical.
2. **Given** the command line, **When** this version is compared with the
   previous one, **Then** the accepted arguments are the same: one optional
   positional path and `--strict`, with no exclusion option added.
3. **Given** a `--strict` run over this repository, **When** it completes,
   **Then** it exits 0 — no note introduced by this feature is a warning.
4. **Given** the eight digested contract artifacts, **When** their hashes are
   taken at this version, **Then** all eight equal the values recorded for
   `wallet-v1.0`.

---

### Edge Cases

- **A nested repository whose `.git` is neither a file nor a directory**
  (a dangling symbolic link, or an unreadable entry): the prune tests only for
  the entry's EXISTENCE, so a path that resolves is pruned and a path that does
  not is not. A prune is the conservative outcome either way — it narrows what is
  adjudicated, never widens it.
- **Nested repositories inside nested repositories**: the outer prune already
  removes every path below it; the inner one needs no separate handling and is
  not reported twice.
- **A nested repository at the scan root's immediate boundary**: the scan root is
  compared by RESOLVED path, so a root reached through a symbolic link is still
  recognised as the root and is not pruned.
- **The packaged corpus already excluded by path parts** (`examples/` under
  `openxwallet` or `openxwallet-agent-profile`): that exclusion is independent of
  the prune and keeps working, including when the corpus sits inside a pruned
  nested repository. Both mechanisms firing on the same path is not an error.
- **A register that exists but is a directory, or is unreadable**: unchanged
  behaviour — the existing findings decide, and the new note is not emitted
  because the read did not succeed.
- **A single-file scan target** (the validator accepts a file, not only a
  directory): no sweep runs, so neither the prune nor the register read applies.
  Unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sweep MUST prune every path descending from a directory, other
  than the scan root itself, that carries a `.git` entry — whether that entry is
  a FILE or a DIRECTORY. (§4.1, D4)
- **FR-002**: The prune MUST be expressed as a general nested-repository rule and
  MUST NOT name any consumer's directory. Adding a consumer's directory name to
  the validator's skip set is refused: it couples the product to one consumer and
  misses every other nested repository. (§4.2, D4)
- **FR-003**: The sweep's existing skip set (`.git`, `node_modules`,
  `__pycache__`, `.venv`, matched on path parts) MUST keep its current behaviour.
- **FR-004**: The scan root itself MUST NOT be pruned when it carries a `.git`
  entry — the ordinary case of a repository scanning itself.
- **FR-005**: The sweep MUST emit a note listing the pruned nested repositories
  by path and nothing else about them. It MUST be a note, never a warning.
- **FR-006**: The packaged-corpus exclusion, which keys on path PARTS and
  therefore holds inside a nested repository too, MUST be unchanged. (§4.6, D4)
- **FR-007**: When the intake register is read successfully, the reader MUST emit
  exactly one note naming the register file's path relative to the scan root and
  the number of rows read. It MUST be a note, never a warning. (§4.5, D3)
- **FR-008**: When no register is present and no review-class grant exists, the
  ratified absent-register note MUST be emitted unchanged and the new note MUST
  be absent.
- **FR-009**: Every existing finding CODE, every existing finding message, and
  the meaning of `--strict` MUST be unchanged. A live consumer pins the code
  strings and runs `--strict`.
- **FR-010**: The command-line surface MUST be unchanged — one optional
  positional path plus `--strict`, and NO exclusion option. An exclusion the
  caller supplies is one the caller can omit. (§4.3, D4)
- **FR-011**: The eight digested contract artifacts MUST be byte-identical to
  their `wallet-v1.0` state. This release changes validator behaviour, tests and
  bookkeeping only.
- **FR-012**: The release bookkeeping MUST record `wallet-v1.1` as an additive
  minor: a CHANGELOG entry naming both behaviours and stating that none of the
  eight digested artifacts is touched, and the manifest's bundle version bumped
  with no row digest changed. (§4.7)
- **FR-013**: The tests proving FR-001 through FR-008 MUST be collected by the
  repository's existing offline test suite, so a regression is caught by the
  required check rather than by a human re-reading the diff. (§4.4)
- **FR-014**: The repository's own documentation MUST tell a consumer how to run
  the pinned validator from the consumer's root, and what the two new notes mean.

### Key Entities

- **Scan root**: the directory the validator is pointed at. The register is
  resolved relative to it, which is why a consumer must point the validator at
  its own root rather than at the nested product.
- **Nested repository**: any directory below the scan root that carries a `.git`
  entry. A submodule checkout carries a `.git` FILE; an independent clone carries
  a `.git` DIRECTORY. Both are nested repositories for this rule's purpose.
- **Intake register**: the review-authority register at a fixed path below the
  scan root. It has no schema — the reader IS its shape.
- **Note / warning / error**: the validator's three finding classes. Notes never
  affect the exit code; warnings red-line a `--strict` run; errors red-line every
  run. The class of a new line is therefore a compatibility decision, not a
  presentation one.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A wallet record placed inside a nested repository below the scan
  root is adjudicated 0 times; the same record placed outside any nested
  repository is adjudicated exactly once.
- **SC-002**: Adjudicating the packaged corpus — 17 positives and 36 negatives
  (32 core plus 4 profile) — produces a finding set identical to the previous
  version's, with zero added and zero removed findings.
- **SC-003**: A run over a tree carrying a valid register emits exactly 1 note
  naming that register's path relative to the scan root, and exits 0 under
  `--strict`.
- **SC-004**: A run over a tree carrying no register emits 0 register-read notes
  and exactly the ratified absent-register note.
- **SC-005**: Running this version from a real consumer's checkout root prunes
  every nested repository in that tree and reads that root's register, exiting 0.
- **SC-006**: All 8 digested contract artifacts hash identically to their
  `wallet-v1.0` values.
- **SC-007**: The command line accepts exactly the arguments it accepted before:
  0 options added, 0 removed.
- **SC-008**: Every requirement FR-001 through FR-008 is covered by at least one
  automated test collected by the existing offline suite.

## Assumptions

- **The two behaviours are decided upstream and are not re-litigated here.** D4
  fixes the prune's mechanism (a nested-repository rule in the sweep, not a skip
  set entry, not a narrowed scan scope, not a CLI flag, not a CI relocation) and
  D3 fixes the register line's class (a NOTE). This feature implements those
  decisions; the alternatives they rejected stay rejected.
- **The note's exact wording is this feature's to choose**, because the governing
  change specifies the note's CONTENT (the resolved register path) and CLASS, not
  its characters. The path is rendered RELATIVE to the scan root so that the line
  is stable across checkout locations and therefore assertable by a downstream
  test; an absolute path would differ between a developer's machine and a CI
  runner.
- **`wallet-v1.0`'s byte-identity floor is already proven** and is not re-proven
  here. This feature's obligation is the narrower one: that it did not disturb
  it.
- **Rollback, per §4.10**: if either behaviour proves wrong, the consumer pins
  `wallet-v1.0` and the downstream cutover is BLOCKED until the prune lands
  again. There is no partial rollback of a released tag.
- **Out of scope**: the `wallet-v1.1` tag itself and its release digest file
  (operator acts, after the human merge); the consumer-side estate run; any edit
  to the eight digested artifacts; any change to the vendored openxFactory
  schema; any network-reading gate.
