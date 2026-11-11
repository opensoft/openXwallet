# Research and decisions

## Ownership

Read current openXwallet AGENTS.md, openxFactory AGENTS.md/constitution and
credential, identity-brokering and trust-anchor contracts. A delegated read-only
check confirmed: factory compositions belong to openxFactory; executable adapter
and test-only services belong to openXwallet. The existing factory-binding
capability covers the validator split, not this runtime, so it needs a proposal.
Keep the draft profile under supporting-docs, not published contracts. Exactly
one executable task list lives here. openxFactory gets no socket/keyholding code.

## Workload authentication

GitHub's [OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)
and [reusable workflow guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows)
distinguish caller workflow/source from reusable workflow ref/SHA. Bind both,
immutable repository/owner IDs, environment/subject and exact run/attempt. This
candidate requires reusable-workflow claims. Operator key snapshots must be
fresh. Synthetic fixture keys cannot qualify GitHub issuance/environment gates.

## Reuse and scope

The accepted neutral source exposes create_proof/verify_proof, current registry
bindings and mutual-TLS RemoteSigner. Inject those explicitly; do not vendor the
primitive or advance the adapter's existing neutral pin. Source qualification
records exact accepted checkout identity. PR #13's usage-control scope remains
independent. No new core wallet/grant vocabulary is needed.

## Alternatives

Reject worker-carried grants, unsigned observations, memory-only replay caches
and token-selected JWKS URLs. The observer reads trusted fixture artifacts
itself. Hostile OS isolation, live issuer qualification, human approval, pilot
activation, pin advancement and releases remain later owner gates.
