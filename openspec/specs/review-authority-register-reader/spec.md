# review-authority-register-reader Specification

## Purpose
The reader-side half of openxFactory's `review-authority-intake`: openxFactory owns the register — the artifact, its human-only floor, and the doctrine of what a row confers — but the program that reads it (`scripts/validate-openxwallet.py`, `check_register`) lives here and runs inside the REQUIRED `wallet-validation` check of every repository that pins openXwallet. This capability owns the obligations of that program: reading the register's whole top level rather than a subset, recording and enforcing per-seat signing keys beside its authority rows, and bounding both the authority-row cap and the key surface's own structure — so a governed declaration a required check parses but never adjudicates cannot pass silently.
## Requirements
### Requirement: The register's whole top level is read, and a declaration no reader reads is refused
The register reader SHALL treat the register's top-level key set as CLOSED and
exactly enumerated, SHALL refuse an unrecognized top-level key, and SHALL
validate every key it recognizes — a governed declaration that the required
check parses but never adjudicates is a vacuous pass and confers nothing.
`revocation_staleness_bound` SHALL be one of the validated keys: present, a
well-formed ISO-8601 duration of weeks, days, hours, minutes and seconds,
naming a non-zero window, and refused by its own named finding when absent,
malformed or zero.

#### Scenario: An unread top-level declaration is added
- **WHEN** a register carries a top-level key the reader does not enumerate
- **THEN** the reader refuses the register with a finding naming the unknown key
- **AND** the refusal MUST NOT be softened to a warning or a note, because a declaration nothing enforces is the defect being closed

#### Scenario: The staleness bound is absent
- **WHEN** a register carries rows but no `revocation_staleness_bound`
- **THEN** the reader refuses it, because a projection of that register has no declared window in which it may be believed

#### Scenario: The staleness bound is malformed or empty
- **WHEN** the declared bound is not an ISO-8601 duration, names years or months, or names a zero-length window
- **THEN** the reader refuses it with a finding distinct from the absent-bound finding

#### Scenario: A calendar-relative window is refused
- **WHEN** the declared bound names years or months
- **THEN** the reader refuses it, because a trust window whose width depends on the calendar is not a bound anybody declared

### Requirement: Per-seat signing keys are recorded in the register and enforced by its reader
The register SHALL be able to record, beside its authority rows, the PER-SEAT
signing key each seat's authority descends from, and the reader SHALL read and
ENFORCE every recorded entry. An entry SHALL carry exactly a seat identifier, the
council it seats as the register spells it, the council as the consuming runtime
spells it, a key identifier, the public key, that key's fingerprint, and the
identifier of the authorizing row — field set checked as exact set equality, as
rows are, because the register has no schema and this reader is its shape. The
reader SHALL recompute the fingerprint from the public key and refuse a
self-disagreeing entry; SHALL refuse a duplicate seat identifier, key identifier
or fingerprint; SHALL refuse an entry whose authorizing row does not resolve, is
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

#### Scenario: A seat is recorded twice
- **WHEN** two entries name the same seat, the same key identifier, or the same fingerprint
- **THEN** the reader refuses the register, rather than resolving the collision by file order

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

### Requirement: The first shape's single-row cap bounds authority rows, and the key surface is bounded structurally
The single-row cap ratified as the register's first shape SHALL be understood to
bound AUTHORITY ROWS — one holder, one target repository, one act, one tier, one
expiry — and SHALL remain enforced over them unchanged. The per-seat key surface
SHALL NOT be bounded by a count, because a council's seat set is governed
elsewhere and a number recorded here would go stale silently; it SHALL be bounded
STRUCTURALLY instead, by the requirement that every entry descend from a row in
this same file. Recording per-seat keys SHALL NOT be read as widening the
register's holder, target or act breadth, and a second authority row SHALL still
be refused.

#### Scenario: A second authority row is still refused
- **WHEN** a register declares two authority rows
- **THEN** the reader refuses it exactly as before
- **AND** the refusal MUST state that the cap binds AUTHORITY rows rather than the file's contents generally, so a later reader of the refusal is not told that a per-seat key surface exceeded the first shape

#### Scenario: Four seats descend from one row
- **WHEN** a register carries one authority row and four per-seat entries naming it
- **THEN** the reader accepts it, because the entries add no holder, no target repository and no act
- **AND** its note MUST report four entries adjudicated, so acceptance is evidence the entries were read and not evidence that they were skipped

