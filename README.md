# openXwallet

**The neutral wallet standard.** A wallet is a signing key anchored to a
decentralized identifier and held by a HOLDER — a person, a practitioner, an
organisation, or an agent. This repository owns the standard: its two contract
families, its packaged corpus, its validator, its syntax gate, and the promoted
specifications that govern them.

Private. Consumed by pin, never by copy.

## What is here

| | |
| --- | --- |
| `contracts/openxwallet/` | The **holder-agnostic core**. Six kinds: the wallet record, the closed custody registry, the attenuated capability grant, the grant exercise record, the opt-in distinct-holder constraint, and the subject attestation. |
| `contracts/openxwallet-agent-profile/` | The **first profile** over that core, registered as a SIBLING family rather than an extension of it — so patient and practitioner profiles arrive the same way. |
| `contracts/manifest.yaml` | The published bundle: eight owned artifacts with per-file digests, plus one declared CONSUMED member. |
| `contracts/CHANGELOG.md` | The release history, including the two openxFactory bundles that first published these contracts. |
| `scripts/validate-openxwallet.py` | The conformance validator. Enforces the rules the shapes cannot express, and READS the approval-scope vocabulary out of the vendored job envelope rather than restating it. |
| `scripts/wallet-yaml-syntax-gate.py` | The syntax gate. |
| `scripts/verify-contract-pin.py` | The pin verifier: recomputes the vendored artifact's digest against `contract_pin.yaml` and **fails closed**. |
| `tests/wallet_yaml_syntax_gate/` | The gate's own tests. |
| `openspec/specs/` | The eleven promoted requirements, in two capabilities. |
| `specs/` | Speckit features `006-openxwallet-contracts`, `010-wallet-validator-ci`, `012-wallet-issuer-anchor`. |

## Document index

- [`docs/openxwallet-cutover-runbook.md`](docs/openxwallet-cutover-runbook.md) —
  the ordered, reversible procedure that created this repository, with a rollback
  per phase written before the phase was taken.
- [`docs/byte-identity-wallet-v1.0.md`](docs/byte-identity-wallet-v1.0.md) — the
  two-part proof that `wallet-v1.0` is a byte-identical move, reproducible by
  anyone with both repositories.
- [`docs/pin-resync-runbook.md`](docs/pin-resync-runbook.md) — how to re-sync the
  one vendored openxFactory artifact when it changes upstream.
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

## How to consume this repository

**Pin the exact commit and the per-file digests.** A movable branch or tag is not
a compatibility pin.

A consumer records the commit, the per-file `sha256` for the eight digested
artifacts, and `pinned_by_commit_only:` for everything else — the packaged corpus,
the validator, the syntax gate and both family READMEs are content-addressed by
commit with no per-file digest. Then it runs
`scripts/validate-openxwallet.py <its own tree>` from the **pinned checkout**: the
validator takes one positional path plus `--strict`, and it scans whatever tree it
is given.

Never vendor a copy and treat it as current. Never edit a pinned artifact in
place.

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
  never declared. Absent when there is nothing to prune.
- **The register-read note** names the register that was actually opened and how
  many rows it held. Its absence, together with `no intake register at this
  tree`, means the tree legitimately has no register; its absence together with
  a `register-*` finding means the register was found and refused.

Both are **NOTES**, never warnings: a consumer runs `--strict`, where a warning
would red-line its required check. Neither carries a finding code, so neither
can collide with a code a consumer pins by name.

## The pin relationship runs in BOTH directions, and there is no cycle

**openxFactory pins openXwallet.** By commit, plus per-file sha256, plus
`pinned_by_commit_only:` — through an `openXwallet/` gitlink and
`contracts/openxwallet-pin.yaml`. openxFactory's own required check invokes the
PINNED validator over openxFactory's tree.

**openXwallet vendors exactly ONE openxFactory artifact**, at a digest pin:
[`contracts/schemas/hermes-job-envelope.schema.yaml`](contracts/schemas/hermes-job-envelope.schema.yaml),
from which validator rule (g) reads the legal approval-scope vocabulary. It sits
at the **identical repository-relative path** it holds in openxFactory, which is
why the validator needed no source edit in the move.

Both directions are commit-pinned READ-ONLY consumption, so nothing builds in a
loop. `contract_pin.yaml` records the openxFactory side and names its verifier;
`scripts/verify-contract-pin.py` runs as the FIRST step of `wallet-validation`,
because the validator checks only that the vendored file EXISTS — presence, not
identity — while rule (g) reads the vocabulary out of it.

The manifest records that file as a **CONSUMED member**
(`member_class: consumed`, `release_surface: false`,
`compatibility: canonical_openxfactory_contract`), so the publisher-marker rule is
met without openXwallet claiming ownership of an openxFactory contract, and the
wallet's release surface excludes it by DECLARED FIELD rather than by a path
heuristic.

## Domain descendants: pin and profile, never fork

`LedgerxWallet`, `MedxWallet`, `codexWallet`, `OpsxWallet` and `AdxWallet` are
DISTRIBUTIONS of this repository, mirroring how DomainxFactories consume
openxFactory: a descendant pins an openXwallet version and carries its domain
profile over the core — its holder classes, its custody declarations, its grant
scopes — and no divergent contract content.

**A domain need a profile cannot express is an upstream change to openXwallet, not
a fork.** Upgrades are a pin bump.

The profile path is already real, not aspirational: the agent profile is a SIBLING
family over the core rather than an extension of it, precisely so a second and
third profile arrive the same way. `LedgerxWallet` is the first descendant, at
extraction time, because LedgerxFactory is the only live consumer today — two
wallet records, two grants, one distinct-holder constraint, an exercise template
and an estate test. `MedxWallet` follows on the Medx EMR thread's first profile;
codex, Ops and Adx on demand.

## Validation

Every gate here is **OFFLINE**: none reads the network, none reads an upstream
tree, and none reads `contracts/manifest.yaml` at check time. The live manifest
cross-check is a SYNC-TIME obligation — see
[`docs/pin-resync-runbook.md`](docs/pin-resync-runbook.md).

```sh
python3 scripts/verify-contract-pin.py       # the vendored artifact's digest
python3 scripts/wallet-yaml-syntax-gate.py .
python3 scripts/validate-openxwallet.py .
python3 scripts/validate-openxwallet.py . --strict
python3 -m pytest tests/ -q
OPENSPEC_TELEMETRY=0 openspec validate --all --strict
```

Two required status checks gate the default branch: **`wallet-validation`**
(the pin verify, then the syntax gate, then the validator) and **`pytest-suite`**.
The `wallet-validation` token is deliberately the same name openxFactory uses —
the token names the check's function, and distinct repositories are distinct
namespaces.

**Branch protection was bootstrapped, not configured.** Ruleset **21607344** was
created in **EVALUATE** enforcement and promoted to **ACTIVE** only after both
checks had reported once. Day-one REQUIRED is *impossible*, not merely
inconvenient: GitHub cannot require a status check that has never reported in the
repository, because the context is not selectable until then. The sequence is
recorded in
[`docs/openxwallet-cutover-runbook.md`](docs/openxwallet-cutover-runbook.md).

## Governance

Contract and boundary changes go through OpenSpec before implementation; Speckit
builds what OpenSpec ratifies. See [`AGENTS.md`](AGENTS.md).

A contract release is five coordinated values: per-file
`contract_schema_version`, `contract_bundle_version` in `contracts/manifest.yaml`,
an annotated `wallet-v<major>.<minor>` tag, the exact release commit with per-file
digests, and a matching `contracts/CHANGELOG.md` entry. Version numbers are
allocated at realization, never reserved in a proposal.
