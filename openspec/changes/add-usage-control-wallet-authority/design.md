## Context

The `openxwallet` core already owns wallet-level grants, monotonic attenuation,
proof of possession, key attribution, and revocation checked at exercise. It does
not carry purpose, fresh workload appraisal, session identity, replay state, or
external KMS evidence. The `openxwallet-agent-profile` separately defines an
agent's composition identity and composition-drift revocation; a workload
appraisal for one session is not a replacement for that identity contract.

The usage-control flow spans three owners. openXwallet can describe bounded
authority and evidence bindings. An application policy gate decides and enforces
access and terminates sessions. A KMS decides whether to release a key and emits
its own evidence. Any public or chain anchoring remains an external evidence
owner's responsibility.

## Goals / Non-Goals

**Goals:**

- Define a holder-neutral profile for a purpose-, scope-, and time-bounded grant
  evaluated against explicit current status.
- Bind an attested workload recipient, request, grant, purpose, resource
  commitment, nonce, and ephemeral session key into one appraisal proof.
- Make one exercise authorize at most one bounded session and make retries and
  replays distinguishable.
- Link, without absorbing, KMS-owned evidence.
- Preserve all existing core and agent-profile machine names and behavior.

**Non-Goals:**

- Define purpose, resource, role, consent, FHIR, Medx, clinical, financial, or
  other domain vocabularies.
- Treat attestation as proof of safe behavior, correct outputs, continuous
  execution, non-exfiltration, or side-channel resistance.
- Store or release encryption keys, decide application access, enforce egress or
  output policy, terminate application sessions, or prove deletion of outputs.
- Operate an evidence chain, blockchain adapter, transparency log, or public
  anchor.
- Change agent composition identity or composition-drift cascade semantics.

## Decisions

### D1 — Add one sibling profile; do not widen or rename the core kinds

The change adds capability `openxwallet-usage-control-profile` under
`contracts/openxwallet-usage-control-profile/`. It introduces three additive
record kinds:

- `xfactory_wallet_usage_control_grant` — the active-use binding over an existing
  `xfactory_wallet_grant`;
- `xfactory_wallet_attested_workload_recipient` — verifier appraisal and
  session-recipient binding; and
- `xfactory_wallet_usage_control_exercise` — the one-session binding over an
  existing `xfactory_wallet_grant_exercise`.

Each record references the core record it composes. Existing kind values, field
names, finding codes, filenames, and agent-composition semantics remain
unchanged. The new names are justified because no existing carrier can express
the new facts without mixing optional usage-control fields into every wallet
grant and exercise.

**Alternative rejected:** add optional blocks directly to the core grant and
exercise. That would move two established digested contracts and make every
consumer parse profile-specific state. A sibling profile keeps existing records
valid byte-for-byte and makes adoption explicit.

### D2 — The active profile composes the core grant instead of duplicating it

`xfactory_wallet_usage_control_grant` references one immutable core `grant_ref`
and carries the minimum facts absent from the core:

- its own immutable `usage_control_grant_id`;
- `purpose_ref`, whose meaning belongs to a consuming domain;
- an optional opaque `resource_set_commitment` digest that binds the requested
  resource set without itself granting an object or act;
- `not_before`; the effective end is the earlier of the profile `expires_at` and
  the core grant's `expires_at`;
- a closed profile `state` of `active`, `suspended`, `expired`, or `revoked`;
- `status_ref`, `revocation_ref`, and a non-zero `status_freshness_bound`; and
- optional neutral `required_execution_class_ref` and
  `required_appraisal_policy_ref` references.

The existing core scope remains authoritative for acts, objects, authority tier,
attenuation, audience, and expiry. The profile carries no parallel audience,
acts, objects, or authority tier, so its resource commitment cannot widen those
facts; the application remains responsible for proving that the committed
request is authorized by the core scope.
Changing purpose, resource commitment, validity, status references, or execution
requirements creates a successor profile record; it does not mutate an
already-exercised profile identity.

An active profile is a predicate, not a self-asserted label: both core and
profile states are active, current time is inside both validity windows, and a
status evaluation no older than the declared freshness bound reports neither
suspension nor revocation. The validator checks the predicate wherever a
session is recorded as permitted.

**Alternative rejected:** encode purpose in `scope.acts` or object identifiers.
That creates a parallel domain vocabulary inside neutral machine identifiers and
cannot distinguish what may be done from why it may be done.

### D3 — Recipient proof records an appraisal result and complete session binding

`xfactory_wallet_attested_workload_recipient` is vendor-neutral. It records:

- `recipient_proof_id`, audience `wallet_ref`, and `presenting_key_ref`;
- `usage_control_grant_ref`, `session_id`, `ephemeral_session_key_ref`, a fresh
  `nonce`, and `request_digest`;
- the same `purpose_ref` and `resource_set_commitment` used by the active profile;
- `evidence_ref` and `evidence_digest` for vendor-owned evidence;
- `verifier_ref`, `appraisal_policy_ref`, appraised measurement reference and
  digest, `appraised_at`, `valid_until`, and a closed appraisal result of
  `accepted`, `rejected`, or `indeterminate`; and
- a verifier-appraised `binding_digest` over the grant profile, audience wallet,
  presenting key, request, purpose, resource commitment, nonce, session
  identifier, and ephemeral session key reference.

The digest input is a JSON object with exactly these lexicographically named
members: `ephemeral_session_key_ref`, `nonce`, `presenting_key_ref`,
`purpose_ref`, `request_digest`, `resource_set_commitment`, `session_id`,
`usage_control_grant_ref`, and `wallet_ref`. An absent resource commitment is
encoded as JSON `null`. The object is canonicalized with RFC 8785 JSON
Canonicalization Scheme, encoded as UTF-8, and recorded as
`sha256:<lowercase hex>`. The verifier's signed appraisal result SHALL commit to
this digest; it is not a recipient's unverified assertion. The validator
recomputes the digest and checks the appraisal result's commitment and
cross-record equality. Attestation vendor quote formats remain external behind
evidence reference and digest.

Only `accepted` can support a permitted session. Acceptance means that the named
verifier appraised supplied evidence against the named policy and accepted the
recorded measurement. The closed record has no field for `safe_behavior`,
`non_exfiltrating`, or an equivalent claim. Rejected or indeterminate appraisal
remains recordable as evidence for a refused exercise.

**Alternative rejected:** put a cloud quote or TEE-specific claims directly in
the contract. That would make a vendor format part of the neutral wallet standard
and still would not establish safe application behavior.

### D4 — A nonce, proof, and exercise identify one session only

`xfactory_wallet_usage_control_exercise` references the core `exercise_ref`, the
active profile, and recipient proof. It repeats and cross-checks `session_id`,
`nonce`, `request_digest`, and `ephemeral_session_key_ref`; records the external
`policy_decision_ref`; and records the evaluated status and resulting bounded
session lease.

Within the validation corpus, a `(usage_control_grant_ref, nonce)` pair and a
`recipient_proof_id` may each occur in only one usage-control exercise. A
permitted exercise must bind exactly the values appraised in its recipient proof
and must point to a core exercise whose outcome is `permitted`. A refusal remains
recordable without inventing a successful session.

A retry uses a new exercise id, proof id, nonce, and session id and may carry
`retry_of` naming the prior exercise. Reusing any prior nonce or proof is a replay
finding, not a retry.

**Alternative rejected:** rely on timestamp freshness alone. Two requests inside
one freshness window would then be indistinguishable, and a captured accepted
proof could be replayed until it expired.

### D5 — Status freshness bounds the session lease; revocation does not rewrite history

The usage-control exercise records a `status_evaluation` containing the status
and revocation references evaluated, the observed state, `checked_at`, and the
resulting `valid_until`. For a permitted exercise, `valid_until` is no later than
the earliest of:

- the core grant expiry;
- the usage-control profile expiry;
- recipient-proof expiry; and
- `checked_at + status_freshness_bound`.

Suspended, expired, revoked, stale, missing, or unresolved status cannot produce
a permitted exercise. Continuing past `valid_until` requires a new exercise with
a new nonce and fresh proof/status evidence. Revocation blocks future exercises
and renewals. It does not claim to erase plaintext, recall outputs, or instantly
clear an already-running workload; application-owned termination and output
handling must be evidenced separately.

**Alternative rejected:** claim continuous status checking. The wallet artifact
can prove only the checks it records. A bounded lease makes that limit explicit
without pretending the wallet runs the enforcement loop.

### D6 — KMS evidence is a typed external link, never a wallet action

Every usage-control exercise carries `kms_evidence` in exactly one of two forms:

- `linked`: `kms_event_ref`, `kms_event_digest`, `kms_issuer_ref`, and
  `recorded_at`; or
- `not_invoked`: a non-empty reason.

The linked form proves only which immutable KMS-owned event the exercise cites.
It carries no key material, key handle that grants possession, or wallet-authored
claim that release succeeded. The KMS owns event semantics and authenticity; the
application owns whether its decision was enforced. The explicit `not_invoked`
form prevents absence from being interpreted as successful release or as a lost
event.

**Alternative rejected:** embed a `key_released: true` assertion. It would let
the wallet claim an action it neither performs nor independently verifies.

### D7 — Holder neutrality is structural

The profile constrains no issuer or audience holder class. Purpose, resource,
execution-class, appraisal-policy, policy-decision, status, revocation, and KMS
values are references or digests, not neutral-core enumerations. A domain may
profile those references while continuing to pin this contract family.

An agent wallet that uses this profile remains subject to
`openxwallet-agent-profile`; an accepted session appraisal neither establishes
agent composition identity nor suppresses composition-drift revocation.

### D8 — Validation and release are additive

The canonical validator loads all three new kinds, resolves every profile
reference, recomputes binding digests, checks active/status/lease predicates, and
enforces nonce and proof uniqueness. The packaged corpus includes positives and
one negative confirmation for each normative branch, with new finding codes
only; no existing code is renamed or repurposed and no warning is introduced.

The three new schemas become owned manifest members. Existing owned artifact
bytes and digests remain unchanged. The bundle version, per-file schema versions,
digests, changelog entry, release commit, and annotated tag are allocated and
coordinated only during realization.

### D9 — Repository-owner ratification precedes feature creation

Ratification is an unconditional fail-closed gate, not an optional repository
policy lookup. Before `/speckit.specify`, feature branch or worktree creation, or
any implementation activity, the repository owner must approve the exact
proposal, design, and delta spec. The durable record lives in `proposal.md` and
must name the owner and authority, UTC time, exact packet revision, approved
artifact set, and verbatim ruling. Both proposal front-matter status fields must
then record ratification.

An oral approval not written into the change, approval of a summary rather than
the packet, or approval recorded only on the later implementation feature does
not open the gate. Any packet change after approval requires the repository owner
to ratify the revised packet before feature creation or implementation resumes.

### D10 — Constitution adoption and checking are separate plan prerequisites

No adopted `.specify/memory/constitution.md` exists in this repository as this
packet is revised. The constitution must be adopted through separate
repository-governance work before this feature's Constitution Check can occur;
this product change must not invent, adopt, or amend its principles.

Before the one Speckit feature enters its plan phase, a separate durable
governance record must identify the adopted constitution revision and perform a
meaningful check of the feature specification against each applicable principle,
including pass/fail results and any owner-approved exception. A template heading,
an absent constitution treated as a pass, or a statement that the check is not
applicable does not satisfy the gate. Constitution adoption and this check are
prerequisites to planning, not deliverables folded into the usage-control feature.

### D11 — Active-change overlap and domain-neutrality recheck

The active changes were re-read after this revision:

- `add-multi-key-wallets` owns the existing wallet record's declared key set and
  per-key custody. This change only references a wallet and presenting key and
  does not modify that schema or its requirements.
- `add-per-seat-register-entries` owns the review-authority register reader. This
  change adds no register field, reader behavior, council, seat, or review
  authority meaning.
- `add-composition-drift-cascade` modifies core revocation propagation and agent
  composition drift. This change consumes current standing, does not redefine
  propagation, and explicitly prevents workload appraisal from replacing agent
  composition identity.

No active change introduces this sibling profile, and this profile takes no
unfinished task from any of them. Its purpose, resource, execution, appraisal,
policy, status, revocation, and KMS values remain opaque references or digests;
no medical, FHIR, Medx, clinical, patient, practitioner, or other domain meaning
enters a machine field or neutral enumeration.

## Risks / Trade-offs

- **[A bounded lease is not continuous enforcement]** → The exercise records the
  exact lease end, and continuing requires a new proof, nonce, status evaluation,
  and exercise.
- **[A valid appraisal may be over-read as safety certification]** → The contract
  names measurement appraisal precisely, closes unknown claims, and includes
  negative confirmation for behavior-assurance language.
- **[External references may resolve differently later]** → Evidence and KMS
  links pair immutable references with digests; audit does not depend on mutable
  endpoint contents alone.
- **[Cross-record state can be partially published]** → Permitted exercises fail
  closed unless the core grant/exercise and all three profile bindings resolve
  and agree.
- **[Nonce uniqueness is only as broad as the validating store]** → The profile
  defines the issuer/grant replay key and requires the enforcing application to
  maintain the authoritative replay store; offline validation detects duplicates
  present in the corpus but does not claim global observation.

## Migration Plan

1. Add the sibling profile schemas, README, examples, validator rules, and tests
   without editing existing contract artifacts.
2. Register the three new owned members, allocate the additive release version,
   and run the complete offline gate bar.
3. Publish the coordinated release and let consumers opt in by pinning it. No
   existing wallet, grant, exercise, or agent-composition record requires
   migration.
4. Rollback by removing profile records from adopting consumers and returning to
   the prior pin. Existing core records remain valid because no core shape moved.

## Open Questions

None. Domain vocabularies, vendor quote adapters, application enforcement, KMS
event schemas, and evidence-chain anchoring are intentionally delegated rather
than unresolved parts of this profile.
