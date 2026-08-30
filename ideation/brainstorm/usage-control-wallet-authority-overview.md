# Usage-Control Wallet Authority Overview — Brainstorm

Status: brainstorm
Kind: reference
Summary: openXwallet can supply active grants and attested recipient proofs for bounded data-use sessions while leaving domain policy, key release, application enforcement, and public anchoring with their proper owners.
Topics: usage-control-wallet-authority, openxwallet, capability-grants, workload-identity, remote-attestation
Repository context: openXwallet neutral product and future domain-profile handoff
Captured: 2026-08-29

## Possible feats

- **Neutral usage-control profile family** — extend wallet authority to bounded
  human and workload sessions without introducing medical semantics.

## Motivation

A static license checked at download cannot govern copied plaintext. A stronger
model evaluates a short-lived capability at use time and releases keys only to
an accepted recipient session. Wallet authority is one part of that system: it
identifies holders, constrains grants, proves possession, and records exercises.

## Goals

- Represent purpose-bound, time-bound, scope-bound authority.
- Bind non-human recipients to fresh attestation evidence and session keys.
- Distinguish offered authority from product policy and actual use.
- Make revocation semantics honest about future access and existing outputs.
- Allow medical profiles to specialize the neutral core without forking it.

## Non-goals

- Releasing or storing medical-record encryption keys.
- Defining FHIR, patient, practitioner, Medicaid, or clinical-purpose semantics.
- Treating attestation as proof of safe behavior.
- Operating a blockchain adapter or public evidence log.
- Claiming a signed destruction event proves every copy was deleted.

## What the system delivers

The wallet layer can provide a signed grant, holder identity, proof of
possession, fresh workload evidence, one session-bound exercise identity, and
revocation/status references. The enforcing application and KMS consume these
inputs and emit their own decisions and events.

## System model

```text
ISSUER / HOLDER
  active grant
       |
       +---- recipient key + attestation evidence
                              |
                              v
                    PRODUCT POLICY GATE
                              |
                         KMS / SESSION
                              |
                       exercise record
```

## Cluster map

- [Synthesis: Grant and Workload Authority](usage-control-wallet-authority-synthesis-grant-workload.md)
  — combines active grants, attested recipient identity, revocation, and one
  bounded exercise.

## How it fits

The packet builds on openXwallet's existing attenuated grants and grant
exercise records. A future MedxWallet descendant can profile patient,
representative, practitioner, organization, payer, and medical-AI holders.
openChart and openPractice remain the enforcement points; openxFactory remains
the external evidence-chain owner.

## Key decisions and open questions

The main unresolved boundary is whether workload attestation fields belong in a
new holder-agnostic sibling profile or only in domain descendants. Measurement
rotation, status freshness, session termination, and linked KMS event shapes
also remain open.

## Document map

### Synthesis documents

- [Grant and Workload Authority](usage-control-wallet-authority-synthesis-grant-workload.md)

### Atomic documents

- [Active Usage-Control Grant](usage-control-wallet-authority-active-grant.md)
- [Attested Workload Recipient](usage-control-wallet-authority-attested-workload.md)
