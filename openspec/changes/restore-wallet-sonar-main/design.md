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

Preserve the unchanged Python 3.12 full/native runtime acceptance without
instrumentation, including its 45-minute cap, complete case selection and
original assertion, resource and network boundaries.

Measure every assertion through a fixed complementary partition. The main
measurement uses Python 3.12 / CTracer for every case except the exact committed
large-manifest lifecycle case. The second uses Python 3.14 / SysMonitor for that
one case. Both collect the entire tests/ inventory. Record complete collection,
selected and complementary deselected node identities, actual parent/child cores,
passing phases and subtest message/parameter identities. Require identical full
collections, disjoint selected sets whose union equals runtime, exact expected
complements, and identical passing assertion records for every case. No assertion
may be omitted, waived, skipped or expected-failure in the complete union.
Partition membership is fixed in source, never an arbitrary operator override.
Provider conformance still prohibits any deselection.

The main measurement cap stays 45 minutes; the isolated measurement has its own
45-minute cap. Fetch full history to execute the existing carve-history seat.
The analysis-only 3.14 wheel closure retains all runtime package versions.
All four source jobs must pass before analysis. Their source/config snapshots
must match. Retain actual raw branch shards and failed diagnostic checkpoints.
No source exclusion, line/arc filtering, invented hit, filename remapping,
threshold reduction, runtime compatibility claim or billing change follows.

Generate the production report under Python 3.12 and retain its complete
executable-line denominator. The secondary 3.14 audit invokes the actual
operator-selected 3.12 compiler and also checks its local inventory is a subset.
Real cross-version calibration checks same-name identity, differing branch hits
and zero-hit annotation preservation. Keep declared Sonar target 3.12.

## Preserved qualification experiments

The earlier all-CTracer full run failed only the large-manifest timed case.
That case passes untraced 3.12 and separately measured 3.14 SysMonitor with its
original fixture bytes. A complete 3.14 run exposed stricter synthetic-PKI
verification and additional unchanged hosted-launch deadline failures even
without instrumentation. A fixture-extension experiment cleared 41 authority
tests but did not resolve the separate runtime deadline; its private patch and
diagnostics remain retained. Original fixture bytes were restored.
The complete-3.14 approach is not accepted and is superseded by the fixed
complementary measurement above. Production runtime, fixtures, matrix identities
and all budgets remain unchanged. This does not commission feature017 work.

## Full-main repair decision (2026-11-16 America/La_Paz)

The main-only findings require explicit local non-null aliases/branches around
existing fail-closed state checks, plus refusal of an incomplete running unit
before worker observation. Add negative state regressions without changing any
accepted timing budget, resource/network control, native identity or authority.
The neutral service config CLI uses the invocation directory as its default
bounded root and a separate operator environment selection for other roots;
LLM-supplied config paths cannot establish their own root. Use descriptor-bound,
regular-file, bounded reads and refuse before registry/TLS/listener effects.
Preserve the existing cwd semantics for paths inside an admitted operator config.
Keep the current 18 package versions/hashes as a real canonical requirements.txt;
retain the old lock input as a compatibility include and keep wheel/hash checks.

Remove duplicate OpenSpec implementations through shared execution. Publish a
provider-owned explicit consumer-root API for verifier and installer, preserving
standalone defaults and separately configured operator authority. Keep the full
canonical scripts in the neutral spec. The adapter uses bounded wrappers over
that declared pinned spec implementation, verifies its revision and source bytes,
and binds its own pin/corpus context. It initializes the tooling spec leg
explicitly where needed, never fetching or falling back implicitly. Product
wallet validation keeps its existing code-leg boundary. Preserve independent
pins, locks, tarballs and corpora. Run every original provider assertion against
the actual canonical source in both consumer contexts, plus real wrapper
transport/refusal tests. Do not remove source from the coverage/analyzer
inventory or replace it with encoded/generated/opaque executable artifacts.

Requalify published provider, neutral leg/root and adapter heads, including all
original and five newly exposed finding keys, complete real coverage and all six
unchanged main gate conditions. Keep the first failed main scan as evidence.

## Final evidence reconciliation

The published main closeout verifies all 26 scoped keys, complete executed-test
coverage, the unchanged six conditions, coherent published pins and preserved
sessions/worktrees. Current evidence is linked from
[feature 019](../../../specs/019-sonar-main-acceptance/plan.md).

The final history audit distinguishes nine original records still live in
Sonar from all ten recorded identities retained in immutable exports. Exactly
one original server snapshot is unavailable; its exact identity and captured
original metadata are hash-bound to the frozen before export and original
capture. The deletion cause is not audit-proven. This is an explicit evidence
availability record: the August baseline stays live and selected, every other
original live identity remains required, and archived data cannot qualify any
current gate, coverage, profile or finding check. No historical snapshot was
recreated or backdated. Full historical source/measure export is not claimed.
