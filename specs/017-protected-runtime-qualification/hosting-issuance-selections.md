# Hosting and issuance selection proposal

Status: T013-S1 design basis accepted at081dad41cfb4; roles unconfirmed; P2 incomplete; setup/dispatch NOT GRANTED
Proposal: T013-S1, 2026-11-19 UTC (2026-11-18 America/La_Paz)
Scope: read-only inventory and documentation; no implementation commissioning or operational grant
Authority: existing factory `prepare-protected-runtime-qualification` and `add-protected-runtime-hosting-issuance`; sole implementation list remains feature017 tasks.md

Current owner act: [T013-S1 acceptance and P3 preparation](p3-design-basis-acceptance.md).
The proposal below is the accepted design basis at the named commit. Its
operational caveats remain, and the historical proposed-acceptance wording below
is not a new unaccepted choice. P3's separate source composition is unratified.

## Accepted entry state

Brett source-ratified [#95](https://github.com/opensoft/openXwallet/pull/95) at
`5303411fde20240b956ae5831f4aa5805f00abc5`. It merged normally as
`05790f37383cdaeb2815b2912d45f267f608fbe3`, with equal ratified/merged tree
`f8fc860bc530d88a5941a74557df5719eb28b75c`. Its independent
[push/main CI](https://github.com/opensoft/openXwallet/actions/runs/44438983720)
passed at that merge. #94's accepted SQLite correction and earlier isolated
qualification remain source evidence, not a deployed system.

This proposal supersedes the older generic hosting recommendations where it
names an explicit candidate. It selects no executing `accepted_commit`, static
digest, preauthorization, credential, grant or run. Default operational bindings
still refuse before outputs/OIDC. All four [operational stages](scoped-authorization.md)
remain NOT GRANTED; T001/T013/T014/T015 remain unchecked.

## Read-only inventory and limits

Inventory observed at 2026-11-19 03:39-03:46 UTC, with subscription-explicit Azure
management reads, narrow directory metadata reads and GitHub GETs. Detailed
resource/RBAC/network/directory responses and query receipts remain host-local;
no secret/key/token value or workload OIDC token was requested. This local draft
has not been pushed, published as a PR or added as a public qualification receipt.

- Opensoft QA subscription `297b2389-33bf-48c8-8deb-0b92838431e4` in tenant
  `74ce1e7d-7455-4694-b00d-9ac83c6821ce` is Enabled. Its ten resource groups
  and 128 resources include shared platform/application infrastructure. None
  of the proposed pilot resource groups/hosts exists in that inventory. The
  production-default CLI context was not changed; queries named the QA scope.
- The same-tenant DR-test subscription inventory returned zero resource groups;
  it is not selected. An empty inventory supplies neither quota nor trust evidence.
- West US total regional vCPUs: 8 used / 14 limit. Original D2as v5: 0 / 0 family
  quota and `NotAvailableForSubscription`. D2as v4 is also restricted. D2s v3
  has no reported restriction and 0 / 10 family usage, but is a retiring series;
  it is a diagnostic alternative only, not an automatic fallback.
- Modern `Standard_D2as_v6` is listed with no restriction, x64/2 vCPU/8 GiB;
  its `standardDav6Family` quota is 0 / 10. D2s v6 and D2as v7 are also listed
  unrestricted, but are not alternate authorized sizes. Listing and quota
  headroom do not reserve capacity or guarantee allocation. Three proposed
  hosts consume all six currently spare regional vCPUs; concurrent QA growth
  can invalidate the selection. No quota increase/reservation was requested.
- Exact stable Canonical base image version observed:
  `Canonical:ubuntu-24_04-lts:server:24.04.202611170`. This is an image candidate,
  not a measured deployed appliance or approval to use a mutable `latest`.
- GitHub still has only ineligible `copilot`; both protected workflows have zero
  runs. Token defaults are read-only with PR approval disabled. OIDC uses the
  default immutable-ID prefix `repo:opensoft@638385/openXwallet@1347887821`.
  Existing configuration is preserved.
- `scottdriscoll` (1554882) and `NikitaFlimakov` (5066327) currently have repository
  admin access. Eligibility is not appointment, availability or independent
  domain human assurance. Directory candidates exist, but cross-provider
  account ownership and effective operational separation remain to be verified.
- QA has subscription-wide Owner assignments, including Brett and two further
  user principals with related directory identities. Do not count accounts as
  independent humans. These administrators remain a common trusted boundary;
  this pilot does not claim resistance to a malicious subscription Owner.

The first role-list invocation used incompatible read-only CLI flags and failed;
a corrected subscription-explicit list succeeded. The high-level SKU list timed
out; the subscription/location-filtered ARM GET succeeded with no continuation.
The broad image list also matched daily offers; the candidate above instead uses
an exact stable-offer GET. Failed/broad diagnostic output is retained, not used
as the final selection evidence. No permission was changed to obtain readback.

## Selections presented for acceptance

These are design selections only. Human appointments require owner acceptance
and acknowledgement; actual deployment identities/endpoints remain P3/P4/P5 gates.

| ID | Recommended selection | Acceptance limit / unresolved fact |
| --- | --- | --- |
| S01 Purpose | `case:codexfactory-possession-qa-001`; one machine possession prerequisite for codeXfactory feature058 T002 | No domain read/marker action, simulated human factor or attended acceptance |
| S02 Target | Azure Opensoft QA tenant/subscription above; West US; new `rg-opensoft-wallet-mfa-qa`, separate `rg-opensoft-wallet-mfa-watchdog-qa` and `rg-opensoft-wallet-mfa-retained-qa` | Existing QA resources and production excluded; proposed names are absent in observed RG inventory, not reserved/created |
| S03 Compute | Three `Standard_D2as_v6` x64 Linux hosts, max 2 vCPU/8 GiB each: `vm-wallet-mfa-control-qa-01`, `vm-wallet-mfa-gate-qa-01`, `vm-wallet-mfa-worker-qa-01`; stable base image above | No size/region/spot fallback; refresh capacity/quota/image and review final build/executable measurements before setup |
| S04 Network | New nonpeered `vnet-wallet-mfa-qa-01`; candidate `10.249.72.0/24`, separate control/gate/worker subnets; private gate/worker addresses; control HTTPS ingress only for bounded authenticated callbacks | No existing AKS/bench/VPN/CA/DNS/peering change; candidate prefix differs from observed QA VNet only, not an org-wide route clearance; exact routing/NSGs/CA/listener/runner reachability need P3 proof |
| S05 Human roles | Brett Heap accountable owner, proposed setup/rollback coordinator and original dispatcher `brettheap` (1513478); Scott Driscoll proposed required reviewer `scottdriscoll` (1554882); Scott also proposed external-watchdog/independent cleanup-readback owner; Nikita Flimakov proposed trusted-service/state administrator | Nobody contacted/appointed; no automated impersonation or self-review. Directory/GitHub account binding and effective access must be confirmed |
| S06 Administration | Proposed Scott: external watchdog administration and independent cleanup readback; Nikita: trusted gate/custody, authority/controller/state/credential-broker and control-host janitor administration; Brett: worker/infra setup coordination, no runtime trusted-service credential | Separate per-service identities/OS permissions, worker exclusion and no control-host credential able to administer the external watchdog required; common subscription Owners explicitly trusted. Audit acceptance needs independent provider evidence, not only an administrator's self-report |
| S07 GitHub protection | New `wallet-mfa-pilot-qa` in repo ID1347887821/owner638385; reviewer1554882 only; prevent self-review, disallow admin bypass, exact main-branch restriction; retain `copilot` unchanged | Actual environment ID, complete protection, branch-versus-tag and current approval readback follow separately authorized setup; one required review is not a quorum claim |
| S08 Source policy | `coordinated`; exact final accepted main SHA and short recorded hold before the sole broker send; independent current source/protection reads | No hold/rule/tag/freeze applied now; GitHub dispatch is not atomic SHA pinning and this is not protection against malicious repository administrators |
| S09 Hosting/issuance | Control: bootstrap/operation authority, repository-only Actions-write broker, separate Actions-read/necessary Contents-read controller, retained dispatch/finalization state and lifecycle janitor; gate: records/challenge/registry/custody/supervisor with separate peer identities; worker: worker-channel workload only | OS/caller/IMDS exclusion and independent authenticated composition/launch measurement required. Exactly seven runtime grammar roles and eight source roles remain; no worker Azure MI, GitHub App key, vault access or shared bench credentials |
| S10 Custody/state | Owning Ed25519 software custody on gate; dedicated pilot credential broker/Key Vault candidate; private local POSIX managed-disk stores for dispatch/authority/replay/staging/finalization; retained state outside disposable cleanup allowlist | No native Key Vault Ed25519/HSM claim, no NFS/Blob SQLite, silent initialization, reset or rollback. Actual disks/device/inode/initialization/access/recovery receipts and key/CA/version refs required |
| S11 Cleanup | Control-host janitor plus independently administered Azure Functions timer watchdog in separate RG/failure domain, with separate identity/state; candidate one-minute poll and conditional exact-generation retirement | Functions is a proposed composition, not a deployed/qualified watchdog. Prove control-loss/expiry handling, provider-safe generation fencing and independent absence/revocation/preservation readback; no cleanup SLA inferred |
| S12 Limits | Max three hosts/6 vCPU/24 GiB; disposable-resource envelope <=24h, case <=30min; proposed total USD50 ceiling and 30-day redacted evidence retention | Full priced allowlist incl retained disks, storage, networking, credentials/watchdog/logs/evidence and future retirement costs remains incomplete. Absolute UTC window/expiry and enforceable limits required in later setup/dispatch decisions; no automatic spend cap claim |

Proposed directory identity references, for account-ownership verification only:
Brett `f4e2f934-10c3-493d-bb45-12ad3f586d24`, Scott
`d2daf25b-c786-4518-bd11-4778d96bf81b`, Nikita
`47f0c0d3-4359-4d61-bca8-5436ba3d69d1`. Alternate similarly named directory
accounts are not substitutes. Names or keys alone do not establish independent
administration. No role assignment or account enrollment is authorized here.

## Proposed resource names and bounded composition

The future source proposal should use the following exact candidate names. These
are labels for acceptance, not assigned resource IDs, availability reservations
or an authorized create/update allowlist. An unexpected existing resource must
refuse rather than be adopted.

| Scope | Candidate names / maximum shape |
| --- | --- |
| Disposable QA RG | `rg-opensoft-wallet-mfa-qa`; VNet `vnet-wallet-mfa-qa-01`; subnets `snet-control` (candidate .0/27), `snet-gate` (.32/27), `snet-worker` (.64/27) within candidate10.249.72.0/24 |
| Disposable compute | The three S03 VMs, three NICs, three OS disks <=64GiB each; no scale set or fourth VM |
| Callback ingress | One control-host public IP `pip-wallet-mfa-control-qa-01`, HTTPS443 only; no public gate/worker or administration listener. Exact server name/certificate/CA and runner path remain P3 choices |
| Retained RG | `rg-opensoft-wallet-mfa-retained-qa`; at most five private local POSIX data disks <=32GiB each, explicit VM detach/preserve policy; dedicated credential-store candidate `kv-os-wallet-mfa-qa-01`; redacted-evidence storage candidate `stoswalletmfaqa01` |
| Watchdog RG | `rg-opensoft-wallet-mfa-watchdog-qa`; timer app `fn-os-wallet-mfa-watchdog-qa-01`, one consumption plan, dedicated storage candidate `stoswalletmfawdqa01`, separate identity candidate `id-wallet-mfa-watchdog-qa-01`; no control/gate/worker credential to modify it |

Global vault/storage/app names have not been availability-reserved; their assigned
identities and effective scopes follow authorized setup. Dedicated CA/issuance,
App installation, private state mapping and bounded egress still need P3 review.
No implicit outbound access, existing VPN/CA/credential reuse or budget-free
network/log service is assumed. Any extra resource (including explicit outbound,
private-endpoint or logging infrastructure) requires a bounded, priced allowlist
amendment before setup. Retained replay/dispatch authority cannot be destroyed
or reset merely because evidence reaches30days; its lifecycle/recovery disposition
and full retention cost require approval independently of disposable24h expiry.

## Identity, credentials and evidence

Retain bootstrap audience `urn:opensoft:openxfactory:bootstrap-admission:v1`.
Propose proof audience `urn:opensoft:codexfactory:wallet-possession:qa:v1`.
Derived expected-subject candidates, not observed token claims:

```text
Preflight: repo:opensoft@638385/openXwallet@1347887821:ref:refs/heads/main
Protected: repo:opensoft@638385/openXwallet@1347887821:environment:wallet-mfa-pilot-qa
```

Full phase claims, actual provider corroboration, trusted transport and relying-
party acceptance/exclusion are required. Job permission can request other
audiences; every owned relying party must enforce its selected purpose. No
workload token is minted for discovery. Select new repository-limited App
installation/credential-version/revocation references through P3/P4; existing
broad Apps, software fixture keys and shared credential stores are not selected.

The seven runtime roles remain records, challenge, registry, custody, supervisor,
worker channel and janitor. Bootstrap/controller/authorization/readback/watchdog
clients do not add grammar roles. All actual service URLs, SP/object IDs, key and
CA references, image/build digests, initialized-store identities, final static
and full approvals remain unselected. A generated role label is not an endpoint
or identity. This packet creates no executable lock/config/grant.

## Pricing and provider capability findings

The Microsoft Retail Prices API returned West US Linux on-demand D2as v6
USD0.107/host-hour (meter `d53210a4-c34c-5cba-be99-a672720c388d`). Three hosts for
24 hours give **USD7.704 VM compute only**. This excludes disk/network/storage/
watchdog/credentials/evidence, taxes, account terms and retained-resource costs;
it is neither a full quotation nor an enforced USD50 cap. Pricing/capacity must
be refreshed before operational acceptance. The API read used Linux, non-Spot,
non-Low-Priority, non-Cloud-Services consumption rows in USD; Windows rows were
not used. D2s v3's diagnostic price is not the selected price.

Official references: [Dasv6 sizes](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dasv6-series),
[retail API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices),
[Functions timer](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-timer),
[VM deletion API](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/delete?view=rest-compute-2025-04-01).
The reviewed VM deletion API documents no `If-Match` generation precondition;
this is not evidence that an arbitrary ETag header will fence deletion. A
read-tags-then-delete sequence alone is insufficient. P3 must prove a reviewed
provider/controller fencing and non-reuse design against concurrent replacement,
or refuse the selected deployment. No deletion or capability probe was sent.
Timer availability alone likewise proves neither deadline completion nor cleanup.

## Acceptance boundary and remaining gates

The proposed owner decision is: accept **T013-S1 S01-S12 as a design basis only**,
including the named role nominations subject to acknowledgement and identity/
access verification. This permits preparing the governed P3 source proposal; it
neither accepts a live composition nor commissions implementation, setup,
credential/signing use, token discovery, dispatch, retries or public disclosure
of the detailed local inventory. The agent does not mark an owner act complete.

P2 remains incomplete until accepted selections have verified account/role
ownership, independent administrative/access evidence, actual source-update
control ownership and complete resource/budget/window selections. The following
block the corresponding later gate, not review of this design basis:

- P3: exact service/App/trust/state/credential/image/executable composition,
  bounded authenticated network path, independent launch measurements and
  provider-safe watchdog retirement; concrete activation source must be reviewed.
- P4 setup: exact existing parent/new-name/action allowlist, complete priced
  scope, absolute UTC window/expiry, setup/rollback owners, capacity/route/name
  recheck and separately explicit setup-only authority.
- P5 readback: assigned resource/environment/principal IDs, effective protections/
  exclusions, initialized state and independent watchdog readiness. These IDs
  cannot be invented before creation.
- P6 one dispatch, P7 actual-run authority and P8 protected qualification/cleanup:
  separately scoped decisions and evidence; no automatic retry or inherited
  rerun authority. The machine receipt can satisfy only part of consumer T002.

Independent human broker/assurance/approval and domain T003 onward remain gated.
Consumer lock/pins, all neutral APIs, workflow bytes and default refusal remain.
Feedback stays deferred; no blocked write is replayed. All observations are dated
readbacks, not ongoing monitoring or operational approval.
