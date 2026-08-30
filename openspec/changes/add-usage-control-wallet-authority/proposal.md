---
Status: draft
Repository-owner ratification: pending
---

## Why

The core can express an attenuated grant and a proof-of-possession exercise, but
it cannot yet represent one bounded data-use session whose purpose, live status,
fresh workload appraisal, replay binding, and external KMS evidence can be
evaluated together. A neutral profile is needed before domain descendants invent
incompatible or medically specific versions of that authority flow.

## What Changes

- Add a holder-neutral usage-control profile over the existing wallet grant and
  exercise contracts. An active usage-control grant binds a purpose reference,
  scope or opaque resource-set commitment, validity interval, and explicit live
  status and revocation references without carrying a key or bearer secret.
- Add an attested workload recipient proof bound to the audience wallet, current
  grant, purpose and resource commitments, request digest, fresh nonce, and an
  ephemeral session key. The proof records verifier appraisal of measured state;
  it never asserts that the workload is safe, non-exfiltrating, or continuously
  trustworthy after appraisal.
- Add a session-bound usage-control exercise that binds one grant evaluation,
  recipient proof, nonce, request, policy-decision reference, status evaluation,
  and result. Reuse of a nonce or proof for another session is refused, and a
  retry is a distinct exercise.
- Link an exercise to KMS-owned evidence by immutable reference and digest when a
  KMS decision or event exists, while making absence explicit when no KMS was
  invoked. openXwallet does not release keys or interpret the linked event as its
  own enforcement act.
- Keep purpose and resource meanings external. The profile introduces no FHIR,
  Medx, patient, practitioner, clinical, or other domain vocabulary.
- Preserve every existing kind and field name. The new proof and bindings require
  an additive sibling profile; the core `xfactory_wallet_grant` and
  `xfactory_wallet_grant_exercise` shapes and the agent-composition profile are
  not renamed or redefined.

## Capabilities

### New Capabilities

- `openxwallet-usage-control-profile`: Holder-neutral active-grant, attested
  workload recipient, session/replay, status/revocation, and linked KMS-evidence
  requirements composed over the existing `openxwallet` core.

### Modified Capabilities

None.

## Governance Gates

**Repository-owner ratification is unconditional.** No Speckit feature, branch,
or worktree may be created and no implementation may begin until the repository
owner ratifies this exact proposal, design, and delta spec. Ratification becomes
effective only when this proposal carries a durable approval record naming the
owner and authority, UTC time, exact approved packet revision, approved artifact
set, and verbatim ruling, and the front matter reads `Status: ratified` and
`Repository-owner ratification: recorded`.

**Constitution governance is separate.** This repository currently has no
adopted `.specify/memory/constitution.md`. Constitution adoption, and a meaningful
Constitution Check of this feature against the adopted principles, are a separate
governance prerequisite to the Speckit plan phase. They are not requirements,
deliverables, or implementation tasks of this product change; Speckit planning
remains blocked until their independently recorded evidence exists.

## Impact

- Adds one sibling contract family with profile records for the active grant
  binding, recipient appraisal proof, and session exercise binding, plus packaged
  positive and negative examples and validator coverage.
- Adds owned manifest members and release bookkeeping; the release version is
  allocated only during realization, and pinning consumers must adopt the
  resulting bundle before using the new profile.
- Leaves the existing core and agent-profile machine names and semantics intact.
  In particular, recipient appraisal does not replace agent composition identity
  or its drift-revocation obligations.
- Does not overlap the active changes: it does not edit the core wallet-record
  key set, the register reader, core revocation propagation, or agent composition
  requirements. It only composes their settled outputs through new sibling
  profile records.
- Applications remain responsible for allow/refuse enforcement and session
  termination; KMS implementations remain responsible for key release and their
  own evidence; openxFactory or another external owner remains responsible for
  any evidence-chain anchoring.

## Repository-Owner Ratification Record

**PENDING.** This section is the durable approval surface. Before any Speckit
feature creation, the repository owner SHALL replace `PENDING` with all of:

- owner identity and explicit repository-owner authority;
- UTC approval date and time;
- exact approved packet revision and the artifact set `proposal.md`, `design.md`,
  and `specs/openxwallet-usage-control-profile/spec.md`;
- the verbatim approval ruling; and
- confirmation that the approval precedes all Speckit feature creation and
  implementation activity.

Approval of a summary, an issue, or a later implementation PR does not satisfy
this gate. Until this record is complete, this change remains `Status: draft`.
