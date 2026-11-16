# T012T proposed source acceptance controls

Status: draft
Kind: test-plan
Scope: source preparation; no T012T case executed or live gate cleared

Every negative needs a complete available positive and an independent mutation.
Keep 2,017 baseline native nodes and existing fingerprints/anchors. New counts and
H10/H12 anchors are measured after implementation, never guessed or CI-generated.

| Control | Required isolated source positive | Independent negative / failure | Later live boundary |
| --- | --- | --- | --- |
| T-01 trusted origin | Actual local authenticated phase collection binds the same finalized run; source run stays fixture-scoped | Copied source/fixture report, live flag, principal label or typed object cannot enter protected emission | T013 actual authenticated operational source facts |
| T-02 real proof | Pinned owning verifier accepts one actual bounded proof through current RuntimeBinding | Wrong source/run/attempt/challenge or revoked current record refuses before custody | Actual selected issuer/custody/authority |
| T-03 replay | Exact accepted proof replay returns the owning replay-refusal outcome | Outage, generic exception or a different malformed proof cannot pass replay coverage | Approved bounded replay case |
| T-04 crypto barriers | Valid-signed audience-only and environment-only mutations are independently refused | Remove each claim check; the corresponding negative must fail while other claims remain valid | Approved negative-case capability; no arbitrary signing grant |
| T-05 worker control | Available authorized signer/control positive and explicit valid worker-preimage denial | Disposable excess permission causes denial qualification to fail; outage is unperformed | Actual kernel/credential process boundary |
| T-06 one operation | One existing RunLifecycle wraps actual qualifier and returns verified cleanup | Repeated run, replacement generation or report-time re-execution refuses; no new launch | Real selected scheduler/lease/generation |
| T-07 fault cleanup | Success/failure/BaseException cancellation preserve actual outcome and independent cleanup | Lost response, stale/wrong scope/attempt/resource, replaced retained file or missing audit keeps qualification false | Same original cleanup_until, actual retirement and independent watchdog limits |
| T-08 runner death | Actual detached runner death leaves existing independent ownership; same-reference status observes eventual cleanup | No runner self-report, newest-run search, fresh reference or consumed-action resend | T014 external failure-domain observations |
| T-09 clock/budget | Complete positive composes accepted phase decisions and earliest expiries | Delay after I/O, regressed wall/monotonic time, exhausted journal or read allowance refuses; no counter reset | No new operational budget is granted |
| T-10 new grammar | Pure golden vectors exercise all required fields/slots and canonical size bound as test data | Unknown/duplicate/wrong type/placeholder/oversized fields refuse; vectors cannot be emitted as live artifacts | Explicit factory profile acceptance first |
| T-11 completeness | Derived status consumes same-run case/proof/issuance/generation/cleanup observations | Missing, mismatched or stale fact; caller pass boolean; all-zero/offline counters cannot qualify | All actual required/live slots independently observed |
| T-12 outcome | Failed/cancelled operation remains so after successful cleanup | Cleanup success cannot upgrade operation failure; absent cleanup cannot pass | Actual independent audit and safe failure outcome |
| T-13 privacy | Private canaries across success/failure/cancel produce only declared digests and safe codes | Canary in exception args/notes/causes, provider/token/PEM/proof/challenge/path input must never escape | No raw operational data in reports |
| T-14 no self-cycle | H12 covers the pre-report redacted projection/privacy checks; final digest is external | Hashing final bytes into their own embedded result or treating hash as provenance refuses | Authenticated delivery remains separate |
| T-15 compatibility | Existing v1 source/fixture vectors and CLI refusal before outputs/OIDC remain intact | Relabel old profile, add scope/case fields, worker-select bindings, enable workflow or add role/input refuses | Setup/dispatch remains unauthorized |
| T-16 authority | Every report fixes human/domain/consumer acceptance false | Report bytes/hash supplied as possession proof, MFA/approval receipt or consumer grant conveys no authority | codeXfactory human/domain gates remain separate |

## Execution boundary after later commissioning

Use the existing private isolated Linux source-test process: normal umask022 inside
a private0700 parent, no capabilities/groups or privilege escalation, and explicit
owning source selection. Native conformance is loopback-only with source read-only
and only task-local fixture writes. Use local TLS/crypto/OS positives; do not mint
provider credentials or invoke protected dispatch. Preserve every old test oracle.

All required setup/call/teardown phases must pass without missing/deselected/skipped/
xfail cases. External fixture audits verify process generations in the correct PID
namespace, issuer retirement and original retained/shared preservation before exact
fixture-root removal. Native container absence must be independently confirmed.
The isolated positive produces honest source/fixture evidence; it cannot emit a
protected operational receipt or clear T014/T015. T012U broader conformance/runbook
and T012V source publication/handoff remain separate.
