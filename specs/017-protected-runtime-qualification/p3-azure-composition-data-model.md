# P3 deployment and remote evidence model

Status: proposed source model; not operative configuration
Canonical ownership: factory add-protected-runtime-azure-composition supporting-docs/composition-boundary.md

## Entities and relationships

| Entity | Identity and bound facts | Validation / lifecycle |
| --- | --- | --- |
| DesignAcceptance | Exact S1 adapter/consumer commits and owner scope | Design only; no appointment/grant |
| DeploymentEnvelope | Proposed profile, deployment/namespace/owner refs, accepted sources/builds, static plan, exact parent/name/resource/dependency refs and limits | Closed reservation/provisioned union <=16KiB/24ephemeral resources; unavailable facts forbidden, complete ordered set/attempt/owner frozen; actual readback only in provisioned form |
| NameReservation | Permanent normalized ARM path plus namespace identity, immutable creation attempt, ownership and accepted deployment digest | reserved -> create-consumed -> pending/quarantined or admitted -> retiring -> absent-tombstoned; never returns to unused |
| ProviderIncarnation | Exact ARM ID + VMvmId/diskuniqueId/networkresourceGuid + terminal creation/original operation ref | Per-kind trusted provider read; tags/numeric IP/path alone insufficient; outstanding writes block admission/retirement |
| RunnerCapture | Original privately held endpoint/bearer + accepted source/job phase and exact trusted origin/path policy | Capture once before untrusted work; immutable, redacted, phase-limited; no worker serialization/discovery |
| ManagedBuild | Exact base, reviewed build recipe/source/executable measurement, actual managed-image ID | Actual value after separately authorized build/setup; mutable base/URN-as-id refuses |
| LocalMeasurementEnvelope | Exact independent principal/observer provenance, local host/boot/process generation, source/plan/case/run/attempt and complete canonical config/policy bytes | Trusted local primitives only; authenticated remote response <=16KiB; current two-observer agreement and complete-byte authority derivation |
| FinalScopeLink | Accepted static/envelope reference, actual full config/policy/run/attempt/lease | Independently authenticated exact closed later link; static/full/run facts only after P6/P7, no backward hash cycle and no fields added to old profiles |
| RuntimeCleanup | Existing RunPlan and process/credential/file verification | Unchanged grammar; cannot represent Azure resources |
| InfrastructureReceipt | Separate closed profile and exact resource operation/identity/readback results plus independent preservation/revocation and scope | Closed setup/run variants; pre-P7 needs no invented final scope; unknown facts absent. Fresh observation authority cannot renew mutation scope; late completion fails, not HTTP202/pass-flag success |

## Permanent namespace rules

The external namespace service alone writes its conditional Blob journal. Initial
namespace/store identity is an explicit setup act, not lazy initialization. First
reservation is create-only; transitions require current ETag and legal state. A
conflict reloads current read-only state and refuses a stale mutation; it never
replays a possibly sent provider operation. Watchdog has semantic retirement/read
capabilities, provisioner one-shot create capability, neither raw storage reset.
Tombstones outlive evidence expiry and closed cases. Missing/corrupt/rolled-back
expected state refuses; no hostile privileged-host/valid-backup rollback claim.

## Independent outcomes

Runtime cleanup and infrastructure retirement have distinct actual origins and
must both pass before overall deployment acceptance. Retained data/disks/images/
vault/storage/watchdog/namespace are outside disposable deletion authority. Every
new scope or resource path needs an explicit accepted selection. Actual setup/run
IDs and authority never appear as placeholders in prepared documents.

Namespace key rule: validate a bounded ASCII ARM path with no query, fragment,
percent encoding, empty/dot segments or trailing slash; derive a
case-folded Azure-resource key so case variants cannot reserve the same path
again. Keep the independently selected original provider ID for wire/readback
binding. This key rule does not normalize GitHub identities, signed claims or
any neutral/runtime source contract. Case-variant reservation attempts refuse.
Empty pilot RGs are retained administrative parents, not automatically deleted
by the bounded per-kind sweep; later parent retirement needs separate scope.

Phase order is reservation under separately authorized P4 setup, actual provisioned
facts at P5, independent static selection at P6, and actual-run final-scope link
at P7. Immutable records reference earlier records; no earlier record hashes an
unavailable later one. Resource-set equality uses the exact reservation projection,
including order/kind/dependencies/policy/attempt/disposition. The setup-retirement
variant also covers partial setup without any provisioned envelope. Distinct
observation_authority_ref can authenticate a late failed observation, but cannot
reset/renew expired cleanup/proof scope, budgets or operations.
