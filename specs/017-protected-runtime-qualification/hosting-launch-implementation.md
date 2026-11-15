# T012R isolated host launch and admission boundary

Status: reviewed isolated implementation candidate in #71; paired factory #1326; unratified
Date: 2026-11-15
Factory owners: add-protected-runtime-hosting-issuance and fix-hosted-protection-read-budget
Sole executable list: feature017 tasks.md, T012R

## Actual owner commission

Brett source-ratified factory #1322 e813051af8c0 and adapter #70 f6956e324e37,
then commissioned ordered landing and T012R implementation/testing in isolation.
They landed normally as 54f720b6df81473473d48c7289c51faafccb1c9d and
27843096189ac6e168999832b821333a58392b4c, with equal accepted/merged trees.
T012S-V, operational setup/dispatch and live qualification remain uncommissioned.

## Bounded realization

Provide separate admission-only HTTPS routes for static-v2 plan and protected
staging, plus private pinned mTLS host registration/start/status routes. Public
bodies contain only the existing three dispatch inputs; no grant, path, UID, URL,
policy or worker code is selected from a request. Wrong intrinsic route/phase,
bootstrap audience or current scope refuses before effects. Trusted source-only
workflow bindings opt in; default CLI bindings and existing workflow YAML refuse
as before. V2 never enters v1 Approval or full-runtime validators with placeholders.

Protected stage correlation reads actual selected run/job/review and source/hold/
control/protection facts. Reuse pure graph/run/review validators, without casting
the static plan to a v1 Approval. A separately authenticated current stage grant
and independently acknowledged durable cleanup registration are mandatory.
Journal the controller operation and named host unit/invocation before any start.
A compare-and-set consumes the one start attempt before manager I/O. Lost replies,
crashes, expiry or failed acknowledgement never permit a second start, reused ref,
replacement generation or automatic authority renewal. Recovery is status-only,
at most six decisions over sixty seconds and the earlier case/grant/lease expiry.

The portable reference manager owns an actual POSIX-session unit, boot/invocation,
PID/start/session and observed cgroup. It has no systemd/backend deployment claim.
It derives immutable worker projection from the approved plan and actual run,
publishes it exclusively, measures all selected artifacts, and launches with a
minimal environment/no credential FDs. A child-only Linux Landlock policy permits
read/execute of selected runtime/artifact/configuration files and denies all
filesystem writes/private material. A no-new-privileges x86-64 seccomp filter
denies network/control/ptrace and metadata-changing syscalls, rejects x32/foreign
ABIs, and is inherited across exec. Unsupported kernels refuse; no skipped positive.
Parent-death fencing kills the child if its reference manager dies. Actual
kernel/process/file observations establish generation; worker READY is only a
bounded scheduling handshake, never authoritative process/proof evidence.

Current checks and original deadlines surround blocking operations. Host start
rechecks independently observed grant and lease against the recorded unit. No
public route exposes private controls or full config/signing capability. Worker
control/key/policy/network denials require allowed positive controls; outage is
not denial and excess-permission mutations must break qualification.

## Qualification and limits

Tests use actual local TLS/mTLS, independent authoritative fixture state, real
journal transactions, sandboxed workers and measured kernel/file state. Include
concurrent and crash/lost-response windows, exact host/unit/generation substitution,
revocation/deadline regressions and pure status-only reconciliation. Extend fixed
H03/H07 anchors only after measured collection, retaining every old identity.
Run ordered full and mandatory native gates and audit attributed cleanup.

The reference POSIX unit and local sandbox qualify only their measured source
boundary. Real systemd/cgroup ownership, installed read-only images, Azure identity/
IMDS/firewall administration, remote-host finalization, actual service enrollment,
T012S durable staging-to-final cleanup takeover and T012T live adapters remain
separate gates. No hostile-root or in-memory model-behavior claim is made.

Primary kernel references: [Landlock](https://docs.kernel.org/userspace-api/landlock.html),
[seccomp filtering](https://docs.kernel.org/userspace-api/seccomp_filter.html),
[Linux x86-64 syscall ABI](https://github.com/torvalds/linux/blob/v6.6/arch/x86/entry/syscalls/syscall_64.tbl).
No live service/setup/dispatch, feedback or blocked/denied write is performed.

## As-built isolated candidate

The public admission service and private host agent are separate actual TLS
listeners, explicitly constructed from source-selected dependencies. Host role
permissions are checked against the authenticated client certificate. Public
requests retain only the three dispatch inputs and return staging readiness;
workers receive no credential-bearing file descriptors or control identity.
Neither the default CLI binding nor the workflow YAML is activated.

The controller and host retain independently initialized, identity-bound SQLite
journals. Registration durably names the manager PID/start, host/boot, unit and
invocation before configuration publication. An independent mTLS read of the
fixture janitor's fsynced registration acknowledgement precedes one consumed
start. Concurrent calls have one winner; lost register/start replies reconcile
through bounded status only. Original expiry, unit and generation remain fixed
across controller reconstruction, with no replacement or authority renewal.

The reference manager launches from a persistent owner thread: Linux PDEATHSIG
tracks the creating thread, so an HTTP request thread is not its lifetime owner.
The worker's inherited seccomp filter prevents fork/session escape and clearing
PDEATHSIG. The child uses the selected UID/GID, no additional supplementary
groups, zero effective/permitted/inheritable/ambient capabilities, no-new-privileges,
minimal environment, and the approved read/execute-only Landlock projection.
After helper creation, current grant/lease/deadline/source are checked again before
worker instructions cross its pipe; a delayed or revoked start cannot execute it.
The actual crash test kills the manager after child measurement and before PID
persistence; a private test subreaper observes SIGKILL and reaps the worker. The
retained start attempt stays consumed and cannot be resubmitted.

Integration exposed a credential transport defect: response reads inherited the
five-second connect timeout. They now use the remainder of the original maximum
ten-second RPC; connect stays at most five seconds. A real delayed TLS response
checks that correction. No deadline or ledger allocation is renewed.

## Initial qualification receipt (superseded by publication review)

The corrected frozen Python source passes all seven ordered repository gates:
contract pin, neutral pin, syntax, plain validator, strict validator, full pytest,
and the pinned OpenSpec CLI in default `--all --strict` mode. Full pytest passes
2,163 cases with zero failures/errors/skips. The mandatory separate native
container passes 1,861 cases with zero failures/errors/skips and conformance PASS:
network none, loopback only, source read-only, non-root UID, empty supplementary
groups, no capabilities, and no-new-privileges.

All 1,792 prior mandatory node identities, per-module fingerprints and anchors
are retained. The 69 new launch cases add 64 substantive H03 anchors and five H07
anchors; H07 now has 33. Actual positives cover protocol correlation, independent
grant/acknowledgement, physical launch, concurrent starts, lost replies and manager
crash. Mutations cover scope, review actor, source, current protection, lease,
artifact/configuration, generation, clock, endpoint and privilege drift. Kernel
probes observe actual private-key read, write, metadata, fork, network/control and
PDEATHSIG-clearing denials. Excess key permission breaks the denial positive;
private role outage and excess worker permissions never count as denial.

Earlier full/native runs are superseded by the parent-death filter correction
and the post-helper authority checkpoint. The old filter's real clearing probe failed; the corrected probe and
launch/crash positives pass, and both complete suites reran on the corrected
source. Private receipts are in `t012r-isolated-20261115`: complete-full.xml,
complete-native.xml, complete-ordered-gates.json,
qualified-source-inputs.json, qualification-summary.json and the cleanup audit.

T012R is an isolated source candidate, with no PR/source ratification inferred.
The grant, operator-context and janitor facts are independent authoritative TLS
fixture services; actual production fact producers, scheduler/takeover and live
provider/VM qualification remain T012S/T012T and later gates. This does not
commission T012S-V, setup, dispatch, live credential enrollment or deployment.


## Initial audited fixture cleanup

The audit ran in py-bench's actual test PID namespace. All 114 recorded owned
process generations, 396 hosted generations, 15,990 credential/helper generations
and eight crash-window worker generations have no matching live instance. No
attributed helper remains. The audit verified 48 preservation records and 24
consumed dispatch-journal records before fixture teardown, and retained 546
staging-state summaries without resetting an attempt. Exploratory pre-counter
journal schemas are distinguished from the final retained-counter schema.

All three task-native containers are absent. The 25 exact temporary fixture roots
were removed only after audit; private XML, source hashes, audit and removal
receipts are retained outside those roots. The shared owner checkout, pinned CLI,
accepted worktrees and active benches remain in place. This is isolated test
resource cleanup, with no production scheduler/takeover qualification inferred.

## Corrected publication qualification

The paired candidate fixes six local/hosted findings: queued-signal and cross-process
resource controls, a complete fresh source/hold/context correlation after durable
cleanup acknowledgement, a whole-frame nonblocking READY deadline, actual run/source
admission reply binding, and ordinary pytest ambient groups/tool-cache selection.
The launcher also pins the current resolved interpreter and fixed interpreter flags;
configuration/worker files must be selected canonical existing files. No suppression
or reduced runtime isolation is used to address static findings.

Factory #1326 proposes two complete protected staging observations sharing the
original ten-second Decision: correlation8/protection6/source8/control4, total26,
private16 (controller uses15). Each correlation reader retains its four-read cap.
A third observation, joined/upgraded/reset ledger or authority renewal refuses.
Ordinary3/13/private12 and finalization6/18/28/private12 remain unchanged. The second
correlation runs after durable acknowledgement and before opening host start; the
request carries the tighter authority expiry and retains its after-TLS grant/lease
check. This profile is proposed source, awaiting paired owner ratification.

Corrected full pytest passes 2,200 cases; the separate network-none, read-only-source
native container passes all 1,898 required cases, with zero skips/failures/errors.
All 1,792 previous required identities/fingerprints/anchors remain; the 106 launch
nodes produce H03/H07 anchor totals 94/40. Focused rechecks pass 140 cases and factory
budget/correlation checks pass 538. All seven ordered gates pass. The final pinned
OpenSpec gate initially refused an inherited /root npm cache; its unchanged source
and verified artifact pass with a task-local cache. The earlier result is retained.

Nine local Codex specialists and the coordinator found no remaining actionable
source issue. Code review covers wallet17cce0b0f9b2 and factory56a0e0510834; subsequent
documentation commits are checked for identical tested runtime/test/workflow inputs.
No hosted Codex connector review is claimed. Fresh hosted checks are recorded on
the paired PRs independently of this isolated qualification.

Current private receipts are retained in t012r-publication-20261115: resumed-full.xml,
resumed-native.xml, resumed-ordered-gates.json, qualified-source-inputs.json,
resumed-focused.xml, factory-resumed.xml and local-codex-review-current.json.
The original t012r-isolated receipts describe only the earlier source.

Only ordinary source-test pytest YAML changes to clear supplementary groups and
select the immutable system interpreter for inert stdlib-only fixture workers.
Protected workflow YAML, neutral APIs/pins, refusing defaults and operational
authority remain unchanged. T012S-V, production cleanup ownership/takeover, actual
provider/host enrollment, setup/dispatch and live qualification remain separate.

Publication cleanup was audited in py-bench's test PID namespace: 38 recorded
process generations, 132 hosted generations, 9,022 credential/helper generations
and three crash-window generations have no matching live instance. No attributed
helper remains. The audit verifies 16 preservation records, eight consumed journals
and 286 retained staging summaries. The exact task fixture roots are removed after
audit; XML/source/review/audit receipts remain outside those roots. The disposable
native container is absent; accepted checkouts and active benches remain intact.
Both protected workflow histories (417795073/417795071) remain zero. This is
isolated fixture cleanup, with no production cleanup/takeover claim.
