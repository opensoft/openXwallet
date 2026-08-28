# Feature Specification: wallet-v1.2 — the register's top level is read, and per-seat keys are enforced

**Feature Branch**: `014-per-seat-register-entries`

**Created**: 2026-08-28

**Status**: Draft — GATED on the ratification of the governing change

**Input**: "Build the register successor: let openxFactory's review-authority
register carry per-seat authority entries with key fingerprints, so the four seat
keys minted 2026-08-28 become verifiable end to end and the authorization POST's
`review_authority.root_key_mismatch` refusal can clear."

## Governing authority

This feature realizes the openXwallet OpenSpec change
`openspec/changes/add-per-seat-register-entries/` — capability
`review-authority-register-reader`, three ADDED requirements — whose designs
**D1** (a per-seat key surface, the cap re-grounded not raised), **D2** (the
register carries the key AND the fingerprint, and the reader recomputes), **D3**
(the top level is a closed read set), **D4** (the staleness bound's grammar is
hermes-install's), **D5** (errors and notes, never warnings), **D6** (additive
finding codes only), **D7** (the seven-field entry, chosen by a
projection-completeness test), **D8** (what "an unknown seat" can mean to this
reader), **D9** (register-side seat keys and rule (r)), **D10** (`seat_keys`
optional, absence a note) and **D11** (hermes-install needs no code change) are
decided there. Nothing here re-opens them.

**THE RATIFICATION GATE IS UNCHECKED.** That change is `Status: draft`, held for
Brett Heap. This branch is authored so the ratification decides a real thing
rather than an intention, and it must not merge before the packet is ratified.

Upstream, the work is item 2 of the numbered successor list in codexFactory
`hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`
(merged `78b8fa2`), and it discharges `add-composition-drift-cascade` task 3.4.

Scope boundaries fixed by the governing change and NOT negotiable here:

- **No `contracts/` byte.** All eight digested artifacts stay byte-identical, and
  that is proven mechanically, not asserted.
- **The tag is `[OPERATOR]`.** `wallet-v1.2` follows the human merge. No agent
  tags.
- **The register edit is openxFactory's**, on a permanently human-only surface.
  This feature makes it adjudicable and writes none of it.
- **The projection is an operator act.** D11 determines that hermes-install needs
  no code change; re-deriving its projection content is out of scope here.

## Requirements

### FR-001 — The register's top-level key set is closed
`check_register` SHALL enumerate `register_version`,
`revocation_staleness_bound`, `rows` and `seat_keys`, and SHALL refuse any other
top-level key as `register-top-level-unknown`.

### FR-002 — `revocation_staleness_bound` is required and validated
It SHALL be present (`register-staleness-bound-missing`) and a well-formed
non-zero ISO-8601 duration of weeks, days, hours, minutes and seconds
(`register-staleness-bound-malformed`); years, months, an empty designator and a
zero-length window SHALL be refused.

### FR-003 — The seat surface's shape
`seat_keys`, when present, SHALL be a non-empty list of mappings whose field set
is exactly `{seat_id, council_ref, council_id, key_id, public_key,
key_fingerprint, authorizing_row}`, each value a non-empty string
(`register-seat-keys-malformed`).

### FR-004 — Each key is self-consistent
`public_key` SHALL be 43 characters of CANONICAL unpadded base64url over 32 raw
bytes (`register-seat-key-malformed`); `key_fingerprint` SHALL match
`sha256:<64 lowercase hex>` (`register-seat-fingerprint-malformed`) and SHALL
recompute from `public_key` (`register-seat-fingerprint-mismatch`).

### FR-005 — Each entry descends from a live row
`authorizing_row` SHALL resolve to a row in the same register that is `active`
and unexpired by COMPUTED time (`register-seat-row-unresolved`), and
`council_ref` SHALL equal that row's `holder_ref`
(`register-seat-council-mismatch`).

### FR-006 — The two spellings denote one body
`council_ref` SHALL equal `agent:` + `council_id` with underscores replaced by
hyphens (`register-seat-council-spelling`).

### FR-007 — Uniqueness
A repeated `seat_id`, `key_id` or `key_fingerprint` SHALL be refused
(`register-seat-duplicate`), never resolved by file order.

### FR-008 — The cap is re-grounded
`REGISTER_MVP_SINGLE_ROW` SHALL stay `1` over `rows`, its refusal SHALL name the
cap as binding AUTHORITY rows, and `seat_keys` SHALL take no count bound.

### FR-009 — Two notes, never warnings
A populated surface SHALL note the number ADJUDICATED out of the number
recorded; an absent surface SHALL note that no per-seat signing key is recorded
and that a projection built from the register can authorize no seat. Both SHALL
be notes.

### FR-010 — Nothing else moves
The eight digested contract artifacts SHALL be byte-identical, the packaged
corpus SHALL adjudicate identically to the previous release, and no existing
finding code SHALL be renamed or repurposed.

## Assumptions

- openxFactory is the only repository in the estate carrying a register
  (verified against codexFactory, LedgerxFactory, MedxFactory, LedgerxWallet and
  openXwallet), so requiring the staleness bound disturbs no consumer.
- The four public halves and fingerprints in
  `SEAT_KEY_MINT_RECORD_2026_08_28` are the mint record's, verbatim, and each
  recomputes — asserted in both the self-test and the pytest suite.

## Out of scope

A register schema (design D11 upstream stands: the reader is the shape); a
wallet record declaring several keys (a contract change, named as a successor —
TAKEN by `add-multi-key-wallets` and released as `wallet-v1.3`, 2026-08-28);
resolving seat ids against the council's roster (needs a cross-repository read
path that does not exist); strictness over the attestation documents beside the
register (same class, different shape, named as a successor).
