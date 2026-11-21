# T013P05 isolated measurement implementation

Status: local candidate; full/native frozen qualification and cleanup pending.
The existing feature017 T013P05 row is the sole implementation task. The source
basis is the owner-ratified and ordered-landed factory #1359 / adapter #100 pair;
this new implementation has no publication, hosted CI or source acceptance yet.

## Producer and wire

`azure_composition/local_host.py` holds an explicitly selected local observer and
mTLS measurement server. The direct internal-v2 request has the accepted 12 keys,
including a fresh 64-character lowercase hexadecimal request nonce, and is bounded
to 4,096 canonical bytes. The direct response contains exactly the existing 21
fields plus that nonce, bounded to 16,384 complete canonical bytes. Configuration
and policy are both carried in full. The unchanged PrivateHttps transport remains
the only client exchange; no wrapper, fallback or old ObservationClient change.

The producer retains the original HostAgent, WorkerSpec, StageStore and persistent
launch-owner executor. Kernel PID/start/boot, UID/GID, capabilities, no-new-privileges,
seccomp, session, roots, files, namespace and original creator-thread child ownership
are checked. Original manager journal reads occur before and after measurement.
A newly constructed manager cannot adopt the process by copying child references.
The selected effective control peer comes from the mTLS certificate and protected
peer approval, never a request role. A valid worker certificate is denied403;
the approved control sends the identical request body and succeeds200.

A pre-existing selected nonce ledger is consumed before measurement. Loss or
cancellation leaves it consumed; there is no initialize, reset or retry route.
Its object, directory and durable identity are retained. Eight bounded server
slots, two-second socket/TLS timeouts, a ten-second handler ceiling and sanitized
errors limit local work. Server timers are subordinate to caller/peer/plan/stage
and lease expiry, never a joined controller Decision or renewed authority.

## Controller and opaque verified handoff

`azure_composition/remote_evidence.py` freezes origin, certificate pins, selected
scope, material bytes, independent credential/approval origins and expiry.
Each measurement charges the original private-read ledger. SendClock is only a
view of the original Decision: it enforces the original fixed interval after
PrivateHttps final material reads and immediately before GO. There is no new
clock, budget, ledger, authority or transport branch.

RemoteFinalizer retains the original finalization Decision/ledger and at most
two joined controller members. Six current-plan and six current independent lease
reads surround three actual observer RPCs: primary, independent, primary refresh.
High-water counts, original deadlines/end and callback identities are guarded.
Approved worker roots are PurePosixPath strings and are never resolved on the
controller filesystem. Configuration and policy are independently recomputed in
full from approved artifacts, projections, process composition and all late fields;
matching copied digests are insufficient. Intermediate Observed data is authenticated
and canonical but generation approval belongs to the final verified handoff.
VerifiedRemote exposes an opaque sealed capability with private complete bytes and
provenance. It is not the old FinalizedPlan and provides no P08 admission route.

## Connected eligibility and retained limits

The fully network-backed PlanFactReader route exhausts private12 before added
measurement reads; an additional read refuses at13. Four accounting diagnostics
and its guard-removal counterfactual retain that route-specific incompatibility.
There is no automatic fallback. The existing PlanBindings local-fact interface
permits an explicit trusted local current-state capability. The eligible isolated
composition uses actual protected file reads with inode/owner/mode/current checks,
all 12 current-fact reads and all six fresh protection observations preserved.
Revocation or replacement after I/O refuses.

Two independent observer PKIs/origins, actual original process/journal evidence and
full byte derivation fit the unchanged ledger: private9/12 (six current lease plus
three observer RPCs), protection12/18 and aggregate GitHub12/28. Six original manager
journal reads are current. Connected proofs take approximately 2.76-3.10 seconds
inside the original ten-second interval; configuration is 5,247 bytes and policy
2,870 bytes, with the complete canonical response within16,384. Those are isolated
measurements, not deployed performance or administrator-separation claims.

## Qualification record before final freeze

All99 focused cases pass together in471.25seconds, with zero failures/errors/skips.
Fourteen isolated weakened guard copies each fail the intended assertion while
the unmodified14-case baseline passes. They cover nonce, canonical/closed/aggregate
body, original manager, kernel namespace, consume-before-measure, full derivation,
selected generation, late current state, immediately-before-GO interval, opaque
state, effective source and private-read charging. No product mutation is retained.
Actual collection is3,438 full parents plus11 existing subtests and3,016 native
cases. The new module's99 sorted identities hash to
`e9aab3cc9cd63e7534033174c50e0619451f88453feaa76f3ca6f8993474bcea`.
All old module counts/digests/identities/order and anchor prefixes remain unchanged.

Earlier diagnostics are retained without qualification claims: initial78-case run
had77 passes and one corrected test expectation about intermediate generation
approval; the targeted follow-up passed24 with74 deliberately deselected. Prototype
R3 had an inherited setup error; R4 collected no tests due to a diagnostic writer
syntax error. R5 passed allfive connected eligibility cases before product copy.
The selected real P05 elapsed clock starts once after independent fixture setup,
before every P05 Decision, and is never reset during the transaction.

After the focused controls, unused imports and composite assertion formatting
were cleaned without changing test identities or semantics. Final full/native
runs must bind the resulting committed source, not the earlier focused hash.

## Authority and completion boundary

Provider/admin payloads remain explicit isolated doubles. The tested protected
local capability selects no operational host, issuer, administrator, credential,
actual appointment or accepted_commit. Default operational refusal and every old
profile, wire, workflow, budget, dependency pin and prior case identity remain.
Only isolated T013P05 is commissioned. P06-P09, setup, protected dispatch, live
human/consumer acceptance, new source publication/review and source ratification
remain separate. Feedback deferred; historical blocked writes unreplayed.


## Fixture isolation correction before final qualification

The first parallel full attempt passed560 cases before a P05 positive call
refused; its native companion had an inherited staging setup error and was
intentionally interrupted after that error. A subsequent sequential full attempt
passed630 cases, then its inherited public staging HTTP setup timed out before
the P05 Decision existed. These are failed/diagnostic attempts, not qualification.
Two targeted structural cases and all28 wire diagnostics pass; they do not prove
the cause of the original generic measurement refusal. No clock or budget is
expanded to erase these results.

P05 fixture setup now calls the existing StageController.handle protected
interface locally with the same three selected context inputs and signed fixture
token. This retains selected_plan authentication, fresh grant/correlation, durable
controller/host stores, independent cleanup acknowledgement and real mTLS
HostClient registration/start/status. It avoids nesting this independent setup
inside P04's public HTTP handler timer. The original HostAgent launch owner, real
worker and kernel evidence remain. Existing P04 transport tests are unchanged.
The real P05 elapsed clock still starts exactly once after setup and authenticated
generation selection; its ten-second Decision, one-second fixed request interval,
all per-request deadlines and every read budget remain unchanged.

Seven targeted connected/denial/manager/wire/cancellation eligibility cases pass
with92 intentionally deselected using an external local-controller fixture copy.
This is setup-locality evidence only; full/native qualification must bind the
corrected candidate. Product runtime, transport and matrix bytes are unchanged.
