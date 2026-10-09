# Agent Instructions

Use the shared OpenSpec/Speckit workflow from:

- `$HOME/.agents/AGENTS.md`
- `$HOME/.agents/protocols/openspec-speckit-workflow.md`
- `$HOME/.agents/protocols/project-agent-bootstrap.md`

Repository documents remain authoritative for openXwallet product facts, contract
ownership, validation, versioning, and release constraints.

<!-- SPECKIT START -->
## Active Speckit Feature

- Feature: NONE is active in this repository.
- Governing change: THIS repository's
  `openspec/changes/split-openwallet-neutral-core/`, RATIFIED 2026-10-08
  (Brett Heap, operator authority, "ratify 26 and merge"). Its §5 is the
  adapter rebuild.
- Active change: `openspec/changes/widen-register-reader-for-a-second-council/`
  (capability `review-authority-register-reader`), realized at `wallet-v1.5`
  and not yet archived.

The last feature named here, `015-multi-key-wallets`, is complete: it was
released as `wallet-v1.3`, and its change was archived on 2026-10-08. It LEFT
this repository, with Speckit `006` and `010`, for openWallet's spec leg in the
adapter rebuild. Speckit `012`, `013` and `014` stay, as records.
<!-- SPECKIT END -->

## What this repository is, in one paragraph

openXwallet is the openxFactory ADAPTER over the neutral wallet standard,
openWallet. It pins openWallet's assembly root, by the gitlink `openWallet/` and
by `contracts/openwallet-pin.yaml`, with the code leg held in lockstep. It
composes the pinned core validator in process with the factory's rules: the
hermes approval-vocabulary binding (`contract_pin.yaml` and the vendored
envelope), rule (t)'s root-issuer operator anchor with its three negatives, and
the review-authority register reader. It owns NO contract. The standard — two
contract families, the corpus, the core validator, the syntax gate and their
promoted requirements — is openWallet's, carved out of this repository at
`90111df262d6f54f7e82651d860adc12345f83f4` by `split-openwallet-neutral-core`.
Its entrypoints and its `wallet-validation` check token are pinned by string by
openxFactory and LedgerxFactory, so they did not move. The factory-layer USE of
wallet authority (the review-authority register itself, grant compositions,
trust-anchor and identity-brokering compositions) stays in openxFactory.

## The rules that are not negotiable here

1. **Consumers pin; nobody forks.** Domain descendants (`LedgerxWallet`,
   `MedxWallet`, `codexWallet`, `OpsxWallet`, `AdxWallet`) pin a version and carry
   a profile. A need a profile cannot express is an upstream change: to
   openWallet when it is the standard's, here when it is the factory binding's.
2. **Machine keys do not move casually.** Paths, `kind:` values, capability ids,
   the `xfactory_wallet_*` prefix, finding codes and filenames are pinned BY NAME
   by live consumers. Renaming one is a breaking change with a migration note,
   never a tidy-up.
3. **`contracts/schemas/hermes-job-envelope.schema.yaml` is not ours.** It is
   vendored from openxFactory at a digest pin recorded in `contract_pin.yaml`, and
   it must stay at that exact repository-relative path. The adapter binds the
   pinned validator's approval vocabulary from it relative to this repository's
   root, and its vocabulary note prints that path byte for byte, as the
   neutrality gate requires (`split-openwallet-neutral-core` `design.md` D4,
   D5). Re-sync through `docs/pin-resync-runbook.md`; never edit it in place.
   **`openWallet/` is not ours either.** It is pinned by
   `contracts/openwallet-pin.yaml` and verified by
   `scripts/verify-openwallet-pin.py`, never edited in place. A fix to the
   standard is an openWallet pull request. Then a pin bump here moves the
   gitlink and the pin file in ONE commit.
4. **Every gate is offline.** No check reads the network, an unpinned upstream
   tree, or `contracts/manifest.yaml`. The two scoped init lines fetch the
   commits the gitlinks record; they are checkout, not a gate, and
   `scripts/verify-openwallet-pin.py` then proves offline that what arrived is
   what the pin names. The live manifest cross-check is a sync-time obligation.
5. **Run the gates before pushing.** First the two scoped init lines,
   `git submodule update --init openWallet` and then
   `git -C openWallet submodule update --init code`, never `--recursive`:
   a recursive init also fetches `openWallet/spec`, which nothing here reads.
   Then, in this order: `scripts/verify-contract-pin.py`,
   `scripts/verify-openwallet-pin.py`, the syntax gate, the validator (plain and
   `--strict`), `python3 -m pytest tests/ -q`, and
   `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`.
6. **A release is five coordinated values**, and the version is allocated at
   realization: per-file `contract_schema_version`, `contract_bundle_version`, an
   annotated tag, the release commit with per-file digests, and the
   `contracts/CHANGELOG.md` entry. The `wallet-v<major>.<minor>` series continues
   at the openWallet root (RULED Q4). This repository's tag opens the adapter's
   own series, spelled and numbered at its first release
   (`split-openwallet-neutral-core` task 5.8, an operator act).
