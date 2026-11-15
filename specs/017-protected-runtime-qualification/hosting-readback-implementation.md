# T012Q isolated current readback adapters

Status: isolated source candidate complete; source acceptance and live gates separate
Date: 2026-11-15 (America/La_Paz)

Brett source-ratified #69 at b73a7d06695e and commissioned only T012Q in
isolation. #69 landed normally as 7bd884106eea5f0ed4b99a35da70d613ccbfd0d2
with the accepted tree unchanged. Factory
`add-protected-runtime-hosting-issuance` governs this slice. Feature017
`tasks.md` remains the sole executable list; factory tasks are handoff-only.
This candidate has no source acceptance, publication or operational grant.

## Implemented boundary

- `hosted/readback.py` supplies immutable canonical snapshots, one enclosing
  Decision and shared counters, an existing-selected-credential GET client,
  and pinned mTLS observation clients. The private request contains only a
  fixed operation/reference and fresh nonce; it sends no candidate facts.
- `hosted/github_readback.py` obtains current main and immutable workflow bytes,
  verifies Git blob identity, requires explicit typed environment protection
  and branch-only main policy, and observes the selected current update-control
  ruleset and separately owned hold. It composes these with the unchanged
  four-read GitHub correlation engine. It does not convert a v2 plan into v1.
- `hosted/platform_readback.py` observes the selected VM/incarnation, immutable
  image, attached managed disks, identity, NIC/subnet/NSG and optional selected
  public IP through ARM GETs. Approved complete model/storage/network digests
  must agree with independently returned linked resource facts.
- Exact-version Key Vault public metadata must yield the selected RSA public
  fingerprint, enabled validity window and sign/verify operations. Separately
  pinned private observations must corroborate current issuer role, repository,
  enrollment, permissions, credential digest and expiry. No sign/mint occurs.
- Guest observations bind current process generation/UID/capabilities, source,
  policy and artifact measurements and explicit denial/positive controls.
  State observations require independently administered initialization/current
  endpoints with different principals, origins and server certificate pins,
  matching existing store identity, schema, integrity and no-restore status.
  Initialization is re-observed after current state; missing state is not made.
- `PlanFactReader` and explicit opt-in `DecisionRead` let v2 preflight consume
  the selected authenticated source under its original parent Decision. No
  default CLI, workflow activation, listener or setup operation is added.

Private transport checks the actual server certificate pin before sending
application data, retains selected CA/client material checks, follows no
redirect, and reaps the private helper on success, refusal and cancellation.
Provider operations use fixed hosts, paths and API versions. Returned provider
URLs are never followed. Observation failures expose fixed safe errors.

## Bounds and freshness

Existing correlation retains four reads and at most two job pages. Protection,
source and hold/control allow three/four/two reads, respectively, with at most
13 aggregate GitHub reads. The counter lives on the same parent Decision across
new clients and callbacks; correlation high-water cannot regress. ARM/key/private
observations have 24/3/12 operation limits. There is no retry or counter reset.

Credential acquisition, TLS readiness, decoding, crypto and final rechecks must
stay within the same wall/monotonic authority. Observation times must be current
and within 60 seconds; the earliest key, credential, hold or observation expiry
clips later work. Snapshots retain their original Decision and cannot renew its
monotonic lifetime. Public JSON is bounded to 1 MiB, private envelopes to 64 KiB,
workflow files to 64 KiB, and public RSA material is bounded before construction.

Missing admin-bypass, missing branch type, tag/wildcard/extra branch policies,
unsupported rule/provider pagination, changed source/hold/control, revoked issuer,
excess guest permission, outage or changed/lost initialized state refuses.
Repository identity in an environment projection is the selected request scope;
the independent run correlation corroborates the actual repository ID.

## Governed composition correction candidate

The baseline safely refused repeated protection reads at D7's three-read limit.
Factory PR [#1322](https://github.com/opensoft/openXfactory/pull/1322), change
`fix-hosted-protection-read-budget`, proposes a finalization-only allocation:
six current observations, eighteen protection and twenty-eight aggregate GitHub
reads. Ordinary admission/correlation remains three/thirteen. The independent
authority joins the caller's ledger; both original clocks, earliest expiry, all
group/snapshot counts and four total correlation reads remain binding. A seventh
observation and a fifth shared correlation request refuse before credential/I/O.
No budget upgrade, stale reuse, dropped check, retry or default activation occurs.

The [feature amendment](hosting-readback-budget-amendment.md) records the source
plan and authority. All 318 focused readback/finalization/allocation cases pass,
including six real mTLS observations, independent actual process/file measurement,
unchanged full admission, owning Ed25519 proof and replay refusal. Full/native
requalification, CI and local expert Codex review are publication gates in progress.
This is an unratified source candidate; T012R-V remain uncommissioned.

## Isolated verification and limits

The baseline 160-node readback corpus passes; the allocation correction adds
33 nodes without removing any baseline identity. Independently mutable authenticated fixture
facts are changed while the approved candidate remains fixed. Positives exercise
actual TLS/mTLS, server pins, RSA public-key construction, OS process/file
measurement, initialized SQLite inspection, kernel-authenticated credential ports,
and the unchanged owning Ed25519 proof with replay refusal.

GitHub, ARM and Key Vault responses come from selected loopback provider doubles.
Guest denial controls establish the fixture credential-port boundary; direct
IMDS/network/filesystem confinement on a deployed host remains unqualified. A
current typed private record alone does not establish an unqualified provider
or guest fact. No live service credential, setup, dispatch, hold change, resource
installation, token issuance or provider retirement is performed. Coordinated
holds do not guarantee atomic main pinning or malicious-administrator resistance.
The baseline before the allocation correction passed 2,043 full-suite tests and
1,741 mandatory native matrix nodes, with zero
failures/errors/skips. The native run uses UID 1000, no capabilities, no new
privileges, read-only source and loopback-only networking. H08/H09 anchor 78/32
nodes. All prior 1,581 matrix identities and anchors remain unchanged.

Cleanup independently checks 38 ownership process generations, 120 hosted
generations and 3439 credential/guest helper generations, plus
16 preservation records and 8 consumed journals. No matching
live generation or attributable helper remains. The disposable native namespace
is absent and all ten exact Q fixture roots are removed after the audit. Redacted
JUnit/log/audit/source-hash receipts remain outside those fixture roots. Final
documentation gates pass; 100 validator scratch roots and the task-local Node
cache are also removed. No scoped fixture/scratch directory remains; see evidence.md.

## Primary provider references

These document parser inputs and method shapes, not live qualification:

- [GitHub environments](https://docs.github.com/en/rest/deployments/environments?apiVersion=2026-03-10)
  and [branch policies](https://docs.github.com/en/rest/deployments/branch-policies?apiVersion=2026-03-10).
  `can_admins_bypass` is a required observed extension; its absence refuses even
  though the published environment response schema omits it. Branch `type` must
  explicitly be `branch`.
- [GitHub contents](https://docs.github.com/en/rest/repos/contents?apiVersion=2026-03-10)
  and [rulesets](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10).
- [ARM VM GET](https://learn.microsoft.com/en-us/rest/api/compute/virtual-machines/get?view=rest-compute-2025-04-01)
  with expanded instance view; image/disk/network queries use separately pinned
  per-resource API versions in `platform_readback.py`.
- [Key Vault key GET](https://learn.microsoft.com/en-us/rest/api/keyvault/keys/get-key/get-key?view=rest-keyvault-keys-2025-07-01)
  requires `keys/get`; the embedding must select a separate approved observation
  credential rather than widen the issuer's signing principal.

Setup/dispatch remain unauthorized, feedback deferred, and neither blocked write
nor the denied optional/private write is replayed. Pins, neutral contracts,
provider policy and default activation remain unchanged.
