# Implementation Plan: 014-per-seat-register-entries

**Feature**: wallet-v1.2 — the register's top level is read, and per-seat keys
are enforced. **Governing change**:
`openspec/changes/add-per-seat-register-entries/` (Status: draft, held for Brett).

## Why there are only three artifacts here

No `data-model.md`, `research.md`, `quickstart.md` or `contracts/`. Feature 013
carried them because it changed a SWEEP whose behaviour a consumer had to be
taught. This feature adds no contract, no schema, no new document kind and no
consumer-facing procedure: the data model IS `REGISTER_SEAT_FIELDS` and its
projection-completeness table, which lives in the governing change's `design.md`
D7 where the decision was made, and duplicating it here would create a second
place for it to go stale. The research is the governing change's `## Context`.
Recorded so the absence reads as a judgement rather than an omission.

## Technical context

One file changes: `scripts/validate-openxwallet.py`. It is in openxFactory's pin
`pinned_by_commit_only:` list, so this is a COMMIT move and never a digest move —
which is what makes the release additive.

Stack: Python 3.12, PyYAML, jsonschema, rfc3339-validator, pytest. Offline: no
check reads the network, an upstream tree, or `contracts/manifest.yaml`.

## The seam

`check_register` gains two helpers and one closure check, in this order, because
the order is what makes a refusal legible:

1. `register_version` (existing) — a version this reader does not know stops
   everything else.
2. **Closure** over `REGISTER_TOP_LEVEL_FIELDS` — an unrecognized key.
3. `_check_staleness_bound` — present, well-formed, non-zero.
4. `rows` shape and the positive read NOTE (existing).
5. The single-row cap (existing, refusal text re-grounded).
6. `_check_seat_keys` — the new surface, which builds its own index of
   ROWS USABLE AS AUTHORITY (exact field set, `state: active`, unexpired by
   computed time) so a row this reader has already refused is never promoted to
   an authority by being merely present.
7. Attestations and the row loop (existing, untouched).
8. The headline grant obligation (existing, untouched).

`_check_seat_keys` counts entries ADJUDICATED CLEAN by comparing the error count
before and after each entry, so the note it emits is evidence rather than a
restatement of `len(entries)`.

## Testing strategy

Two layers, deliberately:

- **The validator's own `self_test()`**, extended in the S4 `_register_probe`
  style: one probe per new refusal, plus a POSITIVE probe over the four real
  public halves and an assertion that each recomputes. This layer runs inside
  EVERY consumer's pinned invocation, so an invariant that matters to a consumer
  is pinned where the consumer runs it. `_s4_tree` gains a `top=` parameter and
  now writes the required staleness bound, which is why the nine existing probes
  keep their expected code sets unchanged.
- **`tests/per_seat_register_entries/`**, subprocess-driven, so the exit codes
  the workflows act on are the ones under test. Every negative asserts a NAMED
  CODE rather than a non-zero exit: a refusal for the wrong reason is a
  different defect wearing the same colour.

One existing fixture changes:
`tests/nested_repo_prune/test_prune_and_register_note.py::_register_tree` now
declares `revocation_staleness_bound`, because a register without it is no longer
a readable register and a fixture that pretended otherwise would test a shape no
consumer can commit. wallet-v1.1's two behaviours are unchanged and still
asserted.

Corpus invariance is already covered by that suite's
`test_the_previous_version_adjudicates_the_corpus_identically`, which recovers
the previous validator from git and refuses to compare a blob against itself.

## Release (five coordinated values)

| Value | This release |
| --- | --- |
| per-file `contract_schema_version` | unchanged — no contract file is touched |
| `contract_bundle_version` | `wallet-v1.2` in `contracts/manifest.yaml` |
| annotated tag | `wallet-v1.2` — **`[OPERATOR]`**, after the human merge |
| release commit + per-file digests | the merge commit; the eight digests recompute to their recorded values, proven before release |
| `contracts/CHANGELOG.md` | the `wallet-v1.2` entry |

## Gate bar before pushing (AGENTS.md rule 5)

`scripts/verify-contract-pin.py`; `scripts/wallet-yaml-syntax-gate.py .`;
`validate-openxwallet.py` (self-test) and `. --strict`;
`python3 -m pytest tests/ -q`; `OPENSPEC_TELEMETRY=0 openspec validate --all
--strict`. Plus the two proofs this feature owes: the digest recomputation, and
an adjudication of a COPY of openxFactory's live register tree carrying the four
real entries.

## Risks carried from the governing change

**R1** — the reader gets stricter on a file only a human may edit. Mitigated by
refusals that name the offending key and the expected shape, and by the positive
fixture being the exact bytes openxFactory will commit.
**R2** — the register becomes a key-distribution surface by habit. Mitigated by
the closed top-level set and by the 43-character canonical check, which refuses a
64-hex private seed by shape.
**R3** — four hand-copied keys. Closed by recomputation in two layers.
