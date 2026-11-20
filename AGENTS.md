Current T013P03 corrected qualification: runtime/test commit a97a69c399efd9a1b30093073bae6637c9046812
passes all seven ordered offline gates, full 3,224 cases plus 11 subtests and
native 2,802 cases, with zero failures/errors/skips. All nine local Codex
specialists clear this corrected head; independent fixture/helper/retention
and container cleanup passes. This documentation receipt changes no qualified
runtime/test/matrix bytes. Hosted CI on the publication head and source-only
owner ratification remain separate. No merge or operational grant is inferred.
P04-P09 and setup/dispatch remain gated; feedback deferred; blocked writes unreplayed.

Earlier T013P03 publication/review checkpoint: Brett commissions PR #98,
hosted source CI, the local nine-role Codex panel, finding resolution and
presentation for source-only ratification. No source acceptance or merge is
granted. The initial panel reproduced four defects; the corrected source has
195 passing focused controls and 13 detected guard/table mutations. Replacement
full/native qualification, cleanup, exact-head follow-up and hosted CI remain
pending at this checkpoint. Earlier e416/37d0 completion records are historical
for the initial candidate. P04-P09, setup/dispatch and consumer/human acceptance
remain gated; feedback deferred and blocked writes unreplayed.

Current T013P03 isolated result: runtime/test commit e416399f4f663463236576782174a42824d96aa4
passes seven ordered gates, full 3,209 parents plus 11 subtests and native 2,787,
with independent helper, retention and container/fixture teardown. See feature017
p3-provider-implementation.md. P03 isolated implementation is complete; source
acceptance/publication, P04-P09 and operational setup/dispatch remain separate.
Feedback deferred; blocked writes unreplayed.

Current T013P03 isolated implementation commission (2026-11-19): Brett explicitly
instructed implementation and testing of T013P03 using the prepared provider
subplan, first pilot only. Earlier preparation-only labels are historical for
this slice. Only P03 code/tests/qualification are commissioned; P04-P09 and
operational setup/dispatch remain unauthorized. Feedback deferred; blocked writes
and rejected optional publications remain unreplayed. Do not mark P03 complete
until substantive exact-source isolated qualification and cleanup pass.

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
  Current P3 preparation subplan: specs/017-protected-runtime-qualification/p3-azure-composition-plan.md.
  Current bounded slice: specs/017-protected-runtime-qualification/p3-provider-plan.md (T013P03; isolated implementation commissioned).
  Earlier T012T subplan remains historical: specs/017-protected-runtime-qualification/hosting-evidence-plan.md.
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

## Historical T012Q continuation (superseded below)

Brett commissioned the T012Q protection-read correction under factory change
fix-hosted-protection-read-budget (#1322), paired publication, CI and local Codex
review. The proposed finalizer-only six-observation/18-protection/28-total ledger
retains default3/13 and all original clocks/current checks. Source ratification and
landing remain separate; T012R-V and setup/dispatch are uncommissioned.

## Historical source-accepted T012R continuation

Brett source-ratified #1322 e813051af8c0 with #70 f6956e324e37 and commissioned
ordered landing then T012R only in isolation. Normal merges 54f720b6df81 and
27843096189a retain accepted trees. Feature017 hosting-launch-implementation.md
records the bounded source plan; tasks.md remains the sole executable list.
T012S-V, setup/dispatch and live acceptance remain unauthorized.

T012R's reviewed isolated candidate now passes 106 new launch cases, 2,200 full tests and
1,898 mandatory native nodes; its as-built boundary and limits are recorded in
hosting-launch-implementation.md. No source ratification or T012S-V commission is
inferred. Default bindings remain refusing; setup/dispatch remain unauthorized.

The reviewed correction is paired with proposed factory #1326 (fix-hosted-staging-refresh-budget).
Two complete protected-stage observations share one original Decision and bounded
26-total/private16 allocation; ordinary and finalization allocations are unchanged.
Adapter #71 changes the ordinary pytest privilege bootstrap only; protected workflow
YAML, default refusal, neutral APIs and pins remain unchanged. Local review is complete;
source ratification, landing and operational authority remain separate gates.

## Historical T012S preparation

Brett source-ratified factory #1326 dc159da61860 with adapter #71 74b4af51322b,
then directed ordered landing and T012S preparation only. They merged in order
as 0503c7bf36ea and 7042b295bc72; accepted packet blobs and adapter tree are verified.
Feature017 hosting-lifecycle-plan.md and hosting-lifecycle-acceptance.md prepare
H05/H11 staging lease, immutable same-generation final takeover and independent
scheduler/janitor/audit. tasks.md remains the sole executable list. T012S and
T012S01-T012S07 stay unchecked/uncommissioned for implementation. T012T-V,
T001/T013-T015, setup/dispatch and live provider/host acceptance remain separate.
No lifecycle initialization, scheduler activation or service restart is performed
by this preparation. Feedback deferred; neither blocked/denied write replayed.

## T012S isolated implementation commission

Brett now commissions implementation/testing of T012S in isolation using the
prepared lifecycle plan, with factory post-merge CI verified separately. Only
T012S01-T012S07 are executable; mark completion only after actual checks. Preserve
all old matrix identities and budgets. T012T-V, setup/dispatch and live qualification
remain uncommissioned; feedback deferred and neither blocked write replayed.

## Historical T012S isolated candidate qualification

The commissioned T012S/S01-S07 implementation and isolated qualification are
complete: 105 lifecycle cases, 2,308 full tests plus four subtests and 2,003 mandatory native cases,
with no failures or skips. All 150 frozen Python/workflow inputs and four pin/dependency files match before/after;
all 1,898 baseline native identities/fingerprints/anchors are preserved. The seven
ordered gates, including the default pinned OpenSpec strict verifier, pass. Factory
post-merge run 43772988866 passes on inherited main fefb5ae4ad72 with the accepted
six-file packet preserved. Evidence.md records exact CI provenance and receipts.

Both active staging/final leases recheck the actual selected scheduler generation;
closed-lease cleanup remains independently available. Exact-generation teardown and
preservation audits pass; task fixtures and native container are removed. This is
an isolated source candidate, not source ratification, deployment, actual provider
qualification or T012T-V commissioning. Setup/dispatch remain unauthorized; feedback
deferred and neither blocked write replayed. The owner commissioned PR #75 publication and local Codex review; exact-head
CI is recorded on the PR, while owner source acceptance remains pending. The explicit local POSIX reference supplies no external control-host-loss
watchdog, automatic VM expiry or cloud infrastructure retirement capability.

## T012S publication commission

Brett authorizes opening the T012S PR, hosted source CI, local Codex expert review,
finding resolution and presentation for ratification. This supplies no source
acceptance, merge, T012T-V or operational grant. Setup/dispatch remain unauthorized,
feedback deferred and neither blocked write replayed. Preserve accepted scope and
budgets; keep CI, local review and source ratification as distinct gates.

T012S07's publication correction includes the ordinary source-CI job cap: 20 to
45 minutes so its existing full and mandatory native suites can both complete.
The prior local 154-input receipts remain historical; one ordinary workflow
hash changes and the other 153 inputs are identical. PR #75 records fresh hosted
full/native results. Protected defaults and runtime authority budgets are unchanged.

The subsequent journal-capacity fix deep-copies validated events without imposing
a single-document limit on their aggregate. Its corpus is 107 lifecycle / 2,310
full / 2,005 native cases. Its new complete 154-input freeze is ready; renewed
full/native and hosted execution remain pending at this source checkpoint, with
completion receipts to be posted on PR #75. The
153/one account above describes only the earlier ordinary-CI cap checkpoint.
The 63-selected-resource mixed-retention positive preserves original clocks;
the separate all-run throughput stress remains unverified after its Decision
expired. Do not infer operational qualification or alter runtime budgets.

The subsequent file-fence correction moves only file claims inside the acquired
parent/pin generation fence. One combined bounded lock wait samples the original
Decision; claim-success followed by failure remains consumed. Process/token
claiming and protected defaults do not change. Its 110 lifecycle / 2,313 full /
2,008 native corpus needs fresh full/native and exact-head hosted completion;
those checks remain pending at this immutable source checkpoint. PR #75 will
record receipts after execution. Existing concurrency/deadline assertions remain.

The optional SQLite rollback-journal correction permits only the artifact's
FileNotFoundError during a legitimate concurrent DELETE-mode commit. Required
identities and locked hash/witness validation remain enforced; forbidden WAL/SHM,
symlink and permission checks still refuse. The actual-writer overlap regression
and four invalid-artifact controls extend the current corpus to 115 lifecycle /
2,318 full / 2,013 mandatory native cases, with H05=29/H11=115 and all 1,898
baseline identities/fingerprints/anchors preserved. The preceding local run's
initial-registration refusal remains a failed checkpoint with unproven internal
cause; see hosting-lifecycle-analysis.md for precise causal limits. Renewed source
review/full/native/exact-head hosted qualification is pending at this checkpoint;
PR #75 will record completion receipts. No lease, read, role or authority changes.

The validated-clock correction records the latest successful Decision observation
outside the business savepoint, restoring append state after business rollback.
It reserves the closing-clock slot under the unchanged 2,048-event cap; a full
journal refuses all further lifecycle use, including reads. Never renew/reset or
repair that journal. Current measured corpus: 119 lifecycle / 2,322 full / 2,017
mandatory native cases, H05=29/H11=119, with every accepted baseline preserved.
Complete immutable-head review/full/native/hosted qualification is pending at
this source checkpoint; completion receipts will be posted on PR #75. Earlier
interrupted/failed runs remain diagnostic. No operational authority is inferred.

## Source-accepted T012S and current T012T preparation

Brett source-ratified #75 at dbe855cf3a41475426cd1329ca46d7b95dee2905 and
then explicitly directed governed landing when green, post-merge CI verification
and T012T preparation. Normal merge d832709a1119c17014287cd15ff8661bfd758cc4
is the clean integration with existing P1 consumer main fce58c192e93; lifecycle
runtime/native tests/feature017 content retain accepted bytes. Exact-merge ordinary
source CI run43887121548 passes full2,322 and required-native2,017, H05=29/H11=119.

Only preparation is now commissioned. Factory draft add-protected-runtime-report
owns the proposed new closed protected-report profile; feature017
hosting-evidence-plan.md/acceptance/analysis/contracts and sole tasks.md T012T01-T012T06
prepare implementation. These source tasks remain unchecked/uncommissioned until
explicit paired-profile acceptance and implementation authorization. H10's budget
anchors are not a connected qualifier; H12 is not implemented. Keep current source/
fixture reports and refusing CLI compatible; no runtime/workflow/dependency/pin
change, provider service, setup or protected dispatch follows. T012U-V/T001/T013-T015,
live report/consumer/human/domain acceptance remain separate. Feedback stays
deferred and neither historical blocked write is replayed.

## Issue #73 complete-source analysis

The Sonar source-analysis and coverage jobs also initialize openWallet/spec,
because this existing complete-assembly project scans that leg and owns
finding acceptance there. This is a source-analysis-only exception to the
runtime/validator two-line init rule. Ordinary runtime and wallet-validation
product-validation gates retain their existing root/code scoped init. OpenSpec
tooling explicitly initializes the pinned spec leg and authenticates its shared
implementation before execution; it retains the adapter pin, lock and corpus.
The analysis inventory binds all four exact Git revisions and real executable
coverage; no source omissions, runtime authority, thresholds or billing change.


### Source-analysis conformance providers

The #73 analysis job may fetch the immutable public provider revisions declared
in requirements/analysis-providers.json and execute their fixed test selections
against the actual copied consumer files. Both main admission and exact source
bytes are required. This is additional source-only conformance; it grants no
runtime, credential, broker, dispatch or operational authority. No test assertion
may be deselected or waived to produce coverage.

## T012T isolated implementation commission

Brett source-ratified factory #1332 aa1896ded7ef with wallet #76 56471096ff98
and commissioned ordered landing followed by T012T in isolation. Factory merged
as 7ad00a2c03a4 (clean integration with concurrent #1331; accepted packet and index
additions preserved); wallet merged normally as 43166dd6ebc3 with its accepted tree.
Only T012T01-T012T06 are commissioned. Internal runtime/custody observation seams
record existing checks without extra reads or changed worker inputs. Preserve
neutral APIs/pins, v1 evidence, phase clocks/budgets and operational default refusal.
T012U-V/T001/T013-T015 and every operational setup/dispatch/live acceptance gate
remain separate. Feedback stays deferred; neither historical blocked write is replayed.


## Source-accepted qualification budget continuation

Brett source-ratified factory #1334 at 7518c058ef3defb7408475cfed65807d7609d626,
then directed landing when green and continuation of T012T in isolation. It merged
as 89974846b847e1c31761792677155cc9779d400d; the accepted packet survives the
clean merge with concurrent #1327. The qualification-only private39 entry must
precede all reads on one original Decision. Preserve all other allocations,
original clocks, earliest expiries, neutral APIs/pins and default refusal. T012T
completion still requires actual hosted source positives, boundaries and cleanup;
component counts alone do not qualify it. T012U/V and operational setup/dispatch
remain unauthorized; feedback deferred and historical blocked writes unreplayed.

The T012T audit-only client binds the original registered plan/context and existing
observer TLS client without active config/RunLifecycle construction or a writer.
Only cleanup routing accepts it; qualification refuses. The shared existing pure
cleanup validator/parser retain old operation semantics. The fresh-process source
control passes after lease expiry and refuses wrong scope/worker/window use.
This is still an isolated candidate pending full/native verification and later
source publication; no T012U/V or operational commission is inferred.

## Completed T012T isolated qualification

Frozen runtime b7049e8ef20f985db26e5b7a966012161737ac7e passes2,511 full tests plus
nine subtests and all2,203 mandatory native nodes. All186 hosted-evidence cases
pass in both; prior identities/fingerprints/anchors survive, H10=75/H11=143/H12=142.
Actual positives verify owning proof and cleanup at38 reads (39 with fixture
origin), with no operational origin inferred. Independent native boundary and
external21,872-generation/ten-positive preservation audit pass; both final fixture
roots and native container are absent. See hosting-evidence-budget-realization.md
for source hashes, historical failure limits, timings and later CI-budget handoff.
Task/evidence reconciliation is documentation-only after those tests. Only T012T
is complete; candidate publication, T012U/V and all operational gates remain
separate and unauthorized. Keep setup/dispatch unauthorized, feedback deferred,
and neither historical blocked write replayed.

## T012U isolated conformance and runbook commission

Brett now commissions only T012U implementation/testing under the existing factory
hosting/issuance/report decisions. Use hosting-conformance-plan.md and the sole
tasks.md T012U entry. Preserve all2,203 baseline native nodes/anchors, neutral
APIs/pins, clocks/budgets, workflows/inputs and refusing runtime defaults. Correct
the source test runner's premature success verdict and add real pytest controls;
reconcile operator source coverage/commands and audit fixture cleanup. T012U stays
unchecked until frozen full/native and external teardown verification complete.
T012V publication/hosted CI and T001/T013-T015 operations remain separate. Keep
setup/dispatch unauthorized, feedback deferred and blocked writes unreplayed.

## Completed T012U isolated conformance and operator source runbook

Brett's T012U commission is complete at tested source
`6e2f0bfc626ab05b5b0384bc3a97d2816cfd696a`:2,523 full tests plus nine subtests,
all2,215 mandatory native nodes,64 conformance self-tests and186 hosted-evidence
cases pass with zero failures/errors/skips. Final success follows owning-source
postflight. Prior identities/anchors survive, R01=47 and all H01-H12 remain.
Operator source commands and their six Git-status shell controls pass. Independent
native boundary and21,879-generation/ten-positive preservation audit pass; final
owned fixture roots and native container are absent. See
`specs/017-protected-runtime-qualification/hosting-conformance-implementation.md`
for exact hashes, retained failed diagnostics,
scoped diagnostic helper retirement, timings and unchanged45-minute hosted-CI gate.
Final reconciliation changes documents only. Candidate remains local/unpublished;
T012V and T001/T013-T015 stay separate. Keep setup/dispatch unauthorized, feedback
deferred and both historical blocked writes unreplayed.

### T012V source publication commission

Brett commissioned candidate PR #78, hosted ordinary source CI, local Codex
review and governed budget-blocker fixes. Feature017 remains the sole task list.
The bounded corrections and delegated source-CI timing rationale are recorded in
`hosting-conformance-implementation.md`. Owner source ratification and all
T001/T013-T015 operational decisions remain open; setup/dispatch unauthorized,
feedback deferred and neither historical denied write may be replayed.

### Historical T012V main #77 publication candidate

Executable source `05101d15ad407264a96818c8527229f1f0273ac0` passes 2,761 full tests plus 11
subtests and all 2,364 mandatory native nodes, with every prior identity retained.
All nine local expert roles clear the source. Independent final audit verifies
24,537 generation observations and ten preservation cases; final fixture
roots and native container are absent. The final source handoff is documentation
only; exact-head hosted CI and owner ratification remain PR #78 gates. See
feature017 hosting-conformance-implementation.md and operator-source-runbook.md.
Main #77 analysis/coverage controls remain required. No operational selection or
grant follows; setup/dispatch unauthorized, feedback deferred, blocked writes
unreplayed.

### Historical T012V accepted-main #79 integration plan

Main #79 advanced after candidate3ceb qualification. Integrate its accepted
shared-tool/pin/runtime fixes under the existing T012V task and the bounded
plan in feature017 hosting-conformance-implementation.md. Old051/3ceb receipts
remain historical; the new integration needs fresh collection/review/full/native/
cleanup and hosted qualification before owner ratification. Preserve both matrix
corpora and every accepted incoming baseline. Exact neutral pins now050bede root,
ed567ed code and0fe3151 spec; shared OpenSpec tooling authenticates the spec leg,
while runtime product validation stays code-only. Explicit qualification ownerbb0
is separate. No setup/dispatch, feedback or blocked-write replay is authorized.

### Historical T012V main #79 qualified source candidate

Frozen executable `223e2c825494041b9104c475a8a294483f6fcaf2` passes 2,781 full tests plus
11 subtests and all 2,369 mandatory native nodes; all 366 input hashes and prior
identities remain. Nine integration expert roles clear it. Independent final
audit checks 25,005 generation observations and ten preservation cases;
final fixture roots/native container are absent. Shared OpenSpec tooling uses
authenticated pinned spec source; product/runtime validation stays code-only.
Feature017 hosting-conformance-implementation.md records exact source/pins and
limits. Final doc-only reconciliation retains qualified executable bytes; fresh
final-head hosted CI/Sonar and owner ratification remain PR #78 gates. No
setup/dispatch, feedback or blocked-write replay is authorized.

### Historical T012V main #80 and advisory clarity plan

Accepted main #80 advances pins/tooling/tests after the completed main #79
qualification. Existing T012V and feature017 hosting-conformance-implementation.md
govern the bounded assertion/preparation/branch/media-type cleanup. Preserve
all oracles, case identities, wire profiles, budgets, broad cancellation/privacy
boundaries and lexical resource ownership. Fresh review/full/native/cleanup and
hosted qualification are required; earlier receipts remain historical. No
setup/dispatch, feedback or blocked-write replay is authorized.

### Historical T012V main #80 qualified source candidate

Frozen executable `f9b9bd5a798dd251f404a8e1ed1660c9378af23e` passes 2,781 full tests plus
11 subtests and all 2,369 mandatory native nodes; all 366 frozen inputs and prior
identities remain. Nine exact-head source roles clear the main #80 integration
and bounded clarity changes. Independent final audit checks 25,018 generation
observations and ten preservation cases; final fixture roots/container are absent.
Neutral root/code/spec are 819de672/fb132776/0fe3151c; separate qualification owner
remains bb0e9dae. Feature017 hosting-conformance-implementation.md records immutable
identities and actual evidence. Final documentation retains qualified executable
bytes; fresh final-head hosted CI/Sonar and owner source ratification remain
PR #78 gates. T001/T013-T015/setup/dispatch remain ungranted; feedback deferred
and neither blocked write replayed.

### Historical T012V exact-refusal clarification plan

The existing T012V commission covers the two Sonar S3403 reliability findings
through a private shared exact-refusal predicate and 20 independent adversarial
controls. The governing bounded plan is recorded in feature017
hosting-conformance-implementation.md. Preserve original predicate/evaluation
order, lazy reservation absence, catch scopes, all source/case identities and
clock/read/wire/authority limits. Earlier 1146747 full/native passes are historical;
fresh source/full/native/cleanup/CI/Sonar and owner acceptance remain gates.
T001/T013-T015/setup/dispatch ungranted; feedback deferred, blocked writes unreplayed.

### Historical qualified T012V selected-port deadline correction

Code candidate `bf0839732d764c2848a4981179e999a44f769d53` incorporates the test-only selected-port correction
and accepted main #84. Original runtime 10s/private39, loaded credentials/four
real RPCs, fixed errors, source pins and protected defaults remain. Complete 22
probe cases pass untraced and under pinned CTracer; five deliberate mutants fail
the intended identity/deadline/server-prefix/arming assertions. The complete
ordered 2801/2389 corpus and static fingerprints remain. Current exact-head
source/document review, full/native/cleanup and hosted CI/Sonar receipts are
maintained on PR #78; no success is predeclared. See feature017
hosting-conformance-implementation.md. T012V/owner acceptance and
T001/T013-T015/setup/dispatch remain ungranted; feedback deferred and blocked
writes unreplayed.

### Historical T012V accepted-main #85/#86 integration

Accepted main `a6a327a36046e130c95b2e654f3b4b5135d9d5de` advanced during the
completed 064103a5 qualification. Its receipt remains historical exact-source
evidence. Integrate accepted runtime/shell clarity and stage-teardown failure
aggregation with T012V private39 and exact probe/claim guarantees, following
feature017 hosting-conformance-implementation.md. Fresh review/collection/full/
native/cleanup/hosted CI and Sonar at the new frozen head are required. No
source acceptance or operational authority is inferred; setup/dispatch remain
unauthorized, feedback deferred and blocked writes unreplayed.

The current code candidate is `1728117f3dbe0ebb3fbeb408613e3d04c69067fc`; exact ordered 2801/2389
collection and all 135 focused readback controls pass. Preserve the 371 non-document
inputs through final source-checkpoint review. Full/native/cleanup/CI/Sonar remain
fresh final-head requirements tracked on PR #78, not success claims here.

### Historical T012V accepted-main #87 integration

Accepted main 001c8321884259b35f17adc3d6cd9f623ad1a947 refactors lifecycle and
validation responsibilities. Both typed LifecycleStores/LifecycleActors constructor
callers are already adapted upstream; qualifier uses the resulting lifecycle and
its preserved methods. Merge cleanly and retain original wire/pin/clock/private39,
cancellation, privacy and resource-ownership guarantees. Follow feature017
hosting-conformance-implementation.md; fresh review/full/native/cleanup/CI and
Sonar remain required before owner source ratification. Setup/dispatch stay
unauthorized, feedback deferred and blocked writes unreplayed.

The current code candidate is `cf21b62b20237d8644aff8a5ae45074c011bbc1c`; collection 2811/2389 preserves
all prior IDs/order, adding ten accepted pin controls outside the native matrix.
Ten pin and two actual qualification/lifecycle compatibility controls pass. Preserve
373 non-document inputs through final ten-document checkpoint review. Fresh
complete full/native/cleanup/CI/Sonar and owner ratification remain PR #78 gates.

### Historical T012V accepted-main #88 provider integration

Accepted main 6cc8c4e40644692dfdf47cda520ae5076eec6f6a refreshes the coherent
neutral root/code/spec and admitted OpenSpec/shape provider records. Source
identities are 3618980408eaaccaa31ec41da32f77cf86fb99f9/6fb72ed4c820d927775ccb698c5cfbd8adff71d7/878293fb3ed84073dd7e285f56f4fee62413297e. Eight contract
digests and CLI package/lock addresses remain unchanged; qualification owning
code stays separately selected at bb0e9dae. Consume the accepted pins without
forking upstream sources; ordinary product validation remains code-only and
shared tooling explicitly authenticates its spec leg. Fresh review/collection/
full/native/cleanup/CI and Sonar remain required; setup/dispatch unauthorized,
feedback deferred and blocked writes unreplayed.

Current code candidate `e92a7728810b51d5537a39b0c12d998f1818baf8` retains 383 regular inputs before final
ten-document checkpoint review; 373 other inputs must remain byte-identical.
Collection 2811/2389 retains IDs/order/fingerprints, and ten pin/two real lifecycle
controls pass. Fresh complete qualification/cleanup/CI/Sonar and owner ratification
remain PR #78 gates. No source acceptance or operational grant is inferred.

### Historical T012V accepted-main #89 source

Code candidate `bf87eaefc74e876431d7a7c0e09b8802cb126e77` consumes the published typed predicates and
wallet root 38f9d0cb, with code 6fb72ed4/spec 878293fb and explicit owner bb0e9dae
unchanged. Nineteen recipe file hashes/Bash syntax and ten pin/two actual lifecycle
controls pass; collection 2811/2389 retains all prior IDs/order/native fingerprints.
Freeze 384 inputs, with 374 non-document bytes preserved through final checkpoints.
Fresh review/full/native/cleanup/CI/Sonar and owner ratification remain gates.
Setup/dispatch unauthorized, feedback deferred and blocked writes unreplayed.

## Historical #78 source acceptance and T013 handoff

Brett source-ratified #78 at `92545e32b4e5f950209cc7312a1a6309055b299d`, directed landing when green and this T013
refresh. Normal merge `2997c8a238f6de6f74488fed933371d7f97d3ca5` has tree `a36a7d66955aa841a3b9aa1e61ecd1a1efad04a9`, carrying only the reviewed
#90 historical backlog documentation alongside the ratified candidate. The source
qualification receipt retains 2,811 full cases plus 11 subtests, 2,389 native cases,
zero failures/errors/skips, independent cleanup and exact-head CI/local review;
merged-main CI is tracked separately, never inferred from PR results. See
`specs/017-protected-runtime-qualification/evidence.md` and the current T013 packet.

T012V records the actual owner source act and documentation handoff. T001 and
T013/T014/T015 remain unchecked. The hosted static-v2 and algorithm source is
accepted in isolation; concrete deployed bindings, principals/state/watchdog,
actual provider evidence and exact executing source remain unselected. Default
operational bindings still refuse before outputs/OIDC. No setup, dispatch, token
mint, freeze, grant, protected-machine/human/domain acceptance or blocked write
is authorized by this refresh. Feedback deferred. Earlier candidate checkpoints
are historical; this source-CI integration permission selects no operational
main-update policy.

## Commissioned isolated SQLite staging-journal correction

Brett source-ratified #91 at cf2c0eee65fc55c1606be4c19f4b61eda2185fab; it
merged normally as bd1b0d8b6ec249f7ed37932a552e5674d046a912 with the accepted
tree. Only the existing feature017 implementation correction in
`specs/017-protected-runtime-qualification/sqlite-journal-plan.md` and sole
task T012VJ is now commissioned in isolation. Preserve all baseline case IDs,
security checks, schema/pins, deadlines, budgets and default refusal. Fresh
exact-source full/native qualification and owned-fixture cleanup are required.
No publication, fix ratification, setup/dispatch or live provider authority is
inferred; feedback deferred and blocked writes unreplayed.

## Accepted main #92 compatibility integration

Integrate accepted #92 main `22bc7bdf6298c043377528c0c289ca26e51cbb07` into
the isolated T012VJ candidate per the owner's incoming-change instruction.
Qualification/probe/CLI retirement and exception boundaries are inherited from
that accepted main; the SQLite correction/tests/matrix remain byte-identical.
Follow feature017 sqlite-journal-plan.md. Old runtime61 results and failed or
superseded native attempts stay historical; fresh exact-source full/native and
cleanup are required. No pins/workflows/budgets/defaults or operational authority
change; setup/dispatch unauthorized, feedback deferred, blocked writes unreplayed.

## Qualified isolated SQLite staging-journal candidate

Integrated runtime c32ac5147fd504426483681a11dc8b60f4aac0fc on accepted main #92 passes
2,859 full cases plus 11 subtests, all 2,437 mandatory native cases and seven
ordered local gates with zero failures/errors/skips. All 387 frozen input hashes
match. Prior identities/fingerprints/anchors and neutral/owner refs remain.
Independent audits verify ten preservation cases and owned roots/containers
absent. Feature017 sqlite-journal-plan.md records exact red/green qualification
and historical failed/diagnostic/superseded attempts without promoting them.
T012VJ is complete in isolation. Fix publication, hosted CI, local expert review
and owner source acceptance remain later gates. T001/T013-T015/setup/dispatch
remain ungranted; feedback deferred, blocked writes unreplayed. This later
five-document reconciliation preserves all other qualified runtime inputs.

## SQLite correction publication and accepted main #93

Brett commissions the SQLite journal correction PR, hosted CI, local Codex expert
review, finding resolution and presentation for source ratification. This supplies
no merge, source acceptance or operational grant. Integrate accepted main #93
`dbbbafab8cb5ab093360b5e12044a7a35b156cc5`, which consumes neutral root
`8be8a2a6af125058ffe956cafbf1e62858d82dd9` for the reviewed decimal worktree
selector repair. Neutral code/spec and explicit qualification owner stay unchanged.
The SQLite runtime, new test module and matrix bytes remain identical to the
completed c32ac514 qualification. Earlier exact-source receipts remain historical;
fresh integrated full/native qualification, cleanup, hosted CI and nine local
Codex expert roles are required for this publication head and recorded on its PR.
Feature017 T012VJ remains the sole correction task; T001/T013-T015 stay unchecked.
Setup/dispatch unauthorized, feedback deferred, blocked writes unreplayed.

## Publication S9073 assertion correction

The first #94 hosted run 44355407295 at 9f462857c5e1176ae591087bc4fdcfab961e38f7
passes all five jobs and all six original conditions (100% new coverage), but
direct analysis c30c54cd-0576-4b92-8c6d-c0b619a181b9 retains four S9073 findings:
AaHv1OauqAoMpLQXSFXl, AaHv1OauqAoMpLQXSFXm, AaHv1OauqAoMpLQXSFXn and
AaHv1OauqAoMpLQXSFXo. That head is not presented for ratification. Split those
four composite assertions, retaining every condition, fixture, test identity,
matrix fingerprint and runtime byte. No rule suppression or scan/gate change.
This remains existing T012VJ publication finding resolution under the owner
commission. Earlier exact-source qualification and review remain historical;
fresh exact-source full/native, cleanup, local Codex follow-up and hosted CI/
analysis readback are required. T001/T013-T015/setup/dispatch stay ungranted;
feedback deferred, blocked writes unreplayed.

## Current #94 source acceptance and T013 refresh

Brett Heap source-ratified [openXwallet #94](https://github.com/opensoft/openXwallet/pull/94#issuecomment-6991564275) at `b1430cedbf555afbfbe0a6de8a41e9208cfc145a`
and directed landing when green, independent post-merge verification, then this
T013 refresh. It merged normally as `255035a41761a88293e565573a319dc112a48522` on `2026-11-18T21:03:25Z`,
with tree `f40947b61c1a9a8a073b1ffe40fc9f042c20daad` exactly equal to the ratified tree.
The [source qualification](https://github.com/opensoft/openXwallet/pull/94#issuecomment-6989959898) and [independent main receipt](https://github.com/opensoft/openXwallet/pull/94#issuecomment-6993081869)
remain separate. T012V/T012VJ are accepted source; T001/T013/T014/T015 remain
unchecked. No operational `accepted_commit`, deployment, principal,
credential, appointment or grant is selected by this source act or its later
documentation descendant.

The [current handoff](specs/017-protected-runtime-qualification/evidence.md#2026-11-18-94-source-acceptance-and-t013-refresh) records actual merged-main CI, current pins/workflow hashes and fresh read-only repository facts. The documentation candidate selects no executing workflow SHA, service, credential or grant. Source handoff publication, hosted CI, local Codex review and finding resolution are now commissioned; owner source ratification and all operational decisions remain separate. Earlier candidate labels are historical; feature017 tasks.md remains the sole list.

Ordinary source-CI reruns supply no protected-operation authority. The accepted
operational broker still permits only its separately approved first run attempt;
no retry/reset, grant, dispatch selection or source-update policy is inherited
from source verification. Default operational_bindings() still refuses
workflow-operational-host-unselected before outputs/OIDC. Setup, one dispatch,
actual-run authority and cleanup/readback remain separately NOT GRANTED.

## Current T013-S1 design acceptance and P3 planning only

Brett accepted adapter081dad41cfb42a3bc58aefe356bb6d424fab871d with
consumer049ede52b6ee03f15a57ecf7cdb9517002d8714f as design basis only; roles
subject to confirmation. Prepare factory add-protected-runtime-azure-composition
and feature017 P3 subplan/research/model/interfaces/acceptance/tasks. T013P01-P09
are proposed/uncommissioned, not implementation permission. Keep original
operational_bindings/default entrypoint, profiles, pins, budgets and existing
checkboxes unchanged. No implementation/setup/dispatch, workload token, feedback
or blocked-write replay. T013/T014/T015 and consumer058 T002 stay gated.

## First bounded P3 source slice

Brett source-ratified factory1353 c2dfbbcc6fa6, adapter96 9a087cf8c146 and
consumer586 aa4a50eea567; all landed in order with equal ratified/merged trees
and green independent main CI. His later instruction commissions isolated
T013P01/T013P02 only. See feature017 p3-namespace-implementation.md and tasks.md.
New code is an unaccepted local source candidate; the conditional storage test
double is not a Blob deployment. Later P3 tasks and T001/T013/T014/T015, roles,
consumer T002 and human acceptance remain gated. Preserve old runtime/profile/
workflow/pin bytes and every prior matrix identity/fingerprint/anchor. Default
operational_bindings still refuses. Setup/dispatch unauthorized; feedback deferred;
historical blocked writes unreplayed.

## First P3 slice candidate review commission

Brett commissions candidate PR #97, hosted source CI and local Codex expert
review, resolution of findings and presentation for source-only ratification.
Only T013P01/P02 is commissioned. Later P03-P09, setup/dispatch and live acceptance
remain separate; feedback stays deferred and blocked writes remain unreplayed.


## Historical #97 source acceptance and bounded P03 preparation

Brett source-ratified #97 at 33a00d474621921a1bd22ac95ba8f254d9875c11 and directed
landing when green, independent post-merge CI, then next bounded P3 preparation.
Normal merge 3ca99fc79ab6ce5339cfd9e347559b241f7a57b8 has the identical ratified
tree; main run44598396381 and its actual unchanged Sonar gate passed.
Feature017 evidence.md records the exact owner act, head/tree, qualification,
review/advisory dispositions, main analysis and retained manual baseline.

Only T013P03 preparation is commissioned now; follow p3-provider-plan.md and the
sole row in tasks.md. Do not implement provider.py or mark P03 complete.
The legacy public-IP/Detach shape and credential-transport limits are explicit
compatibility gates, not permission to strip provider fields or relax old readers.
Preserve runtime/profile/workflow/pin/dependency bytes and all task checkboxes.
P04-P09, T001/T013/T014/T015, unconfirmed roles, consumer058 T002 and independent
human acceptance remain gated. Setup/dispatch unauthorized, feedback deferred,
historical blocked writes and rejected optional publication helpers unreplayed.
