# Phase 1 Contract: the validator's command line and output lines

**Feature**: `013-nested-repo-prune-register-note`
**Date**: 2026-08-26

`scripts/validate-openxwallet.py` is a CLI, and its command line plus its output
lines ARE its public interface — pinned by name in other repositories. This file
states that interface before and after, so the diff is checkable against a
declared contract rather than against a reading of the code.

---

## 1. Command line — FROZEN, byte for byte

```text
usage: validate-openxwallet.py [-h] [--strict] [path]

positional arguments:
  path        repo checkout (or single file) to scan for real openxWallet
              artifacts; omit to self-test only

options:
  -h, --help  show this help message and exit
  --strict    treat warnings as errors
```

**Options added by this feature: 0. Options removed: 0.** No `--exclude`, no
`--no-prune`, no `--skip`. §4.3 of the governing change refuses a caller-supplied
exclusion by name, on two grounds: it edits the argparse surface a downstream test
pins, and an exclusion the caller supplies is one the caller can omit — a vacuous
pass waiting to happen.

The prune is therefore UNCONDITIONAL. There is no way to ask for the old
behaviour, which is deliberate: the old behaviour is the defect.

## 2. Exit codes — FROZEN

| Code | Meaning |
|------|---------|
| 0 | no errors, and (under `--strict`) no warnings |
| 1 | at least one error, or at least one warning under `--strict` |
| 2 | harness failure: a family directory or the vendored schema is missing, a schema fails to load, or the named path does not exist |

Unchanged. Notes never affect any of them.

## 3. Output lines

Order is fixed by the reporter: all notes, then all warnings, then all errors,
then the summary line.

### 3.1 Lines that already exist and MUST NOT change

| Line | Class |
|------|-------|
| `note  approval-scope vocabulary read from <path>: [...]` | note |
| `note  corpus: 17 positive example(s), 36 negative confirmation(s) across 13/13 requirements` | note |
| `note  no intake register at this tree; nothing to read` | note |
| `note  repo scan: N openxWallet artifact(s) validated, M document(s) skipped as another kind` | note |
| `validate-openxwallet: N error(s), M warning(s)` | summary |
| every `ERROR [<code>] ...` and `WARN  [<code>] ...` | error / warning |

**Every finding CODE is frozen.** LedgerxFactory pins code strings by name. This
feature adds no code and renames none.

### 3.2 Lines this feature ADDS — both notes

**The prune note**, emitted once per sweep, only when at least one nested
repository was pruned:

```text
note  nested repositories pruned (not adjudicated): <rel/path>, <rel/path>, ...
```

- Paths are RELATIVE to the scan root and sorted.
- Paths only — no `.git` entry type, no reason, no count of what was skipped.
  §4.1 asks for the paths; anything more is output a downstream reader would then
  depend on.
- Absent entirely when nothing was pruned, so a clean tree's output is unchanged.

**The register-read note**, emitted once per successful read:

```text
note  intake register read: <rel/path> (N row(s))
```

- `<rel/path>` is the register file's path relative to the scan root — in practice
  always `governance/review-authority/register.yaml`. Relative, so the line is
  identical on a developer's machine and a CI runner and can therefore be
  asserted by the downstream consumer-gate test.
- `N` is the number of rows read, from the parsed `rows` list.
- Emitted immediately after `rows` is confirmed to be a list, so it reports "the
  register was read and its rows parsed" — not "the register was clean". It
  therefore appears alongside per-row findings, which is when an auditor most
  needs to know WHICH register produced them.
- Not emitted when the register is absent, unparseable, of an unknown version, or
  carries a non-list `rows`.

### 3.3 The class of both new lines is `note`, and that is a contract term

Not cosmetic. `report()` reds a `--strict` run on warnings, and a live consumer
runs `--strict`. A warning here would red-line a required check in a repository
that never asked for this change. §4.5 states it as "an `f.note`, **never a
warning**"; this contract restates it so a future edit that "promotes" the line
for visibility has to break a written term to do it.

## 4. What a consumer may rely on after this release

1. Pointing the validator at its OWN checkout root adjudicates its own records
   only — no nested repository's YAML is treated as a live record.
2. Its register, if present and parseable, produces one note naming it.
3. Its `--strict` run's exit code is unchanged from `wallet-v1.0` for any tree
   that contains no nested repository.
4. For a tree that DOES contain one, the exit code may IMPROVE (findings that were
   raised against another repository's files disappear) and can never worsen: the
   prune only ever removes candidates.
5. Every finding code it pins by name still exists and still means what it meant.
