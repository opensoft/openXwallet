# P3 preparation and future isolated-source verification

Current bounded preparation (2026-11-24): [T013P08](p3-entrypoint-plan.md).
P07 is source-accepted and qualified; P08 implementation remains uncommissioned.
Earlier proposal and commission labels retain their original checkpoint scope;
see the current [owner record](p3-design-basis-acceptance.md#2026-11-24-105-source-acceptance-and-p08-preparation).

Status: source decision accepted; first P01/P02 isolated source commissioned; setup/dispatch unauthorized

## Inspect the planning packet

Read [owner authority](p3-design-basis-acceptance.md), [plan](p3-azure-composition-plan.md),
[research](p3-azure-composition-research.md), [model](p3-azure-composition-data-model.md),
[interface](contracts/p3-azure-composition.md) and [acceptance matrix](p3-azure-composition-acceptance.md).
The factory add-protected-runtime-azure-composition packet owns the proposed policy.
These documents are not an executable deployment recipe or grant.

## Validate preparation in the declared py-bench

From the selected feature017 worktree:

```sh
export SPECIFY_FEATURE_DIRECTORY=specs/017-protected-runtime-qualification
bash .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

Use the factory's repository-pinned default OpenSpec validation entrypoint for
its new packet/full corpus and this adapter's existing corpus. Check relative
links, unchanged runtime/workflow/pin/lock blobs and original task checkboxes.
Factory ledger provenance needs the real later publication PR; do not invent a
number, hand-edit a generated row or treat a known ledger gap as passing.

## Later source commissioning

Only after exact paired P3 source acceptance and explicit isolated implementation
commission, execute proposed T013P tasks in the sole tasks.md list. Use deterministic
provider/storage doubles and real local loopback TLS/crypto/process/state controls;
no Azure mutation, workload-token discovery or live service setup. Preserve prior
node IDs/fingerprints/anchors, run ordered offline/full/native gates and audit exact
owned-fixture teardown. Measure new counts after actual implementation, not in a plan.

No deploy/apply/setup/dispatch/signing command is supplied. Actual hosting, source/
images, principals, protections, state, complete costs and windows require later
T013 selection/setup/readback decisions. T014/T015 and consumer058 T002/human
assurance remain separate. Feedback deferred; blocked writes unreplayed.

## Current source checkout closure

The pinned neutral root delegates verification into its spec leg, and the full
source suite reads that exact script. In addition to the scoped root/code checkout,
initialize the exact pinned spec leg explicitly; do not fetch floating/recursive
legs. These are source checkout commands, not operational setup:

```sh
git submodule update --init openWallet
git -C openWallet submodule update --init code spec
```

The first publication diagnostic stopped because this pinned spec checkout was
missing. Correcting checkout requires no product/test/pin/expectation change.

## First bounded source slice

See [commission, source boundary and isolated verification](p3-namespace-implementation.md).
Only T013P01/T013P02 are commissioned. Source checkout/tests are not operational
setup. Later P3 source work, provider requests, setup and dispatch remain gated.

## Current next slice: P08 preparation only

P07 is source-accepted and independently qualified on main; the [parent receipt](p3-entrypoint-parent-main-qualification.json)
retains exact-source evidence and the approved bounded source-CI retry. Read the
[P08 subplan](p3-entrypoint-plan.md) before any future implementation commission.
Start with its two eligibility gates: the closed authenticated companion route,
then the complete independently authorized remote handoff into unchanged full
qualification. Package integration follows only a fitting connected positive.

Use the same source-only checkout and declared py-bench validation commands above.
This preparation adds no executable, test, deployment command, filled parameter,
credential, grant or state initialization. The original default CLI continues to
refuse; P08/P09 implementation and every setup/protected-dispatch gate remain open.
