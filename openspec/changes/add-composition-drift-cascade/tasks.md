# Tasks: add-composition-drift-cascade

Governance-level only. The executable implementation list belongs to the single
Speckit feature this change hands off to; do not duplicate it here.

## 1. Spec deltas

- [x] 1.1 `openxwallet` (core) — MODIFIED `Revocation propagates through the
      chain`, restated in full with its two existing scenarios intact and four
      added. Gains: a recorded REASON CLASS that is never consulted to narrow
      propagation, so DRIFT cascades exactly as CAUSE does (Q8 limb b, stated
      in the CORE because the agent profile delegates here); a propagated
      revocation recording the edge it descends from; a revoked grant never
      returning to active, with resumption as a NEW grant recording what it
      supersedes and what it was issued against (limb a's core half); and a
      holder left with no active standing reaching a human through the
      CONSUMING capability's declared escalation path (limb c, stated
      neutrally — openXwallet names no mechanism of openxFactory's).
- [x] 1.2 `openxwallet-agent-profile` — MODIFIED `A composition change revokes
      the agent's grants immediately`, restated in full with its two existing
      scenarios intact and four added. Gains: composition change produces a
      DRIFT-class revocation that cascades under the core rule; the declaration
      is NOT the revocation, so the outstanding grant records must carry the
      revoked state naming the composition event and a declaration beside an
      active grant is a validation failure; resumption requires an explicit,
      human-ratified issuance act (limb a); and a declared model component
      names an EXACT version, a family or alias being a validation failure
      (limb d, ratifying today's behavior as intended).
- [x] 1.3 Both restatements reproduce the promoted `### Requirement:` heading
      byte-for-byte and restate the full body plus ALL scenarios as they read
      after the change. This is the repository's FIRST `## MODIFIED
      Requirements` block — the one archived change used only `## ADDED` — so
      the standard OpenSpec convention is followed deliberately rather than
      inherited from local precedent.
- [x] 1.4 `OPENSPEC_TELEMETRY=0 openspec validate add-composition-drift-cascade
      --strict` and `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`
      green before commit, and again at archive.
- [x] 1.5 Full existing gate bar green with no contract byte touched:
      `verify-contract-pin.py`, `wallet-yaml-syntax-gate.py`,
      `validate-openxwallet.py` (plain and `--strict`), `pytest tests/ -q`.

## 2. Ratification gate

- [ ] 2.1 **[OPERATOR]** Brett Heap ratifies this proposal, design and both
      spec deltas. `Status: draft` until then, and **no realization work in
      §3 may begin before this box is checked**. The underlying Q8 ruling
      (2026-08-26) is already made; what awaits ratification is this ENCODING
      of it, plus the reissuance policy proposed in `design.md`.
- [ ] 2.2 **[OPERATOR]** Rule the CARRIED question before 2.1, not after:
      should this core delta define the family-pin policing mechanism (a family
      pin plus an attested resolved-version record, re-attested on every roll),
      or does exact-versions-only stand un-revisited? Both exits and their costs
      are in `design.md` § Open questions. **The deltas as authored are
      consistent with Exit 2**; adopting Exit 1 requires amending the
      agent-profile delta's fifth paragraph BEFORE ratification, which is why
      this precedes 2.1.
- [ ] 2.3 **[OPERATOR]** Rule the proposed reissuance policy shape (what the
      act records; act rather than state transition; no standing form) or
      amend it. `design.md` proposes it as S5's implementer; the convener rules
      it.

## 3. Declared realization surface — NAMED, NOT PERFORMED HERE

Per `release-realization`, this change carries a code surface and archives only
on merged, green realization evidence for it. Nothing below is done in this
change, and nothing below may start before 2.1.

- [ ] 3.1 **Validator cascade rule.** Walk composition drift into the wallet's
      ACTUAL grant records. Today rule (p) `declared-change-not-revoked`
      (`scripts/validate-openxwallet.py:1233-1244`) only checks the composition
      record against ITSELF; nothing asserts the holder's
      `xfactory_wallet_grant` records carry `state: revoked`, nor that derived
      grants went with them. The walk already exists for the other two
      revocation paths — `_revoked_ancestor`
      (`scripts/validate-openxwallet.py:896-911`) follows `parent_grant_ref`
      and checks holder standing — and composition drift must enter it.
- [ ] 3.2 **Carrier assessment before any schema edit.** The grant schema
      already carries `parent_grant_ref`, `state: [active, expired, revoked]`
      and `revocation: {revoked_at, reason, propagated_from}`. Determine what
      the cascade rule genuinely needs beyond these — at minimum whether
      `revocation.reason` can carry the DRIFT/CAUSE class as-is or needs a
      distinct classed field — and treat any new carrier as a versioned
      contract change with the five coordinated release values, not a tidy-up.
- [ ] 3.3 **Negative-confirmation fixtures**, per the corpus convention of one
      per requirement: a declaration standing beside an active grant; a derived
      grant surviving a DRIFT-class parent revocation; a propagated revocation
      with no recorded origin; a revoked grant returned to active; a model
      family or alias in a declared component.
- [ ] 3.4 **Register reader validates `revocation_staleness_bound`.** Successor
      raised by the S5 session that landed openxFactory task 7.3: a new
      top-level `revocation_staleness_bound: P7D` now sits beside
      `register_version` in `governance/review-authority/register.yaml`, and
      the PINNED reader does not validate it — `check_register` is strict on
      `REGISTER_ROW_FIELDS` but reads only `register_version` and `rows` at the
      top level, so an unknown top-level key passes silently (measured: 0
      errors, 0 warnings against the edited tree). A governed declaration no
      required check reads is the vacuous-pass class, parent-change design risk
      **R3**. The reader SHALL validate the bound — present, a well-formed
      ISO-8601 duration, refused if malformed or absent. Reader work lives in
      openXwallet now, which is why it is on this ledger. Related to this
      change by repository and by S5, NOT by these deltas: it is a named
      successor and no delta here obliges it.
- [ ] 3.5 Version allocated at realization — per-file `contract_schema_version`,
      `contract_bundle_version`, the annotated `wallet-v<major>.<minor>` tag,
      the release commit with per-file digests, and the `contracts/CHANGELOG.md`
      entry. Nothing is reserved by this proposal.

## 4. Handoff

- [ ] 4.1 On ratification, open exactly ONE Speckit feature for the declared
      surface in §3. Ratification authorizes that handoff and nothing else: it
      creates no key, credential, wallet, runtime or issuance service, and it
      obliges no domain to adopt wallets.
- [ ] 4.2 Record the realization evidence on this change before archiving —
      merged, green — and re-run the full gate bar at archive.

## 5. Upstream bookkeeping

- [ ] 5.1 Record against openxFactory `add-wallet-carried-review-authority`
      that Q8's declared core deltas were authored here, per its §8.1 Addendum
      ("S3 and S5's `openxwallet` / `openxwallet-agent-profile` core deltas are
      authored in openXwallet from here on"). The upstream `tasks.md` 8.1
      ruling itself needs no edit — only the deltas' HOME moved.
- [ ] 5.2 Note that this change does NOT close parent-change risk **R1** (the
      `--admin` composition loop) and makes it load-bearing: its exit stays
      that change's task **7.6** runbook, an operator act, deliberately not an
      automatic reissue.
- [x] 5.3 No README or AGENTS edit: neither file carries an active-change list
      in this repository (`README.md` indexes `openspec/specs/` as "the eleven
      promoted requirements", and `AGENTS.md` names the active Speckit feature,
      not active OpenSpec changes). Checked rather than assumed.

## 6. Corpus drift observed, NOT taken on

- [x] 6.1 Recorded in `design.md` and left alone: (i) validator requirement
      rows `OXWR-R1` / `OXWR-R2` (the S2 issuer anchor) exist in the
      `REQUIREMENTS` dict with no `### Requirement:` heading in the promoted
      spec; (ii) `docs/contract-versioning-policy.md` is referenced by both
      contract READMEs and does not exist. Both pre-date this change; fixing
      either is other work.
