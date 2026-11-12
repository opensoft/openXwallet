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
core. Its internal helper carries only public metadata URLs/CA references, never
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
