# Phase 0 Research: wallet-v1.1

**Feature**: `013-nested-repo-prune-register-note`
**Date**: 2026-08-26

No `NEEDS CLARIFICATION` markers entered this phase — the governing ratified
change decided the mechanism and the class. What research remained was factual:
measure the current behaviour so the change can be proven not to have disturbed
it, and confirm the two shapes a nested repository actually takes on disk.

---

## R1 — The current sweep, measured rather than assumed

**Finding.** `repo_scan` (`scripts/validate-openxwallet.py:2037`) builds its file
list as `sorted(target.rglob("*.y*ml"))` and applies exactly two exclusions:

| Exclusion | Line | Keys on |
|-----------|------|---------|
| `set(path.parts) & SKIP_DIR_NAMES` | `:2044` | path PARTS, against `{".git", "node_modules", "__pycache__", ".venv"}` (`:295`) |
| the packaged-corpus rule | `:2050-2053` | `"examples" in path.parts` AND an `openxwallet`/`openxwallet-agent-profile` part |

**Consequence, stated exactly.** `SKIP_DIR_NAMES` matches a path COMPONENT named
`.git`. A submodule checkout has no such component — it has a `.git` FILE
containing `gitdir: ...`, and that file is not a `*.y*ml`, so it is never in the
list and its containing directory is never excluded. Every YAML below a submodule
is therefore adjudicated as a live record of the scanned tree.

**Baseline captured on this branch's base**, `python3 scripts/validate-openxwallet.py .`:

```text
note  approval-scope vocabulary read from contracts/schemas/hermes-job-envelope.schema.yaml: [...]
note  corpus: 17 positive example(s), 36 negative confirmation(s) across 13/13 requirements
note  no intake register at this tree; nothing to read
note  repo scan: 0 openxWallet artifact(s) validated, 20 document(s) skipped as another kind

validate-openxwallet: 0 error(s), 0 warning(s)      exit 0
```

The corpus counts are independently confirmed by counting files: 15 + 2 = **17
positives**, 32 + 4 = **36 negatives**. This matches the spec's numbers and the
governing change's, so the corpus-identity assertion has a checkable target.

**Decision.** The corpus-identity test compares FINDING SETS (errors and
warnings), not note lines. Notes are facts about the run and this feature adds
two of them by design; asserting on the note list would make the test assert the
opposite of the feature. Errors and warnings are what a consumer's exit code turns
on, and they are what must not move.

---

## R2 — The two on-disk shapes of a nested repository

**Finding.** A `.git` entry below a scan root occurs in exactly two shapes, and
they are not interchangeable:

| Shape | Produced by | On disk |
|-------|-------------|---------|
| `.git` FILE | `git submodule update --init`, and `git worktree add` | a text file whose first line is `gitdir: <path>` |
| `.git` DIRECTORY | a plain `git clone` nested inside another tree | a directory |

**Decision.** The prune tests for EXISTENCE of the `.git` entry and does not read
it or stat its type. Rationale: both shapes mean "a different repository's
history governs everything below here", which is the property the prune is about;
distinguishing them would add a branch with no behavioural difference and would
make a dangling symlink behave differently from a broken gitdir file for no
stated reason. `Path.exists()` follows symlinks, so a `.git` symlink that resolves
prunes and one that dangles does not — the conservative outcome in both
directions, because a prune only ever NARROWS what is adjudicated.

**Alternatives considered.** *Reading the `gitdir:` line to confirm it is a real
submodule* — rejected: it makes the product's validator an expert on git's
internal layout, and a worktree's `.git` file is equally a nested repository for
this purpose. *Consulting `.gitmodules` at the scan root* — rejected: it detects
only DECLARED submodules, misses an ad-hoc nested clone (exactly the
`installs/omnigent-install` class of hole), and would read a file the validator
has no business reading.

---

## R3 — Why `rglob` has to go, and what replaces it

**Finding.** `Path.rglob` offers no way to stop descending; a prune implemented as
a post-hoc filter over its results still walks the entire nested repository and
must then test each file's ancestor chain for a `.git` entry.

**Decision.** `os.walk(target)` with in-place `dirnames[:]` mutation. It is
stdlib, its pruning contract is documented, it visits each directory exactly once,
and the `.git` test is therefore one existence check per directory rather than one
ancestor-chain scan per file. Results are sorted before use so the adjudication
order — and hence the order findings appear in — matches today's
`sorted(rglob(...))` exactly.

**Consequences accepted.** On a tree containing a nested repository the new code
visits strictly FEWER paths than the old one, so this is a performance improvement
rather than a cost. On a tree with none, it visits the same paths.

**Alternatives considered.** *`Path.walk()`* (3.12+) — equivalent, and the
repository's floor IS 3.12, but `os.walk` is the form the wider house code uses
and needs no version note. *A recursive helper* — more code, same result, and it
would owe its own recursion-depth argument.

---

## R4 — Where the register note goes, and what it says

**Finding.** `check_register` (`:1855`) has five early-return failure paths before
any row is examined: absent register (`:1867`, which either errors or emits the
ratified "nothing to read" note), unparseable, not-a-mapping, unknown version, and
`rows`-not-a-list. The row count is only known after the fourth.

**Decision.** The note is emitted immediately after `rows` is confirmed to be a
list — the earliest point at which both facts it reports (the path, the row count)
are established. Its text names the register RELATIVE to the scan root.

**Rationale for relative.** The downstream consumer-gate test (D3, landing at P3)
asserts on this line. An absolute path differs between a developer's checkout and
a CI runner's workspace, so an absolute path would make that test either brittle
or forced into a substring match. The relative path
`governance/review-authority/register.yaml` is invariant, and it is the same
string codexFactory's merge-gate floor names — so one string serves all three
readers.

**Rationale for including the row count.** It distinguishes "opened a register"
from "opened a register that had rows in it", which is the difference between a
read and a vacuous read. It is also the one number the reader knows that no other
output line carries.

**Alternatives considered.** *At the end of the function, only when clean* —
rejected: it would make the note report "no findings" rather than "the register
was read", and the positive-read proof would then be unavailable on exactly the
runs where an auditor most wants it. *Before the version check* — rejected: a
register whose version the reader refuses is not meaningfully read, and the row
count is not yet known. *Naming the absolute path as well as the relative one* —
rejected: two paths on one line, one of them unassertable.

---

## R5 — Proving the corpus is adjudicated identically

**Finding.** The comparison needs the PREVIOUS version of the script running
against the SAME tree, without mutating the working tree (a hard limit: no
stash, no checkout, no force anything).

**Decision.** `git show <base-ref>:scripts/validate-openxwallet.py` into a
temporary file, executed as a subprocess with `cwd` at the repository root. The
script's `ROOT` is derived from its own location, so the temp copy must be run
with the repository's paths reachable — resolved by writing the temp copy INTO a
temporary directory and passing the repository root as the scan target, then
comparing finding sets. Where the script's `ROOT`-relative constants make an
out-of-tree copy unrunnable, the copy is written beside the original under a
distinct name inside `scripts/` for the duration of the test and removed
afterwards; the test is responsible for its own cleanup either way.

**Consequence.** The test is skipped, loudly and with a reason, when git history
is unavailable (a tarball export, a shallow clone without the base commit). A
skip that says why is honest; a silent pass is the vacuous-pass class this whole
wave refuses.

---

## R6 — What the release bookkeeping must and must not touch

**Finding.** `contracts/manifest.yaml` carries `contract_bundle_version:
wallet-v1.0` at `:28` and eight owned rows each with a `sha256:`. The eight
digests are the byte-identity floor's subject.

**Decision.** Exactly one line of the manifest changes: the bundle version. Every
`sha256:` stays. The verification is mechanical — `sha256sum` over the eight
paths, compared against the eight values in the file — and it is run and recorded,
not asserted.

**Also decided: what does NOT change.** Per-file `contract_schema_version` values
stay, because no contract file changes; that is what makes this release additive.
`docs/pin-resync-runbook.md` stays untouched — `grep -in "sweep|rglob|repo_scan|SKIP_DIR"`
over it returns nothing, so it does not describe the behaviour this feature
changes.

---

## Open questions carried forward

None. Every unknown that entered Phase 0 is resolved above, and the two
behavioural decisions were never this feature's to make.
