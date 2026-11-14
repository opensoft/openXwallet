# Agent Instructions

Use the shared OpenSpec/Speckit workflow from:

- `$HOME/.agents/AGENTS.md`
- `$HOME/.agents/protocols/openspec-speckit-workflow.md`
- `$HOME/.agents/protocols/project-agent-bootstrap.md`

Repository documents remain authoritative for openXwallet product facts, contract
ownership, validation, versioning, and release constraints.

<!-- SPECKIT START -->
## Active Speckit Feature

- Active feature: 017-protected-runtime-qualification; plan:
  specs/017-protected-runtime-qualification/plan.md.
- Ratified factory composition: opensoft/openXfactory,
  openspec/changes/prepare-protected-runtime-qualification/.
  Feature 017 tasks.md is the sole implementation list. Brett Heap ratified
  #1307 at 04fad0559 with openXwallet #49 at 0a2dda9. The issuer slice
  landed in #50. Brett ratified factory #1308 at 7d99face8934 with adapter
  #51 at 864a2d19fda1 for source acceptance only, then commissioned isolated
  T004/T005 loaders/runtime composition. Brett subsequently ratified adapter
  #52 at 3833bc8629e6 for source acceptance only and commissioned T006 in
  isolation. Brett ratified #53 at aff5b1e14979 for source acceptance only
  and commissioned T007 in isolation. Brett ratified #54 at 8de227dadd53 for
  source acceptance only and commissioned T008 in isolation.
  Brett ratified #55 at caef11d92906 for source acceptance only and commissioned
  T009 in isolation. Brett ratified #56 at 508cb51f3407 for source acceptance
  only and commissioned T010 in isolation. The required offline matrix is
  tests/runtime_binding/conformance.py, bootstrapped by isolation.py inside a
  loopback-only Linux namespace; its reviewed matrix_contract.py rejects missing,
  deselected, skipped or non-passing cases. Brett ratified #57 at 2c36b07622fc
  for source acceptance only and commissioned T011 in isolation. Internal
  evidence.py emits bounded canonical source/fixture reports with fixed errors,
  exact source/case/readback/cleanup digests and no raw sensitive payload.
  Protected-machine receipt scope remains unsupported in this slice. Brett ratified
  #58 at 4916476364f7 for source acceptance only and commissioned T012 in
  isolation. Manual protected workflow preparation uses an exact caller/local
  reusable commit, independent pre-environment admission and narrow OIDC.
  Brett ratified #59 at 948ea81d7cdc for source acceptance only and commissioned
  T013 operational selection/authorization preparation. It landed normally as
  9e1d75d46dfd with the ratified tree. The selection packet and staged authority
  draft are in feature 017 operational-inputs.md and scoped-authorization.md.
  The initial workflow-bootstrap.md packet recorded a verified dispatch/run-digest
  circularity and proposed its factory-governed amendment without changing code.
  The subsequent instruction commissions isolated T012B implementation under
  factory change fix-protected-runtime-dispatch-bootstrap. Static dispatch
  selection and independently authenticated actual-run bootstrap preserve full
  runtime config/grant admission. Brett source-ratified factory #1311 at
  6dadf188a0af with adapter #60 at 78e7bbeabca2. They landed as f2fb60f04c82
  and 61fbe41f7e08 with matching ratified trees. Factory post-merge source CI is
  verified in feature 017 evidence.md. T013's refreshed selection/authority draft
  names the missing bootstrap authentication/atomicity, hosting, principals and
  exact scope decisions; owner/operational checkboxes remain unmarked.
  Brett source-ratified factory #1312 at b741ae396bc0, adapter #61 at
  caa56dc001f6 and adapter #62 at 62b270127e74, then directed ordered landing
  and T013 preparation. They landed with matching accepted trees as
  6604b55b980c, 6171f5f5c53c and 425606899116. The accepted portable authority
  remains fixture-only, not an operational hosting/authentication selection.
  Feature 017 t013-decision-record.md and bootstrap-authentication-plan.md
  prepare source/target decisions; T013 and all setup/dispatch gates stay open.
  Default operational bindings continue to refuse before outputs/OIDC.
  Production hosting stays unselected; no setup/dispatch is authorized.
  Deployed supervisor, custody, state, lifecycle and operation stay
  separately gated. The factory owns the grammar.
  Existing offline entrypoints stay unchanged.
- Accepted baseline: 016-factory-workload-binding; source decision:
  specs/016-factory-workload-binding/source-acceptance.md and plan.md.
- Existing adapter governing baseline: THIS repository's
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
   at the openWallet root (RULED Q4). This repository's series is
   `xwallet-v<major>.<minor>`, first `xwallet-v1.0` (ruled, "Adapter series
   `xwallet-v*`, first `xwallet-v1.0` (Recommended)"), and
   `contract_bundle_version` holds the tag's value ("The adapter's tag value
   (Recommended)"). `xwallet-v1.0` is tagged at the adapter rebuild's merge
   commit by `split-openwallet-neutral-core` task 5.8, an operator act.
