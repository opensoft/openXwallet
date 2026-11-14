# Implementation Plan Extension: Protected Hosting and Issuance

Status: draft
Kind: plan
**Branch**: `017-hosting-issuance-plan` | **Date**: 2026-11-14
**Spec**: [feature specification](spec.md); [canonical plan](plan.md)
**Factory owner**: `opensoft/openXfactory`, `openspec/changes/add-protected-runtime-hosting-issuance/` (draft)
**Implementation owner**: existing feature 017 [tasks](tasks.md), proposed T012N-V; no duplicate executable list

## Summary

Prepare a source-only realization of actual hosting/issuance/readback over accepted
#65/#66, with the recommended T013 QA design as its planning basis. A new static-v2
plan resolves the discovered dependency on unknown run/process composition and
policy digests. Preflight remains read-only and plan-limited; only the protected
phase can request independently authorized staging, measured finalization and
existing full runtime/proof admission. No source code or operational binding changes now.

The user's instruction commissions this proposal/plan only. It neither ratifies the
new v2 policy nor commissions implementation, appoints reviewers/admins, issues
credentials, authorizes token mint/setup/dispatch, or completes T013/T014/T015.

## Technical Context

**Language/Version**: proposed Python 3.12 on Linux; Ubuntu 24.04 LTS is the deployment candidate, exact image/executable/source hashes are later independently accepted inputs.
**Primary Dependencies**: retain the accepted hash-locked Python closure, crypto/standard-library TLS and existing proof/custody clients. New SDK dependencies require a separately reviewed lock update; use bounded fixed-origin REST clients where possible.
**Storage**: explicitly initialized private POSIX managed-disk state for dispatch/authority/replay/staging/finalization; no network-file SQLite, silent creation or active-scope rollback. Independent initialization receipts and current identity/recovery readback remain required.
**Testing**: deterministic pytest/actual local RSA-TLS/process measurements/owning proof and independent cleanup; extend the reviewed fixed matrix only in later implementation. Existing offline gates remain offline.
**Target Platform**: three proposed QA Linux hosts plus an independently administered external watchdog capability before automatic infrastructure expiry/control-host-loss cleanup can be accepted. No existing bench/shared AKS deployment is selected.
**Project Type**: opt-in internal factory runtime adapters and trusted hosting services; no neutral protocol fork, public general-purpose service or worker-selectable plugin.
**Performance Goals**: accepted 5-second connect/10-second bounded RPC decisions, bounded current readback and no stale authority; proposed staging has at most six status reads within 60 seconds and the earlier case/grant/lease limit. No hard realtime host scheduling claim.
**Constraints**: three inputs, seven service roles, eight source roles, first attempt only, unchanged full runtime/proof checks, at-most-one dispatch/start attempt, fixed safe errors and no raw secrets/reports.
**Scale/Scope**: one proposed machine-possession case, 30-minute case window, maximum three small VMs/24-hour resource envelope and proposed US$50 ceiling; actual UTC window/SKU/capacity/pricing/watchdog references remain gated, not guessed.

## Constitution Check

Pre-research and post-design result: PASS for preparation within the declared scope.
The adapter has no local `.specify/memory/constitution.md`; none is fabricated.
Apply repository AGENTS.md and the shared OpenSpec/Speckit protocol, plus the
factory's existing constitution principles as governing composition context
(factory constitution v1.0.0 currently has draft status; this plan does not ratify it).

- Factory governance precedes code: the new profile is a draft proposal; first implementation task requires actual source acceptance and explicit commissioning.
- Neutral ownership: preserve proof/registry/custody APIs and assembly/code pins. Any need for hardware-only custody or stronger neutral assertion goes upstream.
- Fail closed: missing current provider/guest/issuer/state/lease/hold facts refuse; v1/default behavior remains unchanged.
- Evidence discipline: observed source/fixture results remain distinct from live provider/guest/protected acceptance; no credentials, tokens, raw provider documents or host-absolute paths enter committed artifacts.
- Scope: documentation planning only now; separate source realization, T013 selections/authority, T014 qualification and T015/human/domain acceptance.

## Project Structure

### Documentation

The canonical feature files remain spec.md, plan.md, research.md, data-model.md,
quickstart.md and the sole tasks.md. This bounded extension adds:

- [hosting research](hosting-issuance-research.md): source constraints and decisions.
- [model/state transitions](hosting-issuance-model.md): static plan, staging and final ownership.
- [internal interfaces](contracts/hosting-issuance.md): proposed v2 shapes/provenance/bounds.
- [selection basis](hosting-issuance-selections.md): observed facts, proposed values and mandatory later readback.
- [acceptance matrix](hosting-issuance-acceptance.md): independently falsifiable source/live controls.

### Proposed source areas, not created by this plan

- `scripts/workload_factory_binding_runtime/hosted/`: static-v2 validation/finalization, phase-limited admission, authenticated provider/guest/issuer clients, stage/final registration and safe hosting composition.
- Existing `bootstrap.py`, `workflow.py`, `github_bootstrap/`, `supervisor.py`, `launch.py`, `custody.py`, `state.py`, `lifecycle.py` and evidence/CLI/workflow integration: only explicit new opt-in seams; preserve v1/default and proof policy.
- `tests/runtime_binding/test_hosted_*.py` and `matrix_contract.py`: later substantive fixtures/negatives and reviewed counts/fingerprints; no test manifest regenerated by CI.

The same feature owns proposed deployment service units/host agents and selected
HTTPS wrappers. No listener, provisioning file, activation flag, runnable deployment
recipe or dependency change is introduced now. Exact module splitting is an
implementation choice within the documented closed boundaries, not a new task owner.

## Phase 0 — Research decisions

[Research](hosting-issuance-research.md) resolves technical design choices: static-v2
rather than unknown v1 hashes, plan-only preflight rather than effectful admission,
acknowledged staging cleanup before start, immutable full-plan takeover, actual
bounded provider/guest/issuer provenance, host-root/MI limits, software Ed25519
custody, HTTPS admission ingress and truthful watchdog/source-hold limits.

Remaining operational values are explicitly future-gated inputs, not technical
fallbacks or unresolved defaults. In particular unsupported current provider fields,
watchdog/conditional retirement support or network reachability make the eventual
deployment ineligible; they never permit an alternative weaker proof path.

## Phase 1 — Design and integration

### 1. Static-v2 and phase readiness

Build/validate the plan without a run or process. Commit every static field and
exact templates/derivation rules. Only four full-configuration paths are absent:
launch.run_id, launch.run_attempt, composition_digest and authority.policy_digest.
Preallocate state/lifecycle/grant handles; if that cannot be done, require another
explicit versioned decision rather than exempt a whole object. Existing static-v1
and runtime-v1 readers do not accept this plan. The new phase graph and closed
plan-readiness record emit only the approved existing environment before review.

### 2. Protected staging and finalization

After protected identity and actual environment review, recheck current plan/source/
hold/protection and separate narrow launch authority. Persist and acknowledge a
staging lease and exact host-managed unit/cgroup generation before one start call.
The worker is inert, unprivileged and unable to reach proof/control credentials.
Lost acknowledgement/start result permits only bounded read/reconciliation of the
same nonreusable ref; no second start. Deadline/status limits never renew authority.

Measure actual generation/artifacts/projection, derive composition then policy then
full configuration. A separate current authority recomputes complete canonical
bytes. Register a new immutable final plan/lease and full-config-bound state/custody/
operation scope. Keep staging ownership until independent final takeover readback
acknowledges the same generation without a deadline extension. Only then call
unchanged full admission and owning proof. Failure at every step retains cleanup.

### 3. Actual hosting and issuance

Use explicitly selected bounded GitHub, Azure ARM, guest-agent, operator/authority,
issuer and scheduler clients. Each fact has a real provenance source as mapped in
[interfaces](contracts/hosting-issuance.md). No callback may echo the candidate.

Broker/read Apps and role credentials are separate. Source reader may need Contents
read in addition to Actions read; no runtime Contents write/admin. A privileged local
credential broker enforces actual caller UID/capability, not a client-ID parameter.
The worker VM has no assigned identity. Trusted-host IMDS/key access restrictions
must be measured and tested; different UAMIs do not isolate cohosted processes.

Propose a version-pinned Key Vault RSA signing integration for App JWTs and exact
installation token exchange/retirement; live issuance remains separately gated.
Current wallet Ed25519 stays software custody in the owning service. Enrollment
requires independently authenticated actual host/source/nonce/key fingerprint,
not a CSR or self-written deployment manifest. Installation/RunCommand/enrollment
are future writes and never used as preparation/readback shortcuts.

### 4. Readback, hold and cleanup

Require explicit complete protection fields and branch-versus-tag provenance.
The observed can_admins_bypass extension is required typed data, not a documented
vendor guarantee or a default false; unsupported observations refuse. Current ref/
ruleset reads plus an authenticated coordinated hold support trusted coordination,
not atomic main pinning or resistance to malicious administrators.

Control-host janitor must survive worker/gate/runner death. A separately administered
external watchdog outside all three hosts is a deployment prerequisite for control-
host-loss cleanup and automatic 24-hour infrastructure expiry. Actual service refs
and operational scope remain unselected. Missing capability blocks those claims/setup;
no existing bench or extra budget is silently selected. Infrastructure retirement
has a separate exact-generation/conditional-semantics plan; never delete a whole
resource group containing retained state or call read-then-delete atomic.

### 5. Qualification and protected report

Connect later live qualifier/cleanup clients to accepted proof/denial/replay and
fault paths, never substitute offline pytest for the protected operation. Add a
separately versioned protected-machine report only after actual approved provider/
guest/issuance/source/run/case/cleanup evidence exists. Old source/fixture reports
remain unchanged and cannot be relabeled. Any new closed report/case vocabulary
needs explicit factory source review and owner acceptance in this slice.

The v2 read budget is explicit: existing ProviderReader correlation remains four
requests/two job pages; added protection, source/graph and hold/control callbacks
are capped at three/four/two reads respectively (aggregate 13) under one unchanged
enclosing wall/monotonic deadline. Unsupported pagination/complexity refuses; no
counter reset, omitted fact or stale reuse makes the positive path fit. Source
acceptance must exercise the complete positive path and each budget exhaustion.

## Phase 2 — Proposed implementation order

Proposed T012N-V in [tasks.md](tasks.md) serialize owner acceptance, versioned
finalization, issuance/host boundaries, provider/hold readers, actual hosting,
staging/final cleanup, qualifier/reporting, isolated conformance and final source
review/handoff. They are all unchecked and uncommissioned. Before implementation,
run Speckit consistency analysis and resolve critical findings; no automatic apply
follows the planning tool's artifact-complete status.

## Complexity Tracking

| Addition | Why necessary | Simpler alternative rejected |
| --- | --- | --- |
| Static-v2 and plan-only preflight | Actual run/process hashes cannot be precommitted | Dummy v1 hashes, predicted IDs or broad omission violate accepted authority |
| Staging grant/lease plus immutable final takeover | Must launch before actual composition exists without orphaning cleanup | Fake full-config digest or overwrite of an active RunPlan loses provenance/ownership |
| Concrete issuer/provider/guest clients | Types and copied JSON do not authenticate deployment | Self-written readback labels cannot qualify the real boundary |
| External watchdog requirement | Three-host control loss otherwise defeats autonomous expiry | Same control-host janitor cannot prove its own survival |

## Validation and limits

Apply [acceptance matrix](hosting-issuance-acceptance.md) with independent positive
controls, crypto-sensitive negatives, actual process generation, owning proof and
independent cleanup. Preserve existing tests; update only intentional new module
counts/fingerprints/anchors under review. Required native conformance permits zero
missing/deselected/skipped/non-passing cases. Source, CI, live readback, deployment,
protected qualification and owner/human/domain acceptance remain distinct.

Proposal/publication verification uses `python3 scripts/validate-openspec-cli-pin.py --all`
in each consuming repository, in its default pinned-artifact form, plus document/source
consistency checks. Raw CLI diagnostics are not the adjudicated corpus verdict.
No runtime/provisioning implementation, token request, dispatch or live qualification
is performed now. T001/T013/T014/T015 and every operational stage remain ungranted;
feedback stays deferred and neither historical blocked write is replayed.
