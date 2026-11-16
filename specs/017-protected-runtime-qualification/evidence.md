# Preparation and Issuer Slice Evidence

Status: isolated T012S source candidate qualified; operational qualification not performed
Scope: source/isolated fixtures only, with historical preparation and earlier slice evidence

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

### Final T010 source verification and cleanup

Source/tests and HEAD stayed fixed at `959e80061b1041a373498a9aaf0bd548ed26b5dd`
through the complete ordered sequence: **1,096 tests passed**, zero failures,
errors or skips; both pin verifiers, syntax, plain/strict validation and all five
canonical pinned OpenSpec items passed. Full JUnit SHA-256:
`5ef345273e638ade0e7d6b07446909c5812ba4be6f5b597817bdb612f1edca56`.

The final native network-none disposable-container matrix passed **794 tests**,
including **52 harness cases**, with zero failures/errors/skips and all required
I/G/S/L/current-R01 anchors. Both the parent and an isolated Python exec verified
loopback-only networking, no capabilities/groups or privilege regain, a cleared
environment and fresh private home/temp. JUnit SHA-256:
`e6f793088e6d6bedfa3e88991e6423f4b5099f813009a853b6c1acda3d482220`.
The projects/source bind was read-only, only the owned evidence tree was writable,
and no provider/profile/SSH/Docker-socket mounts were supplied. Actual owning
source was clean at `bb0e9dae89a771b05f6c235d0a77237288b95c85`; the adapter's
neutral pin remains unchanged. Hosted sudo/unshare execution is checked separately.

All nine local expert roles completed. QA independently verified the collection-
identity correction with three focused tests; standalone Sonar reported zero
issues in the final four Python files. No rule, threshold or issue was waived.

Independent cleanup readback covered **40 recorded worker generations**: 16
ordinary-bench generations were absent by PID/start-time identity, and the private
PID/network namespaces containing the other 24 were gone with all three owned
disposable containers. No attributable helper process remained. All six owned
initial, focused and final fixture roots were removed and absence verified;
reviewer temporary roots were also removed. Reports/logs remain outside source.
This receipt-only follow-up changes no tested code, tests or workflow. Deployed
qualification, full T011 receipts, protected setup/dispatch and human approval
remain separate. Feedback stays deferred; neither historical blocked write was
replayed.

## T011 source commissioning — 2026-11-13

Brett ratified adapter #57 at `2c36b07622fc81202d5a8167aade7c4a5ff20700`
for source acceptance only and commissioned isolated T011 implementation/tests.
All runnable checks passed with no unresolved review threads. The exact head
merged normally as `cc4e7fb2932116d6fd42b0cadb35233b2d9adeaf`; merged tree
matches the ratified tree. No administrative bypass was used. No main-triggered
CI result is inferred.

The internal receipt builder projects only closed fields/digests from a trusted
validated selection, actual harness case observations and verified lifecycle
cleanup. It binds exact sources/dependencies, case/run/attempt, protection/readback,
results and fresh cleanup attempt/identity/record, without raw token/proof/provider
or credential/factor/browser payloads. Fixed errors do not stringify exceptions.
Reports are historical source/fixture observations, not signed neutral possession
receipts or authentication of supplied Python objects. Missing cases/cleanup
cannot pass; protected-machine scope refuses. Neutral APIs/pins remain unchanged.

The focused isolated matrix passed **88 tests**, including actual owning proof
verification with separate janitor/readback processes on success/failure/cancel.
Only the exercised receipt case is recorded in those runs; unexecuted matrix cases
stay not-performed. Complete synthetic report tests verify schema only. Cases cover
canary redaction, malformed scope/count/time/source/readback/cleanup, missing cases,
failed retry clearing and out-of-order cleanup checkpoint publication. No live
provider setup, protected dispatch, consumer lock or human approval is supplied.
Feedback stays deferred; neither historical blocked write was replayed.

### T011 expert review and provenance correction

All nine local expert roles completed. Reliability reproduced a P2 attribution
race: readback capability rotation during a callback could verify the old
service's record but label it with the replacement identity. Finalization now
captures one capability per attempt and uses its target and identity consistently.
A tracked rotation regression covers the actual record-return path. The focused
receipt matrix now passes **89 tests**. QA independently ran the original 88.
Standalone Sonar's one conventional dictionary construction and two exception-
test setup findings were corrected without waivers; final analysis follows.

### Final T011 source verification and cleanup

Source/tests and HEAD stayed fixed at `2b809c0ebe132fad56dc565b3d895667cf218b79`
through the complete ordered sequence: **1,185 tests passed**, including **89 T011
cases**, zero failures/errors/skips. Both pin verifiers, syntax, plain/strict
validation and all five canonical pinned OpenSpec items passed. Full JUnit SHA-256:
`d5ec271061eb7778bdf6cbef41f9277fb2d15f897390192c596073b1a80cd2fd`.

The native network-none, unprivileged disposable-container matrix passed **883
tests**, zero failures/errors/skips, including **18 R01 anchors**. Selected owning
code was clean at `bb0e9dae89a771b05f6c235d0a77237288b95c85`; neutral pins
remain unchanged. Matrix JUnit SHA-256:
`7b24c0ce4dc6079f6814208082a72fd5341fd9d60f8d83ec86afe6a9cae21408`.
The source/projects bind stayed read-only, only the owned evidence tree was
writable, and no provider/profile/SSH/Docker-socket mounts were supplied.

All nine expert roles completed. Reliability independently closed its provenance
race with three focused tests. Standalone Sonar reports zero issues in final
config, lifecycle, evidence, receipt tests and matrix contract. No rule, threshold
or issue status was waived. Hosted CI/review are checked separately at publication.

Independent cleanup readback accounted for **31 recorded worker generations**:
20 ordinary-bench PID/start-time identities were absent; the private namespace
holding the other 11 was gone with the owned disposable container. No attributable
helper remained. All three owned focused/full/native fixture roots were removed
and absence verified. QA/reliability reviewers removed and verified their own
roots. Reports/logs remain outside source. This receipt-only follow-up changes
no tested source, tests or workflow.

Only structural source/fixture report scopes are supplied. Protected-machine
promotion, selected operational services, provider setup/dispatch, consumer-lock
acceptance and human/domain assurance remain separate. Feedback stays deferred;
neither historical blocked write was replayed.

### Hosted T011 assertion-quality correction

The first published candidate's Sonar quality gate passed, but an explicit issue
query found ten test-only `python:S9073` findings that standalone analysis did not
report. Each composite assertion is now split into its equivalent individual
assertions; no condition, expectation, rule or threshold is removed or waived.
Collected node identities and runtime source are unchanged. A fresh complete
ordered sequence and native matrix qualify the corrected test source below.
GitHub Codex review was explicitly requested but refused by the account's review
usage limit; no completed bot review is claimed.

### Corrected T011 final verification

The complete ordered sequence was repeated with source/tests and HEAD fixed at
`4408c6a5a71a32b8ade921e56e853c7385129c72`: **1,185 passed**, zero failures,
errors or skips, plus all pin/syntax/plain+strict/pinned OpenSpec gates. JUnit:
`29bf770829104e81b0ab2cc06e187c50a79828152194c20066013ead53e45c4f`.
The fresh native offline matrix passed **883 tests**, zero failures/errors/skips.
Matrix JUnit:
`0fc1b2578835ad65edcfc8356ca01fe2cfb5255276d349e2cd7809bf86a9ae88`.

QA independently verified the assertion change by AST equivalence and reran all
89 receipt tests successfully. Standalone analysis of the corrected tests reports
zero issues; fresh hosted issue/quality results are checked at the updated PR head.
No expectation, rule or threshold was removed or waived.

Independent readback accounted for another **22 worker generations** (11 ordinary,
11 in the removed private namespace), with no attributable helper. Both additional
owned fixture roots were removed and verified absent. Across retained T011 run
records, cleanup now accounts for **53 generations**, both disposable containers
and all five owned focused/full/native roots; reviewer roots were independently
removed too. This final receipt-only commit changes no tested code/tests/workflow.
Source/fixture scope and all later operational/human gates remain unchanged.
Feedback stays deferred; neither historical blocked write was replayed.

## T012 source commissioning — 2026-11-13

Brett ratified #58 at `4916476364f79568bc09a14c41d44f4d1c474cdc` for source
acceptance only and commissioned T012 in isolation. All runnable checks passed,
with no unresolved review threads. The exact head merged normally as
`a3867ed906f4da505a0b14d8643fde1dded2d1bf`, tree
`fe072c6146d9412e1891578ff27a06c233f7618f`, matching the ratified tree.
No admin bypass was needed; no main-triggered CI result is inferred.

The candidate prepares a manual caller and same-commit local reusable workflow,
job-scoped permissions, immutable checkout/action pins and independent admission
before environment selection. Readiness binds trusted source/configuration,
actual existing environment protections, separate case/run/attempt operation
authority, external scheduler registration/readback and active lease. It repeats
after environment approval. The CLI blocks with production hosting unselected,
before emitting environment/ready outputs or requesting any token. Qualify/cleanup
remain explicit not-performed integration handoffs; no fixture fallback can pass
live qualification. A future cleanup client must preserve independent T009 authority
after proof expiry/hard runner death. No workflow dispatch or provider setup occurs.

Source validation uses actionlint and isolated readback/CLI/YAML tests; full gate,
expert review and exact-head hosted evidence follow. No new neutral contract, pin,
release or consumer lock is supplied. Feedback stays deferred; neither historical
blocked write was replayed.

### T012 local expert and static review

All nine expert roles completed with no actionable findings. QA independently
ran the original 79 cases and the final **80-case** suite, zero skips. Security
verified the actual CLI/context/OIDC/environment guards; reliability exercised
clock regression, expiry, plan rotation and lease revocation. Reviewers removed
and verified their owned temporary roots. Standalone analysis found one regex
convention issue; it is corrected with `\d` plus explicit ASCII mode, preserving
numeric identity semantics. A new Unicode-digit refusal regression verifies no
widening. No rule, threshold or expectation was waived. Both workflows pass
`actionlint`; final ordered and native qualification follow at fixed source.

### T012 qualification fixture correction

The first complete run at `458b2f2fa7c12042b42a0b29589196e25cdd7043`
reported one existing custody integration failure (`service-unavailable`) and
1,264 passes. The required native matrix passed 963 cases, three focused repeats
passed, and a fresh unchanged-source ordered run passed all 1,265 plus the other
gates. The initial failure remains retained rather than counted as a pass.

Investigation then deterministically reproduced a readiness publication race in
the owned test fixture: direct `Path.write_text` exposes an empty ready file before
the port is written; a waiting consumer can select HTTPS's default 443 rather than
the fixture's ephemeral port. A private delayed-writer wrapper reproduced the
same failure mode on the actual owning-proof case. Delayed atomic publication
passed. Port-443 connections were intercepted locally in the diagnostic, so no
unrelated listener was contacted. This proves the fixture defect/failure mode;
the original failed attempt did not retain its endpoint/cause detail.

As a bounded validation amendment, the fixture now publishes the complete ready
port via sibling staging plus atomic replacement, removing failed staging. Two
tracked paused-writer/failure regressions fail against original direct publication
and pass against the correction. All 61 custody cases pass. Reliability independently
passed both regressions and the formerly failing owning-proof case; QA independently
confirmed deterministic red/green. Existing TLS, service-positive check, valid-preimage
denial, readiness deadlines and cleanup assertions remain unchanged. No retry,
relaxed timeout, neutral API or production behavior is introduced. Standalone
analysis of both touched test files reports zero issues. Fresh complete/native
qualification follows at the amended source.

### Final T012 source verification and cleanup

Source/tests and HEAD stayed fixed at `90a4f90d89b3760e542176b9dc3d492f69063be6`
through the final complete ordered sequence: **1,267 tests passed**, zero failures,
errors or skips, including **80 T012 workflow tests** and both fixture publication
regressions. Both pin verifiers, syntax, plain/strict validation and all five
canonical pinned OpenSpec items passed. Full JUnit SHA-256:
`9a049f67dd52dc2c641569c9ab9b60d66b16010127b583843fd7ad7b47f13ca2`.

The fresh native network-none unprivileged matrix passed **965 tests**, zero
failures/errors/skips, including 22 R01 and 8 G03 anchored cases. JUnit SHA-256:
`ad143b9f5f5e19cd3d327e112eea1288947fa71d4c0761ef1b3d213fcb49c6c7`.
The explicitly selected owning source stayed clean at
`bb0e9dae89a771b05f6c235d0a77237288b95c85`; neutral pins are unchanged.
Source/projects were read-only in the private container; only the owned evidence
tree was writable, with no provider/profile/SSH/Docker-socket mounts supplied.
Both prepared workflow files pass actionlint. Standalone analysis reports zero
issues in all changed Python files. No rule, threshold or expectation was waived.

All nine expert roles completed. QA verified all 80 workflow cases; security and
reliability independently exercised their boundary cases. Both QA and reliability
independently verified the fixture publication correction, including deterministic
red/green and the original owning-proof case. The original failed complete run,
focused repetitions and pre-amendment passing complete/native runs remain retained.

Independent readback accounted for **55 recorded worker generations**: 33 ordinary
PID/start-time identities were absent; private namespaces holding the other 22
were gone with both owned disposable containers. No attributable helper remained.
All eight owned focused/reproduction/full/native roots were removed and absence
verified. Reviewers removed and verified their own roots. Logs/XML remain outside
source. This receipt-only follow-up changes no tested code/tests/workflow.

Only workflow preparation is supplied. Production hosting remains unselected;
actual CLI phases block before outputs/OIDC, and live qualify/cleanup integration
and protected receipt promotion remain T013/T014 source/operational gates. No
protected workflow dispatch, environment/credential setup, consumer lock, human
approval or domain effect is performed. Feedback stays deferred; neither historical
blocked write was replayed. Hosted CI/review is checked at the published head.

### Hosted T012 fixture-access correction

The first candidate's hosted Sonar gate passed, but explicit issue readback found
one test-only S8993 fixture-access finding not reported by standalone analysis.
The lease-revocation test now uses the same lease fixture already prepared by
`w`, rather than a second dynamic lookup. Required late construction remains
inside the fixture after configuration preparation, preserving setup order.
No runtime code, assertion, collected identity, rule or threshold changes.
Fresh complete/native checks qualify this corrected test source below.

### Corrected T012 final verification

The complete ordered sequence ran again with source/tests and HEAD fixed at
`14ea254b1ec856f209c6fdc7463c8be02275489e`: **1,267 passed**, zero failures,
errors or skips, plus all pin/syntax/plain+strict/pinned OpenSpec gates. JUnit:
`e66da8d06f357b35ae00e04383a2346128bf726577889352582441ce0ffd7668`.
The fresh native offline matrix passed **965**, zero failures/errors/skips. JUnit:
`80f14762efa33755563be1c2b1795ab62076ced6e9f6673ce6aff88601fd33a0`.

QA independently passed all 80 workflow cases, verified the stored lease fixture
is the same cached object as before, and matched the exact unchanged collected
node fingerprint. Standalone analysis of the corrected test file reports zero
issues. Fresh hosted quality/issue readback follows at the updated PR head.
No rule, threshold or expectation was removed or waived.

Another 22 recorded worker generations were accounted for (11 ordinary, 11 in the
removed private namespace), and no attributable helper remained. Both new owned
fixture roots were removed and absence verified. Across the retained T012 records,
cleanup now accounts for **77 generations**, all three disposable containers and
all ten owned focused/reproduction/full/native roots. Reviewers removed and verified
their own roots too. This receipt-only follow-up changes no tested code/tests/YAML.
The source-preparation boundary and later T013/T014 operational/human gates stay
unchanged; no protected dispatch or setup occurred. Feedback stays deferred;
neither historical blocked write was replayed.

## T012 source acceptance and T013 preparation — 2026-11-13

Brett ratified #59 at `948ea81d7cdce35f5d006c747680a6b9fde37a29` for source
acceptance only and commissioned operational selection/scoped authorization
preparation. Fresh preflight verified the exact head, all runnable checks green,
clean/mergeable state and no unresolved review threads. Normal merge completed
at 22:10:25 UTC as `9e1d75d46dfd6f170e27cbe7701f34288428ee6f`, tree
`43ac0bd082850da53c54d392c44de069aeeab0b2`, exactly the ratified tree. No
administrative bypass was used. No merge-commit Actions run was returned during
preparation; PR CI is not represented as post-merge CI. This acceptance adds no
new completed GitHub Codex review to the T012 review evidence above.

The [selection packet](operational-inputs.md) replaces stale early-slice status
with verified source/repository identities and workflow content digests, the
existing environment's ineligibility, the portable-service route, a proposed new
nonproduction environment and each missing service/host/admin/state/lifecycle
selection. Read-only GitHub inspection found only `copilot`, with no protection
rules and administrative bypass enabled. It is preserved, not selected or changed.
The authenticated account is `brettheap`, ID `1513478`; dispatcher/reviewer roles
remain unselected. No target-provider deployment is inferred from these facts.

The [authorization draft](scoped-authorization.md) separates exact-target setup,
one future bootstrap dispatch, actual run/attempt authority and independently
bounded generation cleanup. It requires named administrators, a resource
allowlist, budget/window, source acceptance, authenticated readback and explicit
decision/revocation records before any operative approval. Missing values remain
documented, not serialized as runtime handles or self-approval flags. T013 stays
unchecked; no operational grant or executable config is emitted.

A newly verified [bootstrap source prerequisite](workflow-bootstrap.md) blocks
an operative first dispatch: the dispatch config digest covers the run ID/attempt
that must match the actual run. An unprivileged offline probe of the existing
synthetic configuration with the real canonical digest and validator passed the
base and refused stale independent approval after either run ID or attempt alone
changed (`runtime-config-unapproved`). It used no endpoint or fixture service.
The proposal preserves exact run binding through a future independently
authenticated static-selection/bootstrap stage. It is a factory-governed source
proposal, not a change to the accepted grammar or runtime code. Hosting clients,
qualify/cleanup integration and protected receipt promotion still require review.

This preparation edits documentation only. No environment/provider setup,
protected dispatch, token request, credential issuance, pin/consumer update,
signing use, human assurance or domain action was performed. Feedback stays
deferred; neither historical blocked write was replayed.

Preparation checks passed in py-bench as UID 1000: both pin verifiers, YAML
syntax, plain/strict adapter validation (zero errors/warnings), and the pinned
OpenSpec CLI's five canonical items. Local links/portable paths and preservation
of the T001/T013–T015 owner checkboxes were checked. Workflow, runtime and pin
bytes still match the accepted merge. No full runtime suite was rerun for this
documentation-only packet; the retained T012 suite evidence is unchanged.
The digest probe used no fixture services, so it created no fixture processes,
keys or state requiring cleanup. No T014 or deployed cleanup result is claimed.

## Dispatch bootstrap amendment commissioning and initial qualification

Brett commissioned the bootstrap fix through factory/adapter governance with
setup and dispatch still unauthorized. New factory change
`fix-protected-runtime-dispatch-bootstrap` preserves all accepted baseline/origin
fields and hands off to this feature's T012B. The separate static selection
profile commits all runtime fields except assigned run ID/attempt. Independent
bootstrap readback then binds the final full digest/grant to actual source, repo,
case and run/attempt before existing admission. No operational client, provider
authentication or atomic authority service is supplied by this candidate.

Initial adapter source `ce8687baa1f6fc703e33be1d41a2e79e3cd4772f` passed the
complete ordered pin/syntax/plain+strict/pytest/pinned-OpenSpec sequence: **1,348
passed**, zero failures/errors/skips. The native unprivileged network-none
read-only-source matrix passed **1,046**, zero failures/errors/skips, with 38 I04
and 35 R01 anchored nodes. Runtime/neutral pins remain unchanged. Both workflows
pass actionlint. The first native attempt stopped at harness preflight because
the operator had not created its required private root; the corrected fresh
preflight and full matrix passed without product/harness changes. That refusal
is retained and is not counted as a passing run.

All nine expert roles completed source inspection. Security, reliability and QA
independently passed all 161 bootstrap/workflow cases and removed their owned
temporary fixtures. Standalone analysis found zero issues in the four runtime/CLI
files and workflow test file, and one S5778 assertion-scope issue in the bootstrap
test. The correction prepares encoded input/trust before pytest.raises so only
the intended validator can satisfy that assertion. It changes no runtime code,
assertion expectation, collected identity, rule or threshold. Final qualification
at this corrected test source follows.

Independent cleanup readback accounted for 22 recorded worker generations:
11 ordinary identities absent and 11 inside the removed disposable namespace.
No attributable helper remained; the owned container and all three focused/full/
native fixture roots were removed and absence verified. Logs/XML and redacted
audit remain outside Git. Initial full JUnit SHA-256:
`3a2d0dc536ee99e0fca0755a377e82ae2e5e80a36404e27d26abf76a36f7ca8e`;
native JUnit: `102d2f306ffaa8ec11781af40c4951972f248515d7825283dff902af8c77ae47`.
No deployed cleanup, live bootstrap authentication, setup, protected dispatch,
OIDC mint, human approval or consumer acceptance is claimed. Feedback stays
deferred; neither historical blocked write was replayed.

### Corrected bootstrap final qualification

Source/tests and HEAD stayed fixed at
`38d205c0b6b175afff2b38f2968730a307b74ed9` for the fresh complete ordered
sequence: **1,348 passed**, zero failures/errors/skips, both pin verifiers,
syntax, plain/strict validation and five pinned OpenSpec items passed. Full
JUnit SHA-256: `5b2ab4d7a16f0bce345680337f07e2d305c0e306c48e42e192e949679103f92e`.
The fresh native network-none unprivileged matrix passed **1,046**, zero
failures/errors/skips, with all 38 I04 and 35 R01 anchors. JUnit SHA-256:
`fdb61b702685c1403343b690701e8caaaaaa01a2d558d9a74dc222920f1b83fd`.
The owning source remained clean at
`bb0e9dae89a771b05f6c235d0a77237288b95c85`; neutral pins are unchanged.

Standalone reanalysis of the corrected test reports zero issues, completing
zero-issue results for all six touched runtime/CLI/test Python files. All nine
expert roles completed; no actionable finding remains. Security, reliability
and QA independently passed the full 161 bootstrap/workflow corpus. Test-only
assertion setup changed no expectation or collected identity. No rule, threshold
or required case was waived. Both workflows pass actionlint.

Independent cleanup readback accounted for another 22 worker generations
(11 ordinary identities absent, 11 inside the removed private namespace), with
no attributable helpers. Both new owned full/native fixture roots and the
second owned qualification container were removed and absence verified. Across
initial/corrected qualification, 44 generations, two containers and all five
owned focused/full/native roots are accounted for. Reviewer-owned roots were
separately removed and verified; redacted logs/XML/audits remain outside source.

T012B is complete as isolated candidate implementation. Paired factory #1311
and adapter exact-head source acceptance remain pending. Default production
bindings still refuse before outputs/OIDC; actual authenticated bootstrap and
atomic authority consumption, hosting integrations and live receipt promotion
remain separate. T001/T013/T014/T015 owner/operational checkboxes stay unmarked.
No setup, protected dispatch, credential issuance, signing operation, consumer
pin promotion or human/domain acceptance occurred. Feedback stays deferred;
neither historical blocked write was replayed. This receipt-only follow-up
changes no tested runtime, test, workflow, dependency or pin bytes.

## T013 refresh after accepted bootstrap landing — 2026-11-13

Brett ratified factory #1311 at `6dadf188a0afa22e3c205561299f6045a9c95359`
with adapter #60 at `78e7bbeabca250073d5896154ccc99bb163116cc` for source
acceptance only, explicitly retaining the setup/dispatch prohibition. Factory
landed first as `f2fb60f04c8229f4343e25a0155418f2f737d73a` under the standing
self-authored-PR approval exception; adapter landed normally as
`61fbe41f7e08e831e0b15c2c97ea6ff386f587f3`. Both merged trees exactly match
the ratified trees. The current instruction commissions post-merge CI verification
and this refresh, with no new operation.

Factory post-merge CI is verified at the exact merge above: all 5 observed main-triggered Actions runs passed, including [pytest-suite 43526439944](https://github.com/opensoft/openXfactory/actions/runs/43526439944). Its pytest result was **10391 passed, 6 skipped, 338 deselected, 9 warnings, 745 subtests passed**. The JUnit guard recorded `selected=11142`, `passed=11136`, `skipped=6`, `failures=0`, `errors=0`; its named freshness check passed. This is independently observed main CI, not a reuse of the PR run. Main Sonar reported `neutral` / `Quality Gate not computed`; the source PR quality gate is a separate result.

Fresh non-secret GitHub readback still reports only the existing unprotected
`copilot` environment, with admin bypass enabled; preserve it. Qualification
workflow runs remain zero. Repository/owner IDs and default workflow permissions
are unchanged. OIDC configuration reports `use_default: true`,
`use_immutable_subject: true`, prefix
`repo:opensoft@638385/openXwallet@1347887821`. This is configuration readback,
not a minted token or approval of a complete subject/audience.

The selection packet now records accepted source/merge/tree identities, current
workflow/CLI/bootstrap content hashes and the explicit static-dispatch/full-run
interface. Source bootstrap acceptance is resolved. The open decisions are the
actual host, bootstrap authority/principal/authentication/atomic consumption,
other trusted clients and administrative separation, reviewer/dispatcher, state,
lifecycle and budget/window/resource/authority scope. Per-run plan/lease and
grant binding occur after assigned run identity and before admission; pre-dispatch
setup readiness does not require predicting that identity.

The authorization draft separates accepted source from four NOT GRANTED stages:
setup, one dispatch, actual run/attempt authority and exact-generation cleanup.
Only selected creation names/parents can be approved before created IDs exist;
fresh effective readback is required before dispatch/use. No executable config,
grant, service endpoint, credential or approved actor is invented. Human/domain
acceptance and live protected receipt promotion remain separate.

This refresh changes documentation only. Runtime, tests, workflows, dependency
locks, neutral pins and frozen factory origin fields are unchanged. The existing
source/fixture qualification receipts remain evidence within their stated scope;
no new runtime suite or deployed qualification is inferred. T001/T013/T014/T015
owner/operational checkboxes remain unmarked. Feedback stays deferred; neither
historical blocked write was replayed. Document/source-reference checks follow.

Refresh validation passed in py-bench as UID 1000: both pin verifiers, YAML
syntax, plain/strict adapter validation (zero errors/warnings), and all five
pinned OpenSpec items. Local links, portable paths and every listed immutable
source hash match accepted Git objects. Exact diff scope is seven documentation
files; runtime/tests/workflows/locks/pins are unchanged. T001/T013/T014/T015 remain
unmarked. No new runtime suite was rerun for documentation-only changes and no
fixture process/key/state tree was created. Final readback still has zero
protected workflow runs and no adapter merge-triggered Actions run.


## 2026-11-14 source ratification and ordered landing

Brett Heap explicitly ratified the three exact heads below **for source acceptance
only**, directed their landing in order when green, and commissioned T013
preparation. The instruction keeps setup/dispatch unauthorized, feedback deferred,
and both historical blocked writes unreplayed. Source ratification is recorded
on [factory #1312](https://github.com/opensoft/openXfactory/pull/1312#issuecomment-6877063524),
[adapter #61](https://github.com/opensoft/openXwallet/pull/61#issuecomment-6877063887)
and [adapter #62](https://github.com/opensoft/openXwallet/pull/62#issuecomment-6877064249).

| Source | Ratified head | Accepted merge | Ratified and merged tree |
| --- | --- | --- | --- |
| [openXfactory #1312](https://github.com/opensoft/openXfactory/pull/1312) | `b741ae396bc0c75622b69af6052b8cbacf9c57d2` | `6604b55b980cba0c507f1e9c5de9b715282b5c35` | `7e81f953d94c7178dff745a7d601a0bbbf65fa07` |
| [openXwallet #61](https://github.com/opensoft/openXwallet/pull/61) | `caa56dc001f677350edf620508e287d5c1862e53` | `6171f5f5c53cc44c809b3b9419cefe77367207a5` | `83342f410be05f12cf9f7c9df43de99c8e3159dc` |
| [openXwallet #62](https://github.com/opensoft/openXwallet/pull/62) | `62b270127e7407bef76c90ce4038d03f912d40a6` | `425606899116c4e7fe5d3c6fe3382c058081336b` | `16702109fe422966e4cfc2adf2aa58b6679102d1` |

Landings occurred in order at 12:11:09, 12:11:38 and 12:13:07 UTC on 2026-11-14.
Every merged tree was read back and equals its ratified tree. All runnable
exact-head source checks passed; no review threads were present. Factory #1312
used the documented standing self-authored-PR approval exception, because author
and authenticated user were both `brettheap` and only human approval was missing.
This was not reviewer approval and changed no check or repository rule. Both
adapter PRs merged normally. GitHub Codex was explicitly requested and
usage-limit-refused; corrected local expert-panel evidence remains distinct from
a completed connector review.

The portable authority is accepted **only as an isolated reference**. Its fixed
fixture profile, loopback service and simulated signed controller observations
are not actual GitHub authentication, deployed independence, human approval or
an operational host selection. Existing operational bindings still refuse before
environment outputs/OIDC. Workflow/entrypoint bytes and dependency pins did not
change in these three PRs. No release, consumer lock/pin promotion or live receipt
is supplied by this source acceptance.


## 2026-11-14 acceptance of T013 preparation and proposal commission

Brett source-ratified adapter #63 at `54dd1e1d4dc68b377cfa45024eb2be96c13f8bcc` and directed landing
when green, then preparation of the real GitHub bootstrap authentication proposal.
It merged normally as `be41830acd16a197041e3aabb0281208b185d8ee` at 2026-11-14T13:49:16Z;
independent provider tree `2f3b5745b779a4bf9bdf11590b097988f4e501d0` equals the ratified tree. All runnable
exact-head source checks passed; no review threads/requested changes were present.
Owner record: [#63 source ratification](https://github.com/opensoft/openXwallet/pull/63#issuecomment-6878228159).
The instruction authorizes proposal preparation only, not the new admission-OIDC
profile, its implementation, token mint, App/permission change, setup or dispatch.

Factory change `add-github-bootstrap-authentication` and the
[adapter proposal](github-bootstrap-proposal.md) prepare the next source decision.
T012G-M are pending proposed source tasks, not an implementation commission.
The earlier default/reference profile and no-output/OIDC refusal are unchanged.
T001/T013/T014/T015 remain unchecked, feedback deferred, and neither historical
blocked write is replayed.


## 2026-11-14 GitHub bootstrap source ratification and isolated commission

Brett Heap explicitly ratified factory #1314 at
`94bf0f43704fe8899dc48981263615039eac0d89` with adapter #64 at
`ff9bd72278a5b5ed14fda2eddb18265f6a109814` for source acceptance, directed
ordered landing when green, then commissioned implementation/testing of
T012H–K in isolation. This supplies T012G's actual owner decision, including
the new bootstrap-only admission OIDC policy and source trust/failure bounds.
It authorizes no actual credential/App configuration, token mint, setup or dispatch.

Factory #1314 merged first as `3432baf6d929112be283d3daa1a4330a4130ab64`,
using the standing self-authored approval exception after all runnable checks
and exact-head Codex/local review passed. Its ratified and merged tree is
`040d1de2563c5b826ebd93e1c14f6bc9d24688c8`. Adapter #64 then merged normally
as `a352ebc7ed22f67ff9d759789f807573d9f66ff2`, with ratified/merged tree
`60fdb64a19eb87370439b988e9be833e873dd660`. No review threads remained.
Owner records: [factory](https://github.com/opensoft/openXfactory/pull/1314#issuecomment-6879201871)
and [adapter](https://github.com/opensoft/openXwallet/pull/64#issuecomment-6879205316).

Implementation is a subsequent candidate from the accepted adapter merge,
not automatically source-accepted. Operational selections and deployed
qualification stay at T013–T015; their owner checkboxes and T001 stay unchecked.
Feedback remains deferred; neither historical blocked write may be replayed.


## 2026-11-14 isolated GitHub bootstrap T012H–K candidate

Commission: the exact source ratification/ordered landings and isolated H–K
instruction are recorded in the preceding owner-decision section. T012G records
that owner act; T012H–K are implemented/tested in this subsequent local candidate.
T012L review/source ratification and T012M handoff remain pending. T001/T013–T015
stay unchecked. Candidate branch: `017-github-bootstrap-auth`, based on accepted
adapter merge `a352ebc7ed22f67ff9d759789f807573d9f66ff2`.

The separate bootstrap verifier/client uses actual RSA and bounded verified TLS,
with exact selected audience/phase/source/run policy. Protected proof verification
and its environment requirement are unchanged. Signature-valid positive controls
and audience-only/environment-only negatives run before custody. The broker
persists exact dispatch bytes and explicit case/window/source/actor scope before
credential/dispatch I/O, rechecks fresh source and approval after TLS, and retains
consumption on crash, expiry, revocation, lost/insufficient response or cancellation.
No retry/reset/newest-run path exists. Versioned read-only API correlation checks
actual run/first attempt/source/reusable/actor/job facts, current protection and
originating-human/App reviewer separation; final run/authority checks repeat after
blocking reads. Missing/ambiguous provenance or an exhausted budget refuses.

The opt-in phase composition preserves three workflow inputs and seven runtime
roles. Source admission gains bootstrap token-request capability; protected
admission uses its separate route after environment approval. Default production
bindings still refuse before token access/outputs. Qualify/cleanup remain explicit
unperformed hosting handoffs. No listener, App setup, operational selector,
provider credential, neutral API/pin change or receipt-scope promotion is supplied.

Final qualification used the existing reviewed Python closure and clean accepted
owning code `bb0e9dae89a771b05f6c235d0a77237288b95c85`:

- Ordered scoped submodule init, both pin verifiers, syntax gate and plain/strict
  validator pass. Full suite: **1,609 passed, zero failures/errors/skips**.
- Required native matrix: **1,307 passed, zero missing/deselected/skipped/non-passing
  cases**, including 183 new cases. The network-none disposable bench-image
  container mounts source read-only, exposes no host credentials/socket and drops
  groups/capabilities with no-new-privileges before pytest and helper exec.
- Existing I/G/S/L/R and B01–B03 anchors remain; B04/B05 add actual RSA/loopback TLS,
  single-claim proof barriers, durable broker/correlation/phase negatives and one
  owning-verifier-accepted proof/replay plus independent success/failure/cancel/
  runner-death cleanup. Provider observations and dispatch remain deterministic
  fixtures; no bootstrap OIDC token was requested and no provider dispatch endpoint was called.
- Five pinned adapter OpenSpec items and strict governing factory packet validation
  pass. The 21 runtime/test/workflow file hashes were unchanged through final
  qualification. Required module counts/full-node fingerprints were updated only
  for the three new test modules and the accepted workflow-policy assertion update.
- Independent cleanup checked **107 process generations**, **52 integrated
  preservation records** and **32 retained consumed dispatch journals** across
  this task's runs. No attributable helper remained; both disposable containers
  were absent. Eight exact owned temporary roots were removed after verification.
  Runtime cleanup preserved retained/shared state before disposable-fixture teardown.
  Bench containers remained running with their original 2026-11-11 start times.

The initial full invocation omitted matching TMPDIR and correctly failed two
neutrality export-root tests; its other 1,604 tests passed. Corrected invocation
and targeted controls passed without changing that gate. A final integrity review
also added explicit retained case/window scope and wire/scope corruption controls,
then repeated full qualification. `unshare --net` was unavailable inside py-bench;
the mandatory native run used the existing reviewed network-none container route,
not a relaxed isolation check. External token-response metadata is projected out
using the required `value` field; internal envelopes remain closed.

Factory #1314 post-merge CI passed all emitted workflows, including pytest. Adapter
#64 emitted no separate main run; its exact ratified PR checks passed before landing.
This new local implementation has no hosted candidate CI or Codex/panel review
claim; those are T012L. Both protected workflows were independently re-read with
**zero runs**. Actual provider subjects/behavior, callback authentication/administration,
worker exclusion, coarse App scope, source-update controls and live qualification
remain T013/P01 decisions. Setup/dispatch are NOT GRANTED; feedback is deferred
and neither historical blocked write was replayed.

Retained private verification artifact digests (disposable fixture bodies removed):

- `qualified-full.xml`: `5301625f9e68c56843c89e41b8c92b8d805017695bfc5f1d7ce6f689980483ef`
- `qualified-full.log`: `7cac152c4e45ef2540755f2c5324a064b28b369616ab3dcf48532eed0647aba6`
- `qualified-matrix.log`: `583a83fba6f4bd5168d04dec65e038e1cfca5713a29738413ee4358c65399f0a`
- `qualified-runtime-inputs.json`: `92495f3131914872d70d4f1bdc146aad091566a397220d352c14e073f3583edb`
- `cleanup-audit.json`: `d94fe22ede1f9dc2e5fb5a3fd0f6a62e95f537d8c241745d0631be4bbd18203e`


## 2026-11-14 T012L local review and revised source qualification

The owner commissioned publication, ordinary hosted source CI, local Codex review,
resolution of findings and presentation for source ratification. The owner explicitly
chose local Codex review for this candidate, waiving the hosted `@codex review`
request. [Adapter #65](https://github.com/opensoft/openXwallet/pull/65) contains
T012H–K implementation and these review corrections over accepted #64. The governing
factory #1314 is already accepted; no additional factory grammar change is needed.
T012L stays unchecked until actual owner source acceptance; T012M and T001/T013–T015
remain unchecked. This publication supplies no owner ratification or merge authority.

The local review uses the coordinator, nine standard expert roles and one additional
GitHub Actions/OIDC expert. The corrected source checkpoint is
`d0ff4e5d0ba4d144b6cb8f2b38f401b0d73ce11c`. Runtime/test/workflow bytes are bound by a
21-file SHA-256 manifest; the subsequent qualification-record commit changes
feature documentation only. Review found and corrected:

- The workflow parser accepted a command prefix and final phase word. It now
  checks the complete command, exact job guards, closed fields and fixed step order.
- GitHub REST requests lacked User-Agent. All four source clients now send the
  fixed internal User-Agent; actual loopback TLS positive/missing-header controls
  exercise the wire behavior.
- Documented GitHub caller/reusable path representations refused unnecessarily.
  Explicit selected-main variants now map to one binding, with exact SHA and ref
  agreement and no generic path/case/suffix normalization.
- Journal work could finish after a Decision cutoff. Reservation/recording receive
  remaining I/O budgets, and immediate post-return checks refuse before credentials
  or successful return while preserving consumed/correlated state.
- Session fresh reads lost the original cutoff. They now retain the enclosing
  epoch deadline and earliest accepted readback expiry. Each read retains its own
  existing monotonic Decision bound; there is no new cumulative monotonic promise.
- The signature-negative control failed canonical decoding before crypto. It now
  flips decoded signature bytes and canonically re-encodes them; a verify spy and
  deliberate no-op crypto mutation establish that the negative reaches verification.
- A normal concurrent SQLite commit could unlink a DELETE sidecar between exists
  and lstat. Direct lstat tolerates only FileNotFoundError while preserving unsafe
  sidecar checks. A real second-connection commit regression fails with the exact
  old implementation and passes with the correction.

The original 38 valid hosted quality findings and a subsequent local duplicate-literal
warning were corrected. Actual local Sonar snippet analysis of nine runtime modules
and three test modules reports zero issues. Two initial S8703 findings were independently
assessed as false positives by security and static experts: the private helper receives
trusted constructor-selected endpoints from its parent over an anonymous pipe, has no
ambient credential, exposes no listener, validates TLS and follows no redirect. This
assessment depends on trusted hosting; worker-controlled endpoints or ambient identity
would require a new review. No analyzer rule or quality gate is disabled. Fresh hosted
analysis and issue disposition remain distinct from these local results.

Revised qualification, with the accepted clean owning code selected explicitly:

- Scoped submodule initialization, both pin verifiers, syntax gate, plain and strict
  adapter validation pass; five pinned adapter OpenSpec items and the strict governing
  factory change pass.
- Full regression: **1,641 passed, zero failures/errors/skips**.
- Mandatory native network-none matrix: **1,339 passed, zero missing, deselected,
  skipped or non-passing cases**. All 1,307 previously published nodes remain;
  32 substantive review regressions extend only the three new bootstrap modules.
  All 215 GitHub-bootstrap cases independently pass in the QA review.
- QA mutations fail as expected: two signature controls fail under no-op crypto,
  nine graph controls fail under the legacy validator, and the concurrent-sidecar
  control fails under the exact initial stat implementation. No mutation changes
  committed runtime code.
- All 21 runtime/test/workflow input hashes remain unchanged through final qualification.
  Neutral pins, protected-proof verification and existing offline entrypoints remain
  unchanged. First-pass qualification was superseded when closure found the final
  source corrections; no interrupted or superseded run is counted as final acceptance.
- Independent cleanup audited 61 recorded process generations, 28 integrated
  retained/shared-resource preservation records and 12 consumed correlated dispatch
  journals. No attributable helper remained; both disposable matrix containers were
  absent. Seven exact coordinator-owned fixture roots were removed after audit;
  JUnit/log/manifest/review receipts remain private. Reviewer fixture cleanup is
  independently recorded in each final receipt. Bench start times and accepted
  owning source remain unchanged.

Both protected qualification workflows still have zero runs. Provider observations,
identity tokens and dispatch remain fixtures; no real bootstrap token was requested
and no actual protected dispatch was made. Hosting/authenticated callbacks, actual
subjects and provider behavior, worker/admin exclusion, App scope, source-update controls,
operational grants and live qualification remain T013/P01 obligations. Default bindings
still refuse before token access/outputs. Setup/dispatch remain NOT GRANTED, feedback
stays deferred, and neither historical blocked write was replayed.

Retained private artifact SHA-256 values:

- `qualified-full.xml`: `4b8e3bd2c8ed983d0bf76533e02dde3482619c311665db20c0eebf991fe364e7`
- `qualified-matrix.xml`: `2329a162b5f21550c8f13aabea17eccf4a7aeb60e43d9fcf7b3346468df9ceb4`
- `reviewed-runtime-inputs.json`: `d73b793951958667db3791832660b1dea77de60dd04ba0979cf91ee5fda8cc52`
- `cleanup-audit-final.json`: `43a4d2ca97af48c45a28904129451688f1820274e0aed14a5644046fb190d7bb`
- `fixture-removal-final.json`: `7406b286ef67894265719338e3a3cae35512595adade42794fe21098311f6773`
- `static-sonar-closure-final.json`: `e358e2a190d90b2c46dfbfc9f1e87176ee019909221d4f4eca3d3fa6d841bcbd`


## 2026-11-14 #65 source acceptance and T012M handoff

Brett Heap explicitly ratified openXwallet #65 at
`ab34ff4ec4fe27d56c8fd09c99614785c23e760f` for source acceptance only and directed
landing when green, then T012M completion and T013 refresh. The instruction keeps
setup/dispatch unauthorized, feedback deferred and neither historical blocked
write replayed. [The owner record](https://github.com/opensoft/openXwallet/pull/65#issuecomment-6881983735) records this actual source decision.
T012L's owner acceptance is satisfied; T012M is the commissioned accepted-source
reconciliation and handoff, not an operational selection or grant.

#65 merged normally at `2026-11-14T18:09:45Z` as
`366533bed77293b096b0a7dbda61399ff5dbafe5`. Independent GitHub readback gives equal
ratified/merged tree `669a1b431f17d360fcf827a749a756e863ec9ed8`. All seven runnable
ratified-head checks passed; Sourcery was skipped. No review threads remained.
Local Codex/expert review by the coordinator plus ten reviewers closed the source
findings; the owner explicitly waived a hosted connector request. Sonar's quality
gate passed with zero open PR issues after source corrections and two documented
false-positive dispositions, without changing rules/gates. The source review
checkpoint `d0ff4e5d0ba4d144b6cb8f2b38f401b0d73ce11c` and accepted final head differ
only in feature evidence documentation, with all 21 runtime/test/workflow hashes
unchanged. Local full/matrix qualification passed 1,641 / 1,339 cases with zero
skips; [hosted pytest](https://github.com/opensoft/openXwallet/actions/runs/43622459059)
passed 1,638 full cases with three documented shallow-history skips and all 1,339
mandatory cases without skips. Dedicated full-history jobs passed separately.

Read-only post-merge inspection returned zero Actions runs at the merge commit.
The ordinary validation workflows are PR-triggered; no main CI success is inferred
from PR checks or tree equality. No protected workflow was dispatched to create a
post-merge run. Factory #1314's accepted design/merge remains
`3432baf6d929112be283d3daa1a4330a4130ab64`; its already recorded source acceptance
is unchanged. No factory grammar, frozen origin, neutral API/pin, runtime, test,
workflow or dependency lock is changed by this handoff.

T012M refreshes [operational inputs](operational-inputs.md),
[scoped authority](scoped-authorization.md), [T013 decisions](t013-decision-record.md)
and [authentication handoff](bootstrap-authentication-plan.md), with consistent
current task/plan/spec/runbook/context references. The packet now records accepted
source/merge/tree and immutable content hashes, exact three dispatch inputs,
separate preflight bootstrap versus protected proof policy, implemented broker/
journal/API correlation, first-attempt-only behavior and no ambiguous retry/reset.
The obsolete active claims that the new bootstrap adapter was unratified or
unimplemented are removed; prior preparation evidence remains historical.

The source baseline is not an operational `accepted_commit` or complete source
selection. This documentation refresh and later hosting merges can change the
executing `github.workflow_sha` even when workflow content hashes agree. Actual
main-update coordination or bounded-residual-start acceptance, relying-party and
coarse App credential limits remain explicit operator decisions; enum labels
establish no deployed control. Authenticated bounded callbacks/issuance/hosting,
actual complete subjects and distinct proof audience, original human/App/reviewer
identities, target/protection/services, initialized retained stores and independent
cleanup/readback remain unselected. Live qualifier/cleanup and protected-receipt
source integration still require governed review/acceptance. T013 preparation
is refreshed; the actual T013/T014/T015 owner/operational acts remain incomplete.

Fresh read-only provider inspection at `2026-11-14T18:11:54.230954+00:00` confirms repository
ID `1347887821`, owner ID `638385`, default main and only existing `copilot`
environment ID `20677426348`, with no protection rules and admin bypass enabled.
It is preserved and ineligible for the pilot. Default workflow token is read-only
with PR approval disabled. OIDC remains default/immutable-ID with prefix
`repo:opensoft@638385/openXwallet@1347887821`; this configuration read is not a
minted token or full-subject approval. Caller workflow `417795073` and local
reusable `417795071` are active and both have zero runs. No resource, App,
credential, federation, permission or environment setting is changed.

T012L and T012M are complete in the implementation list; T001/T013/T014/T015
remain unchecked. Every setup, one-dispatch, actual-run authority and exact-generation
cleanup stage is NOT GRANTED. There is no executable config/grant, provider setup,
bootstrap token request, protected receipt, pin promotion, human/domain approval
or live qualification. Feedback remains deferred; neither historical blocked write
was replayed, and the optional PR-description update denied in the earlier turn
was not retried. Verification of this documentation-only handoff follows.


T012M documentation verification passed: scoped initialization, both pin checks,
syntax, plain/strict validation, **1,641 full tests with zero failures/errors/skips**,
five pinned adapter OpenSpec items and strict governing factory packet. All eleven
changed files are Markdown. All 116 recorded runtime/test/workflow/contract inputs,
including the neutral gitlink, are unchanged. All 73 relative links and seven
immutable Git-blob artifact hash rows verify; the portable feature pointer remains
unchanged. No new runtime test or source profile is introduced by documentation.
The accepted #65 zero-skip native matrix remains source evidence; ordinary PR CI
separately repeats mandatory conformance for this handoff candidate.

The coordinator plus nine local pre-PR experts completed architecture, performance,
security, QA, static/quality, API/integration, data-integrity, reliability and simplicity
review with no actionable findings. The final addition to the reviewed documents is
this factual verification record only. Local Codex review continues the owner's
local-review preference; no hosted connector review is claimed. Independently audited
cleanup checked 19 process generations, eight integrated retained/shared preservation
records and four consumed correlated journals. No attributable helper remained. The
one exact private fixture root was removed only after audit, with absence verified;
JUnit/log/hash/readback/review receipts remain retained. Benches and accepted owning
code remained unchanged. Every operational stage is still NOT GRANTED.

Private verification artifact SHA-256 values:

- `full.xml`: `6a4168ee0470113059b8946798b5b954e7fb7b6d3d7d90a1a0d9ca4e389d9e71`
- `document-consistency.json`: `8e835e5e2175114bd4ef4d746763be1f3c77fdfdc64b37e23d19c1f398c9dc93`
- `cleanup-audit-final.json`: `c4e8a7e086d426040a2178dd0082eb4d0f7c17d39281fd90437ec2edddcbbbb9`
- `fixture-removal.json`: `8d9763edd5778e7f42156370db8424c8ba9e1d6366328e862fd3aeaf1fbccdcd`
- `unchanged-runtime-baseline.json`: `063902907dc4cc2b495086aa87c5dc0026ceaef6c671a59b4ecb1a545104d68b`


## 2026-11-14 #66 acceptance and hosting/issuance proposal preparation

Brett Heap source-ratified adapter #66 at
`c8050f9eb1ffbcdbc7fdba66a032ca9649f25ae0`. It merged normally as
`5498a9b27d7a61daf8f4088ce85906cb436a2033`, with equal accepted/merged tree
`e3664990f55b49bfb7629b864816900d6b429491`. The
[owner record](https://github.com/opensoft/openXwallet/pull/66#issuecomment-6882506225)
records source acceptance only. Its seven runnable checks and Sonar gate passed;
local full qualification passed 1,641 cases without skips. Hosted full qualification
passed 1,638 with three documented shallow-history skips, and mandatory conformance
passed all 1,339 without skips. No merge-triggered CI or protected workflow run is
inferred from those PR results.

The subsequent user instruction commissions a factory-governed hosting/issuance
source proposal and Speckit plan using the recommended T013 design basis. It does
not commission implementation, appoint actors, approve actual operational inputs or
authorize any setup/dispatch. The new factory draft is
`add-protected-runtime-hosting-issuance`; this existing feature remains sole task
owner through proposed, unchecked T012N-V. See
[plan](hosting-issuance-plan.md), [research](hosting-issuance-research.md),
[interfaces](contracts/hosting-issuance.md), [model](hosting-issuance-model.md),
[selection basis](hosting-issuance-selections.md) and
[acceptance controls](hosting-issuance-acceptance.md).

Research identified a temporal commitment gap: static-v1 includes composition and
policy digests that depend on the actual run/process. The draft proposes a separate
static-v2 plan, read-only plan readiness, protected authorized staging, actual
measurement and independently recomputed final configuration, followed by unchanged
full admission. This material source decision requires later explicit owner
acceptance and isolated implementation commissioning; it is not silently applied
to accepted v1 or neutral APIs/pins. Hosting, actual issuance/provider/guest facts,
credential isolation and external watchdog capabilities remain future source/live
gates. No existing bench or Azure resource is selected by implication.

Only documentation changes in this preparation. No runtime tests, workflow runs,
provider writes, token requests or live qualification are performed. The private
security research artifact write was denied with only “blocked by policy”; it was
not retried or recreated. Findings returned in chat informed the separately
authorized proposal/plan documents. Feedback stays deferred; neither historical
blocked write nor the earlier optional PR-description update was replayed.


Planning validation passes: all five adapter OpenSpec items, strict new governing
factory change, factory code-surface/estate membership, proposal origin, sequenced-
after and former-ID declaration sweep. No history-arrival verdict was inferred
from a corpus-only former-ID run. New relative document links resolve and the
portable feature pointer/frozen factory README record block remain unchanged.
Only documentation/metadata changes; no runtime test suite is repeated for this
planning-only preparation. API/security/runtime research closure addresses actual
provider provenance, role credential limits and staged/final cleanup ownership.
The API read-budget finding is resolved with explicit per-group budgets under one
parent deadline and a complete positive acceptance control.

The initial raw factory diagnostic returned 128 passed/one pre-existing chain-
attestation finding; calling it a publication blocker was incorrect. The governed
corpus command `python3 scripts/validate-openspec-cli-pin.py --all`, in its default
pinned-artifact form, passes with zero undispositioned failures and the existing
ratified chain-attestation exception explicitly reported. It is an adjudicated
pass with one accepted exception, not a clean raw corpus. Neither the frozen
packet nor its existing disposition is changed. Factory [PR #1317](https://github.com/opensoft/openXfactory/pull/1317) supplied
the actual number; its single new ledger row was generated through the sanctioned
seeder with `--moved-by '#1317'`, and the ledger consistency gate passes. Two unchanged baseline factory README
links target absent files; no new link is broken. No candidate PR, hosted CI or
hosted connector review was created by the initial preparation.

The subsequent user instruction commissions publication-gate resolution, both
candidate PRs, hosted CI and local Codex review, then presentation for v2
ratification. Local review continues the owner's preference; no hosted connector
review is requested or claimed. Source owner acceptance and explicit isolated
commissioning remain the next implementation gate; no operational authority is
issued. Setup/dispatch remain unauthorized and feedback deferred.


Publication local qualification passed the two scoped initializations, both pins,
syntax, plain/strict validator, **1,641 full tests with zero failures/errors/skips**,
and the default pinned-artifact OpenSpec corpus entrypoint (five items, clean).
The first full attempt had 1,639 passes/two neutrality failures because the test
invocation placed fixtures outside its TMPDIR allowed root. No source workaround
was made. Both exact cases passed with corrected nesting; the complete corrected
run then passed all 1,641. The superseded attempt is not final acceptance.

Independent cleanup audited 38 process generations,
16 retained/shared preservation records and
8 consumed correlated dispatch journals across the
initial, focused and qualified local fixture roots. No matching process or
attributable helper remained. Retained fixture evidence is private; actual
operational cleanup/setup/dispatch was neither requested nor performed. All 116
recorded runtime/test/workflow/contract inputs remain unchanged. Factory metadata/
ledger checks and 501 focused tests plus four subtests pass.

The coordinator and nine local expert roles reviewed architecture, performance,
security, QA, static/quality, API/integration, integrity, reliability and simplicity
with no actionable material findings. Final published-head/CI/PR-thread closure
will be recorded on the candidate PRs; no hosted Codex connector review is claimed.
T012N-V and T001/T013/T014/T015 stay unchecked; source acceptance/commissioning
and every operational stage remain separate owner acts.

Private publication qualification artifact SHA-256 values:

- `qualified-full.xml`: `4e14da05181dd5ca1491c9b02d1bb5b3baed19b6d5fa95f71afe56a6466ba51e`
- `cleanup-audit-final.json`: `ad03bfd1239c37aacecbb5799e1363e936360a48c0cbdaa3f4bddda670653246`
- `source-boundaries.json`: `494f5d6798f94cfd58013427c2bd2541ad8592805cfbddf23a937449b21dfd4b`


## 2026-11-14 v2 source acceptance, ordered landing and isolated T012O

Brett Heap explicitly source-ratified factory #1317 at
`943e33fdafdc3d155045b96be4b4c24d28937c42` with adapter #67 at
`db7de85f709e5bb62df374fbde52ca263184502f`, then directed landing when green and
implementation/testing of T012O in isolation. Actual owner records:
[factory](https://github.com/opensoft/openXfactory/pull/1317#issuecomment-6887396615),
[adapter](https://github.com/opensoft/openXwallet/pull/67#issuecomment-6887396953).
T012N's source decision/narrow commissioning is recorded; T012P-V and every
operational gate remain separate. The agent does not tick T001/T013/T014/T015.

Factory landed first as `4496ee860587d2c557c9f7dd124d9d0029bd89a8`, using the
standing self-authored-PR missing-approval exception after all14 runnable checks
and exact-head local expert review passed. The authenticated actor and PR author
were both brettheap. Main had separately advanced to
`d4fdef49e96d6178c9da58327d5b956833c7b5df` for Sonar remediation, so whole-tree
equality with the ratified head is not claimed. All seven v2 packet files remain
byte-identical; the exact README addition and generated ledger row are preserved
in the integrated main tree. No unrelated main change was reverted or rewritten.
Adapter then merged normally as `02d902a4b19d9855780aad5996964686e7452929`, with
equal accepted/merged tree `a1f6d8c0140e7668c34a45486a1c3ac7e56452ca`, after all8
runnable checks passed. Source CI/merge readback is not live qualification.

T012O is implemented in the explicit hosted/ source package; see
[implementation and bounded reconciliation](hosting-finalization-implementation.md).
The static-v2 plan exists before assigned run/process values; preflight returns
only environment/plan readiness. Actual kernel generation/artifact measurements
feed canonical composition, policy and full configuration reconstruction. A
separate accepting authority independently reloads the approved plan, observes the
actual process, checks its own clock and compares complete bytes. The coordinator
rechecks after acceptance. `admit_finalized` retains unchanged full configuration,
operation-grant and lifecycle admission. No launch/issuer/listener/default activation
is added. Actual provider/guest/issuance/staging/takeover clients remain future work.

Final source qualification passes both pins, syntax, plain/strict validation, the
default pinned-artifact OpenSpec corpus entrypoint, **1,764 full tests with zero
failures/errors/skips**, and **1,462 mandatory offline cases with zero missing,
deselected, skipped or non-passing nodes**. All old matrix counts/fingerprints/
anchors remain; 123 new H01/H02/H04 nodes are added. Real RSA phase verification,
actual controlled process measurements and an owning-wallet proof/verifier are
exercised. Coupled policy/audience and independently reapproved wrong-source/graph
mutations cannot widen the fixed profile. No runtime result is a protected receipt.

The running bench's unshare capability was unavailable; no source or guard was
weakened. Native qualification used the previously reviewed disposable-container
route, network none, source read-only, private fixture mount only writable, then
the same privilege-dropping isolation wrapper. Earlier qualification attempts are
superseded by the final full/matrix receipts; no failed attempt is final acceptance.

Final qualified/reproduction cleanup audited 152 recorded
process generations, 16 preservation records and
8 consumed journals. Across all scoped
attempts the totals are 546 generations,
48 retained/shared preservation records and
24 consumed journals. No matching live
generation or attributable helper remained. All three disposable containers were
absent; ten exact private fixture roots were removed only after audit, with absence
verified. Logs/JUnit/manifests/readback/audit receipts remain private. Existing
benches, unrelated worktrees and owning source/pins remain. Both protected
workflows still have zero runs. Feedback stays deferred; neither historical blocked
write nor any denied optional/private write is replayed.

Self-review reproduced a late mutable-stage-snapshot alias that could mask a
generation change after the last measurement. Canonical snapshot capture now
precedes further callbacks; the reproduction refuses after the fix and is included
in the final full/native runs. Other closed findings cover copied bindings,
source drift during protection readback, independent authority clocks, coupled
audience/policy and reapproved source/graph substitutions. Superseded runs do not
qualify the final source.

Factory post-merge run43663946312 has a successful pytest job but failed
sonar-analysis/SonarCloud quality checks. Verified project key is
`opensoft_openxFactory`; new_security_rating is3 (C), required1, while new coverage
88.1% passes its80% condition. The v2 factory PR changed no Python implementation
files. At that checkpoint this was an unresolved factory-main quality-gate result,
not a claim of green integrated main. No gate threshold, finding status or disposition is changed.
See [post-merge run](https://github.com/opensoft/openXfactory/actions/runs/43663946312).
The green ratified-head PR checks and isolated T012O qualification remain separate.

Private final artifact SHA-256 values:

- `qualified-full.xml`: `1cc6e4525521f024fa0e5d12758b52866f95e8bd83fefd1522546c5854474eb2`
- `native-final-qualified.log`: `37017a292fac3a4d7633ab2e7e69d48f10f68768c32345baccef7a35f8586872`
- `qualified-source-inputs.json`: `07d4218021fffabb925091b2010dbe913089896086fa5de4d11d9ab38ee7ddaf`
- `cleanup-audit-final.json`: `956240503d949d79e65207e0fd125c75a1fa9b522e418e6646ec6864ac79d81a`
- `cleanup-summary.json`: `2c231d0174d1771233552fd6899262d9a53ec1fa9123ecccf9a5602b545fb0af`
- `fixture-removal-final.json`: `78964367be8c3ba675c15fe43bbbfbc7a0e334ae42805d0ad3cf09c229c649c1`
- `factory-quality-gate.json`: `29ff659293cbdb850f83c1e7c5f4331376e28e98598871f3e37775423082541a`

## 2026-11-14: T012O publication review and isolated requalification

Brett authorized the T012O candidate PR, hosted CI and local Codex review after
factory main Sonar repair, followed by presentation for source ratification.
No new source acceptance, T012P-V commission or operational grant is inferred.
The initial 1,764/1,462 receipts above remain dated evidence for their original
source; the changed source is requalified below rather than inheriting them.

Local review identified a second mutable-acknowledgement edge: observer callbacks
could temporarily change the live stage generation from acknowledged A to measured
B and restore A for the final read. Both PID and invocation witnesses first failed
with DID NOT RAISE on the original implementation. Measurement now compares with
the detached pre-I/O acknowledgement, preserving the full initial/final snapshot
check. Both witnesses and the unchanged real-process positive pass after repair.

The review also found shape-negative tests refusing on a stale template commitment.
Those cases now refresh that commitment unless it is the specific subject of the
negative. The relative-path witness updates both coupled path references. A task-
only in-memory mutation of the non-root UID guard now causes its negative test to
fail with DID NOT RAISE, establishing that the intended guard is exercised. No
mutation helper is committed or used by CI. A dictionary-comprehension cleanup
removes the connected preview's minor measurement finding without changing parsing.

All **1,766 full-suite tests** and **1,464 mandatory native cases** pass, with
zero failures/errors/skips and zero missing/deselected/non-passing matrix cases.
The hosted module has 125 nodes; the two additions retain all 123 previous node
identities. All other module counts, fingerprints and anchors are unchanged.
Both pins, YAML syntax, plain/strict adapter validation and default pinned-artifact
OpenSpec corpus validation pass in the required order. Native qualification uses
the running bench image with external networking disabled, source read-only and
only the task fixture directory writable, followed by the unchanged privilege-
dropping wrapper. No failed bootstrap or diagnostic attempt is acceptance evidence.

Cleanup audits account for 214 additional fixture process generations, 16
retained/shared preservation records and eight consumed dispatch journals. No
matching live generation or attributable helper remains. Native and diagnostic
disposable containers are absent. Existing benches, source pins and unrelated
worktrees are preserved. Both protected workflows remain at zero runs.

Connected preview reports a false positive on the imported Decision exact-type
guard: actual successful authority/finalization paths demonstrate that guard
accepting its intended class. The exact-type check stays intact; no suppression,
status disposition or weaker type check is introduced. Hosted full-project
analysis remains an independent publication gate. PR CI and final local review
receipts will be attached to the exact published head before ratification.

Qualification receipt hashes (private artifacts, not runtime receipts):
- `qualified-full.xml`: `cab91c6b26e14843a7c3607517f071f969d272f623f6715381d8a7add0b0261b`
- `native-qualified.log`: `d4f0fb26cd5a5132e347c1522fef52b0384c7e2c4f8720e0a745ddb93a88b5a2`
- `ordered-gates.json`: `d47b60ff2cff7599a113cca3b5707e1ed283a05bcdd2eb4c0e536bdb1a1757d3`
- `review-corpus-change.json`: `a53d9feb09adf31090d4712097da067bc8ddf3c024045ce1a36a8d347212f625`
- `cleanup-audit-final.json`: `e9bd90c624f7208cf0f80ec5a8fa08224fb01589efed0c119abe0273483974e1`
- `qualified-source-inputs.json`: `c9e903946131e0fd6834c8754727786397aae49e4edc5a9580da471356108775`

## 2026-11-14: factory main repair qualifies T012O publication dependency

The existing governed Sonar feature 044 repaired the two new-period flows in
factory PR #1318, source 7a8e70323b73fdf2f2526ebe3c56dbb3930f4ac3. Its own
exact-head Codex review completed without findings and its required CI passed;
the owning workstream landed it as 5d04859eb42e6b8684fa2825d20a8ed21652b93b.
No competing repair or unrelated checkout mutation was introduced here.

Actual main [run 43669723808](https://github.com/opensoft/openXfactory/actions/runs/43669723808)
passes both the complete pytest job and sonar-analysis. Its complete suite reports
10,570 tests and 807 subtests passed, six expected skips and 338 existing PostgreSQL
deselections, with zero failures/errors. All four other main workflows pass.
Sonar analysis 94982bc0-f624-44c6-8e8c-3d06049cf90c explicitly names that merged
revision and changes the gate from red to green: A reliability/security/
maintainability, 88.6 percent new-code coverage, 0.2 percent duplication and
100 percent reviewed hotspots. The same six thresholds and manual baseline
2026-09-09T23:37:08+0000 remain; ignoredConditions is false. Both former blockers
are CLOSED/FIXED, and the unresolved new-period vulnerability query returns zero.
Older baseline debt remains separately recorded by the owning feature.

All seven files from the ratified v2 factory packet at 943e33fdafdc remain byte-
identical in this merged repair. This current source CI/gate readback resolves
the earlier publication dependency; it supplies no operational permission.

The nine-expert local Codex panel and coordinator closed the T012O source review
at c737e1897bda61a8374aaa4b35b5ab8e627b47a9 with no unresolved actionable finding.
The final publication reconciliation changes only this evidence record; all nine
qualified source/test hashes are unchanged. Hosted CI and actual published-head
review receipts remain required before presentation for source ratification.
Source acceptance, T012P-V commission, setup, dispatch and live acceptance stay
separate. Feedback remains deferred and neither blocked write is replayed.

Readback receipt hashes (private artifacts):
- `factory-main-quality-gate.json`: `272ea392e420398e68793ceb781f091278c298dd984e242048f94374b8fc7b02`
- `factory-main-repaired-issues.json`: `06bcd1522c5a0fc9e6b6d8ed5dbe738cfea0d81c1229615a7ec8ea4df894194f`
- `factory-main-new-vulnerabilities.json`: `0220a40f358e8db1eb1e2d41f96ab5469e26511d768fbf3d1854031fdda867da`
- `factory-ratified-v2-preservation.json`: `3f9cb4789dd89c5e12fe7b1b17ba211e1a3e4c1aee4daf88dd563bfb4a6b879a`
- `local-codex-review.json`: `ac8a22e1abdffcf1c9b66c06233fdf22b5585884e6283cbcdcd94d6334d63a96`
- `fixture-removal-final.json`: `d69c5c179e2c352acc787f9171b450ac536cb280f6f48ca20b33d93b166c4b6e`

## 2026-11-14: hosted analysis assertion reconciliation

The first PR #68 analysis at 4dc5dcaaed168ac6844f3b1df97212dc7e25091e passes
the Sonar quality gate and does not reproduce the local preview's Decision
exact-type false positive. Its nine new S9073 test readability findings are
repaired by splitting composite assertions. Every condition remains asserted;
production source, fixture behavior, all 125 node identities, matrix counts
and fingerprints are unchanged. The complete affected module passes 125 tests
with zero failures/errors/skips after this test-only repair. The prior full/native
receipts remain bound to their recorded checkpoint; fresh hosted full-suite and
mandatory matrix evidence must qualify the updated published head. This adds
no suppression, issue disposition, source acceptance or operational authority.

The revised assertion source also passes the full ordered local gates: 1,766
full-suite tests and 1,464 mandatory native cases, zero failures/errors/skips
and zero missing/deselected/non-passing matrix nodes. The eight other qualified
inputs are byte-identical. Cleanup audits account for 212 additional fixture
generations, 16 preservation records and 8 consumed journals, with no
matching live generation or attributable helper. The disposable native container
is absent. This qualification supersedes no failed result and grants no operation.

Revised-source private qualification receipt hashes:
- `assertion-full.xml`: `6804067f922a7b8f96de8d76e7edd15e43388a4e1b4456ed34d1759eb9931a69`
- `native-assertion-qualified.log`: `a4eb6142964daaba041196697804c7fce0bf5a279276d1acbf869f81d6142d2d`
- `assertion-ordered-gates.json`: `d47b60ff2cff7599a113cca3b5707e1ed283a05bcdd2eb4c0e536bdb1a1757d3`
- `assertion-qualified-source-inputs.json`: `cf8e09446b8dd3bf5b2ccc8175ab02834554a4b52a23618b7e30e8d46c462906`
- `cleanup-audit-assertion.json`: `f4a89e48e6a4cacfd15dee72bc76a7e85e2fc7692b6b19ea1cdff96aa1fc9615`

## 2026-11-15: #68 source acceptance and isolated T012P candidate

Brett source-ratified #68 at 38b029b02a9b and commissioned only T012P
implementation/testing in isolation. [Actual owner record](https://github.com/opensoft/openXwallet/pull/68#issuecomment-6889412055).
All eight runnable ratified-head checks pass and the nine-expert local source
review has no unresolved finding. #68 merged normally as
`4bae2b22f74e19a43d8413055142447319a41202` with equal accepted/merged tree
`3294fa4502130c4e809316e9432fbc0e1febcd2b`. No administrative bypass or rule change was used.
The accepted T012O worktree is preserved; T012P uses its own feature017 worktree.

See [bounded T012P realization](hosting-issuance-implementation.md). The source
contains exact-version RSA digest signing and verified App JWTs, fixed GitHub
App/installation/token/repository/retirement operations, independently current
approval, explicit durable one-attempt nonce state, and a non-renewing private
credential-use seam. Returned one-hour provider expiry is distinct from the
earlier local use deadline; a stolen provider bearer is not narrowed by a case.

Enrollment verifies actual mTLS bootstrap identity, CSR proof, independently
approved public fingerprint and complete host/source/UID/role/case/plan/issuer
selection before nonce consumption. Issued short client certificates authenticate
private role delivery. The App policy pins the complete enrollment digest, so
a same-role certificate from another scope cannot be combined with it. Selected
configuration cannot mutate under an old approval. An actual owning software
Ed25519 proof is created and verified through unchanged registry/custody APIs
using an enrolled certificate; no native Key Vault Ed25519/HSM assertion is made.

Kernel per-message UID/PID/start credentials prevent an inherited descriptor from
impersonating its creator. Independent positive/negative controls cover metadata
resolver, key/sign, control and policy capabilities; exposure mutations and outage
checks prevent false denial qualification. An extra disposable root-only fixture
uses distinct UIDs and real file/connection denials, with deliberate exposure
mutations detected. It is source/fixture evidence, not deployed host qualification.

The final source passes the ordered pin, YAML, plain/strict adapter and pinned
OpenSpec gates, **1,852 full-suite tests with zero failures/errors/skips**, and
**1,550 mandatory native cases with zero missing/deselected/skipped/non-passing
nodes**. There are 86 intentional new nodes across three modules. All previous
module counts, fingerprints and H01/H02/H04 plus other anchors remain unchanged;
new H06/H07 groups contain 32/18 substantive anchored nodes. The extra kernel
fixture passes 11 checks. No live provider credentials or live token requests, protected dispatch
or actual hosting setup are used by this qualification.

Test-first failures include the absent protocol/nonce/enrollment/kernel ports and
a real same-role/different-enrollment composition gap; each has a passing positive
and refusal after implementation. Self-review also closed expired/changed
authority after token mint: known returned tokens retain private cleanup handles;
lost responses stay consumed/indeterminate, never retried or counted as retired.
Revocation ambiguity permits read-only reconciliation of the same capability,
without a second DELETE. Earlier 82-node/1,546-case and 85-node/1,549-case checkpoints are not final
qualification of the later source. A final provider-outage regression first
returned a generic refusal (403); the private delivery route now returns safe
unavailable (503). The red and green witnesses are retained, and all gates above
were rerun after that correction. Outage supplies no authenticated denial.

Cleanup audits cover 2,617 recorded fixture generations,
48 retained/shared preservation records and 24 consumed
journals. No matching live generation or attributable helper remains. All task
disposable containers are absent; source, benches, unrelated checkouts and pins
are preserved. Source/fixture results supply no protected-machine report, actual
provider/VM acceptance, human approval or domain acceptance.

T012P is an isolated implementation candidate, not owner-accepted source. No new
PR, hosted review or runtime activation is commissioned here. T012Q-V and
T001/T013/T014/T015 remain unchecked/uncommissioned. Setup/dispatch remain
unauthorized; feedback stays deferred and neither blocked write is replayed.

Private qualification receipt SHA-256 (task-only artifacts):
- `pr68-landing.json`: `26f7a85e64d8012b76fb7010285cf7742de5b6d5c1675949c15fb7b0b549a8e9`
- `finish-full.xml`: `b8b2daabaa81f5358ba740f805157b527a0d92a6e4d24cd2de269663fe072b31`
- `native-finish-qualified.log`: `0cfa290c9898b02c7ba85af6c4b586b5d954260cc0531513eeac05976365e198`
- `finish-ordered-gates.json`: `d47b60ff2cff7599a113cca3b5707e1ed283a05bcdd2eb4c0e536bdb1a1757d3`
- `finish-matrix-additions.json`: `02a3e46a6188ec5082a8b815552c8ed84254fdd073b50420f6eeaa4e48e792bb`
- `finish-source-inputs.json`: `7273702d84c9f6a07ae14cb8f8861d83ff0dd4075e0b63d3f5c15801f09ee4e8`
- `error-path-red.xml`: `7d40115bd6249c94d9f096c62e6ee016e8563511c9a24379bf7cde4fbfca2957`
- `error-path-green.xml`: `4b125dd866238008375745ab8a42a5fc0c143402bd39995484a0aa6da05089ab`
- `kernel-qualification.json`: `18fe1e5cb09cb55bc4f2864761b3107709974ca60519b727221f55ac003ff34c`
- `cleanup-audit-final.json`: `131f7bf9085c02af8fc9f3dfd33aad38862fa361d3ce193f06fd916eee49a670`
- `cleanup-audit-finish.json`: `e5a57414a0a03883fe2285a43e8cb1bec04599968f6e1df7955fce0ec106a7b7`
- `cleanup-summary-finish.json`: `870adb436abe9b634cc2c8dd65f120b699356195a8b907377df66d49ab1e7a96`
- `fixture-removal-finish.json`: `a884af52fe549ab91fa3f435376eeab3da561083192569d98bba7d6dbfc597cd`
- `protected-workflow-counts-finish.json`: `572c60bb849fb4fca01d47690bd07d6fd5e23246a60a3af72d5f2c72472e45aa`

Final cleanup removes all 20 exact task fixture roots only after generation and
preservation audits; the distinct-UID fixture required its fixture administrator
for removal, as expected from its measured file boundary. All task disposable
containers are absent. Both protected workflow IDs 417795073/417795071 retain
zero runs. This does not retire any live provider resource or authorize setup.

## 2026-11-15: T012P publication review and corrected-source qualification

Brett authorized candidate publication, hosted CI and local Codex review, followed
by presentation for source ratification. [PR #69](https://github.com/opensoft/openXwallet/pull/69)
initially published b5a36b77faef. The earlier no-publication commission above
records the preceding isolated task; this instruction supplies publication only,
not source acceptance, T012Q-V commission or operational permission.

The local nine-expert panel and coordinator identified and closed a P1 shared-
request-endpoint credential reply leak and a P2 cancellation reply-descriptor leak.
See hosting-issuance-implementation.md for the private reply-capability correction.
Three cancellation witnesses first failed their retained-traceback FD counts; all
now pass with immediate descriptor closure and EOF. Seven additional private-
reply/malformed-descriptor cases and those three cancellation nodes retain all
previous node identities. All 13 frozen source/test hashes reconcile with the
reviewed correction. No actionable local source finding remains.

Initial hosted checks passed except Sonar, which reported two private-stdin URL
taint flows, complexity/literal warnings and test exception/assertion clarity.
Source corrections preserve every guard and separate trusted nonsecret routing
from anonymous-pipe credential payloads. No issue disposition, suppression, gate
threshold, baseline or repository rule is changed. Fresh hosted analysis of the
corrected published head remains separate from these local receipts.

Final corrected-source ordered pin, syntax, plain/strict adapter and pinned
OpenSpec gates pass. All 1,862 full-suite tests and 1,560 mandatory native cases
pass with zero failures/errors/skips and no missing/deselected/non-passing matrix
cases. The 96 added cases comprise 49 issuance, 26 enrollment and 21 credential
nodes; H06/H07 anchor 32/28 nodes. The extra UID/kernel fixture passes 11 checks
again on this source. Prior 93-node in-progress runs were deliberately interrupted
after discovering the cancellation defect; they are diagnostics, not qualification
of this final source. Earlier qualified checkpoints remain dated evidence only.

Source ratification remains pending. Setup/dispatch stay unauthorized, feedback
stays deferred, and neither blocked write is replayed. No live provider token,
protected run or service setup is performed.

Corrected-source private receipt SHA-256:
- `final-full.xml`: `c3217ee5d6e92ca356524ca0e1430abfd710fb22e8c67acabaf964a81b974296`
- `native-final-qualified.log`: `c1f3130b0ccb49df10a7418ad9e5e46ebc8960253637506a6972f394a57cecaa`
- `final-ordered-gates.json`: `d47b60ff2cff7599a113cca3b5707e1ed283a05bcdd2eb4c0e536bdb1a1757d3`
- `final-matrix-change.json`: `d8baaf8917beadb0c3f1c668bf9d17bf1c9e3b0a4909ec06785254ee5924c10e`
- `final-source-inputs.json`: `910b92f2545270771a63a666a918a015e781ecf27ed0ed53ff850f797d475828`
- `cancel-red.xml`: `056bce4e51608206ab7a9ea45ddf924b9872600a2eabe7ea2d43356d57ff6353`
- `cancel-green.xml`: `08343319c612f466e655c5f3a1fb8b17a246ab5ba77cf8e3686ad3425c341287`
- `kernel-qualification.json`: `a94c5b9e5695af0f0769a45fe00559a11f89a72c0d598ffd4b4a1644d6fdedea`
- `local-codex-review.json`: `bd4fc3393a58cf3ffe7803ef852fddeae78bd9c10692854d0304081f3ae823b8`
- `qa-final-review.json`: `c26088a3544766e2ea9b293d0ea4cae10280f79e0c2652d86f2e322c7054f47f`

Final publication cleanup independently audits 1002 recorded fixture generations, 24 retained/shared preservation records and 12 consumed journals. No matching live generation or attributable helper remains. The eight reviewed/diagnostic fixture roots and two UID/kernel fixture roots are removed after audit; reviewer-owned roots were removed under their own recorded audits. No live provider retirement is inferred.

## 2026-11-15: closed provider-route requalification

At published 60d44ade20bc, all runnable hosted checks except Sonar passed; Sonar
automatically cleared 38 initial findings and retained one command-line URL flow.
The private helper now independently reconstructs closed literal GitHub routes,
exact-version public Key Vault POST signing and explicitly selected bounded mTLS
loopback fixture routes. Unknown production destinations cannot fall through to
fixture mode. No manual finding disposition or suppression is used.

The nine-expert local panel and coordinator reconciled all 13 new source/test
hashes with no actionable source finding. All 117 focused T012P cases pass. Fresh
ordered pin/syntax/plain-strict adapter/pinned OpenSpec gates, 1,883 full-suite tests
and 1,581 mandatory native cases pass with zero failures/errors/skips and no missing,
deselected or non-passing mandatory case. The 21 new route controls extend H06 to
53 anchors; H07 retains 28. All earlier nodes/fingerprints/anchors remain. The
previous 11-check supplemental UID/kernel qualification retains byte-identical
credential/helper/fixture inputs; no unrelated kernel check was repeated. Earlier
1,862/1,560 receipts remain valid only for their dated source checkpoint.

Hosted checks of the corrected published head and owner source ratification remain
separate. Setup/dispatch stay unauthorized; feedback remains deferred and neither
blocked write is replayed. T012Q-V and all live provider/host gates remain separate.

Route qualification private receipt SHA-256:
- `route-full.xml`: `0dd56aa581f8c5963340d5cdd2d45d7c42975e502727cdbd628f82851782f599`
- `native-route-qualified.log`: `65d478c224a19eff847448dcf243eeeae3c73b2d0d25090a53410e0d74577de1`
- `route-ordered-gates.json`: `d47b60ff2cff7599a113cca3b5707e1ed283a05bcdd2eb4c0e536bdb1a1757d3`
- `route-source-inputs.json`: `02b808cd44441ef1a0b8f2c47ad4a720e437edaaa9daa1547a3ce24017f98176`
- `route-matrix-change.json`: `259da302a31eae61752c6a509e892d21e53d596aed841c732af1848d56567607`
- `routes-focused.xml`: `c77f0edec897c5c8c07e1f374b3957ad3ccd4c2501796d7540d1aa03ebc3f022`
- `local-codex-review-routes.json`: `cf3bde22c65f398dff796085176a9975d2b53dc2778e0ff31af1c6f906c40c66`
- `qa-route-final-review.json`: `d97de8868c140a43509ff765c176ee87ba77e7eac81416ef4e8d05027a531ec5`
- `sonar-issues-corrected.json`: `e90627aff72d08c8fc028f0c44c659e974326e65c223560ebaa7ae86a440bd62`
- `sonar-gate-corrected.json`: `711bff82f9a73c0fb9c1cbf5de00c3bb08d95b2c7e0abd31827f9712f3782e17`

Route requalification cleanup audits 757 additional recorded fixture generations, 16 preservation records and 8 consumed journals. No matching live generation or attributable helper remains. All three exact route fixture roots are removed after audit and the disposable native namespace is absent. Earlier UID/kernel fixture state remains removed; no live provider retirement or operational authority is inferred.

## 2026-11-15: #69 source acceptance and isolated T012Q commission

Brett source-ratified #69 at b73a7d06695e and commissioned only T012Q in isolation. [Actual owner record](https://github.com/opensoft/openXwallet/pull/69#issuecomment-6894503254). All eight runnable exact-head checks pass and the local nine-expert panel/coordinator has no unresolved source finding. Normal merge 7bd884106eea5f0ed4b99a35da70d613ccbfd0d2 retains accepted tree 7b3b00e5c4b8c35c667541fc7187b9a97befaa8b; no administrative override or rule change was used. The accepted T012P worktree is preserved; T012Q has a separate linked feature017 worktree. No source acceptance, setup/dispatch or T012R-V commission is inferred for this new implementation.

## 2026-11-15: T012Q isolated current-readback candidate

The new adapters obtain independently authenticated current source/protection/control,
selected ARM/key metadata, hold/issuer/guest and existing-state observations under
one enclosing Decision. Private requests send no candidate facts. Missing typed
provider fields, branch type, stale/mutated observations, wrong peer/pin and
exhausted budgets refuse. No default activation, workflow, pin or neutral contract
changes. See [implementation and limits](hosting-readback-implementation.md).

Test-first progression: missing adapter collection refused; shared-budget controls
then passed; component/flow integration exposed a fixture-name collision and a
missing closed run-read route, both corrected. Final 160 new cases pass. The
ordered contract pin, neutral pin, syntax, validator, strict validator, full pytest
and default pinned OpenSpec whole-corpus gates pass. Full pytest: **2,043 passed,
0 failures/errors/skips**. Mandatory exact-identity matrix: **1,741 passed,
0 failures/errors/skips**, native UID 1000/no capabilities/no new privileges,
read-only source and loopback-only networking. H08/H09 anchor 78/32 nodes; all
1,581 accepted base matrix identities/counts/fingerprints/anchors are preserved.
The owning source remains clean at bb0e9dae89a771b05f6c235d0a77237288b95c85.

The composed protected reader uses 12 GitHub reads (including four correlation
reads); selected deployment/issuer/guest/state use the same Decision. Actual owning
Ed25519 proof and replay refusal pass. A separate regression proves full v2
finalization currently refuses repeated fresh protection reads at the accepted
three-read limit, before any proof. This is a downstream factory/adapter design
blocker, not permission to reset counters, relax freshness or raise the 13-read
aggregate limit. Resolve it through the governed process before full hosting
wiring/T012R; that later task remains uncommissioned.

Cleanup checks 38 ownership process generations, 120 hosted generations,
3439 credential/guest helper generations, 16 preservation records and
8 retained consumed journals. No matching live generation or attributable helper
remains; native container absent. Ten exact Q fixture roots are removed only after
audit, retaining scoped redacted receipts. Both protected workflow run totals
remain zero. This is a local candidate; no Q PR/hosted CI/review or new expert panel
is claimed. Source acceptance and live provider/host qualification remain separate.
Setup/dispatch remain unauthorized; feedback deferred; no blocked/denied write
is replayed.

Private receipts under `t012q-isolated-20261115` (SHA-256):

- `bounded.xml`: `4e256330158de0375143eb6008c30e52fa6b9a07ead90203feb9a2ac738ece10`
- `final-full.xml`: `06042abd14e8e32f6b15954080861d727eea3e638f6d5b1c01d5eb3347a67b46`
- `native-matrix.xml`: `6b04c52b21686ad7c6f2b49f757fa822ab7c87a43c2b8b956362073193725e50`
- `native-final.log`: `af3c264870fc08630d031d23f80becda5e241a83ea42f367e529d88f2c81ce8d`
- `final-ordered-gates.json`: `d47b60ff2cff7599a113cca3b5707e1ed283a05bcdd2eb4c0e536bdb1a1757d3`
- `qualified-source-inputs.json`: `52d4c651e9e73ceb710020cfbbb9f038e9c802d178ad02b1842f37cf86820052`
- `matrix-preservation.json`: `9f73c4c54f4fe24860c12c619e11c62dd71a771af08fa7173415d14067d539cb`
- `cleanup-audit-final.json`: `ae2d1d04038c8b1b08cc727b1704309d668f6722110b5fecf5b8e5e34b981139`
- `fixture-removal-final.json`: `09086f2273fe5db7bb8231d837d3a0c42ed76b3070473ae5cdfd59dc488a41b2`
- `protected-workflow-counts.json`: `55ab61d23336ac849aebc23653c7a34ee01e6f329a3be8867505445266500dc6`
- `local-source-inspection.json`: `a710a483a5e8a293b4836b0d36ca0c0a6da615bf7b960f8b22308149f3d2600b`
- `qualification-summary.json`: `905b09f085db55abcbdf08ed2df92ed38804c2f96de43c42983d36f21093b3f1`

Final documentation syntax/plain/strict/default pinned OpenSpec gates also pass.
Their validator self-tests left 100 task-local scratch roots and one Node compile
cache, all checked and removed within the exact Q evidence directory. No scoped
fixture/scratch directory remains; redacted receipts are retained.

- `final-document-gates.json`: `89270cdc9c473545b25fa7ad5987ecb84964a24882f5ab48450065cc1529924d`
- `final-document-cleanup.json`: `5089bc6d7326687587f0f2d95ed7357a0de14cbff33869b46fe35855c6ce462d`

## 2026-11-15: Governed protection-read correction and T012Q publication

The user commissioned the bounded correction, paired publication, CI and local
Codex review, with no source ratification/landing or operations. Factory #1322
proposes finalization-only six-observation/18-protection/28-total allocation while
preserving ordinary3/13. The caller and independent authority share one ledger,
per-member correlation high-water and earliest expiry; original clocks remain
binding. ProviderReader enforces four total reads before credential/I/O. All six
fresh protection reads and independent complete-byte recomputation remain.

Test-first allocation collection refused before implementation. Then 61 allocation
and flow cases passed; final 318 focused allocation/readback/finalization cases
pass, including actual mTLS/process/file positives, independent six-position drift,
unchanged admission, owning proof/replay refusal and default-budget refusal.
Factory focused code-surface/target-release/sequencing suite: 538 passed. The
original factory packet is unchanged. Full/native and exact-head CI/local expert
review remain in progress; no hosted Codex review is claimed.

### Local panel corrections

Nine-role local review found two substantive issues: (1) correlation's hosted
ledger lacked the after-TLS/before-GO shared checkpoint; (2) approved ARM disk/NIC
reference metadata was refused by minimal-object equality. Both are corrected.
Hosted correlation now supplies the shared checkpoint while ordinary transport
signature stays unchanged. Real TLS tests expire/regress the joined peer and
require zero application requests. The ARM fixture includes documented storage
and NIC metadata, with typed-link checks and unchanged complete-model digest;
approved metadata positives and independent metadata drift/type negatives pass.
Focused TLS/correlation controls: 15 passed; ARM controls: 22 passed. Earlier
full/native runs were explicitly superseded/interrupted before source correction;
they are not completed qualification. Fresh corrected qualification follows.

### Final corrected source qualification and review

At source head cfaa57cae6570b1adf40fa9048c64ed49324c933 all seven ordered local
gates pass: contract/neutral pins, syntax, validator/plain+strict, full pytest and
default content-addressed pinned OpenSpec whole-corpus validation. Full: **2,094
passed, zero failures/errors/skips**. Mandatory native: **1,792 passed, zero
failures/errors/skips**, native UID1000/no capabilities/no new privileges, read-only
source and loopback-only networking. H08/H09/H10 anchor 87/40/34 nodes. All 1,581
accepted base matrix identities/fingerprints/anchors and prior Q identities remain.
The source head also passed every runnable adapter hosted check; Sourcery is
quota-skipped, not counted as review. Final documentation exact-head CI remains
separate and is recorded on PR #70; factory CI/review lives on #1322.

Nine delegated local Codex expert roles plus independent coordinator inspected
the entire paired diff. Architecture/security/reliability found the shared
post-TLS checkpoint gap; API review found approved ARM metadata rejection. Both
P2s were fixed and all nine roles closed at the corrected source head with zero
remaining actionable findings. [Adapter review record](https://github.com/opensoft/openXwallet/pull/70#issuecomment-6896143770)
and [factory review record](https://github.com/opensoft/openXfactory/pull/1322#issuecomment-6896144305).
No hosted Codex review is claimed. Final documentation retains the exact 15
tested/reviewed production/test input hashes; final coordinator checks and hosted
statuses are posted on the PRs before owner presentation.

Cleanup audits 49 ownership process generations, 263 hosted generations and
3,341 credential/guest helper generations, 24 preservation records and 12 consumed
journals. No matching live generation/helper remains. Disposable native namespaces
are absent and eleven exact publication fixture roots are removed. Both protected
workflow histories remain zero. Original baseline evidence is untouched. No source
ratification, landing, T012R-V, setup/dispatch or live provider qualification is
inferred. Feedback remains deferred and no blocked/denied write is replayed.

Private publication receipts (SHA-256):

- `integrated.xml`: `2d4038319ef898eaee124e0f3fec5c787016aec17acfe9cf9c951bcf7e911369`
- `factory-local.xml`: `f218a4afaa0943c0d96e39268bf589fd492b2822c161261783076b5ac30a4002`
- `tls-focused.xml`: `d7a4c0cfb22436711d1bd617e09056824d1b44bda163586dfbf1cca1a0f9dd07`
- `arm-focused.xml`: `075a081c57ec9ef8832ba53cfa819f333297db3fdfcb2fa12bd7d0939fcc5d88`
- `corrected-full.xml`: `7c2d44cd3b8650078c37ae61e15ddbaf3cd6114e0830bb115c7c5bba6b79a5d4`
- `native-corrected-matrix.xml`: `478eff1aff767a1cfd11ffef58ce6d5809cf3d5228e4ce4164925234a580e294`
- `native-corrected.log`: `50c482b88df79c9c36d260247021ac396191b56a60775b90e49df426dc0a5517`
- `corrected-ordered-gates.json`: `d47b60ff2cff7599a113cca3b5707e1ed283a05bcdd2eb4c0e536bdb1a1757d3`
- `qualified-source-inputs.json`: `d394fc4d1c7040c25c78ba9c537aa548a11f24e553692251e9541a37dabd8eab`
- `matrix-change-final.json`: `ce49ebfeecac12bdb3f80cee0c1c8ad433365d3755213266af67d2ac76f9c018`
- `local-codex-review.json`: `2b5138cf1052bba285a189e04b885bcf9d690095dd3f272d938d08875569b8e5`
- `cleanup-audit-corrected.json`: `737da99d07f3e46fc3c0e9857329b0c31243fb9143a01bad4e5aa270d2c28a84`
- `fixture-removal-corrected.json`: `def63398aa0e4608ff3266040d4750fc9d90f107cf67576701a679638f1badf4`
- `qualification-summary-corrected.json`: `da658c806e93aa9991597249cdb153a224a0a1221d3b89be7a9e0a7ae64867ff`
- `protected-workflow-counts.json`: `8109e667671c1ac1c64ec13ccc5f87461ecfe91446138d9091355f966c7c97af`

Final documentation syntax/plain/strict/default pinned OpenSpec gates pass. The
exact task-local documents scratch root is removed afterward; no scoped fixture
or scratch directory remains.

- `final-document-gates.json`: `8e705062e9caf08fd3c3cc07c11af945aa4de5c9573d8b504661a5dc5ddc828a`
- `document-cleanup.json`: `76501def3d963810d31237cb8666101347d030a5b35120816a3ea1bbeaa91c3f`

## 2026-11-15: Paired source acceptance and T012R commission

Brett source-ratified #1322 e813051af8c0 and #70 f6956e324e37, then directed
ordered landing and T012R in isolation. Both exact heads were green/mergeable
with zero unresolved review threads. Normal merges 54f720b6df81473473d48c7289c51faafccb1c9d
and 27843096189ac6e168999832b821333a58392b4c preserve accepted trees
5594ce2ca90ed76dcf4dc20aadd805fb2652811e and 4bb3cc4ec1799e7e0ca4e60f7e32a6099fdc992e.
No administrative override/rule change. Actual owner records: [factory](https://github.com/opensoft/openXfactory/pull/1322#issuecomment-6896463055),
[adapter](https://github.com/opensoft/openXwallet/pull/70#issuecomment-6896463382).
The accepted Q worktree is preserved; R has a separate linked feature017 worktree.
T012S-V and every operational gate remain uncommissioned. Feedback deferred; no
blocked/denied write replayed.


## 2026-11-15: T012R isolated host launch candidate

The feature017 `017-hosted-launch` worktree starts from accepted adapter merge
27843096189ac6e168999832b821333a58392b4c. The as-built source and explicit later
boundaries are in hosting-launch-implementation.md. No neutral contract, pin,
gitlink, workflow YAML, default activation, setup or dispatch is changed.

The corrected frozen source passes 2,163 full tests, 1,861 mandatory native
cases and all seven ordered repository gates; zero skips/failures/errors. The
69 new launch nodes retain all 1,792 old mandatory identities/fingerprints and
anchors. H03/H07 now anchor 64/33 substantive nodes. Actual TLS, manager/process,
Landlock/seccomp and file observations qualify the bounded reference service.

Earlier runs are superseded by the parent-death and post-helper checkpoint fixes:
PDEATHSIG could be cleared through prctl. The final source blocks that option,
retains read-only queries, verifies GID/supplementary groups, and reruns both
complete suites. The manager crash positive observes SIGKILL, reaping and a
consumed unpersisted start; response loss never triggers a replacement start.

Private evidence: `t012r-isolated-20261115/qualification-summary.json`,
`complete-full.xml`, `complete-native.xml`,
`complete-ordered-gates.json`, `qualified-source-inputs.json`,
`superseded-qualification.json` and cleanup-audit-final.json. Both protected
workflow IDs 417795073/417795071 have zero runs on readback. Source publication,
ratification, real host administration, T012S-V, setup/dispatch and live acceptance
remain separate. Feedback stays deferred; neither blocked write is replayed.

Cleanup audit: actual py-bench PID namespace; no matching recorded process or
attributed helper remains. Verified 48 preservation records and 24 consumed
dispatch journals, then removed exactly 25 task fixture roots. Retained native
XML outside those roots; all three native containers are absent. Details and
counts are in hosting-launch-implementation.md, cleanup-audit-final.json and
fixture-removal-final.json. This does not assert T012S production cleanup.

## 2026-11-15: Corrected T012R publication qualification

The preceding isolated receipt describes the initial candidate only. Adapter #71
and proposed factory #1326 incorporate the review corrections described in
hosting-staging-refresh-amendment.md and hosting-launch-implementation.md. Corrected
source passes 2,200 full tests, all 1,898 mandatory native cases, 140 focused rechecks
and 538 factory checks; zero failures/errors/skips. All1,792 previous required node
identities/fingerprints/anchors remain; 106 new nodes yield H03/H07 totals94/40.
All seven ordered repository gates pass; the final OpenSpec invocation required a
task-local npm cache after an inherited /root cache refused access. The original
environment failure remains in the private ordered receipt.

All nine local Codex specialists plus coordinator completed corrected-source review
with no unresolved finding. Subsequent documentation preserves the 143 tested
Python/workflow input hashes. Local review is distinct from hosted checks; no
hosted connector review is claimed. Factory #1326's optional merge-master-approval
bootstrap fails before candidate evaluation because floating Python3.x selects3.15
and locked PyYAML6.0.3 has no compatible wheel. Effective required checks exclude
that job; no rule, check or workflow was bypassed or changed to hide it.

The proposed protected-stage26/private16 profile retains original clocks and
ordinary/finalization allocations. Protected workflow YAML/pins/default refusal are
unchanged; only ordinary pytest bootstrap changes. No ratification, landing,
T012S-V, setup/dispatch or live qualification is inferred.

Private corrected qualification receipts (SHA-256):

- `resumed-full.xml`: `504c0df62ff58cbfe72f134cbe08c26ca9838b3845c495b82c3bf479f74a1cdc`
- `resumed-native.xml`: `f7bdc86e265ed2fd8a7d3de167134d171979313657c3b06503b3e8e9cf10887e`
- `resumed-ordered-gates.json`: `02e62d022a14f979c5b0b26a15c419381a568a4e6c8b231381c39cffdb55d552`
- `qualified-source-inputs.json`: `74d6ab81f2faae0e30ab9dd619c234c3cdb90d1d4a104f3aab4dbd1b1f956c0e`
- `resumed-focused.xml`: `02061781a6daf46d9affc10add3f99442df3cc75334794e7b91cf09ed20cc80a`
- `factory-resumed.xml`: `bed5e5e79036ee646e9a2e57d3bec638219330be8efad8e6aa657be3e498208c`
- `local-codex-review-current.json`: `87b931735cc4f6b936c724118d74d6f4726a79add75864c382026872762e780c`

Publication cleanup was audited in py-bench's test PID namespace: 38 recorded
process generations, 132 hosted generations, 9,022 credential/helper generations
and three crash-window generations have no matching live instance. No attributed
helper remains. The audit verifies 16 preservation records, eight consumed journals
and 286 retained staging summaries. The exact task fixture roots are removed after
audit; XML/source/review/audit receipts remain outside those roots. The disposable
native container is absent; accepted checkouts and active benches remain intact.
Both protected workflow histories (417795073/417795071) remain zero. This is
isolated fixture cleanup, with no production cleanup/takeover claim.

## 2026-11-15: T012R paired source acceptance and ordered landing

Brett Heap source-ratified factory #1326 at dc159da61860 with adapter #71 at
74b4af51322b, then directed ordered landing when green and T012S preparation only.
Owner source records: [factory](https://github.com/opensoft/openXfactory/pull/1326#issuecomment-6901804063)
and [adapter](https://github.com/opensoft/openXwallet/pull/71#issuecomment-6901804798).
All effective required exact-head checks and both Sonar gates pass; local nine-role
Codex/coordinator review has no unresolved actionable finding or review thread.

Factory merged first as 0503c7bf36ea47c5c2b492bdf24ca11eed87347d at 21:42:25Z.
Actor and PR author are both brettheap, so the standing self-authored-PR exception
was used for missing human approval only. Effective required checks passed. The
optional merge-master-approval Python3.15/PyYAML bootstrap failure stays visible;
no rule/check/workflow was changed to conceal it. The merge tree equals the
predicted integration with main 5b636c767fcc; every accepted changed packet/ledger
blob is byte-identical. Unrelated integrated main changes are not attributed to
the ratified proposal.

Adapter merged normally as 7042b295bc7229748e5b415e5f9ddb3f96a2467e at 21:43:07Z,
without administrator override. Its whole tree equals the ratified head, including
all 143 tested Python/workflow inputs. Accepted worktrees, owner checkout, pinned
CLI and active benches are preserved. The prior R cleanup audit remains intact.

Factory exact-merge main CI started in run 43765166319 and separate source jobs;
completion is an independent gate and is not asserted by these merge receipts.
The adapter has no new exact-merge run on the initial readback; PR CI is not
relabelled as post-merge CI. T012S preparation stays source-only while this is
verified. See PR CI evidence [factory](https://github.com/opensoft/openXfactory/pull/1326#issuecomment-6901736498)
and [adapter](https://github.com/opensoft/openXwallet/pull/71#issuecomment-6901483414).

## 2026-11-15: Bounded T012S preparation

The separate 017-hosted-lifecycle-prep worktree starts at the accepted adapter
merge. hosting-lifecycle-plan.md audits the existing stage store/controller/host
and finalization/RunLifecycle/RunJanitor/replay interfaces, then defines a retained
registration/takeover/action journal, independent scheduler/janitor/audit and
actual same-generation stage-to-final responsibility without a gap or renewal.
hosting-lifecycle-acceptance.md maps H05/H11 to twelve fault/control families.
tasks.md alone contains T012S/T012S01-T012S07, all unchecked/uncommissioned for
implementation; no second factory task list or neutral contract is created.

This preparation runs no T012S test, lifecycle initialization, scheduler, provider
operation, protected dispatch or service restart. No new case count is guessed.
The existing 1,898 mandatory identities/fingerprints/anchors and accepted budgets
are preserved. External-watchdog/conditional-infrastructure retirement, T012T-V,
T001/T013-T015 and every operational authority remain separate. Feedback deferred;
neither blocked/denied write replayed.

Private landing/preparation receipts are retained in t012s-preparation-20261115:
ordered-landing-verification.json, source-ratification records, exact-head CI/rules
readbacks, merge receipts and scoped source-document verification. No runtime
qualification of T012S is inferred.

Preparation verification passes contract/neutral pins, syntax, plain/strict adapter
validation and pinned default OpenSpec --all strict validation. Scoped review is
in hosting-lifecycle-analysis.md. All task IDs remain unique; T012S plus its seven
child tasks and T001/T012T-V/T013-T015 remain unchecked. All 143 tested runtime/test/
workflow inputs are unchanged from accepted R; no new runtime tests were rerun or
claimed for this document-only preparation. Temporary document cache/scratch is
removed after verification; landing, source and review receipts remain retained.

Preparation receipt SHA-256:

- `ordered-landing-verification.json`: `8d22faccc88f454e1ee8b30d7023a7d93052aa77c226ed7029adf7bc37190c7f`
- `preparation-document-gates.json`: `31d8f758c8149036948b9f2fe1ae1702c767e9f5a8b15a3310930e19ddce982a`
- `preparation-scope-proof.json`: `c777707855f87109ab6b87382fdbec1688435340a4faee4cd6ee570344daff7a`

## 2026-11-15: Commissioned isolated T012S lifecycle candidate

Brett directed verification of factory post-merge CI, then implementation/testing
of T012S in isolation from the prepared plan. Setup and dispatch remain NOT GRANTED;
feedback stays deferred and neither historical blocked write is replayed. This
commission covers T012S01-S07 only, not T012T-V, publication/source acceptance or
live qualification.

The source realization and limitations are in hosting-lifecycle-plan.md; controls
and coordinator consistency review are in hosting-lifecycle-acceptance.md and
hosting-lifecycle-analysis.md. The new implementation uses retained independent
scheduler/primary/audit journals, explicit mTLS role capabilities, actual worker
PID/start/session/cgroup observations, same PID-namespace selection, immutable
actual-full-config takeover, per-generation destructive-attempt consumption and
fresh independent cleanup audit. Generic lifecycle/replay code, default refusal,
neutral pins/contracts and all protected workflow YAML are preserved.

The initial focused development batch passes all 80 then-existing nodes. After the scheduler correction, collection measures
2,282 full nodes and 1,980 required native nodes. The new module fingerprint is
`4aeea91a85313922960073905c78414460bf6c6bcfdbd4eddc98b4ed1eb56a15`;
all old 1,898 node identities, module counts/fingerprints and substantive anchors
are preserved. H05 anchors 21 nodes and H11 anchors all 82 lifecycle nodes. These
are committed collection expectations, not a generated CI allowance.

The initial full-run harness placed basetemp beside the selected TMPDIR. Two
existing neutrality export controls correctly refused that path; that run was
interrupted after 427 passes and is not qualification evidence. The corrected
run nests basetemp under its selected private TMPDIR. No source test or production
path boundary was weakened. Development failures and the lost-reply diagnostic
are retained separately from final qualification.

Private retained receipts live at
`/workspace/projects/.factory-binding-qa/runtime-next-20261112T171205Z/t012s-isolated-20261115/`.
The frozen input manifest has 148 tested Python/workflow files. Scope review proves
neutral pins, workflow YAML and generic lifecycle/replay source unchanged. The
development cleanup audit covers 9,540 process-generation records and 614 journal
summaries, with zero matching live processes; 19 exact development fixture roots
were removed after audit. Three retained actual cleanup positives confirm run-file
absence, credential retirement and retained/shared generation preservation. The
initial journal-only `/tmp/pytest-of-brett/pytest-1126` is already absent. None of
these fixture receipts is an operational cleanup or protected qualification report.

At this intermediate checkpoint, final ordered/full/OpenSpec/native qualification
and factory CI readback were pending. Measured completion is recorded below.

### Local review correction before final qualification

A private real-process probe proved that the retained staging acknowledgement could
remain readable after its selected scheduler died, permitting child creation. The
old-source full run was stopped and retained as pre-scheduler-fix-full.log/XML;
its interruption also produced a helper-teardown assertion, requiring actual later
PID-generation audit rather than a clean-teardown claim. It is not final qualification.
The source now rechecks the actual scheduler generation on every staging lease
observation. The new regression and complete protected-start positive both pass
(2 tests), including original private16 accounting. No new RPC, deadline or budget
is introduced. The measured module now has 81 nodes; final qualification restarts
on the corrected 148-file input manifest. No expert-panel or hosted review is claimed.

The final active-lease path had the same reproduced stale-scheduler condition.
Both active staging/final observations now require the actual selected scheduler
PID/start/boot to be current. The final regression proves operation is refused
before entry while independently authenticated janitor/audit cleanup still verifies
under the closed lease with that scheduler dead. The three targeted controls pass;
the intermediate run (386 passes, interrupted for review correction) is retained as
pre-final-lease-fix-full.log/XML and is not final qualification. Final collection
measures 82 new nodes, 2,282 full nodes and 1,980 mandatory native nodes.

### Factory post-merge CI verified

The exact merge run 43765166319 was cancelled by a subsequent main push. Its first
replacement 43766903480 was also superseded. The completed inherited-main
[run 43772988866](https://github.com/opensoft/openXfactory/actions/runs/43772988866)
passes on fefb5ae4ad7227a53469d5f1c711632d993b0dcf, including its existing quality
gate. Current main readback equals that head; accepted merge 0503c7bf36ea remains
its ancestor. The accepted six-file staging-refresh packet is preserved byte for
byte. No stale rerun, rules change or check override was performed. This CI result
is separate from the isolated candidate's full/native results and grants no runtime
authority. Retained receipts: factory-followed-main-ci.json,
factory-postmerge-ci-verified.json and factory-latest-source-proof.json.

### Final corrected-source qualification and teardown

The corrected source passes all seven ordered repository gates. Scoped checkout
initialization, both pin checks, syntax, plain and strict validators pass with no
validator errors/warnings. The full suite passes **2,282 tests**, with zero failures,
errors or skips, in 1,175.81 seconds. The default pinned OpenSpec verifier validates
all five targets strictly through @fission-ai/openspec@1.12.0, after rechecking the
pinned artifact's content address. An initial root-HOME cache permission error is
retained separately; the successful run selects only a task-local
OPENSPEC_CLI_PIN_CACHE and leaves the verifier/version/integrity checks intact.

The separate network-none, read-only-source native container passes all **1,980
mandatory cases** in 1,222.63 seconds and reports **runtime-conformance: PASS**.
There are zero missing, skipped, deselected, xfailed or nonpassing cases. H05 anchors
21 nodes and H11 anchors all 82 new lifecycle nodes. The source retains every old
1,898-node identity/count/fingerprint/anchor. All **148 tested Python/workflow inputs**
match the pre-run manifest after both runs. The 217 Python3.12 threaded-fork fixture
DeprecationWarnings are retained in each result; no warning suppression or case
skip is introduced. These local fixture roles do not qualify deployed administrative
separation or an external watchdog.

The full external audit covers 6,637 process-generation records, 223 journal
summaries and 71 role-helper receipts; the native audit covers 6,638 records, 223
journal summaries and 71 helper receipts. Both have zero matching live task processes
and zero nonclean teardown receipts. Each retains two independent cleanup positives,
including the dead-final-scheduler/closed-lease cleanup case: eight selected
retained/shared file identities preserved, three run files absent, fixture credential
retired and fresh independent audit retained. Eight additional control-journal
records are kept for each full/native run. PID counts are records, not distinct
processes; native numbers are never compared against py-bench's different PID namespace.

The native --rm container's absence is confirmed from the orchestrating daemon and
independently from Windows-native Docker before its namespace is considered gone.
Both final fixture roots were removed after audit, with absence verified. Earlier
19 development roots and seven correction/interruption roots were separately audited
and removed; their failed/interrupted results remain classified as such. Accepted
worktrees, owner-code checkout, shared pinned tooling, benches and unrelated jobs
are preserved. No real provider credentials or operational cleanup action is used.

Retained final receipts under the private evidence root include:

- qualified-inputs-before.json, qualified-results.json and matrix-extension-proof.json;
- ordered-final-static-gates.json, ordered-final-gate-1..5.log, full-command.json,
  full.log/XML, openspec-command.json and openspec.log;
- native-command.json, native-result.json, native.log/XML and native-preflight.json;
- full-qualified-cleanup-audit.json, native-qualified-cleanup-audit.json and the
  full/native-retained-control-journals.json records;
- native-container-absence.json, host-native-container-absence.json,
  full-fixture-removal.json and native-fixture-removal.json.

T012S and S01-S07 are complete as an isolated source candidate. No new candidate
PR/hosted CI, formal Codex panel, source ratification, T012T-V, setup/dispatch or live
hosting/provider acceptance is inferred. Publication/local Codex review and owner
source acceptance follow a later commission. Feedback remains deferred; neither
historical blocked write is replayed.
