# T013 Scoped Authorization Draft

Status: prepared for owner/operator decision; NOT GRANTED; not runtime input
Prepared: 2026-11-13
Selections: [operational inputs](operational-inputs.md)
Source prerequisite: [dispatch bootstrap proposal](workflow-bootstrap.md)

This draft records the scope of a future decision. Brett's ratification of #59
at `948ea81d7cdce35f5d006c747680a6b9fde37a29` accepts source only. It does not
approve this draft, select a host, create resources or authorize a dispatch.
The earlier portable reference-service decision remains the service route;
isolated qualification does not authorize deploying those services.

## Decision record and post-setup readback

Complete the following record with non-secret references. Before setup, select
the intended target, source, administrators, names, actions, limits and policies.
IDs/receipts that can only exist after authorized creation are post-setup
readback requirements; they block dispatch, not that narrowly enumerated setup.
Unselected scope blocks the corresponding decision. Copying this document or
saying "approved" cannot fill a missing selection or readback.

| Decision | Proposed bound | Required owner/operator selection |
| --- | --- | --- |
| Purpose | First codeXfactory pilot, machine possession qualification only | Exact case identifier and accountable operational owner |
| Source | Accepted immutable factory/adapter/owning service revisions and dependencies | Final reviewed source manifest and digest, including bootstrap/hosting integrations |
| Target | Dedicated disposable nonproduction Linux deployment of portable services | Provider/account or tenant/subscription, host/cluster, region, namespace/resource group and immutable target IDs |
| Administrative separation | Worker cannot administer supervisor, custody, grant, readback or cleanup | Named principals, administrative owners, trust roots and effective access readback |
| Environment | Proposed new `wallet-mfa-pilot-qa` in `opensoft/openXwallet` | Before setup: approved name, exact repository ID, eligible reviewer IDs, independent dispatcher and protection policy; after setup: actual created ID and measured protection |
| Setup budget | Smallest bounded pilot; no production or shared-resource mutation | Exact create/update allowlist, resource limits, spend ceiling, UTC start/end, expiration and teardown owner |
| State | Existing explicitly initialized private store; no silent reset | Provisioning owner, initialization receipt, storage identity, retention/recovery policy and preservation list |
| Services | Records, challenge, registry, custody, supervisor, worker channel and janitor | Exact service/principal/credential references and trust digests, plus authenticated readback clients |
| Issuer/workload | Fixed GitHub endpoints, exact repo/ref/workflow/source bindings | Audience, configured subject policy, claim readback and selected measurement policy |
| Lifecycle | Independently registered bounded lease and exact-generation cleanup | Janitor/scheduler/readback principals, registration, cleanup plan digest, deadlines and receipt retention |
| Approval | Separate setup, bootstrap dispatch and actual run authority | Decision identity, decision time/expiry, immutable decision reference and revocation path |

Credential references identify where authorized clients obtain credentials;
credentials, tokens, factor seeds and private keys never belong in this record.
No new App, grant, credential or permission is implicitly authorized by naming a
role. Provider setup commands must be separately reviewed against the completed
allowlist. This draft supplies no runnable setup/dispatch commands.

## Staged scope to authorize after source and selections are complete

1. **Setup only.** Authorize the named operator to create/configure only the
   enumerated nonproduction resources during the selected window/budget. For a
   new resource, bind its create action to exact parent identity and name, refuse
   an unexpected existing resource, then record the assigned immutable ID. Require
   authenticated readback of actual identities, protections, administrative
   separation, initialized state and registered cleanup. Setup authority grants
   neither a protected run nor signing use. Stop on drift, unknown resources or
   an inability to enforce the approved separation. Preserve the old `copilot`
   environment and other shared resources.
2. **One bootstrap dispatch.** After separately accepted bootstrap/hosting
   source exists, authorize one manual `main` dispatch at its exact accepted
   workflow commit, for the selected case, static selection digest and independent
   preauthorization reference. No pull-request/fork trigger, auto retry, floating
   source or second dispatch is covered. If `main` has moved, reconcile and obtain
   exact source acceptance before proceeding. The proposed bootstrap carries no
   signing authority and cannot select an environment or request OIDC before
   independent admission.
3. **Actual run/attempt authorization.** Once GitHub assigns the run identity,
   independently authenticate it and bind the final canonical runtime config,
   current grant, environment, sources and registered lease/cleanup to that exact
   run/attempt. Approve only `qualify-existing-resources`, one bounded owning
   proof, the accepted P01/G02/G03/L01 cases and scoped cancellation/cleanup
   exercises. Enumerate separate run/case authority if those exercises need more
   than one run. Each rerun/attempt requires fresh authority; none is inherited.
   Environment review and this operation grant remain distinct gates.
4. **Cleanup and evidence.** Authorize only the approved generation/ownership
   allowlist. The independent janitor must remain able to expire/reconcile and
   independently read back cleanup after runner death or proof expiry. Remove
   run-owned ephemeral credentials/resources only; preserve replay state, retained
   receipts and every explicitly shared resource. A new target, generation,
   namespace or deletion scope requires a new decision. Missing readback leaves
   the run unqualified and escalated to the named cleanup owner.

Stages 2–3 describe a proposed source amendment, not a capability of the current
workflow. Do not dispatch #59 to discover a run ID, edit immutable dispatch inputs,
predict an ID, reuse a prior grant or bypass the current admission guards.

## Exclusions and acceptance boundary

No production deployment, tenant-wide policy change, standing broad credential,
wildcard deletion, bench restart/rebuild, consumer lock/pin promotion, domain
read/apply/marker operation, human factor enrollment, human approval simulation or
release acceptance is covered. Feedback/support remains deferred. Neither
historical blocked write may be replayed under this scope.

T013 stays unchecked until every required operational category has an explicit
approved reference and independent readback, and setup/dispatch authority is
actually recorded. The draft does not require an uncreated resource's ID before
authorizing its exact scoped creation. T014 execution and protected receipt
promotion require their reviewed integrations and operational gates; T015 requires the separate consumer
acceptance. Environment approval alone supplies none of those acceptances.

The next decision can select a host and the distinct dispatcher/reviewer roles
while commissioning the source-only bootstrap amendment. It cannot yet be a
fully bound operational grant: target, clients, resource allowlist, independent
administration, budget/time window and actual run identity remain unselected.
