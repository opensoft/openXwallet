# OpenSpec P1 consumption acceptance
Status: draft
Date: 2026-11-15

The four declared bodies match published openXfactory
4e7f06ddac55ff46bfa4e8714eabf4d3d4964829 after their declared headers;
the JSON dependency lock is verbatim. Body/full-file hashes and the original
historical consumption record are retained in docs/openspec-cli-pin.md.
The same 1.12.0 artifact and all 80 locked packages verify. The vendored tarball
and existing adapted gate remain unchanged; no runtime/core pin advances.

Local acceptance: three new tests and four body subtests; six real strict
corpus items clean. Contract-pin and openWallet-pin checks, syntax gate,
normal and strict wallet validation pass with zero errors/warnings. Carve
manifest and neutrality identity gates pass. With the exact accepted owning
code bb0e9dae89a771b05f6c235d0a77237288b95c85 supplied as in CI, the
complete suite passes 2097 tests and four subtests with zero skips.
An earlier run omitted that owning source and had 49 explicit integration
skips plus one process timeout. The unchanged timeout-focused suite passed all
52 cases; the fully configured complete rerun supersedes that harness attempt.

The separate loopback-only conformance boundary remains a required hosted
gate. This bench refuses unshare network namespace creation; its permissions
were not changed. No protected runtime setup/dispatch, credential request,
active session/profile, historical release or billing setting is modified.
Provider main landing, fresh hosted CI/Codex review and consumer-main readback
remain required completion gates.
