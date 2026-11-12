# Research and Proposed Decisions

Status: draft; proposed for owner acceptance

## R1 — Preserve the accepted verification core

Decision: adapt `WorkloadVerifier.verify(token, expected, *, now)` without changing
its crypto/claim rules or administrative deadline. The runtime fetch layer supplies
the existing trusted public-key snapshot shape. The offline verifier stays network-free.
Replacing JWT validation or library defaults would widen accepted behavior and is excluded.

## R2 — Application-owned issuer trust

Decision: fixed GitHub issuer/discovery/JWKS locations from the factory design,
verified TLS, no redirects or token-selected key URLs, bounded data/key counts and
5/10-second fetch deadlines. Proposed in-memory snapshots last at most 300 seconds,
shortened by applicable HTTP freshness/Age. Respect no-store/no-cache. Permit one
coalesced unknown-kid refresh/retry with a 30-second initiation limit; otherwise refuse.
No removed-key union, persistent cache, stale-on-error or unapproved ambient
proxy/CA configuration. These budgets are proposed policy, not GitHub guarantees.
Generic discovery and permissive caches were rejected because they expand trust.

## R3 — Exact configured launch

Decision: match immutable owner/repository IDs and caller, reusable workflow,
environment, subject, source and run/attempt claims against trusted selected values.
Independently read environment protection. Do not infer subject syntax from names
or creation dates, normalize claim casing, or use unverified tokens as expected values.
Repository-name compatibility in browser-origin checks is a different boundary.

## R4 — Confined gate and separate supervisor

Decision: the trusted gate alone receives its approved deployment's narrow custody
credential and enforces per-use workload/challenge/authority checks. A separately
administered supervisor measures the actual selected launch and signs existing
observations. Worker control-plane/key access must be denied. Same-user processes,
containers or an mTLS peer/subject allowlist do not establish this deployment binding.
The trusted host/admin remain in the TCB; no hostile-host/model-behavior claim is made.
A need for new custody-side per-use assertions first requires the neutral owner's
API decision, not an adapter protocol fork.

## R5 — Preserve the state guarantee

Decision: require the expected initialized private store at runtime startup and
retain consumed-on-failure behavior. Missing state is never silently recreated.
Retention/recovery/cleanup are outside worker control. Active-scope backup restore
is prohibited; SQLite integrity alone does not establish hostile rollback resistance.

## R6 — Separate acceptance acts

Decision: default conformance remains offline. Owner source commissioning, isolated
fixtures, operational service/protection selection, protected setup/dispatch and
human/domain acceptance remain separate. No executable consumer lock is generated.

## Primary Sources

- [GitHub discovery](https://token.actions.githubusercontent.com/.well-known/openid-configuration): current issuer/JWKS metadata.
- [GitHub OIDC claims](https://docs.github.com/en/actions/reference/security/oidc#oidc-token-claims): documented job claims; configured subject still needs readback.
- [Reusable workflows](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows#how-the-token-works-with-reusable-workflows): caller and called-workflow context.
- [Deployment protection](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#deployment-protection-rules): independently configured restrictions.
- [Self-hosted runner security](https://docs.github.com/en/actions/reference/security/secure-use#hardening-for-self-hosted-runners): shared host/Docker privileges can defeat separation.
- [OIDC Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfigValidation): issuer consistency and TLS validation.
- [OIDC Core rotation](https://openid.net/specs/openid-connect-core-1_0.html#RotateSigKeys): refreshing unfamiliar keys; no rotation schedule is assumed.
- [JWT BCP](https://datatracker.ietf.org/doc/html/rfc8725#section-3.10): application-controlled trust and unsafe key-location inputs.

Local baseline: feature 016 and factory `add-workload-factory-binding/supporting-docs/profile.md`.
Research supplies no live issuer, protection, custody, supervisor or human acceptance.
