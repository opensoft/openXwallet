# Provider-owned tooling consumption
Status: draft

Re-vendor bytes from the published openXfactory P1 repair commit. Scripts differ
only by the existing three-line vendoring header; YAML differs only by its
declared header. The JSON lockfile is copied verbatim so its SHA-512 still
matches the pin. No consumer-specific source fork is allowed.

The artifact stays OpenSpec 1.12.0. npm ci verifies the full committed closure
with lifecycle scripts disabled. The operator's invocation directory/environment
defines allowed roots, rather than model-selectable CLI operands. Directory
descriptors retain identity; missing safe descriptor/proc support refuses.
Invalid generations and fetch evidence are retained, never destructively reset.

Existing workflow adaptations remain at their declared older provenance.
Existing runtime, contract and core pins stay coherent; this tooling refresh
does not advance unrelated runtime composition or grant operational authority.

## Manual source validation of published main

Manual source CI accepts only refs/heads/main. A first-step shell guard
rejects other refs before dependency reads. Existing pull-request conditions
and source checks remain effective. GitHub supplies event/ref metadata; no
model-selected runtime/dependency/base input is introduced. Whitespace
validation on a manual main run compares HEAD to its actual first parent.
The existing named jobs, capability/group removal and offline matrix are
unchanged. A small countertest executes the declared guard for main, another
branch, a tag, an empty ref and a pull-request context.


Final upstream argument-boundary completion (2026-11-16): adopt published provider 87e08c277971bc8a072934df44c291a7e1331ab9 byte-identically below declared headers. Its complete-batch execution check prevents a valid early target from running before a later invalid target refuses. Provider main admission and unchanged checks remain prerequisites for consumer landing. No runtime pins, scan settings, historical evidence or billing changes.
