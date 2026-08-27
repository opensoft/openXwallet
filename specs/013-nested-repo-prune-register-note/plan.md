# Implementation Plan: wallet-v1.1 — the sweep prunes nested repositories, and the register read says so

**Branch**: `013-nested-repo-prune-register-note` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-nested-repo-prune-register-note/spec.md`

## Summary

Two additive-minor behaviours in `scripts/validate-openxwallet.py`, landing as
ONE auditable diff on top of the byte-identical `wallet-v1.0`:

1. **`repo_scan` prunes nested repositories.** The sweep's only exclusion today is
   `set(path.parts) & SKIP_DIR_NAMES` (`:2044`) over `target.rglob("*.y*ml")`
   (`:2040`), and `SKIP_DIR_NAMES` (`:295`) catches a `.git` DIRECTORY component
   only. A submodule checkout's `.git` is a FILE, so the sweep walks straight into
   every nested repository and adjudicates its carried YAML as live records of the
   scanned tree. The prune is a general nested-repository rule — any directory
   below the scan root carrying a `.git` entry of either kind — expressed as a
   directory-level walk that does not descend, so the cost is paid once per
   directory instead of once per file.
2. **`check_register` emits a happy-path NOTE.** On a successful read the reader
   is silent today: the only lines naming the register are failure findings
   (`:1873`, `:1884+`, `:1962+`) and the absent-register note (`:1878`) names no
   path. One `f.note` naming the register path relative to the scan root and the
   row count makes the positive read auditable, and a NOTE never affects an exit
   code — which is the whole reason it is not a warning.

Plus the release bookkeeping (`contracts/CHANGELOG.md`, `contracts/manifest.yaml`
bundle version, a README paragraph) and a new pytest module covering both.

**What this plan deliberately does NOT do**: touch any finding code, any existing
message, `--strict`'s meaning, `main()`'s argparse, or one byte of the eight
digested contract artifacts.

## Technical Context

**Language/Version**: Python 3.12 (the version both workflows pin)

**Primary Dependencies**: `pyyaml`, `jsonschema`, `rfc3339-validator` — the three
the workflows install. `pytest` for the test suite only. **No new dependency**:
the prune uses `pathlib` and `os.scandir`-class stdlib walking, both already
available.

**Storage**: N/A — the validator reads files and writes nothing.

**Testing**: `pytest`, collected by the REQUIRED `pytest-suite` check as
`python3 -m pytest tests/ -q`. Existing suite: one module,
`tests/wallet_yaml_syntax_gate/test_gate.py`, which drives its script as a
SUBPROCESS so the exit codes CI acts on are the ones under test. This feature's
module follows that pattern.

**Target Platform**: Linux (`ubuntu-latest` runners) and developer checkouts.
Offline in both.

**Project Type**: A single-file CLI validator plus an offline test suite. Not a
library, not a service.

**Performance Goals**: The prune must not make the sweep slower. Today's sweep
materialises `sorted(target.rglob("*.y*ml"))` and filters per file; the prune adds
one `.git` existence test per DIRECTORY, and pruning a nested repository removes
its whole subtree from the walk — so on a tree with a nested repository the new
code visits strictly FEWER paths than the old one.

**Constraints**:
- **Offline.** No gate reads the network, an upstream tree, or
  `contracts/manifest.yaml` at check time (AGENTS.md rule 4).
- **Machine keys are frozen.** Finding codes, messages, paths, `kind:` values and
  filenames are pinned BY NAME by live consumers (AGENTS.md rule 2). LedgerxFactory
  pins finding-code strings and runs `--strict`.
- **The byte-identity floor.** The validator's own bytes are inside it for
  `wallet-v1.0`; this release is the ONE auditable diff on top, and the eight
  digested artifacts stay byte-identical.
- **`main()`'s argparse is frozen** (§4.3): a downstream test pins the exact
  invocation, and an exclusion the caller supplies is one the caller can omit.

**Scale/Scope**: One source file touched (~40 net lines), one new test module,
three bookkeeping files. The proof tree is real: openxFactory's checkout, ~19
nested repositories, one live register.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**There is no `.specify/memory/constitution.md` in this repository, by decision.**
openxFactory's constitution came across with the Speckit bootstrap and was
removed: it is a governance document titled for a different repository, carrying a
`Status:` claim about that repository's adoption, and keeping it here would be a
false record. The gate therefore resolves against **`AGENTS.md` § "The rules that
are not negotiable here"**, which is this repository's constitution in fact.
Authoring openXwallet's own constitution is a governance act needing its own
ratification, and P2b does not authorize it.

| Rule | Gate | Verdict |
|------|------|---------|
| 1. Consumers pin; nobody forks | Does this change push work onto a fork or a profile? | **PASS** — the opposite. The prune is made in the PRODUCT precisely so no consumer needs a local edit; §4.2 refuses the consumer-shaped alternative by name. |
| 2. Machine keys do not move casually | Any code, path, `kind:`, id, prefix or filename renamed? | **PASS** — zero. FR-009 is the requirement, and the corpus-identity test is its proof. Both new lines are NOTES, which carry no code at all. |
| 3. The vendored envelope schema is not ours | Touched? | **PASS** — untouched. `contracts/schemas/` is not in this feature's file set. |
| 4. Every gate is offline | Does anything read the network or an upstream tree? | **PASS** — the prune is a filesystem existence test; the note is a string. The new tests build `tmp_path` trees. |
| 5. Run the gates before pushing | Will all six run? | **PASS** — enumerated in `quickstart.md`, and one MORE than the six: the end-to-end run against a real consumer checkout. |
| 6. A release is five coordinated values | Which are this feature's? | **PARTIAL BY DESIGN, and the split is the point.** This feature owns `contract_bundle_version` and the CHANGELOG entry. Per-file `contract_schema_version` does NOT move — no contract file changes, which is what makes this additive. The annotated tag and the release commit's digest file are `[OPERATOR]` acts at §4.8, after the human merge. Recorded here so the two missing values are visibly DEFERRED to their owner, not forgotten. |

**Post-Phase-1 re-check**: unchanged. The design added no dependency, no new
public surface, no network read, and no contract-file edit. Rule 6 remains the
only partial, for the reason stated.

## Project Structure

### Documentation (this feature)

```text
specs/013-nested-repo-prune-register-note/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── validator-cli.md # Phase 1 output: the CLI + output-line contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
scripts/
└── validate-openxwallet.py        # BOTH behaviours. The only source file touched.
                                   #   SKIP_DIR_NAMES         :295   (unchanged)
                                   #   check_register          :1855+ (one f.note added)
                                   #   repo_scan               :2037+ (file list -> pruning walk)
                                   #   main()                  :2110+ (unchanged)

tests/
├── wallet_yaml_syntax_gate/
│   └── test_gate.py               # existing, untouched
└── nested_repo_prune/
    └── test_prune_and_register_note.py   # NEW. Subprocess-driven, tmp_path trees.

contracts/
├── manifest.yaml                  # contract_bundle_version: wallet-v1.0 -> wallet-v1.1
│                                  # NO row digest changes (verified by sha256sum)
└── CHANGELOG.md                   # the wallet-v1.1 entry

README.md                          # a paragraph under "How to consume this
                                   # repository" on running the pinned validator
                                   # from a consumer root, and what the two notes mean

docs/pin-resync-runbook.md         # UNCHANGED: grep confirms zero sweep references
```

**Structure Decision**: The repository has no `src/` and no package — the
validator is a single executable script under `scripts/`, and tests live in
per-subject directories under `tests/`. This feature keeps that layout: one new
test directory named for its subject (`tests/nested_repo_prune/`), mirroring
`tests/wallet_yaml_syntax_gate/`. Introducing a package, a conftest, or a
`pytest.ini` would be scope the feature does not need — `python3 -m pytest tests/ -q`
already collects a bare directory of test modules, which is how the existing
suite is collected.

## Implementation approach

### Behaviour 1 — the prune

The current file list is one expression:

```python
files = sorted(target.rglob("*.y*ml")) if sweep else [target]
```

`rglob` cannot be told not to descend. Replacing it with an explicit walk is
therefore forced, and the walk is where the prune lives: at each directory, if it
is not the scan root and `dir / ".git"` exists, do not descend and record the path
as pruned. `SKIP_DIR_NAMES` keeps its current job unchanged — it still filters the
resulting paths by parts, so `.git`, `node_modules`, `__pycache__` and `.venv`
behave exactly as before, including the pre-existing quirk that the match is
against the RESOLVED absolute path's parts.

`os.walk` with in-place `dirnames[:]` pruning is the mechanism: it is stdlib, it
prunes by contract, and it visits each directory once. The results are sorted so
the adjudication order — and therefore the finding order — is deterministic and
matches today's `sorted(rglob(...))`.

The scan-root comparison is by RESOLVED path (`target` is already
`Path(args.path).resolve()` at `:2151`), so a root reached through a symlink is
still recognised as the root.

The prune note lists paths RELATIVE to the scan root, sorted, for the same reason
the register note does: a line that differs between a laptop and a CI runner
cannot be asserted by a downstream test.

### Behaviour 2 — the register note

One `f.note` inside `check_register`, placed at the earliest point where BOTH
facts the note reports are known: after `reg` is confirmed a mapping, the version
is accepted, and `rows` is confirmed a list. Placing it there — rather than at the
end of the function — means the note reports "the file was read and its rows
parsed", which is precisely the claim D3's positive proof needs, and it fires
alongside per-row findings rather than only when every row is clean. Placing it
before the version check was rejected: a register the reader refuses to interpret
has not been meaningfully READ, and the row count would be unavailable.

`Findings.note` already de-duplicates (`:349`), so "exactly one" is structural.

### Why the corpus-identity test needs the ORIGINAL script

Proving FR-009 and SC-002 means comparing this version's finding set against the
PREVIOUS version's on the same tree. The previous version is recoverable without
touching the working tree: `git show <base>:scripts/validate-openxwallet.py`
written to a temp file, then run with `cwd` set to the repository root so its
`ROOT`-relative constants still resolve. No `git stash`, no checkout, no mutation
of anything.

## Complexity Tracking

*No Constitution Check violations to justify. Rule 6's partial is a deferral to a
named owner (`[OPERATOR]`, §4.8), not a violation.*

One design cost is worth recording even though it is not a violation:

| Cost | Why accepted | Alternative rejected because |
|------|--------------|------------------------------|
| `rglob` replaced by an explicit `os.walk` | `rglob` cannot be stopped from descending, so a prune is impossible without it. The walk is ~15 lines and its output is sorted to preserve today's deterministic order. | Filtering `rglob`'s results after the fact would still WALK the nested repository (the cost the prune exists to avoid) and would need an ancestor-chain `.git` test per file instead of one per directory. |
