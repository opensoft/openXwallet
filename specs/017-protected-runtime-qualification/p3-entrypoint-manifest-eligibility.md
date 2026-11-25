# P08 original-registration manifest eligibility

Status: blocked source eligibility; no selected accounting or handoff implementation.
Date: 2026-11-25, America/La_Paz.

## Accepted source and commission

Brett ratified [factory1368](https://github.com/opensoft/openXfactory/pull/1368)
at01c574bd1f64 with [wallet106](https://github.com/opensoft/openXwallet/pull/106)
at5306efd72c98 for source acceptance only. Normal merges8833c7d001b3a and
12cdf3161c5d landed factory first, preserving both exact ratified trees without
administrative overrides. He then commissioned existing T013P08 in isolation,
starting with both eligibility gates. Independent main runs45539468581 and
45539488585 remain in progress at this checkpoint; PR checks do not substitute.

The accepted [accounting subplan](p3-entrypoint-accounting-plan.md) and factory
bound-remote-lifecycle-accounting require authenticated original registration
resources, original store identity and scope at the caller before selected
accounting/handoff I/O. The policy commitment remains
fd198b7d7e8e786b5d5f64257ec0e276e881ea5364b265cb9ccb519208f77fa7.

## Fresh evidence

Gate A passes all15 source-route positive/refusal controls with zero failures,
errors or skips. The actual protected/preflight admission service paths and all
six affected source consumers are included. The tested source is archived in the
owned ignored QA packet with frozen hashes; product runtime/test/workflow/matrix/
pin bytes are restored to accepted source after Gate B's precondition failed.
The first launch was refused before tests because its runner added an environment
key outside the isolation allowlist. That runner key was removed; the isolation
policy, capability drop and network boundary were unchanged. The initial launch
is diagnostic, not a passing test run.

Gate B cannot establish the original-manifest precondition. RemoteBindings and
PlanBindings have no original registration/resource/store capability. The exact
StagingReadback fields contain source/run/generation facts, not that manifest.
Lifecycle register/status/ack-stage replies expose registration_digest and fixed
status/acknowledgement fields; their closed grammars reject injected resources,
registration documents, counts or store-identity fields. Seven direct contract
shape controls pass. There is no demonstrated product constructor that supplies
the missing capability. This is a contract/input audit, not a connected Gate B
positive or a claim that an unimplemented product guard ran. No handoff RPC,
selected budget, new wire field or authority was used.

The original resources are retained at the lifecycle owner. HostedLifecycle.register
records the canonical registration and returns its digest; resources_for and
prepare_final consume/check it later. A test fixture's private life/store reference,
a supplied count, a future RunPlan or an extra unbudgeted lookup cannot supply
an authenticated original caller capability. The accepted fallback therefore
returns to governance before dependent handoff work.

A separate read-only auditor checked all36 fixture databases and155 file/link
hashes after the successful producer exited. It verified frozen source and made
no store repairs. Its recorded reservation/staging states are not asserted as
final lifecycle retirement. All151 audited temporary fixture entries and the
three owned test/audit containers were removed without force; original benches
were not restarted or reconfigured. This proves closure of these private source
fixtures, not live/P08 runtime cleanup qualification.

## Governed next step

Prepare an explicit original-registration descriptor and retention contract,
with its paired plan, before implementing a new wire or record grammar. The
[design working draft](p3-entrypoint-registration-design-draft.md) compares carrying
the descriptor from existing staging exchanges with an explicitly budgeted new
read. Neither is source-ratified or implemented here. The proposed source design uses existing staging/retention; it remains unratified.

The sole executable list remains [tasks.md](tasks.md), unchecked T013P08. P09,
T001/T013/T014/T015, roles and live/human/consumer acceptance remain separate.
Setup/dispatch unauthorized; feedback deferred; blocked writes unreplayed.
See the [machine-readable record](p3-entrypoint-manifest-eligibility.json).
