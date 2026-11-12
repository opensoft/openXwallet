# Implementation Plan: Protected Machine Runtime Qualification

**Branch**: `017-protected-runtime-qualification` | **Date**: 2026-11-12
**Spec**: [spec.md](spec.md)
**State**: profile ratified; issuer-only source commissioned; remaining runtime pending
**Factory governance**: `opensoft/openXfactory`, `openspec/changes/prepare-protected-runtime-qualification/`.

## Summary

Add an opt-in runtime embedding over the accepted offline proof gate. Trusted
issuer acquisition supplies bounded fresh snapshots to the existing verifier.
Trusted loaders, independent observations and a confined gate/custody deployment
supply the remaining machine boundary. Build offline fixtures first; real protected
qualification needs separately selected/authorized services and launch protection.
The first useful slice is issuer acquisition and verification without a signer.

The 2026-11-12 owner act and preparation landings are recorded in [evidence](evidence.md).
The current implementation is T003 and its necessary issuer-only constructor
configuration. T002's complete operational grammar, source/protection bindings
and service preflight remain pending. There is no trusted runtime composition,
consumer execution lock or protected dispatch in this slice.

## Technical Context

- Python 3.12 / Linux x86_64; `requirements-workload-binding.lock` is the reviewed dependency baseline. Additional transport dependencies require a complete reviewed hash lock.
- Reuse existing cryptography, canonical wallet/grant readers, verifier, owning proof API and SQLite reservations. No new JWT library, algorithm or neutral custody protocol is selected.
- Proposed opt-in package `scripts/workload_factory_binding_runtime/`; tests `tests/runtime_binding/`. Existing offline entrypoints do not import or start live transport.
- Use injected bounded HTTPS transport; default gates use deterministic doubles and isolated loopback fixtures. Live requests occur only in the separately authorized runtime path.
- Runtime configuration is the factory-owned internal operational projection. Credentials are opaque trusted deployment handles; the worker supplies no expected values or trusted loaders.
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
