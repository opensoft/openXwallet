# Byte-identity proof — `wallet-v1.0`

Status: record

**The claim.** openXwallet `wallet-v1.0` is a **byte-identical pure move** of
twelve path sets out of openxFactory at one named commit. Not "essentially the
same". Not "only cosmetic differences". Byte-identical, with two prose lines and
one workflow step declared as the complete set of exceptions.

**Why the claim matters more than it looks.** A move whose diff is not provably
empty cannot be bisected against. openxFactory's later atomic consume-and-shed
(P3) deletes eight artifacts and repoints its own REQUIRED check at a pinned
reader in this repository, in one pull request. That is safe to merge only if the
bytes leaving one repository are demonstrably the bytes arriving in the other. So
this document is not a report; it is the precondition of a tag.

## The NAMED CARVE COMMIT

```
CARVE_COMMIT = 30565e48ffe3d8a9773e10af33425701845e10f6
```

openxFactory, *"Merge pull request #396 from opensoft/016-openxwallet-split-bookkeeping"*.

**Never "HEAD"**, which is no referent across a multi-pull-request wave — and this
wave demonstrated why: openxFactory's `main` moved to `bb7d7ae8` between the
commit being frozen and the carve being taken (six commits, PR #392). The carve
stayed anchored, and the twelve path sets were verified untouched by that move:

```sh
$ git diff --name-only 30565e48..origin/main -- <the twelve path sets>
(no output)
```

Recorded in three places, one machine-read: `contracts/manifest.yaml`'s
`carved_from:`, this repository's cutover runbook, and (at P3) openxFactory's
`contracts/openxwallet-pin.yaml` `carve_commit:`.

## How to reproduce this document

Everything below uses repo-relative paths and `$SRC` / `$W` placeholders for the
two checkouts, so no host path is baked into the record:

```sh
git clone git@github.com:opensoft/openxFactory.git "$SRC"
git -C "$SRC" checkout 30565e48ffe3d8a9773e10af33425701845e10f6
git clone git@github.com:opensoft/openXwallet.git "$W"
```

---

## Part zero — the CONTROL, taken before the carve

If the eight recorded digests did not already describe the carve commit's bytes,
a post-carve match would prove the manifest **stale** rather than the carve
**faithful**. So the control comes first, and it is part of the proof.

| # | id | recorded `sha256:` in openxFactory@CARVE_COMMIT | recomputed there | match |
| --- | --- | --- | --- | --- |
| 1 | `openxwallet-record` | `2012ef432616e73ddaead17c5e79aefa…` | `2012ef432616e73ddaead17c5e79aefa…` | YES |
| 2 | `openxwallet-custody-registry-schema` | `df72638497a7f90c2a4dff47c429cb79…` | `df72638497a7f90c2a4dff47c429cb79…` | YES |
| 3 | `openxwallet-custody-registry` | `94d631d6ee76dab015628a1856afd825…` | `94d631d6ee76dab015628a1856afd825…` | YES |
| 4 | `openxwallet-grant` | `fde433c5821e2e6f62926a72c58a67a7…` | `fde433c5821e2e6f62926a72c58a67a7…` | YES |
| 5 | `openxwallet-grant-exercise` | `f16ad31246186cec36e142ae39bd831d…` | `f16ad31246186cec36e142ae39bd831d…` | YES |
| 6 | `openxwallet-distinct-holder-constraint` | `c2a6d2fd23fb3743fdaf0e165dabc4cb…` | `c2a6d2fd23fb3743fdaf0e165dabc4cb…` | YES |
| 7 | `openxwallet-subject-attestation` | `d29eca519462aff7871de3786f19c820…` | `d29eca519462aff7871de3786f19c820…` | YES |
| 8 | `openxwallet-agent-composition` | `aed3978e8ae952f3ff5b3de1f672bba5…` | `aed3978e8ae952f3ff5b3de1f672bba5…` | YES |

**Control: 8/8.** The manifest describes the carve commit's bytes exactly.

---

## Part one — the eight digests, in the carved tree

For each of the eight digested artifacts, `sha256sum` in **this** repository
equals the `sha256:` recorded in openxFactory at the carve commit, and equals
this repository's own manifest row. Three-way, not two-way — so a manifest that
had been "helpfully corrected" would show up.

| # | id | path | `sha256` (all three agree) |
| --- | --- | --- | --- |
| 1 | `openxwallet-record` | `contracts/openxwallet/openxwallet-record.schema.yaml` | `2012ef432616e73ddaead17c5e79aefacef712c2049ff649c15d7230b1d4eb08` |
| 2 | `openxwallet-custody-registry-schema` | `contracts/openxwallet/openxwallet-custody-registry.schema.yaml` | `df72638497a7f90c2a4dff47c429cb794bc4b6e270ce2dd2b17116478ae3b51a` |
| 3 | `openxwallet-custody-registry` | `contracts/openxwallet/openxwallet-custody.registry.yaml` | `94d631d6ee76dab015628a1856afd82582b98d6a3733622c9afe8b13b5278539` |
| 4 | `openxwallet-grant` | `contracts/openxwallet/openxwallet-grant.schema.yaml` | `fde433c5821e2e6f62926a72c58a67a784961d2e9e27e9f2b3520fcc8e738e88` |
| 5 | `openxwallet-grant-exercise` | `contracts/openxwallet/openxwallet-grant-exercise.schema.yaml` | `f16ad31246186cec36e142ae39bd831d98fbc5c0afd48685057bc39e113c8858` |
| 6 | `openxwallet-distinct-holder-constraint` | `contracts/openxwallet/openxwallet-distinct-holder-constraint.schema.yaml` | `c2a6d2fd23fb3743fdaf0e165dabc4cb1dff24e52a8262a38c86ed1482374b25` |
| 7 | `openxwallet-subject-attestation` | `contracts/openxwallet/openxwallet-subject-attestation.schema.yaml` | `d29eca519462aff7871de3786f19c820e9fc3b95115ce30e57d1f1cc2bc0c0b2` |
| 8 | `openxwallet-agent-composition` | `contracts/openxwallet-agent-profile/openxwallet-agent-composition.schema.yaml` | `aed3978e8ae952f3ff5b3de1f672bba5da350d5aaeb442feafaa870b4de4be91` |

**Part one: 8/8 PASS.** Carved bytes == openXwallet manifest == openxFactory manifest at the carve commit.

---

## Part two (a) — the tree diff over the floor is EMPTY

```sh
$ diff -r "$SRC/contracts/openxwallet" "$W/contracts/openxwallet"
(no output)
$ diff -r "$SRC/contracts/openxwallet-agent-profile" "$W/contracts/openxwallet-agent-profile"
(no output)
$ diff -r "$SRC/tests/wallet_yaml_syntax_gate" "$W/tests/wallet_yaml_syntax_gate"
(no output)
$ diff -r "$SRC/specs/006-openxwallet-contracts" "$W/specs/006-openxwallet-contracts"
(no output)
$ diff -r "$SRC/specs/010-wallet-validator-ci" "$W/specs/010-wallet-validator-ci"
(no output)
$ diff -r "$SRC/specs/012-wallet-issuer-anchor" "$W/specs/012-wallet-issuer-anchor"
(no output)
$ diff -r "$SRC/openspec/changes/archive/2026-08-08-add-openxwallet" "$W/openspec/changes/archive/2026-08-08-add-openxwallet"
(no output)
$ diff "$SRC/scripts/validate-openxwallet.py" "$W/scripts/validate-openxwallet.py"
(no output)
$ diff "$SRC/scripts/wallet-yaml-syntax-gate.py" "$W/scripts/wallet-yaml-syntax-gate.py"
(no output)
```

**Every path in the floor: EMPTY.** Recorded individually rather than as one
aggregate claim, because an aggregate "the diff was empty" hides which paths were
actually compared.

`scripts/validate-openxwallet.py` deserves its own sentence. R6 states the diff of
that file is **empty** — not "touches only `ENVELOPE_SCHEMA_PATH`". It is empty
because the vendored schema sits at the identical repository-relative path and
`:218` is `ROOT`-relative, so even that line did not move. The reader travelled
unmodified.

### The same claim, independently, by git blob hash

`diff -r` compares working trees and can be polluted by build artifacts. The
stronger check compares git's own content hashes over the tracked set, mode
included:

| Measure | Result |
| --- | --- |
| carved paths compared | 100 |
| identical git blob **and** file mode | **97** |
| differing | 3 |

The three that differ, and each is enumerated below rather than discovered:

- `.github/workflows/wallet-validation.yml`
- `openspec/specs/openxwallet-agent-profile/spec.md`
- `openspec/specs/openxwallet/spec.md`

**At the carve layer itself** (before the scaffold commit), the figure was
**100/100** — the carve is a pure copy, mathematically. The three
differences are the scaffold's, and all three are declared.

---

## Part two (b) — each promoted spec differs in exactly two CLASSES of change

The one carve-out the floor permits. The floor covers `contracts/` **bytes** and
does not reach spec prose at all, which is why a single carve-out permits both
edits.

### `openspec/specs/openxwallet/spec.md`

```diff
-TBD - created by archiving change add-openxwallet. Update Purpose after archive.
+The neutral wallet: a signing key anchored to a decentralized identifier and held by a HOLDER of any subject class the family recognises. This capability owns the holder-agnostic core — the wallet record, the closed custody registry, the attenuated grant, the exercise record, the distinct-holder constraint and the subject attestation — and the rules that make a key a wallet's REFERENCE rather than its content.
-openxFactory SHALL define a neutral wallet as a signing key anchored to a
+openXwallet SHALL define a neutral wallet as a signing key anchored to a
-openxFactory SHALL express every authority a wallet confers as a capability
+openXwallet SHALL express every authority a wallet confers as a capability
-openxFactory SHALL require that exercising a grant carries a signature from
+openXwallet SHALL require that exercising a grant carries a signature from
-openxFactory SHALL require every wallet to declare its key-custody model
+openXwallet SHALL require every wallet to declare its key-custody model
-openxFactory SHALL record, for every exercise of a grant, the key that
+openXwallet SHALL record, for every exercise of a grant, the key that
-openxFactory SHALL make revocation effective through derivation: revoking a
+openXwallet SHALL make revocation effective through derivation: revoking a
-openxFactory SHALL allow a consuming capability to require that the holder
+openXwallet SHALL allow a consuming capability to require that the holder
-openxFactory SHALL keep wallets composable and optional for domains: a
+openXwallet SHALL keep wallets composable and optional for domains: a
```

**Accounted for line by line**: 1 line at `:4` (the `## Purpose` placeholder,
written for real) + 8 requirement-subject lines (`openxFactory SHALL` →
`openXwallet SHALL`) = 9 changed lines, 18 diff lines including their removals.
**No other line in the file changed.**

### `openspec/specs/openxwallet-agent-profile/spec.md`

```diff
-TBD - created by archiving change add-openxwallet. Update Purpose after archive.
+The first profile over the neutral wallet core, covering holders of class AGENT, whose identity IS its declared composition. This capability owns what a composition must cover, what changing it revokes, and why the profile is a SIBLING family over the core rather than an extension of it — so patient and practitioner profiles arrive the same way.
-openxFactory SHALL require a wallet holder of class AGENT to declare the
+openXwallet SHALL require a wallet holder of class AGENT to declare the
-openxFactory SHALL treat any change in an agent's declared composition as
+openXwallet SHALL treat any change in an agent's declared composition as
-openxFactory SHALL express what an agent may do as the SCOPE of a
+openXwallet SHALL express what an agent may do as the SCOPE of a
```

**Accounted for line by line**: 1 line at `:4` (the `## Purpose` placeholder,
written for real) + 3 requirement-subject lines (`openxFactory SHALL` →
`openXwallet SHALL`) = 4 changed lines, 8 diff lines including their removals.
**No other line in the file changed.**

**On "diff-limited-to-two-lines".** The ratified phrasing names the two lines the
proposal cites — `:4` and `:8`. `:8` is the FIRST requirement subject; there are
eleven requirements across the two files (8 + 3), so the subject rewrite touches
eleven lines, not one. The ratified scope is **two CLASSES of change**, both
enumerated, and every changed line belongs to one of them. Stating it as "two
lines" would be describing the carve-out; stating it as 1 + 8 and 1 + 3, line by
line, is asserting it.

After the rewrite, the string `openxFactory` does not appear anywhere in either
promoted specification — checked, not assumed.

---

## The ONE post-carve edit to a carved file, declared

```diff
diff --git a/.github/workflows/wallet-validation.yml b/.github/workflows/wallet-validation.yml
index c539411..4db28de 100644
--- a/.github/workflows/wallet-validation.yml
+++ b/.github/workflows/wallet-validation.yml
@@ -1,11 +1,23 @@
 # Wallet contract validation gate for every pull request to main (feature
-# 010-wallet-validator-ci). REQUIRED since 2026-08-26: org ruleset 21538893
-# ("openxFactory wallet-gate") requires this check on the default branch;
-# see the "Wallet validation gate" section in README.md.
+# 010-wallet-validator-ci, carried from openxFactory by the wallet-v1.0 carve).
+# REQUIRED on this repository's default branch by openXwallet's own ruleset,
+# created in EVALUATE mode and promoted to ACTIVE once the check had reported
+# once -- day-one REQUIRED is impossible, because GitHub cannot require a check
+# that has never reported. See docs/openxwallet-cutover-runbook.md.
+#
+# The job id is deliberately the SAME TOKEN as openxFactory's: the token names
+# the check's FUNCTION, and distinct repositories are distinct namespaces. A
+# different name would need its own runbook language and its own rename
+# successor.
 #
 # The job carries no display name on purpose: the status check must surface
 # as exactly `wallet-validation` (FR-007), the literal token the ruleset
 # pins; a distinct job display name silently de-advises the gate.
+#
+# THIS FILE IS THE ONE CARVED FILE THE SCAFFOLD EDITED, and the edit is the
+# verify step below. It is declared in docs/byte-identity-wallet-v1.0.md so it
+# is never mistaken for drift. The byte-identity floor covers the contract
+# BYTES, the two validators and the corpus -- not this workflow.
 name: wallet-validation
 
 on:
@@ -29,6 +41,14 @@ jobs:
 
       - run: pip install pyyaml jsonschema rfc3339-validator
 
+      # FIRST, before anything reads the vendored schema. main() checks only
+      # ENVELOPE_SCHEMA_PATH.is_file() -- PRESENCE, not identity -- while rule
+      # (g) reads the approval-scope vocabulary out of that very file, so an
+      # unverified swap would silently redefine the vocabulary this gate
+      # enforces. Fails closed, and its refusal names its own remediation.
+      - name: Verify the vendored openxFactory artifact against contract_pin.yaml
+        run: python3 scripts/verify-contract-pin.py
+
       - run: python3 scripts/wallet-yaml-syntax-gate.py .
 
       - run: python3 scripts/validate-openxwallet.py .
```

**This file is not in the byte-identity floor.** The ratified floor enumerates
both contract families, the validator, the syntax gate, the gate's tests, the
three Speckit sets and the archive packet. This workflow is carved but not
floored — and the ratified tasks positively require the verify step to run
*before the validator*, which is not expressible across two independent workflows
(they race). So the step is prepended inside the `wallet-validation` job, and the
edit is declared here rather than left to be discovered as drift.

**Why the step must exist at all**, demonstrated rather than argued — from the
red run below:

```
$ python3 scripts/validate-openxwallet.py .     # on a MUTATED vendored schema
exit=0
```

The validator returns **zero** on a tampered vendored schema, because `main()`
checks only `ENVELOPE_SCHEMA_PATH.is_file()` — presence, not identity — while rule
(g) reads the approval-scope vocabulary out of that very file. Without the verify
step, an unverified swap silently redefines the vocabulary the gate enforces.

## The verifier refuses — a verifier that has never refused is not known to refuse

```
$ printf "
# deliberately mutated
" >> contracts/schemas/hermes-job-envelope.schema.yaml
$ python3 scripts/verify-contract-pin.py
REFUSED contracts/schemas/hermes-job-envelope.schema.yaml: DIGEST DRIFT
          recorded   8ce2c89903a2f5a68ce3d73a7b8eb4f47cdef913da038b9a68e22735ee96cb7c
          recomputed d1a0a462c333ecfe6ba06632a1f400c638b2ccfe5372c62648df76aef0ba6a29
        the vendored copy is not the openxFactory artifact pinned at 30565e48ffe3d8a9773e10af33425701845e10f6
  remediation: git submodule update --init openXwallet
  remediation: see docs/pin-resync-runbook.md
exit=1
```

Both remediation strings are present: the refusal carries its own exit, rather
than leaving it in tribal memory.

## The carve, and its completeness

| Measure | Expected | Measured |
| --- | --- | --- |
| tracked files over the twelve path sets | 100 | **100** |
| diff of the two sorted listings | empty | **empty** |
| commits of real path history | > 1 | **26** |
| commits touching `scripts/validate-openxwallet.py` | > 1 | **17** |
| files under `specs/006-openxwallet-contracts/` (its `evidence/` included) | 7 | **7** |
| files under `contracts/openxwallet/examples/negative/` | 32 | **32** |
| files under `contracts/openxwallet-agent-profile/examples/negative/` | 4 | **4** |
| both negative trees together — the ratified "36" | 36 | **36** |
| `contracts/openxwallet/examples/` at that exact relative path | yes | **yes** |
| `contracts/openxwallet-agent-profile/examples/` at that exact relative path | yes | **yes** |

**A correction to the ratified shorthand, recorded rather than absorbed.** The
ratified task asserts "36 under `contracts/openxwallet/examples/negative/`". That
directory holds **32**; the remaining **4** are in the agent-profile family. 32 +
4 = 36. Asserting 36 in the core family alone would FAIL against a correct carve
and send an operator hunting four files that never existed there — which is
exactly the failure mode the explicit-count rule exists to prevent, applied to its
own text. The property the number stands for — no negative was lost — holds
exactly, and the validator independently confirms it: *"corpus: 17 positive
example(s), 36 negative confirmation(s) across 13/13 requirements"*.

**Examples-prefix preservation is an acceptance line, not a hope.** The
validator's corpus exclusion keys on `"examples" in path.parts` AND a part in
`("openxwallet", "openxwallet-agent-profile")`. A carve that flattened or renamed
either prefix would re-adjudicate all 36 intended-invalid negatives as LIVE
records — inside a check that becomes REQUIRED.

## The offline gates, at this commit

| Gate | Exit |
| --- | --- |
| `python3 scripts/verify-contract-pin.py` | **0** |
| `python3 scripts/wallet-yaml-syntax-gate.py .` | **0** |
| `python3 scripts/validate-openxwallet.py .` | **0** (0 errors, 0 warnings) |
| `python3 scripts/validate-openxwallet.py . --strict` | **0** |
| `python3 -m pytest tests/ -q` | **0** (4 passed) |
| `OPENSPEC_TELEMETRY=0 openspec validate --all --strict` | **0** (2 passed, 0 failed) |

The validator's own notes at this tree:

```
note  approval-scope vocabulary read from contracts/schemas/hermes-job-envelope.schema.yaml:
      ['authority_agents_may_approve', 'hermes_approval_required_before_apply',
       'human_escalation_required_for']
note  corpus: 17 positive example(s), 36 negative confirmation(s) across 13/13 requirements
note  no intake register at this tree; nothing to read
```

The third note is expected and is **correct**: R6 keeps
`governance/review-authority/` in openxFactory and moves only its READER. The
register is openxFactory's own review authority, and openxFactory's consumer gate
runs this pinned reader over openxFactory's tree by passing `.` — where the
register does resolve.

## Verdict

| Claim | Verdict |
| --- | --- |
| Completeness — nothing was lost | **PASS** (100/100, empty listing diff) |
| Part one — the eight digests | **PASS** (8/8, three-way) |
| Part two (a) — the floor diff | **PASS** (empty on every path; 97/100 blob-identical, 100/100 at the carve layer) |
| Part two (b) — the two prose classes | **PASS** (1 + 8 and 1 + 3, line by line) |
| The one declared workflow edit | **DECLARED** (not in the floor; required by the ratified task) |
| The verifier fails closed | **PASS** (observed refusing, with remediation) |
| All offline gates | **PASS** (6/6) |

`wallet-v1.0` may be tagged.
