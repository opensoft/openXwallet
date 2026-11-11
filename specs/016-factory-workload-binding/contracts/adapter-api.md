# Candidate adapter API

Canonical composition owner: `opensoft/openxFactory`,
`openspec/changes/add-workload-factory-binding/supporting-docs/profile.md`.
This describes an internal candidate interface, not a published standard.

`ProofGate` is constructed by the trusted embedding process with current policy/
record loader, issuer verifier, registry, trusted challenge loader, replay ledger,
opaque signer, clock and owning `create_proof` callback. Workers select none of
these. `sign(challenge_id, request, token, observation)` returns a possession
proof and local checked authority facts, explicitly with no approval.

Request is exactly `act`, `object_ref`, `run_id`, `run_attempt`.
`request_digest(policy, request)` is used by the trusted challenge creator.
`observe_artifacts` reads supervisor-selected paths/configuration and signs the
result bound to request context. Paths/key/context come from trusted supervisor
configuration, not worker input. Tests never present this as live attestation.

The embedding must authenticate callers, own challenge creation, protect loader/
custody credentials, refresh trust and deploy an independent observer. Errors
contain fixed codes, never token bodies or private material.

Unsupported grant constraints (including distinct-holder references) and unknown authority fields refuse. The selected wallet public-key material must match the current registry; the observer launches the selected reference worker and hashes its source/configuration independently. No hostile OS-isolation claim is made.
