---
Status: draft
code_surface: openXwallet — declared OpenSpec tooling and guarded published-main source validation
target_release: implemented — tooling consumption only, no runtime contract change
---

## Why
Brett Heap commissioned P1 security repairs in openXfactory, preserving active
sessions, evidence and checks. This consumer carries declared copies of that
provider's OpenSpec tooling. Adopt its published repair without a local fork.

## What Changes
Re-vendor the standalone verifier, installer and unchanged-version artifact pin,
including the now hash-addressed package lock. Record exact provider commit and
per-file digests. Preserve the existing workflow adaptation, artifact version,
strict validation, integrity checks and all existing runtime/provider pins.

## Capabilities
### Modified Capabilities
- openspec-cli-consumption: independent operator input/executable authority,
  descriptor-held filesystem operations and retained cache generations.

## Impact
Declared tooling copies, provenance, boundary tests, guarded source-CI
invocation and this maintenance packet are in scope. Existing repository-read
token permissions remain unchanged and source-only. Runtime setup/issuance,
protected workflow authority, active profiles, other feature acceptance,
billing and Sonar policy remain separately governed.
[Implementation tasks](../../../specs/018-p1-openspec-boundaries/tasks.md) are the sole task list.

## Published-main source verification amendment

The P1 consumer update landed, but ordinary test workflows have no direct
published-main entrypoint. Add a manual invocation of the SAME source
validation job on refs/heads/main, with an executable first-step refusal for
any other manual ref before checkout/private dependency access. Preserve all
PR selectors, fork refusals, immutable dependency pins, tests and isolation.
Existing repository-read token scopes remain source-only; this adds no
runtime setup/issuance/hosting authority and invokes no protected workflow.
