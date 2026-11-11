# Tasks: Factory/workload binding

Sole executable task list for openxFactory change `add-workload-factory-binding`.
Candidate implementation commissioned 2026-11-11; exact profile ratification and
live qualification are outside this list. Tier tags are retained for shared
workflow compatibility; Codex executes these tasks directly.

## Phase 1: Governance and design

- [X] T001 [O] Record draft composition and ownership handoff.
  files: openxFactory change packet; spec.md; plan.md; research.md
  verify: OpenSpec strict validation and ownership check.
- [X] T002 [O] Define candidate data/API boundary and requirement coverage.
  files: data-model.md; contracts/adapter-api.md; checklists/requirements.md
  verify: review trusted inputs, no pin/schema/approval expansion, no unresolved markers.

## Phase 2: Foundation

- [X] T003 [S] Add bounded strict JSON/crypto helpers and fresh exact OIDC verification.
  files: scripts/workload_factory_binding/evidence.py; tests/factory_binding/test_binding.py
  verify: issuer/algorithm/claim/key/time refusal matrix.
- [X] T004 [S] Add private durable atomic replay ledger.
  files: scripts/workload_factory_binding/ledger.py; tests/factory_binding/test_binding.py
  verify: restart, token/challenge reuse, concurrent reservation and unsafe-state tests.

## Phase 3: US1 - Current bounded factory authority

- [X] T005 [O] Add current policy, wallet and complete ancestor checks.
  files: scripts/workload_factory_binding/gate.py; tests/factory_binding/test_binding.py
  verify: every scope/audience/expiry/posture/revocation mutation refuses with zero sign calls.

## Phase 4: US2 - Independent evidence before signing

- [X] T006 [O] Add artifact observer and challenge/request-bound proof gate.
  files: scripts/workload_factory_binding/evidence.py; scripts/workload_factory_binding/gate.py
  verify: real signature checks, changed composition/run/source/request, post-sign state change and consumed outage.
- [X] T007 [S] Add exact-source owning primitive/custody integration.
  files: tests/factory_binding/test_owner_integration.py; tests/factory_binding/fixture_role.py
  verify: mTLS sign success, direct worker sign denial, own verifier proof acceptance, separate observer.

## Phase 5: US3 - Isolation and verification

- [X] T008 [S] Qualify success/failure cleanup and wire offline candidate tests into CI.
  files: tests/factory_binding/; requirements-workload-binding.txt; .github/workflows/pytest-suite.yml
  verify: fixture processes stopped and ephemeral key/state directory removed; offline suite executes in CI.
- [X] T009 [O] Reconcile design/evidence and run affected/full offline gates.
  files: analysis.md; evidence.md; quickstart.md; AGENTS.md managed feature block
  verify: full adapter gates; factory packet strict validation; git diff --check; no protected pins/artifacts changed.

## Dependencies and implementation strategy

T001 -> T002 -> T003/T004 -> T005 -> T006 -> T007 -> T008 -> T009.
US1 yields bounded authority checks; US2 adds signing only after full evidence;
US3 qualifies those together. Independent issuer/ledger tests may run in parallel;
source mutations remain sequential. No second OpenSpec implementation checklist.

## Acceptance outside this candidate

No checkbox here ratifies the profile, qualifies real GitHub OIDC or a deployed
independent supervisor, enrolls a human broker, clears pilot T002, publishes a
release or authorizes an external effect.
