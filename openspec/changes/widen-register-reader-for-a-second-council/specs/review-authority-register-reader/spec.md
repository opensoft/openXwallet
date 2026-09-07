# review-authority-register-reader

The reader-side half of openxFactory's `review-authority-intake`. openxFactory
owns the register — the artifact, its human-only floor, and the doctrine of what
a row confers. This capability owns the OBLIGATIONS OF THE PROGRAM THAT READS IT.

**This delta AMENDS the capability rather than landing beside it, and that is
deliberate.** `add-per-seat-register-entries` added the requirement below that
says in terms *"a second authority row SHALL still be refused"* — there is no
door in that sentence to walk through, unlike openxFactory's own intake
requirement, whose first-shape scenario names the wider scope as "a named
successor". A change that admitted a second body while that sentence stood would
leave two promoted requirements contradicting each other, so the sentence moves.

**The sibling archives first, and this is measured rather than assumed.** The
capability is not in `openspec/specs/` yet: it exists only as
`add-per-seat-register-entries`' delta. On openspec 1.2.0 an archive whose
target spec does not exist aborts — *"only ADDED requirements are allowed for
new specs; MODIFIED and RENAMED operations require an existing spec"* — so this
change's archive is ordered behind that one (`archive_after:` in the
front-matter, tasks §5).

## ADDED Requirements

### Requirement: A refusal the reader can no longer emit is retired by name and never re-scoped
A finding code whose invariant is withdrawn SHALL be RETIRED — removed from the
reader, emitted by nothing, and recorded as a removed refusal in the release
that removes it — and SHALL NOT be re-pointed at a different invariant while
keeping its string; consumers pin finding codes BY NAME, and a code that
disappears breaks a pinned assertion loudly while a code that quietly changes
meaning satisfies the same assertion over a different fact. Before a code is
retired the estate SHALL be searched for citations of it and the result
recorded, so the retirement's blast radius is measured rather than assumed, and
a code whose MEANING is unchanged by a narrowing of its trigger SHALL keep its
string rather than being renamed to advertise the narrowing.

#### Scenario: An invariant is replaced and its code has nowhere to go
- **WHEN** a reader invariant is withdrawn and each fact it stood in for already carries its own precise finding code
- **THEN** the withdrawn invariant's code is retired rather than re-pointed at one of those facts
- **AND** the release that retires it records it as a removed refusal, even where the estate search found no consumer pinning it

#### Scenario: A retired string is proposed for a new meaning
- **WHEN** a change would keep a retired code's string alive over a different invariant
- **THEN** it is refused, because a pinned assertion would keep passing while adjudicating something else

#### Scenario: A code's trigger narrows but its meaning does not
- **WHEN** a refusal continues to mean what it always meant and only the set of inputs that trigger it narrows
- **THEN** the code keeps its string, and the narrowing is carried in the message rather than in a new name

### Requirement: The reader's own self-test carries a probe for every invariant that bounds the register's breadth
The reader SHALL carry, inside its own self-test block, a positive probe and a
negative probe for each invariant that bounds how many bodies the register may
commission and how their rows and seat entries must resolve, so that an edit
which silences one of those invariants fails INSIDE the required check every
consumer runs, rather than only in this repository's test suite; where an
invariant is withdrawn, its probe SHALL be withdrawn in the same change, so the
self-test never asserts a refusal the reader can no longer emit.

#### Scenario: A breadth invariant is enforced only by the row loop
- **WHEN** the reader stops refusing on a count and relies on each row resolving end to end
- **THEN** the self-test carries a probe proving a row that does NOT resolve is still refused
- **AND** the probe is in the reader's own self-test, because consumers run the pinned validator and never run this repository's tests

#### Scenario: A later edit silences an invariant
- **WHEN** an edit removes or weakens one of the invariants that replaced a withdrawn count bound
- **THEN** the self-test reds inside every repository that pins this reader, on the run that would otherwise have admitted the widened register

#### Scenario: A refusal is retired
- **WHEN** a finding code is retired
- **THEN** the self-test probe asserting that code is removed in the same change, because a probe expecting a refusal that can never fire is a test of nothing

## MODIFIED Requirements

### Requirement: Per-seat signing keys are recorded in the register and enforced by its reader
The register SHALL be able to record, beside its authority rows, the PER-SEAT
signing key each seat's authority descends from, and the reader SHALL read and
ENFORCE every recorded entry. An entry SHALL carry exactly a seat identifier, the
council it seats as the register spells it, the council as the consuming runtime
spells it, a key identifier, the public key, that key's fingerprint, and the
identifier of the authorizing row — field set checked as exact set equality, as
rows are, because the register has no schema and this reader is its shape. The
reader SHALL recompute the fingerprint from the public key and refuse a
self-disagreeing entry; SHALL refuse a seat identifier repeated WITHIN ONE
COUNCIL, and a key identifier or fingerprint repeated ANYWHERE IN THE FILE;
SHALL refuse an entry whose authorizing row does not resolve, is
not active, or has passed its computed expiry; SHALL refuse an entry whose
council does not match the holder that row commissions; and SHALL refuse an entry
whose two council spellings do not denote one body. Every recorded entry SHALL be
either ADJUDICATED or REFUSED — an entry that is merely parsed is the same
vacuous pass as an unread declaration — and the reader's note SHALL report the
number ADJUDICATED, so that a number equal to the number recorded is only ever
emitted on a run in which every recorded key was stood behind.

#### Scenario: The recorded seat keys resolve end to end
- **WHEN** a register records per-seat entries whose fingerprints recompute from their public keys and whose authorizing row is active and unexpired
- **THEN** the reader accepts them and emits a note naming the number ADJUDICATED out of the number recorded
- **AND** a refused entry MUST be excluded from that number, so the note is evidence of adjudication rather than a restatement of how many entries were parsed
- **AND** the note MUST be a note and never a warning, because consumers run this validator under `--strict`

#### Scenario: The two council spellings name different bodies
- **WHEN** an entry's register-side council reference and its runtime-side council identifier do not denote one body
- **THEN** the reader refuses the entry, because the runtime spelling is projected verbatim and a disagreement between the two would make the projection name a body the authorizing row does not commission

#### Scenario: A seat entry disagrees with itself
- **WHEN** an entry's `key_fingerprint` does not recompute from its `public_key`
- **THEN** the reader refuses the entry, because two spellings of one key's identity mean one of them is wrong and choosing either is choosing which authority to believe

#### Scenario: A seat entry's key is malformed
- **WHEN** an entry's `public_key` is not 32 raw bytes of canonical unpadded base64url
- **THEN** the reader refuses the entry with a finding distinct from the fingerprint-mismatch finding

#### Scenario: A seat entry names no backing row
- **WHEN** an entry's authorizing row identifier resolves to no row in the register, or resolves to a row that is inactive or expired by computed time
- **THEN** the reader refuses the entry, because a key descending from no live authority descends from nothing

#### Scenario: Two councils seat the same role name
- **WHEN** two commissioned bodies each record an entry for the same `seat_id` under their own `council_id`
- **THEN** both entries are admitted and neither is reported as a duplicate of the other, because two bodies commonly seat the same ROLE and a register that cannot say so cannot represent a second body at all

#### Scenario: A seat is recorded twice
- **WHEN** one `council_id` records the same `seat_id` twice
- **THEN** the reader refuses the register rather than resolving the collision by file order, because that council then has two answers to which key is that seat's root
- **AND** the refusal names the council, so it is not read as a collision with a different body's seat

#### Scenario: A key identifier or fingerprint is repeated
- **WHEN** two entries share a `key_id` or a `key_fingerprint`
- **THEN** the reader refuses them REGARDLESS of their councils, because a key is one key and two bodies presenting it are two claims on one identity
- **AND** this uniqueness MUST NOT be narrowed to the council alongside the seat identifier, since a per-council key namespace would let one private half sign for two bodies

#### Scenario: A seat entry names a body the register does not commission
- **WHEN** an entry's council does not match the `holder_ref` of the row it names as its authority
- **THEN** the reader refuses the entry — this is the enforceable meaning of an unknown seat at this altitude, since the council's seat roster is governed in another repository and cannot be resolved here

#### Scenario: An entry carries an unknown or missing field
- **WHEN** an entry's field set is not exactly the enumerated set
- **THEN** the reader refuses it and names both the missing and the unknown fields

#### Scenario: No seat keys are recorded
- **WHEN** a register carries rows and records no per-seat entries
- **THEN** the reader accepts the register and emits a note stating that no per-seat signing key is recorded and that a runtime projection built from it can authorize no seat
- **AND** the reader MUST NOT refuse, because a register is legitimately readable before its keys are minted and refusing would red-line the very check that must stay green across the pin bump that admits them

### Requirement: The register's breadth is bounded by invariants rather than a row count, and the key surface is bounded structurally
The register SHALL carry one AUTHORITY ROW per commissioned body — its own
`row_id`, holder, wallet, grant and expiry — and the reader SHALL NOT bound the
number of such rows by a count; breadth SHALL be bounded instead by three
invariants, all of which SHALL hold: every authority row RESOLVES END TO END, to
its own scanned wallet record, to a grant whose audience, acts, objects, tier and
expiry match the row, to a custody attestation where the row stands at tier
`act`, and to a computed expiry in the future; every per-seat entry ATTACHES TO A
ROW THAT COMMISSIONS ITS BODY; and the pair (`council_id`, `seat_id`) is UNIQUE.
No numeric bound SHALL be substituted for the withdrawn count, because the
register is a permanently human-only surface where every row is one governed
operator act, so its breadth is already bounded by what a human stands behind —
and a number recorded in the reader would go stale on the day a body arrived
while saying nothing true about why that number was right. The per-seat key
surface SHALL likewise NOT be bounded by a count, because a council's seat set is
governed elsewhere; it SHALL be bounded STRUCTURALLY, by the requirement that
every entry descend from a row in this same file. Recording per-seat keys SHALL
NOT be read as widening the register's holder, target or act breadth.

#### Scenario: A second commissioned body is registered
- **WHEN** a register declares a second authority row for a body other than the one it already commissions, and that row resolves to its own wallet, grant and custody attestation with an unexpired computed expiry
- **THEN** the reader ADMITS it, and its `intake register read:` note reports the number of rows
- **AND** no refusal is emitted on the ground of row COUNT, because the count bound is withdrawn rather than raised

#### Scenario: A second authority row is still refused
- **WHEN** a register declares a second authority row whose grant does not back it, whose wallet does not resolve, or which stands at tier `act` with no custody attestation
- **THEN** the reader refuses THAT ROW with the finding naming what failed to resolve
- **AND** the refusal MUST NOT be a count refusal, because the defect is the row's resolution and not the register's breadth

#### Scenario: A third body arrives
- **WHEN** a third commissioned body is added to a register whose existing rows and entries all resolve
- **THEN** it is admitted with no edit to the reader, because the invariants are stated over rows generally and not over a number

#### Scenario: Four seats descend from one row
- **WHEN** a register carries one authority row and four per-seat entries naming it
- **THEN** the reader accepts it, because the entries add no holder, no target repository and no act
- **AND** its note MUST report four entries adjudicated, so acceptance is evidence the entries were read and not evidence that they were skipped

#### Scenario: The one-row register that exists today
- **WHEN** the reader is widened and a register still carrying exactly one authority row and one council's seat entries is read
- **THEN** its output is unchanged — the same notes, no findings, the same exit code — so a consumer's pin advance to the widened reader is provably neutral before its register moves

## RENAMED Requirements

- FROM: `### Requirement: The first shape's single-row cap bounds authority rows, and the key surface is bounded structurally`
- TO: `### Requirement: The register's breadth is bounded by invariants rather than a row count, and the key surface is bounded structurally`
