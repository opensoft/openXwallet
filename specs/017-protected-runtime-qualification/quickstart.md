# Issuer Slice Checks and Future Execution

Status: bounded issuer source candidate; no protected execution command supplied

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
