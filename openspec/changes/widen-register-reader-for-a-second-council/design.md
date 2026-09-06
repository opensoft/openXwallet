# Design: widen-register-reader-for-a-second-council

Lane: hermes-wallet-exercise

Six decisions, each with the alternative it rejects. Every number in D0 and D6
was MEASURED at the reader under discussion, not quoted from the change that
asked for this one; §D0 records the commands and the reader's own output.

## Context

`add-per-seat-register-entries` (ratified 2026-08-28, released `wallet-v1.2`)
built the per-seat key surface for ONE body — codexFactory's
`merge_readiness_council` — and RE-GROUNDED the register's single-row cap so
its refusal says the cap binds AUTHORITY ROWS. That was the right call then:
four keys under one row add no holder, no target repository and no act, so
recording them completed the first shape rather than exceeding it. The cap was
kept because nothing needed a second row.

**Something needs one now.** openxFactory's `register-gate-rules-council-seats`
— ratified 2026-09-06T14:13:46Z, merged as PR #717 → `a59f2ae5` — commissions
`gate_rules_council` over the same repository, and its design D2 shows the
second body cannot descend from the first row: `_check_seat_keys` refuses an
entry whose `council_ref` is not the authorizing row's `holder_ref`, and that
row's holder is `agent:merge-readiness-council`. Attaching gate-rules seats to
`row-mrc-0001` would not merely be untidy; it would RECORD the gate-rules seats
as descending from the merge-readiness council's authority, which is false.

So this change is the arrival of the second body, seen from the reader's side.
Almost everything it finds is a consequence of that: the reader was written
correctly for one holder, and the second one exposes where "one" was written
into the machinery rather than into the policy.

## D0 — The measurement, and it was re-run here

**Both defects are live on this repository's `main`, not only at the pin.**
`scripts/validate-openxwallet.py` at `origin/main` (`05007e26`) is
BYTE-IDENTICAL to the pinned reader
(`b7b0fbb3e6d614f60a24737c247e45dada9408aa`, `wallet-v1.4`):

```sh
git diff b7b0fbb3e6d614f60a24737c247e45dada9408aa origin/main \
  -- scripts/validate-openxwallet.py      # empty
```

The only difference between those two commits anywhere is
`.github/workflows/lane-line.yml`. So the tests in this change measure the
pinned reader by measuring `main`, and no checkout of an old commit is needed
to reproduce them.

**The probe.** A copy of openxFactory's live `governance/review-authority/`
tree at `origin/main`, plus `row-grc-0001` (holder `agent:gate-rules-council`,
`grant_ref: grant-grc-0001`, `expires_at: 2027-06-30T00:00:00Z`), a matching
wallet record, root grant and custody attestation, and the
`gate_rules_council` seat entries — `lead-architect`, `lead-security`,
`lead-quality`, `company-policy-lead`, the four seats openxFactory design D1
registers. The seat keys in the probe are DETERMINISTIC SYNTHETIC keys whose
fingerprints recompute: no gate-rules key exists yet, because minting them is
Brett's operator act (openxFactory task 3.2), and inventing a real-looking one
would put a value in this repository that no ceremony produced.

```sh
python3 scripts/validate-openxwallet.py <probe-tree>
```

**The full act — all four registered seats:**

```
note  intake register read: governance/review-authority/register.yaml (2 row(s))
note  intake register: 5 of 8 per-seat signing key(s) adjudicated and resolved
ERROR [register-minimal-shape-exceeded] …: 2 AUTHORITY rows; the ratified first
  shape is exactly ONE holder/target/act row - wider registers are a named
  successor change. …
ERROR [register-seat-duplicate] …:seat_keys[5] (lead-security): seat_id
  'lead-security' is already recorded at seat_keys[1]; …
ERROR [register-seat-duplicate] …:seat_keys[6] (lead-quality): seat_id
  'lead-quality' is already recorded at seat_keys[0]; …
ERROR [register-seat-duplicate] …:seat_keys[7] (company-policy-lead): seat_id
  'company-policy-lead' is already recorded at seat_keys[3]; …
validate-openxwallet: 4 error(s), 0 warning(s)
```

**Four errors, and the ADJUDICATED note reads `5 of 8`.** openxFactory task 2.8
requires that line to read `8 of 8` after the fix and moves its consumer gate's
literal assertion to match, so the note is not decoration: it is the positive
proof the consuming gate asserts on, and it is wrong by three today.

**Two readings of the number, and only one of them is safe.** Three entries are
refused, so `read < recorded` and the run is red — which is the surface working
as designed. But `lead-architect` (`seat_keys[4]`) IS adjudicated: it is the one
gate-rules seat whose name no other body seats. So a register carrying a second
body today does not fail closed uniformly; it fails per-entry, admitting the
seats that happen not to collide. That is another reason the pair is the right
key: with global seat names, which of a body's seats resolve depends on what a
DIFFERENT body happens to be called.

**Difference from openxFactory design D5, stated so the two records agree.**
That design's probe carried TWO gate-rules entries and reported `4 of 6`; this
one carries the full four and reports `5 of 8`. Both refuse with the same two
codes; the counts differ because D5's two entries were both colliding names
while this probe includes `lead-architect`, which is not. Neither number is
wrong — they measure different probes — and the FULL-ACT number is the one the
fix must move, because the act Brett performs registers four seats.

## D1 — N authority rows, one per commissioned body, each resolving end to end

**Decision.** The register carries one AUTHORITY ROW per commissioned body,
with no numeric bound on how many bodies it may commission. A row is admitted
on the strength of what it RESOLVES TO, not on its ordinal position in the
file: its own wallet record (scanned, `state: active`), its own grant (whose
audience, acts, objects, tier and `expires_at` match the row
character-for-character), its own custody attestation if the row stands at tier
`act`, and a COMPUTED expiry in the future — the checks `check_register`'s row
loop already performs on every row it reads.

**Ground.** The cap was standing in for those checks, at a time when there was
exactly one row and the checks could not distinguish "the first shape" from
"the only row". Q-GRC-5 rules the substitution explicit: *"replace the scalar
cap with the invariants it stood in for — every row resolves end to end, every
seat entry attaches to a row that commissions its body, and (`council_id`,
`seat_id`) is unique."* The row loop is already written to run over a list; it
was never the part that refused a second row.

**Alternative rejected: raise the cap to 2.** openxFactory design D5 rejects it
and Q-GRC-5 rules against it. Two is as arbitrary as one, buys exactly one body
of headroom, and would have to be edited again by the third body — which means
the reader would refuse a correct governed act a second time, for the second
time. The version of this argument that matters is not economy: a number in the
reader is a claim about how many bodies the ESTATE may commission, and this
reader has no standing to make that claim. What it has standing to check is
whether each row stands up.

**Alternative rejected: no bound and no invariant restatement — just delete the
constant.** That would leave the promoted requirement saying the cap "SHALL
remain enforced" while the code enforced nothing, which is the vacuous-pass
class `add-per-seat-register-entries` exists to close, inverted. The spec text
moves in the same change as the constant.

## D2 — Seat identity is the pair, and the duplicate table is re-keyed

**Decision.** `_check_seat_keys`' duplicate table keys `seat_id` on the PAIR
(`council_id`, `seat_id`). `key_id` and `key_fingerprint` stay GLOBAL. A seat
name repeated under ONE council is still refused, with the SAME code —
`register-seat-duplicate` — and the message names the council so the refusal
says which body has two answers to "which key is this seat's root".

**Ground, and it is not this repository's invention.** hermes-install's
`derive_projection` (`src/hermes_install/review_authority/derivation.py`) keys
its duplicate table on `(council_id, seat_id)` and refuses only *"the register
projects `<council>/<seat>` more than once"*. The runtime that CONSUMES this
register already uses the pair; the reader that guards it does not. **The fix
adopts the key the consumer already uses**, which is the strongest available
evidence for its shape — and it removes a disagreement between two programs
that read one file, rather than inventing a third opinion.

**Why `key_id` and `key_fingerprint` must NOT move with it.** A key is one key.
Two entries sharing a fingerprint are two claims on one identity, and if they
sit under different councils the claim is worse, not better: it would mean one
private half signs for two bodies, and a seat return could not be attributed.
openxFactory task 2.3 says this in terms — *"Leave `key_id` and
`key_fingerprint` uniqueness GLOBAL"* — and openxFactory task 3.7 namespaces
the gate-rules key ids (`key-grc-seat-<seat>-0001`) precisely because that
uniqueness stays global.

**Alternative rejected: key on (`council_ref`, `seat_id`).** `council_ref` and
`council_id` are two spellings of one body and the reader already checks they
denote one (`register-seat-council-spelling`), so either would work today. The
pair uses `council_id` because that is the spelling projected VERBATIM into the
runtime, and the runtime's own table is keyed on it. Keying the reader on the
register-side spelling would make the two programs agree by coincidence rather
than by construction.

**Alternative rejected: refuse a repeated seat name across councils with a
WARNING instead of admitting it.** A warning reds a `--strict` run — every
consumer runs `--strict` — so this is a refusal wearing a softer word, and it
would refuse the correct act. Three of gate-rules' four seats reuse
merge-readiness names because two bodies genuinely seat the same ROLE; that is
normal and the register must represent it.

## D3 — The scalar cap is replaced by three invariants, not by a bigger scalar

**Decision.** `REGISTER_MVP_SINGLE_ROW` is REMOVED and the row-count refusal
with it. What stands in its place is the conjunction Q-GRC-5 names, all three
of which the reader already enforces or is fixed here to enforce:

| Invariant | Where it lives after this change |
|---|---|
| Every AUTHORITY ROW resolves end to end | `check_register`'s row loop — wallet, grant, tier attestation, computed expiry (unchanged) |
| Every seat entry attaches to a row that COMMISSIONS ITS BODY | `_check_seat_keys` — `register-seat-row-unresolved` and `register-seat-council-mismatch` (unchanged) |
| (`council_id`, `seat_id`) is unique | `_check_seat_keys`' duplicate table, re-keyed (D2) |

**Ground.** Two of the three are already in the reader and were always the real
guard; the cap was a proxy for them written when one row made the proxy
indistinguishable from the thing. Naming them is what makes the widening a
DECISION rather than a relaxation — a reader that simply stopped counting rows
would admit a second body and also admit a second body whose grant belongs to
the first.

**Why no numeric bound replaces it (Q-WRR-2).** The register is a permanently
human-only surface: every row is one operator act, on a file whose exact path is
a never-clearable floor member. Breadth is bounded by what a human can stand
behind, one governed act at a time. A number here would go stale on the day a
body arrived and would say nothing true about why that number was right — the
same reasoning `add-per-seat-register-entries` used to leave the KEY surface
unbounded by count, applied one level up. This is stated in the spec text, so
the absence of a bound is a declared decision rather than an omission a later
reader must guess at.

## D4 — What the reader's own S4 self-test gains

**Decision.** The self-test block gains probes for the two-row and two-council
shapes, and RETIRES its `self-test/register-minimal-shape-exceeded` probe. Four
probes, at the same altitude as the existing ones:

1. `self-test/register-two-bodies-clean` — two rows, each resolving to its own
   wallet, grant and attestation, plus seat entries under both councils:
   expected CLEAN.
2. `self-test/register-two-councils-one-seat-name` — the same `seat_id` under
   two different `council_id`s: expected CLEAN.
3. `self-test/register-seat-duplicate-within-one-council` — the same `seat_id`
   twice under ONE `council_id`: expected `register-seat-duplicate`.
4. `self-test/register-second-row-unresolved` — two rows where the second's
   grant does not back it: expected `register-grant-mismatch`, proving the
   widening did not become a relaxation.

**Ground.** The self-test block's own comment states its purpose: *"the live
register proves the happy path, and these synthetic probes pin the invariants,
so a later edit cannot silence an invariant while the self-test stays green."*
The invariants that replace the cap are exactly the ones a later edit could
silence, because after this change nothing counts rows — so a reader that
stopped resolving them would be green on a two-row register that resolves to
nothing. Probe 4 is the one that makes the other three safe.

**Why it lives in the SELF-TEST and not only in `tests/`.** Every consumer runs
the pinned validator; nobody runs this repository's `tests/`. A defect that
`tests/` catches is caught in openXwallet's own pull request; a defect the
self-test catches is caught inside the REQUIRED check of every repository that
pins openXwallet. The multi-body invariants belong in the second class — they
guard a governed file on a human-only surface.

**Alternative rejected: `tests/` only, since the fix is small.** The same
argument would have applied to every existing register probe, and the block
exists because it was not accepted then.

## D5 — Refusal codes: one retired by name, one kept and re-keyed

**Decision, stated per code.**

**`register-seat-duplicate` — KEPT, same string, narrower trigger.** It still
refuses a repeated `seat_id`, now within one council rather than across the
file, and it still refuses a repeated `key_id` or `key_fingerprint` globally.
The code's MEANING is unchanged — "this register has two answers to a question
that has one" — so the string keeps saying something true. Its message gains
the council so the refusal is self-explaining.

**`register-minimal-shape-exceeded` — RETIRED BY NAME, never re-scoped.** The
constant goes, the refusal goes, and no invariant inherits the string.

**Why retirement and not re-scoping.** AGENTS.md rule 2: *"finding codes and
filenames are pinned BY NAME by live consumers. Renaming one is a breaking
change with a migration note, never a tidy-up."* The rule protects consumers
from a string that stops existing. It protects them EVEN MORE from a string
that keeps existing and means something else — the first breaks a pinned
assertion loudly, the second passes it while adjudicating a different fact.
There is also nothing left for the string to mean: each of the three
replacement invariants already has its own precise code
(`register-wallet-unresolved`, `register-grant-mismatch`,
`register-tier-act-unattested`, `register-row-expired`,
`register-seat-row-unresolved`, `register-seat-council-mismatch`,
`register-seat-duplicate`), and re-pointing a retired code at one of them would
give that fact two names.

**The retirement is MEASURED as safe, not assumed.** Every citation of
`register-minimal-shape-exceeded` or `REGISTER_MVP_SINGLE_ROW` in the workspace:

| Where | What it is | Effect of retirement |
|---|---|---|
| openXwallet `scripts/validate-openxwallet.py` | the emitter, the constant, and the self-test probe | removed by this change (rows 2.4, 2.5) |
| openxFactory `specs/014-register-and-reader/data-model.md` | a Speckit design document | a stale sentence in a realized feature's design; §5 follow-on, owner openxFactory |

Nothing else in openxFactory, codexFactory, LedgerxFactory, MedxFactory,
OpsxFactory, AdxFactory, hermes-install or omnigent-install cites either name.
openxFactory's consumer gate asserts `! grep -qE '\[register-[a-z-]+\]'` — a
WILDCARD over register findings, not a literal — so it is unaffected in both
directions. **A migration note still travels with the retirement** in
`contracts/CHANGELOG.md` at the cut, because "measured unpinned today" is not
the same as "nobody may have pinned it", and the note costs one paragraph.

**Alternative rejected: keep emitting it as a WARNING for one release.** Every
consumer runs `--strict`, where a warning reds the run. A deprecation warning
here is a refusal with a gentler name, and it would refuse exactly the act this
change exists to admit.

## D6 — Compatibility: today's register validates identically before and after

**Decision.** The one-row register openxFactory carries TODAY must produce
BYTE-IDENTICAL reader output before and after this change — the same notes, the
same absence of findings, the same exit code — and that is asserted by a test
that passes today (the regression test) rather than claimed in prose.

**The measured baseline**, at the pinned reader, over openxFactory's live
`governance/review-authority/` tree at `origin/main`:

```
note  intake register read: governance/review-authority/register.yaml (1 row(s))
note  intake register: 4 of 4 per-seat signing key(s) adjudicated and resolved
validate-openxwallet: 0 error(s), 0 warning(s)     # rc=0, and rc=0 under --strict
```

**Why this is load-bearing and not hygiene.** openxFactory task 2.9 is a GATE
on the pin advance: *"with 2.7 + 2.8 landed and the register still carrying ONE
row, `wallet-validation` is GREEN and the log's `intake register read:` note
still says `1 row(s)`. The pin advance must be provably neutral BEFORE the
register moves."* If the widened reader changed ANY line of that output, the
pin advance would not be neutral and the sequence openxFactory ratified — pin
first, register second — would have no valid ordering. The neutrality is
therefore a REQUIREMENT of this change, not a property it hopes to have.

**What guarantees it.** The row-count refusal is the only thing being removed
from a path a one-row register traverses, and it never fired at one row. The
duplicate table's re-key changes which COLLISIONS are refused, and a register
with one council has none. Nothing else in `check_register` or
`_check_seat_keys` is touched. `4 of 4` stays `4 of 4` because the adjudicated
count is per-entry and no entry's adjudication changes.

**Alternative rejected: fold the "absence flip" (`add-per-seat-register-entries`
task 7.1) into this release, since its trigger has fired.** It would break this
decision: a register with no seat surface goes from a NOTE to a REFUSAL, so the
release would no longer be neutral for a consumer that has not recorded keys.
Q-WRR-3 records the recommendation to keep it separate and why.

## What this design does not decide

- **Whether the register gets a schema.** openxFactory design D11 stands: the
  rule-of-three has not fired and this reader is the shape. This change makes
  the shape wider and keeps it strict.
- **Whether a seat name may be resolved against a council's roster.**
  `add-per-seat-register-entries` design D8 names roster resolution as a
  successor needing a cross-repository read path this validator does not have
  and must not acquire casually. The pair key is not a substitute for it: the
  reader still cannot say "that seat does not exist", only "that entry is not
  attached to a body this register commissions".
- **Anything about the projection, the mint, or the first signed convening.**
  Those are openxFactory's §3, hermes-install's §4 and codexFactory's §4 in the
  ratified packet, with owners, and none of them is this change's to perform.
