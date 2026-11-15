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
  Brett subsequently source-ratified adapter #63 at 54dd1e1d4dc6; it landed
  normally as be41830acd16 with matching tree. Current proposal preparation
  uses factory change add-github-bootstrap-authentication and feature017
  github-bootstrap-proposal.md plus proposed T012G-M. Bootstrap-only admission
  OIDC was subsequently source-ratified in factory #1314 at 94bf0f43704f
  with adapter #64 at ff9bd72278a5, landed as 3432baf6d929 and a352ebc7ed22
  with matching ratified trees. The owner commissioned isolated T012H-K.
  Brett subsequently source-ratified adapter #65 at ab34ff4ec4fe and directed
  landing when green, then T012M completion and T013 refresh. It merged normally
  as 366533bed77293b096b0a7dbda61399ff5dbafe5 with equal ratified/merged tree
  669a1b431f17d360fcf827a749a756e863ec9ed8. T012L is accepted and T012M's handoff
  reconciles the source; actual hosting/issuance, subjects, source-update control
  and every operational decision remain T013 gates. T001/T013-T015 stay unchecked.
  No token mint, setup or dispatch is commissioned.
  Default operational bindings continue to refuse before outputs/OIDC.
  Production hosting stays unselected; no setup/dispatch is authorized.
  Deployed supervisor, custody, state, lifecycle and operation stay
  separately gated. The factory owns the grammar.
  Brett subsequently source-ratified adapter #66 at c8050f9eb1ff; it landed
  normally as 5498a9b27d7a61daf8f4088ce85906cb436a2033 with equal tree
  e3664990f55b49bfb7629b864816900d6b429491.
  The subsequent user instruction commissions only factory-governed hosting/issuance
  proposal and Speckit plan preparation using the recommended T013 design basis.
  Factory draft change: add-protected-runtime-hosting-issuance; feature017 subplan:
  specs/017-protected-runtime-qualification/hosting-issuance-plan.md. Proposed
  T012N-V are the sole future source tasks and stay unchecked/uncommissioned.
  Static-v2 plan-only preflight/protected staging/finalization is a material new
  source decision; preserve v1/default and all neutral APIs/pins. No implementation,
  token acquisition, setup or dispatch is commissioned by this planning request.
  The subsequent publication instruction authorizes gate resolution, both candidate
  PRs, hosted CI and local Codex review, then presentation of v2 for ratification.
  It supplies no v2 acceptance, implementation commission or operational grant.
  Brett subsequently source-ratified factory #1317 at 943e33fdafdc with adapter
  #67 at db7de85f709e, directed ordered landing and commissioned only T012O in
  isolation. Factory merged as 4496ee860587d2c557c9f7dd124d9d0029bd89a8; adapter
  merged as 02d902a4b19d9855780aad5996964686e7452929. Isolated hosted/ source is an
  implementation candidate, not live hosting or an operational binding. T012P-V,
  setup/dispatch, issuance/provider setup and live acceptance remain separate.
  Existing offline entrypoints stay unchanged.
  The subsequent instruction authorizes T012O candidate publication, hosted CI and
  local Codex review after factory main Sonar repair; owner source ratification
  and operational grants remain separate.
  Brett subsequently source-ratified #68 at 38b029b02a9b; it merged normally as
  4bae2b22f74e19a43d8413055142447319a41202 with the accepted tree. Only T012P
  enrollment/issuance/host-credential source is commissioned in isolation.
  T012Q-V, setup/dispatch and live qualification remain uncommissioned.
  The subsequent instruction commissions T012P PR publication, hosted CI and local
  Codex expert review, followed by presentation for owner source ratification.
  PR #69 remains a source candidate; no operational grant is inferred.
  Brett subsequently source-ratified #69 at b73a7d06695e. It merged normally
  as 7bd884106eea5f0ed4b99a35da70d613ccbfd0d2 with equal accepted/merged tree.
  Only T012Q readback implementation/testing is now commissioned in isolation.
  T012R-V, setup/dispatch and live qualification remain uncommissioned.
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

## Current bounded source continuation

Brett commissioned the T012Q protection-read correction under factory change
fix-hosted-protection-read-budget (#1322), paired publication, CI and local Codex
review. The proposed finalizer-only six-observation/18-protection/28-total ledger
retains default3/13 and all original clocks/current checks. Source ratification and
landing remain separate; T012R-V and setup/dispatch are uncommissioned.
