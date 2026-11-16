## Context

The wallet assembly exposes provider files to static analysis. The repair is authorized by openXwallet #73 and must preserve independent ownership, published history, live sessions and current acceptance matrices.

## Goals / Non-Goals

Goals: fix original findings naturally, retain full test execution, verify published source and the unchanged quality gate.
Non-goals: operational activation, new billing, rule suppression, reduced scope or thresholds.

## Decisions

Repair shared tooling at its original owner and consume byte-identical published versions with recorded provenance. Never edit a shape-pinned copy or invent a provider digest.
Use complete hash-pinned wheel closures for CI installs; execute local source without installing its build backend.
Preserve the negative fixture's identity and refusal class using deliberately invalid private-material placeholders; record provenance without exposing old bytes.
Use executed-test coverage for actual scanned paths. Retain all source scope and existing gate conditions. Choose the oldest retained main analysis as the candidate baseline to avoid hiding retained changes; verify the selected revision remains an ancestor.
Keep one executable task list in the paired Speckit feature. OpenSpec is governance and handoff only.

## Risks / Trade-offs

Unrelated main movement can invalidate pins or evidence: re-read exact heads before merging and verifying.
Automatic analysis omits coverage: replace it with CI-based complete-source analysis using the existing organization secret once the pipeline is qualified.
Historical fixture provenance may remain uncertain: do not test old material against a live provider; preserve the commit and only record safe fingerprints.

## Migration Plan

Land provider fixes, then consuming legs, then the neutral root and adapter pins. Require exact-head tests and independent review. Verify the published main analysis, all eight original finding keys and all original gate conditions. Revert through ordinary reviewed commits if acceptance fails; preserve tags and historical analyses.

## Open Questions

Fixture provenance and final retained-baseline ancestry are verification tasks, not inferred approvals.


## Measurement execution decision

Preserve Python 3.12 full/native runtime acceptance without instrumentation.
Collect the same complete full test selection separately under Python 3.14
SysMonitor, with an analysis-only hash-verified wheel closure at unchanged package
versions. Keep both job caps at 45 minutes and retain all original resource and
network boundaries. No test selection, expected failure or skip may qualify
either full run; fetch full Git history to execute the existing historical seat.

Require exact node identities and passing ordinary/subtest phases to match.
Record and require actual parent/child SysMonitor collectors and interpreter
versions. A real cross-version calibration must preserve source identity, branch
hits and zero-hit files; generate the final report under target Python 3.12. Both auditors require
its complete executable-line universe; the 3.14 auditor invokes the real 3.12
compiler and additionally verifies its own statement set is a subset. Keep the declared Sonar target Python 3.12.
This measurement choice supplies no Python 3.14 runtime acceptance or authority.

The untraced runtime, measured full suite and auxiliary conformance source
snapshots must all match. Retain failed CTracer checkpoints and complete verified
coverage artifacts before introducing the Sonar credential. No excluded source,
line/arc filtering, fabricated hits, threshold reduction or billing change follows.


Python 3.14 lazy annotation compilation differs from the target's executable-line
universe. Preserve the 3.12 denominator and collect actual 3.12 module imports
separately from timed assertions. This adds genuine execution data, without
synthesizing annotation hits or relaxing either complete full test run.
