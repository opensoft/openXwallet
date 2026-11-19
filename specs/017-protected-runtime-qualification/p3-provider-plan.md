# T013P03 provider capability and compatibility subplan

Status: preparation only; implementation is not commissioned.
Scope: first codeXfactory machine-possession pilot, feature 017 T013P03 only.
Sole implementation list: [tasks.md](tasks.md).
Source basis: openXwallet #97, ratified head `33a00d474621921a1bd22ac95ba8f254d9875c11`,
landed as `3ca99fc79ab6ce5339cfd9e347559b241f7a57b8` with the identical tree.
The [acceptance record](evidence.md#2026-11-19-97-source-acceptance-and-p03-preparation)
records independent post-merge CI. No operational accepted_commit is selected.

## Authority and scope

Brett ratified #97 for source acceptance only, requested landing when green,
post-merge verification, then preparation of the next bounded P3 slice.
This prepares the existing T013P03 row; it neither commissions its implementation
nor marks that row complete. T013P04-P09 and original T001/T013/T014/T015,
consumer feature058 T002, appointments and independent human approval stay gated.

The factory's accepted
[composition boundary](https://github.com/opensoft/openXfactory/blob/c2dfbbcc6fa6965fcde18661bddca1dac7128d47/openspec/changes/add-protected-runtime-azure-composition/supporting-docs/composition-boundary.md)
owns the per-kind disposition and closed records. This subplan adds no wire
profile, field, role, input, provider kind, RunPlan resource or report grammar.
An implementation need that changes those decisions goes upstream before code.

Deliverable for a later isolated commission: the internal provider capability
module, substantive synthetic/authenticated-port controls and measured matrix
extension. It establishes per-kind facts and safe single-operation semantics,
not an Azure deployment, live provider qualification, watchdog or activated route.

## Technical context and unchanged boundaries

Use the existing Python environment and feature017 package conventions.
Proposed product path: `scripts/workload_factory_binding_runtime/azure_composition/provider.py`.
Proposed controls: `tests/runtime_binding/test_azure_provider.py`; collection changes
belong only in `tests/runtime_binding/matrix_contract.py` after actual measurement.

Reuse P02's validated reservation, immutable creation triplets, permanent namespace,
consume-before-send semantics and caller-owned Decision. A trusted embedding owns
authentication and selected provider/storage capabilities. Record construction,
response fields, tags or worker-supplied booleans do not authenticate a provider.
Raw credentials never enter records, workload context, exceptions or logs.

No ambient Azure credential chain, SDK auto-retry, CLI subprocess, arbitrary
endpoint, redirect, proxy, list/discovery call or automatic API-version fallback.
A narrow injected provider port may be exercised in isolation; production
transport/authentication and selected source-route wiring remain later gates.
The legacy credential transport has no ARM PUT route or general ARM operation-status route. The new injected capability boundary must be explicit and source-selected; a passing fake cannot establish production transport/authentication. Do not extend the legacy private HTTP route allowlist simply to make a fake pass.

Preserve `hosted/platform_readback.py`, existing transports, all old profiles,
inputs, roles, budgets, dependencies, pins, workflow YAML and default refusal.
No provider.py or executable fixture is created by this preparation.

## Provider identity and dependency evidence

Use the accepted request versions literally. Independently selected complete ARM
paths retain wire spelling and P02's normalized uniqueness keys. The evidence must
bind the original request, reserved path/kind/attempt, actual own incarnation,
terminal creation, current attachment/dependency facts and original operation.
Unknown or contradictory facts leave the resource ineligible.

| Kind | Accepted operation/readback version and own identity | Required pre-retirement facts |
| --- | --- | --- |
| VM | Compute 2025-04-01; properties.vmId | Terminal original creation, no pending writes, closed admission, explicit disk/NIC Detach, exact VM |
| Ephemeral OS disk | Compute 2025-01-02; properties.uniqueId | Original VM absent, attachment clear; no retained data disk |
| NIC | Network 2026-01-01; properties.resourceGuid | VM absent; no VM association; exact IP/subnet/NSG policy |
| Public IP | Network 2026-01-01; properties.resourceGuid | Original NIC absent; no foreign association; address text is not identity |
| VNet | Network 2026-01-01; properties.resourceGuid | Selected NICs absent; original approved subnets only; no foreign attachments, peering, private endpoints, delegations or service links |
| NSG | Network 2026-01-01; properties.resourceGuid | Last; NIC/subnet associations empty after selected VNet removal |

No missing identity is replaced by an ETag, numeric address, tag or guessed GUID.
The same name with a different own identity is a replacement and refuses.
No RG, standalone-subnet, force or implicit-cascade deletion is supported.
Deletion is controller-fenced under the accepted sole-ordinary-writer/no-reuse
invariant, not a claim that ARM deletion compares a generation atomically.
A hostile ordinary writer counterfactual must break acceptance.

The [VM GET reference](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/get?view=rest-compute-2025-04-01)
and factory per-kind references supply schema evidence, not deployed capability.
The NIC Learn request for 2026-01-01 currently
[renders 2026-03-01](https://learn.microsoft.com/en-us/rest/api/virtualnetwork/network-interfaces/get?view=rest-virtualnetwork-2026-01-01).
Keep 2026-01-01 pinned; unsupported-version/schema responses refuse. Do not infer
2026-01-01 support from the redirected page. Actual support remains a later
authorized readback gate, or a factory amendment if a version must change.

## Original-operation capability

A source-bound creation operation must consume the P02 creation attempt durably
before exactly one transport invocation. Do not expose a serializable reusable
permit. Restart, contention, a lost consumption reply or a lost provider reply
cannot produce a second mutation. A missing operation stays unknown; do not
invent an LRO ID or infer that no create occurred from a bare 404.

A later retirement capability must instead bind P02's durably consumed retirement attempt, the original incarnation and current controller fence before one fake-provider DELETE. Creation consumption is never deletion authority. P07 remains responsible for retirement orchestration.

Before returning creation/operation references, require independent durable receipt readback. An in-memory locator alone does not establish restart reconciliation; loss before persistence remains unknown and cannot trigger a resend.

A synchronous receipt binds the actual original request and terminal response.
An asynchronous receipt retains only the original authenticated operation
locator. Validate its trusted origin, subscription, provider, operation-specific
path/query and request association before any bounded status read. Never follow
a response URL as an unrestricted bearer destination. Missing correlation or an
unsupported locator refuses.

Azure documents asynchronous status through original response headers and
provider status. Follow only that original operation within the same Decision;
`Retry-After` cannot extend the enclosing deadline.
[Microsoft ARM asynchronous-operation guidance](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/async-operations)
also shows that operation status paths need not be resource-ID-prefixed.
No generic prefix rule may silently reject all valid positives or admit arbitrary
URLs. A 202 or an unrelated Succeeded body is not complete deployment evidence.

The [VM create reference](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/create-or-update?view=rest-compute-2025-04-01)
documents If-None-Match: *; do not extrapolate that header to other kinds or DELETE.
Readback remains distinct from mutation permission. P03 does not implement
P07's trigger handling, watchdog scheduling, independent retirement receipt or
P08's operational builder. No mutation is sent to Azure in source tests.

## Managed image and retained disks

The runtime image selection is an exact managed-image ARM ID with independently
selected immutable build/source and actual measured image facts. A marketplace
base URN is build provenance only: never substitute it for image_id or accept latest.
An image mismatch or mutable/unmeasured build refuses. Image construction and
actual image selection require later authorization.

Keep DeploymentSelection's OS-plus-at-most-one-data-disk bound per host.
The first-pilot design uses two retained data disks total: one on control and
one on gate, none on worker. Each host also has its selected ephemeral OS disk.
Retained data disks/images are excluded from the namespace's ephemeral resources
and from every mutation target, including through case/alias or dependency tricks.
Do not allocate the earlier five-disk upper bound or widen the legacy reader.

Verify explicit Detach for OS/data disks and VM NIC attachments, and the NIC's
public-IP association. Unknown/default-only policy cannot establish the required
explicit preservation proof.
[Microsoft associated-resource deletion guidance](https://learn.microsoft.com/en-us/azure/virtual-machines/delete)
describes these settings; it does not itself prove the selected deployment.

### Existing-reader compatibility edge

The legacy DeploymentReader supports the exact managed-image selection and
one/two disk tuples, with runtime GET versions images2026-03-01 and disks2026-03-02.
Those existing versions stay unchanged; P03's accepted disk-operation version is
2025-01-02. Tests must bind the same selected incarnation across the two contexts,
not silently substitute a version or declare a cross-version capability proven.

The legacy public-IP link check accepts exactly {"id": selected_id}. An expanded
NIC link carrying properties.deleteOption: Detach is therefore rejected there.
Preserve that legacy behavior. The explicit P3 provider adapter must validate the
complete expanded association independently; do not strip fields, rewrite an
authenticated response, synthesize a digest or claim the legacy reader accepted it.
Use real legacy-reader positives for managed-image/two-disk compatibility and a
separate full P3 public-IP/Detach positive and substitution refusals.

P08 must later prove the complete S1 composition through its explicitly selected
source route and existing approved fact interfaces. If that needs an old reader,
closed grammar or exact-type boundary to change, stop for factory/adapter
governance; do not declare the full route qualified in P03.

## Acceptance controls for the later implementation

This table refines the existing P03 acceptance row; it is not another task list.
Every negative starts from a working authenticated-port positive and changes one
fact. An outage is not a denial or a proof of absence.

| Existing requirement | Positive | Independent refusal or counterfactual |
| --- | --- | --- |
| R05 image | Exact measured managed-image ID through unchanged reader | Marketplace URN, latest, changed image/build/source or unauthenticated echo |
| R05 disks | Control/gate one retained data disk each; worker zero; old one/two-disk readers actually pass | Extra/wrong disk, wrong LUN/attachment/identity, retained target or alias selected for mutation |
| R08 one-shot creation | Actual durable namespace consume precedes the one fake-provider send; reconstruct service after process exit | Concurrent sender, crash before/after send, lost reply, stale attempt, missing namespace or reset |
| R08 terminal creation | Original synchronous receipt or original terminal LRO plus own resource readback | Pending/canceled/failed/unrelated LRO, orphan 404, invented operation, terminal status with contradictory resource state |
| R09 identity | Each of six kinds validates its own provider field and exact policy/dependencies | Same tags/name with replacement GUID, wrong field/API/type/subscription, omitted or extra association |
| R09 preservation | Explicit Detach and independent retained-resource observations | Delete/default-only policy, foreign association/subnet/peering, cascade/force/RG/standalone-subnet target |
| R09 fencing | No-reuse namespace plus independently established sole ordinary writer and no outstanding mutation | Legal hostile writer between observation and retirement invalidates eligibility; no fabricated ARM CAS |
| R11 bounds | Complete positive, every nested I/O charged to original Decision and existing counters/body caps | Deadline/clock/counter reset, unmetered pagination/poll, oversize or dropped bytes, URL/bearer export |
| R12 scope | Provider port/durable local controls remain source-only | Fixture relabeled as Azure, setup grant, live deployment, consumer/human acceptance or full P3 qualification |

Use existing real-local TLS/process primitives where they test actual deadline,
cancellation, redaction or restart behavior; deterministic provider/storage doubles
must record real call order/count and supplied original Decision. No live network
transport to Azure, token acquisition or destructive provider probe is authorized.

## Qualification and handoff

Current accepted baseline: 3,029 full parent cases plus 11 subtests, 2,607 mandatory
native cases, 170 P02 cases. Preserve every prior count/fingerprint/anchor prefix.
Measure new identities after implementation; do not guess replacement totals.

After a later implementation commission, qualify the final source through the
seven existing ordered gates and complete native isolation, with fitting positive
controls and independently audited helper/fixture/container teardown. Source
corrections require renewed exact-head qualification and local expert review.
Hosted CI/source-only ratification/landing remain distinct from live acceptance.

For this preparation, validate documentation links, scope/task consistency,
unchanged checkboxes and runtime/workflow/pin/dependency bytes, plus the existing
fast offline documentation/governance gates. Do not rerun hours of runtime tests
for documentation-only changes after verified main CI. No new schema, fake runtime
receipt or executable deployment file is part of the preparation.

## Decision ready for the owner

The next possible commission is isolated T013P03 implementation and testing using
this subplan. It is not granted by preparation or by #97's source acceptance.
T013P04-P09, setup, dispatch, issuance, provider writes and live qualification stay
uncommissioned. Roles, actual endpoints/IDs/images/initialization, full pricing,
UTC windows, independently confirmed human approval and consumer execution locks
remain later gates. Feedback deferred; blocked writes unreplayed.
