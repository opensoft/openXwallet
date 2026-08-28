---
code_surface: openXwallet neutral spec text only in THIS change (two MODIFIED requirements). A code surface is DECLARED and not performed here — a validator cascade rule walking composition drift into the wallet's actual grant records, plus whatever carrier work that rule needs. Per `release-realization`, this change archives only on merged, green realization evidence for that declared surface.
target_release: unallocated. Version numbers — per-file `contract_schema_version`, `contract_bundle_version`, and the `wallet-v<major>.<minor>` tag — are allocated at realization and never reserved in a proposal (AGENTS.md, "a release is five coordinated values").
Status: draft
---

# Proposal: add-composition-drift-cascade

## Why

Composition drift is, today, a self-declaration that nothing checks against
reality.

`contracts/openxwallet-agent-profile/openxwallet-agent-composition.schema.yaml`
lets a composition record carry `grants_state: revoked_on_composition_change`,
and the validator's rule (p) (`declared-change-not-revoked`) checks exactly one
thing: that the composition record does not contradict ITSELF. If the attested
hash differs from the declared hash, the record must say its grants are
revoked. That is the whole check.

Nothing walks from that declaration to the wallet's actual
`xfactory_wallet_grant` records. Nothing asserts those grants carry
`state: revoked`. Nothing asserts a derived grant went with them. The
validator already knows how to do this for the OTHER two revocation paths —
`_revoked_ancestor` walks `parent_grant_ref` upward and checks holder standing
— but composition drift never enters that walk. So a record can declare its
identity ended while every grant it issued stays `active`, and every gate in
the family passes.

That gap is precisely what openxFactory's ratified
`add-wallet-carried-review-authority` ruled on. On 2026-08-26 the operator
ruled **Q8 as a fail-closed bundle**, and placed the mechanical enforcement of
its second limb here: "Mechanical cascade enforcement rides the `openxwallet` /
`openxwallet-agent-profile` core deltas (S5-era work)." The §8.1 Addendum then
moved the deltas' home to this repository, because both capabilities left the
openxFactory corpus at the `split-openxwallet-repo` carve.

This change is that authoring. **It encodes a ruling; it does not make one.**

## What Changes

Two `## MODIFIED Requirements`, no new capability, no new requirement, no
contract byte.

- **MODIFIED `openxwallet` → `Revocation propagates through the chain`.** Gains
  four obligations: revocation records a REASON CLASS which is recorded but
  never consulted to narrow propagation, so a DRIFT revocation cascades exactly
  as a CAUSE one does (limb b, stated in the CORE because the agent profile
  delegates to it); a propagated revocation records the edge it descends from,
  so the chain is inspectable rather than inferred; a revoked grant never
  returns to active — resumption is a NEW grant recording what it supersedes
  and what it was issued against (limb a's core half, the reissuance RECORD);
  and a propagation that leaves a holder with no active standing is surfaced to
  the responsible human through the consuming capability's declared escalation
  path, not discharged by a log line (limb c, stated NEUTRALLY — see below).
- **MODIFIED `openxwallet-agent-profile` → `A composition change revokes the
  agent's grants immediately`.** Gains four obligations: the revocation a
  composition change causes is DRIFT-class and cascades under the core rule
  exactly as CAUSE does; `grants_state: revoked_on_composition_change` is a
  DECLARATION and not the revocation — the outstanding grant records must carry
  the revoked state with a revocation naming the composition event, and a
  declaration standing beside an active grant to that wallet is a validation
  failure (this is the gap, stated as an obligation over EXISTING carriers);
  resuming requires an explicit, human-ratified issuance act, never an
  automatic or standing reissue (limb a); and a declared model component names
  an EXACT version — a family or alias is not a pin and is a validation failure
  (limb d, ratifying today's behavior as intended).

Both restatements keep every existing scenario intact and add four each.

**Limb (c) is stated without naming openxFactory's mechanism.** openXwallet is
a neutral PRODUCT that other repositories pin; it must not name openxFactory's
Human Escalation Contract as its own machinery. The requirement therefore
states the obligation — a human is reached through the consuming capability's
declared escalation path — and `design.md` cites the HEC decision-ready packet
as the HOUSE shape that discharges it.

## What this change does NOT do

- **No contract bytes.** `contracts/` is untouched. Every obligation above is
  stated over carriers the grant schema ALREADY has:
  `contracts/openxwallet/openxwallet-grant.schema.yaml` carries
  `parent_grant_ref` ("revocation propagates down this edge"),
  `state: [active, expired, revoked]`, and
  `revocation: {revoked_at, reason, propagated_from}` — `propagated_from` is
  exactly the edge-recording field the second obligation names. Any genuinely
  new carrier is a DECLARED realization task, not an edit made here.
- **No validator change.** `scripts/validate-openxwallet.py` is untouched. The
  cascade rule is declared as the realization surface and named in `tasks.md`;
  it is not written in a proposal.
- **No version allocation.** See `target_release` above.
- **It does not build limb (d)'s exit.** The ruling says family pinning "may be
  revisited only through a future core delta that can police it." This change
  ratifies exact-versions-only as intended behavior and does not soften it. See
  the carried question below.

## OPEN QUESTION carried for the convener — the model-family pin

**Not decided here, and deliberately not answered.** Q8 limb (d) ratified
exact-versions-only and said family pinning may be revisited only through a
future core delta that can police it. The question this change carries up:

> Should the core delta being authored NOW define that policing mechanism — a
> family pin plus an attested resolved-version record, re-attested on every
> roll — or does exact-versions-only stand un-revisited?

Both exits and their costs are set out in `design.md` under `## Open
questions`. This proposal takes neither. Ruling it is the convener's act, and
it is named here so it cannot be lost in the design document.

## Impact

- Two promoted requirements in this repository are restated; no capability is
  added or removed. Eleven promoted requirements remain eleven.
- Consumers that pin openXwallet gain an obligation they do not yet meet
  mechanically. The declared realization surface is what closes it, and it
  lands under its own version allocation with the full gate bar.
- openxFactory's `add-wallet-carried-review-authority` design risk **R1** — a
  silent provider alias roll revoking every seat grant, parking every convening
  under `missing_required_seat: refused`, with `--admin` as the only routine
  exit under a sole code owner — is NOT closed by this change and is made more
  consequential by it, because the cascade is now an obligation rather than a
  gap. Its exit is that change's task 7.6 runbook, an operator act. This
  proposal names the consequence honestly rather than mitigating it with an
  automatic reissue the ruling forbids.

## Status

`Status: draft`. **Held for Brett Heap's ratification.** Nothing here is
ratified by its authoring, and no realization work may begin until the
ratification gate in `tasks.md` is checked. The underlying Q8 ruling is already
made — what awaits ratification is this ENCODING of it, plus the reissuance
policy proposed in `design.md` and the carried question above.
