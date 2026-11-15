---
Status: draft
code_surface: openXwallet — declared OpenSpec verifier/installer consumption refresh
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
Only declared tooling copies, their lock/provenance documentation, boundary
tests and this maintenance packet change. No deployment, token request, active
profile, source acceptance of another feature, billing or Sonar policy changes.
[Implementation tasks](../../../specs/018-p1-openspec-boundaries/tasks.md) are the sole task list.
