# openxwallet-usage-control-profile Specification

The holder-neutral sibling profile that composes the `openxwallet` core's grant
and exercise records into one bounded usage-control session. It owns authority
and evidence bindings only; consuming domains own meanings, applications own
access enforcement, KMS implementations own key release, and external evidence
systems own anchoring.

## ADDED Requirements

### Requirement: An active usage-control grant is purpose-, scope-, time-, and status-bound

openXwallet SHALL represent usage-control authority as an additive profile over
an existing wallet grant. The profile SHALL name an external purpose reference,
MAY bind a requested resource set with an opaque commitment that confers no
authority by itself, SHALL declare a not-before time and expiry no later than the
core grant's expiry, and SHALL carry explicit status and revocation references
with a non-zero freshness bound. A usage-control grant is active only while both
records are active, the current
time is inside both validity windows, and a current status evaluation reports no
suspension or revocation. Changing any profile binding SHALL create a successor
profile record rather than rewrite an exercised one.

Purpose and resource meanings SHALL remain external references or commitments;
the profile SHALL NOT define a domain vocabulary.

#### Scenario: A current bounded grant is active

- **WHEN** the core grant and its usage-control profile are active, current time
  is inside both validity windows, and a status evaluation within the declared
  freshness bound reports active
- **THEN** the profile is eligible for a usage-control exercise within the core
  grant's audience and scope
- **AND** the purpose reference and any resource-set commitment are bound without
  the profile interpreting their domain meaning

#### Scenario: A stale or revoked grant is not active

- **WHEN** status is stale, missing, unresolved, suspended, expired, or revoked,
  or either validity window is not current
- **THEN** a permitted usage-control exercise SHALL be refused
- **AND** issuance-time validity SHALL NOT substitute for current status

#### Scenario: The profile cannot widen core authority

- **WHEN** a usage-control profile expires later than its core grant or presents
  a resource-set commitment as authority independent of the core scope
- **THEN** the profile SHALL be invalid
- **AND** the profile SHALL carry no parallel audience, act, object, or authority
  tier that could become a second grant mechanism

### Requirement: An attested workload recipient proof is fresh and session-bound

openXwallet SHALL require an attested workload recipient proof for a protected
usage-control session. The proof SHALL bind the audience wallet and presenting
key to the usage-control grant, purpose reference, resource-set commitment,
request digest, fresh nonce, session identifier, and ephemeral session key
reference. It SHALL identify the evidence and its digest, verifier, appraisal
policy, appraised measurement and its digest, appraisal time, proof expiry, and
appraisal result. A deterministic binding digest SHALL cover all session-binding
values, the verifier's signed appraisal result SHALL commit to that digest, and
the digest SHALL be recomputed during validation. The digest SHALL be SHA-256
over the UTF-8 RFC 8785 canonical JSON object defined by the profile contract;
an absent resource-set commitment SHALL be represented by JSON `null`.

The proof SHALL carry no private key material and SHALL remain independent of any
attestation vendor's quote format.

#### Scenario: Accepted evidence binds one measured recipient

- **WHEN** a verifier accepts fresh evidence under the named appraisal policy,
  its signed result commits to the binding digest, and the digest recomputes over
  the recipient, grant, request, purpose, resource, nonce, session, and ephemeral
  session key
- **THEN** the proof identifies the measured recipient appraised for that one
  session
- **AND** changing any bound value SHALL invalidate the proof

#### Scenario: Evidence from another session is refused

- **WHEN** a proof's nonce, session identifier, request digest, grant reference,
  purpose reference, resource commitment, or ephemeral session key differs from
  the exercise that presents it
- **THEN** the exercise SHALL be refused as a binding failure
- **AND** a still-current appraisal timestamp SHALL NOT cure the mismatch

#### Scenario: Vendor evidence stays external

- **WHEN** a workload uses a vendor-specific quote or evidence format
- **THEN** the recipient proof SHALL carry an immutable evidence reference and
  digest rather than embedding that vendor format in the neutral profile
- **AND** the profile SHALL remain validatable without network access

### Requirement: Attestation proves appraised measurement, not safe behavior

openXwallet SHALL interpret an accepted appraisal only as evidence that the named
verifier evaluated supplied evidence under the named policy and accepted the
recorded measurement. It SHALL NOT represent that result as proof that the
workload is bug-free, behaves safely, prevents exfiltration, controls outputs,
runs continuously after appraisal, or resists every side channel. Rejected and
indeterminate appraisal results SHALL remain recordable for refused exercises
and SHALL NOT support a permitted exercise.

#### Scenario: Accepted appraisal is not behavior assurance

- **WHEN** a recipient proof records an accepted appraisal
- **THEN** the proof establishes only the appraised measurement and its stated
  bindings
- **AND** a field or statement claiming safe behavior or non-exfiltration as an
  attestation result SHALL be refused

#### Scenario: Non-accepted appraisal cannot authorize a session

- **WHEN** the appraisal result is rejected or indeterminate
- **THEN** a refused exercise MAY retain the result as evidence
- **AND** a permitted exercise using that proof SHALL be invalid

### Requirement: Every usage-control exercise authorizes at most one bounded session

openXwallet SHALL bind each usage-control exercise to one core grant exercise,
one active usage-control grant profile, one recipient proof, one request digest,
one nonce, one session identifier, one ephemeral session key, and one external
policy-decision reference. A permitted profile exercise SHALL agree with every
bound value in its recipient proof and SHALL reference a core exercise whose
outcome is permitted. The same recipient proof or the same nonce under one
usage-control grant SHALL NOT authorize a second exercise.

A retry SHALL use a new exercise identifier, proof identifier, nonce, and session
identifier and MAY name the prior exercise through `retry_of`; replay SHALL NOT be
treated as retry.

#### Scenario: One accepted proof authorizes one session

- **WHEN** all grant, recipient-proof, request, nonce, session-key, status, and
  policy-decision bindings agree and the core exercise is permitted
- **THEN** the usage-control exercise SHALL identify one bounded session
- **AND** the proof and nonce SHALL be consumed for that grant

#### Scenario: A replay is refused

- **WHEN** another exercise reuses a consumed recipient proof or reuses the same
  nonce under the same usage-control grant
- **THEN** the later exercise SHALL be refused as replay
- **AND** a different exercise or session identifier SHALL NOT make the reuse a
  retry

#### Scenario: A retry is a new exercise

- **WHEN** an application retries a refused or interrupted request
- **THEN** it SHALL create a new proof, nonce, session identifier, and exercise
- **AND** it MAY link the new exercise to the prior one without reusing the prior
  authority binding

### Requirement: Status evaluation establishes a bounded lease and revocation remains honest

openXwallet SHALL record on every usage-control exercise which status and
revocation references were evaluated, the observed state, the check time, and the
resulting session `valid_until`. For a permitted exercise, `valid_until` SHALL be
no later than the earliest core-grant expiry, profile expiry, recipient-proof
expiry, and status-freshness deadline. Continuing after that instant SHALL require
a new exercise with fresh status, proof, and nonce.

Revocation SHALL block future exercises and renewals. The profile SHALL NOT claim
that revocation erased plaintext or derived outputs, instantly terminated an
already-running application session, or proved deletion.

#### Scenario: Fresh status bounds the session

- **WHEN** an active grant, accepted recipient proof, and current status support
  a permitted exercise
- **THEN** the recorded session lease SHALL end at or before every applicable
  grant, proof, and status deadline
- **AND** use beyond that lease SHALL require a new exercise

#### Scenario: Revocation prevents later authority

- **WHEN** the grant or profile is revoked before a new exercise or renewal
- **THEN** that exercise or renewal SHALL be refused
- **AND** prior completed exercise records SHALL remain readable rather than
  being rewritten

#### Scenario: Revocation does not claim impossible recall

- **WHEN** revocation occurs after a session started or output was produced
- **THEN** the wallet record SHALL make no claim that memory, plaintext, or output
  was erased
- **AND** any termination or deletion evidence SHALL remain application-owned

### Requirement: KMS evidence is linked explicitly and remains KMS-owned

openXwallet SHALL make the KMS relationship explicit on every usage-control
exercise. When a KMS was invoked, the exercise SHALL link an immutable KMS-owned
event by reference and digest and SHALL identify its issuer and record time. When
no KMS was invoked, the exercise SHALL state `not_invoked` with a reason. The
profile SHALL carry no released key material and SHALL NOT assert that openXwallet
released a key, enforced an application decision, or verified KMS event semantics
that belong to the KMS.

#### Scenario: A KMS event is linked without being absorbed

- **WHEN** a KMS emits evidence for a decision or event associated with the
  session
- **THEN** the exercise SHALL carry the event reference, digest, issuer, and time
- **AND** the KMS remains the owner of the event and its meaning

#### Scenario: No KMS invocation is explicit

- **WHEN** an exercise reaches a result without invoking a KMS
- **THEN** it SHALL record `not_invoked` and a non-empty reason
- **AND** absence of a KMS event SHALL NOT be interpreted as successful release

#### Scenario: A wallet record never carries a released key

- **WHEN** KMS evidence is linked to an exercise
- **THEN** the profile SHALL contain no private key, plaintext data key, or bearer
  value that grants possession
- **AND** key release SHALL remain a KMS operation outside openXwallet

### Requirement: The profile is holder-neutral and does not become an enforcement or anchoring layer

openXwallet SHALL constrain no issuer or audience holder class in the
usage-control profile. Purpose, resource, execution-class, appraisal-policy,
policy-decision, status, revocation, and KMS values SHALL remain neutral
references or commitments. The profile SHALL NOT define domain meanings, enforce
application access, release keys, or anchor evidence to a chain or public log.

An agent wallet using this profile SHALL remain independently subject to the
agent-composition profile; a workload appraisal SHALL NOT replace composition
identity or suppress composition-drift revocation.

#### Scenario: A domain supplies meanings without changing the neutral profile

- **WHEN** a consuming domain assigns meaning to purpose, resource, policy, or
  KMS references
- **THEN** those meanings SHALL be supplied by the domain's own profile or policy
- **AND** the openXwallet usage-control contract SHALL remain unchanged

#### Scenario: Enforcement stays with the application and KMS

- **WHEN** a complete usage-control exercise is available
- **THEN** the application and KMS MAY consume its bindings in their own decisions
- **AND** the exercise SHALL NOT claim that openXwallet made or enforced those
  decisions

#### Scenario: Evidence anchoring stays external

- **WHEN** an owner chooses to anchor an exercise or KMS-event commitment
- **THEN** the anchoring system SHALL consume a reference or digest from this
  profile
- **AND** openXwallet SHALL NOT operate or define the chain anchor

#### Scenario: Workload appraisal does not replace agent composition

- **WHEN** an agent wallet presents an accepted workload appraisal
- **THEN** its agent composition obligations and drift revocation SHALL still
  apply independently
- **AND** the appraisal SHALL authorize nothing after composition standing is
  revoked
