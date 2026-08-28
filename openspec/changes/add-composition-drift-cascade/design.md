# Design: add-composition-drift-cascade

## Context

openxFactory's ratified `add-wallet-carried-review-authority` ruled **Q8** on
2026-08-26 (Brett Heap, `rulings-2026-08-26.md`) as a **fail-closed bundle** —
all four limbs together, in the fail-closed direction:

1. **(a)** Reissue is always an explicit register act. No auto-reissue, no
   standing reissue policy that acts on its own.
2. **(b)** DRIFT cascades like CAUSE. Derived authority never survives an
   unattested drift. "Mechanical cascade enforcement rides the `openxwallet` /
   `openxwallet-agent-profile` core deltas (S5-era work)."
3. **(c)** Empty-register notification rides the Human Escalation Contract's
   parked decision-ready packet shape (N12).
4. **(d)** Exact model versions only. Today's validation failure on a family
   pin is ratified as intended behavior; family pinning "may be revisited only
   through a future core delta that can police it."

The §8.1 Addendum then moved the home of those two deltas to this repository:
both capabilities left the openxFactory corpus at `contract-v2.0`
(`split-openxwallet-repo`'s two `## REMOVED Requirements` blocks), so a delta
authored against them upstream would modify a capability that corpus no longer
holds.

**This design encodes a ruling. It does not re-open one.** Where it proposes
something the ruling did not settle — the reissuance policy's shape, and the
carried question — it says so explicitly and stops.

## The mechanical gap, precisely

Composition drift is a self-declaration and nothing checks it against the
wallet's actual grants.

- `contracts/openxwallet-agent-profile/openxwallet-agent-composition.schema.yaml`
  carries `grants_state: [active, revoked_on_composition_change]`.
- The validator's rule (p), `declared-change-not-revoked`
  (`scripts/validate-openxwallet.py:1233-1244`), fires only when the attested
  hash differs from the declared hash AND `grants_state` is not
  `revoked_on_composition_change`. It compares the composition record against
  ITSELF.
- Nothing walks from that declaration to the `xfactory_wallet_grant` records —
  their `state`, their `revocation.propagated_from`, their derived children.

The validator already knows how to do this for the other two revocation paths.
`_revoked_ancestor` (`scripts/validate-openxwallet.py:896-911`) walks
`parent_grant_ref` upward, returning the first revoked ancestor grant or the
first revoked holder wallet. Composition drift simply never enters that walk.

So today a composition record can declare that its identity ended while every
grant it issued remains `active`, every derived grant remains `active`, and the
required `wallet-validation` check stays green. That is the fail-open the
ruling closes.

## Why the obligations go where they do

**Limb (b) is stated in the CORE, not the profile.** The agent-profile
requirement already delegates: grants are revoked "at once **through the core's
revocation-propagation rule**." Putting the cascade semantics in the profile
would give the family two propagation rules — one general, one for agents —
which is the failure mode the core/profile split exists to prevent. The core
gains reason classes and the rule that a class is never a propagation gate; the
profile states that composition change produces the DRIFT class and inherits
the cascade. The profile stays agent-specific, and a future patient or
practitioner profile inherits the same cascade for free.

**Limb (c) is stated NEUTRALLY.** openXwallet is a product other repositories
pin; it must not name openxFactory's Human Escalation Contract as its own
mechanism, or every consumer inherits a dependency on one consumer's
machinery. The requirement states the obligation — a human is reached through
the CONSUMING capability's declared escalation path, and a log line does not
discharge it — and the house shape is cited here, in design, where it belongs.

**Every obligation is stated over EXISTING carriers.**
`contracts/openxwallet/openxwallet-grant.schema.yaml` already has
`parent_grant_ref` (documented as the edge revocation propagates down),
`state: [active, expired, revoked]`, and
`revocation: {revoked_at, reason, propagated_from}`. `propagated_from` is
exactly the edge-recording field the core's second new obligation names. The
deltas therefore state obligations the schema can already carry; any genuinely
new carrier is a declared realization task, not a schema edit made in a
proposal.

## The Q8 reissuance policy — PROPOSED, not ruled

Q8 limb (a) settled the DIRECTION: reissue is always an explicit register act.
It did not describe the act. As S5's implementer I propose the following shape;
**the convener rules it.**

### Reissuance as a first-class act

A reissuance is an ACT that is performed and recorded, not a state transition
that happens. It records five things:

| Recorded | Why it is on the act |
| --- | --- |
| The superseding grant | The authority that now exists, as a new grant with its own audience, scope and expiry. |
| The superseded grant | What ended, by reference — so the chain reads forward from the revocation instead of a reader inferring a replacement from timestamps. |
| The composition hash issued against | The identity the authority was granted TO. Without it, a reissuance is authority granted to a name rather than to a thing. |
| The human who ratified it | Limb (a)'s substance. An act with no named human is a policy wearing an act's clothes. |
| The instant | The gap between revocation and resumption is the honest measure of what fail-closed cost, and it is only measurable if both ends are recorded. |

**Why an ACT and not a state transition.** A state transition can be triggered.
Anything that can be triggered can be triggered by the thing it is meant to
police — a provider roll re-attesting itself back into authority is precisely
the failure the composition hash exists to catch. An act cannot fire on its
own: it has a performer, and the performer is a named human. This is also why
the core delta states that a revoked grant NEVER returns to active. If
resumption were reactivation, the record would show authority that appears
never to have stopped, and the drift would leave no trace at all. A new grant
that names what it supersedes keeps the interruption visible forever.

**Why no standing or automatic form exists.** A standing reissue policy is an
auto-reissue with a human's signature collected in advance, for a composition
that did not yet exist when they signed. It converts human ratification from a
judgment about a specific change into a blanket pre-authorization — which is
exactly the authority the composition hash is designed to withhold.

**The operational consequence, named honestly.** Under
`missing_required_seat: refused`, a provider alias roll revokes every seat
grant at once and parks every in-flight and future convening until a human
performs the reissuance act. That is design risk **R1** of the parent change
(HIGH): the only routine exit from a parked candidate under a sole code owner
is `--admin` — the change's strictest inherited control manufacturing the
ritual the change exists to break. **This policy does not mitigate R1. It makes
R1 load-bearing.** The exit is the parent change's task **7.6** — the governed
re-issuance RUNBOOK for a provider alias roll, walked once against a deliberate
composition bump — plus the operator's root authority. It is deliberately NOT
an automatic reissue, because the ruling forbids one. Anyone reading this
design should understand that fail-closed here is a real operational cost that
was chosen with its price known.

### Drift-vs-cause survival

Derived grants do NOT survive either class. The reason class is **evidence,
never a gate**: it is recorded so a reader can tell why authority ended, and it
is never consulted when deciding how far the ending reaches.

This is stated as a positive rule rather than left as an absence, because an
absence invites the natural-seeming optimization: "drift is not misconduct, so
a narrowed derived grant could survive it." That reasoning is wrong in a
specific way. Drift means the holder is not what it was attested to be. A
derived grant is authority granted on the strength of the parent holder's
identity; narrower scope does not make it authority granted to a DIFFERENT,
still-attested thing. Surviving derivation would let an agent that changed
underneath its attestation keep acting through its own children.

### Operator notification

The decision-ready packet is the house shape, cited to the parent change's
**N12** and the Human Escalation Contract (`docs/roles-and-authority.md:124-140`
in openxFactory): decisions requiring human authority PARK rather than
interrupt, and are delivered as a packet carrying a situation summary, at most
three options with exactly one recommendation, evidence references, and the
consequence of each option AND of deciding nothing — with packets deduplicating
by root cause and silence failing closed.

That shape answers all four questions a mass revocation raises: **who** (the
responsible human named by the consuming capability), **what decision** (resume
authority by a reissuance act, or leave it revoked), **what the options are**
(at most three, one recommended), and **what happens if nothing is decided**
(everything stays parked — silence is fail-closed, which is the correct default
and must be stated, not assumed).

Deduplication by root cause matters at exactly this event: one provider roll
revokes N seat grants and would otherwise raise N packets, each individually
true and collectively useless. One root cause, one packet.

**This shape is cited here and NOT written into the neutral requirement.** The
requirement obliges the consuming capability to have a declared escalation path
and to use it; it does not oblige every consumer of openXwallet to adopt
openxFactory's packet.

## Open questions

### CARRIED FOR THE CONVENER, NOT DECIDED — the model-family pin

Limb (d) ratified exact-versions-only and said family pinning "may be revisited
only through a future core delta that can police it." A core delta is being
authored right now. So the question is live, and it is not mine to answer:

> **Should the core delta being authored now define that policing mechanism — a
> family pin PLUS an attested resolved-version record, re-attested on every
> roll — or does exact-versions-only stand un-revisited?**

Both exits, with their costs:

**Exit 1 — define the policing mechanism now.** A holder pins a family
(`gpt-5.x`) and separately attests the EXACT version it resolved to; the
resolved version is a declared component of the composition hash; a roll that
changes the resolved version changes the hash and revokes, exactly as an exact
pin does today.

- *Buys:* the operator writes the pin once instead of editing a declaration on
  every provider roll, while the revocation trigger stays exactly as sharp —
  the hash still covers the exact version, so nothing about the cascade is
  weakened.
- *Costs:* a new attestation carrier and a new attestation obligation, at a
  moment when the family has zero wallets and no key infrastructure (parent
  change risk R2, the day-one empty world). It also introduces a window: between
  a roll and the re-attestation, the declared family is satisfied while the
  attested version is stale, and something must decide what authority means in
  that window — which is a NEW fail-open shape to police, in a change whose
  whole purpose is closing one. And it widens this change from an encoding of a
  ruling into a change that revisits one of the ruling's limbs, which is a
  different kind of act needing its own scrutiny.

**Exit 2 — exact-versions-only stands un-revisited.** This change ratifies
today's validation failure as intended behavior and defines no family-pin
mechanism.

- *Buys:* the change stays exactly what it says it is — an encoding of a ruling
  already made — with no new carrier, no new attestation obligation, and no new
  window to police. The fail-closed bundle stays whole.
- *Costs:* every provider alias roll requires a declaration edit AND a
  reissuance act, so R1's operational pressure is felt at full strength on
  every roll, with task 7.6's runbook as the only relief. If that pressure
  proves unbearable in practice, revisiting it later means a second core delta
  against requirements that will by then be promoted and pinned by consumers.

**No recommendation is offered and none should be inferred from the ordering.**
The deltas as authored are consistent with **Exit 2**; adopting Exit 1 requires
amending the agent-profile delta's fifth paragraph before ratification, which
is a small edit and is the reason this question must be ruled BEFORE the
ratification gate rather than after it.

**Resolved 2026-08-28 by ratification as proposed:** the delta's exact-version
rule stands — a declared model component names an exact version, and a family
pin is a validation failure. Admitting a family pin would now be a new change.

## Corpus drift observed and NOT taken on

Two pre-existing inconsistencies were seen while authoring. Neither is caused
by this change, neither is fixed by it, and both are recorded so the next
reader does not re-derive them:

1. **`OXWR-R1` / `OXWR-R2` have no promoted requirement heading.** The
   validator's `REQUIREMENTS` dict carries these two requirement rows — the S2
   issuer anchor — but no matching `### Requirement:` heading exists in
   `openspec/specs/openxwallet/spec.md`. The validator therefore asserts
   traceability to spec text that the promoted corpus does not contain. Fixing
   it means either promoting the requirement or retiring the rows, both of which
   are S2's business, not this change's.
2. **`docs/contract-versioning-policy.md` does not exist.** Both contract
   READMEs reference it. The versioning rules it would state currently live only
   in `AGENTS.md` ("a release is five coordinated values") and
   `contracts/CHANGELOG.md`.

## What this change deliberately does not do

- **No contract bytes.** `contracts/` is untouched; the obligations are stated
  over carriers the grant schema already has.
- **No validator change.** The cascade rule is the DECLARED realization
  surface, named in `tasks.md` and not performed here.
- **No version allocation.** Versions are allocated at realization (AGENTS.md).
- **No new capability and no new requirement.** Two restatements, eleven
  promoted requirements before and after.
- **It does not soften limb (d).** Exact-versions-only is restated as intended
  behavior; the question of revisiting it is carried up, not answered down.
