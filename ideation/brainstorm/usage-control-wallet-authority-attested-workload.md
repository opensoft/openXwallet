# Attested Workload Recipient — Brainstorm

Status: brainstorm
Kind: architecture
Summary: A wallet recipient could identify an attested workload and supervising authority without treating remote attestation as proof that the workload is safe or non-exfiltrating.
Topics: usage-control-wallet-authority, attested-workload, openxwallet, workload-identity, remote-attestation
Repository context: openXwallet neutral recipient identity and proof binding
Captured: 2026-08-29

## Possible feats

- **Attested workload holder profile** — bind a workload key to approved
  measurements, model identity, operator, supervisor, and attestation policy.
- **Session-bound attestation proof** — prevent replay by binding evidence to
  the grant, nonce, requested resource, purpose, and recipient session key.

## Focus

This document isolates how a non-human recipient can prove which measured
workload is requesting an exercise. It does not define a TEE, KMS, AI model, or
medical policy.

## Proposed model

The candidate recipient proof combines:

```text
holder public key
workload identity and version
model and runtime identifiers
attestation technology and verifier policy
measured configuration or approved-class reference
operator and supervising-authority references
ephemeral session key
fresh nonce
grant, purpose, and resource commitments
attestation result and verifier identity
```

The attestation quote must be bound to the current protocol session. A valid
quote is evidence that a verifier accepted a measured hardware/software state.
It is not proof that the code is bug-free, that it will not leak data through
approved outputs, that it ran continuously after attestation, or that all
side-channel risks are controlled.

The wallet can identify the recipient and retain proof provenance. The KMS and
product enforcement point independently decide whether that proof satisfies
the current release policy.

## Interfaces and boundaries

openXwallet owns the holder and proof envelope. Attestation vendors own quote
formats. A policy service owns acceptable measurements and freshness. The KMS
owns key release. The application owns egress controls, output schemas, rate
limits, logs, and session termination.

The design should follow the appraisal/evidence distinction in
[IETF RFC 9334](https://www.rfc-editor.org/rfc/rfc9334.html). Cloud-specific
integrations, such as AWS Nitro Enclaves or Azure confidential computing, stay
outside the neutral wallet core.

## Alternatives and tensions

- Exact measurement allowlists maximize specificity but make routine model and
  runtime upgrades governance events.
- Policy-class credentials reduce churn but transfer more trust to the issuer.
- A TEE protects against selected host threats while adding hardware, firmware,
  verifier, side-channel, and availability dependencies.

## Open questions

- Does one wallet identity survive workload upgrades, or does each measured
  release receive a distinct holder key?
- Which supervisor statement is required for an AI clinical workload?
- How does a verifier express degraded or stale evidence without an implicit
  pass?

## Relationships

The authority being exercised is defined in
[Active Usage-Control Grant](usage-control-wallet-authority-active-grant.md).
Their joint lifecycle is described in
[Synthesis: Grant and Workload Authority](usage-control-wallet-authority-synthesis-grant-workload.md).
