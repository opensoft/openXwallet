# openxwallet-agent-profile Specification

This delta is the corpus EXIT of `openxwallet-agent-profile` from openXwallet.
Under `split-openwallet-neutral-core` the three agent-holder requirements below
leave this repository for the openWallet project and are promoted in its spec
leg `opensoft/openWallet-spec` under the same capability id. The successor location is recorded in this delta's prose,
in `contracts/openwallet-pin.yaml`, and in the `contracts/CHANGELOG.md` entry for
the adapter's first release.

The titles below are reproduced CHARACTER-FOR-CHARACTER from
`openspec/specs/openxwallet-agent-profile/spec.md`. Two of the three travel with
only the subject edit. The third — *Agent authority is grant scope, not a
parallel vocabulary* — is the one requirement whose successor text differs, and
the difference is enumerated in its migration note rather than discovered later.

## REMOVED Requirements

### Requirement: An agent holder declares its composition

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet-agent-profile`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: A composition change revokes the agent's grants immediately

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet-agent-profile`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: Agent authority is grant scope, not a parallel vocabulary

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet-agent-profile`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. Its successor text DIFFERS in one enumerated way, authored in openWallet's own birth change and drafted in this change's `design.md` D8: the legal approval-posture terms become the keys of ONE DECLARED VOCABULARY BINDING supplied by the consuming layer, and a posture is refused when no binding is declared, because a standalone openWallet has no job envelope to read; openXwallet binds that vocabulary to the hermes job envelope's `approval_policy` keys, as before. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".
