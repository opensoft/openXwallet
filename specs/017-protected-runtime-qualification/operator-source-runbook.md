# Operator source conformance runbook

Status: isolated T012U qualified; local unpublished source candidate
Kind: source-runbook
Scope: offline source and disposable local fixtures only
Sole executable feature task: tasks.md T012U

## Authority and required inputs

T012T's connected isolated qualifier and the accepted private39 entry are source
capabilities. This runbook exercises existing local fixture services, RSA/mTLS,
kernel process controls and the exact owning proof/verifier. Provider observations
remain synthetic. Setup, protected dispatch, live OIDC/token acquisition, Apps,
permissions, environments, service units and operational state are unauthorized.
Feedback stays deferred; neither historical blocked write is a runbook step.

Run from the existing feature worktree in its declared Linux bench. Use its
reviewed hash-locked Python environment, scoped neutral submodules and prefilled
verified OpenSpec CLI cache. Source/dependency acquisition precedes the offline
gates and is not part of this recipe. Leave neutral pins, locks, workflows,
ordinary/staging/finalization/cleanup budgets, original clocks and default refusal
unchanged. The existing source CI job has a45-minute cap; hosted timing and any
cap adjustment remain T012V governance, not an inferred permission here.

Select these non-secret local references outside worker control:

| Input | Required selection |
| --- | --- |
| `QUAL_PYTHON` | Absolute executable path in the reviewed environment; preserve its venv symlink context |
| `WALLET_BINDING_OWNER_CODE` | Explicit clean owning code at `bb0e9dae89a771b05f6c235d0a77237288b95c85`; no ambient substitute |
| `QUAL_EVIDENCE_PARENT` | Existing private parent outside the checkout, owned by the source-test UID |
| Native image and mount mapping | Existing approved local immutable image digest and actual daemon-visible read-root mapping; no pull or guessed host alias |
| Source identity | Exact candidate HEAD/tree, neutral gitlinks, dependency/pin hashes and tracked-input hashes retained outside fixtures |

Use the bench's existing source-test privilege launcher: nonroot UID, empty
supplementary groups, no effective/permitted/ambient/bounding capabilities and
NoNewPrivs=1 across exec. Normal umask022 retains unsafe-permission negative
controls; the evidence parent and synthetic key/state permissions remain private.
A capability-holding/root pytest process is not a qualified substitute.

## Freeze and ordered source gates

With the selected environment and source-test boundary already established:

```sh
set -eu
QUAL_REPO_ROOT=$(git rev-parse --show-toplevel)
test "$(id -u)" -ne 0
QUAL_SOURCE_STATUS=$(git status --porcelain --untracked-files=all)
test -z "$QUAL_SOURCE_STATUS"
: "${QUAL_PYTHON:?select the reviewed absolute Python executable}"
: "${WALLET_BINDING_OWNER_CODE:?select the accepted clean owner}"
: "${QUAL_EVIDENCE_PARENT:?select the private external evidence parent}"
export WALLET_BINDING_OWNER_CODE
umask 022
QUAL_EVIDENCE_ROOT=$(mktemp -d "$QUAL_EVIDENCE_PARENT/t012u.XXXXXXXX")
export QUAL_EVIDENCE_ROOT
"$QUAL_PYTHON" -I -B - "$QUAL_REPO_ROOT" "$QUAL_EVIDENCE_ROOT" <<'PYTHON'
import os, stat, sys
from pathlib import Path
repo, root = (Path(value).absolute() for value in sys.argv[1:])
info = root.lstat()
assert root.resolve() == root and not root.is_symlink()
assert not root.is_relative_to(repo.resolve())
assert stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700
assert info.st_uid == os.geteuid()
PYTHON

git rev-parse HEAD HEAD^{tree} > "$QUAL_EVIDENCE_ROOT/source.txt"
git ls-files --stage > "$QUAL_EVIDENCE_ROOT/tracked-inputs.txt"
git -C "$WALLET_BINDING_OWNER_CODE" rev-parse HEAD > "$QUAL_EVIDENCE_ROOT/owner.txt"
QUAL_OWNER_STATUS=$(git -C "$WALLET_BINDING_OWNER_CODE" status --porcelain --untracked-files=all)
test -z "$QUAL_OWNER_STATUS"

"$QUAL_PYTHON" -B scripts/verify-contract-pin.py
"$QUAL_PYTHON" -B scripts/verify-openwallet-pin.py
"$QUAL_PYTHON" -B scripts/wallet-yaml-syntax-gate.py .
"$QUAL_PYTHON" -B scripts/validate-openxwallet.py .
"$QUAL_PYTHON" -B scripts/validate-openxwallet.py . --strict
TMPDIR="$QUAL_EVIDENCE_ROOT" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$QUAL_PYTHON" -B -m pytest tests/ -q -rs -p no:cacheprovider \
  --basetemp="$QUAL_EVIDENCE_ROOT/full-fixtures" \
  --junitxml="$QUAL_EVIDENCE_ROOT/full.xml" > "$QUAL_EVIDENCE_ROOT/full.log" 2>&1
OPENSPEC_TELEMETRY=0 "$QUAL_PYTHON" -B scripts/validate-openspec-cli-pin.py --all
```

Execute sequentially and stop on the first nonzero exit. The status assignments
preserve Git command failure; an empty captured output alone is insufficient.
Both source/owner prechecks have clean, dirty and command-error shell controls. Check the canonical
resolved evidence root is not a symlink, lies outside source and has the expected
UID/mode0700 before any fixture creation/removal. Independently hash every tracked
regular-file input and retain gitlink modes/SHAs before and after each gate; a HEAD
string or an empty diff alone does not prove bytes were stable. Retain failures
and interrupted runs as diagnostics. Re-freeze and repeat affected full/native
gates after executable corrections. Do not regenerate matrix expectations in CI.

## Mandatory native boundary

Use the existing isolation.py/conformance.py path from ordinary source CI. A native
rehearsal may use an already-approved local Docker image. The source/read root
includes the exact repository, reviewed Python environment and selected owning
code. It is mounted read-only; only a new empty mode0700 native fixture root is
writable. Root is used only for isolation bootstrap, then permanently dropped.
The existing bootstrap requires only loopback, clears groups/capabilities and the
environment, sets NoNewPrivs and rechecks the boundary in a fresh Python exec.

Resolve all `QUAL_DAEMON_*` and `QUAL_CONTAINER_*` references from the actual bench
mount inspection and retained run manifest. They describe the same approved files
in daemon/container namespaces. `QUAL_CONTAINER_NATIVE_ROOT` must be outside the
source checkout; its daemon-side directory must be new, nonsymlink and owned by
`QUAL_UID`. The immutable image must already exist locally. Select a unique
`QUAL_CONTAINER_NAME`/`QUAL_TASK_LABEL`; preserve unrelated containers and mounts.
These are local test-launcher variables, not runtime workflow inputs.

```sh
set -eu
docker run --rm --pull never --name "$QUAL_CONTAINER_NAME" \
  --label "opensoft.qa.task=$QUAL_TASK_LABEL" --network none --read-only --user 0:0 \
  --mount "type=bind,src=$QUAL_DAEMON_READ_ROOT,dst=$QUAL_CONTAINER_READ_ROOT,readonly" \
  --mount "type=bind,src=$QUAL_DAEMON_NATIVE_ROOT,dst=$QUAL_CONTAINER_NATIVE_ROOT" \
  --workdir "$QUAL_CONTAINER_REPO" --entrypoint /usr/bin/python3 "$QUAL_NATIVE_IMAGE" \
  -I -S tests/runtime_binding/isolation.py --uid "$QUAL_UID" \
  --python "$QUAL_CONTAINER_PYTHON" --temp-root "$QUAL_CONTAINER_NATIVE_ROOT" \
  --owner-code "$QUAL_CONTAINER_OWNER" > "$QUAL_EVIDENCE_ROOT/native.log" 2>&1
```

Retain the actual command, selected image digest/mount identities and exit status
outside native fixtures. Independently inspect the running conformance process:
nonzero UID, GID65534, Groups empty, NoNewPrivs1, CapEff/CapPrm/CapAmb/CapBnd zero,
only lo, Docker network none, rootfs/source read-only and only the owned fixture
root writable. The native bootstrap verifies clean environment; an external
observer must not add privilege merely to read another UID's environment.

## Interpret the result

The reviewed matrix contract fixes module counts, full node-ID fingerprints and
substantive anchors, including all H01-H12. Every required test must pass setup,
call and teardown. Missing/extra/duplicate/substituted nodes, deselection, skips,
xfail/XPASS, phase failure, nonzero pytest exit or changed owning source refuse.
The conformance CLI's final `runtime-conformance: PASS` now appears only after
its post-pytest owning-source check; pair it with exit0, JUnit and frozen inputs.
An intermediate pytest pass count, anchor line or tiny self-test corpus verdict
is insufficient. Final source-check exceptions/cancellation/zero-exit attempts
emit fixed refusal and cannot leave a final PASS.

Current measured candidate collection is2,523 full parent cases (plus nine passing
subtests),2,215 mandatory native nodes and64 conformance self-tests. All prior2,203
native identities and anchors remain. Hosted-evidence module remains186 cases;
H10=75/H11=143/H12=142. Collection is not a passing execution receipt; current
execution/cleanup status is in [implementation evidence](hosting-conformance-implementation.md).
The [qualification matrix](qualification-matrix.md) maps every H group to actual
positive/mutation controls and remaining live gates. Anchors overlap and their
counts must not be summed as independent tests.

## Independent fixture teardown and retention

Preserve redacted logs/JUnit, source and image hashes, aggregate case results,
actual38/39-read measurement, generation/retirement/preservation summaries and
exit status outside fixture roots. Retain no raw synthetic keys, tokens, proofs,
provider payloads, worker configuration or exception text as a public receipt.
All such values remain test-only and cannot supply a protected origin.

For the full run, audit inside its bench PID namespace; for native fixtures,
corroborate the exact named container is absent after --rm before interpreting
its namespace-local PIDs. PID alone is insufficient: compare PID plus start-time
from lifecycle-processes.json, helper-cleanup.json, credential-generations.json,
runner/hosted/crashed-generation.json, ownership manifests and lifecycle/staging
journals. Compare /proc/PID/stat field22 after the final ')' split. Process
absence or a different start-time establishes absence of that generation;
permission/namespace uncertainty remains unverified. Check no task-root-attributable
helper remains. A container absence proof cannot establish full-bench PID absence.

Inspect initial helper teardown receipts as well as current absence. Qualified
runs require no matching-alive initial teardown failures. Audit durable lifecycle
registration, stage release, closed lease, consumed action fences and independent
cleanup-audit without replaying any mutation. Verify exact retained/shared file
inode/device generations still exist, selected run generations are absent,
issuance attempts are retired, file pins released and independent audit retained.
The five preservation scenarios in each complete run cover final lifecycle,
scheduler death, maximal mixed-retention manifest and both busy-file-fence cases.
Intentionally corrupt negative-test journals remain diagnostic inputs, never a
reason to classify a positive cleanup as verified.

After verification, remove only canonical task-owned fixture roots with checked
UID/mode beneath the selected external evidence parent. Keep audit/removal receipts
outside those roots. Preserve source worktrees, neutral pins, consumed replay
semantics and unrelated resources. Lost mutation replies are read-only reconciled
at the same reference; unknown cleanup stays unverified rather than retried.

## Stop and hand off

Failure, cancellation, source drift, unsupported live origin or missing cleanup
cannot be upgraded by another passing component. Fix source within commissioned
scope or retain the refusal and request its owning decision. Source success grants
no live P01/deployed G02/G03/L01, administrator separation, external control-host-loss
watchdog, conditional infrastructure retirement, human/domain acceptance or
codeXfactory T002 completion. T012V owns later local review, hosted source CI,
publication and exact-head owner source acceptance. T001/T013-T015 and setup/
dispatch remain unauthorized; feedback deferred and blocked writes unreplayed.

## Current completion record

Frozen source `6e2f0bfc626ab05b5b0384bc3a97d2816cfd696a` passes the full2,523 tests
plus nine subtests and all2,215 mandatory native cases. Every prior node/anchor
remains; all64 conformance self-tests pass. The final native success line follows
owning-source postflight and pairs with exit0, zero errors/skips and unchanged
338-file/source-gitlink verification. Both actual hosted positives retain38-read
proof/cleanup measurements; the fixture-origin variant checks39 without live
promotion. Independent final audit verifies21,879 generation records and all ten
preservation cases, with no live attribution or initial teardown failure. Both
final fixture roots and the native container are absent; receipts remain.

The first full attempt had a setup/staging hosted-issuance refusal before the
intended runner-death boundary; its internal cause is unproven. An external
diagnostic SIGINT was absorbed before a separate cancellation injection, producing
a second diagnostic failure and three same-UID fixture helpers waiting at Python
shutdown. Only those verified direct descendant generations were retired; all
diagnostic roots were independently audited and removed. An unchanged focused
reproduction, fresh full run and native run pass. Qualified runs used no external
interrupt or manual helper retirement. No deadline, cap or assertion was relaxed.

These records qualify source/fixtures only. Later hosted CI, review, publication,
owner source acceptance and every operational/live gate remain separate.
