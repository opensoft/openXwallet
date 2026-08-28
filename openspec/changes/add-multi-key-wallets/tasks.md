# Tasks: add-multi-key-wallets

Speckit builds these; OpenSpec ratified them. The realization feature is
`specs/015-multi-key-wallets/`.

## 1. The schema — ADDITIVE, one digested file

- [ ] 1.1 `contracts/openxwallet/openxwallet-record.schema.yaml`: add OPTIONAL
      top-level `keys:` — an array of ADDITIONAL declared keys beside
      `key_reference` (design D1), `additionalProperties: false` on the array's
      item as everywhere else, `minItems: 1` so an empty list cannot stand in for
      an absent one.
- [ ] 1.2 Each `keys[]` item: REQUIRED `did`, `key_id`, `key_fingerprint`,
      `custody`; OPTIONAL `public_key_multibase`, `signature_algorithm`,
      `state`, `display_label`. `custody` is the SAME shape as the wallet's
      top-level block (design D2). `key_fingerprint` pattern
      `^sha256:[0-9a-f]{64}$` (design D5). `state` is the SAME closed set as the
      wallet's own — `active | suspended | revoked` — and defaults to `active`
      when absent (design D9). `did` is REQUIRED, matching `key_reference`.
- [ ] 1.3 Admit OPTIONAL `key_fingerprint` on the existing `key_reference`, same
      pattern. State the asymmetry with `keys[]` and its reason IN the schema
      description (alignment defect 1, concern 2).
- [ ] 1.4 Describe IN THE SCHEMA: the declared key SET is `key_reference` plus
      `keys`; a record omitting `keys` declares one key; no key-material property
      exists at the new depth either; a declaration is APPEND-ONLY and retirement
      is a state change (D9); and the wallet's top-level `custody` block is BOTH
      the wallet's issuance ceiling AND the primary key's per-key custody (D10) —
      the one field doing two jobs, said out loud where a reader meets it.
- [ ] 1.5 Version fields, named exactly (design D8, alignment concern 10): the
      file's `contract_schema_version: 1 → 2`; the file's own top-level
      `schema_version: 1` does NOT move. Confirm no other digested contract byte
      moves. There is no `docs/contract-versioning-policy.md` in this
      repository, so the applied rule is AGENTS.md rule 6 plus D8's reading,
      recorded in the CHANGELOG.

## 2. The validator — `scripts/validate-openxwallet.py`

- [ ] 2.1 ONE function computes the declared key set —
      `declared_keys(doc) -> [(key_id, custody, declaration_site)]`, primary
      first — and every rule that needs the set calls it (design D1). Duplicates
      are not collapsed there; 2.3 needs to see them.
- [ ] 2.2 `Context.index`: index EVERY declared key into `wallets_by_key`, so
      rule (r) resolves against the declared SET (design D4). Type-guarded like
      the existing index, which runs BEFORE schema validation.
- [ ] 2.3 `check_wallet_record`: run the closed-set check per declared key under
      the EXISTING `custody-model-unknown` code, with the failing key and its
      declaration site named (design D2). The WALLET-LEVEL check keeps its exact
      current form and runs independently of whether `key_reference.key_id`
      parses — a malformed primary reference must not leave the wallet's own
      custody declaration unadjudicated.
- [ ] 2.4 `check_wallet_record`: NEW `declared-key-duplicate` — a wallet
      declaring one `key_id` more than once, including a `keys[]` entry repeating
      `key_reference.key_id` (design D1/D4).
- [ ] 2.5 `check_wallet_record`: NEW `declared-key-raises-authority` — a declared
      key whose custody ceiling RANKS ABOVE the wallet's own (design D2). Keyed
      on rank, not tier name.
- [ ] 2.6 `check_wallet_record`: NEW `declared-key-fingerprint-mismatch` — where
      a `keys[]` entry declares `public_key_multibase`, the `key_fingerprint`
      must RECOMPUTE from it: base58btc-decode, require the two-byte ed25519
      multicodec prefix and 32 raw bytes, and compare
      `"sha256:" + sha256(raw).hexdigest()` (design D5). Conditional on the
      optional field's presence; malformed multibase reports under the same
      code.
- [ ] 2.7 `check_wallet_record`: a NOTE (never a warning — `report()` reds a
      `--strict` run on warnings and LedgerxFactory runs `--strict`) naming how
      many keys a MULTI-KEY wallet declared and which, so a consumer gate can
      assert POSITIVELY that the keys it expects were adjudicated. Emitted only
      when the set has more than one member, so the packaged corpus stays quiet.
- [ ] 2.8 Rule (r): `custody-model-mismatch` compares `custody_model_in_force`
      against the basis function in design D3 — the `keys[]` entry's custody when
      the presenting key is a `keys[]` member, the wallet's top-level custody
      when it is the primary key OR when no presenting key is ESTABLISHED.
      ESTABLISHED means `verified is True` (alignment concern 8); an unverified
      exercise takes the wallet's declaration exactly as today. Code unchanged;
      message names the basis.
- [ ] 2.9 Rule (r): NEW `presenting-key-evidence-cap` — the grant's authority
      tier exceeds the ceiling of the presenting key's custody (design D3).
      GUARDED on `outcome == "permitted"` and on `verified is True`, like every
      other use-time cap; the exercise contract already closes a
      `custody_ceiling_exceeded` refusal code, and a record truthfully
      documenting that refusal must not itself be a finding (alignment defect 5).
- [ ] 2.10 Rule (r): an exercise PERMITTED under a declared key whose `state` is
      `suspended` or `revoked` is refused under the EXISTING
      `revoked-chain-exercised` code (design D9). No new code: revocation
      checked at use is one rule.
- [ ] 2.11 Correct `presenting-key-unresolved`'s message, which says the key "is
      no known wallet's `key_reference`" and after 2.2 is false (alignment
      concern 9a). The code and its pinned detail substring are NOT touched.
- [ ] 2.12 Update the module docstring's rules (r) and (s) to say what they now
      check. No rule letter is reassigned.
- [ ] 2.13 No finding code renamed, repurposed or reclassified; no new WARNING.
      Assert by diffing the code inventory before and after: exactly four new
      ERROR codes and zero new warnings.

## 3. The corpus — positives, one negative per new invariant, named probes

- [ ] 3.1 POSITIVE: a multi-key wallet with MIXED custody — a stronger wallet
      declaring a WEAKER additional key — proving a key may be weaker than its
      wallet. Carries `public_key_multibase` on at least one entry so 2.6 is
      exercised on the happy path.
- [ ] 3.2 POSITIVE: an exercise presented by a NON-PRIMARY declared key, with
      `custody_model_in_force` equal to THAT key's custody and a grant tier
      within that key's ceiling.
- [ ] 3.3 NEGATIVE: presenting key not in the declared set →
      `presenting-key-unresolved`. The fixture names a key that LOOKS like a
      member of the multi-key wallet's set and is not, so it tests the SET
      boundary rather than a random unknown key.
- [ ] 3.4 NEGATIVE: duplicate declared key ids → `declared-key-duplicate`.
- [ ] 3.5 NEGATIVE: a `keys[]` entry with no `custody` → `schema`, with a detail
      pin so it keeps testing the invariant it is named for.
- [ ] 3.6 NEGATIVE: a declared key whose ceiling outranks its wallet's →
      `declared-key-raises-authority`.
- [ ] 3.7 NEGATIVE: an exercise whose grant tier exceeds the presenting key's
      ceiling, recorded as PERMITTED → `presenting-key-evidence-cap`.
- [ ] 3.8 NEGATIVE: `custody_model_in_force` naming ANOTHER of the same wallet's
      keys' custody → `custody-model-mismatch`.
- [ ] 3.9 NEGATIVE: a `key_fingerprint` that does not recompute from the entry's
      own `public_key_multibase` → `declared-key-fingerprint-mismatch`.
- [ ] 3.10 NEGATIVE: an exercise permitted under a declared key whose `state` is
      `revoked` → `revoked-chain-exercised`.
- [ ] 3.11 NEGATIVE: a SINGLE-KEY wallet whose exercise records a custody model
      the wallet does not declare → `custody-model-mismatch`. This is the
      no-op regression proof for the basis change (alignment defect 1): that
      code is currently unprobed by the shipped corpus, so nothing would have
      caught its silent deletion.
- [ ] 3.12 Every new `wallet_id`, `grant_id` and declared `key_id` is DISJOINT
      from the packaged corpus, and the disjointness is ASSERTED in the pytest
      suite rather than assumed (alignment defect 4). A reused `key_id` makes
      `wallets_by_key` two-owner and flips every shipped exercise positive to
      ambiguous.
- [ ] 3.13 NAMED-PROBE assertions for the new fixtures, following
      `add-per-seat-register-entries`' precedent: the new invariants attribute to
      EXISTING requirement ids, so the two-directional requirement closure
      cannot notice a deleted fixture (alignment concern 9b).
- [ ] 3.14 Every new negative carries `# expected_failure:`, an
      `# expected_failure_detail:` pin where the generic `schema` finding would
      otherwise swallow it, and a `# requirement:` attribution. Requirement
      closure stays two-directional and green.
- [ ] 3.15 pytest coverage for each new code, for the basis change, for the
      `verified is True` gate and for the retirement refusal, under
      `tests/multi_key_wallets/`.

## 4. Release bookkeeping — `wallet-v1.3`

- [ ] 4.1 `contracts/manifest.yaml`: `contract_bundle_version: wallet-v1.3`; the
      `openxwallet-record` row's `sha256:` refreshed to the value this tree
      computes and that row's `schema_version: 1 → 2` (it mirrors the file's
      `contract_schema_version`); the other seven rows PROVEN unchanged by
      recomputation, not assertion.
- [ ] 4.2 `contracts/CHANGELOG.md`: a `wallet-v1.3` entry stating the change
      class (ADDITIVE MINOR), that ONE digested artifact moved and which, the
      four new finding codes, the one changed comparison basis with the
      in-tree precedent for reusing `custody-model-unknown` at a new depth, the
      version-field reading from D8, and what a consumer must do (pin bump;
      nothing they declare becomes invalid).
- [ ] 4.3 `contracts/openxwallet/README.md`: the record row and the opening
      "A wallet is a signing key…" sentence carry the key SET. No digest impact
      (the README is `pinned_by_commit_only`).
- [ ] 4.4 Full local gate bar green: `verify-contract-pin.py`, the syntax gate,
      the validator plain AND `--strict`, `pytest tests/ -q`,
      `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`.
- [ ] 4.5 `AGENTS.md`'s Speckit block moves to feature `015-multi-key-wallets`
      and stops naming feature 014's change as held (alignment concern 10).
- [ ] 4.6 Annotated tag `wallet-v1.3` at the MERGE sha, after re-proving the gate
      bar at that head. Push the tag. `wallet-v1.3.digests.yaml` over
      `member_class: owned` members remains the OPERATOR act it has been since
      `wallet-v1.0` and is not produced here.

## 5. Consumer completion — openxFactory (tracked here, executed there)

- [ ] 5.1 `governance/review-authority/wallets/wal-agent-mrc-0001.yaml` declares
      the four seat keys under `keys:`, fingerprints VERBATIM from the mint
      record, custody `holder_readable` each per design D7, `did` and
      `public_key_multibase` DERIVED from the mint record's public halves by the
      `did:key` encoding the live root key already uses. The root key's
      declaration is byte-untouched.
- [ ] 5.2 `contracts/openxwallet-pin.yaml` + the gitlink move to the
      `wallet-v1.3` sha; the `openxwallet-record` digest row refreshed; the other
      seven rows unchanged.
- [ ] 5.3 The consumer gate proves THREE things: the register's 4-of-4 seat-key
      note still fires; the wallet record validates with FIVE declared keys
      (asserted against 2.7's note, positively, not by absence of failure); and
      the register's and the wallet's fingerprints for each of the four seat keys
      AGREE — proven by computation in the pull request, since the cross-surface
      check itself is a named successor (alignment concern 11).

## 6. Ledger ticks this discharges

- [ ] 6.1 `openspec/changes/add-per-seat-register-entries/tasks.md` §7.3 — the
      several-keys successor, whose trigger this change answers.
- [ ] 6.2 `openspec/changes/add-per-seat-register-entries/design.md` "Named
      successors" item 3.
- [ ] 6.3 `specs/014-per-seat-register-entries/spec.md` "Out of scope" — the
      several-keys line, annotated with where it went.
- [ ] 6.4 `openspec/specs/openxwallet/spec.md` `## Purpose`: "a signing key
      anchored to a decentralized identifier" becomes the key SET. NO DELTA FORM
      REACHES `## Purpose` (alignment item 12), so this is an editorial
      correction made in the realization and ratified by this change; without it
      the promoted spec ships contradicting its own first requirement.

## 7. Named successors — NOT taken here (design D6)

- [ ] 7.1 Subwallets.
- [ ] 7.2 Per-key grants.
- [ ] 7.3 Delegation chains (a key authorizing another key).
- [ ] 7.4 Shared holders (one key declared by two wallets).
- [ ] 7.5 A cross-surface fingerprint-agreement check between the register's
      `seat_keys[]` and the same key's wallet declaration — capability
      `review-authority-register-reader`, not `openxwallet`. Narrowed by 2.6:
      each surface now proves its own fingerprint, and what remains unchecked is
      only that the two describe the same 32 bytes.
- [ ] 7.6 Per-key custody in hermes-install's projection. TRIGGER: the first
      wallet whose declared keys carry DIFFERENT custody models and are both
      projected. Until then `custody_model_in_force` matches without a change.
- [ ] 7.7 An independent OPTIONAL `custody` block on `key_reference`, so the
      wallet's issuance ceiling and its primary key's per-key custody can
      diverge (design D10). Additive when wanted; nothing needs it yet.
