# Required Qualification Matrix

Status: T012V accepted-main #79 integration locally qualified on PR #78; final-head CI, owner acceptance and deployed cases pending


## Current H01-H12 source coverage (T012V)

The [operator source runbook](operator-source-runbook.md) supplies the source,
isolation, final-verdict and independent teardown procedure. This table maps
actual existing controls; it does not turn source/fixture results into a live
protected report. Counts are measured anchored nodes and overlap across groups.
Current collection is 2,781 full parent cases and 2,369 mandatory native nodes;
all 64 conformance self-tests, prior 2,761 full / 2,364 native identities and
earlier anchors remain. New source controls cover the probe total Decision,
cancellation ownership and byte-compatible canonical-journal replay. Execution
and cleanup completion are recorded in [current evidence](hosting-conformance-implementation.md#t012v-main-79-integrated-source-qualification).

| Group / anchored nodes | Actual source positive | Independent refusal/mutation | Remaining live gate |
| --- | --- | --- | --- |
| H01 /25 | [Static plan before any run/process](../../tests/runtime_binding/test_hosted_finalization.py): `test_static_plan_commits_before_any_run_or_process` | Exactly four late fields absent; no other omission; v2 through v1 refuses | Accepted deployed source/image/plan selection |
| H02 /27 | Same module: signed plan-only preflight has no effectful ports | Each current fact, wrong purpose, missing protection and hold drift refuse before output | Real complete provider fields/subjects |
| H03 /97 | [Launch](../../tests/runtime_binding/test_hosted_launch.py): protected grant plus durable acknowledgement precedes one actual sandboxed start | Lost responses, concurrent starts, missing store/ack, manager death and substituted generation refuse or remain consumed | Actual host/unit/boot/admin and worker boundary |
| H04 /44 | [Finalization](../../tests/runtime_binding/test_hosted_finalization.py): real generation plus independently recomputed complete bytes | Static/policy/config/run/PID/source/boot mutation and arbitrary caller digest refuse | Actual approved host/source/guest and final authority |
| H05 /29 | [Lifecycle](../../tests/runtime_binding/test_hosted_lifecycle.py): immutable same-generation stage/final takeover without cleanup gap | Interrupt promotion, dead scheduler, changed source/scope, expired clock and concurrent release retain an owner | Independently administered registered scheduler/janitor/audit |
| H06 /53 | [Issuance](../../tests/runtime_binding/test_hosted_issuance.py): actual local RSA App JWT and scoped authenticated role delivery | Returned install/repo/permission/expiry drift, late issuance, lost response and actual retirement refusal controls | Actual App/Key Vault/enrollment and effective retirement |
| H07 /54 | [Credentials](../../tests/runtime_binding/test_hosted_credentials.py), enrollment, launch/lifecycle: allowed controller succeeds and valid worker requests are denied by real process/TLS/kernel controls | Exposed capability, writable/inherited credentials, excess policy or outage must fail denial qualification | Deployed UID/network/IMDS/key-file and administrator exclusion |
| H08 /87 | [Readback](../../tests/runtime_binding/test_hosted_readback.py): authenticated current sources/protection/control and separately measured guest/state facts | Change one observed fact with candidate fixed; missing fields, wildcard/tag/default or candidate echo refuse | Actual selected authenticated provider/guest fact sources |
| H09 /40 | [Readback flow](../../tests/runtime_binding/test_hosted_readback_flow.py): complete protected correlation/current source/protection/hold under one original Decision | Late fact mutation, expiry/regression, deadline or shared-budget reset refuse | Real bounded clients and coordinated-source policy; no atomic main guarantee |
| H10 /85 | [Evidence](../../tests/runtime_binding/test_hosted_evidence.py): complete connected owning proof/replay on one original Decision at38 reads (39 with fixture origin) | Valid-signed audience/environment-only mutations, actual worker denial/excess permission and original/private12 refusal guard | Real protected issuer/custody/source/deployment qualification |
| H11 /284 | [Lifecycle](../../tests/runtime_binding/test_hosted_lifecycle.py) and evidence: independent cleanup after success/failure/cancel/actual runner death; fresh observer-only process after lease expiry | Lost mutation result, wrong generation/attempt, missing store, stale audit and uncertain cleanup never upgrade; no destructive replay | Actual independent expiry/revocation/absence, external control-host-loss watchdog and infrastructure retirement |
| H12 /142 | [Evidence](../../tests/runtime_binding/test_hosted_evidence.py): actual pre-report privacy controls and closed safe projection | Missing/stale/wrong case/source/run/cleanup, raw canaries, CLI parse/cancel errors and fixture-origin promotion refuse | Approved actual protected origin and T014 run; human/domain/consumer gates separate |

All historical I/G/S/L/R/B anchors remain mandatory. R01 additionally anchors all
12 final-verdict controls: real tiny pytest runs mutate selected-source state at
setup/call/teardown, remove it, fail/skip execution or trigger safe postflight
error/cancellation/zero-exit handling. The successful control requires exactly one
final PASS after postflight. A nominal zero exit without complete phase reports
fails. Native boundary and the exact selected owner are separately exercised by
the real mandatory entrypoint; tiny harness doubles cannot qualify either boundary.

T012U changes no proof/report runtime API, source/fixture scope, workflow, budget,
neutral pin or dependency. Protected P01/deployed G02/G03/L01 and all operational
acts remain separate; the following original matrix and preparation records are
retained as historical context.

| Cases | Required observation | Requirements |
| --- | --- | --- |
| I01 issuer/snapshot | Selected RS256 evidence verifies with/without allowed x5t; deadline retained | FR-003,004 |
| I02 transport/data | Wrong issuer/JWKS, redirect, invalid TLS, duplicate JSON/key IDs, oversized/slow/malformed data refuse before custody | FR-003,010 |
| I03 refresh/outage | One coalesced refresh/retry; throttled/unknown keys and stale/outage trust refuse; removed keys not restored | FR-003,009 |
| I04 signed context | Change each owner/repository ID, caller/reusable ref/SHA, environment, subject, source, run and attempt independently; each refuses | FR-002,004,013 |
| I05 clock | Future iat despite old nbf, future nbf, expiry equality, lifetime >300s, clock failure or expiry during I/O refuse | FR-004,009 |
| G01 challenge/authority | Current owning records verify; bad service authentication, worker replacement, revocation or widening chain refuses | FR-005,009 |
| G02 observation | Actual approved launch measures correctly; self-report, stale/replayed observation or untrusted observer refuses | FR-006 |
| G03 custody | Owning verifier accepts one proof; worker cannot sign valid canonical preimage; disposable excess-permission mutation makes denial probe fail | FR-001,007 |
| S01 persistence | Concurrent/restarted reuse and ambiguous failure stay consumed; observable corrupt/missing expected state refuses | FR-008,009 |
| L01 lifecycle | Success/failure/cancel each has fresh independent run-owned absence readback; shared resources preserved | FR-012 |
| R01 scope/privacy | Fixed errors/redacted receipt; no raw sensitive material, human approval, domain effect or consumer lock | FR-010,014,015 |
| P01 protected run | Real issuer, selected sources, independent protection readback, deployed supervisor and gate credential confinement | FR-002,011,013,015 |

Required isolated cases must collect and pass without skips. Live P01 and deployed
G02/G03/L01 require approved services, real observations and operational authorization.
Local keys, loopback, virtual authenticators or same-user processes cannot substitute.
Even a complete machine receipt does not finish codeXfactory T002 or attended acceptance.

## Required offline conformance entrypoint (T010)

The ordinary full suite remains required. In addition, `pytest-suite` runs
`tests/runtime_binding/conformance.py` through `isolation.py` inside a fresh
Linux network namespace. Only loopback exists; the process has no capabilities,
supplementary groups or privilege escalation on exec. Environment/plugin options
are cleared and the home/temp tree starts empty and private. Source checkout and
reviewed hash-locked wheel installation happen before this offline boundary.
No public issuer request, provider credential or protected dispatch is used.

`matrix_contract.py` records the exact parametrized collection count and full-node-ID fingerprint per module
and substantive I01–I05/G01–G03/S01/L01/current-R01 anchors. Every collected test
must report passing setup, call and teardown. Missing/extra/duplicate nodes,
missing anchors, deselection, skips, xfail/XPASS, failures or pytest errors refuse.
Intentional test corpus changes must update counts, full-node-ID fingerprints and anchors in the reviewed contract; there is no
CLI selector or manifest override. The explicitly selected owning code must be
clean at the accepted `bb0e9dae89a771b05f6c235d0a77237288b95c85` before and after
execution, and imports must resolve under that source. The neutral adapter pin
remains unchanged. The harness tests include actual subprocess pytest mutations.

R01 anchors now cover the T011 closed scoped report, fixed error/privacy rules,
exact source/case/readback/cleanup binding and actual owning-proof/cleanup export.
The internal report authenticates no supplied Python object or test observation;
only trusted harnesses supply results. Protected-machine scope remains unsupported. No offline row qualifies deployed
independence, provider administration, real OIDC or human approval. Gate success
is a source result, not a protected machine receipt.

## T012 Preparation Coverage

T012B adds the complete `test_bootstrap.py` corpus: a static commitment prepared
without run fields, actual-run full admission, static substitution, independent
approval, context/source/case/grant/run/attempt replay, freshness/outage/clock
and earliest-deadline refusal. A synthetic locked authority models one binding
under concurrent claims; it does not qualify a deployed authority. Static
validation cannot weaken full runtime required-run fields. Real CLI cases cover
both the migrated static inputs and refusal of legacy inputs in all three phases.
The fixed collection contract adds the new module and substantive I04/R01 anchors;
existing cases are retained. No expectation is regenerated by CI.

`test_workflow.py` covers caller/source/context bindings, existing environment and
exact protection, separately current operation authority, registered external
scheduler/readback, active lease, bounded freshness/clock composition, default CLI
refusal before outputs/OIDC, and manual/local-reusable workflow permissions and
source pins. The entire module is required by the collection contract. These are
preparation checks, not P01 or deployed G02/G03/L01 evidence. Real hosting/clients,
operational selection/authority, actual protected run and protected receipt
promotion remain separately gated. No workflow dispatch is part of conformance.

## GitHub bootstrap source conformance extension

B04/B05 extend the internal fixed-collection test matrix under source-accepted
factory #1314 / adapter #64 and commissioned isolated T012H–K. They cover actual
RSA/loopback TLS identity and independent single-claim proof barriers; durable
pre-I/O dispatch consumption/crash/concurrency/revocation; bounded versioned
provider and phase/source/attempt/review corroboration; unchanged default refusal;
and one owning proof/replay with independent cleanup on all four outcomes.
Provider observations/tokens are synthetic and dispatch uses deterministic doubles.
The existing closed R01 receipt vocabulary is unchanged; these additional internal
anchors do not extend protected-machine receipt scope or clear live P01/G02/G03.

## T012U completed source result

At `6e2f0bfc626ab05b5b0384bc3a97d2816cfd696a`, full2,523 plus nine subtests and
mandatory-native2,215 pass with zero failures/errors/skips. All64 conformance
self-tests and every prior node/anchor remain; unaffected module fingerprints are
unchanged. R01=47 and H01-H12
counts above match actual native output. The final PASS follows exact-owning-source
postflight; all setup/call/teardown phases pass. Independent native boundary and
21,879-generation/ten-positive final preservation audit pass; exact owned roots
are removed. [As-built evidence](hosting-conformance-implementation.md) retains
failed diagnostics and limits. No protected P01, live receipt or source publication
is inferred. T012V and T001/T013-T015 remain separate.
