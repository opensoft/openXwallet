# Required Qualification Matrix

Status: draft; cases specified, new runtime unimplemented

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
