# Portable bootstrap authority candidate

Status: commissioned source candidate; isolated fixture only. Setup and protected
dispatch are unauthorized. Feedback remains deferred; neither historical blocked
write is replayed. Source acceptance and operational qualification remain separate.

## Scope and ownership

Factory proposal: `opensoft/openXfactory`,
`openspec/changes/add-portable-bootstrap-authority/`. Feature 017 tasks T012C–F
are the sole implementation list. This adapter candidate is stacked on T013
refresh PR #61; opening this candidate does not authorize landing #61.

The optional `scripts/workload_factory_binding_runtime/reference_authority/`
package supplies an explicitly initialized SQLite store, loopback-only mTLS
server, pinned client, and `AuthoritySession` bridge into existing bootstrap and
admission. There is no operational host selection or provider setup path.
`operational_bindings()` continues to refuse before outputs or OIDC.

## Trust and retained state

The operator inserts an immutable static selection without run/attempt fields.
An independently selected controller Ed25519 key signs a closed, current fixture
observation of the assigned context. Operator/controller/reader/worker permissions
come from actual mTLS peer fingerprints, selected outside request bodies. Reader
cannot authorize or observe; worker has no authority action. The client validates
CA, hostname, server fingerprint, fixture profile, exact context and configuration
projection before producing adapter capabilities. Bootstrap and operation reads
are fresh; no bundle cache bypasses revocation.

Claim uses `BEGIN IMMEDIATE`, DELETE journal, synchronous FULL and bounded waits.
One complete context wins. Same-context refresh and restart preserve the binding;
a new run or attempt refuses. Revocation cannot reactivate or clear a binding.
Missing, corrupt, unsafe or observably replaced state refuses without reset.
Initialization returns an inode receipt which must be retained independently;
startup cannot recapture an arbitrary replacement. Retained clock high-water
checks refuse regression. Host compromise and valid in-place backup rollback are
outside this reference boundary; recovery requires a separately approved scope.

## Rehearsal and reproduction

Use the owning Python bench, reviewed dependency environment, private temporary
parent and explicitly selected accepted owning-wallet source. Run:

```text
python -B -m pytest tests/runtime_binding/test_authority.py tests/runtime_binding/test_authority_transport.py tests/runtime_binding/test_authority_flow.py -q
```

The full governed qualification remains `tests/runtime_binding/conformance.py`
through `isolation.py` in a loopback-only Linux network namespace with capabilities
and supplementary groups dropped, no privilege regain, read-only source mounts,
and a private writable evidence root. The committed matrix contract includes
B01 (durable binding), B02 (authenticated transport) and B03 (integrated flow).
CI uses committed counts, sorted full-node fingerprints and substantive anchors;
it never regenerates expectations from the run being qualified.

The integrated fixture prepares real owning registry/key/custody before freezing
static approval, registers the assigned observation, binds the full config, and
checks existing admission/scheduler/lease. It creates and verifies an owning wallet
proof through remote custody. A direct worker request with a valid proof preimage
must receive explicit denial. The replay gate refuses a second use. Success,
failure after proof, cancellation and a hard-killed runner all require independent
janitor/readback confirmation of run-resource removal, credential revocation,
shared-resource preservation and retained replay/authority rows.

Issuer and control-plane observations are simulated. Local mTLS and signatures
exercise real cryptography; same-user fixture processes and keys do not establish
deployed OS/administrative isolation, actual GitHub authentication, provider
readback, human approval, setup authority or runtime acceptance. T013/T014/T015
owner and operation gates remain incomplete.

## Candidate review corrections

The nine-role local panel covered architecture, performance, security, QA, static
analysis, API integration, persistence, reliability and simplicity. Corrections
move TLS handshakes into bounded workers, test worker claim and operation denial,
close all fixture processes even during generator cancellation/startup failure,
handle journal disappearance during concurrent refresh, close initializer database
connections explicitly, and retain trusted clock high-water observations while
rolling back failed or cancelled business operations. Negative tests isolate the
intended refusal; integrated replay checks the underlying ledger refusal while the
lease is still active, before cleanup can mask it. The corrected focused suite
passes all 78 tests. Final full-suite, isolated-matrix and hosted-CI evidence is
recorded separately; snippet analysis does not substitute for hosted review.
