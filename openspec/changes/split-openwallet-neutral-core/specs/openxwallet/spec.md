# openxwallet Specification

This delta is the corpus EXIT of `openxwallet` from openXwallet. Under
`split-openwallet-neutral-core` the eight requirements below leave this
repository for the openWallet project, the neutral standard, and are promoted
in its spec leg `opensoft/openWallet-spec` under the same capability id. The successor location is recorded in three
places that survive the archive: this delta's prose,
`contracts/openwallet-pin.yaml` as the live machine-readable pointer, and the
`contracts/CHANGELOG.md` entry for the adapter's first release.

The titles below are reproduced CHARACTER-FOR-CHARACTER from
`openspec/specs/openxwallet/spec.md`, in the form openxFactory's archived
`split-openxwallet-repo` used for the same capability's first exit. No emptied
stub spec is left behind as a signpost, and no archived record is rewritten.
`add-multi-key-wallets` archives BEFORE this change, so the text that leaves is
the text its four MODIFIED requirements promote; the titles are unchanged by it.

## REMOVED Requirements

### Requirement: A wallet is a key, never a record of a key

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: Authority travels as attenuated grants, never as keys

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: Use requires proof of possession, not presentation

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: Custody is declared and bounds what a signature evidences

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: Every exercise is key-attributed

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: Revocation propagates through the chain

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: Distinct-holder constraints are expressible

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".

### Requirement: The capability is an authority control, never an identity substrate

**Reason**: `split-openwallet-neutral-core` separates the neutral wallet standard from its openxFactory adapter. Under it `opensoft/openWallet` owns the standard with no openxFactory input — both contract families, the eight digested artifacts, the corpus, the syntax gate, the core validator and both neutral capabilities — while openXwallet keeps only what binds that standard to openxFactory: the hermes vocabulary binding, the root-issuer operator anchor and the register reader. This requirement is neutral standard content, so it is not amended here; it EXITS.

**Migration**: the requirement is promoted in the openWallet project's own OpenSpec instance, in its spec leg `opensoft/openWallet-spec`, under the SAME capability id `openxwallet`, received by a byte-identical path carve at a NAMED CARVE COMMIT of this repository, and openXwallet consumes it at the commit and per-file digests recorded in `contracts/openwallet-pin.yaml`. The only prose edit the carve permits travels with it: the subject `openXwallet SHALL` becomes `openWallet SHALL`. No `kind:` value, finding code, schema `$id`, filename or capability id is renamed — RULED by Brett Heap, 2026-10-08, "keep the prefix".
