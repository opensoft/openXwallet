# T013P03 isolated provider implementation

Status: local source candidate; focused qualification passed. Full ordered gates,
native isolation and independent final teardown remain pending at this checkpoint.
No source acceptance, publication, setup, dispatch or Azure qualification is implied.

## Authority and source basis

Brett separately commissioned isolated T013P03 implementation and testing using
[p3-provider-plan.md](p3-provider-plan.md), first codeXfactory pilot only.
The accepted factory composition and P01/P02 source remain the governing basis.
Feature017 [tasks.md](tasks.md) is the sole implementation list. The P03 checkbox
stays open until required qualification and cleanup are actually complete.
P04-P09, T001/T013/T014/T015, appointments, consumer058 T002 and independent human
approval remain gated. Feedback deferred; blocked writes unreplayed.

## Internal capability boundary

The new internal azure_composition/provider.py module uses independently selected
provider, durable private receipt and current controller-fence ports. It includes
no Azure client, SDK, credential acquisition, endpoint activation, initializer,
watchdog, trigger loop or source route. Dataclasses and response fields do not
authenticate provenance: the trusted embedding must authenticate each port and
independently approve exact policies and retained paths.

Each actual exchange, receipt lookup and fence observation shares the caller's
original Decision, remaining deadline and existing ARM/private counters. Only
immutable original receipt facts are cached, scoped to that same Decision; current
provider and controller observations are always fresh. Receipt bodies stay private
and bounded. Public reports, profiles and errors are unchanged.

The six selected resource kinds use their accepted literal versions and own
incarnation fields. Complete policy projections, current attachment/dependency
facts, exact managed image, explicit disk/NIC/public-IP Detach, original terminal
operation and retained-resource exclusions are independently checked. Unknown
facts refuse. There is no ARM compare-and-delete claim: the no-reuse namespace
and current sole ordinary writer/controller fence are required.

## One-shot operations and compatibility

A VM PUT implicitly creates its selected OS disk. Both permanent namespace
attempts are consumed before that one provider send; admission requires original
terminal creation plus independent readback of both own incarnations. Separate
admissions may fail partway without producing a provisioned-set proof.
No replayable permit, automatic retry or second mutation repairs uncertainty.

An original private receipt binds the complete request, original HTTP status and
response. Original asynchronous locators are strictly checked before a bounded
status read. A later successful status cannot overwrite an original error.
Restart reconciliation reloads immutable facts; creation authority cannot be
renewed by a fresh Decision. Later independently authorized retirement may read
historic creation facts without restoring old create authority.

Retirement requires current exact incarnation, detached model, dependency
tombstones plus actual absence and current closed admission/exclusive writer.
Its durable retirement attempt is consumed before one DELETE. Terminal original
deletion and independent fresh absence are required before tombstoning.
An acknowledgement or 202/204 alone does not establish removal.

The unchanged DeploymentReader actually passes control/gate OS-plus-one-data-disk
and worker OS-only fixtures. The new pure compatibility check binds independently
authenticated exact image/build facts and two retained disks total; it neither
builds nor measures a real image. Expanded public-IP Detach is validated by the
new provider capability; the legacy reader still rejects the expanded shape.
No stripping, API fallback or relaxed legacy shape is used.

## Measured isolated evidence

- 180 focused cases pass, including durable SQLite receipt/namespace behavior,
  eight-way contention, actual child process death before/after send, a real
  blocked local socket deadline, six-kind retirement and retained image survival.
- Focused branch measurement covers 467/467 provider statements and 82/82
  branches. This is source-test coverage, not deployed Azure capability.
- Five independent guard removals are detected by assertion failures: own GUID
  shape, sole writer, OS Detach, selected measured image and original expiry.
  Two further table substitutions (wrong own identity field and wrong network
  API version) break independent positive controls.
- The provider double uses independent literal API versions, resource types and
  incarnation-field names, and checks the actual requested version. It does not
  construct its oracle from implementation tables. The earlier full/native
  runs at 8a0b268 were stopped for this test-oracle correction, audited and
  removed; their exit137 results are diagnostic, not passing qualification.
- Actual collection is 3,209 full parent cases and 2,787 mandatory native cases.
  The new module contributes 180; all previous module counts, node fingerprints
  and anchor prefixes are preserved. Only bounded R01/H11 anchors are appended.
- Focused receipts, raw logs and source hashes are retained in the host-local
  p3-provider-20261119 evidence directory. The one failed coverage configuration
  preflight and earlier diagnostic runs are retained separately from passing
  qualification; no skipped or failing diagnostic is relabeled as a final pass.

No old runtime module, input, profile, pin, workflow, dependency or validator is
changed. Full/native qualification and teardown receipts must bind the frozen
candidate before this checkpoint may be promoted. Production transport,
authentication, actual provider-version/schema support and complete S1 route fit
remain later authorization/acceptance gates.
