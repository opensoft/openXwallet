# Paired PR review and corrected local qualification

Date: 2026-11-11. Candidate remains unratified.
PRs: [openXwallet #48](https://github.com/opensoft/openXwallet/pull/48) and
[openxFactory #1304](https://github.com/opensoft/openxFactory/pull/1304).

## Review provenance

The coordinator independently inspected the implementation and used the mandatory
nine-expert panel: architecture, performance, security, QA, static analysis,
API/contracts, persistence/integrity, reliability/concurrency and simplicity.
Initial review baselines were adapter ab49ea04bdd1 and factory 8927b9e51937.
Security, QA and integrity experts additionally checked the corrected working
delta with focused isolated probes. No unresolved actionable local finding remains.

GitHub Codex reviewed both initial exact heads and found the review-class authority
and missing corpus-ledger issues. The fixes below address both. Fresh exact-head
Codex review is explicitly requested after publication of this correction;
its receipt and hosted CI status belong to the PRs, not this local test record.

## Finding dispositions

| Finding | Correction and meaningful validation |
| --- | --- |
| GitHub optional x5t rejected | Accept typed optional metadata without using it for key trust; signed positive/negative cases |
| Backdated nbf rejected | Check iat and nbf independently, retaining bounded exp-minus-iat; GitHub-shaped positive cases |
| FIFO artifact open blocks | O_NONBLOCK plus regular-file checks; bounded subprocess FIFO regression |
| Present null parent truncates ancestry | Require a valid present parent reference; malformed-parent/refused revoked-ancestor cases |
| Worker configuration not bound | Verify actual clean owner revision, public transport/binding manifest and invocation context; freeze selected configuration; four drift refusals |
| Existing replay store silently reset | Initialize new files only; reject truncated/uninitialized existing state |
| Missing uniqueness constraints accepted | Verify exact schema/version/index constraints at startup and inside reservation transaction |
| Index contents lost while schema survives | Full startup integrity_check; corruption regression preserves table rows but empties both index leaves |
| Blocking validation crosses expiry | Carry issuer-key deadline and check fresh minimum deadlines after I/O, after reservation and before output |
| Clock exceptions escape error boundary | Fixed-code clock wrapper; outage/non-integer regressions |
| Canonical review-class rules bypassed | Refuse exact review act anywhere in the chain until canonical anchor/register composition exists; anchored/unanchored cases make zero sign calls |
| Pytest workflow does not parse | Quote the wheel-only command; parse all workflows and verify hosted workflow execution |
| Old lane gate rejects unlaned work | Realize in-force Amendment 21 using factory feature 041 precedent; preserve adapter Bot exemption/events/permissions; 21 behavioral/structural cases |
| Isolated quickstart misses dependencies/mounts | Complete pinned dependency file and explicit scoped neutral init; verify in a newly created environment |
| Factory corpus ledger misses draft row | Owning generator adds exactly one #1304 row; ledger consistency and affected factory suites pass |

## Corrected local result and cleanup

Fresh environment installed only the documented complete dependency file.
The complete adapter suite passed **456 tests, zero failures/errors/skips**, in
136.14 seconds: **154 binding cases**, **21 conditional-lane cases**, plus the
existing adapter suites. The affected factory suites passed **538 tests**.

Pin, syntax, plain/strict canonical validation and pinned adapter OpenSpec gates
pass. The new factory proposal passes pinned strict OpenSpec; the wider factory
corpus's already accepted exception is unchanged. No neutral pin, published
contract, release inventory, validation floor or disposition was weakened.

An independent post-suite audit found zero remaining fixture processes and zero
remaining ephemeral integration key/state directories. Host-local JUnit/audit
reports are retained outside the repositories under case paired-pr-review-final.

The source/test/workflow/dependency map uses relative paths and SHA-256 per file,
then SHA-256 of sorted compact JSON. Corrected tested digest:

`28898d615c509e430c8c9be598ffe09fe7ac63d6494ff9bbb3da8d026e383029`

This snapshot additionally includes the conditional-lane workflow and its tests.
The initial 405-test snapshot remains historical evidence in evidence.md.

## Acceptance boundaries

Hosted exact-head checks and Codex receipts are verified on the PRs after this
local record is committed. The profile stays draft pending Brett's ratification.
This is synthetic issuer/reference-process conformance, not live GitHub issuance,
protected environment assurance, hostile OS isolation, deployed supervisor
independence, production custody or human approval. T002 stays blocked.

Replay storage assumes a trusted host: full integrity validation at startup and
transactional schema checking do not resist live hostile byte changes, deletion
or valid-backup rollback. Such operational controls are a separate gate.
Feedback stays deferred; neither historically denied write is replayed.
