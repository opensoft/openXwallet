# Candidate qualification evidence

Date: 2026-11-11. Scope: isolated candidate source, not runtime activation.
Governing factory packet: `opensoft/openxFactory`,
`openspec/changes/add-workload-factory-binding/` (draft).

## Result

The final fresh Python environment ran the complete adapter suite:
**405 passed, 0 failures, 0 errors, 0 skips**, in 190.28 seconds.
Of those, **124** are factory/workload-binding cases. Dependencies matched the
CI declarations: Python 3.12, pytest 9.1.1, cryptography 50.0.1, rfc8785 0.1.4,
PyYAML 6.0.3, jsonschema 4.26.0 and rfc3339-validator 0.1.4.

The factory's affected code-surface/target-release suites passed **252 tests**.
The new factory proposal passed content-address-verified pinned OpenSpec strict
validation cleanly. The adapter OpenSpec corpus passed **5/5**. The wider factory
corpus reported **119 passed and one previously dispositioned finding** in
add-chain-attestation, with **zero undispositioned failures**. This is an existing
accepted exception, not a clean factory corpus. No disposition or floor changed.

## Gates and contract compatibility

In AGENTS.md order: vendored contract pin, neutral root/code lockstep pin, syntax,
plain validator and strict validator passed. Both validator runs reported zero
errors/warnings and confirmed the existing 21 positives/45 negatives across
13 requirements. The new operator snapshot also passed the pinned composed
canonical validator in strict mode.

Neither the neutral gitlink nor its pin changed. The canonical validator remains
at root b0af7c2ce53d63786a08a20aa3602a6f90345606 / code
72313daab1f229c049cb90998931564c1904dbbc. The isolated owning-source test explicitly
verified clean code checkout bb0e9dae89a771b05f6c235d0a77237288b95c85, accepted via
openWallet assembly 32aa09af5e4c28e1b3772b74fb8ddc08321db366. This is a separate
test-source selection, not consumer adoption.

## Positive and refusal evidence

- Real RS256 synthetic issuer token and separately signed Ed25519 observation.
- Exact caller/reusable-workflow identity, source, environment, run and attempt.
- Current wallet/public key/custody/revision, bounded active grant ancestors,
  non-widening acts/objects/lifetime and retained approval posture.
- Unsupported authority/constraints, missing/cyclic grants, changed registry,
  expired keys/tokens/challenges/observations, wrong signatures and scope refuse.
- One-use token/challenge reservation survives restart and concurrent attempts.
  Signer outage consumes the attempt; observed mid-call revocation returns no proof.
- Separate observer launches the measured reference worker from trusted config,
  hashes its source/configuration before and after, and signs the bound observation.
- Actual owning mutual-TLS custody signs a valid canonical preimage for the gate.
  The owning verifier independently accepts the returned possession proof.
- The worker first successfully resolves its current registry binding using the
  same transport credential, then is denied signing a valid canonical preimage.
  Granting that credential excess sign permission makes the denial probe fail;
  the mutation test verifies detection rather than recording a false denial.

## Cleanup and source identity

Success, injected post-proof failure and excess-permission mutation tests stop
their owned subprocesses and remove ephemeral private-key/state directories.
A separate post-suite process/filesystem audit found **zero remaining fixture
processes and zero remaining fixture key/state paths**. No containers, provider
accounts or federation entries were created by this feature.

The audit hashes each Python source/test file in the candidate module/test
directories plus the dependency file and pytest workflow. It SHA-256 hashes
the sorted compact JSON map of relative path to file SHA-256. Final tested digest:

`ca76249382b2d2b8aa9212c26b1b4efede1e06f069358c1d17acb0864a07d659`

Host-local JUnit and qualification audit reports were retained outside the
repository. Source/tests are unchanged after that audit; this record and task
completion are documentation reconciliation.

## Acceptance boundaries

Hosted CI is wired to the exact accepted owner-code commit but has not been run
for these local candidates. No PR is opened, merged or reviewed by a GitHub bot.
This is synthetic issuer conformance and same-user reference-process separation;
it does not qualify real GitHub OIDC, protected environment settings, hostile OS
isolation, deployed supervisor independence or production signer custody.

The profile remains draft, no human approval is supplied, and codeXfactory pilot
T002 remains blocked with runtime_bindings null and attended qualification not
performed. Published contracts, releases, consumer pins and live QA are unchanged.
Feedback remains deferred; neither historically denied write was replayed.
