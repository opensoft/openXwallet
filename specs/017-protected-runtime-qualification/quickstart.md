# Offline Qualification and Operator Runbook

Status: T002–T010 source landed; T011 isolated source candidate; no protected execution command supplied

## Issuer-Only Library Boundary

The opt-in `workload_factory_binding_runtime` package supplies `IssuerKeySource`,
`IssuerWorkloadVerifier` and the bounded `HttpsTransport`. Existing offline
entrypoints stay unchanged. One trusted embedding owns one issuer source and
shares it across its audience-specific verifiers; it must not reconstruct a source
per request. Its in-memory initiation limit is not a distributed or restart-proof
rate limiter. There is no daemon or persistent key cache.

The embedding selects the exact audience and expected claims outside worker
control. The verifier preserves `verify(token, expected, *, now)` and returns the
existing `WorkloadEvidence`; it creates no gate, signer, approval or effect.
The internal operational/source/protection preflight is now a T002 source candidate;
actual deployed composition and protection qualification remain pending.

The helper fetches only the two fixed GitHub metadata URLs, with verified TLS,
identity encoding, no redirects/credentials/cookies/ambient proxy or CA overrides.
The refresh shares a ten-second deadline across discovery and JWKS, with a
five-second connection/DNS/TLS phase and 256 KiB body limit. Every helper is
reaped on completion, timeout or interruption. The OS scheduler/process-creation
boundary is not a hard realtime guarantee.

Freshness uses the earlier discovery/key deadline, a 300-second administrative
cap, HTTP max-age or Expires, Date/Age and request duration. No-store/no-cache or
Vary-star material is not retained for reuse; zero or expired freshness refuses.
Such non-reusable responses can cause subsequent calls to refuse until the
30-second refresh limit permits a new request. There is no stale fallback.
An external set may have up to 64 entries; after validation only the selected
eligible RSA key is projected into the unchanged core's <=16-key snapshot API.

## Run Self-Contained Issuer Tests

In the declared Linux bench with the reviewed locked environment and scoped
submodules initialized, run:

```sh
python3 -m pytest tests/runtime_binding -q -rs
```

These tests inject clocks/transport or use isolated loopback TLS and synthetic
issuer keys. They do not contact the public issuer or request provider credentials.
Use normal test umask 022 inside a private evidence root. The complete repository
gate sequence remains required before publication. No live JWT, environment,
supervisor, custody deployment or human assurance is supplied by this command.

## Check This Preparation

Select feature 017 explicitly in the declared Linux bench. Run Spec Kit prerequisite
checks, strict pinned validation of the owning factory packet, and cross-artifact
requirement/task/matrix and local-link checks. The issuer package is opt-in;
no protected workflow, provider secret or executable domain lock is supplied. Optional git hooks
are disabled by the repository's auto_commit settings.

## Internal T002 Preflight

Import `RuntimeTrust` and `validate_config` from
`workload_factory_binding_runtime.config` only in the trusted embedding. Supply
bounded JSON bytes plus a separately selected approval digest, independent
readback principal/callback and trusted epoch clock. The callback must authenticate
its source and obtain actual measurements/protection context; it must not echo the
candidate or discard unsupported provider rules. There is no provider client here.

The factory-owned `supporting-docs/operational-grammar.md` in the governing change
specifies the closed internal fields. Missing/extra/duplicate/pending input refuses.
All source/dependency/composition, exact launch/run, service/state/lifecycle and
environment restriction/reviewer/bypass selections match independent readback.
Readback lives at most 60 seconds; config expiry may shorten that. Time is checked
again after readback. The result is deeply immutable, supplies no signing authority,
and must not be reused after its deadline or in place of fresh runtime preflight.

The initial narrow protection profile requires explicit User/Team reviewers,
prevented self-review, disabled admin bypass and exact allowed deployment refs.
Source review must accept this grammar before runtime use. The tests use synthetic
readback and isolated real-RSA tokens; they do not demonstrate actual provider
protection, service authentication, administrative isolation or deployment.

## Rehearse the Accepted Baseline

Use feature 016's accepted adapter/head/tree and explicit owning code selection
from codeXfactory 058 `runtime-qualification.md`. Create a mode-0700 evidence parent
outside source. Run pytest unprivileged with normal 022 test umask: applying 077
would mask its deliberate unsafe-directory fixture. Existing fixture key/file
permissions remain explicit. Preserve source trees and failed diagnostics; independently
check run-attributable fixture PIDs and key/state directories, then remove only the
owned temporary tree. Current observations are in [evidence.md](evidence.md).

## Future Protected Machine Sequence

T009's isolated tests are `test_lifecycle.py` and `test_lifecycle_process.py`.
Trusted hosting supplies a fixed registered `RunPlan`, janitor and independent
readback connectors, then binds `RunLifecycle` through the bridge's optional
`lifecycle` constructor argument and calls `run(bridge-operation)`. Success is
returned only after fresh attempt-bound cleanup verification; failure and
cancellation finalize too. A separate janitor schedule handles runner death and
expiry. The tests exercise real fixture processes/files, scoped credential
revocation, preserved replay/shared resources and an acknowledgement-without-removal
mutation. They supply no deployed scheduler, provider registration or dispatch.

T008's isolated source tests are in `test_state.py`. Provision a disposable store
as an explicit fixture/operator act, retain its initialization receipt outside
worker control, then construct `InitializedLedger` and supply it through
`StateBinding`. Runtime does not initialize, replace, reset, restore or prune.
The tests include missing/corrupt/replaced state, actual owning proof acceptance,
restart, concurrent reservations, process exit after commit, ambiguous custody
failure and new-scope recovery. The [embedding interface](contracts/runtime-embedding.md)
records the trusted-host and backup-rollback limits. No production storage setup
or recovery authorization is supplied by these source tests.

T007's isolated source tests are in `test_custody.py`. Trusted hosting binds
`ConfinedCustody.service` into `RuntimeBridge` with actual protected owning TLS
material and independent issuance/deployment readback, as described in the
[embedding interface](contracts/runtime-embedding.md). No worker endpoint,
credential, assertion or claimed confinement boolean is accepted. These tests
exercise actual owning mTLS, owning proof verification and a separate worker's
valid-preimage refusal, plus excess-permission/outage probes and cleanup.
They supply no production readback client, credential issuer or live command.

T006's isolated tests are `test_supervisor.py` and `test_supervisor_access.py`.
They launch a disposable Linux Python worker, capture its actual process
generation through the trusted controller, measure current proc/files/config,
and use the existing observation and owning proof verifier. The mTLS fixtures
test gate/worker/admin roles, valid management requests and mutation-sensitive
denial. No production service endpoint or administrative operation is supplied.
The supported launch profile and snapshot/TCB limits are in the
[embedding interface](contracts/runtime-embedding.md). Required fixtures retain
only isolated scope; live G02/P01 needs separately approved deployment evidence.

T004/T005 now have an isolated source implementation. Import `RuntimeBridge`
and its constructor bindings from the opt-in runtime modules, following the
[internal embedding interface](contracts/runtime-embedding.md). Only trusted
hosting constructs them. Tests in `test_loaders.py`, `test_runtime.py` and
`test_authenticated_loaders.py` exercise current data, each signed launch binding,
actual loopback mTLS, worker-channel certificate selection, owning proof reuse,
one-use concurrency and expiry during added preflight I/O. They authorize no live
command. Selected-source tests require the existing explicit owning-code input;
missing source remains a named skip outside the required qualification matrix.

Run the required matrix with that source explicitly selected and no skips. Use
one private temporary parent with matching TMPDIR/pytest basetemp, then verify
fixture processes and synthetic key/state cleanup. Hosting must supply actual
authenticated bounded connector/readback implementations; a class instance or
same-user TLS fixture is not deployed qualification.

1. Obtain T001 owner acceptance/commissioning, implement/review source and qualify the required offline matrix at exact accepted identities.
2. Complete [operational inputs](operational-inputs.md), including independent configuration/protection readback. Missing selections refuse.
3. Obtain scoped setup/dispatch authorization; provision only approved disposable resources and initialized private state.
4. Start the trusted embedding, separately administered supervisor and confined custody path. Worker control of trusted dependencies/credentials is denied.
5. Run the real protected workload and [matrix](qualification-matrix.md), retaining only safe references/digests/results.
6. Exercise success/failure/cancel with independent fresh absence readback. Missing cleanup or trust evidence fails qualification.
7. Record owner machine acceptance and hand off its portion of T002. Human broker acceptance and domain marker/consent tasks remain separate.

No placeholder live command is supplied: implementation, selected services and
operational grant do not yet exist. Feedback remains deferred; neither blocked
write is part of this preparation or an inferred future authorization.

## Internal T011 Receipt and Error Handling

`workload_factory_binding_runtime.evidence` is an adapter-internal reporting API.
It changes no openWallet proof, registry or custody API and no openMFA possession
receipt contract. Its canonical JSON report is not signed authority, owner
acceptance, human assurance, a dependency lock or a deployment authorization.
Only `source-conformance` and `isolated-fixture` are supported. Requests for
`protected-machine` refuse; T012/T014 hosting and any protected-scope promotion
need separate reviewed inputs and operational commissioning.

Trusted hosting captures `ValidatedConfig` before the operation. That snapshot
contains only the frozen approved selection and digest/time metadata for its
independently authenticated configuration/protection readback. It must come from
`validate_config`; constructor types alone do not authenticate a deployment.
Retain the snapshot for historical reporting, never reuse it as live preflight
after expiry. Select receipt scope, plan, clock and observed cases outside worker
control. This module has no worker JSON endpoint, file resolver or provider client.

Run the prescribed complete repository gates and the T010 fixed-collection matrix.
Obtain each `CaseResult` from the actual trusted harness: case ID, collected,
passed, failures, errors, skipped, observation time and retained artifact digest.
Do not invent counts or mark an unexecuted negative vector passed. The report
checks shape, bounds, duplicate IDs, count consistency and time, but does not
rerun tests or authenticate supplied observations. T010 enforces the complete
reviewed parameter identities. Missing cases are explicitly `not-performed`;
zero collection, failures/errors/skips and incomplete reports cannot pass.

For fixture execution, invoke the existing synchronous `RunLifecycle.run` and
independently verify any owning proof before recording its result. Capture the
actual operation error/cancellation; successful cleanup cannot erase an operation
failure. After run/finalize completes, `cleanup_verification` contains the latest-
started attempt's verified checkpoint or `None`; each retry clears old success.
The checkpoint binds plan/scope, random attempt, independent readback identity,
record digest and observation/check/deadline times. It retains no raw provider
record. Readback must follow the latest reported case observation, match the
selected case/run/attempt/configuration and preserve selected replay/shared state.
A janitor acknowledgement, credential outage or missing independent reader is
not cleanup evidence. Hosting serializes its report assembly after operation and
cleanup; a Python checkpoint is not independent administrative attestation.

The trusted embedding supplies these already-obtained variables; this is a
library call, not a live setup or dispatch command:

```python
from workload_factory_binding_runtime.evidence import build_receipt

receipt_bytes = build_receipt(
    scope="isolated-fixture", selected=selected, cases=observed_cases,
    started_at=started_at, now=trusted_clock(), plan=lifecycle.plan,
    cleanup=lifecycle.cleanup_verification, error=operation_error,
)
```

Keep counts and timestamps case/run bound. For source-only reports omit plan and
cleanup. For fixture reports absent cleanup remains `missing` and prevents pass.
Wrong scope/plan/configuration/time/digest refuses with a fixed error. A complete
report still sets protected-machine qualification, human approval, domain effect
and consumer-lock claims to false. P01 and deployed G02/G03/L01 remain explicitly
`not-performed`. A report created later does not extend the original selection,
proof or readback deadline or turn archived absence into current absence.

The closed projection emits source commit/content digests and hashes repository,
path, case and opaque service/state/retention references. Map them through the
independently retained approved non-secret selection. It emits no token, JWK,
private key, credential/factor response, browser state, raw proof, provider body,
exception args/notes/causes or traceback. `safe_error(error)` returns only a fixed
allowlisted code without calling exception `str`/`repr`. Never publish a raw
exception, traceback/locals dump or arbitrary metadata alongside the report.
The reporting boundary exposes `invalid-qualification-evidence` on bad input.

`build_receipt` returns immutable canonical bytes and performs no file I/O. The
operator's separately selected retention sink must be private (0700 parent, 0600
file), use an exclusive/atomic write and retain its content digest plus the exact
source/run selection. Keep raw temporary evidence in its protected run boundary;
never put keys, tokens, provider responses or browser state in Git or public CI
artifacts. An internal source/fixture report is not a retention-policy setup grant.

On failure or cancellation retain only the safe report and diagnostics. Revoke
and remove only the registered run-owned generations, independently read back
absence/revocation and preserved replay/shared resources, and retry via the
approved janitor if incomplete. Never reset consumed replay state to retry a
proof. Hard runner death still needs the independent scheduler/readback actor.
Do not infer cleanup from a finally block or a successful receipt write. Missing
live services, operational selections or authority stay blocked/not-performed.
