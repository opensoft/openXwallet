# Feature Specification: Factory/workload binding

**Feature Branch**: `016-factory-workload-binding`
**Created**: 2026-11-11
**Status**: Source acceptance ratified by Brett Heap on 2026-11-11; live activation remains unqualified
**Input**: Brett: "Go ahead with the narrow factory/workload binding feature, including the OpenSpec proposal, Speckit plan, implementation and isolated tests. Keep feedback deferred and don't replay either blocked write."

Governing proposal: `opensoft/openxFactory`,
`openspec/changes/add-workload-factory-binding/proposal.md`.
This feature is its sole executable implementation task list. The commission
supports candidate source and isolated evidence, not ratification of an unseen profile.

## User Scenarios & Testing

### User Story 1 - Bind a workload to bounded factory authority (Priority: P1)

An operator binds one approved workload, wallet/key and agent identity to an
existing grant chain. The worker may request only a permitted act and object.

**Why this priority**: Possession alone supplies no factory authority.
**Independent Test**: A valid request succeeds; changing the identity, wallet,
key, act, object, parent scope or current revocation state refuses before signing.

**Acceptance Scenarios**:
1. **Given** current operator records and an authenticated approved workload,
   **When** it requests a permitted act/object, **Then** the gate identifies the
   agent, wallet and complete bounded grant chain.
2. **Given** an expired/revoked parent or widened child, **When** the same
   request is evaluated, **Then** it refuses before custody access.
3. **Given** an agent binding, **When** approval authority is requested,
   **Then** it refuses: authentication supplies no human consent.

### User Story 2 - Require independent evidence before signing (Priority: P1)

The signing gate requires the issuer's workload signature and a separate trusted
supervisor's signed observation of the approved reference composition.

**Why this priority**: A worker must not attest its own composition or obtain
custody signing credentials.
**Independent Test**: Real signatures over synthetic workload evidence plus an
independent observation permit one bound proof; modified evidence refuses.

**Acceptance Scenarios**:
1. **Given** matching evidence for a fresh trusted challenge, **When** the gate
   signs, **Then** the existing wallet primitive produces a proof for exactly it.
2. **Given** evidence for another request/run or an untrusted supervisor,
   **When** presented, **Then** it refuses before custody access.
3. **Given** a used token/challenge, **When** retried concurrently or after a
   restart, **Then** no second signing call occurs.

### User Story 3 - Qualify in isolation (Priority: P2)

A maintainer reproduces positive/refusal cases with disposable keys and reference
processes, without a provider account or installed broker.

**Independent Test**: Success and injected failure tests leave no owned child
process or temporary key/state directory.

### Edge Cases

Missing/duplicate claims, unsupported algorithms, stale or ambiguous issuer keys,
invalid times, grant cycles/missing parents, outage, rotation, replay and stale
observations refuse. Reusable workflows bind their exact ref and SHA as well as
the caller repository, environment, source SHA and run/attempt.

## Requirements

### Functional Requirements

- **FR-001**: Reload operator-owned binding/grants at each exercise; never accept
  worker authority records.
- **FR-002**: Verify issuer, audience, signature, bounded lifetime and exact
  repository/owner IDs, environment, subject, workflow refs/SHAs, source and run.
- **FR-003**: Require the current registry's subject, wallet, key, custody and
  revision to match the operator's selected binding.
- **FR-004**: Check every grant's active state, audience, ancestor state, acts,
  objects, lifetime and non-widening delegation. Support only existing `act`
  authority and retain required approval posture.
- **FR-005**: Require a separate signed observation binding token digest, run,
  challenge, request, policy revision and composition. The observer reads trusted
  reference artifacts itself; worker claims are insufficient.
- **FR-006**: Only the trusted gate invokes its custody client. Reuse the owning
  wallet proof primitive and return no private keys.
- **FR-007**: Reserve issuer/token and challenge identities durably and atomically
  before signing; ambiguous signer failures consume the reservation.
- **FR-008**: Keep candidate source, isolated conformance, live issuer
  qualification, human approval and pilot acceptance distinct.
- **FR-009**: Use synthetic identities/ephemeral custody in tests. Keep feedback
  deferred and never invoke either historically denied write.

### Key Entities

Operator binding; current wallet binding; existing grant/parent chain; workload
claims; supervisor observation; trusted challenge/request; signing reservation.

## Assumptions and Dependencies

The trusted embedding gate owns its clock, current policy/grant loaders, approved
issuer key snapshot, supervisor trust, registry, challenge creation and custody
credentials. Workers cannot administer those interfaces. Issuer-key refresh,
workflow enrollment and deployed isolation are later qualification obligations.
The neutral proof API is explicitly injected; this feature advances no neutral
pin. Reference observation measures fixture artifacts/configuration, not model
behavior, hardware assurance or a human decision.

## Success Criteria

- **SC-001**: Identity, scope, lifetime and delegation refusals make zero sign calls.
- **SC-002**: A permitted request produces one independently verified proof;
  duplicate/concurrent/restarted attempts produce no second one.
- **SC-003**: Worker custody signing refuses and returns no private key.
- **SC-004**: Offline gates pass without changing pins, published contracts,
  validation floors or releases.
- **SC-005**: Success/failure isolation leaves no owned process or temporary
  key directory. No live qualification or pilot T002 completion is claimed.
