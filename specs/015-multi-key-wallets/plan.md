# Plan — 015-multi-key-wallets

## Shape of the change

One additive schema edit, one validator extension, corpus additions, release
bookkeeping. No new capability, no new kind, no renamed machine key.

## D1 — `keys:` is additional, never a replacement

The declared set is `key_reference ∪ keys[*]`, computed by ONE function
(`declared_keys`) returning `(key_id, entry, custody, declaration_site)` with the
primary first. Every rule that needs the set calls it, so membership is not
recomputed in three places. Making `keys:` the whole set was rejected: it would
either break every existing record or leave two spellings of one fact with a
precedence rule between them.

## D2 — The custody basis at exercise

    basis(wallet, key) = the `keys:` entry's custody   if the key is a `keys:` member
                         the wallet's top-level block  if the key is the primary
                         the wallet's top-level block  if no key was ESTABLISHED

ESTABLISHED means `verified is True`. The existing code falls back to the
record's own attribution key when a signature did not verify, and keying custody
on self-declared data is the laundering surface rule (r) exists to close.

`key_reference` carries no custody block of its own, so the primary key's
per-key custody IS the wallet's top-level declaration — one field doing two
jobs, stated in the schema rather than left to be discovered.

## D3 — Codes

New: `declared-key-duplicate`, `declared-key-raises-authority`,
`declared-key-fingerprint-mismatch`, `presenting-key-evidence-cap`. Harness-only:
`examples-invalid`. Reused at a new subject: `custody-model-unknown` (a `keys:`
entry's model outside the closed set — that code already serves two subjects
in-tree) and `revoked-chain-exercised` (an exercise under a retired key —
revocation checked at use is one rule).

Zero new warnings: `report()` reds a `--strict` run on warnings and
LedgerxFactory runs `--strict`.

## D4 — Fingerprints are proven where a public half exists

base58btc decode implemented in the validator (20 lines of integer arithmetic;
every gate here is offline and a wheel is a larger liability), ed25519 multicodec
prefix required, `sha256(raw)` compared. The test suite implements the ENCODER
independently, so a test cannot pass by borrowing a broken decoder.

## D5 — The regression proof, and the test whose direction flipped

`custody-model-mismatch` shipped UNPROBED by the corpus, so moving its basis
could have deleted it silently for the whole estate. A single-key negative is
added as the no-op proof.

`test_the_previous_version_adjudicates_the_corpus_identically` becomes
`test_this_version_adjudicates_the_previous_corpus_identically`: the previous
reader cannot adjudicate a tree whose rules it lacks, so the comparison runs the
CURRENT reader over the recovered PREVIOUS corpus. Harness codes are excluded
because corpus-completeness claims necessarily change when a release adds
fixtures; record-level verdicts are what must not move.

## Order

1. schema (additive) → 2. validator → 3. corpus + named probes + suite →
4. manifest, CHANGELOG, family README, AGENTS.md → 5. gate bar → 6. merge, tag
at the merge sha → 7. openxFactory pin + the four declared seat keys.
