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

Concrete operational grammar, validator and integrity binding are implementation
tasks after owner acceptance. The factory proposal owns their meaning; no executable
configuration is supplied now. Neutral custody/proof/receipt contracts are not copied
or changed. A new custody-side assertion requirement blocks on its owning API decision.
