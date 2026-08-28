# Design: add-per-seat-register-entries

## Context

The register is one file: openxFactory `governance/review-authority/register.yaml`.
It is DELIBERATELY KINDLESS — openxFactory's `add-wallet-carried-review-authority`
design **D11** rules its schema a declared successor until the rule-of-three
fires, so `check_register` in `scripts/validate-openxwallet.py` IS the shape. It
runs inside the REQUIRED `wallet-validation` check of openxFactory's
`openxwallet-consumer-gate.yml`, at the pinned invocation
`python3 openXwallet/scripts/validate-openxwallet.py .`.

Today the reader:

- takes each row's field set as EXACT SET EQUALITY against nine names
  (`REGISTER_ROW_FIELDS`);
- caps the file at one row (`REGISTER_MVP_SINGLE_ROW = 1`);
- reads exactly two top-level keys, `register_version` and `rows`, and IGNORES
  every other one.

Three consequences, all of them the same defect wearing different clothes:

1. A key field on a row is refused, so the four minted seat keys cannot go there.
2. Four per-seat rows are refused, so they cannot go there either.
3. A new top-level block would be ACCEPTED — silently, unread. Which is why the
   mint record refused to write one: "A new unread top-level block would pass the
   reader only because the reader ignores what it does not read, which is not the
   same as being recorded."

And there is already a live instance of (3) in the file:
`revocation_staleness_bound: P7D`, added by openxFactory task 7.3, governed,
carried verbatim into hermes-install's projection — and unread by the check that
gates it.

## D1 — A per-seat KEY surface, not per-seat rows (the load-bearing decision)

**Decision.** Add a top-level `seat_keys:` list. Keep `rows:` as the authority
surface and keep `REGISTER_MVP_SINGLE_ROW = 1` over it.

**Ground.** The mint record names both exits — "row-set semantics, or a per-seat
key surface" — and the facts pick the second. All four seats share ONE holder
(`agent:merge-readiness-council`), one wallet (`wal-agent-mrc-0001`), one grant
(`grant-mrc-0001`), one target repository (`opensoft/openxFactory`), one act
(`review`), one tier (`act`) and one expiry (`2026-11-23T12:00:00Z`). The only
per-seat fact is the signing key. Four rows would repeat six identical values
four times to vary one, and would then need the cap raised — admitting breadth
that openxFactory's ratified intake requirement still calls a successor:

> **WHEN** a first-shape register declares more than one holder, more than one
> target repository, or per-seat GRANTS **THEN** the additional scope is a named
> successor rather than part of the first shape.

A key is not a grant. Recording four keys under one row conveys no additional
holder, repository or act, so the first shape is not exceeded — it is completed.

**Rejected: raise the cap to four.** It buys nothing and spends the one sentence
in the ratified spec that keeps register breadth honest. **Rejected: a
`seat_keys` map keyed by seat id.** A mapping makes the duplicate-seat refusal
unexpressible — YAML resolves the collision before the reader sees it — and the
duplicate refusal is one the brief for this work named explicitly. A LIST of
entries each naming its seat is what lets "recorded twice" be a finding.

## D2 — The register carries the public key AND the fingerprint, and the reader recomputes

**Decision.** Each entry carries both `public_key` (32 raw bytes as unpadded
base64url, 43 characters) and `key_fingerprint` (`sha256:<64 hex>`), and the
reader RECOMPUTES the second from the first.

**Ground.** Two reasons that point the same way.

*Downstream.* hermes-install's projection schema requires per-seat `public_key`
AND `key_fingerprint`, and its reader recomputes and refuses a row that
disagrees with itself ("Two spellings of one row's identity mean one of them is
wrong, and picking either is choosing which authority to believe"). If the
register carried only the fingerprint, the operator would have to source the
public key from somewhere else to build the projection — and a second source for
one fact is drift with a delay. Carrying both makes the register the SINGLE
source a projection is derived from.

*Locally.* The recomputation is a check no schema can state, and it is the only
check available here that touches the key material itself. The reader cannot
verify a signature, cannot reach a key store and cannot know a private half
exists; it CAN prove that a register's two spellings of one key agree. That is
the honest maximum at this altitude and it catches the realistic error — a
transcription slip while copying four rows out of a record by hand.

## D3 — The whole top level becomes a closed read set

**Decision.** Enumerate the top-level keys — `register_version`,
`revocation_staleness_bound`, `rows`, `seat_keys` — and refuse an unrecognized
one. `seat_keys` is optional (D10); the other three are required.

**Ground.** Closing the set is what makes the vacuous-pass class structurally
impossible rather than fixed once. Validating `revocation_staleness_bound`
field-by-field closes today's instance and leaves tomorrow's open: the next
governed declaration added to this file would pass unread exactly as that one
did. A closed set means the next such addition CANNOT be made without a reader
edit, which is the same discipline `REGISTER_ROW_FIELDS` already imposes one
level down. The register has no schema; the closure is the reader's job or it is
nobody's.

This is also the openxFactory parent change's design risk **R3** (the
vacuous-pass class) being retired for this file rather than mitigated.

## D4 — The staleness bound's grammar is hermes-install's, deliberately

**Decision.** Accept `P<n>W` or `P<n>D` with an optional `T<n>H<n>M<n>S` part;
refuse years and months; refuse a `T` with no components; refuse a zero-length
window.

**Ground.** This value is projected VERBATIM into hermes-install's projection as
`projected_from.staleness_bound`, where the schema's pattern is
`^P(\d+W|(\d+D)?(T(\d+H)?(\d+M)?(\d+S)?)?)$` with `minLength: 3`, and the
runtime reader is a second gate on it. Accepting here what the runtime refuses
downstream would let an operator commit a governed value that no projection can
ever carry — a refusal moved from where it can be fixed cheaply to where it
parks a convening. Years and months are refused for the reason that schema
states: a trust window whose width depends on the calendar is not a bound
anybody declared. Zero is refused because a zero window is not a declaration
that revocation is honoured instantly, it is a declaration that no projection
may ever be read — which is a way of turning the gate off that looks like
tightening it.

`P7D` — the value in the live register — is accepted.

## D5 — Every new finding is an ERROR or a NOTE, never a WARNING

**Decision.** As stated. No new warning is emitted anywhere in this change.

**Ground.** LedgerxFactory's `tests/validate_wallet_estate.py` runs the pinned
validator over its own tree with `--strict`, and `report()` reds a `--strict` run
on warnings. A warning here would red-line a required check in a repository that
made no request and gets no benefit. wallet-v1.1 made exactly this call for the
register-read note and recorded it in a comment; this change inherits it as a
rule.

## D6 — Additive finding codes only

**Decision.** Eleven new codes; not one existing code renamed or repurposed.

| Code | Refuses |
| --- | --- |
| `register-top-level-unknown` | an unrecognized top-level key |
| `register-staleness-bound-missing` | no `revocation_staleness_bound` |
| `register-staleness-bound-malformed` | a bound that is not a legal non-zero duration |
| `register-seat-keys-malformed` | `seat_keys` not a non-empty list, an entry not a mapping, or an entry's field set not exactly the enumerated set |
| `register-seat-key-malformed` | a `public_key` that is not 32 raw bytes of CANONICAL unpadded base64url |
| `register-seat-fingerprint-malformed` | a `key_fingerprint` outside `sha256:<64 lowercase hex>` |
| `register-seat-fingerprint-mismatch` | a fingerprint that does not recompute from its own public key |
| `register-seat-duplicate` | a repeated `seat_id`, `key_id` or `key_fingerprint` |
| `register-seat-row-unresolved` | an `authorizing_row` naming no row, or a row not active / expired by computed time |
| `register-seat-council-mismatch` | a `council_ref` that is not the authorizing row's `holder_ref` |
| `register-seat-council-spelling` | a `council_ref` and `council_id` that do not denote one body (D7) |

**Ground.** AGENTS.md rule 2: finding codes are pinned BY NAME by live consumers
and a rename is a breaking change with a migration note, never a tidy-up.
LedgerxFactory pins its probe codes empirically, and the register's own codes are
asserted NEGATIVELY by openxFactory's gate (`! grep -qE '\[register-[a-z-]+\]'`)
— which, note, means every new code is already inside that assertion's reach
without an edit there, because the assertion matches the WHOLE bracketed token
against that pattern. That is a property to keep: every code above matches
`register-[a-z-]+` in full.

**Rejected: fewer, broader codes.** "No two refusals share a reason" is the
property the hermes-install side states and this reader already practises
(`register-row-expired` and `grant-state-stale` are distinct facts about one
row). A malformed key and a mismatched fingerprint are different operator
mistakes with different fixes.

## D7 — The entry's field set, and why the council is named TWICE

**Decision.** Exactly seven fields, checked as exact set equality:

```yaml
seat_keys:
  - seat_id: lead-quality
    council_ref: agent:merge-readiness-council
    council_id: merge_readiness_council
    key_id: key-seat-lead-quality-0001
    public_key: bqJJdpCO4dx31e21t6UA4v7b0r0JaxaqmebrjvhK4OI
    key_fingerprint: sha256:a78d5d8fc075a0c771db521f6e4dd5ebec1ae9c76c5209a3bd54983fccb5e781
    authorizing_row: row-mrc-0001
```

**Ground — the projection completeness test.** The set is chosen so that the
register plus the wallet plus the grant beside it are SUFFICIENT to derive every
required per-seat field of a hermes-install projection row, with nothing invented
by the operator:

| Projection seat field | Derived from |
| --- | --- |
| `seat_id` | the entry |
| `council_id` | the entry, VERBATIM |
| `holder_ref`, `wallet_ref`, `grant_ref` | the authorizing ROW |
| `key_id`, `key_fingerprint`, `public_key` | the entry |
| `custody_model` | the wallet record's `custody.model` (`holder_readable`) |
| `act`, `object_ref` | the row's `act` and `target_repo` |
| `distinct_holder_constraint_refs` | the grant (none declared today → `[]`) |
| `state`, `expires_at` | the row |

The projection's `projected_from` block is PROVENANCE of the projection act, not
of the register's content: `repository`, `revision`, `register_version` and
`projected_at` are facts about the copy the operator takes and are supplied by
the act of taking it. Exactly one of its fields comes from the register —
`staleness_bound`, which is `revocation_staleness_bound` carried verbatim, and
which is why that field entering the enforced read set belongs in this change.

An operator who must invent a value is an operator whose projection can disagree
with the register, so the completeness of this table is the test the field set
had to pass.

**Why the council is named twice, which is the correction the alignment pass
forced.** `council_ref` is the AUTHORITY ATTACHMENT: it must equal the
`holder_ref` of the row the entry descends from, and the live register spells
that `agent:merge-readiness-council`. `council_id` is the RUNTIME NAME: it is
carried verbatim into the projection, whose reader keys a seat lookup on the
exact pair `(council_id, seat_id)` and whose committed example and eight negative
fixtures all spell the council `merge_readiness_council`, with underscores,
beside a `holder_ref` spelled with hyphens.

An earlier draft of this design carried only `council_ref` and derived
`council_id` by stripping `agent:`, on the false claim that an underscore is
illegal under openxwallet's identifier grammar. **It is not: the character class
`[A-Za-z0-9._:/-]` contains `_`**, which the projection's own
`custody_model: holder_readable` and `distinct_holder_constraint_refs` prove one
level up. The derivation would have produced `merge-readiness-council`, the
projection's `find()` would have matched nothing, and the operator would have met
`review_authority.seat_unregistered` — the arc's refusal RENAMED rather than
cleared. So both spellings are recorded, and the two-spelling drift the register
is supposed to end is not reintroduced by the register itself.

The reader checks that the two DENOTE ONE BODY: strip `agent:`, swap `_` for `-`.
That relationship is OBSERVED between two live artifacts and is pinned as a check
rather than assumed; if a future council's spellings relate differently, THIS
READER is the thing that changes, which is what it means for the reader to be the
shape. Its own refusal (`register-seat-council-spelling`) is distinct from the
row-attachment refusal so an operator who mistyped the runtime name is told that,
not that the entry is attached to the wrong council.

## D8 — What "an unknown seat" can mean to THIS reader

**Decision.** An entry is refused as an unknown seat when its `council_ref` is
not the `holder_ref` of the row it names.

**Ground, stated as a limit rather than a feature.** The reader CANNOT resolve
`lead-quality` against a council definition: `merge_readiness_council`'s seat
roster is governed in codexFactory (`hermes/domain/review-councils/`), a
repository this validator has no read path into and must not acquire one — the
same boundary hermes-install's projection reader states about the register itself.
So the reader cannot say "that seat does not exist".

What it CAN say is "that entry is not attached to a body this register
commissions", which is the failure the check is actually for: an entry that names
some other council, or names a row that does not commission the council it
claims, is authority claimed outside the register. The spec scenario says this in
the open, so nobody later reads the check as a roster check it is not. Resolving
seat ids against the council roster is a NAMED SUCCESSOR and would need a
cross-repository read path that does not exist.

## D9 — Register-side seat keys and rule (r)'s key ambiguity

**Decision.** The seat keys are register-recorded roots of authority. They are
NOT wallet-declared keys, and rule (r) is not engaged.

**Ground.** `openxwallet-record.schema.yaml` declares ONE `key_reference` per
wallet, and `wal-agent-mrc-0001` declares `key-mrc-0001` — whose private half is
in the operator's vault, which is why the mint was needed at all. Rule (r)
resolves an EXERCISE record's presenting key through the corpus's wallet records
and refuses a key declared by more than one wallet as ambiguous. No exercise
record in openxFactory's tree presents a seat key: exercise records are minted by
the hermes runtime and live in its store, not in this git tree. So the four seat
`key_id`s introduce no ambiguity into any corpus this validator scans, and the
reader deliberately does NOT try to resolve them through `ctx.wallets` — a check
that would fail on every one of them for the correct reason and the wrong
outcome.

**The successor this names, and it is now concrete rather than theoretical.**
hermes-install copies the projection's `key_id` VERBATIM into the exercise
record it mints — as `proof_of_possession.presenting_key_ref` and
`attribution.presenting_key_ref` (`domain/review_authority.py:1023,1029`) — with
only identifier-grammar validation and no resolution against any wallet record.
That is fine where those records live, which is that runtime's Postgres store.
But it means the estate will hold exercise records whose presenting key no wallet
declares, and rule (r) refuses exactly that shape ("a presenting key no wallet
declares is refused rather than passed over") for any exercise record inside a
tree this validator scans.

So the question — should a wallet record be able to declare SEVERAL keys, making
a per-seat key wallet-declared rather than register-declared — has a date on it:
it must be answered before any exercise record carrying a per-seat key is ever
committed to a governed tree. It is not taken here because it is a contract change
to a digested artifact (a bundle version, hence every consumer's pin) and because
the register can hold the fact today with no contract change at all. It is
recorded as successor 3 below with that trigger.

## D10 — `seat_keys` is optional, and the absence is a NOTE

**Decision.** A register with no `seat_keys` is accepted, with a note stating
that no per-seat signing key is recorded and that a projection built from it can
authorize no seat.

**Ground — the no-mixed-state property.** The realization moves the reader and
the register in TWO repositories across THREE merges: openXwallet's reader,
then a tag, then openxFactory's pin bump plus register edit. If `seat_keys` were
REQUIRED, the ordering would become load-bearing: any moment at which
openxFactory's gitlink points at the new reader while its register has not yet
been edited is a moment when the REQUIRED `wallet-validation` check refuses a
governed file over a human-only surface, and the only routine exit from a parked
candidate under a sole code owner is `--admin` (parent design R1/R5) — the ritual
this whole arc exists to end.

With absence as a note, both orders are green: gitlink first then register, or
both together. The staleness bound is REQUIRED and this costs nothing, because
the live register already declares `P7D` and no other register exists in the
estate.

The note is what keeps this from being leniency: absence becomes VISIBLE in the
gate log rather than indistinguishable from "read and fine", and openxFactory's
gate can assert positively on the seat-key note once the keys are recorded —
which is exactly what the realization's downstream pull request does.

**The hole this leaves, named rather than papered over.** Nothing in these deltas
ever obliges `seat_keys` to be PRESENT. A register that never records a key stays
green forever, and the only positive proof that it did is a grep in another
repository's workflow — a step no requirement here obliges and which could be
deleted without violating this capability. That is this arc's own defect one level
up, and it is a real cost of the ordering safety above.

Its exit is DECLARED, with a trigger rather than an intention (tasks §7): once
openxFactory's register carries the four entries and the pin points at this
reader, the absence NOTE becomes a REFUSAL in the next minor — at which point no
ordering is at risk, because the state the refusal would refuse no longer exists.
That flip is a named successor of this change, not a promise inside it. The
obligation to HAVE keys is register-side doctrine and its home is openxFactory's
intake capability; what this reader can do, and now will, is refuse the absence
once absence is no longer a legitimate posture.

## D11 — hermes-install needs no code change (the determination)

**Determination: projection CONTENT only. No hermes-install code change, and no
schema change.**

Evidence, at `origin/main` (`cba1a2b`) — the commit the mint record verified
against:

- `config/schemas/hermes-review-authority-register-projection.schema.yaml`
  already REQUIRES, per seat: `seat_id`, `council_id`, `holder_ref`,
  `wallet_ref`, `grant_ref`, `key_id`, `key_fingerprint`, `public_key`,
  `custody_model`, `act`, `object_ref`, `distinct_holder_constraint_refs`,
  `state`, `expires_at` — with `public_key` pinned to 43 base64url characters and
  `key_fingerprint` to `sha256:<64 hex>`.
- `src/hermes_install/review_authority/projection.py` already recomputes
  `key_fingerprint` from `public_key` and refuses a row that disagrees with
  itself, and already refuses a projection older than its declared
  `staleness_bound` clamped by the deploy ceiling.
- `src/hermes_install/domain/review_authority.py:verify_seat_key_authorization()`
  compares the presented root fingerprint against `authority.key_fingerprint`,
  which the projection reader supplies, and raises
  `review_authority.root_key_mismatch` on inequality.

So the runtime's SHAPE already anticipates exactly this data. What it lacks is a
source: the projection is operator-established, and the operator has had nothing
authoritative to project FROM, because the register could not hold the keys. Once
the register carries the four entries, the projection is RE-DERIVED at deploy
(step 3 of the mint record's numbered successor list) and the
`root_key_mismatch` refusal clears with no hermes-install byte changed.

The projection reader's own docstring anticipates this: "When S4 lands, the
projection's PROVENANCE mechanism (how the file comes to exist) is expected to be
superseded; this module's function signatures are the seam that absorbs that."
That supersession is a change to how the file is PRODUCED, not to how it is read,
and producing it is an operator act.

**One caveat, and it is the one the alignment pass caught:** the projection spells
the council `merge_readiness_council` while the register spells the holder
`agent:merge-readiness-council` — both legal, neither derivable from the other by
any declared rule. If the register recorded only one, the operator would have to
TRANSLATE at projection time, and a mistranslation lands as
`review_authority.seat_unregistered`: this arc's refusal renamed, not cleared. So
the entry records both (D7), the reader checks they denote one body, and the
projection step is a copy rather than a translation. That is the whole reason this
determination can be "content only" and still be safe.

## Risks

### R1 — The reader gets stricter on a file only a human may edit (MEDIUM)

Closing the top level and requiring the staleness bound means a malformed
register refuses a REQUIRED check on a file no council may clear. The exit is
always a human commit, which is correct, but it is slower than a code fix.

*Mitigation:* every new refusal names the offending key or entry and the
expected shape, so the fix is mechanical; the four positive fixtures in the
realization are the exact bytes openxFactory will commit, so the register edit is
adjudicated before it is written; and D10 keeps the ONE field that could
otherwise force an ordering (`seat_keys`) out of the required set.

### R2 — The register becomes a key distribution surface by habit (MEDIUM)

A file that holds four public keys will attract a fifth thing, then a private
half by mistake.

*Mitigation:* the closed top-level set makes a fifth thing a reader edit with a
review. The 43-character canonical base64url check refuses a 64-hex string, which
is the encoding the PRIVATE seeds are stored in — so the most plausible
catastrophic paste is refused by shape, in the required check, before it can be
merged. That is stated here so it is understood as load-bearing and not tidied
into a laxer pattern later.

### R3 — Four hand-copied keys (LOW, and closed)

The four public halves and fingerprints are transcribed from a markdown table in
another repository.

*Mitigation:* the reader recomputes every fingerprint from its key (D2), and the
realization's positive fixture uses the four REAL values, so a transcription slip
fails the openXwallet suite before it reaches openxFactory. All four were
verified to recompute during this packet's authoring.

## Named successors, taken from the alignment pass rather than left implicit

1. **The absence flip** (D10): once openxFactory's register carries the keys, the
   absent-surface note becomes a refusal. Trigger declared in tasks §7.
2. **Attestation strictness.** `_load_attestations` reads the documents beside the
   register and TOLERATES unknown keys in them — the same vacuous-pass class as
   the register's top level, in the same governed directory. Not taken here
   because the attestation's shape has never been enumerated anywhere, so closing
   it means ratifying that enumeration, which is a wider act than admitting a key
   surface. Named so it is not discovered a third time.
3. **A wallet record declaring several keys**, which would make a per-seat key
   wallet-declared rather than register-declared (D9). A contract change to a
   digested artifact, hence a bundle version, hence every consumer's pin.
4. **Resolving seat ids against the council roster** (D8), which needs a
   cross-repository read path that does not exist and should not be created
   casually.

## The word "only", addressed

openxFactory's ratified intake requirement says "the validator's ONLY obligation
at that shape SHALL be to fail a convening that admits a holder carrying no
active row." This change adds obligations at that shape, so the word deserves an
answer rather than silence.

It is read as a FLOOR, not a ceiling — the minimum a register-with-a-reader had
to enforce for the capability to count as realized, written to stop the register
landing with a reader that did nothing. The shipped reader already exceeds it
(computed expiry over stored state, act-tier attestation, grant/row binding,
tier and act closure), and did so in the change that ratified the sentence. A
ceiling reading would make the reader as-merged non-conformant to its own
ratification, which cannot be what was ratified.

## Open questions

None carried for the convener. The one decision that could reasonably have gone
the other way — cap raised versus key surface added — is taken in D1 with its
alternative and cost stated, and the mint record already named both exits as
acceptable. If the convener prefers row-set semantics, D1 is the section to
reverse and the spec's third requirement is the one that changes.
