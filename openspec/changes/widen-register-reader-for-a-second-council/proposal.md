---
code_surface: openXwallet `scripts/validate-openxwallet.py` — the register reader (`check_register`'s row-count refusal and `_check_seat_keys`' duplicate table), its own S4 self-test block, `tests/`, `contracts/CHANGELOG.md` and the bookkeeping of a release. NO `contracts/` byte moves and no register schema is authored: the register is deliberately KINDLESS (openxFactory design D11) and this reader IS its shape. Per `release-realization` this change archives only on merged, green realization evidence for that surface — which for this change explicitly includes the openxFactory pin advance it exists to unblock, because a reader release no consumer pins has widened nothing.
target_release: unallocated at proposal. The realization is expected to be an ADDITIVE MINOR (`wallet-v1.5`) whose eight contract digests are UNCHANGED — the same release class as `wallet-v1.4`, where the only line moving in `contracts/manifest.yaml` is `contract_bundle_version` and a consumer's pin bump moves `commit:` and `contract_bundle_tag:` and nothing else. Per AGENTS.md rule 6 the five coordinated values are allocated at realization and nothing is reserved here.
Status: draft
sequenced_before: [openxFactory:register-gate-rules-council-seats]
archive_after: [add-per-seat-register-entries]
---

# Proposal: widen-register-reader-for-a-second-council

Lane: hermes-wallet-exercise

## Why

**A ratified register act cannot be performed, because this repository's reader
refuses its correct outcome. Two defects refuse it, and both were MEASURED
against the pinned reader rather than reasoned about.**

openxFactory's `register-gate-rules-council-seats` — ratified 2026-09-06T14:13:46Z
by Brett Heap and merged as PR #717 → `a59f2ae5` — registers codexFactory's
`gate_rules_council` as the SECOND commissioned body in the intake register.
Its design D5 records the measurement; this proposal reproduces it
independently, at the reader openxFactory pins today
(`b7b0fbb3e6d614f60a24737c247e45dada9408aa`, `wallet-v1.4`) — which is
BYTE-IDENTICAL to `scripts/validate-openxwallet.py` on this repository's `main`
at `05007e26` (`git diff b7b0fbb3 origin/main -- scripts/validate-openxwallet.py`
is empty; the only difference between those two commits is a workflow file).
So the defects are live on `main`, not only at the pin.

The probe: a copy of openxFactory's live `governance/review-authority/` tree
plus `row-grc-0001` (holder `agent:gate-rules-council`), a matching wallet,
grant and custody attestation, and the `gate_rules_council` seat entries. The
reader's own words, on **the full act Brett's walk would carry** — all four
registered seats:

```
note  intake register read: governance/review-authority/register.yaml (2 row(s))
note  intake register: 5 of 8 per-seat signing key(s) adjudicated and resolved
ERROR [register-minimal-shape-exceeded] …/register.yaml: 2 AUTHORITY rows; the
  ratified first shape is exactly ONE holder/target/act row - wider registers
  are a named successor change. …
ERROR [register-seat-duplicate] …:seat_keys[5] (lead-security): seat_id
  'lead-security' is already recorded at seat_keys[1]; a repeated seat_id is
  refused rather than resolved by file order
ERROR [register-seat-duplicate] …:seat_keys[6] (lead-quality): seat_id
  'lead-quality' is already recorded at seat_keys[0]; …
ERROR [register-seat-duplicate] …:seat_keys[7] (company-policy-lead): seat_id
  'company-policy-lead' is already recorded at seat_keys[3]; …
validate-openxwallet: 4 error(s), 0 warning(s)
```

Four errors, and the note says `5 of 8` where the act's own gate (openxFactory
task 2.8) requires `8 of 8`.

**Defect 1 — `REGISTER_MVP_SINGLE_ROW = 1`.** A second body needs a second
AUTHORITY row and cannot descend from the first: `_check_seat_keys` refuses an
entry whose `council_ref` is not the authorizing row's `holder_ref`
(`register-seat-council-mismatch`), and that row's holder is
`agent:merge-readiness-council`. The cap is therefore not a stylistic bound
here; it is the thing that makes a second commissioned body unrepresentable.

**Defect 2 — seat-name uniqueness is GLOBAL, not per council.**
`_check_seat_keys` builds `seen = {"seat_id": {}, "key_id": {},
"key_fingerprint": {}}` across every entry in the file. `gate_rules_council`
seats `lead-security`, `lead-quality` and `company-policy-lead` — three names
`merge_readiness_council` already records — so three of its four seats are
refused as duplicates of a DIFFERENT body's seats. **This defect is invisible
with one council and fires the moment a second arrives**, which is the same
shape as the `wallet-v1.4` defect: invisible until the first re-issuance, found
by the act that performed it.

`key_id` and `key_fingerprint` uniqueness are CORRECT as global — a key is one
key, and two bodies presenting it are two claims on one identity — and are not
relaxed with `seat_id`.

## What Changes

One capability, `review-authority-register-reader` (this repository's own, added
by the sibling change `add-per-seat-register-entries`): **one RENAMED + two
MODIFIED requirements, and two ADDED.**

- **The scalar row cap is replaced by the invariants it stood in for**, per the
  Q-GRC-5 ruling verbatim: every authority row resolves end to end; every seat
  entry attaches to a row that commissions its body; (`council_id`, `seat_id`)
  is unique. `REGISTER_MVP_SINGLE_ROW` is RETIRED — not raised to 2. Two is as
  arbitrary as one, buys exactly one body of headroom, and would have to be
  edited again by the third body while saying nothing true about why two is
  right.
- **Seat identity becomes the PAIR (`council_id`, `seat_id`).** The duplicate
  table is re-keyed on the pair; a seat name repeated under ONE council stays
  refused with the SAME code, `register-seat-duplicate`. `key_id` and
  `key_fingerprint` stay globally unique.
- **`register-minimal-shape-exceeded` is RETIRED BY NAME, never re-scoped**
  (design D5). A finding code is pinned by string by live consumers (AGENTS.md
  rule 2); keeping the string alive over a different invariant would make a
  pinned code lie, which is worse than removing it. Measured: the only
  citations of that code in the estate are this repository's own validator and
  one openxFactory Speckit document — no consumer test pins it, and
  openxFactory's consumer gate matches `register-*` findings by WILDCARD, so
  the retirement breaks no green check.
- **The reader's own S4 self-test carries the multi-body probes**, so a later
  edit cannot silence an invariant while the self-test stays green — the same
  discipline the self-test block already applies to every other register
  invariant.

**No new finding code is added.** Every refusal this change keeps already
exists by name; the one it retires is measured as unpinned. Additive-only is
not a courtesy here: AGENTS.md rule 2 makes a rename a breaking change.

## What this change does NOT do

- **It does not write the register.** `governance/review-authority/register.yaml`
  is openxFactory's file, a permanently human-only surface by ratified
  requirement, and every write to it is Brett's operator act
  (openxFactory tasks §3). This change makes the correct act representable and
  performs none of it.
- **It does not move the register's path or its floor entry.** codexFactory's
  gate rules pin the EXACT path as a never-clearable floor member and refuse
  wildcards. The register FILE does not move; only the reader widens.
- **It does not raise the cap.** See above; Q-GRC-5 rules the invariants.
- **It does not relax `key_id` or `key_fingerprint` uniqueness.**
- **It does not author a register schema.** openxFactory design D11 stands: the
  rule-of-three has not fired and the reader is still the shape.
- **It does not touch `contracts/`.** No digested artifact moves, so the
  expected release is the `wallet-v1.4` class — a reader-only bundle.
- **It does not advance any consumer's pin.** openxFactory tasks 2.7–2.9 do
  that, in one pull request with the consumer gate's literal assertions, and
  they are named here as owed acts with their owner.
- **It does not add a per-body staleness bound.** One projection has one age
  (openxFactory design D7); `revocation_staleness_bound` stays file-level and
  this change does not touch that line.

## What this pull request carries, and what waits for ratification

| | This PR | After ratification |
|---|---|---|
| The proposal, design, spec delta, tasks | yes | — |
| The RED tests (openxFactory row 2.2) | **yes** — authoring tests is not blocked | — |
| The reader fixes (rows 2.3, 2.4) | **no** | yes |
| The self-test extension (row 2.5) | no | yes |
| The bundle tag and manifest digests (row 2.6) | no | at the cut |
| openxFactory's pin advance and gate literals (rows 2.7–2.9) | no | that repository's act |

The red tests are the evidence this proposal is about a real defect and not a
reading of one: they FAIL today with exactly the two codes above, and the fix
slice flips them.

## Impact

- **openxFactory** — this change is the hard prerequisite of its ratified
  register act. Its `contracts/openxwallet-pin.yaml` advances `commit:` and
  `contract_bundle_tag:` ONLY; no `files:` digest row moves, because
  `scripts/validate-openxwallet.py` sits under `pinned_by_commit_only:` and a
  reader-only release moves no contract byte. Its consumer gate's LITERAL
  assertions (`4 of 4 per-seat signing key(s)…` → `8 of 8`, plus a new one for
  the second wallet's declared keys) move in the same pull request as the pin,
  and its own task 2.9 requires the pin advance to be provably NEUTRAL — the
  register still at one row, `wallet-validation` green, the note still reading
  `1 row(s)` — before the register moves. **This change is designed to make
  that neutrality true**: with one row and one council in the file, the widened
  reader emits exactly what the pinned one does (design D6).
- **codexFactory** — nothing. Its floor pins the register by exact path and the
  path does not move.
- **hermes-install** — nothing, checked rather than assumed:
  `derive_projection` already keys its duplicate table on
  `(council_id, seat_id)` and already reports `councils` as a sorted set. The
  runtime side is already multi-body capable; only the reader was not. **The
  fix adopts the key the runtime already uses**, which is the strongest
  available evidence for its shape.
- **LedgerxWallet and the other descendants** — nothing. No profile expresses a
  register; openxFactory is the only repository in the estate that carries one.
- **Every consumer running `--strict`** — nothing new is a warning. Notes and
  errors only, as `wallet-v1.2` established for the same reason: `report()`
  reds a `--strict` run on warnings, so a new warning would red-line a required
  check in a repository that never asked for it.

## Overlap with `add-per-seat-register-entries` — stated, because it is direct

**The sibling change is RATIFIED (2026-08-28), REALIZED as `wallet-v1.2`, and
NOT ARCHIVED.** Its delta is the only place the capability
`review-authority-register-reader` exists — it is absent from
`openspec/specs/` — and its third requirement is the one this change amends. In
its own words:

> Recording per-seat keys SHALL NOT be read as widening the register's holder,
> target or act breadth, **and a second authority row SHALL still be refused.**
>
> #### Scenario: A second authority row is still refused

**There is no door in that sentence.** openxFactory's own intake requirement
left one — its first-shape scenario says the wider scope is "a named successor"
— and openxFactory #717 walked through it with seven ADDED requirements and no
MODIFIED block. This repository's requirement is narrower and more explicit: it
says the refusal STANDS. So the honest instrument here is an amendment, not an
arrival beside it, and this change carries a `## MODIFIED Requirements` block
and a `## RENAMED Requirements` entry rather than pretending the sibling's
sentence permits what it forbids.

**Two convergence obligations follow, and the first is MEASURED, not inferred:**

1. **`add-per-seat-register-entries` MUST archive BEFORE this change.** Measured
   on openspec 1.2.0: a MODIFIED delta whose target spec does not exist aborts
   the archive with *"target spec does not exist; only ADDED requirements are
   allowed for new specs. MODIFIED and RENAMED operations require an existing
   spec."* Validation (`--strict`) passes either way; only the archive is
   ordered. This is a task in §5, not a hope.
2. **The MODIFIED text reproduces the sibling's requirement and changes it
   minimally**, so a reader of the promoted spec can see what moved. The
   surviving half of that requirement — the key surface takes no COUNT bound
   and is bounded STRUCTURALLY, every entry descending from a row in this same
   file — is not merely kept: it is promoted to one of the three invariants
   that replace the cap.

**A pre-existing instance of the same collision is recorded here because this
change is the one that found it, and it is NOT fixed here.**
`add-composition-drift-cascade` and `add-multi-key-wallets` both carry
`## MODIFIED Requirements` blocks for `### Requirement: Revocation propagates
through the chain` in the `openxwallet` capability, and the two texts are NOT
byte-identical (3353 vs 1387 characters). Whichever archives second overwrites
the first's amendment silently, because openspec replaces the requirement body
wholesale. openXwallet has no convergence device for this — no
`sequenced_after:` ledger and no restatement convention, unlike openxFactory,
which carries both plus a test suite over the ledger. Open question Q-WRR-4
names it with a recommendation; this change declares its OWN archive order in
front-matter (`archive_after:`) and in §5 rather than leaving a third instance
undeclared.

## Open questions

Each carries a recommendation. None is decided here.

### Q-WRR-1 — Is `register-minimal-shape-exceeded` retired, or re-scoped?

Q-GRC-5 rules the cap replaced by invariants but does not say what becomes of
the CODE. Retiring it means a string that live consumers may pin stops being
emitted; re-scoping it means the same string means something new.

**Recommendation: RETIRE it by name, and record the retirement in
`contracts/CHANGELOG.md` as a REMOVED refusal at the cut.** Measured ground:
the only citations of the code anywhere in the estate are this repository's
validator (the emitter plus its own self-test probe) and openxFactory
`specs/014-register-and-reader/data-model.md` — a Speckit document, not a test.
openxFactory's consumer gate asserts on the WILDCARD `\[register-[a-z-]+\]`, so
no literal breaks; LedgerxFactory's estate suite does not pin it. Re-scoping is
refused on principle: AGENTS.md rule 2 exists because consumers pin codes BY
NAME, and a code whose meaning changes under a stable string is a worse
compatibility break than one that disappears, because nothing fails to warn
anybody.

### Q-WRR-2 — Does a widened reader need a positive BOUND at all?

Retiring the cap leaves no numeric limit on authority rows. A register with
fifty rows would be admitted if all fifty resolved end to end.

**Recommendation: no numeric bound, and say why in the spec text.** Every row
must resolve to its own wallet, grant, custody attestation and unexpired
computed expiry, and every seat entry must attach to a row that commissions its
body — so breadth is bounded by what an operator can actually stand behind on a
permanently human-only surface, one governed act at a time. A number here would
be the same artifact the cap already was: it would go stale on the day a body
arrived, and it would say nothing true about why that number was right. This is
the same reasoning `add-per-seat-register-entries` used to leave the key surface
unbounded by count, applied one level up.

### Q-WRR-3 — Does the absent-seat-surface NOTE become a refusal now?

`add-per-seat-register-entries` task 7.1 declares "the absence flip" as a named
successor whose TRIGGER FIRED on 2026-08-28: the register carries seat keys and
openxFactory's pin points at that reader, so the flip is safe to build and
belongs in "the next additive minor". This change is a candidate for being that
minor.

**Recommendation: NOT in this change, and say so explicitly rather than
letting it ride.** The flip is a REFUSAL on a permanently human-only surface,
and this change is the prerequisite of an act that is about to add a second body
and four more keys to that surface. Landing the flip in the same release would
mean that any ordering slip in openxFactory's own §2/§3 sequence parks a
candidate on a file only Brett can edit — the exact shape both changes exist to
end. It is a one-line change to `_check_seat_keys` and it deserves its own
release, after the register act has landed and settled.

### Q-WRR-4 — openXwallet has no sibling-delta convergence device. Should it?

Three active changes now carry MODIFIED blocks in this repository and two of
them collide on one requirement (see the overlap section). openxFactory solves
this with `sequenced_after:` front-matter, a corpus ledger
(`tests/sequenced_after/corpus-ledger.yaml`) and a test suite over it.

**Recommendation: adopt the minimum — a declared archive order in front-matter,
which this change uses (`archive_after:`) — and open a separate change for the
ledger if a fourth collision arrives.** Building openxFactory's full device
here on the strength of two instances would be tooling ahead of the rule of
three, and this change should not carry a corpus-governance decision it merely
noticed. What it must not do is add a third undeclared instance, and it does
not.

### Q-WRR-5 — The change id, and a citation that must resolve

The orchestrating brief named this change `widen-register-reader-to-multiple-bodies`
(the branch carries that name); openxFactory's ratified packet names it
`widen-register-reader-for-a-second-council` in FOUR committed places —
`proposal.md`'s `sequenced_after:`, `tasks.md` row 2.1, `README.md`, and
`tests/sequenced_after/corpus-ledger.yaml`, which a 162-test suite reads.
**The id here follows the ratified citation**, so nothing dangles.

**Recommendation: keep this id.** The substance is wider than the id says —
Q-GRC-5's invariants admit N bodies, not a second one — and if a rename is
wanted for accuracy, it is one openxFactory bookkeeping edit across those four
places plus this directory, taken deliberately and not as a side effect of a
branch name. Recorded as §5 follow-on, owner the arc owner of
`register-gate-rules-council-seats`.

## Council or not — the call, stated

**No council convening is sought, and it is a call rather than an omission** —
the same three reasons `add-per-seat-register-entries` recorded, and one more
that is sharper here:

1. openXwallet hosts no council machinery. Councils, seats, verdicts and the
   `deliberate` job live in codexFactory; this repository has three required
   checks and a human merge gate.
2. The body whose registration this reader unblocks is `gate_rules_council` —
   the body that SETS codexFactory's gate rules, including the never-clearable
   floor that names this repository's own pin. openxFactory design D6 rules
   that a candidate touching the register or the pin selecting its reader is
   cleared by the OPERATOR ONLY: not by that council, and not by
   merge-readiness either, since both bodies now hold authority conferred by
   the same file.
3. The seats this change makes registrable have never been exercised — the
   roster says the missing piece is a caller — so no convening could review
   this change with verifiable seat authority even if it were eligible. That is
   the circularity the whole arc exists to break.

What replaces it is the measurement, the red tests, and Brett's ratification.
