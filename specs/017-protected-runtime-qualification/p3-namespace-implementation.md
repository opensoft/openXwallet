# P3 first bounded source slice: closed records and namespace

Status: isolated source candidate; source publication/acceptance and operation remain separate
Scope: feature017 T013P01/T013P02 only; first machine pilot

## Authority and provenance

Brett Heap source-ratified factory #1353 at c2dfbbcc6fa6965fcde18661bddca1dac7128d47,
adapter #96 at 9a087cf8c146617bebfb44921360bb4194cb91cf and consumer #586 at
aa4a50eea567ec1741db5e6ca48fda1dab53a945. They landed in order as factory
c41f023762115fbe13e160e0ce5223cc6ab461c8, adapter
93f88007729b85baed08c430e55e2847baa2f367 and consumer
4f929147aa68c554bbca39dd05c3aabcf83ea621; each merged tree equalled its ratified
tree and independent main CI passed.

The subsequent commission is: "Go ahead and implement and test the first bounded
P3 slice in isolation using the landed plan. Keep scope on the first pilot,
setup/dispatch unauthorized, feedback deferred; don't replay blocked writes."

This realizes T013P01 and T013P02, not T013P03-P09 or an operational owner act.
The factory-owned boundary at the accepted factory source remains authoritative.
Original T001/T013/T014/T015, consumer058 T002 and human appointments are unchanged.

## Implemented boundary

selection.py reads separately closed canonical reservation, provisioned,
final-scope and setup/run retirement records. It checks exact root/nested key
sets, canonical bytes and types, 16KiB caps, resource ordering and the approved
complete six-field projection. ARM uniqueness uses a case-folded key while wire
identities remain frozen. Dependency edges are retirement prerequisites from
the factory table, not ARM creation order. Final links are later immutable
records and cannot add backward commitments to earlier envelopes.

Caller-supplied approved/readback bytes and authority assessments must come from
independently authenticated embedding capabilities. Parsing itself authenticates
no service, observer, provider incarnation or permission. No selected source
builder, network listener, Blob client, provider adapter, enrollment or workflow
route exists in this slice. A Python record constructor is not a provenance gate.

Retirement outcome follows authenticated exact result bytes, current independent
read-only observation authority, original exclusive cleanup deadline and actual
preservation/revocation assessment. Late completion is failed; incomplete facts
cannot become complete through a claimed outcome. A provisioned run cannot claim
its created resources were never created. Historic final links may be inspected
after their proof authority expires without renewing it. Old RunPlan and report
formats remain untouched.

namespace.py is the internal semantic service over an injected authenticated
conditional storage port. The embedding alone owns raw storage credentials.
The first-pilot catalog is explicitly initialized out of band with one approved
namespace generation and exact selected path set; the source offers no initializer,
catalog extension, reset, delete, restore or garbage collector.

A conditional catalog claim permanently consumes the complete name set before
create-only resource-record writes. Only after every record exists does a final
conditional catalog transition make it ready. Partial/uncertain reservation stays
quarantined and cannot be silently resumed/repaired. Resource records use ETag
transitions; each original creation attempt is consumed durably before a future
sender may proceed. A conflict/uncertain mutation performs at most one read-only
reload and refuses; it never resends. Admitted incarnation/operation/readback
bindings cannot change. Retirement attempts remain consumed after ambiguity and
terminal tombstones cannot become available again.

The existing caller Decision bounds nested store calls and is never allocated or
renewed here. Namespace mutations in this slice remain inside the original setup
window; later provider/watchdog integration must provide its separately approved
scope. Read-only record inspection grants no mutation authority. This bounded
one-case catalog is not a generic multi-case namespace administration service.
Privileged administrator compromise and valid-backup rollback remain outside the
accepted trusted-administrator guarantee.

## Isolated evidence

The test-only conditional storage double uses durable SQLite transactions with
create-only inserts and revision-conditional updates; it is not a production Blob
adapter or an alternate runtime ledger. Tests use only synthetic QA identities,
approved vectors and no cloud/authentication transport. A separate Python process
commits one consumption and exits; a newly constructed service refuses reopening
that attempt. Concurrent contenders force stale ETags and only one succeeds.
Loss/corruption of expected state, partial reservation, lost responses, expired
scope and contradictory history refuse without reset or send.

Focused verification: 162 cases pass. Measurement covers all 443 executable
statements and all 118 branches of the two new source modules. This is local
source coverage, not a hosted Sonar or live-provider result.

The native matrix adds only this measured module and bounded R01/H11 anchors.
Every prior module count, full-node fingerprint and anchor prefix is retained.
The mechanical collection addition is needed because the native runner collects
the whole runtime_binding directory; leaving new tests outside its contract
would fail closed. T013P09's complete P3 qualification remains pending.

Full/native source receipts and independently audited fixture teardown are
retained separately for the implementation checkpoint; execution results must be
read from those receipts rather than inferred from collection or source coverage.

## Verification commands

Use the declared py-bench, exact pinned root/code/spec source closure, locked
Python environment and an explicit accepted owning-code checkout. The seven
ordered offline gates remain contract pin, wallet pin, syntax, plain/strict
adapter validation, complete tests and pinned OpenSpec. Run the existing native
isolation/conformance entrypoints with their real loopback-only Linux boundary;
do not replace them with a selective pytest invocation.

Focused command:

    python3 -m pytest tests/runtime_binding/test_azure_namespace.py -q

No Azure SDK/dependency, role, input, existing budget, profile, pin or workflow is
changed. Default operational_bindings still refuses. Setup, dispatch, workload
token acquisition, later P3 implementation, live qualification, consumer/human
acceptance and feedback are not commissioned here. Historical blocked writes
remain unreplayed.
