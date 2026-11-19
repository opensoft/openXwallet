# P3 preparation and future isolated-source verification

Status: preparation only; implementation/setup/dispatch unauthorized

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
