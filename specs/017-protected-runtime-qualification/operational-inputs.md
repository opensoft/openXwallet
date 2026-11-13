# T013 Operational Selection Packet

Status: prepared; operational selections incomplete; no setup/dispatch authority
Prepared: 2026-11-13
Governance: `opensoft/openXfactory`, `prepare-protected-runtime-qualification`
Implementation list: [feature 017 tasks](tasks.md); T013 remains an owner act
Decision draft: [scoped authorization](scoped-authorization.md)
Source prerequisite: [dispatch bootstrap proposal](workflow-bootstrap.md)

## Verified source and repository facts

Brett ratified [#59](https://github.com/opensoft/openXwallet/pull/59) at
`948ea81d7cdce35f5d006c747680a6b9fde37a29` for source acceptance only. All
runnable checks passed at that head, it was clean/mergeable, and no unresolved
review thread remained. It merged normally on 2026-11-13 at 22:10:25 UTC as
`9e1d75d46dfd6f170e27cbe7701f34288428ee6f`, tree
`43ac0bd082850da53c54d392c44de069aeeab0b2`, identical to the ratified tree.
No administrative bypass was used. No Actions run was returned for the merge
commit at preparation time; PR checks are not described as post-merge CI.

Read-only GitHub API inspection on 2026-11-13 established:

| Fact | Observed value | Meaning |
| --- | --- | --- |
| Qualification repository | `opensoft/openXwallet`, public, default branch `main` | Current T012 source hardcodes this repository; it is not a codeXfactory workflow |
| Repository ID | `1347887821` | Immutable launch identity candidate; requires fresh operational readback |
| Owner ID | `638385` (`opensoft`) | Immutable owner identity candidate |
| Current authenticated account | `brettheap`, user ID `1513478` | Readback only; does not select dispatcher or reviewer |
| Existing environments | Only `copilot`, ID `20677426348` | No eligible protected environment is currently selected |
| Existing `copilot` protection | Empty protection rules; admin bypass enabled; no deployment branch policy | Ineligible under the accepted profile; preserve it |
| Default workflow token permissions | `read`; PR review approval disabled | Repository default only; job-specific permissions still require readback |

The accepted caller is `.github/workflows/protected-runtime-qualification.yml`;
the local reusable is
`.github/workflows/protected-runtime-qualification-run.yml`, both at the same
immutable source commit. At the merge their respective file digests are:

- Caller: `sha256:a307585baaefa5430e4253663b547d0c73fb4b1d516d8808415db9e3d3daa713`.
- Reusable: `sha256:6d0473d9cedd1768174b30887affc13346af84a542c688570109b439951ea579`.
- CLI `scripts/prepare-protected-runtime.py`: `sha256:a822458b97b7a8df144be1c94f6b638c654b969b345776a6dc7dc17d87fd434c`.

The adapter's neutral pin remains assembly
`b0af7c2ce53d63786a08a20aa3602a6f90345606`, code
`72313daab1f229c049cb90998931564c1904dbbc`. The separately selected portable
registry/custody integration source is owning code
`bb0e9dae89a771b05f6c235d0a77237288b95c85`; it does not replace that pin.
These are source facts, not a completed deployment manifest. Final source roles,
relative paths and content digests must include the separately reviewed hosting
and bootstrap integrations; do not freeze the merge as their future source.

## Proposed operational shape and missing selections

Retain Brett's prior selection of portable reference services, qualified in
isolation. Propose a dedicated disposable **nonproduction** pilot deployment,
with GitHub-hosted orchestration and independently administered Linux runtime
components. The provider, deployment target, credential issuance and administrative
boundaries are unselected. Do not infer Azure, an AKS cluster, an existing bench,
a production namespace or permission to deploy from the architecture proposal.

| Category | Prepared proposal / accepted constraint | Still required for operational completion |
| --- | --- | --- |
| Scope | Machine possession prerequisite for codeXfactory feature 058 T002 | Exact case ID and operational owner; consumer acceptance remains separate |
| Profile and dependencies | Factory-owned `openxfactory-protected-runtime-internal-v1`; fixed reviewed dependency lock | Accepted immutable factory profile, adapter, wallet contracts/code, worker, supervisor, caller and reusable source manifest; dependency/composition digests |
| Environment | Proposed new `wallet-mfa-pilot-qa`; exact `refs/heads/main` deployment restriction | Owner selection of name, authorized setup, actual environment ID and full effective protection readback |
| Review/dispatch | 1–6 distinct User/Team reviewer IDs; prevent self-review; admin bypass disabled | Independent eligible reviewer and dispatcher identities, memberships and effective permissions; Brett cannot approve his own initiated run under this profile |
| Workflow | Manual caller/local reusable at the same accepted commit; no PR/fork execution | Reviewed bootstrap amendment and final exact workflow/source claims; reconcile any later `main` movement |
| Issuer | `https://token.actions.githubusercontent.com`; discovery `/.well-known/openid-configuration`; JWKS `/.well-known/jwks` on that origin | Explicit audience and configured subject/claim policy; authenticated current issuer/protection/source measurements |
| Subject proposal | Environment-bound subject for the selected qualification repo/environment | Verify the actual GitHub subject customization and exact emitted claims; do not assume a default subject or mint a token for discovery |
| Host and measurement | Disposable nonproduction Linux runtime; immutable accepted launch sources | Exact provider/account/tenant/host or cluster/namespace identities, image/source measurement, bounded channel and OS/network confinement policies |
| Supervisor | Independent administration; worker cannot read keys/policy or modify observations/source | Named administrator/principal/key/policy refs and actual worker denial; same-user fixture results are insufficient |
| Gate and custody | Only the confined approved gate holds narrow owning signer access; one bounded proof | Exact deployed gate identity, credential issuance policy and trusted custody principal; valid direct worker signing denial |
| Current records/challenge/registry | Portable owning APIs; trusted authenticated loaders | Non-secret service/principal/credential refs and trust digests for each actual service; current authority/policy/challenge readback |
| State | Private explicitly initialized replay store; no silent startup reset | Store/initialization/retention/recovery references, receipt, access-denial readback and active-scope recovery policy |
| Lifecycle | Run-scoped lease plus independent scheduler/janitor/readback | Registered plan, generation/ownership allowlist, lease/cleanup/receipt-retention refs, deadlines and separate administrative identities |
| Operation | Setup, bootstrap dispatch and actual run/attempt authority are separate | Approved resource allowlist, budget/window, actor/grant refs and final canonical config digest after actual run identity is known |
| Evidence | Redacted exact-source/case/readback/cleanup receipts | Reviewed protected-machine receipt promotion and actual P01/deployed G02/G03/L01 qualification; T011 currently supports source/fixture scope only |

Every service role (`records`, `challenge`, `registry`, `custody`, `supervisor`,
`worker_channel`, `janitor`) needs a service reference, principal reference,
credential reference and trust digest. Environment, authorization, scheduler and
cleanup readback clients also need independently authenticated identities. Merely
assigning different identifier strings does not prove administrative separation.
No service reference is an executable resolver or worker-selected URL.

## Blocking source prerequisite and decision order

The accepted #59 dispatch digest includes the not-yet-known run ID/attempt.
[The bootstrap amendment](workflow-bootstrap.md) records the verified circularity
and its isolated source candidate under factory PR #1311. The candidate migrates
to a distinct static selection plus independently bound actual-run full digest;
paired exact-head source acceptance remains pending. Operational bindings still
refuse `workflow-operational-host-unselected`; qualify/cleanup clients and
protected-machine receipt support are not supplied by #59. Filling selection
rows cannot make this workflow executable.

Select the actual nonproduction host, responsible administrators and distinct
dispatcher/reviewer roles. Review/accept the paired bootstrap source candidates;
actual hosting/authentication clients still require separate source integration
and acceptance before operational setup authority. Then complete
the [staged authorization record](scoped-authorization.md), obtain setup readback,
and obtain a separate bounded dispatch/run decision. No task is duplicated here;
feature 017 remains the sole implementation list.

No executable runtime JSON, grant, environment or provider resource is created by
this packet. Missing selections remain explicit rather than invented handles,
pending values inside runtime input, self-approval flags or fixture fallbacks.
T013, T014 and T015 remain unchecked. Human broker enrollment/assurance and domain
approval remain separate. Feedback stays deferred; neither historical blocked
write was replayed.
