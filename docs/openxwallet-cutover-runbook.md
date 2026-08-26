# openXwallet cutover runbook

Status: record
Ratified by: `split-openxwallet-repo` (openxFactory, 2026-08-26, PR #391)
Realized by: openxFactory Speckit feature `017-openxwallet-carve`

**This document was authored BEFORE the carve it describes.** Each phase carries
its rollback, and each rollback was written before that phase was taken. A
rollback written afterwards is not a rollback; it is a description of what
happened.

## The NAMED CARVE COMMIT

```
CARVE_COMMIT = 30565e48ffe3d8a9773e10af33425701845e10f6
```

openxFactory, "Merge pull request #396 from opensoft/016-openxwallet-split-bookkeeping".

**Never "HEAD."** HEAD is not a referent across a multi-pull-request wave, and
this wave proved it: openxFactory's `main` moved to `bb7d7ae8` between the commit
being frozen and the carve being taken (six commits, PR #392). The carve is
anchored at `30565e48` regardless — and the twelve path sets are untouched by that
move, which was checked rather than assumed.

The commit is recorded in three places, one of them machine-read:

1. `contracts/manifest.yaml` → `carved_from: {repository, commit}` — machine-read.
2. This runbook — the procedure.
3. openxFactory's `contracts/openxwallet-pin.yaml` → `carve_commit:` — **at P3**.

There is deliberately **no bare `CARVE_COMMIT` file**: an unschema'd file nothing
reads is the failure class of a governance floor whose source of truth is loose
markdown.

---

## Phase 1 — the case-variant repository-name check

**ROLLBACK (written first): nothing has happened yet.** No repository, no clone,
no commit. Abandoning here costs nothing.

GitHub repository names are case-insensitive-unique, so `openxwallet`,
`OpenXWallet` or any other casing — in the organisation or in a fork — collides
with `openXwallet`. **Checked and recorded FIRST, because discovering it after a
carve costs the carve.**

```sh
for n in openXwallet openxwallet OpenXWallet openXWallet OPENXWALLET; do
  gh repo view "opensoft/$n"
done
gh search repos openxwallet --owner opensoft
gh search repos openxwallet            # unscoped, catches forks
```

**Pass condition**: every one absent. **On any hit: STOP and report.** Do not
carve, do not create.

---

## Phase 2 — repository creation, the carve, and the completeness check

**ROLLBACK (written first): delete the scratch clone; if the repository was
already created, `gh repo delete opensoft/openXwallet`.** Nothing pins openXwallet
until P3, so deletion restores the world exactly. openxFactory is untouched by
this whole phase — the carve COPIES and deletes nothing.

### 2a. The clone

A **fresh** clone, never the shared checkout: a carve must read a tree nobody else
is editing.

```sh
git clone git@github.com:opensoft/openxFactory.git openxFactory-src
git -C openxFactory-src checkout "$CARVE_COMMIT"
```

### 2b. The control

Before the carve, recompute the eight recorded `sha256:` values in
`contracts/manifest.yaml` over the files their rows name, at `$CARVE_COMMIT`.
**Expect 8/8.** Without this control, a post-carve match would prove the manifest
stale rather than the carve faithful.

### 2c. The carve

`git filter-repo`, one `--path` per set, exact paths, **no globs and no
`--path-rename`**, over the twelve ratified path sets:

| # | Path set |
| --- | --- |
| 1 | `contracts/openxwallet/` |
| 2 | `contracts/openxwallet-agent-profile/` |
| 3 | `scripts/validate-openxwallet.py` |
| 4 | `scripts/wallet-yaml-syntax-gate.py` |
| 5 | `tests/wallet_yaml_syntax_gate/` |
| 6 | `.github/workflows/wallet-validation.yml` |
| 7 | `openspec/specs/openxwallet/` |
| 8 | `openspec/specs/openxwallet-agent-profile/` |
| 9 | `openspec/changes/archive/2026-08-08-add-openxwallet/` |
| 10 | `specs/006-openxwallet-contracts/` |
| 11 | `specs/010-wallet-validator-ci/` |
| 12 | `specs/012-wallet-issuer-anchor/` |

Full path history. A squashed import, or a history that starts at the move, is
unbisectable and is not this carve.

### 2d. The completeness check

```sh
git -C openxFactory-src ls-tree -r --name-only "$CARVE_COMMIT" -- <the twelve> | sort > expected.txt
git -C openXwallet ls-files | sort > actual.txt
diff expected.txt actual.txt        # MUST be empty
```

**Expected: 100 files, empty diff.**

Two path sets are named explicitly because a shorthand loses them:

- **`specs/006-openxwallet-contracts/evidence/`** — the `evidence/` subtree is
  inside the 7-file count and is easy to lose to a shallow copy.
- **`contracts/openxwallet/examples/negative/`** — the intended-invalid corpus.

**A correction to the ratified shorthand, recorded rather than silently
absorbed.** Ratified task 3.7 asserts "36 under
`contracts/openxwallet/examples/negative/`". Measured at the carve commit, that
directory holds **32**; the other **4** are in the second family,
`contracts/openxwallet-agent-profile/examples/negative/`. 32 + 4 = 36. The
assertion is therefore carried in the form the shorthand collapsed:

| Assertion | Expected |
| --- | --- |
| `specs/006-openxwallet-contracts/` (incl. `evidence/`) | 7 |
| `contracts/openxwallet/examples/negative/` | 32 |
| `contracts/openxwallet-agent-profile/examples/negative/` | 4 |
| both negative trees (the ratified "36") | **36** |

Asserting "36 in the core family" would FAIL against a correct carve and send an
operator hunting four files that were never there. This is exactly the failure
mode task 3.7 exists to prevent, applied to task 3.7's own text.

### 2e. Examples-prefix preservation — an acceptance line, not a hope

Both `contracts/openxwallet/examples/` and
`contracts/openxwallet-agent-profile/examples/` must exist at **identical relative
paths**. The validator's corpus exclusion keys on `"examples" in path.parts` AND a
part in `("openxwallet", "openxwallet-agent-profile")`, so a carve that flattened
or renamed either prefix would re-adjudicate 36 intended-invalid negatives as LIVE
records — inside a check that becomes REQUIRED.

---

## Phase 3 — CODEOWNERS, then the ruleset in EVALUATE, then ACTIVE

**ROLLBACK (written first): `PATCH` the ruleset back to `enforcement: evaluate`,
or `DELETE` the ruleset.** Neither act touches a commit. If the repository itself
must go, Phase 2's rollback still applies — nothing pins openXwallet yet.

### 3a. `.github/CODEOWNERS`

The validator, the syntax gate, the pin verifier, `contracts/`,
`contract_pin.yaml` and `.github/workflows/`.

### 3b. The ruleset, in EVALUATE

```sh
gh api -X POST repos/opensoft/openXwallet/rulesets --input ruleset.json
```

Mirroring openxFactory ruleset **21538893**: `target: branch`,
`conditions.ref_name.include: ["~DEFAULT_BRANCH"]`, one `required_status_checks`
rule with `strict_required_status_checks_policy: false`,
`do_not_enforce_on_create: false`, and the contexts `wallet-validation` and
`pytest-suite` — both, because 21538893 requires both.

### 3c. **Day-one REQUIRED is impossible**

Stated plainly, as unachievable rather than promised: **GitHub cannot require a
status check that has never reported in the repository.** The context is not
selectable until a workflow has reported under it once. So there is no
configuration, no ordering and no flag that makes the gate REQUIRED on the day the
repository is created. The EVALUATE → report → ACTIVE sequence is not a
convenience; it is the only path GitHub offers.

### 3d. One trivial pull request

A README touch, so both checks report once and become selectable. Then merge it.

### 3e. Promote to ACTIVE

```sh
gh api -X PATCH repos/opensoft/openXwallet/rulesets/<id> -f enforcement=active
gh api repos/opensoft/openXwallet/rules/branches/main      # the evidence
```

---

## Phase 4 — tag `wallet-v1.0`

**ROLLBACK (written first): delete the tag, locally and on the remote.** Nothing
pins `wallet-v1.0` until P3 records it, so a deleted tag is a non-event.

**Only after the byte-identity proof is green.** Both parts, no exceptions:

### Part one — the eight digests

For each of the eight digested artifacts, `sha256sum` at `wallet-v1.0` EQUALS the
`sha256:` recorded at the NAMED CARVE COMMIT.

| # | id | recorded == recomputed |
| --- | --- | --- |
| 1 | `openxwallet-record` | filled by the proof run |
| 2 | `openxwallet-custody-registry-schema` | filled by the proof run |
| 3 | `openxwallet-custody-registry` | filled by the proof run |
| 4 | `openxwallet-grant` | filled by the proof run |
| 5 | `openxwallet-grant-exercise` | filled by the proof run |
| 6 | `openxwallet-distinct-holder-constraint` | filled by the proof run |
| 7 | `openxwallet-subject-attestation` | filled by the proof run |
| 8 | `openxwallet-agent-composition` | filled by the proof run |

### Part two — the empty diff, and the two-line carve-out

`git diff` EMPTY against the carve commit over `contracts/openxwallet/`,
`contracts/openxwallet-agent-profile/`, `scripts/validate-openxwallet.py`,
`scripts/wallet-yaml-syntax-gate.py`, `tests/wallet_yaml_syntax_gate/`, the three
Speckit sets and the archive packet — **and diff-limited-to-two-lines** over each
promoted spec, asserted line by line at `:4` and `:8`.

The full record, with reproducible commands, is
[`byte-identity-wallet-v1.0.md`](./byte-identity-wallet-v1.0.md).

```sh
git tag -a wallet-v1.0 -m "wallet-v1.0 — byte-identical carve of openxFactory@<CARVE_COMMIT>"
git push origin wallet-v1.0
```

---

## Phase 5 — submodule init in openxFactory and in the xFactory aggregation

**ROLLBACK (written first): `git submodule deinit` the gitlink and revert the pin
commit.** This phase belongs to **P3 and P4**, not to P2; it is recorded here
because the runbook is the wave's procedure and an operator reading it needs the
whole arc.

Then the byte-identity proof is **re-run from each consuming checkout**, because a
proof that holds only in the carving operator's scratch directory is a proof about
that directory.

---

## Phase 6 — rollback per phase, collected

| Phase | Rollback | Cost |
| --- | --- | --- |
| 1 — name check | nothing happened | zero |
| 2 — clone + carve | delete the scratch clone; `gh repo delete` if created | zero; openxFactory untouched |
| 3 — ruleset | PATCH back to `evaluate`, or DELETE the ruleset | zero commits touched |
| 4 — tag | delete the tag locally and on the remote | zero; nothing pins it until P3 |
| 5 — submodule init | `git submodule deinit` + revert the pin commit | one revert in the consumer |

**The P2-wide rollback**: nothing pins openXwallet yet — delete the repository, or
leave it unpinned. **openxFactory is untouched by P2 in either case.** The carve
COPIES; P3's deletions are P3's own commit, and P2 makes none.

---

## What P2 deliberately does NOT do

- It does not delete one byte from openxFactory. That is **P3**.
- It does not cut `wallet-v1.1`. That is **P2b** — the nested-repository prune and
  the register-read note, the one auditable additive-minor diff on top of the
  byte-identical first release.
- It does not emit a deprecation warning anywhere. That is **P2.5**, and it is
  manifest-carried, never validator-carried.
- It does not pin openXwallet from anywhere. Until it is pinned, it is reversible.
