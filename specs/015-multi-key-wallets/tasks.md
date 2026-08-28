# Tasks — 015-multi-key-wallets

Mirrors `openspec/changes/add-multi-key-wallets/tasks.md`. Ticked as built.

## 1. Schema — additive, one digested file
- [x] 1.1 optional `keys:` array, closed item, `minItems: 1`
- [x] 1.2 item requires `did`, `key_id`, `key_fingerprint`, `custody`; admits
      `public_key_multibase`, `signature_algorithm`, `state`, `display_label`
- [x] 1.3 optional `key_fingerprint` on `key_reference`, asymmetry stated in the
      schema
- [x] 1.4 declared SET, append-only retirement and the one-field-two-jobs
      coupling all described IN the schema
- [x] 1.5 `contract_schema_version: 1 → 2`; top-level `schema_version` unmoved

## 2. Validator
- [x] 2.1 `declared_keys()` is the single membership function
- [x] 2.2 `Context.index` indexes every declared key
- [x] 2.3 per-key closed-set check under the existing `custody-model-unknown`;
      the wallet-level check keeps its exact prior form and runs independently
      of whether `key_reference.key_id` parses
- [x] 2.4 `declared-key-duplicate`
- [x] 2.5 `declared-key-raises-authority` (rank-keyed)
- [x] 2.6 `declared-key-fingerprint-mismatch` (base58btc + multicodec + sha256)
- [x] 2.7 multi-key NOTE, emitted only for a set of more than one
- [x] 2.8 `custody-model-mismatch` basis = presenting key, gated on
      `verified is True`
- [x] 2.9 `presenting-key-evidence-cap`, guarded on `permitted`
- [x] 2.10 retired key refused at use under `revoked-chain-exercised`
- [x] 2.11 `presenting-key-unresolved` message corrected to "DECLARED KEY SET"
- [x] 2.12 module docstring rules (r) and (s) updated; no letter reassigned
- [x] 2.13 four new contract codes, one harness code, zero warnings, no rename

## 3. Corpus
- [x] 3.1 multi-key positive with mixed custody, one entry carrying its public
      half
- [x] 3.2 positive exercise presented by a non-primary key
- [x] 3.3–3.11 nine negatives, one per invariant plus the single-key
      `custody-model-mismatch` regression proof
- [x] 3.12 id disjointness asserted in the validator AND the suite
- [x] 3.13 named-probe assertions for all nine
- [x] 3.14 headers, detail pins, requirement attributions; closure green
- [x] 3.15 `tests/multi_key_wallets/` — 21 tests

## 4. Release bookkeeping
- [x] 4.1 manifest: bundle `wallet-v1.3`, record row digest + `schema_version`,
      other seven proven unchanged by recomputation
- [x] 4.2 `contracts/CHANGELOG.md` `wallet-v1.3` entry
- [x] 4.3 `contracts/openxwallet/README.md`
- [x] 4.4 gate bar green: pin verify, syntax gate, validator plain and
      `--strict`, `pytest tests/ -q` (90 passed), `openspec validate --all
      --strict`
- [x] 4.5 `AGENTS.md` Speckit block → feature 015
- [x] 4.6 annotated tag `wallet-v1.3` at `6b248d4`, the merge sha, after
      re-proving the bar at that head. `wallet-v1.3.digests.yaml` over
      `member_class: owned` members REMAINS THE OPERATOR ACT it has been since
      `wallet-v1.0` — not produced here, and listed as remaining work rather
      than silently omitted.

## 5. Consumer completion — openxFactory (PR #480)
- [x] 5.1 `wal-agent-mrc-0001` declares the four seat keys; the root key's
      declaration byte-untouched; custody `holder_readable` per the D7
      determination
- [x] 5.2 pin + gitlink → `wallet-v1.3` (`6b248d4`); ONE digest row moved, the
      other seven reverified by recomputation
- [x] 5.3 gate proves all three: the 4-of-4 register note, the
      five-declared-key note, and fingerprint agreement by computation (the
      register's base64url half and the wallet's base58btc half decode to the
      same 32 bytes for all four seats)

## 6. Ledger ticks
- [x] 6.1 `add-per-seat-register-entries/tasks.md` §7.3
- [x] 6.2 `add-per-seat-register-entries/design.md` named successor 3
- [x] 6.3 `specs/014-per-seat-register-entries/spec.md` out-of-scope line
- [x] 6.4 `openspec/specs/openxwallet/spec.md` `## Purpose` — no delta form
      reaches Purpose, so it is corrected here, ratified by the same change
