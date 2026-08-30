## 1. Governance Closure

- [ ] 1.1 Confirm the proposal, design D1–D11, and
  `openxwallet-usage-control-profile` delta remain the complete governed scope:
  one additive sibling profile, no existing machine-name changes, and no domain,
  application-enforcement, key-release, or chain-anchoring ownership transfer.
- [ ] 1.2 **[REPOSITORY OWNER — UNCONDITIONAL GATE]** Before any Speckit feature,
  branch, or worktree is created and before any implementation begins, the
  repository owner SHALL ratify the exact proposal, design, and delta spec. Make
  the approval durable in `proposal.md` by recording owner identity and authority,
  UTC time, exact approved packet revision, approved artifact set, and verbatim
  ruling; then set both front-matter status fields to ratified/recorded. A revised
  packet requires renewed owner ratification. Ratification SHALL NOT allocate a
  release version.
- [ ] 1.3 **[SEPARATE REPOSITORY GOVERNANCE — PLAN PREREQUISITE]** Before the
  Speckit plan phase, verify that separate governance work has adopted a
  repository constitution because `.specify/memory/constitution.md` is currently
  absent, and has separately recorded a meaningful Constitution Check of this
  feature against the adopted revision. The record SHALL give per-principle
  pass/fail results and any owner-approved exception; an absent constitution,
  placeholder heading, or `not applicable` assertion is not a pass. This task
  records only references to that separate governance evidence; constitution
  adoption and checking are not performed or delivered by this product feature.

## 2. Single Speckit Feature Handoff

- [ ] 2.1 Create exactly one Speckit feature with slug
  `usage-control-wallet-authority`, record its canonical
  `specs/NNN-usage-control-wallet-authority/` path here, and hand it this proposal,
  design, and delta spec as its sole OpenSpec authority. Speckit SHALL own the
  executable implementation task list; no second feature or duplicate OpenSpec
  implementation checklist is authorized. This task SHALL NOT begin until the
  durable repository-owner ratification record in 1.2 is complete.
- [ ] 2.2 In that feature, complete specify and clarify, then stop before plan
  until the separate constitution adoption and meaningful Constitution Check in
  1.3 are durably recorded.
- [ ] 2.3 After 1.3 is complete, run plan/tasks/analyze before implementation and
  prove that the feature artifacts preserve the three new kinds,
  holder neutrality, appraisal-not-safety boundary, replay binding, status lease,
  KMS ownership, and all non-goals from this change.

## 3. Realization Acceptance

- [ ] 3.1 Record Speckit evidence that the sibling profile family, its three
  schemas, packaged positive and negative corpus, validator rules, tests, README,
  manifest rows, and release bookkeeping realize every requirement and scenario
  in the delta spec without changing an existing owned contract byte.
- [ ] 3.2 Record evidence that binding-digest recomputation, verifier commitment,
  one-session nonce/proof uniqueness, active/status/lease evaluation, explicit
  revocation, and linked-or-not-invoked KMS evidence fail closed under the
  specified negative cases.
- [ ] 3.3 Record evidence that existing wallet, grant, exercise, and agent-profile
  records validate unchanged and that no existing kind, field, filename, or
  finding code was renamed, repurposed, or reclassified.
- [ ] 3.4 Allocate the additive release only at realization and coordinate the
  three new per-file schema versions and digests, bundle version, changelog,
  release commit, and annotated tag under the repository release rules.

## 4. Verification and Archive Gate

- [ ] 4.1 Run the repository's complete offline gate bar at the realized feature
  head: contract-pin verification, YAML syntax gate, validator plain and strict,
  pytest, and strict OpenSpec validation; record commands, exit codes, and finding
  counts on this change.
- [ ] 4.2 Verify an adopting consumer can remove the profile records and return
  to the prior pin without migrating any core record, then record the rollback
  evidence.
- [ ] 4.3 Archive this OpenSpec change only after the one Speckit feature is
  merged, its release evidence is recorded, and 4.1's strict validation evidence
  is complete. The archive record SHALL name the merged feature revision and the
  validation runs; feature creation, feature completion, or a green unmerged
  branch alone SHALL NOT satisfy this gate.
