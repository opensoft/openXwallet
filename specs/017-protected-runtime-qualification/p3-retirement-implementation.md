# T013P07 isolated retirement implementation

Status: implementation candidate; full/native qualification and publication remain open.
Date: 2026-11-23, America/La_Paz
Sole implementation row: [T013P07](tasks.md); no new task list.

## Accepted source basis

Brett ratified factory #1365 at `89dbe6e6640361c36321968725932058aa802e2b`
with adapter #104 at `ea7a46206413ba5392734fa67def7dcef6861835` for source
acceptance only, directed ordered landing, then resumed P07 in isolation.

| Repository | Actual merge | Independent main CI |
| --- | --- | --- |
| openXfactory | `587841747ffbbff0d91facee34ac22e76ec632e2` | [45249178184](https://github.com/opensoft/openXfactory/actions/runs/45249178184), attempt 2, success |
| openXwallet | `bfdfba05aad1e3b673bc0a3513297eb749a2cc1e` | [45249350766](https://github.com/opensoft/openXwallet/actions/runs/45249350766), attempt 1, all five jobs successful |

The accepted policy remains
`openxfactory-infrastructure-retirement-accounting-internal-v1`, commitment
`sha256:21b62c2621f3d98e5358c1ba4c5b0345a0237d10cfa52e59bea122487688979e`.
The [accounting plan](p3-retirement-accounting-plan.md) and
[retirement plan](p3-retirement-plan.md) retain the exact graph, limits and holds.

## Implemented candidate

The internal reconciler registers an immutable anchor before validating durable
handoff, retains the original authorization attempt even when its response is
lost or rejected, and admits one genuine later run-link transaction sharing the
original registration meter. Cleanup closes write/run admission, records its
original conditional claim, and reuses authenticated original generation and
operation records in dependency order. A consumed or uncertain send is never
replayed. Failed handoff cannot turn into acknowledgement on retry.

Additive namespace/provider views keep ordinary setup clipping and default
behavior. They prohibit creation/admission in the new scope. Cleanup enforces
both approved time bounds and each frozen request expiry. Pending operation
reads use the owning validator and the original three-read maximum.

The independent observer has its own original allocation and distinct principal.
It derives every resource, credential and preservation result from selected
authenticated ports. Terminal completion needs the actual permanent tombstone,
original terminal/no-send evidence and independent current absence. Supporting
fact expiries clip the final receipt and are rechecked around durable emission.
An authenticated current missing preservation body yields an unavailable audit
item without a current digest and an incomplete outcome. Authentication, scope
or transport uncertainty cannot create an invented failure origin.

All original public profile fields, core/parser behavior, pins, workflows,
dependencies, quality thresholds and operational defaults remain unchanged.

## Fixed source accounting

| Pool | Private | ARM | Namespace | Journal | Complete application bytes | Original clock |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Registration, including genuine run transaction | 128 | 0 | 128 | 32 | 1 MiB | each transaction <=30 seconds |
| Original cleanup | 768 | 160 | 512 | 128 | 12 MiB | <=300 seconds |
| Independent observation | 192 | 48 | 128 | 32 | 3 MiB | <=60 seconds |

Calls retain the <=10-second ceiling and original remaining time. All classes
remain disjoint; there is no reset, borrowing or owner transfer. Serialized
trigger admission permits at most four deliveries. Nested counts, bytes,
original clock objects and terminal burn/ended state retain their high-water
marks across callbacks. Direct private termination is sanitized outside the
caught exception context.

Selected ports must enforce response caps before materialization and expose
every physical backend request. The isolated reference backend supports bounded
metadata-first batch reads and immutable receipt caching. This does not qualify
a live Azure Blob/SDK adapter: a backend without a genuine bounded batch must
charge its actual individual requests and may fail the fixed eligibility gate.
A facade, cache label or aggregate digest cannot conceal those calls.

## Current source evidence

The measured collection adds 126 substantive cases: 3,707 full parent identities
and 3,285 mandatory native identities, retaining every original identity/order,
module fingerprint and anchor prefix. These are measured counts, not full-run
pass claims. Matrix changes contain only measured metadata and substantive anchors.

The strengthened focused run passed 483 cases; two new owner-process cases
revealed an input-framing defect, and both passed after that test correction.
The final 13 affected graph, byte-bound, fresh-process and missing-state cases
pass. The first five repository gates pass. Fresh exact-source full/native
execution, all seven ordered gates, independent teardown and local review
closeout remain required. T013P07 stays unchecked; hosted qualification and
owner source acceptance of this new runtime remain separate.

The fixtures exercise the complete14-resource/16-edge graph and16 registered
credential outcomes, actual retained provider/catalog/journal/controller objects,
real clocks, original mTLS issuance/retirement evidence, actual authenticated
client process loss, and fresh-process observation after mutator loss at claim
and effect-before-ack boundaries. Indexed original-operation lookup does not scan
unrelated history. Oversize metadata refuses before any blob opens; missing
selected state is never initialized or repaired.

No source double establishes live Azure API support, effective RBAC, deployed
watchdog survival, live custody, human approval or a cleanup SLA.

## Scope and next gates

Only existing T013P07 is commissioned. P08/P09, service/role appointments,
operational accepted commits/windows and live human/consumer acceptance remain
separate. Setup and dispatch are unauthorized. Feedback is deferred. Historical
blocked writes remain unreplayed. No new runtime PR or merge is inferred.

Run artifacts remain in the owned
`p3-retirement-implementation-20261123` evidence packet under
`/workspace/projects/.factory-binding-qa/runtime-next-20261112T171205Z/`.
Final source/run manifests and independent cleanup receipts must distinguish
diagnostics, exact-source qualification and later publication.
