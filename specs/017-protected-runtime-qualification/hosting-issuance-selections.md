# Hosting and issuance selection basis

Status: draft
Kind: planning
Authority: user commissioned proposal/plan using recommended T013 selections; source ratification, appointments, setup and dispatch remain separate

## Accepted source and observed non-secret facts

Adapter #66 was source-ratified at c8050f9eb1ffbcdbc7fdba66a032ca9649f25ae0 and
merged as 5498a9b27d7a61daf8f4088ce85906cb436a2033 with equal tree
e3664990f55b49bfb7629b864816900d6b429491. Accepted runtime source is unchanged
from #65. Current execution source must be selected again after later hosting
implementation; no floating main or operative accepted_commit is approved here.

Read-only recommendation research on 2026-11-14 verified the Opensoft QA tenant/
subscription/West US and existing GitHub repository access/configuration. The
resource group, VM names and service roles below are proposed, not created.
No credential, token, factor seed or raw provider response belongs in this packet.

| Category | Planning basis | Later mandatory selection/readback |
| --- | --- | --- |
| Tenant/subscription | Tenant 74ce1e7d-7455-4694-b00d-9ac83c6821ce; sub-opensoft-platform-aks-qa, ID 297b2389-33bf-48c8-8deb-0b92838431e4 | Explicit scope approval and actual parent/permission/current readback before setup; no production subscription use |
| Region/parents | West US; proposed new rg-opensoft-wallet-mfa-qa and vnet-wallet-mfa-qa-01 | Actual name availability, CIDR/DNS/CA/routing and immutable assigned IDs; no shared AKS/bench/peering change |
| Hosts | Proposed vm-wallet-mfa-control-qa-01, vm-wallet-mfa-gate-qa-01, vm-wallet-mfa-worker-qa-01; Ubuntu 24.04 LTS | Exact nonburstable SKU/image/source/dependency/executable IDs/hashes, capacity, roles and actual isolation/measurement; no mutable latest image |
| Host/resource limits | At most three proposed 2-vCPU/8-GiB hosts; resource envelope at most 24 hours; proposed total US$50 ceiling | Full priced resource allowlist including network/storage/vault/watchdog/evidence; external expiry/retirement capability; no cost quote or automatic cap claimed |
| Case/window | case:codexfactory-possession-qa-001; one machine possession qualification, one dispatch and run attempt 1; proposed 30-minute case | Actual UTC start/end/expiry, accountable owner, full source/target/grant and exact generation scope; no domain action or human-factor simulation |
| Initiating dispatcher | Proposed brettheap, User ID 1513478 | Explicit appointment and actual originating-human authentication; no App actor substitution |
| Reviewer | Proposed scottdriscoll, User ID 1554882; alternate NikitaFlimakov, User ID 5066327 | Appointment/availability/current eligibility and independent review; nobody was contacted or assigned |
| Environment | Proposed wallet-mfa-pilot-qa in opensoft/openXwallet (repository ID 1347887821; owner ID 638385) | Actual new environment ID and exact reviewer/self-review/admin-bypass/main-branch protections after separately authorized setup; existing copilot is preserved/ineligible |
| Workflow | Existing caller ID 417795073 and local reusable ID 417795071; both observed with zero runs | Final accepted same-commit graph/source, current provider run/phase/review and new v2 source acceptance; three inputs unchanged |
| Main-update policy | coordinated | Named hold/control owner, exact accepted main/window/control and independent current supporting readback; no freeze/rule/tag applied and no atomic-prevention claim |
| Broker/reader | Separate repository-only Actions-write broker and Actions-read provider reader Apps; Contents-read only for required source reads | App/install/key/version/permission/retirement refs and effective scope; runtime gets no Contents-write/admin; root/MI limits must be qualified |
| Issuer/credential store | Proposed dedicated pilot Key Vault/issuer and per-role private credential broker | Actual name/key/issuer/principal refs, authenticated enrollment, OS peer/IMDS denial, private transport and retirement; no existing broad credential or fixture key reused |
| Wallet custody | Accepted owning Ed25519 software custody on trusted owning-service host | Actual key/credential/deployment/issuance refs and valid-preimage worker denial; no native Key Vault Ed25519/HSM claim |
| State | Explicit private POSIX retained dispatch/authority/replay/staging/finalization stores | Actual parent/device/inode/init receipt/recovery/retention refs; managed disk naming alone proves no continuity; no active-scope backup restore |
| Cleanup/evidence | Independent control-host janitor plus required external watchdog/audit for control-loss/automatic expiry; proposed 30-day redacted evidence retention | Actual external failure domain/principal/service refs, exact-generation ownership, conditional retirement capability and fresh absence/revocation/preservation readback |

## Proposed purpose and phase policy

Retain bootstrap audience `urn:opensoft:openxfactory:bootstrap-admission:v1`.
Propose proof audience `urn:opensoft:codexfactory:wallet-possession:qa:v1`, distinct
from bootstrap and accepted only with existing protected proof checks.

Expected-subject candidates, derived from independently read provider settings
and documented syntax, not observed by minting a token:

```text
Preflight: repo:opensoft@638385/openXwallet@1347887821:ref:refs/heads/main
Protected: repo:opensoft@638385/openXwallet@1347887821:environment:wallet-mfa-pilot-qa
```

Actual complete claims, request endpoint, server CA, relying-party policy and
worker exclusion still need independently approved selections and later authorized
corroboration. No bootstrap trust into Azure/signing is created. Job id-token
permission can request other audiences; current owned relying parties need review.

## Staged authority remains ungranted

Source preparation uses these as design inputs only. A later owner must separately
accept/commission the material v2 and hosting source; then accept actual T013 values
and source readiness; then authorize scoped setup, one dispatch, actual-run use and
exact cleanup. No executable runtime JSON, static digest, preauthorization, grant,
resource/deployment command or provider credential is produced. T001/T013/T014/T015
remain unchecked. Feedback stays deferred; neither historical blocked write is replayed.
