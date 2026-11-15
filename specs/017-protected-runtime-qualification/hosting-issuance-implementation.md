# T012P isolated enrollment, issuance and host credential boundaries

Status: published T012P candidate PR #69; owner source ratification and live gates separate
Date: 2026-11-15 (America/La_Paz)

Brett source-ratified #68 at 38b029b02a9b and commissioned only T012P in isolation.
Factory add-protected-runtime-hosting-issuance remains the governing decision;
feature017 tasks.md is the sole executable list. No duplicate factory checklist
is created in response to the OpenSpec CLI handoff-only task warning.

The bounded realization pins a complete enrollment selection: case, static plan,
host/incarnation, immutable source, UID, role, public key, bootstrap peer and exact
issuer certificate/version. The App policy pins that entire enrollment digest;
matching role names alone cannot combine different selections. Current reads also
refuse mutation of the selected configuration without fresh approval.

The bounded realization uses independently current enrollment facts, valid CSR
proof plus approved public-key fingerprint, an explicitly initialized atomic
nonce ledger, short client certificates and mTLS certificate-fingerprint role
authentication. Request names or CSR subjects never authenticate a peer.

A selected exact-version Key Vault RSA sign operation is verified locally before
fixed-origin GitHub App/installation checks, repository/permission-limited token
exchange and actual returned-repository readback. Returned provider bearer expiry
is recorded separately from the shorter use deadline. The original wall/monotonic
decision is retained for later credential resolution; a fresh caller cannot renew it. Reader credentials cannot
request broker permissions. An independently constructed retirement observer must
see explicit authentication refusal after revocation; outage is incomplete.

The local credential port uses kernel per-message PID/UID/GID and selected process
generation/capability. Worker role strings cannot replace that identity, including
when a socket descriptor is inherited. Known-good issuer/controller requests are
positive controls for explicit worker denials; outage is never a denial. Source
fixtures do not establish deployed VM identity/IMDS/network/mount/key-file/admin
isolation, which remains an independently observed operational gate.

Software Ed25519 custody and all owning APIs/pins remain unchanged. No Key Vault
Ed25519/HSM/non-exportability, deployed source provenance, live issuance, listener
activation or protected receipt is claimed. Lost issuance responses remain consumed
and indeterminate, and cannot be retried or counted as retired without evidence.

Primary protocol sources:
- [GitHub App JWT](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app)
- [Installation access tokens](https://docs.github.com/en/rest/apps/apps#create-an-installation-access-token-for-an-app)
- [Installation token retirement](https://docs.github.com/en/rest/apps/installations#revoke-an-installation-access-token)
- [Key Vault digest signing](https://learn.microsoft.com/en-us/rest/api/keyvault/keys/sign/sign?view=rest-keyvault-keys-2025-07-01)

T012Q-V, setup/dispatch and live qualification remain uncommissioned. Feedback
stays deferred and neither blocked write is replayed.

## Additional kernel qualification

credential_kernel_qualification.py is an explicit, root-only disposable fixture,
not a deployment command or default gate. It uses separate numeric UIDs 1001/1002
inside a network-none container to prove actual key-file/policy access boundaries
and the source broker's per-message credential check. A trusted positive reaches
a synthetic loopback metadata endpoint; a worker seccomp connect filter returns
EPERM. Deliberately exposed key, writable policy and network paths invalidate the
denial qualification. No public metadata/provider endpoint or existing bench
policy is touched. All helpers are reaped and only the task fixture mount is writable.
The current image's libseccomp is an observed fixture prerequisite; no runtime
Python dependency or production sandbox is selected by this check.

The full mandatory matrix remains unprivileged and separately exercises every
reviewed node. This extra UID/kernel fixture supplements those source controls;
it does not establish deployed VM/IMDS/admin isolation or protected acceptance.
[libseccomp API](https://github.com/seccomp/libseccomp/blob/main/include/seccomp.h.in).

## Qualified source checkpoint

The final source adds 96 measured nodes: 49 issuance, 26 enrollment and 21 kernel
credential-port cases. All 1,862 full-suite tests and 1,560 mandatory native cases
pass without failures/errors/skips; old matrix identities/fingerprints remain.
H06/H07 have 32/28 anchored nodes. The separate kernel fixture passes 11 checks.
Source and private receipt hashes, exact #68 acceptance/landing, earlier failed
diagnostics and cleanup readback are recorded in evidence.md. A provider-outage regression first returned a refusal; it now returns unavailable,
so an outage cannot qualify as an authenticated denial. No failed or earlier
checkpoint qualifies this final source. This candidate is published in #69 and is not source-ratified; actual service identities/provider facts/host safeguards,
T012Q-V and every operational setup/dispatch gate remain separate.

## Publication review corrections

The local nine-expert Codex panel found and closed two defects. Kernel credentials
authenticate the request sender but do not bind the reader of an inherited socket.
Each requester now creates a fresh private reply socketpair after untrusted
descriptor inheritance and transfers only its send endpoint with SCM_RIGHTS. The
broker validates that capability and returns credentials exclusively through it;
the shared request channel receives no reply. Missing, extra, malformed and
truncated descriptors close without capability execution.

An outer finally also closes the reply on BaseException cancellation. Tests retain
the interruption traceback and assert descriptor count plus reader EOF, preventing
garbage collection from concealing the leak. The passive-reader regression retains
an authorized issuer positive while the inherited request endpoint receives no
credential. Existing explicit worker denial and outage distinctions remain.

Hosted-analysis refinements move only nonsecret method/URL routing to trusted
parent-selected process arguments. Headers, body and TLS references remain on the
anonymous pipe. TLS/framing guards, deadlines and reaping remain intact; test
setup is outside exception assertions. No finding suppression, threshold change
or manual finding disposition is introduced.
