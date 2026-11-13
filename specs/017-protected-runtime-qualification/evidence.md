# Preparation and Issuer Slice Evidence

Status: issuer-only source candidate; remaining qualification not performed
Scope: current bounded issuer source plus historical preparation/rehearsal evidence

At preparation baseline #49, the new runtime feature had no implementation or live qualification result.
Baseline adapter merge is `336055fde62e45b49c5ff45cee36e1152ca695f1`, acceptance
head `83fbc91f12f856ec84c9a02be5726c18428bff03`, common tree
`2de0fdcdc7c392033fc51c0b84ca2ed9babc2344`; accepted owning wallet code is
`bb0e9dae89a771b05f6c235d0a77237288b95c85`.

A fresh Linux Python 3.12 run in py-bench as UID 1000 passed **154 tests with zero
failures/errors/skips**, including all seven selected owning-source integration cases.
JUnit SHA-256: `b2534eb7aa5c4dc4862cf800d7ea2cd6a46f09ee827932d8deb027b81e29405a`.
Independent readback found no run-attributable fixture processes or fixture key/state
directories. Both owned temporary roots were removed and absence verified. The
accepted adapter and owning-code worktrees stayed clean during the rehearsal.

The first diagnostic run reported 153 passed / one failed under inherited umask 077.
`test_private_state` could not create its intended unsafe 0755 directory because
the wrapper masked it to 0700. That failed log/XML is retained. Rerun used normal
022 test umask inside a private 0700 evidence parent; product/tests were unchanged.
Initial cloud-bench venv setup also stopped at missing ensurepip before tests;
the private environment was completed in py-bench without shared package changes.

This exercises real crypto and loopback mTLS custody with synthetic issuer keys
and same-user reference processes. It does not qualify a deployed issuer client,
independent supervisor, workload-bound custody, protected environment or human
broker. Runtime bindings remain null; attended qualification is not-performed.
Feedback remains deferred; neither blocked write was replayed.

Preparation publication gates also passed: both pin verifiers, syntax, plain and
strict validators, the full adapter suite (**456 passed**) and the canonical
vendored-artifact OpenSpec 1.12.0 gate (**five items passed**). The full-suite
diagnostic first placed pytest temporary exports outside the path gate's allowed
roots (454 passed / two refused). Setting the invocation's temporary-directory
root to the private evidence parent resolved the harness restriction; no gate,
test, pin or runtime source changed.

## 2026-11-12 Owner Act and Landed Preparation

Brett Heap ratified factory #1307 at `04fad0559d127427b5d62a4674409756cbca3c92`
with adapter #49 at `0a2dda9c998825a3098b6151a5fb319454df13cd`, then commissioned
only the bounded issuer/JWKS slice after all three preparation PRs landed.
The decision is recorded on [factory #1307](https://github.com/opensoft/openXfactory/pull/1307#issuecomment-6832086737)
and [adapter #49](https://github.com/opensoft/openXwallet/pull/49#issuecomment-6832088973).

- Factory merged at `21fafd4f34bdd6ffdcd2ab80865fcbe994fc38f6`; its actual tree `e64037069eecd473deaa75b35e72e4e0fa4b32a8` matched the tested current-main composition. All main-triggered workflows passed; pytest reported 10,391 passed, six skipped and 338 deselected, with 741 subtests passed.
- Adapter merged at `7817b66f91ba15920737ec794cba900579258fd3`; its tree `7a851111689bda92cfc4238ccf95065b99fa826b` matched the reviewed/CI-tested candidate. Its CI is PR-triggered; no post-main workflow result is invented.
- Consumer #582 was reconciled to head `d3652362ad80bfc860d06e0fbf22a14278d84892`, retaining a byte-identical six-file owned diff. Fresh validation/browser, coverage and Sonar passed. Its one-off owner-approved administrative merge landed at `a8855717c7d2fda7828a73bf9102c04a2177bfb7`; actual tree `8aab39cca1617c20df27b59fbc2c48aefbf22d86` matched the candidate. Both hosted ephemeral-bench cleanup steps passed. No check or rule was changed.

The local preparation expert panel found no actionable issues; it does not review
future runtime code. Upstream connector reviews were quota-refused and no completed
consumer connector review is claimed. The agent does not tick T001's owner checkbox.

## Commissioned Source Slice

Implementation branch: `017-bounded-issuer-jwks`, from accepted adapter merge
`7817b66f91ba15920737ec794cba900579258fd3`. Only T003 and its necessary
issuer/audience/transport/clock constructor fragment are implemented. T002's full
runtime grammar, integrity/protection preflight, service bindings and every later
runtime/operational task remain pending. No neutral schema, gitlink, dependency
lock, default entrypoint, consumer lock, source pin or protected workflow changes.

The new opt-in source delegates real RS256 signature/claims checking to the unchanged
core. Its internal helper carries only fixed endpoint selectors/CA references, never
a workload token. Tests exercise synthetic issuer responses and real loopback TLS,
bounded body/connect/overall deadlines, cache age/expiry/non-reuse, coalescing,
rotation/removal, exact signed context, post-I/O and post-crypto clocks, and helper
termination/reaping. This establishes source behavior only, not deployed trust.

The initial 71 tests passed. Expanded tests then caught a missing post-crypto
token deadline check and an invalid TLS fixture chain whose CA/leaf shared one
subject name. The deadline check was added and the fixture chain corrected;
certificate validation was not weakened. The corrected expanded run passed 92
tests. Final gate results and cleanup follow.

### Pre-review local source verification

The complete gate sequence ran in py-bench as UID 1000, normal test umask 022,
inside a private evidence parent. Both scoped init steps, both pin verifiers,
syntax, plain and strict validators passed. The full suite passed **561 tests**,
including **105 issuer-slice cases** and all seven existing selected-owning-source
integration cases, with **zero failures/errors/skips**. The canonical verified
vendored OpenSpec 1.12.0 gate passed all five items. There are no added dependencies.

Full JUnit SHA-256:
`39627f7beacc2a3a577e618beadb1864957a5c003cc3f798effa4f529e1bd011`.

Native TLS tests established valid chain/hostname verification, rejection of bad
chain/hostname, ignored ambient CA/proxy/keylog/credential configuration, no auth
or cookies on requests, no redirect following, body/encoding limits, bounded slow
connect/body refusal and helper reaping on timeout/interruption. The isolated
server threads exited. Independent process readback found no attributable helper
or fixture PID. Full-suite, focused-test and diagnostic temporary roots were then
removed and absence verified, including their synthetic TLS keys and ledger files.
Failed diagnostic logs/XML were retained without retaining fixture key directories.

This is source-candidate conformance. It supplies no real GitHub workload token,
protected environment/readback, trusted hosting deployment, independent supervisor,
confined custody deployment, persistent runtime state, janitor or human approval.
The consumer source-only lock is unchanged, `runtime_bindings` remains null and
attended qualification remains not-performed. T002 and all later runtime tasks
remain pending. Feedback stays deferred; neither historical blocked write was replayed.

### Source expert review and corrected candidate

The pre-PR panel covered architecture, performance, security, QA, static/Sonar,
API/integration, data integrity, reliability/concurrency and simplicity, plus
CI/release, with independent coordinator review. It reviewed source commit
`ccc99aadd8c71dadd78599486b109ffce643918f` and the focused corrections below.
The committed candidate also passed the complete 561-test gate sequence before
the review corrections, proving the export-based checks saw the tracked files.

Two actionable P2 findings were reproduced and corrected:

1. `HTTPResponse.read1()` can return EOF before a declared Content-Length is
   satisfied. The helper now checks completed fixed-length body size before
   returning a frame. A loopback response with valid JSON but ten missing
   advertised bytes failed before the fix and is refused afterward.
2. HTTP delta-seconds with many leading zeros were incorrectly saturated as
   overflow, extending padded max-age zero/one to 300 seconds. Leading zeros
   are now normalized before bounded conversion. Three padding regressions
   failed before the fix; padded zero/one, padded max-age/Age and genuine
   overflow cases pass afterward.

The finding owners independently confirmed both closures. No unresolved local
panel finding remains. The corrected focused suite passes **111 tests**, with
zero failures/errors/skips. This review is distinct from hosted CI, a completed
GitHub Codex review, source acceptance or live qualification.

### Final corrected-commit verification and cleanup

The full repository sequence passed again at corrected source commit
`3972d4b57cf866a51cea22a7726291a0936b5994`: **567 tests**, including **111 issuer
tests**, zero failures/errors/skips, both pin verifiers, syntax, plain/strict
validators and all five canonical verified OpenSpec items. Selected owning code
remained `bb0e9dae89a771b05f6c235d0a77237288b95c85`. The receipt-only follow-up
changes this evidence file; the tested source, tests and tracked path set remain unchanged.

Final full JUnit SHA-256:
`3b41da319c3a9f95fc6eda19711e6fed18411b01876f7381df2fa72399535b08`.

Independent process readback again found no attributable helper/fixture PID.
Tracked/full/focused temporary roots were removed and absence verified after
the corrected run; their synthetic key/state files are absent. Diagnostic logs
and XML remain. Existing verifier/gate source, contracts, dependency locks,
workflows, neutral gitlink and relative feature pointer remain unchanged.
No public issuer/provider call, protected dispatch, human acceptance, executable
domain lock or source pin advancement was performed.

### Hosted static-analysis follow-up

The first published implementation head, `aa0d6c1`, failed Sonar's new-code
security rating. The analyzer traced a command-line URL through the existing
allowlist into the request path. The helper now accepts only opaque
`discovery`/`jwks` selections and constructs both HTTP requests with literal paths;
no command-line/provider text reaches the request path. New helper-boundary tests
reject a URL or unknown selector before connection construction.

The two complex functions were split into focused parsing, framing and exchange
helpers. ASCII delta-seconds validation preserves the accepted digit set without
the flagged regex form. Exception-test inputs are sampled before entering the
raises context, and composite assertions were separated. No quality rule,
exclusion, finding status or protection was weakened or waived.

The revised focused suite passes **113 tests**. The standalone Sonar analyzer
reports zero issues in both revised production files; that is not a hosted
quality-gate receipt. Full repository and fresh hosted results follow separately.

The complete local sequence passed at `5cef834e5adfb15a8cb85f0b9a9ffbad9daa099c`:
**569 tests**, including **113 issuer tests**, zero failures/errors/skips, both
pin verifiers, syntax, plain/strict validators and all five canonical OpenSpec
items. Security/static follow-up review found no new issue or semantic regression.
Final JUnit SHA-256:
`c41d8ce636295e347ef12eb14fe19dc0030dff1a3d4ab521164352c0640a4f6d`.

Independent readback found no attributable helper/fixture PID; the remaining
focused/full temporary roots and their synthetic keys/state were removed and
absence verified. The receipt-only follow-up preserves the tested source/tests.
Fresh hosted acceptance is assessed at that published head, separately from
these local results. All live/deployed/human gates remain unperformed.

## T002 commissioning and source realization — 2026-11-12

Brett directed: “Go ahead and land openXwallet #50 through the governed process
when green, then implement and test the remaining T002 operational/source/
protection binding. Keep feedback deferred and don’t replay either blocked write.”

PR #50 landed at `75b88eaad84d4e302d27700bb50b761b95167f2e`, carrying reviewed
head `7c6c113ae98d1aad383acdd72f0d60db374096d2`. Actual merged tree equals the
tested candidate. All runnable hosted checks passed, including Sonar with zero
open issues. The general hosted suite passed 566 with three shallow-history
skips; full-history carve and neutrality/pruning suites passed 84 and 60.
The neutrality comparator's informational mirrored-child failure was already
present at #49; its comparison verdict remained IDENTICAL. GitHub Codex review
was quota-refused, not an approval. Local expert findings had been closed.
No main-triggered workflow exists for that merge, so none is claimed.

The T002 candidate adds only `config.py`, its focused tests and feature context.
Factory governance carries the concrete internal grammar in
`supporting-docs/operational-grammar.md`. Closed bounded input, external approval
digest, source/dependency/composition pins, exact launch/run and effective
protection/service/state/lifecycle selection are compared against fresh trusted
readback. The result is deeply immutable and expires at the earliest deadline.
No service is constructed or credential issued by preflight. Tests cover each
signed launch claim through the existing real-RSA issuer verifier.

The focused suite passes **157 tests**. The local expert panel's architecture,
performance, security, QA, static-analysis, API, data-integrity, reliability and
simplicity reviews found no actionable issue. The initial full invocation
passed 724 and failed two legacy sandbox tests because its explicit pytest
temporary root was outside the configured TMPDIR. Corrected invocation results
are recorded separately; no sandbox rule or production code was weakened.

These are source/isolated results. Actual authenticated provider readback,
complete effective-provider-rule projection, service source measurement,
administrative isolation and runtime enforcement of the returned deadline are
later trusted-hosting/composition obligations. Actual selections, protected
setup/dispatch, deployed qualification and human/domain acceptance remain
unperformed. The consumer's source-only lock and runtime gate remain unchanged.
Feedback stays deferred and neither historical blocked write was replayed.

Corrected full verification at `e24ffa45b132dd814f110641a380135147985709` passed
**726 tests**, including **157 new T002 cases**, zero failures/errors/skips and
the seven selected owning-source integrations. Both pin verifiers, syntax,
plain/strict validation and all five canonical pinned OpenSpec items passed.
JUnit SHA-256:
`bede283928bebbae1dc24f19b16a88cbaefa05d340f1a39f0fa90d43eaf7f6f6`.
No attributable test/helper process remained; owned failed/corrected full-suite
temporary roots and synthetic key/state material were removed, absence verified.
Logs and XML remain outside source. This receipt follow-up changes no source/tests.

The paired factory grammar at `7d99face8934f39fcccc4d9e4d0cf4b068d67ab6` passes
strict scoped OpenSpec validation; its 247-row corpus ledger remains consistent.
Broad factory OpenSpec validation passes 122 items and fails the pre-existing
`add-chain-attestation` missing-MODIFIED-scenario check. Both that packet and its
canonical signed-execution-chain spec are unchanged from factory main. This
limitation is retained explicitly; no unrelated packet, gate or rule was changed.

### T002 quality follow-up

The first hosted candidate passed its quality gate but retained five maintainability
issues: duplicated ref prefixes, concise decimal syntax and two exception tests
with argument preparation inside the assertion. Shared immutable prefixes,
`re.ASCII`-restricted concise digits and precomputed test inputs address them.
The additional mixed-Unicode digit refusal guards the unchanged ASCII-only rule.
Security/static reviewers found no semantic regression. No rule, exclusion or
issue status was waived or weakened.

The complete sequence at `d8c166acc2961f349680e779311543eec0258d43` passes
**727 tests**, including **158 T002 cases**, zero failures/errors/skips, both
pin verifiers, syntax, plain/strict validation and all five canonical pinned
OpenSpec items. JUnit SHA-256:
`66f443784ad97fd8d3a527e2162a55347763310952ebbb23aee10ce3940c248e`.
No attributable helper/test process remained; the follow-up temporary root and
synthetic key/state files were removed, with absence verified. The receipt-only
follow-up changes no source/tests. Fresh hosted acceptance remains a separate
readback at the published head, not an inference from these local results.

## T004/T005 source commissioning — 2026-11-12

Brett ratified factory #1308 at `7d99face8934` with adapter #51 at
`864a2d19fda1` for source acceptance only, directed both landings when green,
and commissioned implementation/testing of T004/T005 in isolation. Feedback
remains deferred and neither historical blocked write is authorized for replay.

Factory #1308 landed first as `469526935630d92f870a31b19d626725b55793e6`,
tree `309fc342a8ce60bcfb8b65d9a4f3b2988597e219`. All required checks passed;
there were no unresolved review threads. The standing global self-authored
approval override applied because both author and authenticated actor were
`brettheap`; only missing approval was bypassed. Adapter #51 then landed normally
as `b2beb54e42b620242dd6e774de8655cea98ca831`, tree
`5f95417b219705f330b0f0fc098918098dd13c47`. Both actual merge trees equal
their reviewed/ratified candidate trees. GitHub Codex review was quota-refused,
not approval; prior local panel and hosted evidence remain separately identified.

The new opt-in `loaders.py`/`runtime.py` connect trusted authenticated connector
capabilities, current canonical policy/challenge data and hosting channel context
to the unchanged proof gate. Worker inputs retain the four accepted arguments.
Service/credential/trust and state references must match the selected configuration.
The token is verified before current-record/challenge access. Preflight repeats
around blocking work; no accepted per-use deadline can be extended by fresh data.

Coordinator review reproduced two timing gaps in the initial composition: a token
could expire in post-crypto preflight before record access, and an observation
could expire in added post-reservation preflight before custody. Both red tests
were retained and corrected by carrying the earliest known token/key, observation,
policy/grant, challenge, registry, channel and protection deadline through every
added blocking checkpoint. Registry/grant/key-expiry variants also refuse before
actual custody use; reservations remain consumed on failure.

The focused matrix has **93 cases**, including exact selected service identities,
each signed launch claim, canonical current records/challenge binding, actual
loopback mTLS, selected worker-certificate hosting context, impostor/unknown-trust
refusal, owning proof acceptance, concurrency and the timing regressions. It uses
the existing explicitly selected owning source and synthetic keys/data only.
The full gate sequence and expert review are recorded at their candidate heads,
separately from this focused source record.

These sources do not implement actual deployment measurement, a production
provider client, supervisor administrative isolation, custody confinement,
initialized-state/recovery or lifecycle qualification. Trusted connectors and
hosting must authenticate/bound their real transports outside worker control;
Python types or matching metadata are not isolation. T006–T015, live protected
qualification and the consumer's independent runtime/human gates remain pending.

### Local review and connector-deadline correction

The initial complete sequence at `89a241efc9c7237addddba814218bf8c357457e9`
passed **820 tests**, zero failures/errors/skips, both pin verifiers, syntax,
plain/strict validation and all five canonical pinned OpenSpec items. The
pre-PR expert panel then found one P2 reliability issue: `_read()` captured a
connector deadline before guarded preflight could shorten it. Post-call refusal
prevented proof acceptance, but the connector received a stale I/O budget.

The red regression observed initial deadline `1794400030`, refreshed deadline
`1794400010`, and connector-received deadline `1794400030`. The invocation is
now deferred until after fresh preflight and supplies `1794400010`. The reviewer
independently reproduced closure. The focused suite passes **94 cases**. The
architecture, performance, security, QA, static-analysis, API, data-integrity and
simplicity reviewers found no additional actionable issue. No rule, check,
neutral contract or original verification core was changed.

### Corrected full verification

The complete local sequence at `10b75f3eb43eb8050b7adf10225a84c657c2123b`
passes **821 tests**, including **94 new composition cases**, zero failures,
errors or skips, both pin verifiers, syntax, plain/strict validation and all five
canonical pinned OpenSpec items. The selected owning-source proof/transport
integrations are included. JUnit SHA-256:
`453a23fe937475775d7acfb6d5a7462006f3d397496fe8cc3863d0d0e27b9538`.
The standalone analyzer reports zero issues in both new production files and
the mTLS fixture file. That is separate from fresh hosted Sonar acceptance.

Independent process readback found no attributable test/helper PID. Owned
focused, initial full and corrected full temporary roots were removed after
completion, including identified default pytest roots, with absence verified.
Synthetic key/state files are absent; logs/XML remain outside source. This
receipt-only follow-up changes no source/tests. No provider credential, public
issuer call, protected setup/dispatch, release or consumer pin change occurred.

All five factory #1308 actual-main-triggered workflows passed at merge
`469526935630d92f870a31b19d626725b55793e6`. Its main pytest result was
10,391 passed, six skipped, 338 deselected and 741 subtests passed. Adapter #51
has no main-triggered workflows, so none is inferred. These post-merge results
do not establish runtime deployment or human acceptance.

## T006 source commissioning — 2026-11-12

Brett ratified adapter #52 at `3833bc8629e6` for source acceptance only,
directed its landing when green, and commissioned T006 implementation/testing
in isolation. Feedback stays deferred; neither historical blocked write is
authorized for replay.

The PR landed normally as `b86b92512a17019c9fd1b5ac171f116949bffe4e`, tree
`9e64a50e62e5cd5740e693cd5c16bf7287ead19f`, equal to the ratified candidate
tree. Required checks and all runnable hosted checks passed; there were no
unresolved review threads. No approval override was needed. The adapter has no
main-triggered workflows, so no separate post-merge run is inferred. GitHub
Codex review remained quota-refused; prior local review and hosted results are
separate evidence, not bot approval.

`SupervisorObserver` and `SupervisedBridge` obtain actual controller-selected
Linux process/file/configuration measurements and use the unchanged observation
and owning proof APIs. `ProcessLaunch` captures a process generation, requires
explicit expected executable bytes and checks actual argv/cwd/liveness/source
and bounded regular-file configuration. PID/start time and execution/configuration
metadata enter the existing composition digest. No worker PID, file paths,
measurement, policy or key are accepted in the observation request.

The initial focused matrix passes **56 cases**, including actual loopback mTLS,
separate gate/worker/admin credentials, valid observation/control requests,
policy revocation/key rotation, an excess-worker-permission mutation and outage
refusal. The owning proof verifier accepts a measured supervised result. Two
coordinator regressions were reproduced before correction: denied peers initially
reached protected configuration I/O, and an independently configured gate
allowlist was not yet joined to the approved service principal/credential pair.
Both now refuse with focused coverage. Distinct fixture CA names fixed an admin
chain ambiguity without weakening certificate/hostname validation.

These fixtures prove isolated behavior only. They do not establish worker OS
key/policy secrecy, separate deployment administration, read-only launch mounts,
actual image/dependency selection, continuous liveness or memory/model behavior.
Observable snapshots can miss changes restored between reads. Real G02/P01 and
T007–T015 remain separately gated. No protected setup/dispatch, live issuer,
provider write, human approval, consumer lock/pin or release is supplied.

### T006 expert review and clock checkpoint correction

The full sequence at `8cd7876a4b2aa9d9a153d1a91360b7e3ab0e2178` passed
**877 tests**, zero failures/errors/skips, both pin verifiers, syntax, plain/
strict validators and all five canonical pinned OpenSpec items. The pre-PR
expert panel found one P2: the observer did not retain the newest clock sample
from configuration preflight. A clock progressing from `N` to `N+10` during
preflight, then falling to `N+5`, could be accepted against the earlier sample.

The focused red regression reproduced that behavior. The observer now records
`current.checked_at` before its next clock sample. The reviewer independently
confirmed refusal with `supervisor-clock-unavailable`; the focused suite passes
**57 cases**. Architecture, performance, security, QA, static-analysis, API,
data-integrity and simplicity reviews found no additional actionable issue.
Standalone analysis reports zero issues in both production modules and the
RPC fixture with its test scope; hosted acceptance remains a separate readback.

### Corrected T006 full verification and cleanup

The complete sequence at `4ee4b97f94ed96fdfc0ee9c972a0824d76dfbabe` passes
**878 tests**, including **57 new supervisor cases**, zero failures/errors/skips,
both pin verifiers, syntax, plain/strict validators and all five canonical pinned
OpenSpec items. Selected owning-source proof and transport integration are included.
JUnit SHA-256:
`2c643775534077c5b5a9c9281b4fec127c9f8612e20c0e09471138818c8ef777`.

Independent process readback found no attributable worker/test/helper PID. All
owned focused/red/full temporary roots, including PKI and state files, were
removed after completion and absence verified. Logs/XML remain outside source.
The receipt follow-up changes no production code or tests. Fresh hosted CI,
Sonar and Codex review are assessed at the published candidate head separately.
Same-user fixture success still grants no deployed OS/admin isolation, provider
activation, human approval or domain effect. Feedback remains deferred; neither
historical blocked write was replayed.

### T006 hosted test-structure follow-up

The first hosted T006 head passed its quality gate but retained one S5778
test-structure finding: request preparation occurred inside an exception assertion.
That preparation now occurs before the assertion. Static review confirmed the
intended call alone can satisfy the assertion, with production code unchanged.
No rule, exclusion or issue status was waived or weakened.

The complete sequence at `0385b8b62734583ad9fb44ead9176afc99b4f4a7` again
passes **878 tests**, including **57 T006 cases**, zero failures/errors/skips,
both pin verifiers, syntax, plain/strict validation and all five canonical pinned
OpenSpec items. JUnit SHA-256:
`1943ec8d8e21ac272d1392af38b4d65dd4b3a2f6260cc96697c80c2121c3eb8a`.
No attributable process remained, and the follow-up key/state/temp root was
removed with absence verified. The receipt-only update preserves these tested
source/tests. Fresh hosted acceptance remains separate from the local receipt.

## T007 source commissioning — 2026-11-13

Brett ratified adapter #53 at `aff5b1e14979` for source acceptance only,
directed landing when green and commissioned isolated T007 implementation/tests.
The exact ratified head passed all runnable checks with no unresolved review
threads, then merged normally as `9fbff0266b31a7845499b6fdbd7f350009325e70`,
tree `41422c76c3cd8caac6997f87cf831a9cea2a45a6`, equal to its ratified tree.
No administrative approval override was needed. The adapter has no main-triggered
workflows; a separate post-merge CI result is not inferred.

`ConfinedCustody` joins protected actual TLS material and the selected owning
client/signer to fresh authenticated deployment/issuance capability readback.
It enforces exact approved configuration/sources/case/run, service, certificate,
endpoint and sign-only subject/key/custody scope with monotonic per-use deadlines.
The existing neutral API, offline entrypoints, proof semantics and pins remain.
New custody-side assertions refuse for an upstream owner decision.

The focused isolated matrix passes **59 tests**. A real owning mTLS service
accepts one gated proof verified by its owning verifier. A separate worker process
using a resolve-only credential is explicitly denied the exact valid canonical
preimage captured from that proof. An excess-worker-sign-permission mutation
breaks the probe, and an outage cannot count as denial. Success/injected-failure
paths reap processes and remove their disposable custody key/state directory.

These are isolated source results. The deployment/issuance readback is a trusted
fixture, not a real provider control-plane integration. Same-user fixtures cannot
prove OS key secrecy, independently administered deployment, immutable sources,
actual image/dependency selection or network confinement. Live G03/P01, T008–T015
and consumer runtime/human acceptance remain pending. Feedback stays deferred;
neither historical blocked write is replayed. No protected setup/dispatch occurs.

### T007 local review and composed deadline correction

The initial complete sequence at `2762c8a66273afb4cc2f9e33c52982cee45eacde`
passed **935 tests**, zero failures/errors/skips, both pin verifiers, syntax,
plain/strict validation and all five canonical pinned OpenSpec items. The expert
panel found one P2 composition issue independently reproduced in both directions:
custody readback could cross an earlier outer proof deadline before invoking the
signer; a shorter custody lease was not retained through later outer proof I/O.

Both connected regressions failed before correction. The internal per-use seam
now accepts the outer deadline before any custody preflight and returns its
retained earliest deadline to `RuntimeBridge` before later checks. The unchanged
neutral signing API receives only the canonical message. Both regressions and
the complete **59-case** T007 matrix now pass. No deadline, check or rule is waived.

### Corrected T007 full verification and cleanup

The complete ordered sequence at `ce1824c56f2a8445f1323a238b9307a01e948200`
passes **937 tests**, including **59 T007 cases**, zero failures/errors/skips,
both pin verifiers, syntax, plain/strict validation and all five canonical pinned
OpenSpec items. Owning-source proof/transport integrations use the explicitly
selected clean `openWallet-code` at `bb0e9dae89a771b05f6c235d0a77237288b95c85`.
JUnit SHA-256:
`377db69ce85552a810a294db60c473648ba837eb4ba5eec6ba9eb8ab2688267f`.

The API and reliability reviewers independently confirmed closure in both
deadline directions, including zero actual signer calls after the outer deadline.
All nine local expert roles completed with no other actionable finding.
Standalone Sonar reports zero issues across the new source/tests and runtime glue.

Independent process readback found no attributable fixture/worker/test PID. The
owned focused, red, initial-full and corrected-full temporary roots, including
synthetic PKI/key/state files, were removed and absence verified. Reviewers also
removed their own reproduction roots. Logs/XML remain outside source. This
receipt follow-up changes no production code or tests. Fresh hosted CI, Sonar
and Codex response are separate checks at the published candidate head.
Deployed machine/human acceptance stays pending; feedback remains deferred and
neither historical blocked write was replayed.

### T007 hosted assertion follow-up

The first published T007 head passed all runnable hosted checks and its Sonar
quality gate. Hosted Sonar retained one S9073 test-clarity finding for a composite
assertion. It is split into two assertions; production code is unchanged. No
issue, rule or quality threshold is waived.

The complete local sequence at `2a974736dd122a57e5a48cedea4c693ecd6b114d`
again passes **937 tests**, zero failures/errors/skips, both pin verifiers,
syntax, plain/strict validation and all five canonical pinned OpenSpec items.
JUnit SHA-256:
`f05f7b599f8836b4c5f8d1748daafad965c85c50acad53248eca0e283546ea84`.
No attributable fixture process remained; the follow-up PKI/key/state temporary
root was removed and absence verified. This receipt follow-up changes no code/tests.
Fresh hosted acceptance is checked at the updated PR head separately.

GitHub Codex refused the initial manual request because the account review limit
was reached. No bot approval is inferred; the nine-role local panel and independent
deadline-fix checks are separate evidence. Machine/human acceptance remains pending.

## T008 source commissioning — 2026-11-13

Brett ratified adapter #54 at `8de227dadd53` for source acceptance only,
directed landing when green and commissioned T008 in isolation. The exact head
passed all runnable checks with no unresolved review threads and merged normally
as `3f4a358cf27d79027ec370ef89c5df676b4642c1`, tree
`8c7f7bbd5bab9e37e1a2552e82d350d3063ba5cc`, equal to its ratified tree.
No administrative approval override was needed. Source acceptance supplies no
deployed storage or human acceptance.

`InitializedLedger` requires an independently recorded existing-store identity,
private files, the existing exact schema/integrity and fresh authenticated active
scope/recovery readback. Runtime connections use `mode=rw` and cannot create a
missing file. The opt-in bridge exchanges earliest deadlines with state preflight
and reservation and checks state through final proof acceptance. The original
offline initializer, schema, proof/signing interfaces and pins remain unchanged.

The focused isolated matrix passes **49 tests**, including owning proof
verification, restart and replay refusal, four concurrent reservation attempts
with one winner, actual process exit after commit, ambiguous custody failure,
post-commit revocation, missing/corrupt/replaced/unsafe state, expiry during I/O
or lock acquisition and separately approved new-scope initialization. The initial
test collection failed before the runtime state module existed; these cases now
pass with the implementation present.

The initialization receipt and administrative readback are trusted fixtures.
Device/inode and integrity checks do not establish hostile-host or valid-backup
rollback resistance. Active-scope restore is prohibited; recovery requires
revocation and a new approved initialization/workload scope. Real provider readback,
retention/recovery enforcement, OS/admin isolation, lifecycle and live machine
qualification remain pending. No protected setup/dispatch, consumer pin movement,
release or human approval occurs. Feedback stays deferred and neither historical
blocked write is replayed.

### T008 review and bounded-integrity correction

An initial diagnostic sequence started at `818d7fe358922e13402eb97fd8511911048967ed`
reported **986 tests**, zero failures/errors/skips, both pin verifiers, syntax,
plain/strict validation and all five canonical pinned OpenSpec items. Local expert
review found one P2: SQLite's progress handler retained a new three-second budget
even when its caller supplied an earlier deadline. Post-I/O refusal prevented a
proof after expiry, but integrity work could exceed the forwarded short budget.

The focused regression reproduced continuation at 1.5 seconds with a one-second
budget. The progress deadline now uses the earlier requested budget and is set
before connection. The regression and complete **50-case** T008 matrix pass.
Standalone static findings were corrected with a filename constant, explicit
preflight transaction checks and exception-test setup outside assertions. No
rule, issue status or gate threshold was waived.

Reliability review also identified a P2 composed-clock gap: the state wrapper
returned expiry without its newest clock checkpoint, so a later parent sample
could regress relative to the child's observation. Both connected regressions
failed before correction. `StateUse` now carries earliest expiry and latest
checked time; the bridge forwards its clock floor inward and retains the child's
newest sample on return. The focused T008 matrix now passes **52 cases**.

Both reviewers independently verified their corrections. Reliability also
verified a connected post-reservation case: a newer child timestamp followed by
an older parent timestamp refuses before signing, retains the durable reservation
and refuses reuse after restart. That case is now tracked; the focused matrix
passes **53 tests**. The preceding complete run reported **989 passed**, zero
failures/errors/skips, with all ordered gates passing. Final qualification includes
the added regression in a fresh complete sequence at the recorded source head.

### Final T008 source verification and cleanup

The complete ordered sequence ran with source/tests and HEAD fixed at
`d92f683b63338c0df74ddbb72c2f677e2d878ae0`: **990 tests passed**, including
**53 T008 cases**, zero failures/errors/skips, both pin verifiers, syntax,
plain/strict validation and all five canonical pinned OpenSpec items. Explicit
owning-source integrations use clean `openWallet-code` at
`bb0e9dae89a771b05f6c235d0a77237288b95c85`. JUnit SHA-256:
`a12014ccc1c3bc5c45d9f893333e1883011b911fe41cda6a0ce3309c0e76e4c3`.

All nine expert roles completed. The performance and reliability findings have
independent closure checks; the post-commit clock case is included in the tracked
suite. Standalone Sonar reports zero issues in the new state source, runtime glue
and final tests. Hosted acceptance and Codex response are checked separately at
the published candidate head.

Independent process readback found no attributable fixture/worker/test PID.
Owned initial, focused, red, corrected and final temporary roots, including
synthetic keys/state, were removed and absence verified. Reviewers removed their
own reproduction roots. Logs/XML remain outside source. This receipt follow-up
changes no production code or tests. Deployed storage/recovery, lifecycle,
protected operation and human acceptance remain pending. Feedback stays deferred;
neither historical blocked write was replayed.

## T009 source commissioning — 2026-11-13

Brett ratified adapter #55 at `caef11d92906` for source acceptance only,
directed landing when green and commissioned isolated T009 implementation/tests.
The exact head passed all runnable checks with no unresolved review threads and
merged normally as `46c83b1bd10a742ddd9b7d68459d8ea2ba13c949`, tree
`9f417f60768ced57fd829e1502b06083458f69de`, equal to the ratified tree.
No administrative approval override was needed. The adapter has no main-triggered
workflows; no separate post-merge CI result is inferred.

`RunLifecycle` binds the fixed run scope, lease and resource manifest and exchanges
deadline/clock checkpoints with the trusted bridge. The one-shot runner finalizes
success, failure and cancellation and returns an operation value only after fresh
independent cleanup verification. `RunJanitor` closes leases and conditionally
cleans only exact run-owned generations, with retained replay/shared assets excluded.
Its separately scheduled expiry sweep needs no runner finally or live proof config.

The initial focused isolated matrix passed **46 tests**. Separate janitor/readback
processes use bounded JSON over host-selected pipe capabilities, with peer identity
outside the request. Actual worker processes are stopped/reaped, fixture credentials
revoked and run files removed; replay state and shared sentinels remain. An owning
proof verifies, including success/failure/cancellation after signing. Hard runner
death, expiry cleanup, forged peer denial, missing reader, acknowledgement-without-
removal and replacement generation are exercised. Cleanup readback includes a fresh
random attempt reference so a prior positive observation cannot satisfy a new attempt.

The fixture registrations, controlled clock and same-user processes establish only
isolated behavior. Provider registration durability/conditional operations, actual
independent scheduling/admin/readback, retention, OS isolation and deployed L01/P01
remain unqualified. No provider setup, protected dispatch, release, consumer pin or
human approval is supplied. Feedback stays deferred; neither historical blocked
write is replayed.

### T009 expert review and timing corrections

All nine local expert roles completed. Three P2 timing findings were reproduced
with focused regressions before correction: registration lookup could consume
the janitor budget before a fresh budget began; cleanup could outlive an earlier
proof-use deadline before the runner returned its value; and a final bridge-only
clock sample was not retained by the outer active run.

The janitor now holds the approved fixed plan, rejects another plan before I/O,
caps the whole attempt before lookup and verifies the current registration digest.
The runner carries cleanup verification's latest time and rechecks the retained
proof-use deadline after cleanup without revalidating the intentionally closed lease.
The bridge publishes its final checkpoint without another clock sample or I/O.
Performance, QA and API reviewers independently confirmed their respective closures.

Cleanup catches ordinary provider exceptions while allowing control cancellation
to propagate; an independent sweep remains responsible after interruption. Fixture
audit denials are explicit rather than assertions hidden by generic error handling.
No rule, issue status or gate threshold is waived. The focused matrix now passes
**54 tests**, including the post-cleanup and bridge-return regressions, retained
reservations after refusal, interruption during finalization and revoked leases.

### Final T009 source verification and cleanup

The complete ordered sequence ran with source/tests and HEAD fixed at
`8bb41cd33782f140878caefdabe3e7b94d818e92`: **1,044 tests passed**, including
**54 T009 cases**, zero failures/errors/skips, both pin verifiers, syntax,
plain/strict validation and all five canonical pinned OpenSpec items. Explicit
owning-source integrations use clean `openWallet-code` at
`bb0e9dae89a771b05f6c235d0a77237288b95c85`. JUnit SHA-256:
`a6cb25f72474aa6d2fe4af0a921f8561e1141b0a3324ec71286885a5d24ccbe6`.

All nine expert roles completed and the three P2 findings have independent closure.
Standalone Sonar reports zero issues in both production files and all three test
files. Fresh hosted CI, Sonar and Codex response are assessed at the published
candidate head separately.

Independent readback checked **16 recorded worker generations**, with none still
present, and found no attributable fixture/worker/test PID. All owned focused,
red and full temporary roots, including synthetic credential/key/state material,
were removed and absence verified. Reviewers removed their own reproduction roots.
Logs/XML remain outside source. This receipt follow-up changes no production code
or tests. Actual provider lifecycle/admin isolation and protected-machine/human
acceptance remain separate gates. Feedback stays deferred; neither historical
blocked write was replayed.

## T010 source commissioning — 2026-11-13

Brett ratified adapter #56 at `508cb51f34074bfa87d65880c8ebdd69f8634076`
for source acceptance only and commissioned isolated T010 implementation/tests.
All runnable checks passed with no unresolved review threads. The exact head
merged normally as `1b313bac487956a3cb74eddf581197e7dc486358`, tree
`1eebadea83a328063c282e4f16088bbe2bd1d5ed`, equal to the ratified tree.
No administrative bypass was needed. No main-triggered CI result is inferred.

The new explicit conformance entrypoint binds the substantive offline matrix to
an exact per-module collection contract plus required case anchors. Every test
requires passing setup/call/teardown; deselection, skips, expected failures,
unexpected passes and collection drift fail. Owner integration requires the
explicit clean accepted owning code before and after execution. The existing
neutral pin and ordinary entrypoints remain unchanged. The workflow disables
persisted checkout credentials and performs source/dependency acquisition before
the loopback-only namespace gate. Namespace/privilege checks survive isolated
Python exec; provider environment and ambient pytest options are removed.

The first native network-none disposable-container trial passed **781 tests**
with zero failures/errors/skips. Eleven subsequent actual-pytest mutation tests
strengthen the harness. Final frozen-source gate and review evidence follows
separately. This source candidate supplies no deployed OS/admin isolation,
provider setup, protected dispatch, consumer pin or human approval. Full scoped
redacted receipts remain T011. Feedback stays deferred; neither historical blocked
write was replayed.

### T010 expert review and collection-identity correction

All nine expert roles completed. QA reproduced a P2 false-green case: dropping
one required parameter and adding an unrelated test could preserve module counts
and function anchors. The audit now also compares committed per-module SHA-256
fingerprints of compact JSON containing sorted full node IDs, including parameter
IDs. A compensated-substitution unit test and actual pytest subprocess mutation
require refusal while preserving order independence. Expected fingerprints are
never generated during CI. The preceding frozen commit passed all **1,094 tests**
and a native **792-test** offline matrix; a fresh corrected sequence follows.
