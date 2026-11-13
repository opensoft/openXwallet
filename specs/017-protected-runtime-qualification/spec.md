# Feature Specification: Protected Machine Runtime Qualification

**Feature Branch**: `017-protected-runtime-qualification`
**Created**: 2026-11-12
**Status**: T002–T005 source accepted and landed; isolated T006 source candidate
**Input**: Prepare the next runtime qualification step for the first codeXfactory pilot after #581 post-merge verification.
**Governance owner**: `opensoft/openXfactory`, `openspec/changes/prepare-protected-runtime-qualification/`.

2026-11-12: Brett Heap ratified factory #1307 at `04fad0559` with adapter #49
at `0a2dda9` and commissioned only the bounded issuer/JWKS slice after the
preparation landings. See [evidence](evidence.md). The original input and full
feature requirements remain the baseline; this slice does not complete the feature.

Subsequently Brett commissioned landing #50 and implementing/testing the remaining
T002 operational/source/protection binding. The source realization is internal
preflight under factory governance, not live qualification or a consumer lock.

Brett then ratified factory #1308 at `7d99face8934` with adapter #51 at
`864a2d19fda1` for source acceptance only, and commissioned T004/T005 in
isolation. The opt-in bridge connects selected authenticated connector/hosting
capabilities and preserves the unchanged proof semantics; no deployed machine
or human acceptance follows from those isolated tests.

Brett subsequently ratified #52 at `3833bc8629e6` for source acceptance and
commissioned T006 in isolation. The observer measures controller-selected live
process identity, launch/files/configuration and key/transport refs, signing the
unchanged observation format. It does not establish independent deployment
administration or worker OS access denial from same-user fixtures.

## User Scenarios & Testing

### User Story 1 — Verify a configured issuer at the trusted boundary (P1)

A trusted operator obtains fresh approved GitHub verification keys and supplies
them to the existing verifier without giving the worker control of trust.

**Independent test**: Inject deterministic issuer transport and keys. Valid
selected RS256 evidence verifies; endpoint/key/freshness/time failures refuse
before any signer. This first slice does not require a deployed custody service.

1. Given an approved launch and fresh keys, when the exact signed caller and reusable-workflow claims match, verification returns the accepted evidence and administrative deadline.
2. Given an unknown kid, when its one permitted refresh cannot establish an approved key, verification refuses with a fixed safe error.
3. Given stale trust, a redirect or a token-selected key URL, verification refuses without stale fallback or unapproved network access.

### User Story 2 — Produce one bounded proof through a confined gate (P2)

A separately administered trusted embedding composes current records, authenticated
challenge access, observed launch evidence, private state and the owning signer.

**Independent test**: Isolated services exercise the existing proof API and valid
canonical direct-sign denial. Real deployment independence remains a distinct test.

1. Given current approved inputs and a measured launch, one proof is accepted by the owning verifier, with human approval explicitly false.
2. Changed source/configuration/key binding, wrong/missing claims, revoked records, untrusted observation or worker-selected dependencies refuse.
3. Duplicate token/challenge use, ambiguous custody failure and restart preserve one-use reservations; missing expected state refuses.

### User Story 3 — Qualify the actual protected machine boundary (P3)

An authorized operator selects exact services/protection settings and runs a
machine-only qualification with independent cleanup and redacted evidence.

**Independent test**: A real protected run supplies actual signed evidence and
independent administrative readback. Missing live inputs are blocked/not-performed.

1. Real issuer/protection, supervisor confinement and valid worker direct-sign denial are observed at the selected sources and run/attempt.
2. Success, injected failure and cancellation each have fresh case-bound absence readback; missing readback fails.
3. Source/fixture success does not claim human assurance, domain markers or completion of codeXfactory T002.

## Requirements

- **FR-001** Preserve neutral proof/custody APIs, the source-accepted profile and the existing offline entrypoints; no canonical contract belongs to this adapter.
- **FR-002** Validate the owner-approved internal operational input, immutable source/dependency/profile bindings and protection/readback context before using trusted dependencies; no consumer runtime lock is published here.
- **FR-003** Use fixed configured issuer/discovery/JWKS locations, TLS verification, bounded fetch/response/key limits, freshness and single unknown-key refresh. Proposed bounds and cache policy are in the factory design; no token-selected URL, ambient untrusted configuration or stale-on-error fallback is accepted.
- **FR-004** Preserve RS256, x5t-as-metadata, exact expected signed claims, independent iat/nbf checks, maximum 300-second token lifetime and fresh administrative deadlines. No wildcard or case normalization is added.
- **FR-005** Authenticate the trusted current-challenge/record source and bind its canonical data to the verified subject/request/run. The worker supplies no replacement loader, full challenge or authority record.
- **FR-006** Require a separately administered supervisor with worker-inaccessible policy/key and actual launch measurement; retain the existing observation format and maximum 60-second validity.
- **FR-007** Confine signing credentials and owning API access to the approved gate deployment. Prove worker denial on a valid canonical signing request. A peer/subject allowlist or distinct keys alone is insufficient workload-bound custody evidence.
- **FR-008** Require selected initialized private persistent state at runtime startup, preserve consumed-on-failure reservations and restart/concurrency behavior, and refuse observable missing/corrupt state. No hostile-host or valid-backup rollback guarantee is added.
- **FR-009** Preserve fresh-clock and current-authority checks after blocking I/O, durable reservation and signing; failures emit no accepted proof result and do not erase consumed state.
- **FR-010** Expose fixed safe errors and redacted case-bound receipts. Retain no raw workload token, private key, credential, factor response, browser state or provider payload.
- **FR-011** Keep default gates offline using injected transport/local reference fixtures. Live qualification is opt-in and separately authorized; fixtures cannot self-label as deployed trust evidence.
- **FR-012** Require independent cleanup/readback for success/failure/cancel, preserving shared resources. Cleanup must address only selected run-owned processes/state/trust/resources.
- **FR-013** Corroborate actual protected environment settings separately from the signed environment claim, including the selected restrictions and applicable approval/bypass configuration.
- **FR-014** Refuse absent/unaccepted runtime schema/validator/protection bindings. Keep codeXfactory's existing source-selection lock non-executable and unchanged.
- **FR-015** Owner acceptance and implementation commissioning precede runtime implementation. Operational setup/dispatch and independent human broker/domain acceptance remain separate gates.

## Edge Cases

Unknown/duplicate kid; invalid TLS; endpoint mismatch/redirect; duplicate JSON;
oversized/slow responses; key removal; cache expiry/outage; throttled concurrent
refresh; future iat with backdated nbf; expiry during I/O; missing reusable claims;
changed run attempt; worker-selected loaders; observation replay; lost replay
state; ambiguous custody outcome; revocation during signing; missing cleanup.

## Success Criteria

- **SC-001** Every FR has substantive positive/refusal coverage with selected owner-source integration, zero failures/errors/skips in the required isolated matrix.
- **SC-002** No default gate reaches a public issuer or requires provider credentials; optional live execution cannot run with missing approved inputs.
- **SC-003** A successful live receipt identifies exact sources, protection/readback, real run/attempt, bounded machine proof, refusal cases and independent cleanup without sensitive payloads.
- **SC-004** No result claims human assurance, domain effect, consumer pin movement or T002 completion; unavailable live facts remain explicitly blocked.
