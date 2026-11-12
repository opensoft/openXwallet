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
