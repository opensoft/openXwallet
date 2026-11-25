# Original-registration handoff design working draft

Status: alternatives retained for context; proposed route A selected for drafting only, unratified.
Date: 2026-11-25, America/La_Paz.

## Problem and required result

The [fresh eligibility record](p3-entrypoint-manifest-eligibility.md) establishes
that a digest-only lifecycle reply cannot provide the original complete credential
manifest or retained-store capability required by the accepted accounting policy.
The first codeXfactory pilot needs a real source-owned path to carry those facts
into the companion caller before per-manifest accounting or handoff I/O.

The resulting capability must bind the exact original registration digest,
original owner/store identity, complete canonical credential-resource subset,
resource epoch, launch/source/run/attempt scope, capture provenance and original
authority deadlines. N is derived from every original credential row, never a
count argument or a later final RunPlan. An identity/content hash alone does not
authenticate the provenance. Original owner checks must still enforce the actual
registered resource equality at prepare and independent acknowledgement.

## Design alternatives

| Route | Proposed source work | Consequence |
| --- | --- | --- |
| A: carry from existing staging exchanges (recommended drafting basis) | A distinct closed internal descriptor returned by the existing authenticated registration/acknowledgement path; sealed capture and original retained-state handoff across phase/process boundaries | Avoids inventing a new manifest-read RPC, but requires explicit wire and retention/record grammar ownership plus a demonstrated caller materialization path |
| B: explicit bounded manifest acquisition | A source-fixed owner read before dependent handoff, with original-attempt consumption, peer/scope/store binding and full physical prepayment | Requires a revised acquisition sequence and measured accounting amendment; it cannot be hidden inside the just-accepted totals |

The proposed route-A factory retain-original-registration-manifest draft and
[paired registration plan](p3-entrypoint-registration-plan.md) now define the
recommended original controller-store placement and same-row claim. The source design remains unratified.

A source proposal must choose and fully define one path. No hypothetical callback,
fixture-private store, source-independent JSON/file input or generic plugin may
stand in for the path. The actual owner and location of retained state and its
consumer must be mapped to the existing composition before implementation. If
that mapping needs a new backend, role, grant or managed resource, disclose it for
governance rather than treating it as an existing prerequisite.

## Recommended route A contract work

Specify a complete owner-derived credential-resource projection from the original
registration, binding registration_digest, original retained-store identity,
resource_epoch and scope. The independent acknowledgement must corroborate the
same original facts. Preserve current v1 closed wire behavior; any companion
profile and record grammar must be separate source-selected contracts, with old/
new mismatch refusal and no data-driven negotiation.

A capture operation may accept only authenticated owner-module transport evidence,
not caller-built dictionaries. Retention must preserve that evidence, original
attempt identity and store continuity across the actual staging/finalization
process boundary. Reopen must never create/initialize/copy/restore an absent
backend, renew a grant or manufacture a replacement approval. Pure in-memory
one-shot state cannot be advertised as durable cross-process conservation.

Before per-manifest selection, source construction must materialize the genuine
retained capability without an extra unbudgeted lookup. Missing, changed, expired,
replayed, ambiguous or mismatched material refuses before dependent I/O. After
selection, freeze the binding and retain original high-water counts and clocks.
Lost original state refuses. Cleanup and audit stay their original separately
authorized operations; a manifest supplies identity facts and no new permission.

## Required evidence before source acceptance or implementation

The governed packet must explicitly resolve transport fields and producer/
consumer identities, storage placement/ownership, closed record transitions,
original consumption/loss semantics, source selection, complete byte bounds and
physical call inventory. Do not assume the no-new-RPC design automatically fits
current caps: prove all affected real transports and full owning-proof callbacks.

The paired feature017 plan must cover N1/N2/N3; genuine existing-owner capture,
retained reopen, cross-process restart/loss; changed scope/registration/store/
resource epoch and omission/duplication; forged/replayed evidence; response loss;
concurrent original claims; old/new wire crossover; source-only activation
refusal; exact original budgets/deadlines/body caps; complete unchanged full
admission and qualification39; independent cleanup and prior full/native test
identity preservation. Additional mismatches stop for governance.

## Scope boundaries

This draft changes no accepted policy bytes or ceilings. The existing three
manual inputs, seven runtime and eight source roles, fourteen-resource graph,
neutral contracts, old static/full/report grammars, workflow phase permissions
and unconditional default refusal remain constraints. Any proposed exception
must be explicit and source-ratified before dependent code. Do not add a duplicate
implementation task list: existing T013P08 in [tasks.md](tasks.md) remains owner.

No source publication/acceptance or new wire/retention implementation is inferred
from this draft. Setup/dispatch, role appointments, live/human/consumer acceptance
and feedback remain ungranted/deferred; blocked writes remain unreplayed.
