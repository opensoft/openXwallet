# T013 Operational Selection Packet

Status: source-accepted portable reference; T013 decision preparation; setup/dispatch NOT GRANTED
Updated: 2026-11-14
Governance: `opensoft/openXfactory`, `prepare-protected-runtime-qualification`
Bootstrap amendment: `fix-protected-runtime-dispatch-bootstrap`
Implementation list: [feature 017 tasks](tasks.md); T013 remains an owner act
Decision draft: [scoped authorization](scoped-authorization.md)
Accepted bootstrap and hosting gates: [bootstrap record](workflow-bootstrap.md)

## Current source acceptance and next decision

Factory #1312 and adapter #61/#62 landed in the ratified order, with unchanged
ratified trees. See the [owner/landing record](evidence.md#2026-11-14-source-ratification-and-ordered-landing).
The accepted portable reference is described in [portable authority](portable-authority.md).
The earlier bootstrap baselines below remain historical provenance; the current
adapter source merge is `425606899116c4e7fe5d3c6fe3382c058081336b` and current
factory source merge is `6604b55b980cba0c507f1e9c5de9b715282b5c35`.
These are source baselines, not an approved execution `accepted_commit`.

The concrete next decisions and dependency order are in the
[T013 decision packet](t013-decision-record.md). The proposed authenticated
GitHub correlation path and its remaining source/issuance gates are in
[bootstrap authentication preparation](bootstrap-authentication-plan.md).
Neither document supplies a runtime config, grant, credential or setup/dispatch
command. T013 remains incomplete and all operational authority stays NOT GRANTED.

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

At adapter merge `61fbe41f7e08e831e0b15c2c97ea6ff386f587f3`:

| Relative path | Content SHA-256 |
| --- | --- |
| `.github/workflows/protected-runtime-qualification.yml` | `03951b10405b3d81b394db1a1915586f3e475b8337351d140e00d51340916bf8` |
| `.github/workflows/protected-runtime-qualification-run.yml` | `ae525cd1ba76296684fb0b5eb15f56bf4cf796d112c88e8d0563c55774dce84b` |
| `scripts/prepare-protected-runtime.py` | `8dbc140a6dcdd6f06d808c2b9215c5c17dbc235e597987c3e9171ea21e900f63` |
| `scripts/workload_factory_binding_runtime/bootstrap.py` | `5d8548ffde04a6b4771d2b878ac4d4af5b5c423999f2df1e38ca71515dde6458` |

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
after environment approval. The accepted reference now supplies atomic preauthorization consumption in
isolation. Actual GitHub authentication, credential issuance, deployed durability
and administrative independence remain hosting qualification requirements. No worker hash, output
or boolean can stand in for either.

The earlier input circularity is resolved in accepted source. The default
operational factory still refuses `workflow-operational-host-unselected` before
environment outputs/OIDC. Qualify/cleanup clients and protected-machine receipt
promotion require separate source integration/review before any operative run.

## Fresh repository and protection readback

Read-only GitHub API inspection refreshed on 2026-11-14 established the following. These
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
| Protected qualification workflow runs | `0` | No protected qualification has been dispatched |

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
| Bootstrap authority | Accepted reference provides durable atomic one-preauthorization/one-run-attempt binding; fixed fixture profile only | Administrator/principal/client/trust/credential refs, actual GitHub context authentication, authoritative atomic consumption/revocation and freshness/readback evidence |
| Workload/issuer | Fixed GitHub issuer/discovery/JWKS; same-commit caller/reusable | Explicit audience, complete configured subject, exact claims/ref/source/measurement policy; preserve observed immutable prefix semantics |
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
preauthorization independently for one dispatch. A separately source-approved
broker must durably reserve/consume the one dispatch attempt before external I/O;
a lost response or crash never permits automatic retry/reset. This future dispatch
phase is distinct from the accepted reference authority's actual-run binding.
Once assigned, independently
bind the final full config and current grant to its exact run/attempt. A changed
source/ref, time window or selection requires reconciliation; a rerun never
inherits authority. If `main` has moved, reconcile its exact workflow SHA before
dispatch. This packet emits no executable runtime configuration or grant.

T013/T014/T015 remain unchecked. No environment, service, credential or provider
resource is created/modified here. Source acceptance and post-merge CI do not
authorize setup, dispatch, proof use, human approval or domain effects. Feedback
stays deferred; neither historical blocked write was replayed.
