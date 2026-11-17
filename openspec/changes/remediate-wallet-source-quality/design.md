## Context

The source acceptance at main 835f92c5890ec03eac1e72f3c34c5b95f0504093 is complete; this is a new maintenance cohort under issue #82. See proposal.md for the authorized scope. The existing complete assembly includes four repositories and immutable shared-provider conformance.

## Goals / Non-Goals

Goals: reduce every actionable original finding through reviewed owner repairs with evidence-bound consumer publication and actual-main acceptance.

Non-goals: new wallet/authority/runtime behavior, changed release artifacts, feature-017 ratification or activation, scanner waivers, altered baseline/profiles/thresholds, source omissions or billing changes.

## Decisions

- Freeze exact keys and source revision before work. Rule/severity summaries support prioritization but do not replace per-key evidence.
- Repair provider-owned and shape-pinned files upstream. Re-publish actual source and coherent gitlinks/pin metadata; preserve package/release identities and artifact digests.
- Make behavior-preserving changes in bounded cohorts. Preserve assertion predicates and intended exception targets; preserve shell support, quoting, integer handling, statuses and side effects.
- Keep coverage tied to executed physical files and unchanged complete source scope. Retain all existing native identities and budgets, provider assertions and matching full/partition collections.
- Treat intentional contracts explicitly. A non-actionable key requires reviewed semantic evidence and stays visible without issue-status waivers.
- Use normal reviewed landing and exact-head/main evidence. Previous successful PRs or local runs do not substitute for the published main result.
- Keep the #73 history distinction: ten exported original identities, nine live and one captured-metadata-only record. The selected August baseline remains live; archived metadata cannot qualify current checks.

## Risks / Trade-offs

- Bash conditional rewrites can alter glob/word-splitting or integer behavior -> inspect declared shells and validate actual supported inputs before consumption.
- Complexity extraction can change evaluation order, cleanup or refusal boundaries -> retain existing APIs and prove relevant paths with existing meaningful regressions.
- Shared copies can drift -> bind consumer bytes, provider revisions and immutable conformance together.
- Large historical debt can hide new findings -> keep exhaustive original-key accounting and separately audit newly introduced unresolved issues.
- Parallel feature work can advance independently -> isolate maintenance worktrees, preserve PR #78 and existing sessions, and reconcile only this task's reviewed changes.

## Migration Plan

Land owner fixes before coherent consumers. Preserve source and failed checkpoints; rollback uses a normal reviewed revert/pin update rather than rewriting history. No deployment follows this source maintenance. The only executable adapter list is specs/020-sonar-backlog/tasks.md.

## Bounded implementation-time finding: synthetic pytest discovery

The full local run at e43d2b1 passed 2,416 cases plus 11 subtests but failed 18 cases. Twelve were synthetic conformance-child timeouts; the unchanged accepted main reproduced that timeout. A phase probe located it in pytest collection. Setting confcutdir to the synthetic fixture's already selected root changed the control result from the unchanged 20-second timeout to PASS in 0.5 seconds.

The self-test child now explicitly fences discovery at that fixture root. This enforces its existing tiny-corpus contract without changing production ConformancePlugin, audit counts/phases/digests, native runner/matrix/isolation files or any time limit. All twelve passing/refusing mutation cases must still behave as declared. Six worker-startup failures remain diagnostic until renewed focused/full qualification; accepted-main and candidate replay already differ nondeterministically, so no source cause is claimed for them.


B01 coverage correction: retain the complete existing native contract and extend
its two existing invalid-Python-option cases to exercise the same launcher
refusal function directly under measurement. Scoped module doubles fail and
record any attempted OS, ctypes or sandbox effect; status and both output
streams must show a quiet pre-effect refusal. The original subprocess/kernel
checks continue to run. This repairs observed missing coverage rather than
changing measurement, runtime checks or operational authority.
