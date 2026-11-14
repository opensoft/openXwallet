# Hosting and issuance research decisions

Status: draft
Kind: research
Scope: Phase 0 source planning; no implementation or operation

## R1 — Temporal finalization is a source prerequisite

Decision: propose static-v2 plus plan-only preflight and protected staging/finalization.
`bootstrap.py` projects only run_id/attempt out of the current config; `launch.py`
worker_configuration includes launch claims, and ProcessLaunch composition includes
actual PID/start/argv/cwd. The policy includes composition digest, and full config
then binds state/custody/operation/scheduler/cleanup. Existing supervisor fixtures
launch first and recompute policy/config afterward; they do not prove a real
predispatch commitment. Worker projection excludes self-referential hashes, so
derive composition -> policy -> full configuration after actual launch.

Alternatives rejected: predict IDs/PID, use dummy hashes, omit whole trust objects,
mutate static-v1 or start the worker in read-only preflight. Use the exact four late
paths and deterministic plan-to-final comparison in the new source profile instead.
Accepted old isolated evidence and v1 remain scoped and unchanged.

## R2 — Narrow staging ownership before effects

Decision: actual environment review precedes a separate staging launch grant;
acknowledged durable janitor registration precedes start. Bind plan/case/run/source,
host incarnation and a preallocated nonreusable unit/cgroup ref, then observe actual
invocation/PID/start/boot/source. Ambiguity stays consumed, never creates another
generation. Create a linked immutable final full-config-bound plan with independent
takeover acknowledgement; retain staging cleanup until that acknowledgement.
No placeholder full-config digest or implicit lease extension is acceptable.

## R3 — VM identity does not isolate service processes

Decision: worker host has no managed identity; privileged kernel-authenticated local
credential brokering and actual OS restrictions are required on trusted hosts.
Microsoft documents VM-wide managed-identity access. Separate UAMIs/client IDs or
service names are not process boundaries. Guest agent/source and host roots remain
an explicit trusted administration boundary; actual provider metadata alone proves
no key-file, IMDS, capability, mount or process-access denial.
Sources: [VM token boundary](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-to-use-vm-token),
[managed-identity boundary](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/managed-identities-faq).

## R4 — Key Vault scope and enrollment

Decision: propose exact-version RSA signing of App JWTs through the selected Key Vault
key, verify signature/public-key binding and exact installation/repository/permissions/
expiry, keep tokens private and separately retire them. This is a proposed compatible
API composition, not a qualified integration. A GitHub App private key may need
controlled generation/import during later authorized setup; runtime issuer has no
import/admin permission. Installation tokens can last one hour, beyond a 30-minute
case; local authority restriction alone is not provider revocation.

The owning service at accepted code bb0e9dae89a771b05f6c235d0a77237288b95c85 requires
Ed25519 PEM. Key Vault Keys documents RSA/EC, not native Ed25519. Wallet custody
therefore remains trusted-host software custody; secret storage/delivery is not
an HSM or non-exportability claim. Stronger custody goes upstream.
Sources: [Key Vault key algorithms](https://learn.microsoft.com/en-us/azure/key-vault/keys/about-keys-details),
[App JWT](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app),
[installation tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app),
[key import](https://learn.microsoft.com/en-us/rest/api/keyvault/keys/import-key/import-key?view=rest-keyvault-keys-2025-07-01),
[digest signing](https://learn.microsoft.com/en-us/rest/api/keyvault/keys/sign/sign?view=rest-keyvault-keys-2025-07-01).

## R5 — Current provider facts, not asserted readback

Decision: fixed authenticated GitHub source/run/review/environment/branch-policy
reads; Azure ARM identity/image/disk/network facts; authenticated guest agent for
actual OS/process/artifact facts; selected issuer and independent initialization/
scheduler/audit sources. Every observation gets provenance, principal, target,
time/expiry and scoped digest; do not echo the candidate.

Actual retained environment response contains can_admins_bypass, while official
schema omits it. Use a strictly required typed observed extension and qualify future
false behavior in separately authorized setup; missing/unsupported values refuse.
Do not assume a GraphQL fallback or synthesize false. Prove branch type before
projecting main to refs/heads/main; reject tags/wildcards/additional permissive rules.
Sources: [environment API](https://docs.github.com/en/rest/deployments/environments?apiVersion=2026-03-10),
[branch-policy API](https://docs.github.com/en/rest/deployments/branch-policies?apiVersion=2026-03-10).

## R6 — Reachability, source hold and failure domain

Decision: propose admission-only public-CA HTTPS ingress to the control boundary
for existing GitHub-hosted orchestration, with private issuer/dispatch/guest routes.
A private VNet alone supplies no runner reachability. Keep bootstrap-purpose identity
out of Azure federation/signing trusts and worker reach. Complete expected subjects
are proposed policy, not live token observations.

Choose the recommended coordinated source-update policy as planning basis. Hold
owner/window/source/control readback must be actual; ref/ruleset reads cannot prove
future administrator behavior or atomic pinning. Stronger guarantee goes upstream.
Control-host janitor covers worker/gate/runner failure, not total control loss.
An independent external watchdog is a deployment gate before claiming that cleanup
or automatic infrastructure expiry; unsupported retirement stays incomplete.
Sources: [OIDC claims and permissions](https://docs.github.com/en/actions/reference/security/oidc),
[ruleset API](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10).

## R7 — Operational unknowns are explicit future gates

Actual SKU/image/capacity/price, DNS/CA/network allocation, appointed people,
App/key/issuer/host/store IDs, watchdog service, conditional retirement support
and UTC windows remain unassigned. The earlier read-only SKU query timed out;
there is no reservation or cost quote. US$50/24h/three-host limits are proposed
bounds, not hard-stop evidence. Azure budgets notify without stopping consumption.
Source: [budget behavior](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets).

These values require later accepted non-secret references and independent readback.
No technical default, alternate identity, broader scope or fixture material fills
them. The plan resolves design approach while refusing unsupported deployment facts.
