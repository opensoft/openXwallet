# Operator source conformance runbook

Status: T012V accepted-main #79 integration locally qualified; final-head CI/owner acceptance pending
Kind: source-runbook
Scope: offline source and disposable local fixtures only
Sole source publication task: tasks.md T012V; owner acceptance and operations separate

## Authority and required inputs

T012T's connected isolated qualifier and the accepted private39 entry are source
capabilities. This runbook exercises existing local fixture services, RSA/mTLS,
kernel process controls and the exact owning proof/verifier. Provider observations
remain synthetic. Setup, protected dispatch, live OIDC/token acquisition, Apps,
permissions, environments, service units and operational state are unauthorized.
Feedback stays deferred; neither historical blocked write is a runbook step.

Run from the existing feature worktree in its declared Linux bench. Use its
reviewed hash-locked Python environment, scoped neutral root/code plus the pinned
spec leg for shared OpenSpec tooling, and prefilled
verified OpenSpec CLI cache. Source/dependency acquisition precedes the offline
gates and is not part of this recipe. Leave neutral pins, locks, workflows,
ordinary/staging/finalization/cleanup budgets, original clocks and default refusal
unchanged. The sequential ordinary source-CI job cap is 90 minutes under
T012V delegated wall-time governance; the separate traced coverage jobs retain
45-minute caps. Actual final-head hosted timing is recorded on PR #78, not
inferred from local execution. Accepted main #79 OpenSpec tooling explicitly
initializes and authenticates shared source in the exact spec leg. Complete-source
analysis also reads that leg; ordinary product/runtime validation stays code-only.

The private Linux qualifier must run on the main Python thread. Secondary-thread
entry refuses before any probe RPC/private debit. Trusted forked I/O inherits
the already-loaded TLS context and no extra privilege. One original Decision
bounds each RPC, reply/EOF and child retirement; failure/cancellation kills and
reaps before lifecycle cleanup. Fork-sensitive inherited locks can cause bounded
refusal. This reference does not claim general multithreaded-host support or an
external watchdog for loss of the entire control host.

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

Current measured candidate collection is 2,781 full parent cases (plus 11 passing
subtests), 2,369 mandatory native nodes and 64 conformance self-tests. All prior
2,761 full and 2,364 native identities and anchors remain. Hosted-evidence module
has 198 cases; probe controls add 22 and canonical-journal controls 115.
H03=97/H10=85/H11=284/H12=142. Collection is not a passing execution receipt; current
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
codeXfactory T002 completion. T012V owns local review, hosted source CI,
publication and exact-head owner source acceptance. T001/T013-T015 and setup/
dispatch remain unauthorized; feedback deferred and blocked writes unreplayed.

## Historical T012U completion record

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

## Historical T012V completion before main #79


The publication candidate's executable source is `05101d15ad407264a96818c8527229f1f0273ac0`.
All seven ordered repository gates pass, including pins, YAML, plain/strict
validator, the complete full suite and default content-addressed OpenSpec strict
validation. Full execution passes **2,761 parent tests plus 11 subtests**, zero
failures/errors/skips, in 1802.872 seconds outer wall time. Mandatory
native execution passes **2,364 nodes**, zero failures/errors/skips, in
1619.765 seconds outer wall time; final conformance success follows
owning-source postflight. All prior 2,523 full and 2,215 native identities remain.
There are 198 hosted-evidence, 22 total-deadline probe and 115 canonical-journal
controls; all 64 conformance self-tests remain. Current anchors H10/H11/H12 are
85/282/142 and R01 is 47; overlapping groups are not independent test counts.

All 365 frozen regular tracked inputs match after both runs. The neutral
assembly/code/spec pins are respectively `58cfa716c66e5b7f594db19b2d16f2bbc6fe7d9b`,
`b7c8ca1e0f9bb58674a12ffef89bf5dfc92cc58c` and
`e0f7467f52f75103e10cb6824ad88de460ec9d39`. The spec checkout is solely the
accepted main #77 source-analysis exception. Explicit qualification owning code
remains `bb0e9dae89a771b05f6c235d0a77237288b95c85`; it does not replace a neutral pin.

Independent native observation confirms the selected immutable image, Docker
network none, only loopback, read-only source/rootfs, UID1000/GID65534, empty groups,
NoNewPrivs1 and zero effective/permitted/ambient/bounding capabilities. External
final audit checks **24,537 generation observations**, 842 journals,
258 helper receipts and all ten positive preservation cases.
These are observations, not unique process counts. There is no attributable live
process or initial qualified teardown failure. Exact retained/shared file
identities remain, run files are absent, credential attempts are retired, file
pins released and independent cleanup audit retained. Both final owned fixture
roots and native container are absent. Earlier diagnostics and focused-control
roots are separately audited and removed; safe reports remain outside fixtures.

Nine-role local Codex expert review plus the master clears this implementation,
including deadline/cancellation/FD ownership, actual child tracing, real outage
injection and canonical replay compatibility. Retained focused tracing covers
145/152 helper statements and 39/42 branches with zero exclusions; actual child
resolve/sign/denial execution is retained. GitHub connector review is not claimed
or requested under the owner's local-only instruction.

Earlier interrupted/failed runs remain diagnostic. In particular, the staging
setup refusal and later 64-resource credential-retirement refusal have no proven
root cause. The pure byte-compatible replay correction reduces observed repeated
encoding cost; passing fresh full/native tests do not establish a general timing
guarantee. No consumed mutation is replayed, and runtime clocks/private39/other
phase caps and neutral APIs remain unchanged.

Final reconciliation is documentation only; executable/test/pin/workflow inputs
retain the qualified bytes above. Exact final PR-head hosted CI, actual coverage
job timing, Sonar and local-review reconciliation are tracked on
[PR #78](https://github.com/opensoft/openXwallet/pull/78); this record does not
predeclare their results. Only the sequential source-CI wall cap is 90 minutes;
separate traced coverage jobs remain at 45 minutes without threshold/exclusion
changes. Owner exact-head source ratification and landing remain separate.
T001/T013-T015, real provider/host/protected-origin qualification, external
control-host-loss watchdog, infrastructure retirement and human/domain/consumer
acceptance remain open. Setup and protected dispatch remain unauthorized;
feedback deferred and neither historical blocked write replayed.

## Current accepted-main #79 completion record

Executable `223e2c825494041b9104c475a8a294483f6fcaf2` passes 2,781 full tests plus 11 subtests
and all 2,369 mandatory native cases, with all prior identities preserved.
Nine integration roles clear the source. Independent final audit checks
25,005 generation observations and all ten preservation cases; final
owned fixture roots and native container are absent. Neutral root/code/spec are
050bede/ed567ed/0fe3151; explicit qualification owning code remains bb0e9dae.
Use the [full source/pin/evidence record](hosting-conformance-implementation.md#t012v-main-79-integrated-source-qualification)
for exact immutable IDs, actual timing and authority limits. Fresh final-head
hosted CI, evaluated Sonar and owner source ratification remain PR #78 gates;
this local source runbook grants no operational setup or protected dispatch.
