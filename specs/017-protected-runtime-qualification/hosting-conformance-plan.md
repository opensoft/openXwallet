# T012U isolated conformance and operator source runbook

Status: commissioned; implementation and fresh qualification pending
Kind: implementation-plan
Scope: T012U only; source/fixture conformance and documentation
Governance: openXfactory add-protected-runtime-hosting-issuance, with accepted report and qualification-budget amendments
Sole executable list: tasks.md, T012U

Brett commissioned implementation/testing of T012U after isolated T012T completed
at runtime b7049e8ef20f985db26e5b7a966012161737ac7e and documentation child
49a1202d4294a22f7ab9713cbab32e43eb0da769. Existing native collection has2,203
nodes, including186 hosted-evidence cases; H01-H12 anchors are already present.
This commission grants no publication, workflow timeout change or operational act.

## Bounded realization

Retain every old node, fingerprint and anchor. Extend the existing conformance
self-tests with actual tiny pytest subprocesses proving final owning-source
checks occur after all setup/call/teardown and before the final success verdict.
The current runner prints PASS before its final owning-source check; an owner
failure can therefore coexist with a success banner. Correct only the test runner's
verdict ordering and safe postflight failure handling. Preserve the existing
small-corpus mutation controls and all production CLI arguments. Add no manifest,
selector, plugin, provider API or runtime/report contract.

Reconcile qualification-matrix.md and quickstart.md to implemented H01-H12 source
coverage. Provide a focused operator source runbook with exact source/owner checks,
reviewed dependencies, existing isolation bootstrap, measured collection/all-phase
verdict, preserved diagnostics and independent exact-generation teardown. Keep
commands restricted to offline source tests; no setup, OIDC, token mint or dispatch
command is supplied. Record remaining live/admin/watchdog/infrastructure and
human/domain/consumer gates honestly.

## Validation and handoff

First reproduce the premature-success bug with the new controls against unchanged
source, then require the controls to pass after correction. Measure the added
collection and update only its reviewed module count/fingerprint and appropriate
source-result anchors. Run ordered pin/YAML/plain/strict/full/pinned OpenSpec gates,
then required native conformance with explicit clean owning source, loopback only,
nonroot UID, no groups/capabilities, no-new-privileges, clean environment and
read-only source. Freeze exact source identities before qualification; do not
regenerate expectations in CI. Audit process generations and retirement/preservation
in the correct namespaces before removing only owned fixture roots.

Mark T012U complete only after those actual results, reconcile documentation and
prove executable inputs unchanged by final documentation-only completion. Keep
failed/interrupted runs diagnostic. Local timings do not qualify the unchanged
45-minute hosted source CI job; actual hosted budget assessment and publication
remain T012V. T001/T013-T015, setup/dispatch and live acceptance remain unauthorized.
Feedback stays deferred; neither historical blocked write is replayed.
