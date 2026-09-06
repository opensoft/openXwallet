# Tasks: add-per-seat-register-entries

## 1. Ratification gate

- [x] 1.1 **RATIFICATION — Brett Heap.** DONE 2026-08-28. `proposal.md`'s
      `Status:` reads `ratified`, its front-matter carries the `Ratified:` line,
      and `## Ratification record, 2026-08-28` records the ruling verbatim
      ("ratify #4, then merge #5, tag and complete C"). §3 is authorized by that
      ratification and by nothing else. The realization branch
      `014-per-seat-register-entries` (PR #5) was GATED on this box and is
      released by it.
- [x] 1.2 DONE — ratified as proposed, so `design.md` **D1** stands: the mint
      record's SECOND exit (a per-seat key surface) over its first (row-set
      semantics), with `REGISTER_MVP_SINGLE_ROW` kept at `1` and re-grounded
      over AUTHORITY ROWS rather than raised. Recorded in the ratification
      record.

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

- [x] 3.1 **`check_register` reads the whole top level.** Enumerate
      `register_version`, `revocation_staleness_bound`, `rows`, `seat_keys`;
      refuse an unrecognized key as `register-top-level-unknown`. The closure is
      the point (`design.md` D3) — a field-by-field fix leaves the class open.
- [x] 3.2 **`revocation_staleness_bound` enters the enforced read set.**
      Required; `P<n>W` or `P<n>D` with an optional `T…` part; years and months
      refused; a `T` with no components refused; a zero-length window refused.
      Codes `register-staleness-bound-missing` /
      `register-staleness-bound-malformed`. Grammar and reasoning are
      hermes-install's, deliberately (`design.md` D4). **This discharges
      `add-composition-drift-cascade` task 3.4** — record that against it when
      this change archives (§6.1).
- [x] 3.3 **The seat-key surface.** `seat_keys` optional, a non-empty list when
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
- [x] 3.4 **The cap is re-grounded, not raised.** `REGISTER_MVP_SINGLE_ROW`
      stays `1`; its refusal text says the cap binds AUTHORITY ROWS. No count
      bound on `seat_keys` — the bound is structural (`design.md` D1).
- [x] 3.5 **Two notes, never warnings** (`design.md` D5): one naming how many
      recorded seat keys were ADJUDICATED out of how many are recorded, one
      naming that none are recorded and that a projection built from this
      register can authorize no seat. Both are notes because LedgerxFactory runs
      `--strict`. The first is the line openxFactory's positive-proof step
      asserts on, which is why it must count adjudication and not parsing.
- [x] 3.6 **Self-test probes extended** in `self_test()`, matching the existing
      `_register_probe` convention exactly: one probe per new refusal, plus a
      POSITIVE probe carrying the FOUR REAL public halves and fingerprints from
      codexFactory `hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`
      (merged `78b8fa2`) — copied verbatim, so a transcription slip fails here
      and never reaches openxFactory.
- [x] 3.7 **`tests/` suite** under `tests/per_seat_register_entries/`, run by
      `pytest-suite`: the positive four-seat register; every negative in §3.3;
      the staleness-bound negatives; the second-row refusal unchanged; the
      absent-`seat_keys` note; and a corpus-invariance assertion — the packaged
      corpus adjudicates IDENTICALLY before and after (same finding set, same
      exit code), because this change touches no contract byte.
- [x] 3.8 **The eight contract digests are unchanged, and it is PROVEN**, not
      asserted: recompute each `sha256:` in `contracts/manifest.yaml` and each
      in openxFactory's `contracts/openxwallet-pin.yaml` `files:` block over the
      realization tree and show equality. `scripts/validate-openxwallet.py` is
      in the pin's `pinned_by_commit_only:` list, so a reader edit moves the
      COMMIT and no digest.
- [x] 3.9 **Release bookkeeping**, allocated at realization and not reserved
      here: `contract_bundle_version` → the next additive minor, the
      `contracts/CHANGELOG.md` entry naming the reader change and the unchanged
      digests, and the annotated `wallet-v<major>.<minor>` tag. **The tag is
      `[OPERATOR]`** and follows the human merge — no agent tags.
- [x] 3.10 Full local gate bar before pushing (AGENTS.md rule 5):
      `scripts/verify-contract-pin.py`, the syntax gate, the validator plain AND
      `--strict`, `python3 -m pytest tests/ -q`, and
      `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`.

### Realization evidence for §3 (merged, green, tagged — 2026-08-28)

All of §3 is landed by ONE Speckit feature, `014-per-seat-register-entries`,
merged as **openXwallet PR #5 (`93b0a47`)** and released as the annotated tag
**`wallet-v1.2`** pointing at that commit. Boxes are checked against runs that
were actually made, at that exact head:

- `python3 scripts/validate-openxwallet.py .` — 0 errors, 0 warnings
- `python3 scripts/validate-openxwallet.py . --strict` — 0 errors, 0 warnings;
  corpus 17 positive examples, 36 negative confirmations across 13/13
  requirements
- `python3 scripts/wallet-yaml-syntax-gate.py .` — exit 0
- `python3 scripts/verify-contract-pin.py` — OK, 1 vendored file matches at
  openxFactory@30565e48ffe3 (bundle contract-v1.44)
- `python3 -m pytest tests/ -q` — **69 passed**
- `OPENSPEC_TELEMETRY=0 openspec validate --all --strict` — 4 passed, 0 failed

`contracts/manifest.yaml` reads `contract_bundle_version: wallet-v1.2` at that
sha, and `contracts/CHANGELOG.md` carries the `wallet-v1.2` entry naming the
reader change and the unchanged digests (§3.9). **§3.9's tag is `[OPERATOR]`
and was authorized as one**: Brett Heap ruled in-session "ratify #4, then merge
#5, tag and complete C" (2026-08-28), which is the operator act the task
required — the tag follows the human merge, and no agent tagged on its own
authority.

**§3.8 is PROVEN, not asserted, and the proof is in the consumer:**
openxFactory's `scripts/verify-openxwallet-pin.py` recomputes every digest in
`contracts/openxwallet-pin.yaml` over the realization tree and reports
`8 digest(s) recomputed` at `openXwallet@93b0a47` — **8 of 8 unchanged**. That
is expected and is the shape of an additive minor: the change touches
`scripts/validate-openxwallet.py`, which the pin carries in its
`pinned_by_commit_only:` list, so a reader edit moves the COMMIT and no digest.

## 4. Downstream, gated on §3 merging and the tag (openxFactory)

- [x] 4.1 `contracts/openxwallet-pin.yaml`: `commit` → the release commit,
      `contract_bundle_tag` → the new tag. The eight `files:` digests are
      UNCHANGED (§3.8 is the proof).
- [x] 4.2 `governance/review-authority/register.yaml` gains the four `seat_keys`
      entries with the mint record's exact public halves and fingerprints.
      **[HUMAN-ONLY]** — the register is a permanently human-only surface by
      ratified requirement and by name in gate rules; the pull request IS the
      human act, and no council verdict may clear it.
- [x] 4.3 The consumer gate's positive-proof step gains an assertion on the
      seat-key note, so a green check PROVES the four seats were read. A green
      check that proves nothing was read is the class that step exists to close.
- [x] 4.4 Gitlink and pin move TOGETHER in one commit — never a mixed state.
      (`design.md` D10 makes either ordering green, which is a safety net, not a
      licence to split them.)

### Realization evidence for §4 (openxFactory, merged 2026-08-28)

Landed as **openxFactory PR #475**, merge commit **`0c0075df80737798a03b1d4582300a053fb8195b`**, as a
deliberate TWO-STEP on one branch:

1. `governance/review-authority/register.yaml` gains the `seat_keys` surface
   carrying the four public halves copied verbatim from codexFactory's mint
   record (`78b8fa2`), and the consumer gate's positive-proof step gains the
   seat-key assertion (§4.2, §4.3).
2. `contracts/openxwallet-pin.yaml` `commit` →
   `93b0a47fe9086e65f71ef2916f60a82b2ac4cdca`, `contract_bundle_tag` →
   `wallet-v1.2`, and the `openXwallet` gitlink to the SAME sha in that one
   commit (§4.1, §4.4).

**Step 1 could not land alone, and that is the property, not a caveat.** Its
assertion demands a note only `wallet-v1.2`'s reader emits, so the required
`wallet-validation` check was RED until step 2. The mixed state — four public
keys recorded in a governed file while the pinned reader ignores them, green and
unadjudicated — is structurally impossible rather than merely discouraged.
`verify-openxwallet-pin.py` reads the gitlink from **HEAD** and refuses
`pin-gitlink-mismatch` when pin and tree disagree, so §4.4's "together in one
commit" is enforced by a required check in both directions.

**§4.3's green check PROVES the four seats were read.** From the
`openxwallet-consumer-gate` workflow's own CI log at that head:

```
OK openxwallet-pin verified: openXwallet@93b0a47fe9086e65f71ef2916f60a82b2ac4cdca
   (tag label wallet-v1.2), gitlink read from HEAD, 8 digest(s) recomputed
note  nested repositories pruned (not adjudicated): openXwallet
note  intake register: 4 of 4 per-seat signing key(s) adjudicated and resolved
validate-openxwallet: 0 error(s), 0 warning(s)
```

The assertion greps that line with a **LITERAL `4 of 4`**, not `[0-9]+`, and
also refuses the reader's absent-surface note — so a dropped `seat_keys` block
cannot pass either. The count is over entries that stood behind full
adjudication (the reader excludes refused entries), so it proves adjudication
rather than parsing, which is the class the step exists to close.

**§4.2 stayed human-only in fact as well as in name.** The register is a
permanently human-only surface and a never-clearable floor member; the pull
request WAS the human act, and no council verdict cleared it — nor could the
council whose own commission it records have been eligible to try.

## 5. Downstream, operator (hermes-install and the runtime)

- [x] 5.1 **[OPERATOR]** Re-derive the register projection from the register that
      now carries the keys, and establish it. `design.md` **D11** determines
      that this is CONTENT ONLY: no hermes-install code change and no schema
      change — its projection schema and reader at `cba1a2b` already require and
      recompute per-seat `key_id` / `key_fingerprint` / `public_key`.
      **DONE, proven by a committed artifact.** hermes-install feature 019
      (`register-projection-refresher`), PR #63 merged `6b68c93`, deployed
      2026-08-30 (`docs/evidence/register-projection-refresher-deploy-2026-08-30.md`):
      the migration job `register-projection-migration-202608301523` re-derived
      the projection from openxFactory revision
      `698073f7c06836e860585ac816d98c65de050f9a` — the revision carrying this
      change's `seat_keys` block (landed openxFactory PR #475, 2026-08-28) —
      and recorded `seat_count 4`, `seats_validated` naming all four seats
      (`lead-quality`, `lead-security`, `lead-integration`,
      `company-policy-lead`) under `merge_readiness_council`, and
      `projection_digest sha256:9fe17acd7c5b8175ba973689bb3be8019e6ce3dfca74e5b92eedc0cbf161dc3e`.
      The verification step in the same record states plainly: "All four seats
      resolve at now." The projection is not a one-time act: CronJob
      `hermes-register-projection-refresher` (schedule `0 */2 * * *`) has
      re-established it every two hours since, so it continues to be
      re-derived from the register's live content, including its
      2026-09-02 `row-mrc-0001` repoint (`grant-mrc-0002`).
- [ ] 5.2 **[OPERATOR]** Confirm `review_authority.root_key_mismatch` no longer
      fires for a seat whose key the register now records — the refusal this arc
      is clearing. Steps 4 and 5 of the mint record's successor list (the
      per-target credential and machinery map; a hermes-install image carrying
      the verifying half) remain that record's, not this change's.
      **NOT PROVABLE FROM COMMITTED ARTIFACTS as of 2026-09-06 — left unticked
      on purpose.** hermes-install's own evidence trail says this directly:
      `docs/evidence/wallet-exercise-deploy-2026-08-29.md` records verification
      items "3–7. `root_key_mismatch` cessation, preflight notice, signed seat
      returns, S3 exercise rows, envelope stamp — NOT OBSERVABLE YET:
      codexFactory's `council-deliberation-worker` has failed at workflow level
      … To be observed at the first convening after that fix"; the 2026-08-30
      evidence doc repeats the same items as still blocked; and
      `docs/evidence/verified-subject-pin-deploy-2026-09-03.md` (feature 021,
      2026-09-03) still reads "Not yet observable: a stamped convening — needs
      the first commissioned convening after this deploy." No hermes-install
      commit after 2026-09-03 (last is `9ad76dc`, 2026-09-05, a QA resource
      tune) adds a later observation. The walk this row needs is
      `docs/runbooks/wallet-exercise-deploy-window.md` VERIFICATION step 3 —
      owed to the operator, blocked on a real convening running end to end
      (codexFactory `council-deliberation-worker`). This does not gate this
      change's archive: the code_surface this change declares is openXwallet's
      `validate-openxwallet.py` reader alone, and §5 is downstream-operator
      bookkeeping outside that surface, tracked here so it is not lost.

## 6. Upstream bookkeeping

- [x] 6.1 Record against `add-composition-drift-cascade` that its task 3.4
      (`revocation_staleness_bound` validated by the register reader) is
      discharged by this change, so it is not carried twice or archived as
      outstanding.
- [x] 6.2 Record against openxFactory `add-wallet-carried-review-authority` that
      the per-seat successor its intake requirement NAMED was authored here, on
      the reader side, per the precedent of that change's
      `## Addendum — split-openxwallet-repo P3 (2026-08-27, contract-v2.0)`,
      which moved the wallet deltas' home to this repository (its `tasks.md`
      line 521 records the same handoff for the S5 core deltas).

### Where §6.1 and §6.2 were recorded

- **6.1** — `openspec/changes/add-composition-drift-cascade/tasks.md` task 3.4
  is ticked and annotated DISCHARGED, with its original successor text kept
  unedited as the record of what was found. It is not carried twice.
- **6.2** — openxFactory `openspec/changes/add-wallet-carried-review-authority/tasks.md`
  task **7.3** carries the note, in PR #475 (`0c0075df80737798a03b1d4582300a053fb8195b`): that task's own
  FINDING — the pinned reader accepting a governed top-level declaration
  silently, the vacuous-pass class — is recorded as structurally closed by
  `wallet-v1.2`'s enumerated top level. **7.3 was deliberately left UNTICKED**,
  because its own enforcement half is 7.4's (the hermes-install runtime refusing
  a stale projection) and closing a reader's blind spot is not that.

**§6.3 and §6.4 remain open, and neither is discharged by this wave.** 6.3 is an
edit to codexFactory's mint record (a third repository) saying item 2 of its
successor list is realized and item 3 is unblocked; 6.4 is the archive-time
re-run of the full gate bar. §5.1 and §5.2 keep their `[OPERATOR]` marks — the
Hermes projection re-derivation is content-only (`design.md` D11) but it is the
operator's act, and until it happens `review_authority.root_key_mismatch` has
not yet been observed to stop firing.

**At archive time (2026-09-06, lane `hermes-wallet-exercise`): 6.3 stays
unticked and OWED, on purpose — it is not a record inside this repository.**
It requires an edit to codexFactory's
`hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`,
a third repository this archive does not touch. Recorded here as an obligation
with a named owner rather than folded into this PR: the next session or lane
that edits that record (or Brett Heap directly) should annotate its numbered
successor list — item 2 ("the register successor") realized by this change
(`wallet-v1.2`, openxFactory PR #475), item 3 (the client-tree projection)
unblocked and an operator act (§5.1/§5.2 above). This is a named-successor
bookkeeping row, not part of the `release-realization` code_surface this
proposal declares (openXwallet's reader alone), so it does not gate this
archive.
- [ ] 6.3 Record against codexFactory's mint record that item 2 of its numbered
      successor list ("the register successor") is realized, and that item 3
      (the client-tree projection) is unblocked and is an operator act.
      **OWED — cross-repository, not done here; see note above.**
- [x] 6.4 Record the realization evidence on this change before archiving —
      merged, green — and re-run the full gate bar at archive.

### §6.4 — realization evidence and archive-time gate bar (2026-09-06)

**Realization evidence for the code_surface (`scripts/validate-openxwallet.py`
`check_register` plus self-test probes, tests, and release bookkeeping),
merged and green, per the proposal's `target_release`:**

- Tag `wallet-v1.2` → commit `93b0a47fe9086e65f71ef2916f60a82b2ac4cdca`
  (merge of PR #5, `014-per-seat-register-entries`, 2026-08-28).
- `contracts/CHANGELOG.md` carries the `## wallet-v1.2 — 2026-08-28 (additive
  minor; validator behaviour only)` entry naming this change by name and
  confirming none of the eight digested artifacts moved.
- `contracts/manifest.yaml` reads `contract_bundle_version: wallet-v1.2` at
  that sha (§3.9 realization evidence, above).
- The consumer-side pin at openxFactory `contracts/openxwallet-pin.yaml`
  cites `contract_bundle_tag: wallet-v1.4` at `commit:
  b7b0fbb3e6d614f60a24737c247e45dada9408aa` (read at `origin/main`,
  2026-09-06) — two additive releases past `wallet-v1.2`, so the consumer has
  long since moved onto and past this change's release; it was never rolled
  back.
- Validator self-test lines at this archive's head (2026-09-06, gate bar
  re-run below) confirm the corpus still adjudicates the seat-key surface:
  `wallet 'wal-agent-council-0011': 4 declared key(s) adjudicated`; corpus
  `21 positive example(s), 45 negative confirmation(s) across 13/13
  requirements`.

**The full gate bar, re-run at archive (2026-09-06, HEAD of
`archive/add-per-seat-register-entries` off `origin/main`):**

- `python3 scripts/verify-contract-pin.py` — OK, 1 vendored file matches
  `contract_pin.yaml` at `openxFactory@30565e48ffe3` (bundle `contract-v1.44`).
- `python3 scripts/wallet-yaml-syntax-gate.py .` — exit 0.
- `python3 scripts/validate-openxwallet.py .` — 0 errors, 0 warnings.
- `python3 scripts/validate-openxwallet.py . --strict` — 0 errors, 0
  warnings; corpus 21 positive examples, 45 negative confirmations across
  13/13 requirements.
- `python3 -m pytest tests/ -q` — **96 passed**.
- `OPENSPEC_TELEMETRY=0 openspec validate --all --strict` — **5 passed, 0
  failed** (the three active changes — `add-composition-drift-cascade`,
  `add-multi-key-wallets`, `add-per-seat-register-entries` — plus the two
  promoted specs `openxwallet` and `openxwallet-agent-profile`).

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
  - **THE TRIGGER FIRED 2026-08-28.** openxFactory PR #475 (`0c0075d`) landed
      both halves: its register carries the four `seat_keys` entries AND its
      `contracts/openxwallet-pin.yaml` plus gitlink point at this reader
      (`93b0a47` / `wallet-v1.2`). §4 is complete. So this successor is now
      SAFE to build and is an obligation with its condition met — it is left
      unticked because the flip itself is unbuilt, not because it is still
      blocked. The next additive minor is where it belongs.
- [ ] 7.2 **Attestation strictness.** `_load_attestations` tolerates unknown keys
      in the custody attestations beside the register — the same vacuous-pass
      class, in the same governed directory. Needs the attestation's shape
      ENUMERATED and ratified first, which is why it is not folded in here.
- [x] 7.3 **A wallet record declaring several keys** (`design.md` D9), which would
      make a per-seat key wallet-declared rather than register-declared. A
      contract change to a digested artifact: a bundle version and every
      consumer's pin. TRIGGER, and it has a date on it: hermes-install copies the
      projection's `key_id` verbatim into the exercise record's
      `presenting_key_ref`, so this MUST be answered before any exercise record
      carrying a per-seat key is committed to a tree this validator scans — rule
      (r) refuses a presenting key no wallet declares.
  - **ANSWERED 2026-08-28.** Brett Heap ruled option 1 in session ("rule option 1
      and build it"): one wallet MAY declare several keys as presenters of its
      single authority. Packet `openspec/changes/add-multi-key-wallets/`
      (ratified 2026-08-28, PR #7); realized as `wallet-v1.3` through Speckit
      feature `specs/015-multi-key-wallets/`. Rule (r) now resolves a presenting
      key against the wallet's DECLARED KEY SET, so a `presenting_key_ref`
      naming a per-seat key resolves once openxFactory's
      `wal-agent-mrc-0001` declares those keys — which is that repository's half
      of the same wave. The trigger this line named is discharged; the successor
      it named is built.
- [ ] 7.4 **Roster resolution** (`design.md` D8): resolving a `seat_id` against
      the council definition that governs it. Needs a cross-repository read path
      this validator does not have and should not acquire casually.
