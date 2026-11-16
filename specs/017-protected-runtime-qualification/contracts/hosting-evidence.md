# Proposed internal qualification and report interfaces

Status: draft
Kind: internal-contract-design
Owner: factory add-protected-runtime-report; implementation feature017 T012T
Scope: preparation only; no canonical neutral contract or executable config

## Ownership and compatibility

The factory candidate owns the exact new profile and case vocabulary. The adapter
must not independently add protected scope or H-case fields to the existing
`openxfactory-runtime-evidence-internal-v1`. Preserve seven service roles, eight
source roles, three dispatch inputs, full-config/static-v2 validation and default
refusal. Proposed paths below do not exist yet and are not runtime selections.

## Trusted source capabilities

| Proposed capability | Required inputs and provenance | Output / authority |
| --- | --- | --- |
| Qualification construction in `hosted/qualification.py` | Authenticated admitted context, immutable actual finalized binding, current selected runtime/lifecycle and fixed authenticated observation ports | One bounded qualification operation; no provider setup or new grant |
| Owning proof/barrier operation | Current accepted source, exact challenge/request/run/attempt, actual verifier; preselected approved negative-case capabilities | Sanitized verification/replay/barrier digests; no proof/key/token export |
| Phase facts collector | Actual independent admission/source/issuance/guest/kernel observations tied to original decisions/generation | Fixed case outcomes derived from facts; no supplied pass boolean or live flag |
| Lifecycle outcome collector | Existing `CleanupVerification` from one run and its independently authenticated readback | Same plan/scope/generation/attempt and retention/retirement verification; no cleanup resend |
| Protected encoder in `hosted/evidence.py` | Validated operational-origin facts and factory-v1 closed projection | At most 16,384 canonical bytes; no I/O, file sink, uploader or operation authority |
| Later trusted CLI phase routing | Existing actual context and explicitly constructed authenticated hosting binding | Default remains unselected; no worker/environment/plugin selection surface |

Python types and digests do not authenticate a service. Construction is trusted
hosting only; selected transports and factual verifiers must establish provenance.
A transport outage, unknown consumed action or absent capability is a refusal,
not a negative-control success. No arbitrary signer/preimage API is introduced.

## Same-scope consistency and time

Require exact case, first run/attempt, actual source digests, config/policy/composition,
worker generation and registered plan equality across facts and cleanup. Retain
original phase clocks, budgets and earliest expiries. Report creation is historical
projection, not a current-use grant. A passed report requires every required actual
case and live gate plus fresh successful independent cleanup; failed/cancelled or
incomplete observations cannot be upgraded by successful cleanup.

Case labels cover source semantics only when the actual required observation was
performed. H10's existing budget anchors are not owning-qualifier proof; missing
H12/live observations remain absent. Source/fixture qualification never supplies a
protected-machine origin. Test-only golden projections have no acceptance channel.

## Privacy and authority

Use only factory-declared fields, safe fixed errors and bounded digests. Exclude
raw provider payloads, proof/challenge bytes, credentials, PEM/private keys, service
locations, local paths and exception strings/args/notes/causes/tracebacks. H12's
digest is over the redacted projection/privacy control, not the final enclosing
report. Public content addressing does not authenticate deployment or convey a grant.

The report cannot be a wallet possession proof, openMFA factor receipt, human
approval or consumer dependency decision. It makes no HSM/non-exportability or
human-MFA claim. No fixture credential/report is an operational input. Retention,
transport, publication and live acceptance require later separate source/owner gates.

## Factory context and report-time ordering

Valid-signed audience/environment mutations exercise the existing factory workload/
context verification path before the unchanged neutral owning proof; they do not
teach neutral openWallet verification GitHub-specific fields or semantics.

Cleanup freshness is relative to the latest actual operation/proof-use observation.
Cleanup-derived and H12 privacy results can follow verified cleanup and precede
report issuance, without reactivating runtime use. The new encoder cannot directly
reuse v1's all-case-before-cleanup floor for those later report-only observations.
Validate operational-use ordering and report-time freshness separately; preserve
existing v1 output/validation behavior. This avoids an impossible temporal cycle
between checking the completed projection and the cleanup facts it contains.
