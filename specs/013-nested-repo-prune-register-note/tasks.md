# Tasks: wallet-v1.1 — the sweep prunes nested repositories, and the register read says so

**Feature**: `013-nested-repo-prune-register-note`
**Input**: Design documents in `/specs/013-nested-repo-prune-register-note/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/validator-cli.md`, `quickstart.md`

**Tests are REQUIRED, not optional, for this feature.** FR-013 and governing task
§4.4 both demand them, and they must be collected by the existing REQUIRED
`pytest-suite` check — a behaviour change to a validator that live consumers pin,
proven only by a human re-reading a diff, is not proven.

**Governing authority**: openxFactory change `split-openxwallet-repo` (ratified
2026-08-26), `tasks.md` group 4 (P2b) §4.1–§4.7, `design.md` D3 and D4,
`clarifications.md` N4 — at openxFactory `f9457d6f`. §4.8 (the tag), §4.9 (the
LedgerxFactory estate run) and §4.10 (rollback, recorded not implemented) are
NOT in this feature's scope.

**Hard limits carried into every task**: no finding code renamed, no existing
message changed, `--strict` semantics untouched, `main()`'s argparse untouched,
and not one byte of `contracts/openxwallet*/` altered.

---

## Phase 1: Setup

- [x] T001 Capture the pre-change baseline: run `python3 scripts/validate-openxwallet.py .` and `... . --strict` from the repository root and record both outputs (all four note lines, the summary line, both exit codes) into the task notes below, so every later comparison has a written target rather than a remembered one
- [x] T002 [P] Record the eight digests as they stand: `sha256sum` over the eight owned contract paths listed in `specs/013-nested-repo-prune-register-note/quickstart.md` §5, and confirm each equals its `sha256:` row in `contracts/manifest.yaml`
- [x] T003 [P] Confirm `docs/pin-resync-runbook.md` contains no reference to the sweep (`grep -inE "sweep|rglob|repo_scan|SKIP_DIR"`), which is what licenses leaving it unchanged

## Phase 2: Foundational (blocks every user story)

- [x] T004 Create the test module skeleton `tests/nested_repo_prune/test_prune_and_register_note.py` with a module docstring naming P2b / D3 / D4, and a `_run(target, *args)` subprocess helper that invokes `scripts/validate-openxwallet.py` exactly as CI does (`sys.executable`, `cwd` at the repository root, `capture_output=True`) — mirroring the pattern `tests/wallet_yaml_syntax_gate/test_gate.py` established, so the exit codes the workflows act on are the ones under test
- [x] T005 Add to `tests/nested_repo_prune/test_prune_and_register_note.py` a `_nested_repo(dir, kind)` fixture helper that makes a nested repository of either shape — a `.git` FILE containing `gitdir: ../.git/modules/x`, or a `.git` DIRECTORY — since both shapes are needed by three separate tests

## Phase 3: User Story 1 — the sweep prunes nested repositories (Priority: P1) 🎯 MVP

**Goal**: A consumer's required check adjudicates only the consumer's own records,
never the pinned product's carried YAML.

**Independent test**: point the validator at a tree holding the same wallet record
inside a nested repository and outside one; the nested copy is not adjudicated and
the outside copy is.

### Tests for User Story 1 (write first — they must fail before T010)

- [x] T006 [P] [US1] Test in `tests/nested_repo_prune/test_prune_and_register_note.py`: a nested directory carrying a `.git` FILE (`gitdir: ../.git/modules/x`) holding a valid wallet record is NOT adjudicated — assert the `repo scan:` note reports 0 validated and the record's `wallet_id` appears in no finding (spec AS-1, FR-001)
- [x] T007 [P] [US1] Test: the same, for a nested `.git` DIRECTORY (spec AS-2, FR-001)
- [x] T008 [P] [US1] Test the control: the SAME record placed in the scan root outside any nested repository IS adjudicated — `repo scan:` reports exactly 1 validated. This is what makes the prune a nested-repository rule rather than a blanket exclusion (spec AS-3, FR-002)
- [x] T009 [P] [US1] Test that the scan root's OWN `.git` entry does not prune it: build a tree whose root carries a `.git` file AND a wallet record, and assert the record is still adjudicated (spec AS-4, FR-004)

### Implementation for User Story 1

- [x] T010 [US1] In `scripts/validate-openxwallet.py`, replace `repo_scan`'s `sorted(target.rglob("*.y*ml"))` with an `os.walk`-based candidate collector that prunes in place: for each directory other than the resolved scan root, if `dir / ".git"` exists (file OR directory), do not descend and record the directory. Sort the resulting file list so adjudication order stays identical to today's. Keep the `SKIP_DIR_NAMES` parts filter exactly as it is (FR-001, FR-003, FR-004; research R3)
- [x] T011 [US1] In the same function, emit the prune note — paths only, relative to the scan root, sorted, and only when at least one directory was pruned — per `contracts/validator-cli.md` §3.2 (FR-005). A note, never a warning
- [x] T012 [US1] Add the code comment the diff is owed: WHY the rule is general rather than `SKIP_DIR_NAMES + {"openXwallet"}` (hard-coding a consumer's directory name into the product's validator is the coupling the split removes, and it misses every other nested repository, including `installs/omnigent-install`) and why `.git` existence is tested rather than its type (§4.2, research R2)
- [x] T013 [US1] Test that the packaged-corpus exclusion is unchanged and still keys on path PARTS, including inside a pruned nested repository: assert the corpus note still reads `17 positive example(s), 36 negative confirmation(s) across 13/13 requirements` and that a corpus-shaped path inside a nested repository produces no finding (§4.6, FR-006, spec AS-5)

**Checkpoint**: User Story 1 is independently shippable — the prune works and is proven.

## Phase 4: User Story 2 — the durable register-read NOTE (Priority: P1)

**Goal**: a successful register read leaves positive evidence naming the register
it read, so an auditor can distinguish it from a run that opened nothing.

**Independent test**: a tree carrying a valid register plus the grant, wallet and
attestation it resolves against emits the note and exits 0 under `--strict`.

### Tests for User Story 2 (write first — they must fail before T017)

- [x] T014 [P] [US2] Add a fixture in `tests/nested_repo_prune/test_prune_and_register_note.py` that builds a minimal tree which reads CLEAN: one register row, its backing grant, its audience wallet, and the custody attestation the `act` tier requires — modelled on the validator's own `_s4_tree` / `s4_row` / `s4_grant` / `s4_wallet` / `s4_attest` self-test fixtures (`scripts/validate-openxwallet.py` ~`:1682-1760`), with a future `expires_at` so the computed-expiry rule passes
- [x] T015 [P] [US2] Test that exactly ONE note reads `intake register read: governance/review-authority/register.yaml (1 row(s))` — the path relative to the scan root, and the row count (FR-007, spec AS-1 of US2)
- [x] T016 [P] [US2] Test that the same run exits 0 under `--strict`, and that a tree with NO register still emits the ratified `no intake register at this tree; nothing to read` and NO register-read note (FR-008, spec AS-2/AS-3 of US2)

### Implementation for User Story 2

- [x] T017 [US2] In `check_register` (`scripts/validate-openxwallet.py` ~`:1855`), emit one `f.note` naming the register path relative to `base_dir` and the row count, placed immediately after `rows` is confirmed to be a list — the earliest point at which both reported facts are known (FR-007; research R4). A note, never a warning
- [x] T018 [US2] Add the code comment recording WHY it is a NOTE and not a warning (`report()` reds a `--strict` run on warnings and a live consumer runs `--strict`), and why the path is relative (the downstream consumer-gate test must be able to assert the line across checkout locations) — §4.5, D3

**Checkpoint**: both behaviours land; User Story 2 is independently shippable.

## Phase 5: User Story 3 — nothing a live consumer keys on moves (Priority: P1)

**Goal**: the release is provably an additive MINOR.

**Independent test**: the previous version and this one produce identical finding
sets over the packaged corpus; the command-line surface is unchanged.

### Tests for User Story 3

- [x] T019 [US3] Test corpus identity: recover the previous version with `git show <base>:scripts/validate-openxwallet.py` into a temp file, run BOTH versions against the repository root, and assert their ERROR and WARNING sets are identical — notes are excluded by design, since this feature adds two. Skip with an explicit reason (never silently) when the base blob is unavailable (FR-009, SC-002; research R5)
- [x] T020 [P] [US3] Test that the command-line surface is unchanged: `--help` output offers exactly the optional positional `path` and `--strict`, with no exclusion option (FR-010, SC-007, §4.3)

### Verification for User Story 3

- [x] T021 [US3] Run `git diff --stat HEAD -- contracts/` and confirm the only changed lines are the bundle version and the CHANGELOG entry; re-run T002's `sha256sum` and confirm 8/8 digests unchanged (FR-011, SC-006)

## Phase 6: Bookkeeping (§4.7)

- [x] T022 Add the `wallet-v1.1` entry at the top of `contracts/CHANGELOG.md`'s release history, in the `wallet-v1.0` entry's shape: change class ADDITIVE MINOR, both behaviours named, the realization line citing P2b of `split-openxwallet-repo` and this feature, and the explicit statement that **none of the eight digested artifacts is touched — so the eight sha256s at `wallet-v1.1` still equal the carve commit's rows** (§4.7)
- [x] T023 Bump `contracts/manifest.yaml` `contract_bundle_version:` from `wallet-v1.0` to `wallet-v1.1` — that ONE line, with no row digest and no `contract_schema_version` altered (FR-012)
- [x] T024 [P] Add to `README.md` § "How to consume this repository" a short block on running the PINNED validator from the consumer's own root (why the target must be the consumer root: the register resolves relative to it), what the prune note means, and what the register-read note means (FR-014)

## Phase 7: Polish & cross-cutting verification

- [x] T025 Run all six gates from `quickstart.md` §1 and record each exit code: `verify-contract-pin.py`, the syntax gate, the validator plain and `--strict`, `python3 -m pytest tests/ -q`, and `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`
- [x] T026 Run the end-to-end proof from `quickstart.md` §6: the feature worktree's validator against the openxFactory checkout (READ-ONLY), and confirm both required lines — a prune note naming `installs/omnigent-install`, and a register-read note naming `governance/review-authority/register.yaml` — with exit 0 (§4.1, §4.5, §4.2's "closes the same pre-existing hole")
- [x] T027 [P] Compare the pytest collection count before and after, and record it: the suite grows from its existing count by exactly this feature's new tests, so a silently-uncollected module is visible as a number rather than assumed away
- [x] T028 Re-read the whole diff of `scripts/validate-openxwallet.py` against `HEAD` and confirm by inspection that zero finding codes, zero existing messages, `report()`, and `main()`'s argparse are touched (FR-009, FR-010, §4.3)

---

## Dependencies

```text
Phase 1 (T001-T003)  ─┐
                      ├─► Phase 2 (T004-T005) ─┬─► Phase 3 US1 (T006-T013)
                      │                        ├─► Phase 4 US2 (T014-T018)
                      │                        └─► Phase 5 US3 (T019-T021)
                      │                                    │
                      └────────────────────────────────────┴─► Phase 6 (T022-T024)
                                                                      │
                                                                      └─► Phase 7 (T025-T028)
```

- **T001 blocks Phase 7**: T025 and T026 compare against T001's recorded baseline.
- **T004/T005 block every test task**: the helper and the fixture are shared.
- **T010 blocks T011, T012, T013**: they edit the function T010 restructures.
- **US1, US2 and US3 are mutually independent** once Phase 2 lands. US3's corpus
  identity test (T019) is strongest run LAST, but it is correct at any point — it
  compares against git history, not against an intermediate working tree.
- **T023 must not precede T021**: bumping the bundle version before the digest
  check makes the check less meaningful, not more.
- **T026 requires T010 and T017 both landed** — it is the one proof that exercises
  both behaviours in a single real run.

## Parallel execution opportunities

- **Phase 1**: T002 and T003 in parallel (different files, read-only).
- **Phase 3 tests**: T006, T007, T008, T009 in parallel — four independent cases
  in one module, no shared mutable state (each builds its own `tmp_path` tree).
- **Phase 4 tests**: T014 then T015 and T016 in parallel.
- **Phase 5**: T020 in parallel with T019.
- **Phase 6**: T024 (README) in parallel with T022/T023 (contracts/).
- **Phase 7**: T027 in parallel with T025/T026.

Two source-file tasks (T010/T011 and T017) touch the SAME file
(`scripts/validate-openxwallet.py`) in different functions — sequential, not
parallel, to keep the diff reviewable as one auditable change.

## Independent test criteria

| Story | Independently testable by |
|-------|---------------------------|
| US1 | one scratch tree, three copies of one record, two nested shapes; assert the validated count and the prune note |
| US2 | one scratch tree with a clean register; assert the note text and `--strict` exit 0 |
| US3 | git history plus `--help`; assert an empty error/warning diff and an unchanged option set |

## Implementation strategy

**MVP = User Story 1 alone.** The prune is the behaviour that sits inside a
REQUIRED check and is the reason P2b lands before P3; shipping it alone would
already discharge the hazard. US2 is shipped in the same release because it is
three lines and because D3's positive proof depends on it, and US3 is not a
feature at all — it is the evidence that the other two are additive.

**Order actually executed**: Phase 1 → 2 → 3 → 4 → 5 → 6 → 7, single-threaded,
because the whole change is ~40 net source lines in one file and one new test
module. Parallelism is recorded above for completeness, not because the work needs
it.

---

## Evidence recorded on completion (2026-08-26)

All 28 tasks complete. Measured, not summarized.

**T001 baseline** (pre-change, repository root) — 4 notes, `0 error(s), 0 warning(s)`,
exit 0 plain and `--strict`; `repo scan: 0 validated, 20 skipped`;
`corpus: 17 positive example(s), 36 negative confirmation(s) across 13/13 requirements`.
**Post-change output on this tree is byte-identical to that baseline** — this
repository carries no nested repository below its root and no register, so neither
new note fires here. That is the point of T007's "no prune note when there is
nothing to prune".

**T002 / T021 digests** — 8/8 `sha256sum` values equal their `contracts/manifest.yaml`
rows, before AND after; `diff` of the two recordings is empty.
`git diff --stat HEAD -- contracts/openxwallet contracts/openxwallet-agent-profile contracts/schemas`
is EMPTY: not one contract byte is touched. (A ninth `sha256:` exists in the
manifest — the CONSUMED `hermes-job-envelope.schema.yaml` row, `member_class`
declared, not part of any wallet bundle.)

**T003** — `grep -inE "sweep|rglob|repo_scan|SKIP_DIR" docs/pin-resync-runbook.md`
returns nothing, which is what licenses leaving that runbook unchanged.

**T006–T020 tests** — `tests/nested_repo_prune/test_prune_and_register_note.py`,
**18 tests**. Suite grew **4 → 22** (T027). Written first and confirmed RED:
8 failed / 10 passed before implementation, with the 8 failures being exactly the
two absent behaviours; 22/22 pass after.

**T019's first version was VACUOUS in CI, and the count is what caught it.**
The baseline-ref candidate list ended at `HEAD`, so wherever the base ref is
unreachable — a depth-1 checkout of a merge ref, whose parents were never
fetched — it compared this version against ITSELF and passed. CI reported
`22 passed, 0 skipped`, which the test cannot legitimately produce there.
Fixed: a recovered blob byte-equal to the working copy is treated as NO
baseline, so the test skips with its reason. CI now reports **`21 passed,
1 skipped`** — the honest number, and the delta IS the proof the fallback was
firing. Locally the recovered `origin/main` blob differs, the comparison is
real, and its error/warning-set diff is empty (22 passed, 0 skipped).

**T028 diff audit** — `scripts/validate-openxwallet.py`: 105 insertions, 1
deletion (the `rglob` line), most of it the WHY comments T012 and T018 owe. Zero
added or removed `f.error` / `f.warn` calls. The only diff lines mentioning
`--strict`, `report()` or `main()` are COMMENTS; `add_argument` appears in no diff
line. `--strict` semantics, `report()` and the argparse surface are untouched, and
T020 asserts the option set is exactly `{--strict, --help}` plus the optional
positional `path`.

**T025 six gates**, each exit 0: `verify-contract-pin.py`;
`wallet-yaml-syntax-gate.py .`; the validator plain; the validator `--strict`;
`python3 -m pytest tests/ -q` (22 passed); `OPENSPEC_TELEMETRY=0 openspec validate
--all --strict` (2 passed, 0 failed).

**T026 the end-to-end proof** — this worktree's validator against a real
openxFactory checkout (read-only). `installs/omnigent-install/.git` is `ASCII
text`, i.e. the `.git` FILE shape `SKIP_DIR_NAMES` cannot catch:

```text
note  nested repositories pruned (not adjudicated): installs/omnigent-install
note  intake register read: governance/review-authority/register.yaml (1 row(s))
note  repo scan: 3 openxWallet artifact(s) validated, 1596 document(s) skipped as another kind

validate-openxwallet: 0 error(s), 0 warning(s)      exit 0
```

The recovered `wallet-v1.0` validator on the SAME tree reports
`3 validated, 1683 skipped` with the same `0 error(s), 0 warning(s)`. So the
prune removes **87 files** from the sweep and the finding set does not move —
none of those 87 carries a wallet `kind:` today, which is precisely what makes
this a LATENT hazard rather than a live break, and why §4.2 insists the rule be
general and §4.10 blocks P3 until it lands.

**Not done here, by scope**: §4.8 the `wallet-v1.1` tag and its
`wallet-v1.1.digests.yaml` (`[OPERATOR]`, after the human merge); §4.9 the
LedgerxFactory estate run (that repository's evidence); §4.10 rollback (recorded
in `spec.md` Assumptions, not implemented).
