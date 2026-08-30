# Agent Instructions

Use the shared OpenSpec/Speckit workflow from:

- `$HOME/.agents/AGENTS.md`
- `$HOME/.agents/protocols/openspec-speckit-workflow.md`
- `$HOME/.agents/protocols/project-agent-bootstrap.md`

Repository documents remain authoritative for openXwallet product facts, contract
ownership, validation, versioning, and release constraints.

<!-- SPECKIT START -->
## Speckit Baseline

- Active feature: none
- Latest completed feature: `015-multi-key-wallets`
- Plan: `specs/015-multi-key-wallets/plan.md`
- Governing change: THIS repository's
  `openspec/changes/add-multi-key-wallets/` — capability `openxwallet`

The governing change was RATIFIED (2026-08-28, Brett Heap, operator authority,
in-session ruling "rule option 1 and build it") and merged. Feature
`015-multi-key-wallets` is complete and released as `wallet-v1.3`; feature
`014-per-seat-register-entries` and `wallet-v1.2` are the preceding baseline.
<!-- SPECKIT END -->

## What this repository is, in one paragraph

openXwallet owns the neutral wallet standard — two contract families, the packaged
corpus, the conformance validator, the syntax gate, and eleven promoted
requirements. It is a PRODUCT that other repositories pin. It is not a factory
layer: the factory-layer USE of wallet authority (review-authority registers,
grant compositions, trust-anchor and identity-brokering compositions) stays in
openxFactory.

## The rules that are not negotiable here

1. **Consumers pin; nobody forks.** Domain descendants (`LedgerxWallet`,
   `MedxWallet`, `codexWallet`, `OpsxWallet`, `AdxWallet`) pin a version and carry
   a profile. A need a profile cannot express is an upstream change here.
2. **Machine keys do not move casually.** Paths, `kind:` values, capability ids,
   the `xfactory_wallet_*` prefix, finding codes and filenames are pinned BY NAME
   by live consumers. Renaming one is a breaking change with a migration note,
   never a tidy-up.
3. **`contracts/schemas/hermes-job-envelope.schema.yaml` is not ours.** It is
   vendored from openxFactory at a digest pin recorded in `contract_pin.yaml`, and
   it must stay at that exact repository-relative path — the validator's
   `ENVELOPE_SCHEMA_PATH` is ROOT-relative and the validator's bytes are inside
   the byte-identity floor. Re-sync through `docs/pin-resync-runbook.md`; never
   edit it in place.
4. **Every gate is offline.** No check reads the network, an upstream tree, or
   `contracts/manifest.yaml`. The live manifest cross-check is a sync-time
   obligation.
5. **Run the gates before pushing.** `scripts/verify-contract-pin.py`, the syntax
   gate, the validator (plain and `--strict`), `python3 -m pytest tests/ -q`, and
   `OPENSPEC_TELEMETRY=0 openspec validate --all --strict`.
6. **A release is five coordinated values**, and the version is allocated at
   realization: per-file `contract_schema_version`, `contract_bundle_version`, an
   annotated `wallet-v<major>.<minor>` tag, the release commit with per-file
   digests, and the `contracts/CHANGELOG.md` entry.
