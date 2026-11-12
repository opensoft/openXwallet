# Tasks: Protected Machine Runtime Qualification

Status: sole executable implementation list; issuer landed; T002 source candidate complete
Commission: 2026-11-12 owner ratification, issuer commissioning, then explicit
T002 implementation commissioning after #50. Operation stays separate. See [evidence](evidence.md).

## Owner Gate

- [ ] T001 [O] Obtain owner acceptance/source commissioning of the factory profile and explicit confined-gate trust model; files: specs/017-protected-runtime-qualification/evidence.md; verify: actual owner record names exact reviewed candidates/scope. The agent does not tick this owner act.

## US1 — Bounded Issuer Acquisition

- [x] T002 [O] Realize the factory-owned internal operational grammar, runtime validator and protection/source binding; files: scripts/workload_factory_binding_runtime/config.py, tests/runtime_binding/test_config.py; verify: missing/pending/floating/worker-selected trust or service input refuses; no consumer executable lock is published. Source candidate only; grammar/source review precedes runtime use, authenticated live readback acquisition and deployed acceptance remain later hosting gates.

T002 now supplies a closed bounded internal grammar, independent approval digest
and fresh exact readback binding under the trusted embedding boundary. Factory
governance owns its concrete grammar; it is not a canonical neutral contract.
No real service/protection selection, authenticated provider client or deployed
qualification is supplied by its synthetic tests. T001's actual human act remains
recorded; its owner checkbox stays unmarked by the agent.
- [x] T003 [O] Add opt-in bounded issuer fetch, freshness/coalesced refresh and accepted verifier adapter; files: scripts/workload_factory_binding_runtime/issuer.py, scripts/workload_factory_binding_runtime/transport.py, scripts/workload_factory_binding_runtime/_https_worker.py, tests/runtime_binding/**; verify: I01-I03/I05 and signed-claim I04 vectors pass, with no unapproved endpoint, stale fallback or network in existing offline gates. Landed #50; P01 deployed source/protection/service acceptance remains pending.

Independent acceptance: issuer evidence verifies through the unchanged core; failure precedes any signer.

## US2 — Trusted Runtime Composition

- [ ] T004 [O] Connect authenticated current-record/challenge loaders and trusted hosting context; files: scripts/workload_factory_binding_runtime/loaders.py, tests/runtime_binding/test_loaders.py; verify: G01, service/source identity and canonical request binding; no worker-selected data/URL/loader.
- [ ] T005 [O] Compose exact launch/protection/source preflight with existing ProofGate; files: scripts/workload_factory_binding_runtime/runtime.py, tests/runtime_binding/test_runtime.py; verify: each I04/P01 binding independently refuses when wrong/absent; worker booleans confer no authentication.
- [ ] T006 [O] Integrate independent supervisor observation and actual launch measurement; files: scripts/workload_factory_binding_runtime/supervisor.py, tests/runtime_binding/test_supervisor.py; verify: G02 and worker control-plane/key/policy denial; fixtures retain fixture-only scope.
- [ ] T007 [O] Bind confined gate deployment/credential to the owning signer; files: scripts/workload_factory_binding_runtime/custody.py, tests/runtime_binding/test_custody.py; verify: G03 owning proof plus direct valid-preimage denial; new custody assertions refuse for upstream owner decision.
- [ ] T008 [O] Add expected-initialized state preflight and restart/recovery enforcement; files: scripts/workload_factory_binding_runtime/state.py, tests/runtime_binding/test_state.py; verify: S01, no silent reset, ambiguity stays consumed and no hostile-host/backup rollback claim.

Independent acceptance: one bounded owning proof; no approval/apply operation.

## US3 — Qualification and Handoff

- [ ] T009 [O] Implement run leases/finalizer and independent cleanup/readback; files: scripts/workload_factory_binding_runtime/lifecycle.py, tests/runtime_binding/test_lifecycle.py; verify: L01 success/failure/cancel; missing readback fails; shared resources remain.
- [ ] T010 [S] Wire substantive offline matrix and selected owning-source integration into conformance; files: tests/runtime_binding/**, .github/workflows/pytest-suite.yml; verify: required I/G/S/L/R cases collect with zero failures/errors/skips and no public issuer/provider credential use.
- [ ] T011 [O] Add safe errors, redacted scoped receipts and operator runbook; files: scripts/workload_factory_binding_runtime/evidence.py, specs/017-protected-runtime-qualification/quickstart.md, tests/runtime_binding/test_evidence.py; verify: R01 exact sources/case/results/cleanup with no raw sensitive material.
- [ ] T012 [O] Prepare protected qualification workflow after source acceptance; files: .github/workflows/protected-runtime-qualification.yml; verify: accepted immutable sources, protected environment, narrow OIDC permissions, trusted configuration, independent cleanup and manual dispatch. Workflow creation authorizes no setup/dispatch.
- [ ] T013 [O] Obtain operational selections and scoped setup/dispatch authorization; files: specs/017-protected-runtime-qualification/evidence.md; verify: all operational-input categories have approved non-secret references and independent readback. This is an owner/operator act.
- [ ] T014 [O] Execute real protected machine qualification at accepted sources; files: specs/017-protected-runtime-qualification/evidence.md; verify: P01/deployed G02/G03/L01, real issuer/independence/confinement and fresh cancellation/cleanup; missing facts stay blocked/not-performed.
- [ ] T015 [O] Deliver accepted machine-only receipt to codeXfactory 058 T002; files: specs/017-protected-runtime-qualification/evidence.md; verify: owner acceptance names evidence/pins; human/domain gates remain separate.

## Dependencies

T001 -> T002/T003 -> T004/T005 -> T006/T007/T008 -> T009/T010/T011 -> T012 ->
T013 -> T014 -> T015. US1 is the smallest useful slice. No parallel-agent
implementation is required. Factory governance and consumer handoff duplicate
no implementation list. Future paths are proposed; reconcile them against
reviewed code during commissioned implementation without widening scope.
