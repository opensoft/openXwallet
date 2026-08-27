# Phase 1 Data Model: wallet-v1.1

**Feature**: `013-nested-repo-prune-register-note`
**Date**: 2026-08-26

This feature adds no contract, no schema and no persisted record. Its "data
model" is the set of run-time entities the sweep and the reader reason about, and
the rules that decide each one's fate. It is written down because the prune's
correctness is entirely a question of which entity a given path belongs to.

---

## Entities

### Scan root

The single directory the validator is pointed at, resolved to an absolute path
(`main()`: `target = Path(args.path).resolve()`).

| Property | Value |
|----------|-------|
| Cardinality | exactly one per run, or none (self-test only) |
| Identity | its RESOLVED path — so a root reached through a symlink is the same root |
| Governs | the register's location: the reader joins the scan root with `governance/review-authority/` |
| Prune status | **never pruned**, even when it carries a `.git` entry. The ordinary case is a repository scanning itself. |

A sweep happens only when the scan root is a directory. A file target is
adjudicated directly, with no sweep, no prune and no register read.

### Nested repository

Any directory strictly below the scan root that carries a `.git` entry.

| Property | Value |
|----------|-------|
| Detection | `(<dir> / ".git").exists()` — existence only; neither the entry's type nor its contents are read |
| Shapes | a `.git` FILE (submodule checkout, `git worktree`) or a `.git` DIRECTORY (a nested clone). Both qualify. |
| Effect | the directory is not descended into; nothing at or below it enters the candidate set |
| Reported as | one path, relative to the scan root, in the prune note |
| Nesting | a nested repository inside a pruned one is never reached, so it is never reported separately |

### Candidate file

A path the walk yielded that matches `*.y*ml` and survives the prune.

Its fate is then decided by three further rules, in this order — all three
unchanged by this feature:

1. **Skip-set filter.** Dropped if any part of its path is in
   `{".git", "node_modules", "__pycache__", ".venv"}`.
2. **Packaged-corpus rule.** Dropped if `"examples"` is a path part AND some part
   is `openxwallet` or `openxwallet-agent-profile`. This keys on PARTS, so it
   holds inside a nested repository too — the prune and this rule can both fire on
   one path, which is not an error.
3. **Kind filter.** Counted as "skipped as another kind" unless it parses as a
   mapping carrying a known family `kind:`; and the canonical custody registry is
   excluded by resolved-path identity.

### Adjudicated record

A candidate that survived all four filters. Indexed into a context of the scanned
repository's own records FIRST, then validated — the existing two-pass order,
unchanged.

### Intake register

The file at `<scan root>/governance/review-authority/register.yaml`.

| State | Existing behaviour | This feature |
|-------|--------------------|--------------|
| absent, no review-class grants | note: "no intake register at this tree; nothing to read" | unchanged; the new note is absent |
| absent, review-class grants present | `register-no-active-row` error | unchanged |
| present, unparseable / not a mapping | `register-unparseable` | unchanged; no new note (the read did not succeed) |
| present, unknown `register_version` | `register-version-unknown` | unchanged; no new note |
| present, `rows` not a list | `register-row-malformed` | unchanged; no new note |
| **present, rows parsed as a list** | silent on success | **one NOTE naming the relative path and the row count** |

### Finding

The validator's three output classes, and the reason the class of a new line is a
compatibility decision:

| Class | Carries a code | Affects exit code | This feature adds |
|-------|----------------|-------------------|-------------------|
| error | yes | always | none |
| warning | yes | only under `--strict` | **none — and this is the constraint** |
| note | no | never | two |

A live consumer pins finding-code STRINGS and runs `--strict`. A warning would
red-line that consumer's required check; a note cannot. Neither new line carries a
code, so neither can collide with a pinned string.

---

## State transitions

The only transition this feature introduces is in the directory walk:

```text
directory reached
   ├── is the scan root? ──────────────────► DESCEND (always)
   └── otherwise
         ├── carries a .git entry? ────────► PRUNE  (record path, do not descend)
         └── no .git entry ───────────────► DESCEND
```

And in the reader:

```text
register path resolved
   ├── does not exist ──► existing absent-register behaviour (unchanged)
   └── exists
         ├── parse fails / not a mapping / bad version / rows not a list
         │        └────────► existing findings (unchanged), NO note
         └── rows is a list ─► EMIT NOTE (path relative to scan root, row count)
                               then proceed to the existing per-row obligations
```

## Validation rules, as invariants

- **I1**: no adjudicated record's path descends from a nested repository.
- **I2**: the scan root's own `.git` entry never removes a record from
  adjudication.
- **I3**: the set of errors and warnings over the packaged corpus is identical to
  the previous version's.
- **I4**: at most one register-read note per run, and exactly one when the
  register's rows parsed. (`Findings.note` de-duplicates by line, so this is
  structural rather than defended.)
- **I5**: no new line is a warning; `--strict` over this repository exits 0.
- **I6**: adjudication order is deterministic and equals sorted-path order, as it
  is today.
