# Tasks: Protected Machine Runtime Qualification

Status: sole executable implementation list; T012G owner act recorded; T012H–K isolated candidate qualified; operation unauthorized
Current commission: 2026-11-14 source-ratify/land #1314/#64, then implement/test T012H–K in isolation.
Prior commission: 2026-11-13 verify #1311 post-merge CI and refresh T013 after paired
source-only ratification/landing of #1311/#60. Setup and dispatch stay unauthorized.
See [evidence](evidence.md), [selections](operational-inputs.md),
[authority draft](scoped-authorization.md) and [source prerequisite](workflow-bootstrap.md).

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
- [x] T012B [O] Resolve dispatch bootstrap through factory change fix-protected-runtime-dispatch-bootstrap; files: scripts/workload_factory_binding_runtime/bootstrap.py, config.py, workflow.py, scripts/prepare-protected-runtime.py, .github/workflows/protected-runtime-qualification*.yml, tests/runtime_binding/test_bootstrap.py; verify: independently accepted static selection before run assignment, full run-bound config/grant admission preserved, replay/substitution/expiry/concurrency/CLI refusal tested in isolation. Source accepted and landed through factory #1311 / adapter #60; source/isolated scope only, with no setup/dispatch authority.
- [x] T012C [O] Implement explicitly initialized durable portable authority state under factory change add-portable-bootstrap-authority; files: scripts/workload_factory_binding_runtime/reference_authority/**, tests/runtime_binding/test_authority.py; verify: immutable approval, atomic one-run binding, concurrent winner, restart/revocation/lost-state refusal and no reset/backup-rollback claim.
- [x] T012D [O] Implement bounded loopback mTLS authority/client with independent signed fixture context; files: scripts/workload_factory_binding_runtime/reference_authority/**, tests/runtime_binding/test_authority_transport.py; verify: actual peer roles/server identity, signed source/context/freshness checks, forged/worker denial, bounded safe errors, fresh bootstrap/operation clients and no operational CLI activation.
- [x] T012E [O] Connect isolated authority to existing admission/owning wallet/cleanup; files: tests/runtime_binding/authority_fixture.py, tests/runtime_binding/test_authority_flow.py; verify: static selection before run observation, full actual-run admission, owning cryptographic proof and replay refusal, restart/revocation/cancellation/runner-death cleanup with retained state and shared resources.
- [x] T012F [O] Qualify/publish paired source candidates; files: tests/runtime_binding/matrix_contract.py, feature017 evidence and reference-authority runbook, factory proposal evidence/ledger; verify: substantive fixed matrix/complete gates, local expert and Codex review attempts, actual cleanup and CI; source-only acceptance remains separate.
### Real GitHub bootstrap source prerequisite — isolated T012H–K commissioned

The owner source-ratified factory #1314 / adapter #64 and commissioned isolated
T012H–K on 2026-11-14; the exact heads and equal-tree landings are in evidence.md.
This records T012G's actual owner act. T012L/M and T013's operational owner act
remain separate and unchecked; no setup/dispatch/token mint is authorized.

- [x] T012G [O] Obtain explicit owner acceptance and source commissioning for bootstrap-only admission OIDC, purpose/phase policy, coarse broker permission and failure bounds; files: specs/017-protected-runtime-qualification/evidence.md; verify: actual owner record names reviewed paired heads/scope; no setup/dispatch or live acceptance inferred.
- [x] T012H [O] Implement separate scoped bootstrap token acquisition/verifier/client after T012G; files: scripts/workload_factory_binding_runtime/github_bootstrap/**, tests/runtime_binding/test_github_bootstrap_identity.py; verify: trusted request/server endpoints, exact issuer/audience/claims/phase/time, worker token exclusion, safe errors, no stored runner secret, and independent signature-valid single-claim controls (protected claims with bootstrap audience only; proof audience with only environment removed) rejected by unchanged proof policy before custody, plus provider-shaped unprotected proof-audience refusal.
- [x] T012I [O] Implement durable dispatch-attempt journal and independently authenticated GitHub correlation/controller adapters after T012G; files: scripts/workload_factory_binding_runtime/github_bootstrap/**, tests/runtime_binding/test_github_bootstrap_correlation.py; verify: reservation persisted before mock I/O, fresh approval/window/revocation after blocking work before send, zero sends for expired/revoked reserved winners, concurrent at-most-one attempt, crash/lost-response no retry/reset, 200 run ID corroboration, 204/mismatch/source drift refusal, fixed endpoints, coarse credential boundary and originating human/App distinction. Tests do not call live writes.
- [x] T012J [O] Integrate opt-in phase-separated bootstrap and planned workflow token-request scope after H/I; files: scripts/prepare-protected-runtime.py, scripts/workload_factory_binding_runtime/workflow.py, .github/workflows/protected-runtime-qualification*.yml, tests/runtime_binding/test_github_bootstrap_workflow.py, tests/runtime_binding/test_workflow.py; verify: unchanged three inputs/seven roles, exact allowlisted job graph/caller/reusable source, preflight versus post-environment subject/approval policy, no proof identity relaxation, default unselected refusal, no token request or dispatch in source tests.
- [x] T012K [O] Extend fixed isolated conformance controls for the accepted new source profile; files: tests/runtime_binding/test_github_bootstrap*.py, tests/runtime_binding/matrix_contract.py; verify: valid-signature independently isolated audience/environment barriers with known-good positive controls, provider-shaped unprotected proof-audience refusal, other wrong-phase/claims, malformed/stale/redirect/rate-limit responses, journal/correlation/clock/revocation failures, source race and App-originator review negatives, one proof/replay and independent cancellation/runner-death cleanup with retained state; zero missing/skipped matrix cases.
- [ ] T012L [O] Review, qualify and present paired source candidates for owner ratification; files: specs/017-protected-runtime-qualification/evidence.md; verify: full ordered gates, isolated matrix, exact-head hosted CI, local expert review/Codex request receipts, no unresolved source findings and actual owner acceptance; no operational grants or pin promotion.
- [ ] T012M [O] Reconcile the accepted source and hand off actual selection/authorization obligations to T013; files: specs/017-protected-runtime-qualification/operational-inputs.md, scoped-authorization.md, t013-decision-record.md; verify: main-update residual-exposure/control, actual subjects/target/identities/protection/issuance/state/cleanup remain operator decisions; setup/dispatch NOT GRANTED and T013/T014/T015 unchecked.

### Operational owner gates — not granted

- [ ] T013 [O] Obtain operational selections and scoped setup/dispatch authorization; files: specs/017-protected-runtime-qualification/evidence.md, operational-inputs.md, scoped-authorization.md, t013-decision-record.md, bootstrap-authentication-plan.md; verify: all operational-input categories have approved non-secret references and independent readback. This is an owner/operator act.
- [ ] T014 [O] Execute real protected machine qualification at accepted sources; files: specs/017-protected-runtime-qualification/evidence.md; verify: P01/deployed G02/G03/L01, real issuer/independence/confinement and fresh cancellation/cleanup; missing facts stay blocked/not-performed.
- [ ] T015 [O] Deliver accepted machine-only receipt to codeXfactory 058 T002; files: specs/017-protected-runtime-qualification/evidence.md; verify: owner acceptance names evidence/pins; human/domain gates remain separate.

## Dependencies

T001 -> T002/T003 -> T004/T005 -> T006/T007/T008 -> T009/T010/T011 -> T012 ->
T012B -> T012C/T012D -> T012E -> T012F -> T012G -> T012H/T012I ->
T012J -> T012K -> T012L -> T012M -> T013 -> T014 -> T015. US1 is the smallest useful slice. No parallel-agent
implementation is required. Factory governance and consumer handoff duplicate
no implementation list. Future paths are proposed; reconcile them against
reviewed code during commissioned implementation without widening scope.


T013 preparation on 2026-11-14 records exact owner source ratifications and
ordered equal-tree landings, refreshed read-only provider configuration, proposed
operational decisions and remaining real-GitHub authentication/issuance source
gates. This preparation is complete as a reviewable packet; T013 itself and
T001/T014/T015 remain owner-controlled and unchecked. No duplicate implementation
list or operational authorization is added.

T012H–K completion is isolated source qualification only: 1,609 full regression
tests and 1,307 required matrix cases pass without skips. Evidence records the
accepted design, exact artifact hashes, integrity fixes and verified cleanup.
T012L/M, T001/T013–T015 and every operational stage remain unchecked/ungranted.
