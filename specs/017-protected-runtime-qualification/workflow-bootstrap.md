# T013 Dispatch Bootstrap Source Prerequisite

Status: isolated source candidate commissioned; paired source acceptance pending
Prepared: 2026-11-13
Scope: source preparation; no protected dispatch or operational authority

## Commissioned candidate implementation

Brett subsequently commissioned this fix through the factory/adapter process,
with setup and dispatch still unauthorized. The new factory change is
`opensoft/openXfactory`, `openspec/changes/fix-protected-runtime-dispatch-bootstrap/`.
It preserves the accepted baseline/origin and hands off to feature 017 T012B.

The candidate implements `bootstrap.py`: closed static selection document with
profile `openxfactory-dispatch-selection-internal-v1`, exactly `profile` and
`configuration`, with only launch run ID/attempt omitted. All other runtime
fields remain committed. Full runtime validation still requires both run fields.
Actual-run bootstrap uses an independently selected approved digest/principal
and authenticated reader, corroborates static/full config, then calls existing
grant/protection/scheduler/lease admission with the earliest deadline. Readback
includes preauthorization, selection/source/repository/case/run and attempt,
full config digest and operation grant. Production authentication and atomic
authority consumption remain unselected hosting obligations, not fixture claims.

Manual and same-commit reusable inputs migrate explicitly from `config_digest`
and `operation_grant_ref` to `selection_digest` and `preauthorization_ref`.
Environment variable names migrate to `OPENXWALLET_SELECTION_DIGEST` and
`OPENXWALLET_PREAUTHORIZATION_REF`. Old variables are refused, not reinterpreted.
Internal `WorkflowContext.config_digest` and operation grants keep their full
run-bound meaning. Each preflight, including after environment approval, repeats
independent bootstrap/admission. No approval is passed through a job output.

The candidate resolves the circular input contract; it supplies no operational
clients, authorization or protected receipt promotion. The historical finding
and proposed reasoning below remain provenance. Source review and exact-head
isolated evidence are recorded in [evidence](evidence.md).

## Verified mismatch at accepted #59

The manual caller requires `config_digest` and `operation_grant_ref` before
dispatch. The reusable propagates these values unchanged into admission. The
factory-owned runtime grammar requires the full canonical configuration to contain
`launch.run_id` and `launch.run_attempt`. `validate_config` hashes that entire
configuration and checks an independently approved digest. `workflow.admit`
requires that digest to equal the dispatch input, and the launch and current
grant must match the actual workflow run/attempt exactly.

GitHub's [dispatch API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
accepts the inputs in the request and documents the run ID in the response.
Its [variable reference](https://docs.github.com/en/actions/reference/workflows-and-actions/variables)
defines a run's stable ID and an attempt that increments on rerun. From those
API semantics and the source bindings, a first-run full config digest cannot
be prepared before dispatch without predicting the assigned ID. Reusing its
digest for a later attempt also fails the exact attempt binding. This is a
planning finding; no dispatch was attempted to reproduce it.

An offline probe used the existing synthetic `test_config.configuration` fixture
and real canonical `digest`/`validate_config` functions, unprivileged in py-bench.
The valid base configuration passed. Changing only run ID `789` to `790`, or
only attempt `1` to `2`, changed the full digest. Keeping the original independent
approval refused both with `runtime-config-unapproved`. No endpoint, credential,
key service or fixture process was used.

| Synthetic case | Canonical digest |
| --- | --- |
| Base | `sha256:6ce0b5fcdae669ac9eb0152079a1ce7bd3cba4789412a3f91796d01e56ec323b` |
| Different run ID only | `sha256:f39996870890709e5ab2092d6a8d2c431b14d4c19be2a1cd6e4f4efe1ec52280` |
| Different attempt only | `sha256:b3d90794aa45d64e0ad25575ea27f5025e767ade9e3db0bbbd930a68720bdf2b` |

This finding does not weaken the accepted run binding. The default operational
factory still refuses before environment outputs/OIDC. #59 supplies source
preparation, not an operable live hosting integration.

## Proposed governed resolution

Keep the full runtime configuration, independently approved digest and exact
run/attempt checks. Introduce a separately reviewed static selection commitment
and bootstrap preauthorization for dispatch. Their new names/schema/validation
are a factory decision, not a reinterpretation of `config_digest`.

After dispatch assigns the actual run/attempt, an independently administered
bootstrap authority authenticates that context, verifies the accepted static
selection and preauthorization, then binds/approves the final canonical runtime
configuration and a short-lived case/run/attempt operation grant. The admission
host obtains these through authenticated trusted clients. A worker-provided
output, config hash, environment variable, artifact or boolean cannot supply the
independent approval. No bootstrap OIDC or signing privilege is implied: the
authority's independent GitHub/context authentication and trust roots must be
explicitly designed, reviewed and qualified before integration.

The caller/reusable must distinguish the static dispatch commitment from the
final runtime digest. If trusted outputs transport the latter, the producing
principal and output integrity require explicit review. Bootstrap precedes
environment selection and OIDC-capable work; admission repeats after environment
approval with fresh effective protection, source, grant, lease and scheduler
readback. Changed/expired selections and attempts require fresh independent
authority. No discovery dispatch, ID prediction, input mutation, prior-run reuse
or omission/zeroing of run fields is an acceptable workaround.

## Source ownership and review handoff

The amendment belongs first in `opensoft/openXfactory`'s canonical
`prepare-protected-runtime-qualification` change, including origin/ratification
handling under its governance. Adapter feature 017 then implements the accepted
interface in its sole task list. Preserve existing machine-key meaning; any new
interface needs an explicit migration note and source acceptance. This document
does not amend the factory's accepted grammar or commission runtime implementation.

Before an operational decision, reviewed verification must cover independent
bootstrap authentication, source/static-selection substitution, grant/run/attempt
replay, concurrent dispatches, stale/changed protection, failure before OIDC,
fresh admission after approval, expiry/revocation and independent cleanup after
hard runner death. Live hosting/readback/qualify/cleanup clients and protected
receipt scope require separate source review too. These are review criteria,
not a second executable task list.

The T013 packet and [authorization draft](scoped-authorization.md) remain
nonoperative until this source dependency and all actual selections are resolved.
Feedback remains deferred; neither historical blocked write may be replayed.
