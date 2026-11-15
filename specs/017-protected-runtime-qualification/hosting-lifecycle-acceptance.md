# T012S isolated lifecycle acceptance preparation

Status: prepared test design; no T012S cases executed
Owner: accepted factory hosting/issuance model; feature017 tasks.md only
Scope: H05/H11 source qualification; no live cleanup/provider acceptance

Every negative needs a complete positive with independently owned authoritative
fixture state. Remove the specific guard to prove its test becomes unsafe/fails;
outage, malformed multi-fault input or a request echo must not count as denial.
Expected new case counts stay unallocated until actual implementation/collection.

| Case | Required actual isolated positive | Independent fault/control | Required result |
| --- | --- | --- | --- |
| S-01 pre-start registration | Real pinned mTLS registration, committed journal and independent scheduler/audit acknowledgement before one child | Interrupt before/after journal commit, before ack publication/read, or lose reply | No pre-ack launch; retained stage owner; no hidden registration/start resend |
| S-02 generation binding | Actual POSIX unit, manager PID/start/boot and observed child PID/start/session/cgroup; bound artifacts/credentials | Manager crash before PID persistence, reused PID, unit/invocation/boot/resource substitution | Same consumed start; independent absence/cleanup evidence or explicit unverified state; no replacement child |
| S-03 final preparation | Derive accepted complete config/policy and register a new RunPlan/lease linked to stage | Wrong accepted/source/run-attempt/config/policy/plan/resource-retention or generation; dummy digest | Refuse before responsibility release; original stage remains owned |
| S-04 takeover acknowledgement | Separate final scheduler acknowledgement and independent exact-generation readback | Lose/expire/copy ack; writer echoes its own success; interrupt each prepare/commit/read/release boundary | Stage responsibility persists until valid independent ack; no cleanup gap |
| S-05 concurrent responsibility | Separate stage/final schedulers race on a retained per-resource action fence | Duplicate tick, double release, stale stage restart, lost cleanup response | At most one destructive action per consumed attempt; ambiguity reconciles by reads; no resurrection/reset |
| S-06 expiry and clocks | Launch/proof stops at original expiry; registered cleanup runs under its fixed separate window | Wall/monotonic regression, delayed TLS/SQLite/ack/readback, lease extension or late finalization | Refuse use/release; cleanup authority is not renewed; bounded status/attempt counts survive reconstruction |
| S-07 hard process failure | Separate janitor/audit processes survive real runner/gate/worker termination and act from durable registration | SIGKILL outside finally, controller reconstruction, dead launch authority, unavailable runtime config | Actual measured run-generation cleanup plus independent fresh readback, or explicit unverified result; no live-config dependency |
| S-08 preservation | Run process gone, exact credential generation revoked, run files removed, retained/shared generations unchanged | Replace inode, reclassify retained/shared, change ownership, inject newer credential/process generation | Changed generation is never mutated; audit refuses copied/partial cleanup success; replay/dispatch/nonce journals retained |
| S-09 independent audit | Fresh attempt-bound reader reports actual resource state under distinct transport identity | Stale/cross-attempt/cross-plan audit, missing resource, raw provider error/exception or actor-only success | No cleanup success without complete independent bounded evidence; no sensitive payload in safe projection |
| S-10 initialized stores | Reopen the same registered schema/device/inode with high-water and consumed actions intact | Missing init, corruption, swapped store, unsupported schema or rollback/recreated DB | Fail closed without create-on-open, migration, reset or reused attempt |
| S-11 unsupported infrastructure | Explicitly selected isolated process/credential/file cleanup capability passes its measured controls | Missing external watchdog, same failure domain, provider lacks conditional-generation retirement | Total control-host-loss/automatic VM expiry/infrastructure retirement remain unsupported/unqualified |
| S-12 compatibility | Existing full admission/proof/replay, refusing defaults, worker control denials and old matrix pass | Worker requests janitor/scheduler/audit/private takeover authority; extra role/route/dispatch input | Denied through an available authorized positive; neutral APIs/pins/workflows/defaults unchanged |

Interruption coverage must name before/after durable registration, ack publication,
start-consumption, actual child start, generation persistence, final-plan commit,
final scheduler acknowledgement, independent readback, stage release, per-resource
cleanup consumption and final audit persistence. At each boundary record the actual
responsible owner and consumed attempt, then independently observe process/credential/
file state. Repeating a mocked callback is not an independent process-crash test.

Extend matrix_contract.py only from measured full node IDs and substantive H05/H11
anchors. Preserve baseline 1,898 identities/old fingerprints/anchors; retain ordinary
full-suite coverage separately. Zero native skips/deselections/xfail are permitted.
No real cloud credential, provider setup, protected dispatch or service restart is
used. Audit/teardown must retain source hashes, XML, journal summaries and cleanup
receipts outside exact removed fixture roots; do not prune accepted worktrees/benches.
