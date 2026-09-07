# Realization evidence — `widen-register-reader-for-a-second-council`

Status: record

Lane: hermes-wallet-exercise

Recorded 2026-09-06 for tasks §3.1–§3.6 (openxFactory rows 2.3, 2.4, 2.5) and
the bookkeeping half of §4 (openxFactory row 2.6). Authority: the change is
RATIFIED (2026-09-06T23:25:11Z, Brett Heap, operator authority — "ratify 16 and
archive add-per-seat-register-entries") and landed as PR #16 → `6ec84b1b`; the
realization slice was authorized in-session ("go on the 16 realization slice").

Branch `realize/widen-register-reader-for-a-second-council`, cut fresh from
`main` at `6ec84b1b`. Reader + tests: commit `9ebc686`.

## 1. What moved in the reader

| | Before | After |
|---|---|---|
| Row-count bound | `REGISTER_MVP_SINGLE_ROW = 1`, refusal `register-minimal-shape-exceeded` | RETIRED; no numeric bound; three invariants, each with its existing code |
| Seat identity | `seat_id` unique across the FILE | pair (`council_id`, `seat_id`); the message names the council |
| `key_id` / `key_fingerprint` | globally unique | globally unique (UNCHANGED — asserted across councils) |
| New finding codes | — | NONE, by design D5 |
| Self-test probes on the cap | 2 (`register-minimal-shape-exceeded`, `seat-keys-do-not-raise-the-cap`) | 0 (both removed) |
| Self-test probes on the invariants | 0 | 6 |

## 2. Gate bar (AGENTS.md rule 5), run from the repository root

| Gate | Before the slice | After |
|---|---|---|
| `python3 -m pytest tests/ -q` | 104 passed, 2 xfailed | **107 passed**, 0 xfailed |
| `scripts/validate-openxwallet.py .` | rc=0, 0 error(s) 0 warning(s) | rc=0, 0 error(s) 0 warning(s) |
| `scripts/validate-openxwallet.py . --strict` | rc=0 | rc=0 |
| `scripts/wallet-yaml-syntax-gate.py .` | rc=0 | rc=0 |
| `scripts/verify-contract-pin.py` | rc=0 (openxFactory@30565e48ffe3, contract-v1.44) | rc=0 |
| `openspec validate widen-register-reader-for-a-second-council --strict` | valid | valid |
| `openspec validate --all --strict` | 6 passed, 0 failed | 6 passed, 0 failed |

Test-count arithmetic, so the delta is not taken on trust: 106 collected before
(104 passing + 2 strict xfails) → 107 collected after. The two xfails became
plain passes, the two "exact codes today" measurements were CONVERTED rather
than deleted, and ONE test was added —
`test_a_seat_entry_attached_to_another_bodys_row_is_refused`, the invariant only
a multi-body register can violate.

## 3. The self-test probes BITE — proven by mutation, not asserted

Two mutations were applied to the reader in the worktree, the validator run, and
the file restored byte-for-byte (sha256 compared):

| Mutation | Self-test result |
|---|---|
| `seen_key = entry[field]` (revert the pair key to a global seat namespace) | 4 findings: `register-two-bodies-clean` (codes AND the note assertion), `register-two-councils-one-seat-name`, `register-second-row-unresolved` |
| `scoped = True` (narrow `key_id`/`key_fingerprint` to the council) | 2 findings: `seat-duplicate-across-councils[key_id]`, `[key_fingerprint]` |

Both mutations red the REQUIRED check every consumer runs, which is why design
D4 put these probes in the self-test rather than only in `tests/`.

## 4. Consumer check A — openxFactory's LIVE register is untouched (design D6)

Read-only. openxFactory `origin/main` = `9ffc6252`; its `governance/` tree was
exported with `git archive` into a temp directory and read by BOTH readers — the
pinned one (`git show origin/main:scripts/validate-openxwallet.py`, byte-identical
to the reader openxFactory pins at `b7b0fbb3` / `wallet-v1.4`) and the widened
one:

```
note  intake register read: governance/review-authority/register.yaml (1 row(s))
note  intake register: 4 of 4 per-seat signing key(s) adjudicated and resolved
validate-openxwallet: 0 error(s), 0 warning(s)
```

`diff` of the two readers' full output is **EMPTY**, plain and under `--strict`;
rc=0 in all four runs. This is openxFactory task 2.9's neutrality gate, measured
on the live bytes rather than on a fixture: its pin advance moves the reader
BEFORE its register moves, so an output that differed by one line would leave
the ratified pin-first/register-second sequence with no valid ordering.

## 5. Consumer check B — the #717 design-D5 probe now ACCEPTS `8 of 8`

The probe tree is the LIVE `governance/` export above plus the second
commissioned body: `row-grc-0001` (holder `agent:gate-rules-council`, tier
`act`, `expires_at 2027-06-30T00:00:00Z`), `wal-agent-grc-0001` declaring five
keys (root + four seats), `grant-grc-0001` backing the row field for field, its
custody attestation, and the four `gate_rules_council` seat entries
(`lead-architect`, `lead-security`, `lead-quality`, `company-policy-lead`).

The gate-rules key material is DETERMINISTIC SYNTHETIC, derived by the same
`_derive` the test module uses, so the probe's values are exactly the values
`tests/widen_register_reader/test_second_council.py` asserts on. **No
gate-rules key exists yet** — minting them is Brett's operator act (openxFactory
task 3.2) — and a real-looking invented value would be a key no ceremony
produced.

| Reader | Result |
|---|---|
| PINNED (`wallet-v1.4`) | rc=1, `2 row(s)`, **`5 of 8`**, 4 errors: `register-minimal-shape-exceeded` + 3 × `register-seat-duplicate` (`lead-security`, `lead-quality`, `company-policy-lead`) |
| WIDENED (this branch) | **rc=0**, `2 row(s)`, **`8 of 8`**, 0 error(s) 0 warning(s); rc=0 under `--strict` with no `WARN` line |

The pinned column reproduces design D0's measured transcript exactly, code for
code and count for count, so the design document's quotation is checkable rather
than quotable. The widened column is the literal openxFactory task 2.8 moves its
consumer gate's assertion to.

## 6. The release — allocated at realization (AGENTS.md rule 6)

**`wallet-v1.5`**, an ADDITIVE MINOR for the bundle and REDUCING for the
reader's refusal set. The five coordinated values, and where each one is:

| Value | State |
|---|---|
| per-file `contract_schema_version` | UNCHANGED on all eight artifacts (no `contracts/` byte moves) |
| `contract_bundle_version` in `contracts/manifest.yaml` | `wallet-v1.4` → `wallet-v1.5`, in this pull request; it is the ONLY line that moves in that file |
| `contracts/releases/wallet-v1.5.digests.yaml` | CUT BY RECOMPUTATION in this pull request; differs from `wallet-v1.4.digests.yaml` in exactly ONE line, `bundle_tag` |
| `contracts/CHANGELOG.md` entry | in this pull request, carrying the REMOVED-refusal migration note |
| annotated `wallet-v1.5` tag | **NOT created and NOT pushed by this slice** — see the cut act below |

The digest cut is verified rather than trusted: the same procedure was run for
`wallet-v1.4` first and reproduced that committed file BYTE-FOR-BYTE, and every
one of the eight recomputed digests was cross-checked against
`contracts/manifest.yaml`'s recorded value. Selection is by the DECLARED FIELD
`release_surface: false` (which excludes the one vendored member), never by a
`contracts/schemas/` path heuristic.

### The cut act, named with its performer (task §4.1)

**The act:** an ANNOTATED git tag `wallet-v1.5` at the merge commit this pull
request produces on `main` — never at a branch head and never at a
force-movable ref — whose message names the release, its change class for
contract content (NONE), and the authority it was cut on. That is the shape of
every tag since `wallet-v1.0`; `wallet-v1.4`'s is the model
(`b7b0fbb3`, "Change class NONE for contract content. Tagged by the coordinator
… on Brett Heap's word").

**Who performs it:** the lane coordinator (lane `hermes-wallet-exercise`), on
Brett Heap's word, AFTER the human merge. It is not this slice's act: the tag
addresses a commit that does not exist until the merge, and pushing a tag is an
`[OPERATOR]`-class act in this repository. The realization slice therefore lands
four of the five values and leaves the fifth to the cut.

## 7. Corrections to the change's own record, found in realization

1. **design D5's estate search was incomplete by one row.** It named this
   reader and openxFactory `specs/014-register-and-reader/data-model.md` as the
   only citations of the retired code. openXwallet's OWN Speckit feature spec
   `specs/014-per-seat-register-entries/spec.md` (FR-007, FR-008) is a third,
   and `tests/per_seat_register_entries/` carried a fourth (an assertion, which
   would have gone red). Both are handled in this slice — the test converted,
   the spec carrying AMENDED/SUPERSEDED notes — and the CHANGELOG's migration
   note records all four rather than the two the design measured. Nothing about
   the RULING changes: no consumer outside this repository pins the string, and
   openxFactory's gate matches `register-*` by wildcard.
2. **Two probes asserted the retired code, not one.** Design D4 named
   `self-test/register-minimal-shape-exceeded`; `self-test/seat-keys-do-not-raise-the-cap`
   asserted the same code and is removed with it.

## 8. What this slice does NOT do

- No tag is created or pushed (§6 above).
- No register is written: `governance/review-authority/register.yaml` is
  openxFactory's file and a permanently human-only surface.
- No consumer pin advances: openxFactory tasks 2.7–2.9 (this change's §5.1–§5.3).
- The Q-WRR-3 absence flip does not ride this release.
- The archive gate (§6) is untouched: `add-per-seat-register-entries` archives
  FIRST, and this change archives only on merged + green realization evidence
  INCLUDING the openxFactory pin advance.
