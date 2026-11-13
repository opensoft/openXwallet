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

The read deadline is supplied inside the guarded connector invocation, after its
fresh preflight. Capturing an earlier deadline before that preflight would allow
I/O beyond a newly shortened protection/channel lease; the regression checks
that the connector receives the current earliest deadline.

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

## Isolated T006 realization

`SupervisedBridge` is an opt-in trusted wrapper with the existing bridge and a
selected `BoundService` supervisor. Its three-argument `sign(challenge_id,
request, token)` obtains an observation through the authenticated connector,
verifies it with the existing verifier, enforces the current deadline, and calls
the unchanged four-argument bridge. It sends no worker policy, key, PID, path,
measurement or loader. The connector's `observe(payload, *, deadline)` must
authenticate the selected service and propagate the epoch deadline to the observer.

`SupervisorObserver` has its own protected configuration/readback, current-source
connectors, issuer source, observation key and `ProcessLaunch`. The authenticated
server supplies `SupervisorPeer` outside the body. The protected gate allowlist
must match the selected supervisor service's principal/credential pair and differ
from the worker channel. Unexpected peer identities fail before protected configuration I/O.
The observation key must match the policy's supervisor public key and differ from
the wallet key. Only the existing domain-separated observation can be produced;
there is no production key-export, generic-sign or policy-management operation.

The trusted launcher captures the PID/start-time generation and selects resolved
worker/configuration/cwd paths, source artifacts and an explicit executable digest.
The supported command is exactly `executable -I -B worker configuration`. The
observer checks actual Linux proc start time/liveness, argv, cwd and executable
bytes, with bounded regular-file reads and no symlink/FIFO configuration acceptance.
It reads actual worker configuration and sources, including this measurement
module, and compares them with protected selection. The internal worker projection
binds launch/source/dependency/service references, wallet/key/custody binding,
authority refs and the supervisor public key, excluding self-referential hashes.

Actual PID/start time, argv/cwd/executable digest and worker configuration enter
the unchanged artifact/composition digest structure. The worker cannot supply the
expected projection. A controller can calculate a candidate composition after
launch; that calculation does not itself grant source or operational approval.
The observer rechecks authority, protection, process/files and freshness after
signing before returning any observation. The signed format and maximum 60-second
validity remain unchanged, shortened by every accepted source/peer/client deadline.

Before/after snapshots are not continuous liveness or memory/model attestation.
They cannot prove that a program honored configuration, detect a change restored
between snapshots, or defeat a hostile host. Deployment must enforce approved
read-only launch sources and genuinely separate supervisor administration/key/
policy/control access. Actual container/image/dependency selection remains an
independent readback obligation. Filesystem paths and process metadata stay
host-local; the returned observation carries their digest, not raw metadata/key.

Isolated TLS fixtures use distinct gate/worker/admin credentials and real
authorization routes to test observation, policy and key-control denial. An
excess-permission mutation makes the denial probe fail; an outage does not pass
as denial. Fixture admin routes are test-only, not a production API. Same-user
processes cannot establish worker OS key secrecy or deployed administrative
isolation. Those G02/P01 facts remain pending live gates.

## Isolated T007 realization

Trusted hosting constructs `ConfinedCustody` with the selected owning `TLSClient`
and `RemoteSigner` constructors, intrinsic `ServiceIdentity`, protected
`CustodyMaterial`, approved runtime trust and `CustodyTrust`. Its `service` is
the custody `BoundService` supplied to `RuntimeBridge`; `sign(message)` and the
neutral service protocol remain unchanged. The worker receives none of these
constructor capabilities, material paths or owning primitive.

This narrow TLS embedding binds the selected custody trust digest to the actual
CA file bytes and the issued certificate digest to the actual DER certificate.
Endpoint, certificate, CA and private-key material are fixed at construction;
bounded no-follow regular-file reads check owner, link count and private-key
permissions before/after construction and each signing call. Key bytes/digests
stay internal. Hosting must enforce immutable protected paths/parents: snapshots
cannot detect a change restored between reads or defend against a hostile host.

`CustodyTrust` independently selects deployment, boundary, issuance and gate
principal references. Its authenticated `load_access(deadline=epoch)` derives
`CustodyAccess` from actual protected issuance/deployment state, not a candidate
echo. This internal capability record binds those approvals to the canonical
approved configuration/source digest, case/run/attempt, exact service identity,
actual certificate/endpoint and sign-only subject/key/custody scope. Gate principal
must differ from worker, supervisor and runtime-readback principals. Readback is
valid at most 60 seconds. The per-use earliest runtime/readback/issuance deadline
never extends; time/configuration/material/issuance checks repeat after signing.
Post-sign refusal cannot undo an already-created signature.

The bridge invokes the internal `sign_for_use(message, *, deadline)` seam after
fresh guarded preflight. It passes the outer proof-use deadline inward, before
added custody readback, and retains the returned earliest custody deadline through
all later proof checks. The neutral owning signer still receives only `sign(message)`.
Standalone `ConfinedCustody.sign(message)` is a trusted compatibility seam; it
cannot know an enclosing proof deadline and is not the runtime bridge path.

There is no new custody-side per-use assertion: unsupported trust models refuse
with `custody-owner-decision-required`. Hosting callbacks must authenticate and
bound I/O, independently measure the approved source/configuration selection,
and deny worker access to issuance/control planes and credential files. Matching
Python records or separate certificate labels do not establish these facts.

The G03 fixture uses the selected clean owning source, real mTLS custody and an
owning-verifier-accepted gated proof. A separate worker process first resolves the
current binding, then submits that proof's exact valid canonical signing preimage
with its resolve-only credential. Only explicit service refusal passes. A disposable
excess-sign-permission mutation and an outage both make the probe fail. Fixture
PKI/state/process cleanup is checked on success and injected failure. Same-user
fixtures do not qualify deployed issuance administration, OS/network confinement,
worker key-file secrecy, source/image immutability or live G03/P01.

## Isolated T008 realization

Trusted hosting supplies `InitializedLedger` in the existing `StateBinding`.
Its constructor requires a selected private directory, runtime trust and
`StateTrust`: exact state references, independently recorded initialization
identity, authenticated readback principal and bounded `load_access(deadline=epoch)`.
The readback joins those references and initialization to the exact approved
configuration, case/run/attempt and current active recovery/retention scope.
Worker flags or a missing initialization receipt cannot establish readiness.
The existing generic `StateBinding` is a compatibility seam, not evidence of T008;
this provided runtime path uses `InitializedLedger` and its fresh checks.

The operator explicitly provisions the store before runtime using the existing
initializer and independently records `inspect_initialized_state()` metadata.
Runtime never calls the initializer or implicitly captures a new expected identity.
Restart reuses the original receipt. Directory/database device and inode metadata
must match; private owner/mode/link checks, the existing exact schema/version,
full SQLite integrity and DELETE-journal mode are checked. Missing, blank,
corrupt, replaced or unsafe state refuses without initialization/repair. Existing
hot-journal recovery is normal transaction recovery, not backup restoration.
WAL/SHM and unsupported modes refuse in this narrow existing-store profile.

SQLite connections explicitly use `mode=rw`, so loss between metadata check and
connect cannot create a file. Integrity work and lock timeout are capped by three
seconds and the remaining use budget; progress deadline is set before connecting. Epoch
time is rechecked after blocking I/O and lock acquisition, before insert/commit
and after reservation. State preflight and `reserve_for_use` exchange the earliest
deadline and latest checked time with the bridge. Internal `StateUse` carries
those two checkpoints; the child retains the parent's clock floor before I/O,
and the parent retains the child's newest sample before sampling again. State
preflight repeats through the final proof check. Ordinary
reservation, uniqueness and reserve-before-sign semantics are unchanged.

Durably committed reservations survive restart, process exit without a response,
ambiguous custody failure and later readback refusal. No failure path deletes or
prunes them. Failures before durable reservation return no proof; this is not a
claim that an uncommitted transaction has reserved an identity. Readback expiry,
revocation or recovery-required status fails closed. Recovery requires operator
revocation and a new approved store/initialization and workload scope; it is not
an automatic same-scope reset or restoration command.

Private file metadata and integrity checks cannot detect hostile in-place edits,
an otherwise valid backup restored into the same inode, or changes restored
between observations. Hosting must protect parent paths, database files and
initialization/recovery administration and prohibit active-scope restore. Actual
authenticated storage readback, retention enforcement and OS/admin isolation
remain deployed acceptance inputs. Same-user isolated tests do not qualify them.

## Isolated T009 realization

Trusted hosting creates `RunLifecycle` from an operator-selected `RunPlan`, current
runtime trust, a selected janitor `BoundService`, an independent readback capability
and a separate cleanup clock. The plan binds exact configuration/case/run/attempt,
lease/cleanup/receipt-retention references, fixed lease interval and bounded cleanup
budget (1–60 seconds). Its bounded manifest names each resource's immutable provider
generation, kind and run/retained/shared retention. References and generations are
unique. The selected replay store is mandatory retained state in both the client
and janitor plan validation. No worker supplies a plan, callback, path or peer.

The trusted bridge's optional `lifecycle` constructor argument uses this capability
before/after guarded proof I/O and through the final check. Earliest expiry and
latest clock checkpoints pass both ways; an active one-shot run retains the same
checkpoints across bridge calls. Existing neutral proof and worker-facing methods
stay unchanged. A bridge without lifecycle is a compatibility seam, not L01 evidence.
Hosting invokes `run(bridge-operation)`; the operation callback is trusted code,
never deserialized from a worker. This is a synchronous embedding, not an async
server or a generic provider-execution API.

`RunJanitor` holds the approved fixed plan and authenticates transport-derived
`JanitorPeer` before protected I/O. It rejects other plan references, caps the whole
attempt budget before lookup and compares current registration to the fixed digest.
It loads protected lease records, closes the lease, and attempts
each run resource's cleanup. Current provider ownership and generation must match
the registered scope. The cleanup callback must conditionally revoke/remove that
exact generation/owner; it cannot use a worker path or perform an unscoped sweep.
Retained/shared resources never enter deletion callbacks. Partial failure still
attempts remaining scoped resources. Registrations and ownership must be durable
before credentials are issued; the provider implements those atomic ownership and
conditional-operation guarantees, not these Python types.

Success, ordinary failure and cancellation each invoke finalization. Cleanup uses
its own clock/authority and the accepted fixed plan, so expired/lost proof
configuration does not disable resource cleanup. The cleanup actor's acknowledgement
is never sufficient. A distinct principal/credential supplies independent readback
bound to the exact plan, scope, fresh timestamp and a new random cleanup-attempt
reference. Missing/stale/duplicate/mismatched readback refuses. Every run resource
must be absent; credentials must also be revoked. Every retained/shared resource
must remain present at its selected generation. Internal `CleanupVerification` is
a checkpoint; full redacted receipt construction remains T011.

The bridge publishes its final clock/deadline checkpoint into the active run without
another clock sample or I/O. After cleanup verification, the runner retains its latest
time and rechecks the proof-use deadline before returning the operation value; it
does not revalidate the intentionally closed lease.
Ordinary operation failures produce a fixed error; operation cancellation finalizes
before propagation. Control cancellation during finalization may interrupt it and
requires independent sweep/retry. Cleanup uncertainty fails qualification even if the operation itself
succeeded. Post-sign failure cannot undo a signature; consumed replay state remains.
No callback can preempt arbitrary hung provider code: all connectors/provider
callbacks must enforce the supplied deadline and their own I/O budget.

Runner finally cannot execute after hard death. An independently hosted scheduler
must invoke the janitor's local `sweep` capability when the fixed lease expires or
is revoked/cancelled/closed. It refuses an active unexpired run and can retry cleanup
without live proof configuration. Scheduler availability, durable registrations,
actual provider revocation/absence, retention and independent readback/administration
are mandatory deployed inputs; this library supplies no provider setup or daemon.

Isolated tests use separate janitor and readback processes with host-selected OS
pipe capabilities and bounded JSON frames. They stop/reap actual owned processes,
revoke a scoped fixture credential and remove run files while preserving the actual
replay database and shared sentinel. Owning proofs verify. Success/failure/cancel,
hard-runner-exit expiry cleanup, forged worker peer denial, missing reader,
acknowledgement-without-removal and replacement-generation refusal are exercised.
Same-user fixtures do not prove deployed OS/admin isolation or hostile-host safety.

## Isolated T011 realization

`ValidatedConfig` additionally retains configuration/protection readback digest,
principal digest and observation/expiry timestamps. It retains no raw readback.
`CleanupVerification` additionally records independent cleanup readback/identity
and attempt digests with observed/check/expiry times. `RunLifecycle` publishes its
latest-started successful checkpoint through `cleanup_verification`; starting a
retry clears previous success, and an older completion cannot overwrite a newer
attempt. The property is cleanup evidence only, never operation success.

`evidence.build_receipt` emits at most 16 KiB of canonical JSON from a closed
projection of trusted selected configuration, a tuple of `CaseResult` observations,
explicit scope and optional exact plan/checkpoint plus operation error. It reports
sources, dependency/composition, protection/readback, case/run/attempt, results and
cleanup via fixed fields and digests; repository/path/reference strings are hashed.
No arbitrary payload/metadata or exception text is copied. `safe_error` uses only
fixed codes, never exception stringification. There is no sink or provider I/O.

These are structural historical reports, not authentication of arbitrary Python
objects or supplied test observations. Hosting owns authenticated measurements,
complete actual case collection, owning proof verification, operation outcome and
private retention. The T010 collection contract remains the substantive source
conformance gate. Only source-conformance/isolated-fixture scopes are implemented;
protected-machine promotion refuses until separately reviewed operational hosting.
Missing case/cleanup evidence prevents pass, wrong bindings refuse, and every
report explicitly withholds protected qualification, human/domain authority and
consumer-lock claims. Neutral proof/custody/possession receipt contracts stay unchanged.
