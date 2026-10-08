---
code_surface: NINE repositories named — THREE of them NEW — and FIVE of the nine change. (1)-(3) the openWallet PROJECT, NEW: THREE PUBLIC repositories in the openRepoShape three-leg shape (RULED Q3 "Three-leg shape at birth", Q5 "Public"), each receiving its path sets by a byte-identical PATH CARVE from this repository at a NAMED CARVE COMMIT (never HEAD; named 2026-10-08, task 2.3: `90111df262d6f54f7e82651d860adc12345f83f4`) with every repository-relative path unchanged — the ASSEMBLY ROOT `opensoft/openWallet` (`project.yaml` with `elected_by: "Brett Heap"`, `elected_on: 2026-10-08`, topic `xf-project-openwallet`; the leg pins and the shape's `validate` gate; and the release identity, `contracts/manifest.yaml`, `contracts/CHANGELOG.md`, `contracts/releases/` and the `wallet-v*` tag); the SPEC leg `opensoft/openWallet-spec` (the promoted capabilities `openxwallet` and `openxwallet-agent-profile`, the archive records of `add-openxwallet` and `add-multi-key-wallets`, the active `add-composition-drift-cascade`, Speckit 006, 010 and 015, and an OpenSpec gate of its own, vendored for the leg rather than carved, which commits the content-addressed 1.12.0 tarball and installs from it offline — RULED "Vendor the tarball (Recommended)" for that leg, as this repository's gate was ruled for this one); the CODE leg `opensoft/openWallet-code` (RULED Q7 "Code leg, declared override (Recommended)": both contract families with the eight digested artifacts at unchanged sha256, the packaged corpus less the three issuer-anchor negatives, the syntax gate, the CORE validator `scripts/validate-openxwallet.py` with a DECLARED and ENUMERATED diff, the moved tests, and the `wallet-validation` and `pytest-suite` checks). (4) openXwallet, THIS repository — rebuilt as the openxFactory ADAPTER: a nested `openWallet/` gitlink mounting openWallet's ASSEMBLY ROOT (its `code/` leg initialized one level deeper) plus `contracts/openwallet-pin.yaml` and its verifier; `scripts/validate-openxwallet.py` recomposed over the pinned core at `openWallet/code/scripts/validate-openxwallet.py` with rule (t), the register reader and the hermes vocabulary binding as adapter rules; `scripts/wallet-yaml-syntax-gate.py` kept as an entrypoint; the carved paths shed; `contracts/manifest.yaml`, `contracts/CHANGELOG.md`, `README.md`, `AGENTS.md`, `.github/CODEOWNERS` and `.github/workflows/` updated. It KEEPS `contract_pin.yaml`, the vendored `contracts/schemas/hermes-job-envelope.schema.yaml`, capability `review-authority-register-reader`, Speckit 012, 013 and 014, and the change `widen-register-reader-for-a-second-council`. (5) openxFactory — `contracts/openxwallet-pin.yaml` `files:` and `pinned_by_commit_only:` re-pathed ONCE under `openWallet/code/` plus one pin bump; `.github/workflows/openxwallet-consumer-gate.yml`'s scoped init extended two levels (`openXwallet/openWallet`, then its `code` leg); `scripts/verify-openxwallet-pin.py` gains nested-checkout parity through both levels; `scripts/validate-trust-anchor.py`'s `OPENXWALLET_REGISTRY_PATH` literal and the test holding it; the gate's LITERAL assertions do NOT move. (6) LedgerxWallet — nothing on day one; a two-level nested init on its next pin bump. (7) LedgerxFactory — its estate run's checkout initializes two levels deeper; its finder's candidate paths are unchanged. (8) codexFactory and (9) the xFactory aggregation — no change expected under Q2's ruling (the floor already protects the `openXwallet` gitlink through which openWallet is reached), VERIFIED at realization rather than assumed. Per `release-realization` this change archives ONLY on merged, green realization evidence across that surface.
target_release: unallocated. Two release identities follow at realization — openWallet's first release, an annotated `wallet-v*` tag on the openWallet ASSEMBLY ROOT (series RULED Q4; root placement following openDox, `design.md` D7), and openXwallet's first adapter release in its own series — and per AGENTS.md rule 6 each is five coordinated values (per-file `contract_schema_version`, `contract_bundle_version`, an annotated tag, the exact release commit with per-file digests, and the `contracts/CHANGELOG.md` entry), allocated at realization and never reserved in a proposal. The eight digested artifacts are expected to keep their sha256 exactly, so no per-file `contract_schema_version` is expected to move.
Status: ratified
archive_after: [add-multi-key-wallets]
Ratified: 2026-10-08T17:10:47Z by Brett Heap (operator authority) — in-session
  ruling, verbatim: "ratify 26 and merge"; head
  `2ae4eee1885536297e5653e64b6abb1b85cc8e9e`.
  Ruling: https://github.com/opensoft/openXwallet/pull/26#issuecomment-6065121015
  Prefix: KEPT — "keep the prefix" (2026-10-08).
  Q1 (2026-10-08T16:30:50Z): "In-process, extension points (Recommended)".
  Q2 (2026-10-08T16:30:50Z): "Nested gitlink, one chain (Recommended)".
  Q3 (2026-10-08T16:30:50Z): "Three-leg shape at birth", against its
    recommendation.
  Q4 (2026-10-08T16:30:50Z): "openWallet continues wallet-v* (Recommended)".
  Q5 (2026-10-08T16:30:50Z): "Public (Recommended)".
  Q6 (2026-10-08T16:30:50Z): "Document plus pointer, fail closed (Recommended)".
  Q7 (2026-10-08T17:01:43Z): "Code leg, declared override (Recommended)".
  Spec-leg OpenSpec gate, tasks.md 3.6 (2026-10-08T17:01:43Z):
    "Vendor the tarball (Recommended)".
  Codex review did not run on this head (the connector reported its usage limit
  reached), so the merge proceeds on the operator's word with the five required
  checks green.
---

# Proposal: split-openwallet-neutral-core

Lane: openXwallet-2

**Status: ratified by Brett Heap (openXwallet operator authority), in session,
2026-10-08T17:10:47Z, verbatim: "ratify 26 and merge". This packet still
performs nothing.** Ratification authorizes the successor groups in `tasks.md`
and performs none of them: no repository is created, no byte is carved, no
validator line moves, no pin advances. It ratifies the change as authored at
head `2ae4eee1885536297e5653e64b6abb1b85cc8e9e`, including the NINE
rulings it carries as constraints, all of 2026-10-08: "keep the prefix"; Q1–Q6,
by multiple choice (recorded at 2026-10-08T16:30:50Z), of which Q3 overrode its
recommendation and reshaped the packet; and Q7 with the spec leg's
OpenSpec-gate question, by multiple choice (recorded at 2026-10-08T17:01:43Z).
Every other position the packet takes is ratified with it, as proposed, and the
ratification changes no delta. Ruling:
https://github.com/opensoft/openXwallet/pull/26#issuecomment-6065121015

## The decision being governed

Brett Heap (operator authority), in session, 2026-10-08, verbatim:

> consider if we make openWallet as a standalone neutral wallet system that does
> not need openXfactory. then we make openXwallet as the adapter layer for
> neutral contracts for openXfactory and then the actual wallets are the domain
> wallets like medXwallet and ledgerXwallet. this then matches our openDox
> project and openAvatar. we can keep all our projects able to run stand alone
> but tuned version that run with our xFactories.

> write the openspec proposal for the split, keep the prefix

That is a three-layer split:

| Layer | Repository | Owns | Needs openxFactory |
|---|---|---|---|
| Neutral standard | the openWallet PROJECT (NEW, three-leg, public): root `opensoft/openWallet`, `opensoft/openWallet-spec`, `opensoft/openWallet-code` | both contract families and the eight digested artifacts, the corpus, the syntax gate, the core validator (code leg); capabilities `openxwallet` and `openxwallet-agent-profile`, Speckit 006/010/015 (spec leg); the release identity (root) | **no** — no vendored artifact, no operator identity, no register |
| Factory adapter | `opensoft/openXwallet` (this repository) | the pin of openWallet, the hermes vocabulary binding (`contract_pin.yaml` + the vendored envelope), rule (t), the register reader, capabilities `review-authority-register-reader` and `openxwallet-factory-binding` (NEW), Speckit 012/013/014 | yes, by design |
| Domain wallets | `LedgerxWallet` today; `MedxWallet` and the rest on their first profile | profiles, never forks | through the adapter inside a factory, or not at all when pinning openWallet standalone |

A "tuned" variant is a PIN TARGET — which layer a descendant pins — and never a
fork.

## Ruled — the prefix is kept

Brett's word, verbatim: **"keep the prefix"**. Its scope, as relayed by the
orchestrating session that took the ruling: **the `xfactory_wallet_*` kind
prefix, every finding code, and the existing schema `$id` namespace
(`https://xforge.us/schemas/openxfactory/openxwallet/v1/…` and
`…/openxwallet-agent-profile/v1/…`) are KEPT unchanged in the carve; the rename
to a neutral prefix stays deferred to a future wallet MAJOR and is out of
scope.** This packet encodes that and does not re-open it.

What follows from it is construction, not further ruling: the seven kinds and
the `$id`s sit INSIDE the eight digested artifacts' bytes, so keeping them is
what lets every digest survive the carve. The packet PROPOSES the same treatment
for three neighbours the ruling does not name — the schema-document kind
`openxfactory-openxwallet-contract-schema` (also inside the digested bytes), the
manifest's `compatibility: canonical_openxfactory_contract` and
`adapter_owner: openxFactory` fields (carried verbatim, as the `wallet-v1.0`
manifest comment already promised: "revisited by a later change in this
repository, never by the carve"), and the filenames and capability ids AGENTS.md
rule 2 pins by name.

## Why

### The wallet collapses two layers the house keeps apart

openxFactory's doctrine, `docs/project-repo-schema.md`: the 2026-09-02 ruling
*"Descendant only if it pins open<Product>."* (`:86-90`), and its 2026-09-05
amendment, Brett Heap verbatim *"elect the shape for both, follow the pin chain,
no family yet"* (`:109-131`) — a `<Domainx><Product>` classifies as a descendant
where its declared neutral-product pins REACH `open<Product>` through a chain of
declared pins, as `codexDox` declares `openXdox` whose manifest declares
`openDox`. openDox/openXdox is that chain (openxFactory
`split-opendox-two-layer-product`); openAvatar is the standalone neutral
product. **The wallet has no `open<Product>` at the bottom of its chain**:
openXwallet is the neutral standard and the factory-tuned layer at once, so
`LedgerxWallet` descends from a repository that is half openxFactory adapter.

### Measured at `b7c6e0b`: the neutral core is non-neutral in exactly two places

1. **An organisation's operator identity sits inside the core grant check.**
   Rule (t), `scripts/validate-openxwallet.py:986-1032`, inside `check_grant` —
   the function every grant in every consumer passes through — refuses a root
   REVIEW-class grant unless `issued_by` equals `ROOT_ISSUER_OPERATOR_TOKEN =
   "Brett.Heap@opensoft.one"` (`:274`), citing
   `ISSUER_ANCHOR_AUTHORITY = "docs/roles-and-authority.md:103-140"` (`:275`), a
   path that exists only in openxFactory. It implements openxFactory's
   `review-authority-intake` requirement *Every review-authority grant names its
   issuer, and a root grant's issuer is anchored outside the register* (ADDED by
   openxFactory's active `add-wallet-carried-review-authority`) through this
   repository's Speckit 012. **No requirement promoted HERE names it**: its three
   negatives attribute to `OXWR-R1`/`OXWR-R2` (`:323-328`), rows with no heading
   in `openspec/specs/` — the drift `add-composition-drift-cascade`'s design
   already logged.
2. **The vocabulary runs envelope → wallet.** `ENVELOPE_SCHEMA_PATH` (`:254`)
   names openxFactory's hermes job envelope; `approval_policy_vocabulary()`
   (`:422-428`) reads the legal approval-posture keys out of it; `main()` exits 2
   when it is absent (`:3498-3503`). The promoted requirement *Agent authority is
   grant scope, not a parallel vocabulary* states the same direction in its text.

Beside those, one factory SURFACE lives here whole: the register reader
(`:2561-3326`) and its self-test (`:2036-2558`) read
`governance/review-authority/register.yaml`, which exists only in openxFactory —
this repository's own scan says `no intake register at this tree; nothing to
read`. The reader's capability Purpose calls it "the reader-side half of
openxFactory's `review-authority-intake`".

### What that costs, and why the split is cheap now

A product outside the factory — openChart, openPractice, the vault and
secret-distribution control plane — cannot run the wallet standard without
vendoring an openxFactory artifact, inheriting an openxFactory operator's e-mail
as a hard-coded root issuer, and carrying a reader for a register it will never
hold.

The coupling is narrow. `Context(registry, vocabulary)` (`:621-625`) already
takes the vocabulary as a dict, so the core's only tie to the envelope is one
file read plus `main()`. Rule (t) is one block; the register reader is one
contiguous block reached from one call in `repo_scan` (`:3464-3465`). And the
syntax gate already imports the hyphenated validator as a library by `importlib`
path-load (`scripts/wallet-yaml-syntax-gate.py:52-66`), so in-process composition
has an in-tree precedent.

## What Changes

### What this packet ratifies — its own diff

Only `openspec/changes/split-openwallet-neutral-core/`. Three spec deltas:

- **REMOVED — `openxwallet`, all eight requirements**, successor recorded:
  the openWallet project's spec leg `opensoft/openWallet-spec`, capability
  `openxwallet` (the id kept).
- **REMOVED — `openxwallet-agent-profile`, all three**, successor recorded. One
  successor text differs: *Agent authority is grant scope, not a parallel
  vocabulary* flips from "admits the neutral job envelope's values" to "admits
  the keys of ONE DECLARED VOCABULARY BINDING; absent a binding, a posture is
  refused" — authored in openWallet's own birth change, substance drafted in
  `design.md` D8 so it is ratified here.
- **ADDED — NEW capability `openxwallet-factory-binding`**, five requirements:
  (i) openWallet is pinned by commit and digest, declared twice, and composed in
  process with entrypoint, codes and check token unchanged; (ii) the approval
  vocabulary is bound to the hermes envelope from the digest-verified vendored
  copy; (iii) the root-issuer operator anchor and its negatives live in the
  adapter; (iv) kinds, codes and `$id`s are the pinned openWallet's, unchanged —
  the prefix is kept; (v) a consumer reaches openWallet through openXwallet's
  declared pin, and a direct pin suffices standalone.
- **`review-authority-register-reader` — NO delta.** None of its three
  requirements names the core or the envelope, and the program its Purpose names
  (`scripts/validate-openxwallet.py`, `check_register`) stays here.

Eleven requirements leave, five arrive, three stay: after archive this
repository promotes eight requirements in two capabilities and openWallet eleven
in two.

### What it authorizes as successors, each its own Speckit feature

OpenSpec ratifies the boundary; Speckit builds it. In `design.md`'s migration
order: archive `add-multi-key-wallets` and reflow the promoted specs' wrapped
scenario lines; openWallet's birth as three public repositories; the carve into
its three legs and its path-mapping proof; openWallet's declared edits;
openWallet's first release; the adapter
rebuild here; the adapter's first release; openxFactory's re-path and bump;
consumer notices; the archive. The declared validator diff in openWallet is
ENUMERATED in advance, so the proof can fail against it:

| | Hunk | Lines at `b7c6e0b` |
|---|---|---|
| (a) | remove the envelope: `ENVELOPE_SCHEMA_PATH`, the hard exit, the vocabulary note | `:254`, `:3498-3503`, `:3529-3530` |
| (b) | take the vocabulary from ONE DECLARED BINDING the caller supplies; absence binds the empty set, so every `approval_posture` key is refused under the EXISTING code `authority-vocabulary-parallel`, with a NOTE saying why; the packaged corpus is adjudicated under a declared corpus binding (Q6) | `:422-428`, `:3507`, docstring `:73-78` |
| (c) | move rule (t) OUT — constants, check, requirement rows, self-test probes, three negatives, docstring | `:256-283`, `:986-1032`, `:323-328`, `:1789-1974`, docstring `:172-181` |
| (d) | move the register reader OUT — the block, its call, its self-test, docstring | `:2561-3326`, `:3464-3465`, `:2036-2558`, docstring `:183-212` |
| (e) | add the declared, EMPTY-by-default extension points the adapter registers into, at the exact positions (c) and (d) vacate (Q1) | the same positions |

Every changed line lands in openWallet's byte-identity proof by hunk, as
`wallet-v1.0` enumerated its two prose classes. The three-leg shape adds NO hunk:
the validator, the contracts and the tests land in one leg with today's layout
(`design.md` D7; RULED Q7).

### Kept, by ruling or by construction

The seven `xfactory_wallet_*` kinds, every finding code, every `$id` (ruled); the
eight sha256s (by construction); openXwallet's entrypoint
`scripts/validate-openxwallet.py` with its one positional target and `--strict`,
its `validate-openxwallet: N error(s), M warning(s)` summary, and the
`wallet-validation` check token, all of which openxFactory's REQUIRED gate and
LedgerxFactory's estate run pin by string; `contract_pin.yaml` and the vendored
envelope, which stay HERE.

## What this does NOT do

- **No rename** of a kind, finding code, `$id`, filename or capability id —
  RULED. The neutral-prefix rename is a future wallet MAJOR.
- **No runtime** — no issuer, key store or custody host.
- **No new contract content and no digest move.** No schema, kind or field is
  authored. The one new file openWallet's corpus gains is a corpus binding
  (Q6) — teaching data under `examples/`, never a contract member.
- **No new finding code.** An absent binding reuses `authority-vocabulary-parallel`.
- **No change to the register**, its path, its codexFactory floor entry, or
  `review-authority-register-reader`'s requirement text.
- **It does not realize `add-composition-drift-cascade`.** That change travels to
  openWallet's spec leg and is realized in the openWallet project.
- **It does not decide domain-wallet content** — `LedgerxWallet`'s profile line
  stays with openxFactory's `create-ledgerxwallet-overlay-boundary`.

## How this answers the precedent's carried Q1 and Q3

openxFactory's archived `split-openxwallet-repo` carried five questions; this
split answers two.

**Q1 — "Should the review-authority register be promoted to a wallet primitive,
or should the reader be split back into openxFactory?"** Neither. The split
creates a third home that did not exist when Q1 was asked: the ADAPTER layer.
The reader is not a wallet primitive — it enforces an openxFactory register and
travels with an organisation's operator anchor, so openWallet carries neither —
and it is not split back into openxFactory, because it stays a pinned tool whose
digest says "which reader ran", the property the precedent valued, invoked by an
openxFactory command that does not change. The precedent's lean (promote the
register "once a second consumer of authority registers exists") is not
followed; that trigger has not fired, and the register is still openxFactory's
alone.

**Q3 — "What is the deprecation window for renaming the kind prefix
`xfactory_wallet_*` to `openxwallet_*`?"** RULED today: the prefix is KEPT
through this split and the rename stays a future wallet MAJOR. The dual-accept
window that packet recommended belongs to that future change's design. Its price
grows by one hop, stated now rather than discovered: a rename would be an
openWallet MAJOR, an openXwallet re-pin, an openxFactory pin bump and a
LedgerxWallet re-pin.

## Sequencing with the three active changes

- **`add-multi-key-wallets` ARCHIVES BEFORE THE CARVE** (`archive_after:` above).
  Realized at `wallet-v1.3` with its evidence recorded in its own `tasks.md`, it
  is unarchived, so its four MODIFIED requirements are not yet promoted text. If
  it archived after the carve, its archive would land in the wrong repository.
  It carries no `.openspec.yaml`; recorded, not fixed here.
- **`add-composition-drift-cascade` TRAVELS to openWallet's spec leg.** Ratified
  2026-08-28 and unrealized; its declared surface — a cascade rule in the core
  validator and two core/profile deltas — is openWallet territory. Two
  obligations travel with it, as openWallet's first open item after the carve and
  a precondition of nothing here: the KNOWN collision with `add-multi-key-wallets`
  on *Revocation propagates through the chain* (two MODIFIED texts, not
  byte-identical, named by Q-WRR-4 and never fixed) must be rebased onto the text
  promoted by multi-key's archive — on the pinned 1.12.0 its archive ABORTS until
  then, MEASURED: "current spec contains scenario(s) not present in the modified
  block: 'retiring one key does not revoke the wallet'" (Q-WRR-4 assumed a silent
  overwrite; the pinned CLI refuses instead); and its deltas take the same
  subject rewrite as the moved requirements.
- **`widen-register-reader-for-a-second-council` STAYS**, independent of this
  change; its own archive gate is unchanged.
- **This change archives LAST**, after `add-composition-drift-cascade` has left
  this repository: this change RETIRES the spec that change modifies, and on the
  pinned 1.12.0 a MODIFIED delta against a retired spec aborts — MEASURED:
  "target spec does not exist; only ADDED requirements are allowed for new
  specs". Two further archive preconditions were MEASURED on 1.12.0 in a scratch
  copy and are carried, not discovered later: the change declares
  `retire_capabilities: true` (in `.openspec.yaml` now), and the seven wrapped
  scenario-bullet lines the promoted `openxwallet` spec holds after multi-key's
  archive are reflowed onto their bullets first, because the retirement guard
  refuses lines it cannot account for. With both, the archive applies +5 / −11
  and retires both specs.

## Questions — Q1–Q7 and the spec leg's gate, all RULED 2026-10-08

Brett Heap (operator authority) ruled Q1–Q6 in session on 2026-10-08, by
multiple choice; Q3's ruling raised Q7 and the spec leg's OpenSpec-gate
question, and he ruled both later the same day, by multiple choice. **The
change itself was ratified separately, on 2026-10-08T17:10:47Z ("ratify 26 and
merge")** — see the front-matter `Ratified:` block. Each label is quoted verbatim; the recommendation each question carried is kept
below it as the rationale on record.

### Q1 — How does openXwallet compose the pinned openWallet validator?

**RULED — "In-process, extension points (Recommended)"**, as recommended.
Recorded at 2026-10-08T16:30:50Z; taken in session minutes earlier by multiple choice.

*Rationale on record:* in process, as a library, loaded by `importlib`
path-load exactly as the syntax gate already loads it; ONE scan `Context`
shared by both layers; the adapter's rules registered into declared extension
points AT THE POSITIONS THEIR CODE OCCUPIES TODAY — rule (t) inside
`check_grant`, the register reader where `repo_scan` calls it, their self-test
probes where the self-test runs them, `OXWR-R1`/`OXWR-R2` and their three
negatives inside the core's own per-requirement closure. The core never imports
the adapter, and the adapter never suppresses or reorders a core finding. That
buys MECHANICAL neutrality — on any tree the composed run's output is
byte-identical to today's validator's — so openxFactory's pin bump is proven
neutral by a plain `diff` (the widen packet's D6 standard) and its gate
assertions do not move. `design.md` D5.

### Q2 — How does openWallet arrive here, and what does openxFactory re-path?

**RULED — "Nested gitlink, one chain (Recommended)"**, as recommended.
Recorded at 2026-10-08T16:30:50Z; taken in session minutes earlier by multiple choice.

*Rationale on record, read through Q3's ruling:* a nested submodule gitlink
`openWallet/` — which, under Q3, mounts openWallet's ASSEMBLY ROOT — plus
`contracts/openwallet-pin.yaml`, declared twice in the same commit:
`revision_kind: commit`, the root's commit, the code-leg commit that root pins
held in LOCKSTEP, per-file sha256 for the eight digested artifacts at
`code/contracts/…`, and `pinned_by_commit_only:` for the rest. The double
declaration mirrors how `LedgerxWallet` pins openXwallet; the field grammar is
openxFactory's wallet pin's, `kind: pinned_contract_manifest`. **No mirror copy
of any openWallet contract.** openXwallet keeps BOTH consumer entrypoints — the
validator and the syntax gate — at their paths. openxFactory re-paths its pin's
`files:` ONCE, to `openWallet/code/contracts/…` under its existing
`submodule_path: openXwallet`; its commit and digests stay authoritative, and it
reaches openWallet's commit through openXwallet's pin — ONE chain. In-family
domain wallets pin openXwallet; a standalone product pins openWallet directly; a
repository that declared both would hold them equal by a running lockstep check,
as openxFactory does for openDox since Brett's 2026-09-10 Q7 ruling superseded
RULING F for openDox. `design.md` D6.

### Q3 — One repository, or the three-leg shape?

**RULED — "Three-leg shape at birth"** — AGAINST the recommendation.
Recorded at 2026-10-08T16:30:50Z; taken in session minutes earlier by multiple choice.

**The ruling overrides the recommendation, and this packet is rewritten to it.**
openWallet elects the openRepoShape three-leg shape AT CREATION, as openDox did:
an assembly root `opensoft/openWallet` with a spec leg `opensoft/openWallet-spec`
and a code leg `opensoft/openWallet-code`. What it changes, each worked in
`design.md` D7:

- **Three repositories, not one**, each created PUBLIC (Q5), with the project's
  `project.yaml` recording `elected_by: "Brett Heap"`, `elected_on: 2026-10-08`
  and topic `xf-project-openwallet`. Scaffolding into `opensoft` is openRepoShape's
  own namespace and needs `--allow-upstream-org`, an operator act.
- **Every carved path set gets a declared leg** (PROPOSED in D7; the contracts'
  leg RULED by Q7). The validator, the syntax gate, the moved tests and their
  workflows land in the CODE leg, with the contracts, as Q7 ruled; the
  promoted specs, the archive records, the travelling change and Speckit
  006/010/015 in the SPEC leg; the release identity at the ROOT.
- **The proof becomes a DECLARED PATH MAPPING**, and it stays byte-identical:
  within each leg every carved path keeps its repository-relative path, so the
  carve is still a pure copy per leg and the eight digests are unchanged. What a
  consumer sees gains one prefix, `openWallet/code/`.
- **The validator diff does NOT grow** — Q7's ruling keeps it so. Contracts
  and scripts land in the same leg with today's layout, so `ROOT = parents[1]`
  resolves to the code leg and hunks (a)–(e) remain the whole diff.
- **openWallet's own required checks run per leg**: `wallet-validation` and
  `pytest-suite` from the code leg's own root, the OpenSpec gate in the spec
  leg, the shape's `validate` at the root. A wallet-validator run from the
  assembly root prunes both legs and scans nothing — measured, D7.
- **Consumers initialize the code leg too**: openXwallet initializes `openWallet`
  then `openWallet/code`; openxFactory initializes three named levels from
  `openXwallet` down, never `--recursive`, and never the spec leg (D6).

*The recommendation it overrides, on record:* one repository for the carve,
because the proof is path-based. That estimate was too pessimistic: per leg the
paths do not move, so the shape costs a mapping and a prefix, not the identity
property.

### Q4 — Which repository continues the `wallet-v*` series?

**RULED — "openWallet continues wallet-v* (Recommended)"**, as recommended.
Recorded at 2026-10-08T16:30:50Z; taken in session minutes earlier by multiple choice.

*Rationale on record:* openWallet owns the eight digested artifacts, and
`contracts/releases/wallet-v1.0…v1.5.digests.yaml` travel with them;
openXwallet starts its own adapter series (spelled at its first release, for
example `xwallet-v*`). For every consumer the commit and sha256 are
authoritative and the tag is a label. **No number is allocated.** *Placement
under the shape (declared here, following openDox):* the annotated `wallet-v*`
tag, `contracts/manifest.yaml`, `contracts/CHANGELOG.md` and
`contracts/releases/` sit at the openWallet ASSEMBLY ROOT — the one commit that
names both legs, and the commit openXwallet pins — while the eight artifacts and
their per-file `contract_schema_version` sit in the code leg. `design.md` D7.

### Q5 — Is openWallet public or private?

**RULED — "Public (Recommended)"** — public at creation, all three repositories
of the project. Recorded at 2026-10-08T16:30:50Z; taken in session minutes earlier by multiple choice.

*Consequence on record:* openXwallet is already PUBLIC and openxFactory's
consumer gate retired its app-token mint on that ground (its header records the
flip at 2026-09-07T15:24:11Z and the retirement on 2026-09-11); a public
openWallet keeps every CI that initializes it token-free. `LedgerxWallet` stays
PRIVATE and is unaffected.

### Q6 — The vocabulary binding's declared form

**RULED — "Document plus pointer, fail closed (Recommended)"**, as recommended.
Recorded at 2026-10-08T16:30:50Z; taken in session minutes earlier by multiple choice.

*Rationale on record:* a binding is a document path plus a pointer to a mapping
whose KEYS are the legal posture terms; openXwallet binds the exact node read
today (`properties.job.properties.approval_policy.properties` of the vendored
envelope), unconditionally, with no flag a caller can omit. That meets the
precedent's LOCKED R4, which rejected "making rule (g)'s vocabulary a CLI
parameter with no default, which silently weakens the gate": here absence
REFUSES rather than admits. openWallet's packaged corpus — five positives and
three negatives carry `approval_posture` — is adjudicated under a declared
corpus binding naming the three keys those fixtures use, for layer 1 only and
never for a repo scan. Rule (h) and the posture limb of rule (f) name those
three keys literally (`:1106-1128`, `:1148-1161`); they stay in the carve —
inert under any binding that does not admit them, because rule (g) refuses an
unbound key first — and their neutral re-expression joins the deferred prefix
MAJOR. `design.md` D4.

### Q7 — Which leg holds the two contract families? (raised by Q3's ruling)

**RULED — "Code leg, declared override (Recommended)"**, as recommended.
Recorded at 2026-10-08T17:01:43Z; taken in session minutes earlier by multiple choice.

Contracts, corpus and validator stay together in `opensoft/openWallet-code` at
today's repository-relative paths. The override of openRepoShape's
`spec-governance` default is DECLARED in the carve manifest
(`docs/openwallet-carve-manifest.yaml`, `design.md` D7), on every row it
governs.

*Rationale on record:* Q3's ruling raised a question the six did not: openRepoShape places contracts
in the SPEC leg. Its pinned `AGENTS-shape.md` says "A contract the code READS
but does not OWN lives in the SPEC leg" (ruled and measured on MedxEHR, whose
tooling then took `CONTRACTS_DIR` from the environment), and its default
`contracts/path-classification.yaml` rule `spec-governance` sends
`contracts/**` to the spec leg. The nearest precedent agrees with that
default: openxFactory's `docs/opendox-carve-manifest.yaml` sent openDox's
neutral contract schemas (3 rows) and their examples (52 rows) to
`opendox_spec`, and its scripts (78) and tests (45) to `opendox_code`.

**The recommendation it followed: the CODE leg, declared as an override of that
default.** The validator resolves every contract path from its own location
(`:249-253`), its corpus exclusion keys on the `examples` path parts, and the
code leg's tests resolve the corpus as `REPO_ROOT / "contracts" / …` beside
`scripts/` (`tests/multi_key_wallets/test_declared_key_sets.py:32-34`) or build
fixture trees with `contracts/` beside it
(`tests/nested_repo_prune/test_prune_and_register_note.py:230`). The packaged
corpus is the validator's own self-test fixture set, and the schemas, the
corpus and their conformance validator are ONE release unit. In the code leg
they need no edit beyond hunks (a)–(e), and one checkout serves the leg's own
CI and every consumer. **The spec-leg alternative is costed, not dismissed:** a
sixth validator hunk (`CONTRACTS_DIR` across the root mount), edits to every
`relative_to(ROOT)` label and to the tests' fixture builders, a code-leg CI
that must also fetch the spec leg, consumers initializing both legs, and
openxFactory's pin split across `openWallet/spec/…` and `openWallet/code/…`.

### The spec leg's OpenSpec gate (`tasks.md` 3.6) — raised by Q3's ruling

**RULED — "Vendor the tarball (Recommended)"**, as recommended.
Recorded at 2026-10-08T17:01:43Z; taken in session minutes earlier by multiple choice.

`opensoft/openWallet-spec` commits the content-addressed
`@fission-ai/openspec@1.12.0` tarball and its gate installs from it OFFLINE —
the same shape as this repository's `.github/workflows/openspec-cli-pin-gate.yml`
under the 2026-09-07 ruling ("Vendor the tarball into the repo", taken for this
repository's AGENTS.md rule 4, "Every gate is offline"). The ruling is the spec
leg's own, recorded in that leg's `AGENTS.md` — the same per-repository pattern,
never this repository's ruling stretched to another.

*Rationale* (this packet had written no recommendation for this question before
the ruling; the reading below is the packet's): an online install makes the
archive gate depend on the
registry at run time, which the offline-gate rule refuses here; the content
address (`integrity` in `contracts/openspec-cli-pin.yaml`) is the trusted
referent either way, so vendoring changes where the bytes come from and not
which bytes are trusted. The gate is CI tooling in the spec leg, outside every
byte a consumer pins or runs, so it does not touch the neutral standard's
no-openxFactory-input boundary (`design.md` D7).

## Impact

- **openWallet (NEW, three repositories)** — scaffolded public by openRepoShape,
  carved leg by leg, proven by a declared path mapping, given a required check
  and a ruleset in each repository, and released from its root; its code leg
  holds the contracts (RULED Q7); its spec leg runs its own offline OpenSpec
  gate (RULED) and inherits the active `add-composition-drift-cascade`.
- **openXwallet** — becomes the adapter: three capabilities' worth of neutral
  content leaves; the entrypoints, the check token, the register reader and the
  hermes binding stay. Its README, AGENTS.md and manifest are rewritten for the
  role.
- **openxFactory** — one pull request: the pin re-path to `openWallet/code/…`
  and the bump, the consumer gate's scoped init two levels deeper, nested-checkout
  parity through both levels in `scripts/verify-openxwallet-pin.py`, the
  trust-anchor registry literal (`scripts/validate-trust-anchor.py:348-350`,
  becoming `openXwallet/openWallet/code/contracts/openxwallet/…`) and
  `tests/trust-anchor/test_openxwallet_pin_refusal.py`; and
  `tests/openxwallet_consumer_gate/test_gate_invocation.py`, which pins the
  scoped-init line verbatim (`:47`). Its gate literals (`8 of 8`, the five-key
  wallet note, `repo scan:`) do NOT move, which is the neutrality Q1 buys.
- **LedgerxWallet** — nothing on day one (it pins openXwallet at `wallet-v1.1`);
  initializes `openXwallet/openWallet` and its `code` leg on its next bump; may
  later pin openWallet directly instead, per Q2.
- **LedgerxFactory** — its estate run invokes
  `openxFactory/openXwallet/scripts/validate-openxwallet.py --strict` and parses
  `repo scan:` (as the precedent measured it; not checked out here, re-measured
  at realization); both survive, and its checkout must initialize two levels
  deeper.
- **codexFactory** — none expected: `scripts/merge_master/openxfactory_floor.py`
  already floors the `openXwallet` gitlink as a protected root file, and under
  Q2 openxFactory gains no second wallet gitlink. A direct openWallet mount would
  need a second floor entry. Verified at realization.
- **xFactory aggregation** — none expected under Q2. A root `openWallet` gitlink,
  if ever added, owes root-gitlink parity against the commit openXwallet's pin
  records.
- **Standalone open products** — openChart, openPractice and the planned vault
  control plane can pin openWallet and inherit no factory rule. That is the point
  of the split.

## Status

`Status: ratified`. **Ratified by Brett Heap (openXwallet operator authority),
in session, 2026-10-08T17:10:47Z, verbatim: "ratify 26 and merge"** — the change
as authored at head `2ae4eee1885536297e5653e64b6abb1b85cc8e9e`. The first
clause ratifies this change on PR #26; the second authorizes the merge of that
pull request into `main`, which this record does not perform. Ratified with it
are the rulings already encoded beside their questions: "keep the prefix"
(2026-10-08); Q1–Q6 (2026-10-08, by multiple choice, recorded at
2026-10-08T16:30:50Z); and Q7 and the spec leg's OpenSpec-gate question
(2026-10-08, by multiple choice, recorded at 2026-10-08T17:01:43Z). No question
is pending. The ratification changes no delta: moving this status from proposed
to ratified is a bookkeeping act on the same branch.

Codex review did not run on this head — the connector reported its usage limit
reached — so the merge proceeds on the operator's word with the five required
checks green.

**Ratification of the change authorizes the successor groups in `tasks.md` and
performs none of them.** Nothing from §2 on is done by it: no repository is
created, no byte is carved, no validator line moves, no pin advances.

Full ruling:
https://github.com/opensoft/openXwallet/pull/26#issuecomment-6065121015
