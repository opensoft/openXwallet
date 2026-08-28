# Feature 015 — multi-key wallets

Governing change: `openspec/changes/add-multi-key-wallets/` (capability
`openxwallet`), RATIFIED 2026-08-28 by Brett Heap, operator authority, by the
in-session ruling **"rule option 1 and build it"**. Released as `wallet-v1.3`.

## The problem, in one sentence

hermes-install writes the register-recorded per-seat `key_id` into an exercise
record's `presenting_key_ref`, and `wal-agent-mrc-0001` declared exactly one
key — so rule (r) would refuse the first such record to reach a scanned tree,
because a presenting key no wallet declares is refused rather than passed over.

## Acceptance

- **A1.** A wallet record MAY declare a SET of keys: `key_reference` plus an
  optional `keys:` list of additional entries. A record omitting `keys:`
  declares a set of one and validates unchanged.
- **A2.** Each `keys:` entry declares its own `custody` (from the closed
  registry), its own `key_fingerprint`, its own `did`, and optionally its own
  `state`.
- **A3.** Rule (r) resolves a presenting key against the declared SET. A key in
  no wallet's set is refused; a key in more than one wallet's set is refused as
  ambiguous.
- **A4.** `custody_model_in_force` is compared against the custody of the key
  that SIGNED, where signing means a VERIFIED proof named it. Unverified
  exercises compare against the wallet's own declaration, as before.
- **A5.** A grant's tier may not exceed the presenting key's custody ceiling,
  on a PERMITTED exercise.
- **A6.** No declared key's custody ceiling may outrank the wallet's own.
- **A7.** A wallet declares each key identifier once.
- **A8.** Where a `keys:` entry declares `public_key_multibase`, its
  `key_fingerprint` recomputes from it.
- **A9.** A declared key is retired by STATE, never by deletion; an exercise
  permitted under a retired key is refused, and the wallet's other keys and its
  own standing are unaffected.
- **A10.** Four new contract-level ERROR codes, zero new warnings, no rename, no
  repurpose. One harness-only code over the packaged corpus.
- **A11.** Exactly one digested contract byte moves, and the other seven are
  proven unchanged by recomputation.

## Out of scope

Subwallets; per-key grants; delegation chains; shared holders; a cross-surface
fingerprint-agreement check between the review-authority register's `seat_keys[]`
and a wallet's declaration (capability `review-authority-register-reader`);
per-key custody in hermes-install's projection; an independent `custody` block on
`key_reference`. Each is a named successor in the governing change's
`design.md` D6 and `tasks.md` §7.

## Assumptions

- The four CI-resident seat root keys and the per-convening ephemerals both fall
  under `holder_readable`: their private halves are readable by the holder's own
  execution context (a GitHub Actions job's process environment), and the
  authorization an ephemeral's use requires is produced by that same context, so
  it is not an authorization OUTSIDE it. The closed three-member set fits both
  without stretching, and the still-open Q10 `isolated_per_use_authorized`
  authorizer question is NOT implicated — no key this release declares carries a
  ceiling above `act`.
- hermes-install needs NO change: it already emits the register-recorded `key_id`
  as `presenting_key_ref` and the projected `custody_model` (`holder_readable`)
  as `custody_model_in_force`, and once the wallet declares those keys both
  resolve.
