# Proposed Runtime Embedding Interface

Status: draft; adapter-internal API under factory composition, not a published standard

The accepted `ProofGate` and `WorkloadVerifier` interfaces stay unchanged. An opt-in
runtime composition validates the factory-owned operational projection, accepted
source/dependencies and actual embedding/protection evidence before constructing
trusted dependencies. The worker never constructs that composition.

Its issuer adapter implements `verify(token, expected, *, now)` and returns accepted
`WorkloadEvidence` with the bounded snapshot deadline. It uses selected HTTPS
transport and delegates signature/claim verification to the accepted core. Refresh
does not change expected issuer/audience/claims.

Trusted inputs include current-record and authenticated challenge loaders, supervisor
client/trust, opaque owning signer/registry, protected state and clocks. The hosting
embedding authenticates and bounds its worker channel and selected services. A
worker boolean, URL, path or loader is not evidence of authentication. Real deployment
acceptance must independently establish that hosting boundary; this feature does not
standardize a public service protocol.

Worker inputs remain the challenge ID, exact request, token and bound observation.
A wrapper may obtain observation through the selected supervisor, but cannot promote
worker measurement into supervisor evidence. Output stays possession proof plus
checked local authority facts, with `human_approval` false. No apply/marker/consent
operation is exposed.

T002 realizes an internal `validate_config(raw, *, trust)` preflight in `config.py`.
The factory proposal's `supporting-docs/operational-grammar.md` owns the grammar's
meaning. A trusted `RuntimeTrust` supplies the independently approved canonical
digest, readback principal/callback and clock outside worker control. The callback
must authenticate its source and measure actual source/protection context, never
echo candidate data or ignore unsupported provider rules. Python constructor types
do not establish that deployment boundary. The deeply immutable `ValidatedConfig`
is valid only until the earlier configuration/readback deadline (readback at most
60 seconds). Later runtime composition must rerun preflight and enforce that deadline.
It does not construct services or prove deployed isolation. No executable live
configuration, consumer lock or protected dispatch is supplied. Neutral custody/
proof/receipt contracts stay unchanged; new assertions need the owning API decision.

## Isolated T004/T005 realization

`RuntimeBridge` is constructed only by trusted hosting with `load_config`, accepted
`RuntimeTrust`, `load_worker_context`, selected `services`, `StateBinding`, one
shared `IssuerKeySource`, and the owning `create_proof` primitive. Its worker-facing
method retains `sign(challenge_id, request, token, observation)`; there is no worker
parameter for credentials, service URLs, loaders, expected claims or authentication.

Each `BoundService` pairs a connector's intrinsic `ServiceIdentity` (service,
principal, credential and trust references) with its opaque target. Hosting must
derive those identities from authenticated protected connector configuration,
not copy them from candidate/worker data. Records/challenge targets implement
`read(operation, reference, *, deadline)` with a UTC epoch deadline and current
UTF-8 JSON bytes bounded to 16 KiB. The fixed operations are `policy` and
`challenge`; the reference is a lookup key, never a URL/path/resolver. Registry
and custody targets retain the owning `resolve` and `sign` interfaces. All blocking
connectors must bound their I/O; post-call checks are not a way to preempt an
arbitrary hung Python callback. No generic provider client or public server API
is standardized by this internal composition.

The hosting callback independently authenticates/bounds its current worker channel
and returns a `WorkerContext` bound to the exact selected service identity,
configuration digest, case, run/attempt and at most 60-second validity. Worker
booleans/dictionaries cannot supply this context. Python classes and matching
metadata still do not establish actual transport authentication or administrative
isolation: the selected connectors/hosting must enforce those boundaries. The
loopback tests exercise real mTLS and certificate refusal within isolated fixtures.

Current policy bytes must match the approved canonical policy digest, revision,
claims, binding, grant and composition. The loader reuses existing policy/grant
validation. Current challenge bytes use the existing factory projection, with its
digest recomputed, selected authenticated service as issuer, and exact subject,
request/run and deadline binding. Worker-supplied full records are not accepted.

Each proof use is independent. Preflight and channel checks repeat around trusted
I/O, before reservation and custody, and after signing. The earliest observed
token/key, signed-observation, policy/grant, challenge, registry, configuration,
readback and channel deadline can only shorten that use. A worker-provided
observation expiry may initially only shorten it; the unchanged gate still verifies
the entire observation before reservation. Failures after reservation leave it
consumed and emit no result. Post-sign refusal cannot undo a signature already made.

`StateBinding` identifies the selected existing ledger; it does not provision,
initialize, recover or qualify storage. Actual source measurement, supervisor
independence, custody confinement, initialized-state/recovery and lifecycle gates
remain T006–T009 and deployed acceptance work. The isolated composition yields
only the existing possession result with `human_approval` false.
