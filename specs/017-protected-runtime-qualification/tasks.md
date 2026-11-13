# Tasks: Protected Machine Runtime Qualification

Status: sole executable implementation list; T002–T011 landed; isolated T012 workflow preparation candidate
Commission: 2026-11-13 source ratification of #58 at 4916476364f7 and explicit
isolated T012 commissioning. Operation stays separate. See [evidence](evidence.md).

## Owner Gate

- [ ] T001 [O] Obtain owner acceptance/source commissioning of the factory profile and explicit confined-gate trust model; files: specs/017-protected-runtime-qualification/evidence.md; verify: actual owner record names exact reviewed candidates/scope. The agent does not tick this owner act.

## US1 — Bounded Issuer Acquisition

- [x] T002 [O] Realize the factory-owned internal operational grammar, runtime validator and protection/source binding; files: scripts/workload_factory_binding_runtime/config.py, tests/runtime_binding/test_config.py; verify: missing/pending/floating/worker-selected trust or service input refuses; no consumer executable lock is published. Source accepted at #1308/#51; authenticated live readback acquisition and deployed acceptance remain later hosting gates.

T002 now supplies a closed bounded internal grammar, independent approval digest
and fresh exact readback binding under the trusted embedding boundary. Factory
governance owns its concrete grammar; it is not a canonical neutral contract.
No real service/protection selection, authenticated provider client or deployed
qualification is supplied by its synthetic tests. T001's actual human act remains
recorded; its owner checkbox stays unmarked by the agent.
- [x] T003 [O] Add opt-in bounded issuer fetch, freshness/coalesced refresh and accepted verifier adapter; files: scripts/workload_factory_binding_runtime/issuer.py, scripts/workload_factory_binding_runtime/transport.py, scripts/workload_factory_binding_runtime/_https_worker.py, tests/runtime_binding/**; verify: I01-I03/I05 and signed-claim I04 vectors pass, with no unapproved endpoint, stale fallback or network in existing offline gates. Landed #50; P01 deployed source/protection/service acceptance remains pending.

Independent acceptance: issuer evidence verifies through the unchanged core; failure precedes any signer.

## US2 — Trusted Runtime Composition

- [x] T004 [O] Connect authenticated current-record/challenge loaders and trusted hosting context; files: scripts/workload_factory_binding_runtime/loaders.py, tests/runtime_binding/test_loaders.py, tests/runtime_binding/test_authenticated_loaders.py; verify: G01, service/source identity and canonical request binding; no worker-selected data/URL/loader. Source accepted and landed #52; real deployment authentication remains unqualified.
- [x] T005 [O] Compose exact launch/protection/source preflight with existing ProofGate; files: scripts/workload_factory_binding_runtime/runtime.py, tests/runtime_binding/test_runtime.py; verify: each I04/P01 binding independently refuses when wrong/absent; worker booleans confer no authentication. Source accepted and landed #52; real P01 and deployed supervisor/custody/state/lifecycle gates remain pending.
- [x] T006 [O] Integrate independent supervisor observation and actual launch measurement; files: scripts/workload_factory_binding_runtime/supervisor.py, scripts/workload_factory_binding_runtime/launch.py, tests/runtime_binding/test_supervisor.py, tests/runtime_binding/test_supervisor_access.py; verify: G02 and worker control-plane/key/policy denial; fixtures retain fixture-only scope. Isolated controlled-Python launch/source and RPC-denial candidate; deployed independent administration, OS key/policy access denial and immutable launch filesystem remain unqualified.
- [x] T007 [O] Bind confined gate deployment/credential to the owning signer; files: scripts/workload_factory_binding_runtime/custody.py, tests/runtime_binding/test_custody.py; verify: G03 owning proof plus direct valid-preimage denial; new custody assertions refuse for upstream owner decision. Isolated source candidate with actual owning mTLS and mutation-sensitive separate-process worker probe; deployed issuance/readback administration and OS/network credential confinement remain unqualified.
- [x] T008 [O] Add expected-initialized state preflight and restart/recovery enforcement; files: scripts/workload_factory_binding_runtime/state.py, tests/runtime_binding/test_state.py; verify: S01, no silent reset, ambiguity stays consumed and no hostile-host/backup rollback claim. Isolated source candidate requires an independent initialization receipt, existing private DELETE-journal SQLite state and fresh active-scope readback; startup never provisions or restores. Deployed storage administration and recovery-policy qualification remain separate.

Independent acceptance: one bounded owning proof; no approval/apply operation.

## US3 — Qualification and Handoff

- [x] T009 [O] Implement run leases/finalizer and independent cleanup/readback; files: scripts/workload_factory_binding_runtime/lifecycle.py, tests/runtime_binding/test_lifecycle.py, tests/runtime_binding/test_lifecycle_process.py; verify: L01 success/failure/cancel; missing readback fails; shared resources remain. Isolated source candidate with actual independent janitor/readback processes, scoped generation/ownership checks, hard-runner-exit expiry cleanup and preserved replay/shared resources. Deployed registration, scheduler, administrative isolation and provider cleanup/readback qualification remain separate.
- [x] T010 [S] Wire substantive offline matrix and selected owning-source integration into conformance; files: tests/runtime_binding/**, .github/workflows/pytest-suite.yml; verify: required I/G/S/L and current R01 scope/error-privacy cases collect with zero failures/errors/skips and no public issuer/provider credential use. The dedicated fixed-collection gate verifies the clean exact selected owner before/after pytest, requires all three phases to pass, and runs unprivileged with loopback only across exec. Full redacted receipts remain T011; deployed qualification stays separate.
- [x] T011 [O] Add safe errors, redacted scoped receipts and operator runbook; files: scripts/workload_factory_binding_runtime/evidence.py, specs/017-protected-runtime-qualification/quickstart.md, tests/runtime_binding/test_evidence.py; verify: R01 exact sources/case/results/cleanup with no raw sensitive material. The internal canonical source/fixture report uses closed projection and digest bindings, immutable config/readback metadata and actual lifecycle cleanup checkpoints; missing cases/cleanup cannot pass. Protected-machine scope refuses until later separately reviewed operational qualification; no neutral receipt API is changed.
- [x] T012 [O] Prepare protected qualification workflow after source acceptance; files: .github/workflows/protected-runtime-qualification.yml, .github/workflows/protected-runtime-qualification-run.yml, scripts/prepare-protected-runtime.py, scripts/workload_factory_binding_runtime/workflow.py, tests/runtime_binding/test_workflow.py; verify: manual caller/local reusable same-commit wiring, accepted immutable sources, existing protected environment, job-scoped OIDC, trusted current configuration/operation grant and registered independent cleanup readiness. Production hosting is unselected; the entrypoint blocks before outputs/OIDC and qualify/cleanup remain not-performed handoffs until separately reviewed T013/T014 hosting. Workflow preparation authorizes no setup or dispatch.
- [ ] T013 [O] Obtain operational selections and scoped setup/dispatch authorization; files: specs/017-protected-runtime-qualification/evidence.md; verify: all operational-input categories have approved non-secret references and independent readback. This is an owner/operator act.
- [ ] T014 [O] Execute real protected machine qualification at accepted sources; files: specs/017-protected-runtime-qualification/evidence.md; verify: P01/deployed G02/G03/L01, real issuer/independence/confinement and fresh cancellation/cleanup; missing facts stay blocked/not-performed.
- [ ] T015 [O] Deliver accepted machine-only receipt to codeXfactory 058 T002; files: specs/017-protected-runtime-qualification/evidence.md; verify: owner acceptance names evidence/pins; human/domain gates remain separate.

## Dependencies

T001 -> T002/T003 -> T004/T005 -> T006/T007/T008 -> T009/T010/T011 -> T012 ->
T013 -> T014 -> T015. US1 is the smallest useful slice. No parallel-agent
implementation is required. Factory governance and consumer handoff duplicate
no implementation list. Future paths are proposed; reconcile them against
reviewed code during commissioned implementation without widening scope.
