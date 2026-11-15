# Hosting and issuance acceptance matrix

Status: draft
Kind: test-plan
Scope: proposed later implementation/source qualification; no cases executed by this preparation

Every source group needs an actual positive control and independent failure mutation.
A token with many wrong claims, outage, mocked success boolean or copied deployment
record cannot mask removal of the specific check. Existing proof/fixture tests remain;
no expected case count is guessed or generated dynamically in CI.

| Group | Required source positive | Independent negative/failure control | Later live gate |
| --- | --- | --- | --- |
| H01 static-v2 | Construct canonical plan before a run/process; finalize after actual independently supplied run and real measured child | Each of four late fields wrong; any other static byte changed; dummy/extra field; v2 passed to v1; alternate derivation | Actual accepted final source/image/plan selection |
| H02 plan-only preflight | Valid signed preflight plus independent current journal/source/hold/protection returns only approved existing environment | Assert zero launch/issuer/custody/full-config calls; wrong phase/claims; missing bypass/branch-type/current hold | Real expected subjects and actual complete provider fields |
| H03 staging ownership | Actual protected approval/review, independent stage grant and durable janitor acknowledgement before one controlled inert child | Kill/fail before acknowledgement, after start/before PID persistence, lost response, concurrent starts, replacement manager generation | Actual host/unit/cgroup/boot/readback and worker privilege boundary |
| H04 finalization | Measure real PID/start/argv/cwd/executable/artifacts; recompute composition -> policy -> config against plan | Independent policy/config/static/source/nonce/PID/boot mutation; launcher supplies arbitrary signed hash; phase/type confusion | Real source/image/guest-agent facts and independent authority |
| H05 cleanup takeover | Create immutable final full-config plan; independent takeover confirms same generation before stage retires | Interrupt each promotion step; changed deadline/generation; double owner-release; late finalization | Registered real scheduler/janitor/audit and case scope |
| H06 issuance | Actual local RSA-sign/verify and mTLS role delivery; exact requested/returned App repo/scope/key version match | Wrong issuer/key/install/repo/permissions/expiry; late issuance; replayed nonce/CSR self-identity; reader-to-broker escalation | Actual Apps/Key Vault/guest enrollment/effective scope and retirement |
| H07 host privilege | Allowed controller/issuer succeeds; separate valid worker preimage/control request explicitly denied | Expose IMDS/resolver/key/control credential or writable policy; require denial probe to fail; outage must not count | Actual kernel UID/capability/mount/network/IMDS/private-key and admin boundary |
| H08 provenance | Complete positive protected path includes correlation plus current source/protection/control callbacks under one deadline and explicit budgets; mutate observed facts independently while candidate stays fixed | Candidate echo, self-signed manifest, absent field/default false, tag-as-branch, extra wildcard/policy/page; reset correlation/global budget or omit a callback | Current authenticated actual fact sources, not constructor labels |
| H09 deadlines/hold | Enclosing and returned earliest expiry survive all nested calls, cancellation and status reads | Stall journal/TLS/credential/measurement/issuer/registration beyond deadline; regress clock; expire hold after blocking work | Actual bounded clients/current source/update-control scope; no atomic pin claim |
| H10 proof barriers | Existing owning verifier accepts one bounded proof from a finalized actual isolated run, then replay refuses | Crypto-sensitive signed audience-only/environment-only negatives, worker valid-signing-preimage denial, excess-permission mutation | Real protected issuer/source/custody/deployment qualification |
| H11 failure cleanup | Independent stage/final janitor/audit after success/failure/cancel/runner/worker/gate death preserves shared/retained state | Lost ack, stale generation, false cleanup success, missing init/store, changed inode, interrupted takeover | Actual expiry/revocation/absence and independent external watchdog for control-host loss |
| H12 report privacy | Separate new protected report requires all actual bounded case/source/run/cleanup facts | Relabel source/fixture report, omit/mismatch/stale case/result/cleanup, raw secret/exception/provider payload | Protected report source acceptance plus T014 actual qualification; no T015/human/domain inference |

## Qualification sequence

Use isolated synthetic provider/issuer/host observations only to test adapters and
independent mutations; actual local RSA/TLS/OS process and owning proof exercise the
real boundaries they claim. Actual provider credentials, identity minting, App/Key
Vault writes, source freezes and dispatch endpoints are never used for offline tests.
No mutable expected counts or skip-for-service-unavailable path may pass conformance.

Extend matrix_contract.py with reviewed exact new module counts, full-node fingerprints
and substantive H-group anchors after later source implementation. Preserve all old
nodes/anchors and existing admission/nonce/consumed-state/privacy/cleanup controls.
The mandatory native gate must collect/pass every setup/call/teardown with zero missing,
deselected, skipped, xfail/XPASS or non-passing cases; ordinary full suite is separate.

Only later source acceptance and scoped T013 setup/readback/dispatch/run/cleanup may
qualify live P01/deployed G02/G03/L01 and the new protected report. Actual provider
API/schema/complete subjects, OS/admin denial, software custody, initialization,
source coordination, external scheduler and infrastructure retirement limits must
be independently observed. Unsupported facts stay blocked/not-performed; no fixture
or machine proof alone supplies consumer, human, domain or release acceptance.
