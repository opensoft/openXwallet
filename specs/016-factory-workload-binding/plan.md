# Implementation Plan: Factory/workload binding

**Branch**: `016-factory-workload-binding` | **Date**: 2026-11-11
**Spec**: [spec.md](spec.md)

## Summary

Implement an opt-in offline adapter library. A trusted gate reloads operator
records, authenticates a workload JWT with an explicitly trusted key snapshot,
verifies a separate signed artifact observation, checks bounded existing grants
and reserves the token/challenge before invoking the owning wallet proof API.

## Technical Context

- **Language/Version**: Python 3.12+.
- **Dependencies**: cryptography (RSA/Ed25519), rfc8785, stdlib SQLite; pytest.
- **Storage**: private file-backed replay ledger, hashed identities only.
- **Tests**: unit refusal matrix and isolated reference subprocess qualification.
- **Platform**: Linux bench/hosted CI, offline after dependency checkout.
- **Type**: adapter library and test-only processes; no installed service.
- **Performance**: bounded 16 KiB token, key set and grant depth; no throughput claim.
- **Scope**: exact reusable workflow and agent, existing `act` tier only.

## Constitution Check

Before research: PASS against AGENTS.md's non-negotiable rules. This repository
deliberately has no constitution (feature 013 records this). Do not adopt one
or inherit PR #13's broader proposal.

After design: PASS. openxFactory owns the draft composition; this repo owns its
adapter. No published schema, neutral source, pin, machine key, vendored artifact,
manifest, release or validation floor changes. Gates stay offline. Explicit API
injection tests separately accepted neutral source without advancing a pin.
Candidate implementation does not ratify its profile or authorize activation.

## Project Structure

```text
scripts/workload_factory_binding/   # candidate adapter library
tests/factory_binding/     # unit matrix and test-only processes
specs/016-factory-workload-binding/
  spec.md, plan.md, research.md, data-model.md, quickstart.md
  contracts/adapter-api.md, tasks.md, analysis.md, evidence.md
```

## Design Decisions

1. Preserve canonical wallet/grant field names. This narrower runtime projection
   supports only `act`, explicit bounded objects and conservative posture; it
   does not replace the canonical validator.
2. Trust only operator-selected fresh issuer keys; never token-supplied URLs.
   RS256 only, exact claims, no wildcard matching or clock leeway.
3. The observer reads its own selected artifacts/configuration and signs their
   digest with a separate key. It does not establish host/model behavior.
4. Challenge loading belongs to the trusted gate. Its request digest includes
   policy revision, wallet, grant and exact act/object/run binding.
5. Commit one-use reservation before custody. Ambiguous failures stay consumed.
6. Reload authority/registry/evidence after signing before returning. This detects
   observed mid-call changes; it is not distributed atomic revocation.
7. Test subprocesses separate worker, observer and custody credentials. Same-user
   tests establish interface separation, not hostile operating-system isolation.

## Complexity Tracking

SQLite is necessary for restart/concurrency replay refusal; an in-memory set
cannot meet FR-007. No refresh daemon, provider client, executor, grant issuance,
domain marker or human broker is introduced.
