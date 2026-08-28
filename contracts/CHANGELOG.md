# openXwallet contract changelog

Status: standard

The wallet standard's own release history. Bundles are `wallet-v<major>.<minor>`
and are identified by five coordinated values: per-file `contract_schema_version`,
`contract_bundle_version` in [`manifest.yaml`](./manifest.yaml), an annotated
`wallet-v<major>.<minor>` tag, the exact release commit with per-file SHA-256
digests, and the matching entry below. Consumers pin the exact commit and digests
— **a movable branch or tag is not a compatibility pin.**

**Release-surface rule.** `wallet-vN.M.digests.yaml` selects
`member_class: owned` **only**. Exclusion is by DECLARED FIELD, never by a
`contracts/schemas/` path heuristic — that heuristic breaks the day openXwallet
publishes a schema of its own there. The one consumed member
(`contracts/schemas/hermes-job-envelope.schema.yaml`, vendored from openxFactory
at a digest pin) carries `release_surface: false` and is never part of a wallet
bundle.

---

## wallet-v1.2 — 2026-08-28 (additive minor; validator behaviour only)

**Change class: ADDITIVE MINOR.** No contract content changes. **None of the
eight digested artifacts is touched**, so the eight `sha256:` values at
`wallet-v1.2` still equal the rows recorded at the NAMED CARVE COMMIT — and
therefore still equal the `files:` block of openxFactory's
`contracts/openxwallet-pin.yaml`, which a pin bump to this release moves
`commit:` and `contract_bundle_tag:` in, and NOTHING ELSE. The proof is
mechanical and was run before release: every digest in `contracts/manifest.yaml`
and every digest in that pin's `files:` block recomputes to its recorded value
over this tree. `scripts/validate-openxwallet.py` is in the pin's
`pinned_by_commit_only:` list precisely so a reader change is a COMMIT move and
never a digest move.

Realizes the openXwallet change `add-per-seat-register-entries` (capability
`review-authority-register-reader`, ratified 2026-08-28), through Speckit feature
`specs/014-per-seat-register-entries/`. It also discharges
`add-composition-drift-cascade` task 3.4, which named this reader work as a
successor no delta on that ledger obliged.

### 1. The register's whole top level is read (design D3/D4)

`check_register` enumerated exactly two top-level keys — `register_version` and
`rows` — and IGNORED every other one. So openxFactory's governed
`revocation_staleness_bound: P7D`, added by that repository's ratified task 7.3
and projected verbatim into the Hermes runtime, sat inside a REQUIRED check
unadjudicated (measured on the edited tree: 0 errors, 0 warnings). A governed
declaration a required check parses and never adjudicates is a vacuous pass.

The top-level key set is now CLOSED — `register_version`,
`revocation_staleness_bound`, `rows`, `seat_keys` — and an unrecognized key is
refused (`register-top-level-unknown`). Closing the SET rather than validating
one field is the point: the next declaration added to that file cannot pass
unread without a reader edit. The bound itself is now required and validated
(`register-staleness-bound-missing`, `register-staleness-bound-malformed`) under
hermes-install's own grammar — weeks/days/hours/minutes/seconds, no years or
months, no zero-length window — so a value accepted here is one that repository's
projection schema can carry.

### 2. Per-seat signing keys are recorded and ENFORCED (design D1/D2/D7/D8)

Four Ed25519 keypairs were minted 2026-08-28, one per seat of codexFactory's
`merge_readiness_council`, and the register could not hold their public halves: a
key field on a row fails the nine-field exact set equality, and four per-seat rows
fail the single-row cap. A new unread top-level block would have passed only
because the reader ignored what it did not read — which is why the mint record
named this release instead of writing one.

The register may now carry a top-level `seat_keys:` list. Each entry is exactly
`{seat_id, council_ref, council_id, key_id, public_key, key_fingerprint,
authorizing_row}`, checked as exact set equality the way rows are. Per entry the
reader recomputes the fingerprint from the public key
(`register-seat-fingerprint-mismatch`), pins the public key to 43 characters of
CANONICAL unpadded base64url (`register-seat-key-malformed` — which also refuses a
64-hex PRIVATE seed by shape, the most plausible catastrophic paste into a
governed file), refuses duplicate seat/key/fingerprint
(`register-seat-duplicate`), requires the authorizing row to resolve ACTIVE and
unexpired by COMPUTED time (`register-seat-row-unresolved`), requires
`council_ref` to be that row's `holder_ref` (`register-seat-council-mismatch`),
and requires the register spelling and the runtime spelling to denote one body
(`register-seat-council-spelling`).

Two spellings are recorded on purpose. `council_ref` anchors the authority inside
the register; `council_id` is carried VERBATIM into the Hermes projection, which
keys its seat lookup on the exact pair `(council_id, seat_id)` and spells the
council with underscores. Neither is derivable from the other by a declared rule,
so recording one would force an operator to invent the other at projection time —
and an invented value is a projection that can disagree with the register.

The surface is OPTIONAL and its absence is a NOTE, not a refusal, so every
landing order of the two-repository wave keeps the REQUIRED `wallet-validation`
check green; the note is what keeps that from being leniency. The note on a
populated surface names the number ADJUDICATED out of the number recorded, which
is the line a consumer gate can assert on positively — a count of entries PARSED
would prove parsing and nothing else.

### 3. The single-row cap is re-grounded, not raised

`REGISTER_MVP_SINGLE_ROW` stays `1` and keeps refusing a second AUTHORITY row.
What changed is that the reader now says what the cap binds: one holder, one
target repository, one act, one tier, one expiry. Four keys under one row add
none of those, so recording them completes the ratified first shape rather than
exceeding it. The key surface takes no COUNT bound — a council's seat set is
governed in another repository and a number here would go stale silently — and is
bounded structurally, by every entry descending from a row in the same file.

### What did NOT change

The eight digested contract artifacts (proven above). The corpus: 17 positive
examples and 36 negative confirmations across 13/13 requirements, adjudicated
identically by the previous release — asserted by
`tests/nested_repo_prune::test_the_previous_version_adjudicates_the_corpus_identically`.
No finding code renamed or repurposed; all eleven codes are NEW and all match
`register-[a-z-]+`, so openxFactory's existing negative gate assertion reaches
them with no edit there. No new WARNING anywhere: LedgerxFactory runs this
validator with `--strict`, where warnings red the run.

### Evidence

`python3 scripts/validate-openxwallet.py` (self-test, 0/0);
`python3 scripts/validate-openxwallet.py . --strict` (0/0);
`python3 -m pytest tests/ -q` (69 passed, from 22);
`python3 scripts/verify-contract-pin.py`; `scripts/wallet-yaml-syntax-gate.py .`;
`OPENSPEC_TELEMETRY=0 openspec validate --all --strict`. The four real public
halves were adjudicated against a copy of openxFactory's live register tree
before release: `4 of 4 per-seat signing key(s) adjudicated and resolved`, 0
errors, 0 warnings.

---

## wallet-v1.1 — 2026-08-26 (additive minor; validator behaviour only)

**Change class: ADDITIVE MINOR.** No contract content changes. **None of the
eight digested artifacts is touched, so the eight `sha256:` values at
`wallet-v1.1` still equal the NAMED CARVE COMMIT's rows** — `wallet-v1.0` remains
the byte-identical pure move, and the byte-identity floor is proven against IT.
This release is the ONE auditable diff on top: two behaviours in
`scripts/validate-openxwallet.py`, their tests, and this entry.

Realizes **P2b** (group 4, §4.1–§4.7) of the openxFactory change
`split-openxwallet-repo` (ratified 2026-08-26), designs **D4** and **D3**, under
clarifications **N4** — at openxFactory `f9457d6f`, through Speckit feature
`specs/013-nested-repo-prune-register-note/`.

### 1. The sweep prunes nested repositories (D4, §4.1–§4.2)

`repo_scan` no longer descends into any directory below the scan root that
carries a `.git` entry, **file OR directory**. A consumer pins this validator and
runs it over its own checkout ROOT — it must, because `check_register` joins the
SCAN TARGET with `("governance", "review-authority")`, so any narrower target
silently disables the register read. Before this release that sweep walked into
every nested repository and adjudicated its carried YAML as LIVE RECORDS of the
consumer's tree.

`SKIP_DIR_NAMES` could not close it: the filter is `set(path.parts) &
SKIP_DIR_NAMES`, which matches a path COMPONENT named `.git`, and a submodule
checkout has no such component — its `.git` is a FILE holding a `gitdir:` line.

**The rule is GENERAL, not `SKIP_DIR_NAMES | {"openXwallet"}`** (§4.2).
Hard-coding one consumer's directory name into the product's validator is the
exact coupling that publishing openXwallet separately removes, and it would miss
every other nested repository. As written it also closes the same pre-existing
hole for `installs/omnigent-install`, which openxFactory's sweep walks into
today: on a real openxFactory checkout the prune drops **87 files** out of the
sweep (1683 → 1596 documents read) while the error and warning sets stay
identical. None of those 87 carries a wallet `kind:` today, which is exactly what
makes this a LATENT hazard rather than a live break — and why it closes BEFORE
the consumer gate starts running, not after.

`main()`'s argparse is UNCHANGED (§4.3): there is no `--exclude`, because an
exclusion the caller supplies is one the caller can omit. The packaged-corpus
exclusion still keys on path PARTS and so still holds inside a nested repository
(§4.6). `SKIP_DIR_NAMES` keeps its current behaviour. `Path.rglob` was replaced
by `os.walk` because `rglob` cannot be told to stop descending; the result is
sorted, so adjudication order is unchanged.

### 2. The register read leaves a durable positive line (D3, §4.5)

On a successful read `check_register` now emits ONE note naming the register file
relative to the scan root, with the number of rows read:

```text
note  intake register read: governance/review-authority/register.yaml (1 row(s))
```

Before this the reader was silent on success — the only output naming the
register was a failure finding, and the absent-register note names no path — so
"the register was read" could only be inferred from a conjunction of absences.

**It is an `f.note` and NEVER a warning.** `report()` reds a `--strict` run on
warnings and LedgerxFactory runs `--strict`, so the CLASS of this line is a
compatibility term rather than a presentation choice. The path is RELATIVE
because the consumer gate's positive-proof test asserts on it and an absolute
path differs between a developer's checkout and a CI runner's workspace.

Absent register with no review-class grants keeps the ratified behaviour, byte
for byte: `no intake register at this tree; nothing to read`, and no new note.

### What did NOT change

Zero finding codes added, renamed or removed. Zero existing messages edited.
`--strict` semantics untouched. `main()`'s argparse untouched. Zero bytes of
`contracts/openxwallet/` or `contracts/openxwallet-agent-profile/`. The 17
positives and 36 negatives (32 core + 4 profile) adjudicate identically to
`wallet-v1.0` — proven by running the recovered previous version against this
tree and diffing the error and warning sets, in
`tests/nested_repo_prune/test_prune_and_register_note.py`.

### Evidence

18 new tests in `tests/nested_repo_prune/`, collected by the REQUIRED
`pytest-suite`, plus an end-to-end run of this validator against a real
openxFactory checkout showing both notes and exit 0. The `wallet-v1.1` tag and
its `wallet-v1.1.digests.yaml` over `member_class: owned` members are §4.8, an
operator act that follows the human merge.

---

## wallet-v1.0 — 2026-08-26 (the byte-identical carve; no content change)

**Change class: NONE.** This release changes no contract content whatsoever. It
is the first publication of contracts that already existed, from a new home.

Realizes P2 of the openxFactory change `split-openxwallet-repo` (ratified
2026-08-26, PR #391) through openxFactory Speckit feature
`017-openxwallet-carve`.

**Carved from openxFactory at the NAMED CARVE COMMIT
`30565e48ffe3d8a9773e10af33425701845e10f6`** — recorded in
[`manifest.yaml`](./manifest.yaml)'s `carved_from:`, in
[`../docs/openxwallet-cutover-runbook.md`](../docs/openxwallet-cutover-runbook.md),
and (at P3) in openxFactory's `contracts/openxwallet-pin.yaml`. **Never "HEAD"**,
which is no referent across a multi-pull-request wave — and this wave proved it:
openxFactory's `main` moved to `bb7d7ae8` between the commit being frozen and the
carve being taken, without touching one byte of the twelve carved path sets.

### The twelve path sets, carved with full path history

`contracts/openxwallet/` · `contracts/openxwallet-agent-profile/` ·
`scripts/validate-openxwallet.py` · `scripts/wallet-yaml-syntax-gate.py` ·
`tests/wallet_yaml_syntax_gate/` · `.github/workflows/wallet-validation.yml` ·
`openspec/specs/openxwallet/` · `openspec/specs/openxwallet-agent-profile/` ·
`openspec/changes/archive/2026-08-08-add-openxwallet/` ·
`specs/006-openxwallet-contracts/` · `specs/010-wallet-validator-ci/` ·
`specs/012-wallet-issuer-anchor/`

100 files, 26 commits of real history. `git filter-repo` with one `--path` per
set — **no globs, no `--path-rename`**. A rename of an
`contracts/openxwallet*/examples/` prefix would re-adjudicate 36 intended-invalid
negatives as LIVE records, because the validator's corpus exclusion keys on
`"examples" in path.parts` AND an `openxwallet*` part.

### The byte-identity floor

**All eight digested artifacts carry the sha256 openxFactory recorded at the carve
commit, unchanged.** The full two-part proof — eight recomputed digests, an empty
tree diff over the whole floor, and a two-line-only diff over each promoted spec —
is [`../docs/byte-identity-wallet-v1.0.md`](../docs/byte-identity-wallet-v1.0.md).

Zero renames of `kind:` values, capability ids, finding codes or filenames; zero
corpus edits (R2, LOCKED). LedgerxFactory pins five kinds and several finding-code
strings by name, so a rename inside the move would be unbisectable — and the empty
diff is what makes openxFactory's later atomic consume-and-shed safe to merge at
all.

### The two prose edits, and they are the only ones

Both are outside the floor, which covers `contracts/` BYTES and does not reach
spec prose:

1. `openxFactory SHALL` → `openXwallet SHALL` in the eleven moved requirement
   bodies of `openspec/specs/openxwallet/spec.md` and
   `openspec/specs/openxwallet-agent-profile/spec.md`. A requirement naming the
   wrong repository is not a pure move either.
2. The `## Purpose` placeholder of each promoted spec — *"TBD - created by
   archiving change add-openxwallet. Update Purpose after archive."* — written for
   real. A moved spec whose Purpose names another repository's archiving change is
   not a pure move either.

### What the scaffold added (not carried, and not contract content)

`contracts/manifest.yaml` at `wallet-v1.0`; this changelog; the vendored
`contracts/schemas/hermes-job-envelope.schema.yaml` at its identical
repository-relative path, with `contract_pin.yaml` and
`scripts/verify-contract-pin.py`; `.github/workflows/pytest-suite.yml`;
`.github/CODEOWNERS`; the two runbooks; the byte-identity record; `README.md`,
`CLAUDE.md`, `AGENTS.md`; and `openspec/config.yaml`.

One carved file was edited after the carve, declared here so it is never mistaken
for drift: `.github/workflows/wallet-validation.yml` gained
`python3 scripts/verify-contract-pin.py` as its first run step. The validator
checks only that the vendored schema EXISTS — presence, not identity — while rule
(g) reads the approval-scope vocabulary out of it, so the digest must be verified
before the validator runs. That file is not part of the byte-identity floor.

---

## Inherited history — the two openxFactory bundles that published these contracts

Carried so this repository's history does not begin at its own carve. Both entries
are openxFactory releases; the contracts they describe are the ones above.

### contract-v1.31 — 2026-08-07 (openxFactory; additive; the openxWallet core and its first profile)

Registered the two neutral contract families this repository now owns, realizing
`add-openxwallet` tasks 3.1–3.2 through Speckit feature
`006-openxwallet-contracts`, and modifying no existing capability.

`contracts/openxwallet/` is the HOLDER-AGNOSTIC core — a wallet is a signing key
anchored to a decentralized identifier and held by a person, practitioner,
organisation or agent. Six kinds: the wallet record (a key REFERENCE and a
declared custody model, never key material, with every object closing
`additionalProperties` so no key-shaped field can be added at any depth); the
closed custody registry; the attenuated capability grant (audience, scope, expiry,
parent, narrowing monotonically); the grant exercise record (proof of possession,
key attribution, revocation checked at use, distinct-holder evaluation); the
opt-in distinct-holder constraint; and the subject attestation carrying the
non-substrate rule that preserves MedxFactory's two ratified wallet constraints.

The custody registry is where custody being DECLARED from a closed set and CAPPING
authority becomes contract content rather than an implementation detail.
`evidences` is DERIVED from two declared booleans and enforced, not asserted: a
key readable by the holder's own execution context evidences the ENVIRONMENT, and
only isolation together with an authorization that context cannot supply evidences
the HOLDER. Three invariants make the collapse structurally impossible rather than
discouraged — the derivation itself, a top-of-ladder ceiling that must be earned
(keyed on RANK, not on the tier's name, so renaming the top tier cannot disable
the rule), and a check that no model evidencing only the environment sits at or
above a model evidencing the holder.

`contracts/openxwallet-agent-profile/` is the FIRST profile over that core,
registered as a SIBLING family rather than an extension of it, so patient and
practitioner profiles arrive the same way. Every composition component carries a
`binding_mode`: `content` digests the component itself, while `reference` covers a
corpus's identity and governing configuration but not its row-level contents.
Swapping a corpus or widening retrieval scope changes identity and revokes;
documents arriving in an already-governed corpus do not.

The validator enforces the rules the shapes cannot express and READS the legal
approval-scope vocabulary out of
`contracts/schemas/hermes-job-envelope.schema.yaml` at run time rather than
restating it — restating it would recreate the parallel authority vocabulary the
profile's third requirement forbids. **That read is why this repository vendors
that one openxFactory artifact at a digest pin.** The packaged corpus is 16 valid
examples and 36 intended-invalid negatives (32 in the core family, 4 in the agent
profile) covering 11 of 11 ratified requirements, with coverage closed in both
directions — a requirement with no probe, and a probe naming no requirement, are
both validation failures.

### contract-v1.43 — 2026-08-25 (openxFactory; additive; the issuer anchor)

`contracts/openxwallet/openxwallet-grant.schema.yaml` gained an
`issuer_identifier` def, and `issued_by` moved to it: the issuer grammar is the
identifier grammar plus `@`, so a review-authority root grant can record its
issuer as the responsible OPERATOR's email address, anchored outside the register
under the Human Escalation Contract. Every other identifier field kept the strict
machine-id grammar unchanged (Speckit `012-wallet-issuer-anchor`, S2 of
`add-wallet-carried-review-authority`; convener-authorized schema widening
2026-08-24, with the manifest entry's sha256 refreshed to match).

An earlier additive step (`contract-v1.32`) widened
`openxwallet-record.schema.yaml`'s `signature_algorithm` with `rsa-2048-sha256`
and `rsa-3072-sha256`, measured against BC 28.3 AL by the first consumer; that
fold left the digest itself unchanged.
