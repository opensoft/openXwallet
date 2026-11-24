# P3 source research and decisions

Current bounded preparation (2026-11-24): [T013P08](p3-entrypoint-plan.md).
P07 is source-accepted and qualified; P08 implementation remains uncommissioned.
Earlier proposal and commission labels retain their original checkpoint scope;
see the current [owner record](p3-design-basis-acceptance.md#2026-11-24-105-source-acceptance-and-p08-preparation).

Status: planning research complete; no live capability qualification
Date: 2026-11-19

## Authority and method

T013-S1 exact design basis is [accepted](p3-design-basis-acceptance.md), roles unconfirmed.
Read-only source and primary-document research resolves proposed source choices;
actual deployment facts remain operator gates. No provider writes, workload tokens,
secret reads, feedback, publication or runtime implementation occurred. Research
used two bounded read-only agents per the Spec Kit planning workflow.

## Decisions, rationale and alternatives

| Decision | Source evidence / rationale | Rejected alternative |
| --- | --- | --- |
| Separate selected companion route | workflow.py's operational_bindings is unconditional refusal; explicit new source can construct accepted hosted capability types after later acceptance | Flag/file/plugin or edited JSON activates default |
| Protected helpers on worker kernel | hosted/measurement.py reads local boot/proc/files; hosted/finalization.py independently derives bytes; hosted/lifecycle.py checks local PID namespace/boot and exact PosixResources | Passing remote PID/JSON as local ProcessLaunch or replacing exact types through configuration |
| Closed authenticated remote whole-byte evidence | Existing primitives are local; independent control must verify actual signed/authenticated observer provenance and complete final configuration/policy | Digest-only agreement, worker fact echo or GuestReader JSON as kernel measurement |
| Managed-image build/import | hosted/platform_readback.py requires imageReference exactly selected id | Substituting S1 marketplace base URN or mutable latest |
| Two retained disks total | DeploymentSelection permits OS plus at most one data disk per host; control/gate one each fits S1 ceiling | Widening disk reader silently or allocating all five permitted upper-bound disks |
| Original runner capture is platform trust | TokenClient enforces exact endpoint; GitHub documents injected URL/bearer, actual URL is per-job | Pretend REST corroboration, discovery token or untrusted env as its own anchor |
| External authoritative namespace | Control POSIX ledgers cannot be silently restored/mounted after host loss; separate conditional Blob service survives the three-host failure domain | Network SQLite or stale independent backup called authority |
| Permanent path tombstones and sole ordinary writer | VM create documents create-only precondition; delete lacks generation comparison; vmId identifies incarnation | Claim If-Match delete, tags-then-delete or TTL name reuse |
| Per-kind incarnation and explicit Detach | VMvmId/diskuniqueId/networkresourceGuid identify distinct resources and dependent deletion differs | VM semantics extrapolated to all kinds, implicit cascade or broad RG sweep |
| Separate retirement receipt | lifecycle.RunResource kinds are process/credential/file; PosixResources disclaims cloud deletion | VM-as-process/disk-as-file or hidden old-report fields |
| Original budgets remain bounds | Existing hosted/readback/qualification code accounts one shared Decision and fixed reader/body caps | Reset clocks/private budgets, unmetered remote fetch, guess counts or claim positive before source exists |

## Primary references and limits

- [GitHub OIDC reference](https://docs.github.com/en/actions/reference/security/oidc) documents injected token URL/request bearer; [runner source](https://github.com/actions/runner/blob/main/src/Runner.Worker/Handlers/ScriptHandler.cs) supplies them from its trusted system connection. This supports explicit platform trust, not independent REST attestation.
- [VM create/update](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/create-or-update?view=rest-compute-2025-04-01) documents create-only If-None-Match; [VM delete](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/delete?view=rest-compute-2025-04-01) documents no generation precondition. Absence of a documented header is not a successful mutation probe.
- [VM GET](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/get?view=rest-compute-2025-04-01), [disk GET](https://learn.microsoft.com/en-us/rest/api/compute/disks/get?view=rest-compute-2025-01-02), [NIC GET](https://learn.microsoft.com/en-us/rest/api/virtualnetwork/network-interfaces/get?view=rest-virtualnetwork-2026-01-01), [VNet GET](https://learn.microsoft.com/en-us/rest/api/virtualnetwork/virtual-networks/get?view=rest-virtualnetwork-2026-01-01), [NSG GET](https://learn.microsoft.com/en-us/rest/api/virtualnetwork/network-security-groups/get?view=rest-virtualnetwork-2026-01-01) and [public-IP GET](https://learn.microsoft.com/en-us/rest/api/virtualnetwork/public-ip-addresses/get?view=rest-virtualnetwork-2026-01-01) identify the per-kind fields. Actual supported versions/identities need later current readback.
- [Explicit associated deletion policy](https://learn.microsoft.com/en-us/azure/virtual-machines/delete) supports selected Detach; [RBAC roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-definitions) explains additive grants/NotActions. Trusted privileged administrators are not excluded by merely naming a narrow ordinary role.
- [Blob concurrency](https://learn.microsoft.com/en-us/azure/storage/blobs/concurrency-manage) and [Put Blob](https://learn.microsoft.com/en-us/rest/api/storageservices/put-blob) supply storage conditional primitives, not cloud-resource CAS delete. Namespace credentials/retention remain private trusted-service responsibilities.
- [Functions timer](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-timer) supplies scheduling; its lock is not generation fencing and its schedule is not an assured cleanup deadline.

## Research closure versus later inputs

The source approach is selected for proposal, not accepted or implemented. Actual
resource/service/MI/App/CA/image/credential IDs, runner origin policy, human account
ownership/appointments, inherited-writer exclusions, initialized journals, capacity,
network routes, full pricing and absolute windows cannot be invented. They are
explicit future operator gates, not unresolved source-algorithm defaults. Any
contradiction discovered in source acceptance requires a governed amendment before
implementation; no hidden fallback is authorized.

## 2026-11-24 P08 research refinement

Decision: preserve the old CLI/default and select one literal companion command
through trusted source construction. Rationale: the graph validator and its
Controller, staging and current GitHub readback consumers all authenticate that
command; editing YAML alone cannot select a valid new route. Alternatives such
as a flag, arbitrary callback/path, environment or data-file switch are refused.

Decision: add the sealed-result consumption seam in its existing owner module,
remote_evidence.py, only after the implementation gates identify the exact original
launch/store/registration state and independent complete-byte/run authorizer.
Rationale: VerifiedRemote alone is not full admission; existing FinalizationBinding
and FinalizedPlan constructors supply no authority. The owning lifecycle checks
and Qualifier's single existing admit_finalized call remain mandatory. A private
one-shot capability is not durable cross-process exactly-once state.

Decision: package immutable reviewed source and launch wiring while preserving
consume-before-send ephemeral ownership. Rationale: a bulk ARM/Bicep deployment
would bypass the existing namespace/provider/reconciler operation model. Retained
foundation setup and actual service activation remain separate operator acts.

The [P08 subplan](p3-entrypoint-plan.md) captures the source decisions and amendment
boundary. Two read-only planning research agents and their bounded consistency
follow-ups informed it; no implementation or live capability result is claimed.
Concrete live configuration remains a later operator gate, not a source default.
