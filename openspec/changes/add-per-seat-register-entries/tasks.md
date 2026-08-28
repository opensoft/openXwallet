# Tasks: add-per-seat-register-entries

## 1. Ratification gate

- [ ] 1.1 **RATIFICATION — Brett Heap.** `Status: draft` is held for the
      operator. Nothing below §2 may land until this box is checked and
      `proposal.md`'s `Status:` reads `ratified` with a ratification record.
      The realization branch `014-per-seat-register-entries` exists and is
      GATED on this box; its pull request says so in its own body.
- [ ] 1.2 The one reversible decision, named for the ruling: `design.md` **D1**
      takes the mint record's SECOND exit (a per-seat key surface) over its
      first (row-set semantics). Ratifying as proposed ratifies that choice.

## 2. Alignment

- [x] 2.1 Compact alignment pass run before ratification was sought; verdicts
      recorded in `proposal.md` under `## Alignment pass, 2026-08-28`. It
      returned two MISALIGNED verdicts and two vacuous passes; all four are
      fixed in these artifacts, and the fix to `design.md` D7 changed the entry
      shape from six fields to seven.
- [x] 2.2 Council-or-not call stated in `proposal.md` under `## Council or not —
      the call, stated`: no convening sought, three reasons, and the packet is
      unamended if the convener rules otherwise.

## 3. Declared realization surface (openXwallet)

Authorized by ratification and by nothing else. ONE Speckit feature.

- [ ] 3.1 **`check_register` reads the whole top level.** Enumerate
      `register_version`, `revocation_staleness_bound`, `rows`, `seat_keys`;
      refuse an unrecognized key as `register-top-level-unknown`. The closure is
      the point (`design.md` D3) — a field-by-field fix leaves the class open.
- [ ] 3.2 **`revocation_staleness_bound` enters the enforced read set.**
      Required; `P<n>W` or `P<n>D` with an optional `T…` part; years and months
      refused; a `T` with no components refused; a zero-length window refused.
      Codes `register-staleness-bound-missing` /
      `register-staleness-bound-malformed`. Grammar and reasoning are
      hermes-install's, deliberately (`design.md` D4). **This discharges
      `add-composition-drift-cascade` task 3.4** — record that against it when
      this change archives (§6.1).
- [ ] 3.3 **The seat-key surface.** `seat_keys` optional, a non-empty list when
      present, each entry a mapping whose field set is EXACTLY
      `{seat_id, council_ref, council_id, key_id, public_key, key_fingerprint,
      authorizing_row}` (`design.md` D7). Per entry: canonical 43-character
      unpadded base64url public key; `sha256:<64 lowercase hex>` fingerprint;
      the fingerprint RECOMPUTED from the key; `authorizing_row` resolving to a
      row in this file that is `active` and unexpired by COMPUTED time;
      `council_ref` equal to that row's `holder_ref`; and `council_ref` and
      `council_id` denoting ONE body. Duplicate `seat_id`, `key_id` or
      `key_fingerprint` refused rather than resolved by file order. Every
      recorded entry adjudicated or refused, never merely parsed.
- [ ] 3.4 **The cap is re-grounded, not raised.** `REGISTER_MVP_SINGLE_ROW`
      stays `1`; its refusal text says the cap binds AUTHORITY ROWS. No count
      bound on `seat_keys` — the bound is structural (`design.md` D1).
- [ ] 3.5 **Two notes, never warnings** (`design.md` D5): one naming how many
      recorded seat keys were ADJUDICATED out of how many are recorded, one
      naming that none are recorded and that a projection built from this
      register can authorize no seat. Both are notes because LedgerxFactory runs
      `--strict`. The first is the line openxFactory's positive-proof step
      asserts on, which is why it must count adjudication and not parsing.
- [ ] 3.6 **Self-test probes extended** in `self_test()`, matching the existing
      `_register_probe` convention exactly: one probe per new refusal, plus a
      POSITIVE probe carrying the FOUR REAL public halves and fingerprints from
      codexFactory `hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`
      (merged `78b8fa2`) — copied verbatim, so a transcription slip fails here
      and never reaches openxFactory.
- [ ] 3.7 **`tests/` suite** under `tests/per_seat_register_entries/`, run by
      `pytest-suite`: the positive four-seat register; every negative in §3.3;
      the staleness-bound negatives; the second-row refusal unchanged; the
      absent-`seat_keys` note; and a corpus-invariance assertion — the packaged
      corpus adjudicates IDENTICALLY before and after (same finding set, same
      exit code), because this change touches no contract byte.
- [ ] 3.8 **The eight contract digests are unchanged, and it is PROVEN**, not
      asserted: recompute each `sha256:` in `contracts/manifest.yaml` and each
      in openxFactory's `contracts/openxwallet-pin.yaml` `files:` block over the
      realization tree and show equality. `scripts/validate-openxwallet.py` is
      in the pin's `pinned_by_commit_only:` list, so a reader edit moves the
      COMMIT and no digest.
- [ ] 3.9 **Release bookkeeping**, allocated at realization and not reserved
      here: `contract_bundle_version` → the next additive minor, the
      `contracts/CHANGELOG.md` entry naming the reader change and the unchanged
      digests, and the annotated `wallet-v<major>.<minor>` tag. **The tag is
      `[OPERATOR]`** and follows the human merge — no agent tags.
- [ ] 3.10 Full local gate bar before pushing (AGENTS.md rule 5):
      `scripts/verify-contract-pin.py`, the syntax gate, the validator plain AND
      `--strict`, `python3 -m pytest tests/ -q`, and
      `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`.

## 4. Downstream, gated on §3 merging and the tag (openxFactory)

- [ ] 4.1 `contracts/openxwallet-pin.yaml`: `commit` → the release commit,
      `contract_bundle_tag` → the new tag. The eight `files:` digests are
      UNCHANGED (§3.8 is the proof).
- [ ] 4.2 `governance/review-authority/register.yaml` gains the four `seat_keys`
      entries with the mint record's exact public halves and fingerprints.
      **[HUMAN-ONLY]** — the register is a permanently human-only surface by
      ratified requirement and by name in gate rules; the pull request IS the
      human act, and no council verdict may clear it.
- [ ] 4.3 The consumer gate's positive-proof step gains an assertion on the
      seat-key note, so a green check PROVES the four seats were read. A green
      check that proves nothing was read is the class that step exists to close.
- [ ] 4.4 Gitlink and pin move TOGETHER in one commit — never a mixed state.
      (`design.md` D10 makes either ordering green, which is a safety net, not a
      licence to split them.)

## 5. Downstream, operator (hermes-install and the runtime)

- [ ] 5.1 **[OPERATOR]** Re-derive the register projection from the register that
      now carries the keys, and establish it. `design.md` **D11** determines
      that this is CONTENT ONLY: no hermes-install code change and no schema
      change — its projection schema and reader at `cba1a2b` already require and
      recompute per-seat `key_id` / `key_fingerprint` / `public_key`.
- [ ] 5.2 **[OPERATOR]** Confirm `review_authority.root_key_mismatch` no longer
      fires for a seat whose key the register now records — the refusal this arc
      is clearing. Steps 4 and 5 of the mint record's successor list (the
      per-target credential and machinery map; a hermes-install image carrying
      the verifying half) remain that record's, not this change's.

## 6. Upstream bookkeeping

- [ ] 6.1 Record against `add-composition-drift-cascade` that its task 3.4
      (`revocation_staleness_bound` validated by the register reader) is
      discharged by this change, so it is not carried twice or archived as
      outstanding.
- [ ] 6.2 Record against openxFactory `add-wallet-carried-review-authority` that
      the per-seat successor its intake requirement NAMED was authored here, on
      the reader side, per the precedent of that change's
      `## Addendum — split-openxwallet-repo P3 (2026-08-27, contract-v2.0)`,
      which moved the wallet deltas' home to this repository (its `tasks.md`
      line 521 records the same handoff for the S5 core deltas).
- [ ] 6.3 Record against codexFactory's mint record that item 2 of its numbered
      successor list ("the register successor") is realized, and that item 3
      (the client-tree projection) is unblocked and is an operator act.
- [ ] 6.4 Record the realization evidence on this change before archiving —
      merged, green — and re-run the full gate bar at archive.

## 7. Named successors, with triggers

Declared here so they are obligations with conditions rather than intentions.
None of them is part of this change's realization surface.

- [ ] 7.1 **The absence flip.** TRIGGER: openxFactory's register carries the four
      `seat_keys` entries AND its pin points at this reader (§4 complete). THEN
      the absent-surface NOTE becomes a REFUSAL in the next additive minor,
      closing the hole `design.md` D10 names — a register that records no key
      staying green forever, with the only positive proof living in another
      repository's workflow step that no requirement here obliges. Safe only
      after the trigger, because before it the refusal would park a candidate on
      a permanently human-only file.
- [ ] 7.2 **Attestation strictness.** `_load_attestations` tolerates unknown keys
      in the custody attestations beside the register — the same vacuous-pass
      class, in the same governed directory. Needs the attestation's shape
      ENUMERATED and ratified first, which is why it is not folded in here.
- [ ] 7.3 **A wallet record declaring several keys** (`design.md` D9), which would
      make a per-seat key wallet-declared rather than register-declared. A
      contract change to a digested artifact: a bundle version and every
      consumer's pin.
- [ ] 7.4 **Roster resolution** (`design.md` D8): resolving a `seat_id` against
      the council definition that governs it. Needs a cross-repository read path
      this validator does not have and should not acquire casually.
