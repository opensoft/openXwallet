# Tasks: 014-per-seat-register-entries

Boxes are checked only against a run that was actually made. `[OPERATOR]` and
`[openxFactory]` tasks are out of this branch's scope and are listed so the
handoff is legible.

## Phase 0 — the gate

- [ ] T001 **`add-per-seat-register-entries` is ratified.** Held for Brett Heap.
      This branch is authored and green, and MUST NOT merge before this box is
      checked upstream. Its pull request says so.

## Phase 1 — the reader

- [x] T002 Module docstring rule (u) extended: the whole top level is read; the
      per-seat surface is read and enforced; the cap binds authority rows.
- [x] T003 `REGISTER_TOP_LEVEL_FIELDS` / `REGISTER_TOP_LEVEL_REQUIRED`
      enumerated; closure check in `check_register` before anything is
      adjudicated (`register-top-level-unknown`). FR-001.
- [x] T004 `_check_staleness_bound` — required, weeks/days/hours/minutes/seconds,
      no years or months, no empty designator, no zero-length window
      (`register-staleness-bound-missing`, `-malformed`). Grammar and reasoning
      are hermes-install's. FR-002. **Discharges
      `add-composition-drift-cascade` task 3.4.**
- [x] T005 `REGISTER_SEAT_FIELDS` (seven names) and
      `SEAT_COUNCIL_HOLDER_PREFIX`, with the two-spellings rationale recorded at
      the constant. FR-003, FR-006.
- [x] T006 `_decode_public_key` — canonical 43-character unpadded base64url over
      32 raw bytes, checked by ROUND TRIP so trailing bits in the final sextet
      cannot spell one key and mean another. FR-004.
- [x] T007 `_fingerprint_of` — the one spelling the mint record and the runtime
      both compute. FR-004.
- [x] T008 `_check_seat_keys` — the surface, its per-entry refusals, its
      usable-row index, and its two notes; entries counted ADJUDICATED, never
      parsed. FR-003 – FR-007, FR-009.
- [x] T009 The cap's refusal text re-grounded to name AUTHORITY rows;
      `REGISTER_MVP_SINGLE_ROW` unchanged at 1. FR-008.

## Phase 2 — proof inside the pinned validator

- [x] T010 `SEAT_KEY_MINT_RECORD_2026_08_28` — the four real public halves and
      fingerprints, copied verbatim from codexFactory's merged mint record, with
      a self-test assertion that each recomputes.
- [x] T011 `_s4_tree` gains `top=` and now writes the required staleness bound,
      so the nine existing `_register_probe` expected-code sets are unchanged.
- [x] T012 New probes: unknown top-level key; bound missing; seven malformed
      bounds; five well-formed bounds; three malformed surfaces; unknown field;
      missing field; private-seed-shaped key; non-canonical key; malformed
      fingerprint; mismatched fingerprint; three duplicate fields; unresolved
      row; expired row; council mismatch; council spelling; the cap not raised;
      the live spelling pair; the positive four-seat probe and its note.
- [x] T013 Self-test green: `python3 scripts/validate-openxwallet.py` → 0/0.

## Phase 3 — the offline suite

- [x] T014 `tests/per_seat_register_entries/test_top_level_and_seat_keys.py`,
      subprocess-driven, one named code per negative, positives asserting the
      ADJUDICATED count. 47 new tests.
- [x] T015 `tests/nested_repo_prune/..::_register_tree` declares the bound, with
      the reason recorded in place.
- [x] T016 `python3 -m pytest tests/ -q` → 69 passed (was 22).

## Phase 4 — the proofs this feature owes

- [x] T017 **The eight digests are unchanged, proven not asserted.** Every
      `sha256:` in `contracts/manifest.yaml` AND every one in openxFactory's
      `contracts/openxwallet-pin.yaml` `files:` block recomputes to its recorded
      value over this tree. 9/9 (the eight owned plus the vendored envelope).
- [x] T018 **The four real entries adjudicate clean.** A copy of openxFactory's
      live `governance/review-authority/` tree with the exact `seat_keys:` block
      the downstream pull request will commit: `4 of 4 per-seat signing key(s)
      adjudicated and resolved`, 0 errors, 0 warnings, under `--strict`.
- [x] T019 **The current live register still passes**, unedited — the
      no-mixed-state property: gitlink-first is green because the bound is
      already declared and the absent surface is a note.

## Phase 5 — release bookkeeping

- [x] T020 `contracts/manifest.yaml` → `contract_bundle_version: wallet-v1.2`.
- [x] T021 `contracts/CHANGELOG.md` — the `wallet-v1.2` entry, newest-first,
      naming the unchanged digests and the evidence.
- [x] T022 `AGENTS.md` active-Speckit block points at this feature.
- [ ] T023 **[OPERATOR]** the annotated `wallet-v1.2` tag, after the human merge.

## Phase 6 — handoff (not this branch)

- [ ] T024 **[openxFactory]** pin bump (`commit`, `contract_bundle_tag`; the
      eight `files:` digests unchanged) AND the four `seat_keys` entries in
      `governance/review-authority/register.yaml`, in ONE commit — a
      **human-only** pull request over a never-clearable floor file.
- [ ] T025 **[openxFactory]** the consumer gate's positive-proof step gains an
      assertion on the adjudicated seat-key note, so a green check proves the
      four seats were READ.
- [ ] T026 **[OPERATOR]** re-derive and establish the Hermes register
      projection. No hermes-install code change (design D11); `council_id` keeps
      the runtime's underscore spelling, which the register now records so
      nothing is translated by hand.
- [ ] T027 **[OPERATOR]** confirm `review_authority.root_key_mismatch` no longer
      fires for a seat whose key the register records.
