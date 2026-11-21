# T013P04 original runner capture and bounded phase transport subplan

Status: corrected isolated source qualified; final publication/owner acceptance pending.
Scope: first codeXfactory machine-possession pilot, feature017 T013P04 only.
Branch: `017-p3-runner-transport-prep`; prepared 2026-11-20 UTC.
Sole implementation list: [tasks.md](tasks.md). This refines its existing P04 row,
not a second task list or a new feature.

## Source basis and authority

Brett source-ratified #98 at `03d1ee71b53187b5b52233db02b7cca55281b3aa`, then
requested landing when green, independent main CI and next-slice preparation.
Normal merge `7f85c43c6a4eee311d7033e59df2d8bbd4b1ddf7` has the identical tree
`bd9f68cde018b2d43fbef967ce1f2ec59d8e7995`. The
[acceptance/main receipt](evidence.md#2026-11-20-98-source-acceptance-and-p04-preparation)
records five passing jobs and actual evaluated Sonar/baseline verification.

The accepted [P3 plan](p3-azure-composition-plan.md),
[research](p3-azure-composition-research.md), [model](p3-azure-composition-data-model.md),
[private interfaces](contracts/p3-azure-composition.md) and
[acceptance matrix](p3-azure-composition-acceptance.md) remain the architecture.
Factory [R04/R11](https://github.com/opensoft/openXfactory/blob/c2dfbbcc6fa6965fcde18661bddca1dac7128d47/openspec/changes/add-protected-runtime-azure-composition/specs/protected-runtime-azure-composition/spec.md)
and [D4](https://github.com/opensoft/openXfactory/blob/c2dfbbcc6fa6965fcde18661bddca1dac7128d47/openspec/changes/add-protected-runtime-azure-composition/design.md)
own runner trust, phase and budget semantics. This is a refinement within those
accepted boundaries, not a new wire profile, role, input or grant.

The subsequent owner instruction commissions P04 code and testing in isolation.
P05-P09, setup/dispatch, T001/T013/T014/T015, consumer058 T002 and
independent human assurance remain gated. Roles are still subject to confirmation.
No operational accepted_commit is selected. Feedback deferred; blocked writes unreplayed.

## Technical context and constitution check

Use existing Python 3.12/Linux, locked dependencies and internal package conventions.
Implementation path: `scripts/workload_factory_binding_runtime/azure_composition/runner_transport.py`.
Controls: `tests/runtime_binding/test_azure_runner_transport.py`. Both were created by the explicit isolated commission, after preparation.
Measured collection and completion evidence are recorded below.

The feature deliberately has no local constitution. Use the factory decisions,
repository rules and shared OpenSpec/Speckit protocol; do not inherit another
feature's constitution. Before/after-design check: PASS for preparation. Preserve
neutral APIs, old local exact types, profiles, three manual inputs, seven runtime/
eight source roles, default refusal, workflow YAML, pins, locks, issuer policy,
counters and every prior matrix identity/fingerprint/anchor prefix.

## Research decisions and source map

| Decision | Existing source | Required interpretation |
| --- | --- | --- |
| Original capture plus selected policy | `github_bootstrap/client.py` | Generic HTTPS and selected-URL equality do not authenticate original injection; its bearer is currently reread |
| Drift checks plus frozen sends | Factory R04/D4 | Freeze-only proves non-redirection, not the required later-mutation refusal |
| Actual TokenClient and bounded Https for GET | `workflow.py`, `github_bootstrap/https.py` | Exact TokenClient survives; private URL/bearer cross anonymous stdin with a TLS-to-GO check |
| Existing intrinsic POST | `hosted/stage_client.py` | AdmissionClient/Channel require exact types, including PrivateHttps; do not bypass them |
| Explicit fixed runner accounting | `hosted/readback.py`, `workflow.py` | TokenClient/Https do not consume ReadBudget automatically; keep the fixed GET/POST distinct from nested ledger reads |
| Effective credential compatibility | `workload_factory_binding/evidence.py`, `github_bootstrap/client.py` | reference() limits the request bearer to 512; the later 8,192 expression does not widen it |

[GitHub's OIDC reference](https://docs.github.com/en/actions/reference/security/oidc#methods-for-requesting-the-oidc-token)
documents the injected request URL/bearer. The runner's
[ScriptHandler](https://github.com/actions/runner/blob/main/src/Runner.Worker/Handlers/ScriptHandler.cs)
obtains them from its trusted system connection. This supports explicit platform
trust. GitHub REST run/job correlation does not independently attest the URL.
No real origin/path/query policy, complete subject or proof audience is selected
from those documents or discovered by acquiring a token.

## Private data and interface model

Reuse the parent model's RunnerCapture concept. These are private capabilities,
not new serialized records or public schema fields.

| Capability | Held facts and behavior |
| --- | --- |
| Trusted policy selection | Accepted source, original job class, phase/audience and exact HTTPS origin/path/closed-query rules; independent of worker configuration and captured values |
| Original capture | Only the original URL/bearer, captured once before untrusted execution; frozen private send values, never worker context or repr/asdict/pickle/export data |
| Negative integrity observation | Trusted original two-field mapping/accessor retained solely to compare against frozen values, never to adopt or return replacements |
| One phase acquisition | Existing separately authorized phase context and original Decision; consume before transport invocation, never reopen after uncertainty |
| Admission result | Existing StageAdmission after actual intrinsic client/controller checks; neither capture nor token response establishes readiness |

A mapping, constructor or dataclass is not authentication. Trusted hosting supplies
original injection and policy. This private embedding does not establish a hostile
launcher/root or privileged-Python memory guarantee; later P05/P08 and operational
readback retain OS exclusion and actual source-route obligations.

## Original capture and token GET

Validate the original URL against independently selected exact HTTPS authority and
closed path/query policy before any token request. Reject userinfo, fragments,
unselected ports/origins, ambiguous encoding/path forms, duplicate query keys,
preset audience and unapproved fields. Do not guess the issuer host as the per-job
request host, approve a URL using its own fields, or add permissive suffix fallback.
Actual per-job policy bindings remain a later trusted selection.

Copy only the two original string values privately. Keep the original trusted
mapping/accessor solely for a negative equality comparison of both fields. Check
initial binding and actual token-send time, including Https's TLS READY-to-GO
checkpoint. Missing/changed URL or bearer, coherent pair substitution, explicit
rebinding and source/phase overrides refuse without using replacement values.
Frozen values are the only send authority. This is capture once plus drift detection.

The private GET wrapper delegates actual `github_bootstrap.Https.exchange` with
`before_send=guard`, preserving an actual TokenClient. Its selected CA, sanitized
child argv/environment, anonymous stdin, proxy/trust/keylog exclusions, time/body
bounds and child reaping remain mandatory. PrivateHttps places its URL in argv
and is not the transport for this private runner request URL.

Consume the single attempt before transport invocation, including concurrent calls.
Success, lost reply, exception or cancellation never reopens it. No automatic
retry, recapture, re-fetch or reconstruction from worker data is permitted. This
adds no durable mint-grant service, namespace reuse or hostile-host rollback claim.

## Intrinsic phase POST and purpose separation

| Existing phase | Permitted behavior | Retained boundary |
| --- | --- | --- |
| preflight | Bootstrap audience `urn:opensoft:openxfactory:bootstrap-admission:v1`, policy preflight without environment; POST `/v2/plan` | plan-ready confers no protected launch/proof/issuance authority |
| protected-admission | Same bootstrap audience, policy protected, selected environment and eligible human review; POST `/v2/protected` | Signed claims and independent provider/run/job/protection correlation remain necessary |
| qualify | Existing trusted Qualifier, finalized full context and distinct configured proof audience | No new runner admission POST or CLI finalize phase |
| cleanup | Existing registered cleanup audit | No acquisition, finalization, resend or renewed operation authority |

The returned immutable JWT goes to the independently selected intrinsic controller
route. Signature/current-key, exact source/repository/owner/workflow/run/attempt,
active job, eligible review and protection checks stay in the existing verifier/
controller before readiness. A valid signature from an untrusted URL is insufficient;
audience encoding is not a restriction on the request bearer's own permission.

POST delegates existing actual AdmissionClient, Channel and exact PrivateHttps.
The original runner pair no longer selects/authenticates it. Preserve current
route/binding, nonce/principal, response, ledger, expiry and material guards.
The new capture callback does NOT propagate into AdmissionClient.read. No subclass,
instance monkeypatch, field stripping or fake exact-type object is allowed.
P04 may prove isolated composition around existing admission APIs; P08 owns actual
production construction and wiring. Existing admit_hosted/default operational_bindings
are not newly wired or activated by this preparation.

## Accounting and effective bounds

The fixed runner graph is ONE token GET attempt then ONE intrinsic phase POST
attempt on the SAME original runner Decision. Capture/validation itself performs
zero token/provider/network calls. TokenClient/Https do not consume ReadBudget;
assert those fixed call counts explicitly while preserving every nested controller/
provider read's real existing group charge. Do not charge GET as REST correlation:
protected correlation already consumes run/jobs/reviews/run, all four slots.
No unmapped exchange, new group, reset, late upgrade or extra decision enlarges the
graph. A complete positive that cannot fit requires separate governance.

| Boundary | Effective existing limit |
| --- | --- |
| Original Decision | At most 10 seconds, wall and monotonic; earlier expiry wins, regression/equality at expiry refuses |
| Connection readiness | Five seconds inside the original remaining total |
| Ordinary ledger | GitHub readback aggregate 13; correlation 4 / source 4 / protection 3 / control 2; ARM 24 / key 3 / private 12 |
| Staging | Aggregate 26; correlation 8 / source 8 / protection 6 / control 4 / private 16, with existing observation bounds |
| Finalization | Aggregate 28, protection 18, six protection observations and ordinary private 12 |
| Qualification | Ordinary aggregate 13 and correlation 4 / source 4 / protection 3 / control 2; private 39, no join or used-ledger upgrade |
| Request bearer | At most 512 characters and existing reference/transport character restrictions; not 8,192 effective |
| Token projection/POST | JSON 24,576 bytes; returned JWT 16,384 characters; usable POST JWT 16,377 including room for the Bearer prefix |
| Generic HTTPS | URL 4,096 characters, request 65,536 bytes, response 1 MiB; existing header/framing caps unchanged |

Reject a returned token exceeding 16,377 before POST; never truncate or acquire another.
Keep the original remainder across slow GET/POST and existing send/return checks.
Existing bounded issuer discovery/JWKS verification is distinct from minting a token
to discover the runner endpoint; add no new runner discovery request or credential chain.

Real runner length/characters and endpoint policy remain unqualified. If later
approved material cannot fit 512, the route is ineligible until a governed factory/
adapter correction is accepted. Do not inspect a live secret now, truncate, fork
the old client or silently widen its check. Body/counter incompatibility follows
the same governance boundary.

## Future acceptance controls

This table traces the existing P04 row, not a second implementation list. Each
negative starts from a fitting positive with fresh independent scope so replay,
missing fixture data or outage cannot mask the intended guard.

| Requirement | Complete positive | Independent refusal/counterfactual |
| --- | --- | --- |
| R04 trust | Original capture and selected policy through actual local TLS GET | Origin/path/query/port/encoding/duplicate/preset-audience substitution before bearer transmission |
| R04 drift | Frozen private pair with actual TLS-to-send check | URL-only, bearer-only/coherent drift; explicit rebind, concurrent acquisition, lost-reply reuse |
| R04 readiness | Real signature-valid bootstrap identity, provider corroboration and intrinsic phase result | Validly signed wrong source/phase/audience/environment/run/job/reviewer; proof/bootstrap purpose substitution |
| R04 privacy/transport | Real TLS/CA, scrubbed helper and fixed errors | Wrong host/CA, proxy/trust/keylog, redirect, malformed/compressed/truncated/slow data, canary in repr/export/exception/cause/context |
| R11 bounds | Complete GET/POST transcript with identical Decision and actual nested charges | Counter/clock/deadline reset, shortened expiry, extra exchange, oversized bearer/JWT/body, cancellation after TLS before send |
| R12 scope | Existing default refusal and source-fixture evidence only | Flag/file/plugin/input activates route; fixture relabeled GitHub/Azure/live/human/consumer acceptance |

A server 3xx after the authorized first request refuses without following or sending
credentials again; do not promise to predict a response before the original send.
Supplied unapproved destinations refuse before send. Reuse real local crypto/TLS/
process primitives and independent literal expectations, not only synthetic.jwt.only,
copied pass flags or expected URLs derived from the same product-policy helper.
Independently audit child reaping, pipes, fixtures and container absence on cancellation.

## Qualification, quickstart and next commission

Verified baseline: full 3,224 parent cases plus 11 subtests, native 2,802, provider 195.
Preserve all old identities/fingerprints/anchor prefixes. Measure P04 identities only
after implementation and append substantive controls to existing relevant case
families; R04 is a requirement identifier, not a new conformance-family key.

Preparation checks links, scope/task consistency, unchanged checkboxes and all
non-document source/pin/workflow bytes, plus the six fast offline governance gates.
Main CI verifies the unchanged runtime; do not rerun hours of full/native tests for
this documentation-only preparation.

For a later explicit isolated commission, use this feature worktree and only the
existing T013P04 row, create its proposed module/controls, measure collection, then
qualify frozen final source with all seven ordered gates and mandatory native
isolation. Audit owned helpers/fixtures/containers. Run hosted source CI/local review
when publication is commissioned and present the exact candidate for owner source
ratification. Preparation is neither that commission nor acceptance/merge authority.

P05-P09, actual origin/credential compatibility/subjects/proof audience, appointments,
setup, dispatch, provider writes, full S1 qualification and independent human/consumer
gates remain separate. Feedback deferred; blocked writes unreplayed.


## 2026-11-20 isolated implementation result

The owner explicitly commissioned T013P04 using prepared plan commit
`6fcd43f4872fdeb91748fe9d654634a62093b6e0`. Earlier future/preparation wording
records that baseline; it does not describe the completed isolated source slice.
Qualified code/test/matrix head: `6f4fb345bc99b0ea3a5bddc3bacdf381f123360f`.
See [the qualification and cleanup record](evidence.md#2026-11-20-t013p04-isolated-implementation).

The [private implementation](../../scripts/workload_factory_binding_runtime/azure_composition/runner_transport.py)
and [110 controls](../../tests/runtime_binding/test_azure_runner_transport.py)
exercise actual local TLS GET, signature-valid bootstrap identity, independently
corroborated fixture facts and the existing intrinsic phase clients/controller.
They retain fixed GET/POST attempt counts and the same original Decision, with
no runner-pair use after GET and no new callback injected into intrinsic POST.

All seven ordered gates pass, including 3,334 full parent cases plus 11 subtests;
mandatory native conformance passes all 2,912 cases. The focused 110-case run has
100% statement/branch coverage for this module (127 statements/two branches).
Ten removed-guard counterfactuals are detected by actual assertion failures,
with a passing ten-case baseline and no fixture errors. Every old accepted
node identity/order, per-module fingerprint and anchor prefix is preserved.
Independent namespace/helper/retention audit and owned-fixture disposal pass.

Only T013P04 is marked complete by this result. P05-P09, publication/hosted CI/
local expert review, source ratification, real runner endpoint/credential-length
compatibility, role appointments and every operational/human/consumer gate
remain separate. Setup/dispatch unauthorized; feedback deferred; blocked writes unreplayed.


## PR #99 routine state-export correction

Publication review found that blocking reduction did not block Python's inherited
normal-instance __getstate__ hook. Actual capture and token-transport fixtures
exported their private slot state. This is a routine export within R04's existing
privacy boundary, distinct from hostile base-class bypass/private-slot inspection.
Shared _Opaque now refuses that hook. Two new actual-instance controls require
fixed private errors, absent cause/context and no runner request; both fail on
the previously published source. Two unused non-fixture test imports were removed.

The earlier 110-case qualification and initial panel clearances are historical.
Corrected collection has 112 P04 cases, preserving every earlier node ID/order,
module fingerprint and anchor prefix; new controls extend existing R01. Corrected
frozen full/native, cleanup, specialist follow-up and hosted CI remain required.
Source scope and all existing limits/defaults/pins/operational gates remain unchanged.


## PR #99 initial hosted analyzer follow-up

The initial published head passes hosted CI and the unchanged quality gate but
reports a regex repetition warning and seven multi-invocation exception assertions.
The hostname expression now uses one initial alphanumeric character rather than
an overlapping repetition; the accepted language and all independent limits remain
unchanged. Seven negative tests construct their fitting inputs/capture before the
exception assertion, leaving only the intended failing invocation inside it.

S5754's broad-catch advisory is intentionally retained after security/coordinator
review. Every BaseException subclass can carry credentials in its payload or
context, including SystemExit, GeneratorExit and a custom direct subclass. The
private boundary must sanitize those too; narrowing the catch or reraising the
original would weaken privacy. Three new actual-capture controls prove fixed
refusal, absent cause/context and no request. Empty KeyboardInterrupt cancellation
semantics remain unchanged. This is a documented intentional rule exception, not
a suppressed rule or an API-classified false positive; final Sonar must be read.

Collection is now 115 focused controls, 3,339 full parent cases and 2,917 native.
All prior identities/order/fingerprints/anchor prefixes are preserved. The 10fc043
full run was stopped without reported failure at approximately 74 percent for
these corrections; its audited cleanup remains diagnostic. Final frozen source
qualification, cleanup, review and replacement hosted CI are still required.


## Final corrected qualification

Qualified runtime/test/matrix head: `19c516bcd50e6f2f966f669f313a5b0f043d2eb6`. Final source passes all seven
ordered gates, full 3,339 parent cases plus 11 subtests, native 2,917 and focused
115 controls. Module statement/branch coverage is 100% (129 statements/two branches),
with twelve detected guard-family counterfactuals and a passing twelve-case baseline.
Nine local specialist follow-ups clear this exact code head. Independent namespace/
helper/retention audit and owned-fixture disposal pass for both complete runs.
See [the final corrected record](evidence.md#final-pr-99-corrected-isolated-qualification).

Earlier pending and initial 110/112-case records retain their dated scope. The
completion-record commit changes documentation only; final-publication hosted CI
and exact-head review confirmation remain separate. Only P04 is complete in
isolation; owner ratification, P05-P09 and operational/human/consumer gates remain
separate. Setup/dispatch unauthorized; feedback deferred; blocked writes unreplayed.
