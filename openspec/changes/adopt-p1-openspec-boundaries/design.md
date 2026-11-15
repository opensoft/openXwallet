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
