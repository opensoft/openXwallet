---
code_surface: openXwallet `scripts/validate-openxwallet.py` (`check_register`) plus its self-test probes, its tests, and the bookkeeping of a release. NO `contracts/` byte and no register schema. Per `release-realization`, this change archives only on merged, green realization evidence for that surface.
target_release: unallocated at proposal. The realization is expected to be an ADDITIVE MINOR (`wallet-v1.2`) whose eight contract digests are unchanged, but per AGENTS.md rule 6 the five coordinated values are allocated at realization and nothing is reserved here.
Status: draft
Held: for Brett Heap. Nothing in this packet is ratified by its authoring. The
  realization branch exists and is gated on this ratification; no reader byte
  and no register byte lands until the gate below is checked.
---

# Proposal: add-per-seat-register-entries

## Why

Four council seat signing keys exist and the register they must descend from
cannot hold them.

On 2026-08-28 the operator minted four Ed25519 keypairs, one per seat of
codexFactory's `merge_readiness_council`, provisioned their private halves as
GitHub Actions secrets in that repository's `worker-credentials` environment,
and proved the chain end to end off-runner: each seed round-tripped through the
worker's own `root_key_from_env()` under the pinned backend, and each resulting
root signature verified under hermes-install's own verifier from the recorded
public half alone, over a byte-identical canonical message. The record is
codexFactory `hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`
(merged at `78b8fa2`).

That record's own §"What this does NOT discharge" names this change:

> The public halves are recorded HERE and NOT YET in openxFactory's
> review-authority register, because the register has no slot for them. Its
> reader … takes each row's field set as EXACT set equality against nine named
> fields, so a key field on a row is rejected; and `REGISTER_MVP_SINGLE_ROW = 1`
> rejects a second row outright, so four per-seat rows cannot be recorded
> either. … A new unread top-level block would pass the reader only because the
> reader ignores what it does not read, which is not the same as being recorded.

The consequence is live and named: until the register knows these keys, the
deliberation lane SIGNS but the runtime cannot authorize what it signs with.
`verify_seat_key_authorization()` refuses a root fingerprint the operator's
projection does not record — `review_authority.root_key_mismatch` — and the
projection must not carry a fact the register does not.

There is a second, older instance of the same defect on the same file. The S5
session that landed openxFactory task 7.3 added a top-level
`revocation_staleness_bound: P7D` to the register, and the PINNED reader does
not validate it: `check_register` is strict on `REGISTER_ROW_FIELDS` but reads
only `register_version` and `rows` at the top level, so an unknown top-level key
passes silently (measured on the edited tree: 0 errors, 0 warnings). It is
carried today as `add-composition-drift-cascade` task 3.4, a named successor
that no delta on that ledger obliges.

Both are the same class — a governed declaration that a required check parses
and never adjudicates — and both are closed here, because the field that closed
one enters the read set at the same moment the field that closes the other does.

## What Changes

One `## ADDED` capability, `review-authority-register-reader`, with three
requirements. No new contract family, no contract byte, no register schema.

- **The register's whole top level is read, and a declaration no reader reads is
  refused.** The top-level key set becomes CLOSED and exactly enumerated; an
  unrecognized key is refused. `revocation_staleness_bound` enters the enforced
  read set: present, a well-formed ISO-8601 duration of weeks/days/hours/
  minutes/seconds, non-zero, refused by its own named finding when absent,
  malformed or zero. Years and months are refused because a trust window whose
  width depends on the calendar is not a bound anybody declared — the same
  reasoning, and the same grammar, hermes-install's projection schema already
  applies to the value it projects VERBATIM from this field.
- **Per-seat signing keys are recorded in the register and enforced by its
  reader.** A new top-level surface records, per seat: the seat identifier, the
  council as the REGISTER spells it, the council as the RUNTIME spells it (two
  legal spellings of one body, neither derivable from the other — see `design.md`
  D7, the correction the alignment pass forced), a key identifier, the public
  key, that key's fingerprint, and the authorizing ROW. The reader recomputes the
  fingerprint from the public key and refuses a self-disagreeing entry; refuses a
  duplicate seat, key id or fingerprint; refuses an entry whose authorizing row
  does not resolve, is not active, or has passed its COMPUTED expiry; refuses an
  entry whose council does not match the holder that row commissions; refuses an
  entry whose two spellings do not denote one body; and checks the entry's field
  set as exact set equality, as rows are checked, because the register has no
  schema and this reader is its shape. Every recorded entry is ADJUDICATED or
  REFUSED, and the note the reader emits reports the number ADJUDICATED — a count
  of entries PARSED would prove parsing and nothing else, which is the defect one
  level up from the one being closed.
- **The first shape's single-row cap bounds authority rows, and the key surface
  is bounded structurally.** `REGISTER_MVP_SINGLE_ROW` is RETAINED at one and
  keeps refusing a second authority row; what changes is that the reader now
  says what the cap binds. The key surface takes no count bound — a council's
  seat set is governed in another repository and a number recorded here would go
  stale silently — and is bounded instead by the structural requirement that
  every entry descend from a row in this same file.

## Why the cap is re-grounded rather than raised

The mint record named two exits: "row-set semantics, or a per-seat key surface".
This change takes the SECOND, and the choice is the packet's load-bearing
decision (`design.md` D1).

Raising the cap would admit register breadth that openxFactory's ratified intake
requirement still calls a successor — more than one holder, more than one target
repository, per-seat GRANTS — and none of that is needed. The four seats share
one holder (`agent:merge-readiness-council`), one wallet, one grant, one target
repository, one act and one expiry. What they no longer share is a signing key.
A key is not a grant, and recording four keys under one row widens no authority:
the register still commissions exactly one body over exactly one repository for
exactly one act.

So the cap is not superseded in its force, only in its SCOPE, and the scope it
had was never stated because nothing else was in the file. Stating it is part of
the work.

## What this change does NOT do

- **No contract bytes.** `contracts/` is untouched, and the realization is
  expected to leave all eight digested contract artifacts byte-identical. The
  seat keys live on the register — which is DELIBERATELY KINDLESS (openxFactory
  design D11) and has no schema — precisely so that admitting them needs no
  contract change.
- **No register schema.** D11 stands: the rule-of-three has still not fired, and
  the reader is still the shape. This change makes the shape wider and stricter;
  it does not author a schema for it.
- **No second key on a wallet record.**
  `contracts/openxwallet/openxwallet-record.schema.yaml` declares ONE
  `key_reference` per wallet, so four per-seat keys under one wallet cannot be
  wallet-declared without a contract change. Whether a wallet should be able to
  declare several keys is a NAMED SUCCESSOR and is not taken here — see
  `design.md` D9, which also records why rule (r)'s DID-scoped key-ambiguity
  refusal is not engaged by register-side seat keys.
- **No finding-code rename.** Every finding this change adds is a NEW code.
  LedgerxFactory's estate suite pins codes by string and AGENTS.md rule 2 makes
  a rename a breaking change; additive-only is not a courtesy here.
- **No warning.** Every new finding is an ERROR or a NOTE. LedgerxFactory runs
  the validator with `--strict`, where `report()` reds a run on warnings, so a
  new warning would red-line a required check in a repository that never asked
  for it — the same reasoning that made wallet-v1.1's register-read line a note.
- **No register edit, and no projection.** Writing the four public halves into
  `governance/review-authority/register.yaml` is an openxFactory pull request
  over a PERMANENTLY HUMAN-ONLY surface; establishing the runtime projection is
  an operator act downstream of it. This change makes both possible and performs
  neither.
- **No version allocation.** See `target_release` above.

## Impact

- **A new capability in this repository**, taking the count of promoted
  capabilities from two to three on archive. Eleven promoted wallet requirements
  remain eleven; nothing in the `openxwallet` or `openxwallet-agent-profile`
  families is restated.
- **openxFactory's consumer gate stays green across the pin bump in either
  order.** The staleness bound becomes REQUIRED, and openxFactory's register
  already declares it (`P7D`); the seat surface's ABSENCE is a note, not a
  refusal. So a pin bump that moves the gitlink before the register carries seat
  keys is green, and one that lands both together is green — there is no window
  in which the required `wallet-validation` check refuses a register the
  operator has not yet been able to fix. This is a deliberate design property
  (`design.md` D10), not a leniency.
- **No other consumer is disturbed.** openxFactory is the only repository in the
  estate that carries a register at all (checked: codexFactory,
  LedgerxFactory, MedxFactory, LedgerxWallet, openXwallet itself carry none), and
  a tree with no register and no review-class grant remains clean with a note, as
  it is today.
- **hermes-install needs no code change** — see `design.md` D11. Its projection
  schema at `origin/main` (`cba1a2b`) already requires per-seat `key_id`,
  `key_fingerprint` and `public_key`, and its reader already recomputes the
  fingerprint from the key and refuses a self-disagreeing row. What it lacks is
  not a shape but CONTENT: something authoritative to project FROM. This change
  supplies it; the projection is then re-derived at deploy.
- **`add-composition-drift-cascade` task 3.4 is discharged here**, not there. It
  was recorded as a named successor on that ledger by repository and by S5, with
  no delta obliging it; this packet obliges it.

## Alignment pass, 2026-08-28

One reviewer, adversarial on the vacuous-pass class, reading the deltas against
the reader as it ships, the live register, the ratified intake spec and design
D11, the mint record, the three hermes-install files at `cba1a2b`, openxFactory's
consumer gate and pin, and LedgerxFactory's estate suite. Verdicts as returned:

| Question | Verdict |
| --- | --- |
| A — the packet's home (a new openXwallet capability, not a MODIFIED delta on the unpromoted `review-authority-intake`) | ALIGNED |
| B — D1: the cap re-grounded, not raised | ALIGNED WITH NOTE |
| C — D7's field set completes a projection with nothing invented | **MISALIGNED — fixed** |
| D — D10: the surface optional, the bound required | ALIGNED WITH NOTE, plus a hole of its own |
| E — codes and note-not-warning keep LedgerxFactory and openxFactory green unedited | ALIGNED |
| F — D11: hermes-install needs no code change | right on code, **MISALIGNED on the caveat — fixed** |
| G — unenforceable or vacuously satisfiable delta text | two live vacuous passes — **fixed** |

**What the pass changed, and it was load-bearing.** C and F turned on a factual
error: the draft claimed an underscore is illegal under openxwallet's identifier
grammar and therefore derived the runtime's council id by stripping `agent:` from
the register's holder reference. The character class `[A-Za-z0-9._:/-]` CONTAINS
`_`, and hermes-install's projection spells the council `merge_readiness_council`
beside a `holder_ref` spelled `agent:merge-readiness-council` — in its committed
example and in all eight of its negative fixtures. The derivation would have
produced the wrong key for a lookup that matches `(council_id, seat_id)` exactly,
and the operator would have met `review_authority.seat_unregistered`: the very
refusal this arc is clearing, renamed. The entry now carries BOTH spellings, the
reader checks they denote one body, and the projection step is a copy rather than
a translation. Six fields became seven.

G's two vacuous passes are closed in the delta text: the seat-key note now
reports the number ADJUDICATED (a count of entries parsed would have satisfied
the old wording, and openxFactory's positive-proof step asserts on exactly that
line), and the four-seats-under-one-row scenario now requires that note rather
than mere acceptance, which a reader that never opened the surface would also
have satisfied. Two obligations that were claims about an author rather than
checks ("an entry the reader ignores shall not exist"; "its refusal names the
cap") are restated as an adjudicated-or-refused rule and an explicit
message-content obligation.

B's note and D's hole are answered rather than absorbed: `design.md` gains
`## The word "only", addressed` (the ratified sentence is a floor, and the reader
as merged already exceeds it) and a named successor with a TRIGGER for the
absence flip, so "green with nothing recorded" is not a permanent legal state.
The pass also named three successors this change does not take —
`_load_attestations`' unknown-key tolerance, a wallet record declaring several
keys, and roster resolution — now recorded in `design.md`.

Everything else it checked came back clean: `78b8fa2`, `cba1a2b`, the nine row
fields, `P7D`, the eight digests, `pinned_by_commit_only` covering the validator,
all eleven new codes matching `register-[a-z-]+`, and all four public halves
recomputing to their recorded fingerprints (recomputed independently).

## Council or not — the call, stated

**No council convening is sought for this packet, and that is a call rather than
an omission.** Three reasons, in order of weight:

1. openXwallet hosts no council machinery. Councils, seats, verdicts and the
   `deliberate` job live in codexFactory; this repository has two required
   checks and a human merge gate.
2. The convening that would review it is the very body whose keys are being
   recorded. openxFactory's ratified intake requirement is explicit: "a council
   whose own commission is recorded in the register SHALL NOT be eligible to
   clear a candidate that edits it." The register-side act (deliverable C) is
   therefore human-only by name; a council clearance of the READER packet that
   admits its own keys would be the same conflict one repository to the left.
3. The lane the keys unblock is not yet authorizing anything, so no convening
   could be convened over this change with verifiable seat authority even if it
   were eligible — that is the circularity this whole arc exists to break.

What replaces it is the compact alignment pass below plus Brett's ratification.
If the convener judges otherwise, the packet is unamended by that judgement and
can be put to a council without rework.

## Status

`Status: draft`. **Held for Brett Heap.** Ratification is the operator's act and
has not been made. The realization branch (`014-per-seat-register-entries`) is
authored and gated: its ratification gate in `tasks.md` is unchecked, and it must
not merge before this packet is ratified.
