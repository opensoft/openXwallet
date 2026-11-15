# Proposed internal hosting and finalization interfaces

Status: draft
Kind: internal-contract-design
Owner: factory change add-protected-runtime-hosting-issuance; implementation feature 017
Scope: proposed source interfaces only, not a published neutral contract or executable config

## Compatibility and construction

Preserve neutral proof/registry/custody APIs, runtime-v1 full validation, static-v1,
existing source/fixture reports and the default unselected CLI. New v2 types/routes
are explicitly source-selected trusted construction, not worker-selectable plugins
or activation flags. Exactly three dispatch inputs, seven runtime service roles
and eight immutable source roles remain. New callbacks are hosting capabilities,
not new runtime role strings. No implementation is commissioned by this document.

## Static v2 plan

Proposed closed top-level fields: profile, configuration_template, policy_template,
measurement_plan, derivation_rules, staging_policy, hosting_selection_digest,
source_hold_ref. Profile is openxfactory-dispatch-selection-internal-v2; nested
records have exact versioned fields and canonical bounded serialization.

configuration_template is the complete existing runtime-v1 shape except exactly
launch.run_id, launch.run_attempt, composition_digest and authority.policy_digest.
They are absent, never null/sentinel values. All other nested fields and explicit
scope/window/source/handle values stay committed. policy_template is the complete
approved policy except its measured composition digest. measurement_plan fixes exact
artifact/executable/source hashes and allowed root-relative install/config/argv/cwd/
UID/capability policy. derivation_rules names one fixed code-reviewed canonical
algorithm, never dynamic expressions. staging_policy commits one launch/ref/host/
cleanup template, bounds, registration/takeover and no-retry behavior.

The hosted plan validator must not call a full runtime validator with fake values.
After actual run and process observation, deterministic finalization reconstructs
and compares every complete configuration/policy byte, then calls unchanged full
validation. Host allocation outside this exact late-field boundary needs another
explicit versioned decision; arbitrary object omission is not supported.

## Proposed phase and ownership records

All returned records bind actual authenticated source principal, purpose/profile,
case, plan/selection digest, accepted source and actual first run/attempt, observed
and expiry times, and a closed status. Identity is established by selected authenticated
channels and factual sources, not the presence of principal strings.

| Record / capability | Additional required fields or scope | Effect |
| --- | --- | --- |
| PlanAdmission | Current hold/protection/scheduler-capability digest, approved existing environment ID/name | Read-only environment readiness; no full config, operation grant, start or proof capability |
| StageLaunchGrant | Issuer/decision ref, actual host resource/incarnation, immutable template, preallocated launch ref, action/window and distinct original human/App review context | At most one inert launch; never signing authority |
| StagingLease | Fixed stage scope, janitor/scheduler principals and registration acknowledgement, expiry, immutable manager slot/generation policy | Durable independent cleanup responsibility before start; no final-config placeholder |
| StageStatus | Same ref/scope plus registered/starting/measured/indeterminate/refused state and actual generation when available | Read/reconciliation only; no resubmission or second launch |
| FinalizationBinding | Actual run/host/manager generation/PID/start/boot/source, measured composition, complete policy/full config digests and independent authority decision | One immutable accepted actual binding after canonical recomputation; no arbitrary hash signing |
| FinalRunPlan takeover | Existing full config digest, exact same generation/ownership scope, stage link and independent final registration/takeover acknowledgement | Transfers cleanup only after durable acknowledgement; no gap or extension |
| Enrollment/issuance readback | Actual host/source/key fingerprint/nonce/UID/role, issuer/key version, effective returned scope/expiry and retirement record | Current narrow authenticated service capability; no raw material in evidence |
| ProtectedReportV1 | Closed actual qualification/result/source/case/run/independent-cleanup projection | Protected factual report only after later live qualification; no neutral/human/domain receipt claim |

Endpoint phase is intrinsic. Wrong profile/type/phase, duplicate/unknown fields,
wrong source/attempt/subject, expired or missing scope/provenance refuses. Tokens,
request credentials, PEM, private fingerprints/configuration and raw provider
responses never appear in public readiness/status/report envelopes. Safe fingerprints
and digests are used only where the closed redacted projection permits them.

## Concrete readback / operation ports

| Port | Trusted selected transport and actual evidence | Minimum boundary |
| --- | --- | --- |
| Operator approval/static plan | Authenticated authoritative decision store, immutable record digest/revision, current status/window/revocation and original human | Never approve request-body content or use a worker service credential |
| GitHub source/run/review/protection | Fixed API origin and selected repo/ref/blob/run/job/review/environment/branch-policy endpoints; version-specific strict projection | Actions-read; Contents-read only for source APIs; no write/admin scope; fixed URLs, User-Agent and no returned-URL navigation |
| Coordinated source hold | Authenticated accountable hold record plus current actual main/control facts | Refuse absent/expired control; no provider atomic execution claim from a signed label or ruleset snapshot |
| Azure deployment | Fixed selected ARM provider/resource IDs and API versions, actual VMid/image/disks/NIC/identity/network state | Least read scope; never provider RunCommand/setup as a readback shortcut |
| Guest measurement | Selected mTLS host agent, actual kernel/process/files/UID/capability/key-file/IMDS/network facts under trusted host root | Worker cannot invoke control/observation/signing paths; manager identity plus generation, not PID/name alone |
| Credential issuer | Authenticated current provider/bootstrap enrollment and selected role/key/version, kernel-authenticated caller, actual returned permissions/expiry/revocation | Worker has no MI; direct IMDS and privileged resolver access are measured denials; no host-identity-as-process-isolation claim |
| Key Vault / App exchange | Exact versioned RSA key and public identity, RS256 verification, fixed GitHub installation endpoint, requested and returned repo/permission/expiry match | Issuer sign only, setup import/admin separate; no raw App/key/token export into worker/evidence; actual retirement required |
| Initialization/recovery | Independent retained init receipt and actual private store device/inode/schema/retention/recovery current scope | No create-on-open/reset or active-scope backup rollback claim |
| Stage/final scheduler/janitor | Durable registration plus authenticated acknowledged current scope/generation/lease, actual cleanup and separate audit | Ack before start; stage retained until final takeover; external watchdog required for control-host-loss/automatic infrastructure expiry |

Protection requires explicit typed can_admins_bypass false, prevent_self_review true,
exact eligible reviewers and branch-only main policy. The observed bypass field is
an adapter-specific extension omitted from current official schema; absence/wrong
type is unsupported, never default false. Branch/tag type and all policy pages must
be proven; no normalization of tags/wildcards or ignored permissive entries.

## Bounds, retries and private channels

Retain existing transport/connect/data/key/field bounds: at most 10 seconds per
RPC under the enclosing deadline, five-second connect, up to 1 MiB API response,
64 KiB internal record and 16 KiB full configuration. The existing run/job/review
ProviderReader alone retains four requests/two job pages per correlation decision.
New v2 protection callbacks get at most three reads (environment plus two policy
pages, maximum 32 entries); source/graph gets four (main, caller/reusable blobs,
final main); hold/control gets two (maximum 32 rules, one selected control set).
Aggregate maximum: 13 GitHub reads per decision. All counters share the SAME
enclosing wall/monotonic deadline; no client resets the correlation budget or
uses stale/omitted protection to make a positive path fit. Unsupported pagination
or control complexity refuses. Other provider/issuer/guest operations have fixed
per-operation bounds under the parent and no hidden retry. The proposed staging phase uses
at most six read-only status decisions within 60 seconds and the earlier case/
grant/lease deadline. Each decision reauthenticates current facts; no success
extends the parent. No mutation/dispatched launch is automatically retried.

Lost registration/start/finalization/retirement responses stay indeterminate with
retained ownership/scope. Resolve only the same preallocated nonreusable reference
and observed generation. No replacement generation, newest-run search, broad
resource-group delete or hidden provider/HTTP retry is supported.

Public-CA HTTPS admission ingress is proposed solely for existing GitHub-hosted
orchestration. Private mTLS broker/issuer/guest routes and local kernel-authenticated
credential channels carry capabilities. A private VNet is not runner connectivity.
Actual DNS/CA/provider identities and enrollment are later approved setup inputs.
