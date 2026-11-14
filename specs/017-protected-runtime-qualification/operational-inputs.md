# T013 Operational Selection Packet

Status: GitHub bootstrap source accepted in #65; T012M handoff complete; T013 selections pending; setup/dispatch NOT GRANTED
Updated: 2026-11-14
Governance: `opensoft/openXfactory`, `prepare-protected-runtime-qualification`
Bootstrap amendment: `fix-protected-runtime-dispatch-bootstrap`
Implementation list: [feature 017 tasks](tasks.md); T013 remains an owner act
Decision draft: [scoped authorization](scoped-authorization.md)
Accepted bootstrap and hosting gates: [bootstrap record](workflow-bootstrap.md)

## Current source acceptance and next decision

Brett source-ratified [adapter #65](https://github.com/opensoft/openXwallet/pull/65#issuecomment-6881983735) at `ab34ff4ec4fe27d56c8fd09c99614785c23e760f` and directed landing when green, then T012M completion and T013 refresh. It merged normally as `366533bed77293b096b0a7dbda61399ff5dbafe5` on 2026-11-14 at 18:09:45 UTC. The merged tree `669a1b431f17d360fcf827a749a756e863ec9ed8` equals the ratified tree. Factory design #1314 is accepted at merge `3432baf6d929112be283d3daa1a4330a4130ab64` (tree `040d1de2563c5b826ebd93e1c14f6bc9d24688c8`); adapter #64 is its accepted preparation baseline. Earlier #1311/#60 and #1312/#61/#62 remain historical provenance.

#65 supplies the separate bootstrap verifier/token/TLS client, durable dispatch-attempt journal/broker, current provider/source/phase/review correlation and opt-in admission session. T012G–L source work is accepted; T012M reconciles it here. Local qualification passed 1,641 full cases and 1,339 mandatory native cases without skips. Exact ratified-head hosted CI passed 1,638 full cases with three documented shallow-history skips and all 1,339 mandatory cases without skips; dedicated full-history jobs passed. Local Codex/expert review closed all findings; the owner waived the hosted connector request. Sonar passed. No separate merge-triggered adapter run was emitted on this readback; do not relabel PR checks as post-merge CI.

These are source/fixture baselines, **not an approved execution `accepted_commit`**, deployment, configuration or grant. This documentation refresh also changes the Git commit that a later workflow could execute; identical workflow file content does not select that future `github.workflow_sha`. Reconcile and accept the exact current main SHA after all required hosting source integration before any separately authorized dispatch.

The [T013 decision packet](t013-decision-record.md), [authentication handoff](bootstrap-authentication-plan.md) and [scoped authorization](scoped-authorization.md) now distinguish accepted adapter source from unselected operational hosting/issuance and source-update controls. No executable config, issued preauthorization, credential or setup/dispatch command is produced. T013/T014/T015 remain incomplete; every operational stage remains NOT GRANTED.

## Earlier accepted source baselines

Brett ratified factory #1311 at `6dadf188a0afa22e3c205561299f6045a9c95359`
with adapter #60 at `78e7bbeabca250073d5896154ccc99bb163116cc` for source
acceptance only. Both merged after all runnable exact-head checks passed and no
unresolved review thread remained. Each merged tree equals its ratified tree:

| Source | Accepted merge | Tree | Landing |
| --- | --- | --- | --- |
| [openXfactory #1311](https://github.com/opensoft/openXfactory/pull/1311) | `f2fb60f04c8229f4343e25a0155418f2f737d73a` | `6e7bbe32e25e4c18692600677b819d41787e072f` | 2026-11-13 23:20:57 UTC; standing self-authored-PR approval exception |
| [openXwallet #60](https://github.com/opensoft/openXwallet/pull/60) | `61fbe41f7e08e831e0b15c2c97ea6ff386f587f3` | `b990b7694f8a635d399e1bf4ca7100083f00f0f1` | 2026-11-13 23:21:59 UTC; normal merge |

Factory post-merge CI is verified at the exact merge above: all 5 observed main-triggered Actions runs passed, including [pytest-suite 43526439944](https://github.com/opensoft/openXfactory/actions/runs/43526439944). Its pytest result was **10391 passed, 6 skipped, 338 deselected, 9 warnings, 745 subtests passed**. The JUnit guard recorded `selected=11142`, `passed=11136`, `skipped=6`, `failures=0`, `errors=0`; its named freshness check passed. This is independently observed main CI, not a reuse of the PR run. Main Sonar reported `neutral` / `Quality Gate not computed`; the source PR quality gate is a separate result.

Adapter source qualification remains the retained 1,348 local passes and 1,046
native network-none passes, all zero failures/errors/skips. Hosted adapter CI
passed 1,345 general cases with three documented shallow-history skips and all
1,046 required conformance cases without skips; dedicated full-history carve
(84) and neutrality/pruning (60) suites passed. No main-triggered adapter run
was returned during this refresh. These are source/fixture results. GitHub Codex
review was explicitly requested and quota-refused; the nine-role local review
remains the review evidence, not a completed connector review.

The adapter's neutral pin remains assembly
`b0af7c2ce53d63786a08a20aa3602a6f90345606`, code
`72313daab1f229c049cb90998931564c1904dbbc`. Separately selected portable
registry/custody integration code remains
`bb0e9dae89a771b05f6c235d0a77237288b95c85`; it does not replace that pin.
No source acceptance here selects a deployment, image, service, credential or
runtime configuration. Final sources must include later accepted hosting clients.

## Accepted workflow content and dispatch interface

Current source-only baseline: adapter merge `366533bed77293b096b0a7dbda61399ff5dbafe5`. Hashes below are recomputed from immutable Git blobs; no workflow invocation is selected:

| Relative path | Content SHA-256 |
| --- | --- |
| `.github/workflows/protected-runtime-qualification.yml` | `03951b10405b3d81b394db1a1915586f3e475b8337351d140e00d51340916bf8` |
| `.github/workflows/protected-runtime-qualification-run.yml` | `1c75e0f777a60f6bc21205c2164c302d507ad08d8e89e6fb66c0b221fbfb252a` |
| `scripts/prepare-protected-runtime.py` | `484d49357141078768602deee6100c5222fa4ce5e4bc6261ccf5a7f9993c89a8` |
| `scripts/workload_factory_binding_runtime/bootstrap.py` | `5d8548ffde04a6b4771d2b878ac4d4af5b5c423999f2df1e38ca71515dde6458` |
| `scripts/workload_factory_binding_runtime/workflow.py` | `dd19229cd3d41c6557040d15f3079f98d62f3d725c9afbb8ab2cd069007fd1b7` |
| `scripts/workload_factory_binding_runtime/github_bootstrap/broker.py` | `f9f03bebfac4aa0dde3450c9d0e136e8d310e16d6a20f5077e628137e883818a` |
| `scripts/workload_factory_binding_runtime/github_bootstrap/controller.py` | `4e1d63f15d65218ceef3eba05dcf578a516a63812d3ebc2afab38c6697a7ba5d` |

The manual caller/local reusable take exactly `accepted_commit`,
`selection_digest`, `preauthorization_ref`. The static profile is
`openxfactory-dispatch-selection-internal-v1`; its closed document contains
`profile` and `configuration`, committing every runtime field except launch
run ID/attempt. The full runtime profile
`openxfactory-protected-runtime-internal-v1` still requires both assigned fields
and an independently approved full `config_digest`. The old dispatch digest/grant
inputs are refused. No static digest or configuration is approved by this packet.

Fresh independent bootstrap must bind selected source, repository, case,
preauthorization, actual run/attempt, full config digest and operation grant.
Existing environment/protection, source, authorization, scheduler and active
lease checks follow, bounded by the earliest deadline. Bootstrap/admission repeat
after environment approval. Accepted #65 supplies a separately scoped bootstrap OIDC
client/verifier and durable dispatch-attempt correlation in isolation; the earlier
portable fixture alone does not. Actual provider claims/behavior, authenticated
hosting callbacks, credential issuance, deployed durability and administrative
independence remain unqualified. No worker hash, output or boolean supplies them.

The earlier input circularity is resolved in accepted source. The default
operational factory still refuses `workflow-operational-host-unselected` before
environment outputs/OIDC. Qualify/cleanup clients and protected-machine receipt
promotion require separate source integration/review before any operative run.

## Fresh repository and protection readback

Read-only GitHub API inspection at `2026-11-14T18:11:54.230954+00:00` established the following. These
observations must be reacquired for an eventual operational decision/use:

| Fact | Observed value | Operational meaning |
| --- | --- | --- |
| Qualification repository | `opensoft/openXwallet`, public; default `main`; ID `1347887821` | Accepted caller is here; it is not a codeXfactory workflow |
| Owner | `opensoft`, ID `638385` | Exact immutable identity binding |
| Authenticated account | `brettheap`, User ID `1513478` | Readback only; no dispatcher/reviewer appointment |
| Environment inventory | Only `copilot`, ID `20677426348` | Preserve it; no pilot environment selected/created |
| `copilot` protection | No rules, admin bypass enabled, no deployment branch policy | Ineligible under the accepted protection profile |
| Default workflow token | `read`; PR review approval disabled | Job-specific effective permissions remain separate readback |
| OIDC subject settings | `use_default: true`, `use_immutable_subject: true` | Record actual provider settings; do not assume a name-only subject |
| OIDC configured prefix | `repo:opensoft@638385/openXwallet@1347887821` | Exact full environment/workflow subject still needs selection/corroboration |
| Protected workflow identity | ID `417795073`; `.github/workflows/protected-runtime-qualification.yml`; active | Workflow exists; this is not operational admission |
| Local reusable workflow | ID `417795071`; `.github/workflows/protected-runtime-qualification-run.yml`; active | Same-commit caller binding remains required |
| Both protected workflow run counts | `0` each | No protected qualification has been dispatched |

OIDC settings came from the read-only repository
`actions/oidc/customization/sub` endpoint. This reads configuration; it does not
mint or observe a workload token. Do not derive an approved complete `sub` or
audience from the prefix alone, alter the provider settings, or create federation
to make a guessed subject work. Later acceptance must corroborate exact actual
claims under separately approved authority. The
[GitHub OIDC API](https://docs.github.com/en/rest/actions/oidc#get-the-customization-template-for-an-oidc-subject-claim-for-a-repository)
documents the configuration-read endpoint.

## Operational selection matrix

Retain the earlier portable reference-service route, qualified in isolation.
The proposed operational shape remains a dedicated disposable **nonproduction** Linux
deployment, with GitHub-hosted orchestration and independently administered
runtime services. No provider, tenant, host/cluster/namespace or administration
boundary has been selected. An existing bench or production target is not an
implicit deployment choice.

| Category | Accepted constraint / prepared proposal | Missing operator selection or acceptance |
| --- | --- | --- |
| Purpose | Machine possession prerequisite for codeXfactory feature 058 T002 | Exact case identifier and accountable owner; consumer acceptance separate |
| Final source set | Accepted factory/bootstrap/adapter baselines above | All eight source roles, relative content paths/digests, dependencies, composition, deployed image/launch measurements and later hosting client source acceptance |
| Environment | Proposed new `wallet-mfa-pilot-qa` in the exact qualification repository | Approved name and create scope; actual assigned ID and effective protection after authorized setup |
| Reviewer/dispatcher | 1–6 distinct User/Team reviewer IDs; self-review prevented; admin bypass disabled; exact `refs/heads/main` restriction | Distinct eligible reviewer and dispatcher, membership/permission readback; Brett cannot approve his own initiated run |
| Bootstrap/controller | Accepted #65 source provides separate purpose/phase OIDC plus broker/journal/API correlation; first attempt only | Authenticated bounded approval/source/environment/materialization callbacks, controller endpoint/CA/principals, token-request transport/worker exclusion, actual claims/API behavior and deployed store initialization/retention/readback |
| Workload/issuer | Fixed GitHub endpoints; accepted bootstrap audience `urn:opensoft:openxfactory:bootstrap-admission:v1`; same-commit caller/reusable | Complete preflight/protected subjects, distinct proof audience, phase/source/job/ref/measurement policy and actual claim corroboration; no token mint for discovery |
| Source-update control | Accepted source admits `coordinated` or `bounded-residual-exposure` policy values | Owner must select and accept implemented coordination controls or exact residual-start exposure/credential boundaries; enum label alone supplies neither |
| Broker/App and originating human | Broker alone resolves repository Actions-write credential; controller/readers are read-only; human originator retained separately from App actor | Repository-only installation/permission/issuance/revocation refs, administrator, opaque credential resolver, originator and eligible human reviewer IDs; provider scope is broader than one workflow invocation |
| Hosting/control plane | Nonproduction immutable accepted runtime; bounded authenticated worker channel | Exact provider/account/host or cluster/region/namespace IDs, network/OS policy and independent administrative ownership |
| Supervisor | Worker cannot read keys/policy, alter observation or modify measured launch sources | Named administrator/principal/key/policy refs and actual OS/network/process denial evidence |
| Gate/custody | Only the approved confined gate holds narrow signer capability; one bounded proof | Deployed gate/credential issuance/owning custody identities and valid direct worker-signing denial |
| Services/current authority | Exactly records, challenge, registry, custody, supervisor, worker channel and janitor roles | Service/principal/credential refs and trust digests, actual current policy/challenge/record authentication and independent approval/readback clients |
| State | Expected initialized private replay store; retained reservations; no silent reset | Storage/initialization/retention/recovery refs and receipt, access controls and active-scope recovery policy |
| Lifecycle | Independent janitor/scheduler/readback services ready before dispatch; full-config-bound plan/lease registered after assigned run and before admission | Named independent principals, plan/lease/cleanup/receipt-retention refs, exact generation scope, deadlines and preservation allowlist |
| Setup/dispatch authority | Separate target setup, one dispatch and actual run/attempt grant | Resource/action allowlist, budget/window/expiry, setup/dispatch actor and decision refs, preauthorization and independently approved static digest |
| Actual run authority | Full config digest and `qualify-existing-resources` grant after assigned run/attempt | Actual run identity, fresh independently approved full config/grant, lease/scheduler/protection/source readback; no prediction or inherited rerun grant |
| Qualification/receipt | Accepted source/fixture checks remain evidence within their scope | Real P01/deployed G02/G03/L01, live qualification/cleanup clients and protected-machine receipt source promotion; human/domain handoffs separate |

The bootstrap reader is a separately selected trusted hosting capability; this
amendment does not add an eighth role to the runtime `services` grammar. Bootstrap,
environment, authorization, scheduler and cleanup readback clients all need actual
authentication and administration outside worker control. Different reference
strings do not establish that separation. Only non-secret references belong here.

## Decision sequence and remaining gates

First select the nonproduction target, responsible administrators and distinct
dispatcher/reviewer roles, then review the concrete hosting/authentication,
qualification/cleanup and protected-receipt source integrations. Complete the
[authorization draft](scoped-authorization.md) for that exact source and target.
Authorize setup only through a separate explicit decision; created-resource
identities and actual protection/readback are prerequisites for a later dispatch.

After all rows and integrations are accepted, approve the static selection and
preauthorization independently for one dispatch. The accepted #65 broker source must be connected to independently selected/qualified
hosting, credentials and retained state; it durably reserves/consumes the one
dispatch attempt before external I/O. Source acceptance alone grants no invocation;
a lost response or crash never permits automatic retry/reset. This future operational dispatch
phase is distinct from the portable reference authority's actual-run binding.
Once assigned, independently
bind the final full config and current grant to its exact run/attempt. A changed
source/ref, time window or selection requires reconciliation; a rerun never
inherits authority. If `main` has moved, reconcile its exact workflow SHA before
dispatch. This packet emits no executable runtime configuration or grant.

T013/T014/T015 remain unchecked. No environment, service, credential or provider
resource is created/modified here. Source acceptance and post-merge CI do not
authorize setup, dispatch, proof use, human approval or domain effects. Feedback
stays deferred; neither historical blocked write was replayed.
