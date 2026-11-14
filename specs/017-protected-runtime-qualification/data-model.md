# Proposed Operational Model

Status: draft; internal composition, no neutral vocabulary fork

| Entity | Required binding | Authority / refusal |
| --- | --- | --- |
| Launch selection | Exact profile/source/dependency hashes, expected claims, service/state identities and protection readback | Operator-owned; missing or worker-selected data refuses |
| Issuer snapshot | Approved issuer/endpoint, unique eligible public keys, fetch time/digest and expiry | Bounded trusted transport; no token URL or stale extension |
| Authenticated request context | Verified workload plus selected embedding/channel evidence | Worker flags or unverified claims cannot establish authentication |
| Current records/challenge | Existing canonical wallet/key/custody/grant/challenge and request/run/deadline binding | Authenticated owning sources and existing validators; no worker replacement |
| Observed launch | Existing signed source/configuration/key and token/request/challenge/policy/run binding | Separately administered supervisor; no self-report-only evidence |
| Gate custody binding | Approved gate deployment and opaque narrow signing handle | Valid direct-worker signing denied; no new neutral assertion API |
| Replay state | Existing one-use reservations in selected initialized private state | Reserve before sign; ambiguity stays consumed; no silent reset |
| Lease and receipt | Run-owned lifecycle, independent readback and redacted digests | Missing cleanup blocks acceptance; shared resources preserved |

Transition: missing/unaccepted inputs -> blocked; accepted inputs -> trusted preflight
-> workload/authority/observation verification -> durable reservation -> owning sign
-> fresh authority/deadline recheck -> bounded machine proof. Failures after reservation
leave it consumed. Missing cleanup makes qualification incomplete even after valid proof.

Receipt scope is source-conformance, isolated-fixture or protected-machine. It grants
no human approval, domain effect or runtime dependency lock. Retain no raw token,
private key, credential, factor material or browser state. Source-only assembly
evidence in codeXfactory remains separate.

T011 realizes a closed canonical internal report for source/fixture scope only.
The approved selection snapshot retains configuration readback digest/principal
hash and times; cleanup checkpoints retain independent record/identity/attempt
digests and times. Case aggregates use closed IDs, bounded integer counts,
observation time and artifact digest. Missing cases/cleanup remain explicit and
prevent pass. Reports are historical structural observations, not signed neutral
possession receipts or authority. They omit raw sensitive material by construction
and cannot self-promote to protected-machine scope.


## Proposed hosting/issuance source planning

The user commissioned preparation of factory change
`add-protected-runtime-hosting-issuance` and this feature's
[hosting/issuance plan](hosting-issuance-plan.md), using the recommended
[T013 design basis](hosting-issuance-selections.md). This does not ratify or
commission the new source profile. Proposed T012N-V in tasks.md stay unchecked.

Research found a material remaining source prerequisite: static-v1 commits
composition/policy digests derived from actual run/process data. The proposed
versioned plan-only preflight, protected staging lease and measured finalization
resolve that dependency without predicting IDs/hashes or weakening full admission.
[Research](hosting-issuance-research.md), [model](hosting-issuance-model.md),
[internal interfaces](contracts/hosting-issuance.md) and
[acceptance matrix](hosting-issuance-acceptance.md) define the future source slice.
Current v1/default, neutral pins/APIs, runtime/tests/workflows remain unchanged.
T001/T013/T014/T015 and every setup/dispatch stage remain ungranted; feedback is
deferred and neither historical blocked write is replayed.
