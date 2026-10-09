# openXwallet

**The openxFactory adapter over the neutral wallet standard.** A wallet is a
signing key anchored to a decentralized identifier and held by a HOLDER — a
person, a practitioner, an organisation, or an agent. The standard itself —
two contract families, the packaged corpus, the core validator, the syntax gate
and their promoted requirements — is
[openWallet](https://github.com/opensoft/openWallet), which needs no
openxFactory input. openXwallet is what binds it to openxFactory. It pins
openWallet's ASSEMBLY ROOT twice, by the gitlink `openWallet/` and by
`contracts/openwallet-pin.yaml`, and composes the pinned core with the
factory's rules: the hermes approval-vocabulary binding, the root-issuer
operator anchor (rule (t)), and the review-authority register reader. It runs
them behind the same entrypoints openxFactory's required gate has always
invoked.

**Public.** openWallet's three repositories are public by ruling (Q5, "Public
(Recommended)", 2026-10-08), and this repository already was: the ruling's
consequence on record says so, and `gh repo view` reads `PUBLIC`. So every CI
that initializes the chain clones it with the default token and no secret.
Consumed by pin, never by copy.

| Layer | Repository | Owns |
| --- | --- | --- |
| Neutral standard | openWallet: root `opensoft/openWallet`, legs `opensoft/openWallet-spec` and `opensoft/openWallet-code` | both contract families and the eight digested artifacts, the corpus, the core validator and the syntax gate (code leg); the promoted `openxwallet` and `openxwallet-agent-profile` capabilities (spec leg); the `wallet-v*` release identity (root) |
| Factory adapter | `opensoft/openXwallet` (this repository) | the pin of openWallet; the hermes binding; rule (t) and its three negatives; the register reader |
| Domain wallets | `LedgerxWallet` today; `MedxWallet` and the rest on their first profile | profiles, never forks |

This is the three-layer split of `split-openwallet-neutral-core`, ratified
2026-10-08 by Brett Heap: [`openspec/changes/split-openwallet-neutral-core/`](openspec/changes/split-openwallet-neutral-core/).

## What is here

| | |
| --- | --- |
| `openWallet/` | A gitlink to the openWallet ASSEMBLY ROOT. Its `code/` leg is initialized one level deeper; its `spec/` leg is never initialized here, because nothing here reads it. Never edited in place. |
| `contracts/openwallet-pin.yaml` | The openWallet pin, changed in the same commit as the gitlink: the root `commit:`, `legs.code` (the code-leg commit that root pins, held in LOCKSTEP), the eight per-file sha256 at `code/contracts/…`, and `pinned_by_commit_only:` for the rest. The ONLY record here of which openWallet bytes run. |
| `scripts/verify-openwallet-pin.py` | The openWallet pin verifier: each checkout level present, gitlink and checkout equal to the pin, the code leg's lockstep read from git objects, the eight digests recomputed, every path-only member present and unmodified in its working tree, and a hollowed pin refused. **Fails closed.** |
| `scripts/validate-openxwallet.py` | The conformance validator ENTRYPOINT. It loads the pinned core in process from `openWallet/code/scripts/validate-openxwallet.py` and registers the adapter's rules at the core's declared extension points: rule (t), the register reader, and the hermes binding. Its output on any tree is byte-identical to the pre-split validator's. |
| `scripts/wallet-yaml-syntax-gate.py` | The syntax-gate entrypoint, delegating to the pinned core's: one implementation. |
| `scripts/neutrality-gate.py` | THE NEUTRALITY GATE (`split-openwallet-neutral-core` task 5.4): the validator at the openWallet carve commit and the composed entrypoint, run over this tree, an export of openxFactory's live `governance/` tree and every fixture tree the suites build. It requires an EMPTY `diff`, plain and `--strict` (a suite's own invocations as given and again with `--strict` toggled), with the same exit code; this tree's one new prune note is declared. Its workflow, `neutrality-gate.yml`, reports and is not a required check. |
| `contract_pin.yaml`, `contracts/schemas/hermes-job-envelope.schema.yaml`, `scripts/verify-contract-pin.py` | The hermes binding: the one vendored openxFactory artifact, its digest pin, and the verifier that **fails closed** on it. |
| `contracts/openxwallet/examples/negative/grant-review-*.yaml` | The adapter's own corpus: three negatives, attributed to `OXWR-R1` and `OXWR-R2`, at the path they always had. |
| `contracts/manifest.yaml` | No owned row. One declared CONSUMED member, the vendored envelope. |
| `contracts/CHANGELOG.md` | The release history: the standard's through `wallet-v1.5`, then the adapter's. |
| `tests/` | The suites this repository keeps: the register reader's (`per_seat_register_entries`, `register_reissuance`, `widen_register_reader`), the prune and register note through the composed entrypoint (`nested_repo_prune`), the openWallet pin's (`openwallet_pin`), the neutrality gate's (`neutrality_gate`) and the carve manifest's (`carve_manifest`). The standard's suites run in openWallet's code leg. |
| `openspec/specs/` | `review-authority-register-reader` (three requirements) is the adapter's own. `openxwallet` (eight) and `openxwallet-agent-profile` (three) stay until `split-openwallet-neutral-core`'s archive retires them; their successors live in openWallet's spec leg. The same archive adds `openxwallet-factory-binding` (five), leaving eight requirements in two capabilities. |
| `specs/` | Speckit features `012-wallet-issuer-anchor`, `013-nested-repo-prune-register-note` and `014-per-seat-register-entries`, kept as records. `006-openxwallet-contracts`, `010-wallet-validator-ci` and `015-multi-key-wallets` left for openWallet's spec leg. |
| `docs/openwallet-carve-manifest.yaml` | The declared path mapping of the openWallet carve: one row per tracked path at the carve commit, checked by `scripts/validate-carve-manifest.py`. |
| `contracts/openspec-cli-pin.yaml`, `tools/openspec-cli-pin/` | The pinned OpenSpec CLI, installed offline from a committed tarball. |

## Document index

- [`docs/openxwallet-cutover-runbook.md`](docs/openxwallet-cutover-runbook.md) —
  the ordered, reversible procedure that created this repository, with a rollback
  per phase written before the phase was taken.
- [`docs/byte-identity-wallet-v1.0.md`](docs/byte-identity-wallet-v1.0.md) — the
  two-part proof that `wallet-v1.0` is a byte-identical move, reproducible by
  anyone with both repositories.
- [`docs/openwallet-carve-manifest.yaml`](docs/openwallet-carve-manifest.yaml) —
  every path at the openWallet carve commit, the one place it went, and whether
  it stays here.
- [`docs/pin-resync-runbook.md`](docs/pin-resync-runbook.md) — how to re-sync the
  one vendored openxFactory artifact when it changes upstream.
- [`docs/openspec-cli-pin.md`](docs/openspec-cli-pin.md) — the pinned OpenSpec
  CLI and its offline gate.
- [`contracts/CHANGELOG.md`](contracts/CHANGELOG.md) — the release history.
- [`CLAUDE.md`](CLAUDE.md) / [`AGENTS.md`](AGENTS.md) — agent instructions.

## `wallet-v1.0` is a byte-identical carve

This repository was carved from **openxFactory at commit
`30565e48ffe3d8a9773e10af33425701845e10f6`** — the NAMED CARVE COMMIT — over
twelve path sets, with full path history and **no renames**.

**Every one of the eight digested artifacts carries the sha256 openxFactory
recorded at that commit, unchanged.** Zero renames of `kind:` values, capability
ids, finding codes or filenames; zero corpus edits. Exactly two prose lines
changed in each of the two promoted specifications, enumerated in the proof.

That property is not tidiness. A move whose diff is not provably empty cannot be
bisected against, and openxFactory's later atomic consume-and-shed rests on it.
The proof is [`docs/byte-identity-wallet-v1.0.md`](docs/byte-identity-wallet-v1.0.md).

The second carve, of openWallet out of this repository at
`90111df262d6f54f7e82651d860adc12345f83f4`, kept the property per leg: every
carved path keeps its repository-relative path inside its leg, and every digest
is unchanged. Its rows are declared in
[`docs/openwallet-carve-manifest.yaml`](docs/openwallet-carve-manifest.yaml), and
its proof is a declared path mapping at the openWallet root
(`split-openwallet-neutral-core` `design.md` D7).

## How to consume this repository — ONE chain

**Pin openXwallet's exact commit and the per-file digests, and reach openWallet
THROUGH it.** A movable branch or tag is not a compatibility pin.

A consumer inside the factory carries this repository as `openXwallet/` and
records, in a pin file of its own:

- this repository's commit;
- the per-file `sha256` of the eight digested artifacts at
  `openWallet/code/contracts/…`;
- `pinned_by_commit_only:` for everything else. That means this repository's
  two entrypoints, the core's `openWallet/code/scripts/validate-openxwallet.py`
  and `openWallet/code/scripts/wallet-yaml-syntax-gate.py`, which are the bytes
  that run, and the corpora and family READMEs at `openWallet/code/contracts/…`.

**It records no openWallet commit, root or leg.** It reaches both through this
repository's `contracts/openwallet-pin.yaml`, at the commits this repository
pins: ONE chain (RULED Q2, "Nested gitlink, one chain (Recommended)"). A path `P`
in openWallet's code leg is `openWallet/code/P` here and
`openXwallet/openWallet/code/P` in the consumer, and its sha256 is the same at
every depth.

**Init is scoped: three named levels, never `--recursive`.**

```sh
git submodule update --init openXwallet
git -C openXwallet submodule update --init openWallet
git -C openXwallet/openWallet submodule update --init code
```

A recursive init pulls whole submodule trees, which in an aggregation means all
of them. Even a path-scoped `git submodule update --init --recursive openXwallet`
also fetches `openWallet/spec`, which nothing in a gate reads (`design.md` D6,
"Init is scoped"). A level left uninitialized is exit 2 with a refusal that
names the missing level and its remediation, never a quiet green.

Then the consumer runs `scripts/validate-openxwallet.py <its own tree>` from the
**pinned checkout**. The validator takes one positional path plus `--strict`,
and it scans whatever tree it is given.

Never vendor a copy and treat it as current. Never edit a pinned artifact in
place, here or under `openWallet/`.

**Standalone, outside the factory, pin openWallet directly.** A product with no
factory pins openWallet's assembly root and inherits no rule this repository
adds: no register reader, no operator anchor, no hermes binding. It declares its
own vocabulary binding if it uses approval postures.

### Point the pinned validator at YOUR OWN ROOT

**The scan target must be the consumer's checkout root, not this repository's
directory inside it.** The register reader resolves
`governance/review-authority/register.yaml` relative to the SCAN TARGET, so a
narrower target silently reads no register and the check goes green having
adjudicated nothing that matters. From a consumer whose tree carries this
repository as `openXwallet/`, that is:

```sh
python3 openXwallet/scripts/validate-openxwallet.py .
```

Since **`wallet-v1.1`** that is safe to do from a root with nested repositories
in it. Two notes make the run auditable:

```text
note  nested repositories pruned (not adjudicated): installs/omnigent-install
note  intake register read: governance/review-authority/register.yaml (1 row(s))
```

- **The prune note** lists every directory below the scan root that carries a
  `.git` entry — file (a submodule checkout or a `git worktree`) or directory (a
  nested clone). Nothing at or below such a directory is adjudicated, so a
  pinned product's own OpenSpec instance, test fixtures and canonical registries
  are never mistaken for live records of the consuming tree. The rule is general
  and names no repository: it also covers an ad-hoc nested clone the consumer
  never declared. Absent when there is nothing to prune. A consumer's sweep
  prunes `openXwallet/` whole, `openWallet/` inside it included, so the adapter
  rebuild changes no line of a consumer's output. Only THIS repository's own
  run gains one line, declared in
  [`contracts/CHANGELOG.md`](contracts/CHANGELOG.md):
  `nested repositories pruned (not adjudicated): openWallet`.
- **The register-read note** names the register that was actually opened and how
  many rows it held. Its absence, together with `no intake register at this
  tree`, means the tree legitimately has no register; its absence together with
  a `register-*` finding means the register was found and refused.

Both are **NOTES**, never warnings: a consumer runs `--strict`, where a warning
would red-line its required check. Neither carries a finding code, so neither
can collide with a code a consumer pins by name.

## Three pins, and no cycle

**openxFactory pins openXwallet.** By commit, plus per-file sha256, plus
`pinned_by_commit_only:` — through an `openXwallet/` gitlink and
`contracts/openxwallet-pin.yaml`. openxFactory's own required check invokes the
PINNED entrypoint over openxFactory's tree.

**openXwallet pins openWallet.** By the `openWallet/` gitlink and
`contracts/openwallet-pin.yaml`, declared twice in one commit: the root commit,
the code-leg commit held in lockstep, and the eight digests.
`scripts/verify-openwallet-pin.py` checks that the gitlink, the checkouts at
both levels and the pin name the same commits, and that the eight digests
recompute.

**openXwallet vendors exactly ONE openxFactory artifact**, at a digest pin:
[`contracts/schemas/hermes-job-envelope.schema.yaml`](contracts/schemas/hermes-job-envelope.schema.yaml).
The adapter binds the pinned validator's rule (g) to the approval-scope
vocabulary it reads out of that file, unconditionally (RULED Q6). The file sits
at the **identical repository-relative path** it holds in openxFactory, which is
why the validator needed no source edit in the `wallet-v1.0` move.

Every one of the three is commit-pinned READ-ONLY consumption, and openWallet
pins nothing of either repository above it, so nothing builds in a loop.
`contract_pin.yaml` records the openxFactory side and names its verifier.
`scripts/verify-contract-pin.py` runs FIRST of the two verifiers in
`wallet-validation`, because the adapter's entrypoint reads rule (g)'s
vocabulary out of the vendored file and never checks its identity: an
unverified swap would silently redefine what the gate enforces.

The manifest records that file as a **CONSUMED member**
(`member_class: consumed`, `release_surface: false`,
`compatibility: canonical_openxfactory_contract`), so the publisher-marker rule is
met without openXwallet claiming ownership of an openxFactory contract, and the
release surface excludes it by DECLARED FIELD rather than by a path heuristic.
It is the manifest's only row: the eight digested artifacts are openWallet's,
and the pin file, not a second digest in the manifest, records them here.

## Domain descendants: pin and profile, never fork

`LedgerxWallet`, `MedxWallet`, `codexWallet`, `OpsxWallet` and `AdxWallet` are
DISTRIBUTIONS, mirroring how DomainxFactories consume openxFactory. A descendant
pins the layer it needs: openXwallet inside a factory, or openWallet standalone.
It carries its domain profile over the core — its holder classes, its custody
declarations, its grant scopes — and no divergent contract content. A "tuned"
variant is a PIN TARGET, never a fork.

**A domain need a profile cannot express is an upstream change, not a fork**: to
openWallet when it is the standard's, here when it is the factory binding's.
Upgrades are a pin bump.

The profile path is already real, not aspirational: the agent profile is a SIBLING
family over the core rather than an extension of it, precisely so a second and
third profile arrive the same way. `LedgerxWallet` is the first descendant, at
extraction time, because LedgerxFactory is the only live consumer today — two
wallet records, two grants, one distinct-holder constraint, an exercise template
and an estate test. `MedxWallet` follows on the Medx EMR thread's first profile;
codex, Ops and Adx on demand.

## Validation

Every gate here is **OFFLINE**: none reads the network, none reads an unpinned
upstream tree, and none reads `contracts/manifest.yaml` at check time. The two
init lines are checkout, not gates: they fetch the commits the gitlinks record,
and `scripts/verify-openwallet-pin.py` then proves, offline, that what arrived is
what the pin names. The live manifest cross-check is a SYNC-TIME obligation —
see [`docs/pin-resync-runbook.md`](docs/pin-resync-runbook.md).

```sh
git submodule update --init openWallet             # the openWallet root; never --recursive
git -C openWallet submodule update --init code     # its code leg; never the spec leg
python3 scripts/verify-contract-pin.py             # the vendored envelope's digest
python3 scripts/verify-openwallet-pin.py           # the openWallet pin: gitlink, checkouts, lockstep, eight digests
python3 scripts/wallet-yaml-syntax-gate.py .
python3 scripts/validate-openxwallet.py .
python3 scripts/validate-openxwallet.py . --strict
python3 -m pytest tests/ -q
OPENSPEC_TELEMETRY=0 openspec validate --all --strict
```

`wallet-validation` runs the first seven lines in that order, and **`pytest-suite`**
runs the two init lines and then the suite, because the kept suites drive the
composed validator, which needs the core. Ruleset **21607344** requires both,
with `lane-line` and `carve-manifest` (read with `gh api` on 2026-10-09). The
`wallet-validation` token is deliberately the same name openxFactory uses: the
token names the check's function, and distinct repositories are distinct
namespaces. The neutrality gate, `scripts/neutrality-gate.py`, runs in its own
workflow, `neutrality-gate.yml`, which reports on every pull request and is not
among the required checks.

**Branch protection was bootstrapped, not configured.** Ruleset **21607344** was
created in **EVALUATE** enforcement and promoted to **ACTIVE** only after both
checks had reported once. Day-one REQUIRED is *impossible*, not merely
inconvenient: GitHub cannot require a status check that has never reported in the
repository, because the context is not selectable until then. The sequence is
recorded in
[`docs/openxwallet-cutover-runbook.md`](docs/openxwallet-cutover-runbook.md).

## Governance

Contract and boundary changes go through OpenSpec before implementation; Speckit
builds what OpenSpec ratifies. See [`AGENTS.md`](AGENTS.md). A change to the
standard itself is openWallet's, in its spec leg; a change to how the standard is
bound to openxFactory is this repository's.

A release is five coordinated values: per-file `contract_schema_version`,
`contract_bundle_version` in `contracts/manifest.yaml`, an annotated tag, the
exact release commit with per-file digests, and a matching
`contracts/CHANGELOG.md` entry. The `wallet-v*` series continues at the
openWallet root (RULED Q4). This repository's next release opens the adapter's
own series, spelled and numbered at its first release
(`split-openwallet-neutral-core` task 5.8). Version numbers are allocated at
realization, never reserved in a proposal.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
