# Wallet Sonar backlog acceptance

Status: in progress under [issue #82](https://github.com/opensoft/openXwallet/issues/82), separately from completed #73.

The [frozen 1,505-key inventory](backlog-before.jsonl) comes from main 835f92c5890ec03eac1e72f3c34c5b95f0504093 and analysis d040c7d6-3dbb-4fc4-a182-68d0c7daef58. Its SHA-256 is 4e231282a251efc8c2203fdf38e3815a0f7c641713de9e8ec113af5f557c4bbe.

All entries were classified as code smells: 2 blocker, 125 critical, 1,342 major and 36 minor. Initial scanned-path ownership is openXwallet 481, openWallet root 966, openWallet-code 37 and openWallet-spec 21. Severity is a prioritization input, not proof of a runtime defect.

The [feature plan](../../specs/020-sonar-backlog/plan.md) defines owner-first reviewed batches and unchanged acceptance. The [task list](../../specs/020-sonar-backlog/tasks.md) records actual completion. Every original key must receive an evidence-backed disposition; every actionable key must be naturally analysis-fixed on actual main. Non-actionable decisions remain visible without suppressions or manual waivers.

All 26 previously repaired keys, the selected live August baseline, profiles, thresholds, full source scope, genuine coverage, native identities/budgets, active sessions/worktrees and frozen evidence remain acceptance requirements. The prior [history-availability limitation](sonar73-acceptance.md#historical-analysis-availability) remains explicit. Feature-017 PR #78 and operational decisions remain separate.

## Batch B01: adapter refusal and test precision

Candidate scope: 154 original keys (71 composite assertions, 82 ambiguous exception contexts and one duplicate launcher refusal return). The [per-key triage ledger](backlog-triage.json) distinguishes these candidates from the remaining 1,351 pending detailed review; no main fix is claimed yet.

All conjunction predicates/messages, comments, function signatures and decorators are retained. Exception setup is evaluated before the expected operation. The ruleset test now requires list-selection faults to fail in begin_control and detailed-rule faults in finish_control, preserving the two-request bound. The launcher has one documented common refusal exit; all eight actual malformed-input probes preserve status 2 with empty stdout/stderr.

All 2,434 ordered collected node IDs remain identical. Native matrix, runner, isolation and coverage-workload records are byte-unchanged. The four explicit branch/starred/ruleset test repairs pass all 18 parametrized cases in the existing restricted environment. Complete source/native/coverage CI, independent review, publication and main acceptance remain pending.

### Pre-publication review correction

Independent QA/reliability review found that five deliberately invalid-state tests must require ReadBudget reconstruction itself to refuse: its constructor immediately checks the original clocks and shared counters. The candidate's earlier constructor hoists escaped the exception scope. Those 15 parameter cases now target the single refusing constructor. The two staging-clock cases construct a valid budget before clock invalidation and then require both the existing operation and a reconstructed client to refuse.

The first focused candidate run is retained as an interrupted, unqualified diagnostic, including observed failures and its pytest interruption/teardown diagnostic. No production check was relaxed. All 17 affected parameter cases now pass in the same restricted environment. Renewed full qualification and exact-head review remain required after this correction.

### Frozen full-run diagnostics and fixture fence

At e43d2b1, the unchanged source run reports 2,416 passed, 18 failed and 11 subtests passed. Twelve failures are timeouts in unchanged synthetic conformance self-tests; six are worker-startup failures. Accepted main reproduces the synthetic timeout and a worker-startup failure, while a subsequent candidate worker replay passes. These remain unqualified diagnostics, not evidence of a clean full run.

The synthetic child now explicitly selects confcutdir at its existing fixture root. A controlled before/after probe changes only that boundary and passes in 0.5 seconds under the unchanged 20-second timeout. The production conformance plugin, mandatory native runner/matrix/isolation and all audit checks remain byte-unchanged. Both newly introduced mixed-case file-tuple locals are also renamed; whole-file alpha-normalized AST equality holds. Renewed focused/full and hosted main verification remain pending.

The renewed focused run passes all 76 selected cases, including all 18 full-run failures and the earlier constructor/special-case checks. Full final-head qualification and hosted main acceptance remain pending.
