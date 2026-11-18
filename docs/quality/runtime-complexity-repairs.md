# Runtime validation maintenance

The carve checker separates document grammar, per-row digest checks, and
cross-row consistency. Its two digest passes and the order of refusals stay
the same. The register reader separates row, grant and per-seat checks, with
the same self-test probes and expected refusals. Pin validation keeps its
existing Git and content checks.

The hosted lifecycle code separates journal lock acquisition, state replay,
process cleanup, request decoding, and validation of independently read facts.
The existing deadline checks, callback order, and failure translations remain
in place. Trusted source construction of HostedLifecycle now takes
LifecycleStores for its three journals and LifecycleActors for the janitor,
auditor and scheduler. Both construction sites use those typed groups. The
existing field checks still run, and the wire format is unchanged.

The required source and native checks will qualify the refactors before the
assembly scan determines which original Sonar findings have closed.
