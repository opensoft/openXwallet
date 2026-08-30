# Active Usage-Control Grant — Brainstorm

Status: brainstorm
Kind: architecture
Summary: openXwallet could express a short-lived, purpose-bound capability whose exercise is revalidated for each protected session rather than treated as a static download license.
Topics: usage-control-wallet-authority, active-grant, openxwallet, capability-grants, consent
Repository context: openXwallet holder-agnostic grant and exercise semantics
Captured: 2026-08-29

## Possible feats

- **Usage-control grant profile** — bind recipient, purpose, scope, duration,
  execution constraints, output limits, delegation, and live status.
- **Session-bound grant exercise** — record which grant, holder, workload, and
  policy decision authorized one protected session.

## Focus

This document isolates the wallet-level authority needed for usage control.
The grant is not a durable decryption key and does not itself release records.
It is a signed capability that a policy enforcement point and key service can
evaluate at use time.

## Proposed model

An active grant could declare:

```text
issuer and authority basis
recipient holder or workload key
opaque resource-set commitment
allowed operations
purpose reference
not-before and expiry
delegation ceiling
revocation/status reference
required execution-class reference
permitted output class
break-glass policy reference
nonce and proof-of-possession requirements
```

Each exercise should bind the grant version, request, recipient proof,
evaluated status, session identity, policy decision reference, and result. A
retry should be distinguishable from a second exercise. Revocation governs
future use and key release; it cannot recall plaintext or derived outputs that
were already lawfully disclosed.

The grant stays holder-agnostic. Patient, practitioner, organization, payer,
and medical-AI meanings belong in domain profiles such as the proposed
MedxWallet descendant.

## Interfaces and boundaries

openXwallet owns grant structure, signatures, attenuation, exercise identity,
status references, and revocation semantics. A domain owns purpose and resource
vocabularies. The enforcing product owns the allow/refuse decision. A KMS owns
key release and destruction operations. openxFactory owns public evidence
checkpointing.

FHIR Consent may map into a medical grant, but FHIR Consent is a portable policy
representation rather than an enforcement engine. The wallet contract should
not make FHIR a neutral dependency.

## Alternatives and tensions

- Per-record grants minimize scope but can create unmanageable cardinality;
  record-set grants reduce overhead while increasing blast radius.
- Continuous status checks improve revocation latency but introduce availability
  and privacy dependencies.
- A grant can name a concrete workload measurement or an execution-class policy.
  Concrete measurements are precise but create frequent update churn.

## Open questions

- Which execution constraints are neutral enough to enter the wallet contract?
- Is status checked per operation, per session, or through a bounded lease?
- How are successor grants linked when policy or scope changes mid-session?

## Relationships

Workload binding is explored in
[Attested Workload Recipient](usage-control-wallet-authority-attested-workload.md).
Their authority flow is related in
[Synthesis: Grant and Workload Authority](usage-control-wallet-authority-synthesis-grant-workload.md).
