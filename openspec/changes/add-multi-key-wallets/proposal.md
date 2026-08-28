---
code_surface: openXwallet `contracts/openxwallet/openxwallet-record.schema.yaml` (ADDITIVE — one optional `keys:` list, one optional `key_fingerprint` on the existing `key_reference`), `scripts/validate-openxwallet.py` (rule (r) declared-set extension, rule (s) per key, three new record-level codes, one new exercise-level code, no rename), the packaged corpus, `contracts/openxwallet/README.md`, `AGENTS.md`, and the bookkeeping of a release. Per `release-realization`, this change archives only on merged, green realization evidence for that surface.
target_release: unallocated at proposal. The realization is expected to be an ADDITIVE MINOR (`wallet-v1.3`) whose `openxwallet-record` digest MOVES — the first wallet release that changes a digested contract byte since the carve — so every consumer's pin moves with it. Per AGENTS.md rule 6 the five coordinated values are allocated at realization and nothing is reserved here.
Status: ratified
Ratified: 2026-08-28 by Brett Heap (operator authority) — in-session ruling
  ("rule option 1 and build it"), option 1 as explained and recommended
  in-session: one wallet MAY declare several keys as presenters of its single
  authority. See `design.md` "Ratification record"; the one-reviewer alignment
  pass and the disposition of all fourteen verdicts are recorded there.
---

# Proposal: add-multi-key-wallets

## Why

Four council seat signing keys are recorded in a register that a wallet does not
declare, and the moment an exercise record naming one of them reaches a tree
this validator scans, that record is refused.

The chain is already built and its last link is missing. On 2026-08-28 the
operator minted four Ed25519 keypairs, one per seat of codexFactory's
`merge_readiness_council`, and provisioned their private halves as GitHub
Actions secrets in that repository's `worker-credentials` environment
(codexFactory `hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`,
merged at `78b8fa2`). `add-per-seat-register-entries` then taught the register
reader to hold and enforce their public halves, and openxFactory's register
carries all four at `wallet-v1.2` (PR #475, `0c0075d`).

That change named this one, with a date on it — its own tasks §7.3:

> **A wallet record declaring several keys** (`design.md` D9), which would make
> a per-seat key wallet-declared rather than register-declared. A contract
> change to a digested artifact: a bundle version and every consumer's pin.
> TRIGGER, and it has a date on it: hermes-install copies the projection's
> `key_id` verbatim into the exercise record's `presenting_key_ref`, so this
> MUST be answered before any exercise record carrying a per-seat key is
> committed to a tree this validator scans — rule (r) refuses a presenting key
> no wallet declares.

The trigger is not hypothetical. hermes-install's exercise writer sets
`presenting_key_ref = <projection.key_id>` — the REGISTER-RECORDED key, chosen
deliberately over the per-convening ephemeral one, because "the contract
requires this ref to resolve to a wallet key present in the corpus, and an
ephemeral key never is"
(`src/hermes_install/domain/review_authority.py`, mint-the-exercise docstring).
So the ref hermes writes is `key-seat-lead-quality-0001` and its four siblings —
and today `wal-agent-mrc-0001` declares exactly one key, `key-mrc-0001`. Rule
(r) resolves a presenting key through the corpus's wallet records and refuses a
key no wallet declares:

> a presenting key no wallet declares is refused rather than passed over

The register knowing a key is not the wallet declaring it. The register is a
factory-layer intake surface for review authority over governed objects; the
wallet record is where the family says which keys may present a wallet's
authority and what each one's signature evidences. A key recorded only in the
register is authority the standard does not model.

## What the operator ruled

Four shapes were put to the operator in session on 2026-08-28. The ruling was
**"rule option 1 and build it"** — option 1 being:

**One wallet MAY declare several keys as presenters of its single authority.**

- Each declared key carries its OWN custody declaration and its OWN fingerprint.
- Grants stay WALLET-LEVEL. Keys never multiply authority: declaring a key
  cannot raise what the wallet may hold, and no declared key's custody may
  outrank the wallet's own.
- Audit stays KEY-ATTRIBUTED, unchanged: the presenting key is what an act is
  attributed to.
- The validator's rule (r) extends from "the presenting key IS the audience
  wallet's key_reference" to "the presenting key is IN the audience wallet's
  DECLARED KEY SET".
- Per-key custody CAPS what that key's signature evidences: the custody an
  exercise records in force is the custody of the key that signed, not the
  wallet's primary key's.

Explicitly NOT ruled in, and named here so nobody reads them into the delta:
**subwallets**, **per-key grants**, **delegation chains** (a key authorizing
another key), and **shared holders** (one key declared by two wallets). Those
are the deferred successors; see `design.md` D6.

## What Changes

Four `## MODIFIED Requirements` on the existing capability `openxwallet`. No
new capability, no new contract family, no new kind, no renamed machine key.

1. **"A wallet is a key, never a record of a key"** is RE-GROUNDED on the key
   SET. The requirement's sentence survives intact and is made precise: the
   wallet is identified by the set of keys it declares, and it is still never a
   record of someone else's key — every key in the set is a key the holder
   holds. The record references each key and carries each key's custody; it
   still has no property at any depth that could hold key material.

2. **"Custody is declared and bounds what a signature evidences"** becomes
   PER KEY. Every declared key declares its custody from the same closed
   registry; a signature evidences only what the custody of the key that SIGNED
   permits; and no declared key's custody ceiling may outrank the wallet's own,
   which is the "keys never multiply authority" limb of the ruling made
   mechanical rather than promised.

3. **"Every exercise is key-attributed"** extends the audience binding to the
   declared SET, and requires a wallet to declare each key identifier once.

4. **"Revocation propagates through the chain"** gains the case multi-key makes
   ordinary: retiring ONE declared key stops that key presenting the wallet's
   authority without revoking the wallet or what its other keys present, and the
   retirement is checked at exercise like every other revocation. A declaration
   is APPEND-ONLY — a key is retired by state, never by deletion — because
   deleting it would retroactively invalidate every committed act already
   attributed to it. Four CI-resident seat keys will rotate, so this is the
   operation, not an edge case (`design.md` D9).

## Backward compatibility

**Every existing single-key wallet record remains valid, unchanged, and the set
has one member.** The schema change is ADDITIVE in both directions:

- `keys:` is a new OPTIONAL top-level list of ADDITIONAL declared keys. A record
  that omits it declares exactly one key — its `key_reference` — and the whole
  of rule (r), rule (s) and the custody basis resolve to today's behaviour by
  construction, not by a compatibility branch.
- `key_fingerprint` is admitted as an OPTIONAL field on the existing
  `key_reference`, because requiring it there would break every record in the
  estate. It is REQUIRED on every entry of `keys:`. The asymmetry is honest and
  stated in the schema: the primary key's declaration predates the field.
- No finding code is renamed, repurposed, or reclassified, and no new WARNING is
  introduced — LedgerxFactory runs this validator with `--strict`, where a
  warning is an exit code. FOUR new codes are added
  (`declared-key-duplicate`, `declared-key-raises-authority`,
  `declared-key-fingerprint-mismatch`, `presenting-key-evidence-cap`); the
  existing `custody-model-unknown` covers the per-key closed-set case, being the
  same rule at a new depth — that code already serves two different subjects
  in-tree — and `revoked-chain-exercised` covers a retired key, revocation
  checked at use being one rule. `custody-model-mismatch` keeps its code while
  its comparison BASIS becomes the presenting key, which for every single-key
  record resolves to the same block it compares against today
  (`design.md` D3).

**A digested contract byte moves.** `openxwallet-record.schema.yaml` changes, so
its `sha256:` in `contracts/manifest.yaml` and in every consumer's pin `files:`
block moves with it. This is the first wallet release since the carve for which
that is true, and it is why the realization is a MINOR with a recorded digest
rather than a validator-only release like `wallet-v1.2`.

## Impact

- **openXwallet**: one additive schema change, a validator extension, corpus
  additions, `wallet-v1.3`.
- **openxFactory**: `governance/review-authority/wallets/wal-agent-mrc-0001.yaml`
  gains the four seat keys as declared keys, with `holder_readable` custody
  each; the root key's declaration is byte-untouched. Pin + gitlink move to
  `wallet-v1.3` with the refreshed `openxwallet-record` digest.
- **hermes-install**: NO CHANGE. Its writer already emits the register-recorded
  `key_id` as `presenting_key_ref` and the projected `custody_model` as
  `custody_model_in_force`; once the wallet declares those keys, both resolve.
  The conditional successor is named in `design.md` D6.
- **LedgerxFactory, MedxFactory, other pinning consumers**: a pin bump when they
  next re-sync. Nothing they declare becomes invalid.
