# Preparation Evidence

Status: draft
Scope: planning and accepted-source isolated rehearsal only

The new runtime feature has no implementation or live qualification result.
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
