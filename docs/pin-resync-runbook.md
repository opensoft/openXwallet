# Contract-pin re-sync runbook

Status: standard

The checklist for re-synchronizing [`../contract_pin.yaml`](../contract_pin.yaml)
against a **then-current** openxFactory release, when the one artifact openXwallet
vendors changes upstream.

**Run it whenever `contracts/schemas/hermes-job-envelope.schema.yaml` changes in
openxFactory.** Validator rule (g) reads the legal approval-scope vocabulary out
of that file, so an upstream edit to it changes what this repository's REQUIRED
check enforces.

## Why this exists from day one

Because the cost is spread across three repositories and nobody discovers that
mid-incident. An `openxwallet` core delta costs **a wallet release** here, **an
openxFactory pin bump** there, and **a LedgerxFactory re-pin** downstream. A
runbook written after the first such delta is a post-mortem.

## The offline law

`scripts/verify-contract-pin.py` reads `contract_pin.yaml` and the files it names.
It reads **no** network, **no** upstream tree, and **not**
`contracts/manifest.yaml`. The live manifest cross-check is a **SYNC-TIME**
obligation — step 3 below — never a CI read. A gate that reaches upstream is a
gate that fails when upstream is unreachable, which is the opposite of fail-closed.

## Preconditions

- A local openxFactory checkout at the release commit you intend to pin. Its exact
  40-hex commit goes into the pin; **never** a branch, never a movable tag, never
  hand-typed from memory.
- The upstream change has actually **landed** in that checkout — a pin to a commit
  on somebody's branch is a pin to a commit that may be rebased away.
- You know which openxFactory `contract_bundle_version` that commit publishes; it
  becomes `pinned_bundle:` here and `pinned_openxfactory_bundle:` on the manifest's
  consumed row.
- You are on a branch, and you stage explicit paths — never `git add -A`.

## Checklist

### 1. Re-vendor the artifact byte-identically

```sh
cp <openxFactory>/contracts/schemas/hermes-job-envelope.schema.yaml \
   contracts/schemas/hermes-job-envelope.schema.yaml
```

**The path is load-bearing.** It must stay exactly
`contracts/schemas/hermes-job-envelope.schema.yaml`, because
`ENVELOPE_SCHEMA_PATH` in `scripts/validate-openxwallet.py` is ROOT-relative and
the validator's bytes are inside the `wallet-v1.0` byte-identity floor. Moving the
vendored file would force a source edit to the validator — which is the one thing
the floor forbids.

A byte copy, not a transcription. No reformatting, no comment insertion, no YAML
round-trip.

### 2. Re-bake the pin

Update in [`../contract_pin.yaml`](../contract_pin.yaml):

- `commit:` — the exact 40-hex openxFactory commit;
- `pinned_bundle:` — the `contract_bundle_version` that commit publishes;
- the `files[].sha256` — recomputed over the newly vendored bytes.

```sh
sha256sum contracts/schemas/hermes-job-envelope.schema.yaml
```

### 3. Cross-check against the published manifest — the sync-time obligation

Read openxFactory's `contracts/manifest.yaml` at the pinned commit **once, here,
by hand or by script — never from CI.**

Note the standing asymmetry: **openxFactory's row for this artifact carries no
per-file `sha256`.** It is `compatibility: copied_from_source_commit` with
`adapter_owner: Omnigent-Install`, content-addressed by commit from
`opensoft/Omnigent-Install`. So the cross-check is:

- the row still exists at that path, and
- its `source_path` and `compatibility` still say what they said — i.e. the
  artifact is still the canonical envelope schema, not something else that moved
  into the path.

The DIGEST authority is the recomputed one from step 2. If openxFactory ever
starts recording a digest for this row, cross-check against it too.

### 4. Re-verify the pin offline

```sh
python3 scripts/verify-contract-pin.py
```

Expected: `OK`, exit 0. It rejects a commit-less or non-40-hex pin (rule 1) and
recomputes every vendored digest, failing on drift **before any test runs**
(rule 2). Every refusal names its own remediation.

### 5. Re-run the offline gate suite

```sh
python3 scripts/wallet-yaml-syntax-gate.py .
python3 scripts/validate-openxwallet.py .
python3 scripts/validate-openxwallet.py . --strict
python3 -m pytest tests/ -q
OPENSPEC_TELEMETRY=0 openspec validate --all --strict
```

**All must exit 0.** Rule (g) reads the vocabulary out of the newly vendored file,
so a vocabulary that narrowed upstream will surface here as a validator failure —
which is the point. Do not widen the corpus to make it pass; adjudicate the
upstream change.

### 6. Update the manifest's consumed row

In `contracts/manifest.yaml`, the consumed row's `sha256` and
`pinned_openxfactory_bundle:` must match the pin exactly. **The verifier and the
manifest must never disagree** — if they do, one of them is describing a file that
is not on disk.

### 7. Decide whether this is a wallet release

If the re-vendored artifact changed what the validator ENFORCES, it changed this
repository's contract behaviour, and that is a `contracts/CHANGELOG.md` entry plus
a bundle version — additive if nothing valid became invalid, breaking otherwise.
If the vendored bytes changed but the enforced vocabulary did not, record it in the
changelog's entry for the next release rather than cutting one.

### 8. Notify the pinning side

openxFactory pins this repository by commit and per-file digest. A new wallet
release means an openxFactory pin bump, and — for any domain descendant — a
re-pin downstream. Those are their own changes in their own repositories; name
them when you land this one.

## Rollback

Revert the pin commit. The previous `commit:` + `sha256` pair and the previous
vendored bytes are restored together, and `scripts/verify-contract-pin.py` passes
again — because the pin and the bytes always move as one commit. **Never revert
one without the other**: a reverted digest with un-reverted bytes fails closed,
which is safe but is a self-inflicted red.
