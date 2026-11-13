# Implementation Plan: Protected Machine Runtime Qualification

**Branch**: `017-protected-runtime-qualification` | **Date**: 2026-11-12
**Spec**: [spec.md](spec.md)
**State**: T002–T011 source landed; isolated T012 workflow preparation candidate
**Factory governance**: `opensoft/openXfactory`, `openspec/changes/prepare-protected-runtime-qualification/`.

## Summary

Add an opt-in runtime embedding over the accepted offline proof gate. Trusted
issuer acquisition supplies bounded fresh snapshots to the existing verifier.
Trusted loaders, independent observations and a confined gate/custody deployment
supply the remaining machine boundary. Build offline fixtures first; real protected
qualification needs separately selected/authorized services and launch protection.
The first useful slice is issuer acquisition and verification without a signer.

The 2026-11-12 owner act and preparation landings are recorded in [evidence](evidence.md).
T003 landed in adapter #50. Brett subsequently commissioned T002's internal
operational grammar and source/protection preflight. Its factory-owned grammar
is `supporting-docs/operational-grammar.md` under the governing change; the
adapter implements `config.py` and refusal tests. Those sources landed at
factory #1308 / adapter #51 after source-only ratification. Brett subsequently
commissioned T004/T005 in isolation. `loaders.py` and `runtime.py` now compose
trusted connector capabilities and the unchanged proof gate. There is no deployed
runtime, consumer execution lock or protected dispatch in these slices.

Brett ratified adapter #52 at `3833bc8629e6` for source acceptance and
commissioned T006 in isolation. `supervisor.py` composes an admin-owned observation
key/current-source boundary; `launch.py` measures one controller-selected Linux
Python process generation. `SupervisedBridge` obtains and checks the existing
observation before using the unchanged four-argument bridge. Production service
hosting and separately administered deployment remain unqualified.

Brett ratified adapter #53 at `aff5b1e14979` for source acceptance only and
commissioned T007 in isolation. `ConfinedCustody` constructs the owning TLS
client/signer using actual protected material and joins fresh authenticated
issuance/deployment readback to the approved configuration. This is the accepted
confined-gate model, not a new neutral custody assertion. Deployment isolation,
initialized-state/recovery and lifecycle acceptance remain separate.

Brett ratified adapter #54 at `8de227dadd53` for source acceptance only and
commissioned T008 in isolation. `InitializedLedger` opens only existing private
state and requires an independently retained initialization identity plus fresh
authenticated scope/recovery readback. Runtime uses SQLite `mode=rw`, the existing
schema and reservation-before-signing semantics. It neither creates nor restores
state. Deployed storage protection, retention/recovery administration and lifecycle
qualification remain separate.

Brett ratified adapter #55 at `caef11d92906` for source acceptance only and
commissioned T009 in isolation. `RunLifecycle` binds a fixed run lease/manifest,
guards proof uses and returns the trusted operation's value only after independent
cleanup verification. `RunJanitor` operates over protected registrations and exact
provider ownership/generation, preserving retained/shared resources. A separately
scheduled expiry sweep works without runner finally. Actual provider registration,
independent scheduler/admin/readback hosting and live acceptance remain later gates.

Brett ratified adapter #56 at `508cb51f3407` for source acceptance only and
commissioned T010 in isolation. The required offline conformance runner now
checks a reviewed collection/count/anchor contract and every pytest phase, with
explicit clean owning-source integration. Linux loopback-only networking, a clean
environment/private home and irreversible privilege removal apply to helper execs
as well as pytest. This is source conformance; full R01 receipt construction remains
T011 and deployed P01/G02/G03/L01 remain separate.

Brett ratified adapter #57 at `2c36b07622fc` for source acceptance only and
commissioned T011 in isolation. `evidence.py` now builds bounded canonical internal
source/fixture reports from trusted selected configuration, observed case counts
and verified cleanup checkpoints. Exact sources, case/run, protection/readback and
cleanup are bound through closed fields/digests; raw credentials, tokens, proofs,
provider payloads and exception text are omitted. This report is not an openMFA
possession receipt or an acceptance grant. Protected-machine scope refuses in this
slice; later protected hosting/acceptance must review any promotion separately.

Brett ratified adapter #58 at `4916476364f7` for source acceptance only and
commissioned T012 in isolation. The manual caller and local reusable workflow
prepare same-commit source/claim binding, read-only admission before environment
selection, narrow job-level OIDC and an always-run cleanup handoff. Trusted
readiness requires current independent configuration, actual existing environment
protection, a separate case/run/attempt operation grant, registered external janitor
scheduling and independent readback. Production bindings remain unselected; the
CLI blocks before admission outputs or token access. Live execution and cleanup
clients remain T013/T014 hosting integrations, not a fixture fallback or hidden
environment activation switch. No setup or dispatch is authorized or performed.

## Technical Context

- Python 3.12 / Linux x86_64; `requirements-workload-binding.lock` is the reviewed dependency baseline. Additional transport dependencies require a complete reviewed hash lock.
- Reuse existing cryptography, canonical wallet/grant readers, verifier, owning proof API and SQLite reservations. No new JWT library, algorithm or neutral custody protocol is selected.
- Proposed opt-in package `scripts/workload_factory_binding_runtime/`; tests `tests/runtime_binding/`. Existing offline entrypoints do not import or start live transport.
- Use injected bounded HTTPS transport; default gates use deterministic doubles and isolated loopback fixtures. Live requests occur only in the separately authorized runtime path.
- Runtime configuration is the factory-owned internal operational projection. Credentials are opaque trusted deployment handles; the worker supplies no expected values or trusted loaders.
- Current-record connectors implement bounded authenticated `read(operation, reference, deadline=epoch)` and return at most 16 KiB of JSON. Intrinsic service identities and worker-channel context come only from trusted hosting. No public service protocol or production endpoint resolver is supplied.
- Every use repeats preflight around blocking operations and preserves the earliest known token/key, observation, policy/grant, challenge, registry, channel and protection deadline. Extra preflight I/O must not extend an accepted proof-gate checkpoint.
- T006 supports the narrow controlled command `executable -I -B worker configuration`, with explicit expected executable digest and controller-captured process generation. Actual proc metadata, bounded regular files and the worker's configuration enter the existing composition digest. This is not general memory, container-image or hostile-host attestation.
- Storage remains private initialized persistent state under the accepted trusted-host boundary; no throughput, hostile-host or backup-rollback guarantee is claimed.
- Fetch budgets, cache/rotation and administrative deadlines are proposed factory policy, not issuer service guarantees.

## Constitution Check

Before research: PASS against AGENTS.md's non-negotiable rules. Features 013/016
document that this adapter deliberately has no local constitution. No constitution
is adopted or inherited from the unrelated usage-control proposal.

After design: PASS for preparation. Factory governance owns composition; neutral
APIs remain upstream. No runtime/keyholding/deployment code goes into factory.
No existing pin, vendored schema, release, machine key, manifest or offline gate
changes. Confined-gate custody trust is explicit. New-profile owner acceptance
precedes implementation; live setup/dispatch and human acceptance remain separate.

## Project Structure and Interfaces

[Data model](data-model.md), [embedding API](contracts/runtime-embedding.md),
[qualification matrix](qualification-matrix.md) and [operational inputs](operational-inputs.md)
define the proposed boundary. Paths in [tasks](tasks.md) are future implementation
paths, reconciled against reviewed code without widening scope. That file is the
sole executable implementation list across the owning repositories.

## Design Decisions

[Research](research.md) records primary sources and alternatives. The trusted gate
enforces per-use workload/challenge/authority checks and alone receives the narrow
credential for its selected deployment. A separately administered supervisor
measures the actual approved launch. Worker access to either control plane is denied.
An mTLS peer/subject allowlist alone does not establish workload-bound custody.
A requirement for new custody-side assertions first needs the neutral owner's
decision; this adapter must not invent a replacement protocol.

The embedding is not a new public server protocol. Its operator-owned hosting
transport must authenticate/bound the worker channel and selected challenge/record
services. That hosting/deployment is a live acceptance input. Worker-provided
booleans or untrusted configuration cannot substitute for it. Preflight validates
exact selected source/profile, dependencies and protection evidence before composing
trusted constructor dependencies.

## Phases and Verification

1. Obtain owner acceptance and source implementation commissioning of the concrete factory projection/trust model.
2. Implement projection validation, issuer fetch/cache and accepted verifier adaptation with offline refusal vectors. This slice is independently testable before custody.
3. Compose authenticated current records/challenge, independent observation, confined signer and expected private state; reference evidence retains its fixture scope.
4. Wire offline conformance and safe receipts. Prepare protected workflow source after source review, without implying provider setup or dispatch authorization.
5. Obtain exact operational selections and scoped authorization. Run real machine qualification with independent readback, then deliver only its accepted portion to codeXfactory T002.

## Complexity and Rollback

A separate runtime package prevents accidental networking in offline gates.
No refresh daemon or persistent key cache is required. Bounded coalesced refresh
and the existing reservations suit the selected trusted-gate model. Disable the
opt-in bridge and revoke run-owned credentials/leases on rollback; retain consumed
state and safe evidence. Do not reset replay state or move domain/neutral pins
to manufacture qualification success.
