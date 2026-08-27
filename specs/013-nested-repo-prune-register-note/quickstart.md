# Phase 1 Quickstart: validating wallet-v1.1

**Feature**: `013-nested-repo-prune-register-note`
**Date**: 2026-08-26

Every command below is offline and reads nothing outside the two checkouts named.
Run them from the feature worktree root unless a step says otherwise.

```sh
WT=/home/brett/projects/openXwallet-worktrees/P2b
```

## Prerequisites

```sh
python3 --version                       # 3.12+, the version both workflows pin
python3 -c "import yaml, jsonschema"    # pyyaml, jsonschema
python3 -m pytest --version             # pytest, for the suite
```

`rfc3339-validator` is installed by both workflows and used through
`jsonschema`'s format checking.

## 1. The six gates AGENTS.md rule 5 requires before any push

```sh
cd "$WT"
python3 scripts/verify-contract-pin.py            # the vendored artifact's digest
python3 scripts/wallet-yaml-syntax-gate.py .
python3 scripts/validate-openxwallet.py .
python3 scripts/validate-openxwallet.py . --strict
python3 -m pytest tests/ -q
OPENSPEC_TELEMETRY=0 openspec validate --all --strict
```

**Expected**: all six exit 0. The two validator runs must produce IDENTICAL
error and warning sets (there are none of either on a clean tree) — the `--strict`
run exiting 0 is the proof that neither new line is a warning.

**Expected note lines** on this repository's own tree: the four that exist today,
plus nothing new — this tree carries no nested repository (a git WORKTREE's `.git`
is a file, so a worktree checkout DOES prune nothing because the `.git` file sits
at the scan ROOT, which is never pruned) and no intake register.

## 2. The prune, proven on a scratch tree

The new test module does this hermetically; this is the same proof by hand.

```sh
cd "$(mktemp -d)"
mkdir -p root/nested-submodule root/nested-clone/.git root/plain
printf 'gitdir: ../.git/modules/x\n' > root/nested-submodule/.git

# The SAME record in three places: two nested, one not.
for d in root/nested-submodule root/nested-clone root/plain; do
  cp "$WT"/contracts/openxwallet/examples/wallet-practitioner.example.yaml "$d"/live.yaml
done

python3 "$WT"/scripts/validate-openxwallet.py "$PWD/root"
```

**Expected**: the `repo scan:` note reports **1** artifact validated, not 3; a
prune note names `nested-clone` and `nested-submodule`; exit 0.

**Before this feature** the same command reports 3 validated.

## 3. The register-read note, proven on a scratch tree

The test module builds a minimal valid register plus the grant, wallet and
attestation it must resolve against. By hand, the shortest sufficient check is
that the note fires and `--strict` still exits 0:

```sh
python3 "$WT"/scripts/validate-openxwallet.py <a tree carrying a register> --strict
```

**Expected**: one line
`note  intake register read: governance/review-authority/register.yaml (1 row(s))`
and exit 0.

**Expected on a tree with NO register**: the ratified
`note  no intake register at this tree; nothing to read` and NO register-read
note.

## 4. Corpus identity — the 17 positives and 36 negatives adjudicate the same

```sh
cd "$WT"
git show HEAD:scripts/validate-openxwallet.py > /tmp/v10-validator.py   # the previous version
```

The test module automates the comparison (see `research.md` R5 for why the
previous version is recovered from git history rather than by stashing). By hand:
run both versions against the repository root and diff the ERROR and WARNING
lines only — notes differ by design.

**Expected**: an empty diff over errors and warnings; both exit 0.

## 5. The eight digests are unchanged

```sh
cd "$WT"
sha256sum \
  contracts/openxwallet/openxwallet-record.schema.yaml \
  contracts/openxwallet/openxwallet-custody-registry.schema.yaml \
  contracts/openxwallet/openxwallet-custody.registry.yaml \
  contracts/openxwallet/openxwallet-grant.schema.yaml \
  contracts/openxwallet/openxwallet-grant-exercise.schema.yaml \
  contracts/openxwallet/openxwallet-distinct-holder-constraint.schema.yaml \
  contracts/openxwallet/openxwallet-subject-attestation.schema.yaml \
  contracts/openxwallet-agent-profile/openxwallet-agent-composition.schema.yaml
grep -n 'sha256:' contracts/manifest.yaml
```

**Expected**: 8 computed digests, each equal to the `sha256:` on its manifest row.
`git diff --stat HEAD -- contracts/openxwallet contracts/openxwallet-agent-profile`
must be EMPTY: this release touches no contract byte.

## 6. The end-to-end proof: a real consumer's tree

The proof the governing change actually asks for (§4.1, §4.5) is a run from a real
consumer root that has both a nested repository and a live register. openxFactory
is that tree. **Read-only** — the validator writes nothing.

```sh
python3 "$WT"/scripts/validate-openxwallet.py /home/brett/projects/xFactory/openxFactory
```

**Expected**:
- a prune note naming `installs/omnigent-install` — the nested submodule the sweep
  walks into today, and the reason §4.2 insists the rule is general rather than
  wallet-shaped;
- a register-read note naming `governance/review-authority/register.yaml`;
- exit 0.

## 7. What is NOT validated here

- The `wallet-v1.1` tag and its `wallet-v1.1.digests.yaml` — `[OPERATOR]` acts at
  §4.8, after the human merge.
- The LedgerxFactory estate run — §4.9, that repository's own evidence.
- The consumer-gate invocation test — D3, landing at P3 in openxFactory.
