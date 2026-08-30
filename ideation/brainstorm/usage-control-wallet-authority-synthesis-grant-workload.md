# Synthesis: Grant and Workload Authority — Brainstorm

Status: brainstorm
Kind: architecture
Summary: Combining an active capability with fresh workload evidence can authorize one bounded session without distributing a durable decryption key or confusing attestation with behavior assurance.
Topics: usage-control-wallet-authority, grant-workload-authority, active-grant, attested-workload, synthesis
Repository context: openXwallet neutral capability exercise and recipient proof composition
Captured: 2026-08-29

## Possible feats

- **Attested grant exercise** — issue one signed exercise record binding holder,
  workload, policy, session, and result.

## Members and their joints

Atomic members:
[Active Usage-Control Grant](usage-control-wallet-authority-active-grant.md),
[Attested Workload Recipient](usage-control-wallet-authority-attested-workload.md).

```text
active grant + holder proof + fresh attestation
                     |
                     v
              policy appraisal
                     |
              allow or refuse
                     |
              exercise record
```

### Authority and identity

The grant answers what authority was offered. The workload proof answers which
measured recipient requested it. Neither answers whether the clinical or
financial operation is appropriate; that remains an owner-local policy
decision.

### Revocation and session life

Status must be evaluated at session inception and according to a declared
freshness or lease rule. Revocation prevents later exercises and key releases.
An already running session needs explicit termination and output policy rather
than an assumption that changing chain state instantly erases enclave memory.

### Evidence handoff

The exercise record can be included in an owner-local use event and later
anchored through openxFactory. Public receipts should carry commitments, not the
medical purpose, patient identity, workload details, or resource scope.

## Emergent behavior

The combination supports a patient or organization granting one named workload
a limited purpose and time window while retaining precise evidence of which
identity and measured configuration exercised the grant.

## Tensions to hold

- Attestation improves confidence in a measured boundary but does not eliminate
  malicious prompts, excessive outputs, model memorization, or side channels.
- Revocation reduces future access but cannot revoke knowledge already emitted.
- Holder-neutral contracts must not absorb Medx role, consent, or FHIR
  semantics.

## Recombination opportunities

The same mechanism could authorize clinical AI, financial analysis, governed
factory workers, or other bounded services through domain-owned profiles.

## Open questions

- What neutral result vocabulary covers refused, expired, stale, terminated,
  and completed exercises?
- Should key-release evidence be part of the exercise record or a linked KMS
  event?
