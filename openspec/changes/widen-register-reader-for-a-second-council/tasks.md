# Tasks: widen-register-reader-for-a-second-council

Lane: hermes-wallet-exercise

Dependency-ordered, and the order is inherited rather than chosen: openxFactory's
ratified `register-gate-rules-council-seats` fixes it as a FINDING — there is no
interleaving in which its register carries a second authority row and the
REQUIRED `wallet-validation` check is green at the pinned reader.

**Tags.** Untagged = openXwallet. `[openxFactory]` = `opensoft/openxFactory`.
`[OPERATOR]` = only Brett can perform it — a ratification, a tag, a platform
setting. `[GOVERNANCE]` = it needs a ruling or a ratification before the work is
legal.

**Row mapping.** openxFactory tasks §2 rows 2.1–2.6 are tagged `[openXwallet]`
and are this change's §1–§4; its rows 2.7–2.9 stay that repository's and are
named in §5. Each row below cites the openxFactory row it discharges.

---

## 1. Governance — ratification and the open questions

- [x] 1.1 **[openxFactory row 2.1]** OPEN this change under the id
      openxFactory's ratified packet declares — `widen-register-reader-for-a-second-council`,
      cited in `proposal.md`'s `sequenced_after:`, `tasks.md` row 2.1,
      `README.md` and `tests/sequenced_after/corpus-ledger.yaml`. Both defects
      re-measured here at `b7b0fbb3` / `wallet-v1.4`, which is byte-identical to
      this repository's `main` for `scripts/validate-openxwallet.py`
      (`design.md` D0).
- [ ] 1.2 **[OPERATOR] [GOVERNANCE]** Ratify or return this proposal. **Nothing
      in §3 or §4 is legal until this is ticked**, and ratification alone
      realizes nothing: no reader line moves, no bundle is cut, no pin advances.
      §2 is deliberately NOT gated on it — authoring a failing test that
      measures the reader as it stands prejudges nothing.
- [ ] 1.3 **[OPERATOR] [GOVERNANCE]** Rule **Q-WRR-1** — is
      `register-minimal-shape-exceeded` RETIRED or RE-SCOPED? Recommendation on
      record: retire it by name, with a removed-refusal note in
      `contracts/CHANGELOG.md` at the cut. Ground measured (`design.md` D5): the
      only citations in the workspace are this repository's validator and one
      openxFactory Speckit document; openxFactory's consumer gate matches
      `register-*` by wildcard.
- [ ] 1.4 **[OPERATOR] [GOVERNANCE]** Rule **Q-WRR-2** — does a widened reader
      need a positive numeric bound at all? Recommendation on record: no bound,
      stated in the spec text as a decision rather than left as an omission.
- [ ] 1.5 **[OPERATOR] [GOVERNANCE]** Rule **Q-WRR-3** — does
      `add-per-seat-register-entries` task 7.1 (the absent-seat-surface NOTE
      becoming a REFUSAL, trigger fired 2026-08-28) ride this release?
      Recommendation on record: NO — it would break the pin-neutrality this
      change owes openxFactory task 2.9, and it deserves its own release after
      the register act has settled.
- [ ] 1.6 **[OPERATOR] [GOVERNANCE]** Rule **Q-WRR-4** — does openXwallet adopt
      a sibling-delta convergence device? Recommendation on record: the minimum
      only (a declared `archive_after:`, which this change uses); a corpus
      ledger waits for a fourth collision. The two PRE-EXISTING colliding
      MODIFIED blocks on `### Requirement: Revocation propagates through the
      chain` (`add-composition-drift-cascade` vs `add-multi-key-wallets`, not
      byte-identical) are named in `proposal.md` and are NOT fixed by this
      change.
- [ ] 1.7 **[OPERATOR] [GOVERNANCE]** Rule **Q-WRR-5** — keep this change's id
      or rename it. Recommendation on record: keep it, because four committed
      citations on openxFactory `main` resolve to it and one of them is read by
      a test suite; a rename for accuracy is a deliberate openxFactory
      bookkeeping act, not a side effect.
- [ ] 1.8 On ratification, set `proposal.md`'s `Status:` to `ratified`, add the
      `Ratified:` line with the word verbatim, and record the five rulings
      beside the questions they answer.
- [ ] 1.9 `OPENSPEC_TELEMETRY=0 openspec validate widen-register-reader-for-a-second-council
      --strict` and `--all --strict` clean from the repository root.

## 2. RED FIRST — carried by THIS pull request

**[openxFactory row 2.2].** Authoring a test that measures the reader as it
stands is not gated on ratification, and landing the measurement with the
proposal is what makes the proposal answerable: a reviewer can run the failing
tests rather than take the transcript on trust.

- [x] 2.1 `tests/widen_register_reader/test_second_council.py`, driving the
      validator as a SUBPROCESS over fixture trees under `tmp_path` — the
      discipline `tests/per_seat_register_entries/` established, so the exit
      codes the workflows act on are the ones under test and nothing touches the
      repository or the packaged corpus.
- [x] 2.2 **RED** — `test_a_second_commissioned_body_is_refused_today`: two
      authority rows, each resolving end to end to its own wallet, grant and
      custody attestation, asserted CLEAN. **Fails today** with exactly
      `register-minimal-shape-exceeded`, asserted by CODE and marked
      `xfail(strict=True)` so it fails loudly the moment the fix lands and is
      converted.
- [x] 2.3 **RED** — `test_two_councils_may_seat_the_same_role_name`: one
      `seat_id` recorded under two different `council_id`s, each attached to its
      own body's row, asserted CLEAN. **Fails today** with exactly
      `register-seat-duplicate`.
- [x] 2.4 **PASSING NOW AND AFTER** —
      `test_one_council_naming_a_seat_twice_is_refused`: the same `seat_id`
      twice under ONE `council_id`, asserted REFUSED with
      `register-seat-duplicate`. It passes today and must keep passing: the fix
      narrows the trigger and must not remove the refusal.
- [x] 2.5 **PASSING NOW AND AFTER (the regression)** —
      `test_the_live_one_row_register_stays_clean`: the shape openxFactory
      commits TODAY — one authority row, four per-seat entries under one council
      — asserted clean with the notes `1 row(s)` and `4 of 4`, plain and
      `--strict`. This is openxFactory task 2.9's neutrality gate expressed as a
      test in the repository that owns the reader.
- [x] 2.6 **PASSING NOW AND AFTER** —
      `test_key_id_and_fingerprint_stay_globally_unique`: a `key_id` and a
      `key_fingerprint` repeated ACROSS two councils, asserted REFUSED with
      `register-seat-duplicate`. The fix must not narrow these two to the
      council alongside `seat_id`.
- [x] 2.7 **PASSING NOW AND AFTER** —
      `test_a_second_row_that_does_not_resolve_is_refused`: two rows where the
      second's grant does not back it, asserted REFUSED with
      `register-grant-mismatch` — proving the widening is not a relaxation.
- [x] 2.8 The fixture's synthetic seat keys are asserted to RECOMPUTE
      (`test_the_probe_keys_recompute`), independently of the reader, so a stale
      fixture cannot make a negative pass for the wrong reason. Mirrors
      `test_the_mint_records_four_keys_recompute`.

## 3. The fixes — AFTER ratification (§1.2), not before

- [ ] 3.1 **[openxFactory row 2.3]** Key `_check_seat_keys`' duplicate table on
      the PAIR (`council_id`, `seat_id`). **Leave `key_id` and
      `key_fingerprint` uniqueness GLOBAL.** The refusal keeps the code
      `register-seat-duplicate` and its message names the council.
- [ ] 3.2 **[openxFactory row 2.4] [GOVERNANCE]** Per the Q-GRC-5 ruling, retire
      `REGISTER_MVP_SINGLE_ROW` and its refusal in favour of the three
      invariants (`design.md` D1/D3), rather than substituting the number 2 for
      the number 1. Retire `register-minimal-shape-exceeded` by name per the
      Q-WRR-1 ruling; re-point it at nothing.
- [ ] 3.3 Convert §2's two `xfail(strict=True)` tests to plain assertions in the
      same commit as the fix they measure. A strict xfail that starts passing
      fails the suite, so this cannot be forgotten silently — but the conversion
      is what makes the test an assertion about the widened reader rather than a
      record of the old one.
- [ ] 3.4 **[openxFactory row 2.5]** Extend the reader's own S4 self-test block
      with the four probes `design.md` D4 names — two-bodies-clean,
      two-councils-one-seat-name, seat-duplicate-within-one-council, and
      second-row-unresolved — and REMOVE the
      `self-test/register-minimal-shape-exceeded` probe in the same edit, so the
      self-test never asserts a refusal the reader can no longer emit.
- [ ] 3.5 Update the reader's own comments where they state the retired rule:
      the `REGISTER_MVP_SINGLE_ROW` block, `check_register`'s docstring, the
      `REVOKED IS EXEMPT` note (which cites the cap as forbidding the second
      row a re-issuance would need), and `_check_seat_keys`' duplicate comment.
      A comment that describes a removed constant is the same defect one
      altitude up from a spec that does.
- [ ] 3.6 Run the full gate bar locally: `scripts/verify-contract-pin.py`, the
      syntax gate, the validator plain and `--strict`, `python3 -m pytest
      tests/ -q`, and `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`
      (AGENTS.md rule 5).

## 4. The release — allocated at realization, never reserved

- [ ] 4.1 **[openxFactory row 2.6] [OPERATOR]** Cut the bundle
      (`wallet-v1.5` or as allocated). AGENTS.md rule 6: FIVE coordinated
      values — per-file `contract_schema_version` (all UNCHANGED here),
      `contract_bundle_version` in `contracts/manifest.yaml`, an annotated
      `wallet-v<major>.<minor>` tag, the exact release commit with per-file
      digests, and the `contracts/CHANGELOG.md` entry.
- [ ] 4.2 Cut `contracts/releases/wallet-v1.<n>.digests.yaml` BY RECOMPUTATION
      over the tree, as v1.2/v1.3/v1.4 were, and prove it differs from its
      predecessor in exactly ONE line, `bundle_tag`. This is the reader-only
      release class: a consumer's pin bump then moves `commit:` and
      `contract_bundle_tag:` and nothing else.
- [ ] 4.3 `contracts/CHANGELOG.md` entry, carrying the MIGRATION NOTE for the
      retired refusal `register-minimal-shape-exceeded` (Q-WRR-1) — a REMOVED
      finding code, named, with the estate search that measured its blast
      radius. AGENTS.md rule 2 requires the note even though the search found no
      consumer pinning it.
- [ ] 4.4 Realization evidence recorded on this change before archive: merged,
      green, and the openxFactory pin advanced (see §5.1) — because a reader
      release no consumer pins has widened nothing.

## 5. Owed downstream, named with owners — NOT discharged here

- [ ] 5.1 **[openxFactory row 2.7]** Advance `contracts/openxwallet-pin.yaml`:
      `commit:` and `contract_bundle_tag:` ONLY; no `files:` digest row moves,
      because `scripts/validate-openxwallet.py` sits under
      `pinned_by_commit_only:`. Reverify the other eight digests by
      recomputation at the new commit.
- [ ] 5.2 **[openxFactory row 2.8]** Move the consumer gate's LITERAL assertions
      in `.github/workflows/openxwallet-consumer-gate.yml` in the SAME pull
      request as 5.1: `4 of 4 per-seat signing key(s)…` → `8 of 8`, plus a new
      assertion for `wal-agent-grc-0001`'s five declared keys. Every count stays
      LITERAL.
- [ ] 5.3 **[openxFactory row 2.9]** The neutrality gate: with 5.1 + 5.2 landed
      and the register still at ONE row, `wallet-validation` is GREEN and the
      note still reads `1 row(s)`. §2.5's regression test is this change's half
      of that proof.
- [ ] 5.4 **[openxFactory]** `specs/014-register-and-reader/data-model.md` cites
      `register-minimal-shape-exceeded` / `REGISTER_MVP_SINGLE_ROW`. It is a
      Speckit design document for a realized feature, not a test, so nothing
      breaks — but it becomes stale on the day §3.2 lands. Owner: the arc owner
      of `add-wallet-carried-review-authority`.
- [ ] 5.5 **[openxFactory]** If Q-WRR-5 is ruled RENAME, the id moves in four
      committed places on that repository's `main` — `proposal.md`'s
      `sequenced_after:`, `tasks.md` row 2.1, `README.md`, and
      `tests/sequenced_after/corpus-ledger.yaml` — plus this directory. One
      deliberate act, or none.

## 6. Archive gate

- [ ] 6.1 **`add-per-seat-register-entries` ARCHIVES FIRST.** MEASURED on
      openspec 1.2.0: an archive whose target spec does not exist aborts with
      *"target spec does not exist; only ADDED requirements are allowed for new
      specs. MODIFIED and RENAMED operations require an existing spec."* The
      capability `review-authority-register-reader` lives only in that change's
      delta today. `--strict` validation passes in either order; only the
      archive is ordered. Declared in `proposal.md`'s `archive_after:`.
- [ ] 6.2 `code_surface` is NOT `none`, so per `release-realization` this change
      archives only on MERGED, GREEN REALIZATION EVIDENCE. The evidence set is
      exactly: §3 merged and green; §4 cut with the CHANGELOG migration note;
      §5.1–§5.3 merged on the openxFactory side with `wallet-validation` green
      and the register still at one row; §1.3–§1.7 ruled and recorded.
- [ ] 6.3 §5.4 and §5.5 are EXPLICITLY OUT of the archive gate — they are
      another repository's bookkeeping, and holding this change open on them
      would park a reader release on a documentation edit.
- [ ] 6.4 Before archive, re-run the full gate bar (§3.6) and re-read
      openxFactory's register at the then-current `origin/main`: if the second
      row has landed, the regression test's one-row fixture is still correct
      (it is a FIXTURE, not a copy of the live file) but §2.5's citation of the
      live shape needs its note updated to say so.
