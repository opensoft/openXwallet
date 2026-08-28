# Design: add-multi-key-wallets

## D1 — `keys:` declares ADDITIONAL keys beside `key_reference`; it does not replace it

The declared key set is `{key_reference} ∪ {keys[*]}`, and `keys:` is OPTIONAL.

The alternative — make `keys:` the whole set and demote `key_reference` to a
convenience — was REJECTED. It would either require every existing record in the
estate to move its primary key into a new list (a breaking change to a digested
contract, which is not what "additive" means), or leave two spellings of the
same fact with a precedence rule between them, which is the shape that lets a
reader and a writer disagree about which key is the wallet's. Keeping
`key_reference` as the primary declaration means a record that omits `keys:`
takes exactly the code path it takes today: the union is a one-element set and
every rule keyed on it computes what it computed before.

A `keys:` entry repeating `key_reference.key_id` is therefore a DUPLICATE, not a
restatement (D4).

The set is computed by ONE function, `declared_keys(doc)`, which returns
`(key_id, custody_mapping, declaration_site)` triples with `key_reference`
first. Every rule that needs the set calls it, so there is no second traversal
to drift — the failure mode of a shape whose membership is recomputed in three
places.

## D2 — Custody is declared PER KEY, and a key may not outrank its wallet

Each `keys[]` entry carries a `custody` block of the SAME shape as the wallet's
top-level one — `model` and `registry_version` required, `declared_at` and
`declared_by` optional — resolved against the SAME closed registry. Rule (s)
(a wallet's declared custody is in the closed set) therefore runs per key, under
the EXISTING `custody-model-unknown` code: it is the same rule at a new depth,
not a new rule, and adding a code string for it would put a second name on one
defect for consumers that pin code strings. The in-tree precedent is exact —
that one code already serves two different subjects, a wallet's declaration and
an exercise's `custody_model_in_force`.

`custody` is REQUIRED on a `keys[]` entry. A declared key with no custody
declaration would be a key whose signature evidences nothing anybody wrote down,
which is precisely the state the 2026-08-07 ruling exists to make
unrepresentable.

**A declared key's custody ceiling may not outrank the wallet's own**
(`declared-key-raises-authority`, NEW). The check compares RANKS, the way rule
(c) does, so a registry that renamed a tier cannot slip past it.

**Its rationale, corrected.** The first draft justified this as closing "a route
around rule (e)". That was FALSE and the alignment pass caught it:
`ceiling_for_wallet` reads the wallet's top-level custody only, nothing in this
change moves it, and D3 caps use by the SIGNING key — so a stronger declared key
never widened anything. The real reason is a MONOTONE DECLARATION INVARIANT: a
reader of a wallet record must be able to take the wallet's declared ceiling as
the ceiling of everything that record declares, without walking the key list to
find out whether some member claims more. Without the check, "this wallet's
authority is capped at `act`" stops being a fact about the record and becomes a
fact about the primary key only, and every consumer that reads the wallet's
custody to decide what it may be granted would be reading a partial answer. The
ruling's words for the same idea are "keys never multiply authority"; this is
what makes them a computation instead of a promise.

Note the direction: a key may be WEAKER than its wallet, and often should be.
Weakness is capped at exercise (D3), where it belongs — the wallet's own ceiling
stays the grant-issuance cap, so adding a weak key never silently lowers
authority a grant already relies on.

## D3 — At exercise, the custody in force is the PRESENTING key's

`custody-model-mismatch` keeps its code and changes its comparison BASIS. The
resolution is stated as a function rather than described, because the alignment
pass found the description ambiguous enough to read as deleting the check:

    basis_custody(wallet, presenting_key) =
        the `keys[]` entry's `custody` block   when the presenting key is a
                                              `keys[]` member of that wallet
        the wallet's top-level `custody` block when the presenting key is the
                                              wallet's `key_reference`
        the wallet's top-level `custody` block when NO presenting key is
                                              ESTABLISHED

`key_reference` carries no `custody` block of its own (D10), so the primary key's
per-key custody IS the wallet's top-level declaration. For every single-key
record the basis is therefore byte-identical to today's, and the check cannot be
silently deleted by a falsy lookup.

**ESTABLISHED means a VERIFIED proof named the key.** The alignment pass caught
the second half of this: the existing code sets
`presenting_key = verified_key if verified is True else attributed_key`, so a
record claiming `verification_failure` with `mode: key_attributed` names a key
from its own UNVERIFIED attribution block. Keying the custody basis or the
evidence cap on that key would measure an exercise against a self-declared fact,
which is the laundering surface rule (r) exists to close. So both new behaviours
gate on `verified is True`; an unverified exercise takes the wallet's top-level
custody, exactly as before.

**The teeth: `presenting-key-evidence-cap` (NEW).** The grant's authority tier
may not exceed the CEILING of the presenting key's custody. Rule (e) already
caps a grant's tier by its audience wallet's ceiling at issuance — the only cap
issuance can apply, since it cannot know which of the wallet's keys will sign.
This caps the same tier by the SIGNING key's ceiling at use. Without it a wallet
holds a grant its weakest key exercises anyway, and the custody ladder is
silently re-flattened by whichever key was reachable.

**Guarded on `outcome == "permitted"`, like every other use-time cap.** The
alignment pass caught that an unguarded check makes a TRUTHFUL REFUSAL
unrecordable: the exercise contract already closes a refusal code
`custody_ceiling_exceeded` for exactly this event, and a record that correctly
documents such a refusal must not itself be a finding. `proof-of-possession-`
`missing`, `revoked-chain-exercised` and `distinct-holder-violated` all guard the
same way.

## D4 — Rule (r) resolves against the declared SET, and identifiers are declared once

`Context.wallets_by_key` gains every declared key, not only
`key_reference.key_id`. Rule (r)'s two existing refusals then do the work
unchanged and under their existing code:

- a presenting key in NO wallet's declared set → `presenting-key-unresolved`;
- a presenting key in MORE THAN ONE wallet's declared set →
  `presenting-key-unresolved` (ambiguous; `key_id` is DID-scoped, so a bare ref
  cannot say which wallet presented).

That code's MESSAGE currently says the key "is no known wallet's
`key_reference`", which this change makes false. The message is corrected; the
code and its pinned detail substring (`an exercise presented by an unknown key`)
are not touched.

The inter-wallet ambiguity check dedupes by wallet id, so it cannot see a wallet
declaring one identifier TWICE — and last-write-wins on the index would then
decide which declaration (and therefore which custody) an exercise resolves to.
`declared-key-duplicate` (NEW) refuses that at the record, which is where the
defect is, rather than at the exercise, where it is only observable.

## D5 — The fingerprint is RECOMPUTED where a public half is declared

`key_fingerprint` is REQUIRED on every `keys[]` entry and admitted as OPTIONAL
on the existing `key_reference`. The asymmetry is deliberate and stated in the
schema: requiring it on `key_reference` would invalidate every record in the
estate, and a contract that breaks its consumers to gain a field is not additive.

The value's SHAPE is validated — `sha256:` plus 64 lowercase hex, the one
spelling the mint record, the register reader and hermes-install all compute.

**And where the entry declares `public_key_multibase`, the fingerprint is
RECOMPUTED from it** (`declared-key-fingerprint-mismatch`, NEW). The first draft
said the record carried no public half to recompute from, and the alignment pass
was right that this left the fingerprint decorative in the one instance that
motivated the change. It is not true that no public half is available: the
schema's existing `public_key_multibase` field is `did:key`'s own encoding —
`z` plus base58btc of the two-byte ed25519 multicodec prefix and the 32 raw
bytes — which the estate's live wallet already carries, and
`sha256(raw 32 bytes)` over the decoded body is exactly the fingerprint spelling
everything else computes. So the field is decoded and the fingerprint checked.
The check is CONDITIONAL because `public_key_multibase` is optional: an entry
that declares no public half declares a fingerprint whose proof lives on
whatever surface holds the key, and that is honest rather than checked.

`did` is REQUIRED on a `keys[]` entry, matching `key_reference`. The first draft
made it optional, and the alignment pass rejected that on the delta's own terms:
the requirement says a wallet's keys are "anchored to decentralized
identifiers", and D4 rests the ambiguity refusal on `key_id` being DID-scoped —
a key with no anchor has nothing to be scoped by. For an ed25519 key the anchor
is not an invention either; `did:key:<multibase>` is derived from the public half
itself, which is why the live wallet's `did` and `public_key_multibase` are the
same string.

**What remains deferred, and it is now narrow.** The register's `seat_keys[]`
entries recompute their fingerprints from a base64url public half; a wallet's
declared keys recompute theirs from a base58btc one. Both anchor to the same
mint record, and both are checked. The one unchecked step is that the TWO
SURFACES describe the same 32 bytes — a cross-surface comparison belonging to
`review-authority-register-reader`, not to `openxwallet` (D6.5). The consuming
change is obliged to PROVE the agreement by computation in its own pull request
(tasks 5.3) rather than assert it.

## D6 — Non-goals, named so they are not read into the delta

The operator ruled option 1 and only option 1. These are OUT, and each is out
for a reason rather than by omission:

1. **Subwallets.** A wallet inside a wallet needs a containment relation, a
   propagation rule for revocation and standing, and an answer to whether a
   subwallet's holder is its parent's. None of that is a key-set question.
2. **Per-key grants.** Grants stay WALLET-LEVEL by the ruling, and by shape: the
   grant contract's `audience` admits `wallet_ref` and `holder_ref` only, and
   nothing here adds a key field to it. A per-key grant would make the key the
   unit of authority, which is the exact inversion the core's second requirement
   exists to prevent — authority travels as attenuated grants, never as keys.
3. **Delegation chains.** A key authorizing another key is a second attenuation
   mechanism beside grants, with its own revocation semantics. hermes-install
   already runs a root-key/ephemeral-key authorization protocol INSIDE one
   convening; the ruling deliberately keeps that inside the runtime and out of
   the contract, and the exercise record names the REGISTER-RECORDED key for
   exactly that reason.
4. **Shared holders.** One key declared by two wallets stays what it is today:
   ambiguous, and refused as ambiguous. Making it legal needs a rule for which
   wallet an act attributes to, which is an attribution question, not a set one.
5. **A cross-surface fingerprint-agreement check** between the register's
   `seat_keys[].key_fingerprint` and the same key's wallet declaration (D5). It
   is small and worth doing; it belongs to `review-authority-register-reader`
   and is named here so it is not discovered a third time.
6. **Per-key custody in hermes-install's projection.** Today the projection
   carries ONE `custody_model` per seat and every seat key in openxFactory
   declares `holder_readable`, so `custody_model_in_force` matches the
   presenting key's custody without a change. The day two of a wallet's keys
   declare DIFFERENT custody models and both are projected, the projection must
   carry custody per key or D3's basis check will refuse the record. Named,
   dated by that condition, and not built on speculation.
7. **An independent custody declaration for the primary key** (D10). Additive
   when it is wanted, and not wanted yet.

## D7 — Which closed-set member the seat keys fall under, determined honestly

The realization records this determination and openxFactory's completion acts on
it, so it is settled here rather than assumed downstream.

**The four CI-resident seat root keys: `holder_readable`.** The registry member
is defined by two booleans, and both are answerable from the mint record without
interpretation. Each private half is a 32-byte Ed25519 seed held as an encrypted
GitHub Actions secret in codexFactory's `worker-credentials` environment and read
by `root_key_from_env()` out of the `deliberate` job's own process environment.
The holder's execution context is that job. So
`key_readable_by_holder_execution_context: true` and
`use_requires_authorization_outside_holder_execution_context: false` — which is
`holder_readable`, evidencing the ENVIRONMENT, ceiling `act`. Nothing is
stretched: this is the member's own description ("an environment variable or a
mounted secret") describing the artifact exactly.

**The per-convening ephemeral keys: `holder_readable` as well, and they are not
declared.** An ephemeral key is minted inside the job and its private half lives
in that job's process memory, so the first boolean is true for it too. It is not
`isolated_per_use_authorized`: the authorization its use requires is the root
signature, and the SAME execution context produces that — an authorization a
context can supply itself is not an authorization outside it. Ephemerals are
therefore not declared in the wallet at all (they cannot be enumerated in a
static record, and hermes already names the register-recorded key in
`presenting_key_ref` for precisely this reason); their fingerprint travels as
runtime evidence.

**Q10 is NOT implicated.** The still-open authorizer question — may a non-human
authorizer such as MRC satisfy `isolated_per_use_authorized`, ruled ADMIT WITH
CONDITIONS on 2026-08-26 with the `act_unsupervised` exclusion left in force
until the admission conditions are designed and validated — bears on the
`isolated_per_use_authorized` member. Neither the seat roots nor the ephemerals
reach for that member, and no key declared by this change carries a ceiling above
`act`. The closed three-member set fits both cases without stretching, so nothing
here is carried against Q10 and nothing here narrows it.

## D8 — Release class: an ADDITIVE MINOR whose digest MOVES

`wallet-v1.2` was the unusual case — a reader change with eight unchanged
digests. `wallet-v1.3` is the ordinary case: `openxwallet-record.schema.yaml`
changes, so its `sha256:` moves in `contracts/manifest.yaml` and in the `files:`
block of every consumer's pin. Seven of the eight rows are untouched.

MINOR, not MAJOR, because nothing a consumer declares today becomes invalid: the
new list is optional, the new required fields are required only inside the new
list, no code is renamed, and no warning is added.

**Which version field moves, named exactly**, because three fields are called
some spelling of "schema version" in this one file and the alignment pass was
right that "refreshed" does not say which:

- the schema file's `contract_schema_version: 1 → 2` — the per-file value
  AGENTS.md rule 6 names among the five coordinated release values;
- `contracts/manifest.yaml`'s `openxwallet-record` row `schema_version: 1 → 2`,
  which mirrors it;
- the schema file's own top-level `schema_version: 1` does NOT move. It is the
  contract-schema-DOCUMENT meta version, shared by all nine members of the
  bundle, and it describes the shape of the wrapper rather than the contract.

There is no `docs/contract-versioning-policy.md` in this repository — the
reference `contracts/openxwallet/README.md` carries is a dangling carve
artifact, already logged in `add-composition-drift-cascade`'s design. So the
bump rule applied here is AGENTS.md rule 6 plus the reading above, stated in the
CHANGELOG so the next release has a precedent rather than a broken link.

`wallet-v1.3.digests.yaml` over `member_class: owned` members is an OPERATOR ACT
that follows the human merge, exactly as it was at `wallet-v1.0` and
`wallet-v1.1`. It is not produced by this change and is listed as remaining work
rather than silently omitted.

## D9 — A declared key is RETIRED, never deleted

A `keys[]` entry admits an OPTIONAL `state` — `active | suspended | revoked`,
the same closed set and the same default as the wallet's own `state`.

The alignment pass found the hole this closes, and it is not hypothetical: four
CI-resident seat keys will rotate, and the whole point of this change is that
exercise records naming those keys get COMMITTED to a tree this validator
scans on every run. If the only way to retire a key were deleting its entry,
every already-committed exercise naming it would start failing
`presenting-key-unresolved` the moment it was retired — history retroactively
invalidated by a rotation. A single-key wallet never meets this, because you
revoke the WALLET and never delete its `key_reference`; multi-key makes
rotation the ordinary operation, so the ordinary operation needs a shape.

**So the rule is: a declaration is APPEND-ONLY and its state is what moves.** An
exercise PERMITTED under a key whose declaration is `suspended` or `revoked` is
refused under the EXISTING `revoked-chain-exercised` code — the same rule as a
revoked grant or a suspended wallet, checked at use rather than trusted from
issuance, so it needs no new code string. A record naming a retired key with any
other outcome still validates, which is what keeps committed history readable.

## D10 — The primary key's custody does two jobs, and this says so

The wallet's top-level `custody` block is simultaneously rule (e)'s
ISSUANCE CEILING for the wallet and the PER-KEY custody of the primary key.
That is not a defect of this change — it is how the record has always been read —
but the alignment pass was right that a delta claiming custody is declared "for
every key it declares" must say where the primary key's declaration lives.

The consequence is real and is recorded rather than hidden: a wallet cannot
weaken or retire its primary key without lowering its own grant ceiling, and
`declared-key-raises-authority` compares each `keys[]` entry against a value that
is definitionally the primary key's ceiling. Admitting an OPTIONAL `custody` on
`key_reference` so the two roles can diverge is equally additive and is a NAMED
SUCCESSOR (D6.7), not taken here: it would introduce a precedence question
between two declarations of one key's custody, and nothing in the estate needs
the divergence yet.

## Alternatives rejected

- **Declare the seat keys as four separate WALLETS.** Rejected in the ruling's
  own terms: it multiplies authority (four wallets need four grants, or one grant
  whose audience is four wallets, neither of which the grant shape expresses),
  and it says the council is four holders when it is one body. The register
  already commissions ONE holder with ONE row.
- **Widen rule (r) to resolve a presenting key through the REGISTER.** Rejected:
  it makes the neutral validator's core rule depend on a factory-layer intake
  surface that most consumers do not have, and it leaves the wallet standard
  unable to say which keys may present a wallet's authority — the gap this change
  exists to close.
- **Relax rule (r) to warn instead of refuse on an undeclared presenting key.**
  Rejected: LedgerxFactory runs `--strict`, so a warning is an exit code there
  and a silence everywhere else, which is the worst of both. And the refusal is
  correct — an unresolvable presenting key means the audience binding cannot be
  checked at all.

## Alignment pass — 2026-08-28

ONE reviewer, adversarial, over the authored packet at `Status: draft`, against
the current ratified spec, the three contracts, the validator's rules and the
whole packaged corpus. Fourteen verdicts returned: five DEFECT, six CONCERN,
three ALIGNED. Recorded as returned, with the disposition of each.

1. **DEFECT — the custody basis for a PRIMARY presenting key was undefined, and
   the literal reading deleted `custody-model-mismatch` for every record in the
   estate.** `key_reference` carries no `custody` block, so "the presenting key's
   declared custody" resolved to nothing for a single-key record and the check
   would never fire; no shipped negative pins that code, so the corpus would not
   have caught it. FIXED: D3 states the resolution as a function, and a
   SINGLE-KEY `custody-model-mismatch` negative is added as the no-op regression
   proof (tasks 3.11).
2. **DEFECT — `did` OPTIONAL on a `keys[]` entry contradicted the delta's own
   requirement text and was not in the ruling.** FIXED: `did` is REQUIRED,
   matching `key_reference` (D5). The reviewer's reasoning is adopted verbatim —
   a key with no anchor has nothing for `key_id` to be scoped by, which is what
   D4's ambiguity refusal rests on.
3. **DEFECT — no per-key retirement, so retiring a key retroactively invalidates
   committed history.** FIXED: D9. An optional per-key `state`, declarations
   append-only, and an exercise permitted under a retired key refused under the
   existing `revoked-chain-exercised` code.
4. **DEFECT — no id-disjointness constraint on the new corpus fixtures; a reused
   `key_id` would make `wallets_by_key` two-owner and flip every shipped
   exercise positive to ambiguous.** FIXED: tasks 3.12 makes disjointness an
   asserted obligation rather than an assumption.
5. **DEFECT — `presenting-key-evidence-cap` had no outcome guard, making a
   TRUTHFUL REFUSAL unrecordable** (the exercise contract already closes a
   `custody_ceiling_exceeded` refusal code for this event). FIXED: guarded on
   `outcome == "permitted"`, like every other use-time cap (D3).
6. **CONCERN — D2's stated rationale for `declared-key-raises-authority` was not
   true against the code.** ACCEPTED as stated. The check is KEPT and its
   rationale replaced with the real one — a monotone declaration invariant
   (D2). The reviewer's correction of the false claim is adopted in full.
7. **CONCERN — one field doing two jobs, unacknowledged.** ACCEPTED: D10 states
   the coupling and its consequence, and names the divergence as a successor
   rather than taking it.
8. **CONCERN — D3's fallback claim was wrong for the verification-failure
   path**: `presenting_key` falls back to the record's UNVERIFIED attribution
   key, so the basis would key on self-declared data. FIXED: both new behaviours
   gate on `verified is True` (D3).
9. **CONCERN — a message left factually false, and new invariants with no
   durable probe.** FIXED both: `presenting-key-unresolved`'s message no longer
   says "key_reference" (D4), and named-probe assertions are added for the new
   fixtures (tasks 3.13), following the precedent
   `add-per-seat-register-entries` set — requirement-level closure cannot notice
   a deleted fixture when the new invariants attribute to existing requirement
   ids.
10. **CONCERN — three soft spots in release bookkeeping**: a cited versioning
    policy that does not exist in this repository, an ambiguous "schema_version
    refreshed", and an omitted `wallet-v1.3.digests.yaml`. FIXED: D8 names the
    exact fields that move and the one that does not, states the bump rule
    applied in the absence of the policy document, and records the digests file
    as the operator act it has been since `wallet-v1.0`. The AGENTS.md Speckit
    block is ticked to feature 015 (tasks 4.5).
11. **CONCERN — the fingerprint's declared purpose was entirely deferred.**
    PARTLY FIXED, and the fix is larger than the reviewer proposed: the
    fingerprint is now RECOMPUTED from `public_key_multibase` wherever an entry
    declares one (`declared-key-fingerprint-mismatch`, D5), so a wallet's
    fingerprint is provable on its own surface rather than decorative. The
    remaining step — that the register's and the wallet's public halves describe
    the same 32 bytes — stays a `review-authority-register-reader` successor,
    and the consuming change is OBLIGED to prove the agreement by computation
    in its own pull request (tasks 5.3).
12. **ALIGNED — OpenSpec mechanics**, with one residual: the capability's
    `## Purpose` still reads "a signing key anchored to a decentralized
    identifier" and no delta form can move it. ACCEPTED: tasks 6.4 corrects that
    sentence as an editorial edit in the realization, ratified by this change,
    with the reason recorded — otherwise the promoted spec ships
    self-contradictory.
13. **ALIGNED — finding-code discipline on `custody-model-unknown`, and D4's
    reading of the duplicate machinery.** The reviewer's stronger argument (that
    one code already serves two subjects in-tree) is adopted into D2 and into
    the CHANGELOG entry.
14. **ALIGNED — the rest of the rule walk**: rule (a) already recurses through
    lists and needs no `_KEY_NAME_ALLOW` edit; rule (q) resolves by `wallet_ref`
    and is untouched; `_ID_FIELDS` is per-RECORD identity and correctly stays
    out of per-key ids; rule (u)'s seat surface takes no wallet-declaration
    dependency; ONE digested artifact moves, verified against the eight owned
    manifest rows.

## Ratification record

Ratified 2026-08-28 by Brett Heap, operator authority, by in-session ruling:
**"rule option 1 and build it"** — option 1 as explained and recommended
in-session, being: one wallet MAY declare several keys as presenters of its
single authority, each declared key carrying its own custody declaration and
fingerprint; grants stay wallet-level so keys never multiply authority; audit
stays key-attributed; the validator's rule (r) extends to "presenting key ∈ the
wallet's declared key set"; and per-key custody caps what that key's signature
evidences. Subwallets, per-key grants, delegation chains and shared holders were
explicitly excluded by the same ruling.

The ruling is the ratification basis. The alignment pass above ran against the
draft; its five defects were fixed and its six concerns dispositioned before
this status was recorded. The verdicts stand as returned, not as summarised —
including the two that found this packet's own reasoning false (items 1 and 6),
which are recorded as errors corrected rather than paraphrased away.
