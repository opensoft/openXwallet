# openXwallet #73 source acceptance

Status: implementation in progress; main acceptance is pending.

The [original issue and gate record](sonar73-before.json) preserves all eight
finding identities, six original Sonar way conditions and profiles. The
oldest retained main analysis (2026-08-27, revision 63f5a1ad) was verified as
an ancestor of main d832709 and selected as the manual baseline. All ten
retained analyses remain. No date was advanced to hide retained changes.

The neutral source repair is [openWallet-code #6](https://github.com/opensoft/openWallet-code/pull/6),
landed as b7c8ca1e0f9bb58674a12ffef89bf5dfc92cc58c.
All nine standard local independent review roles plus CI/build found no
remaining actionable issues. Published pytest, strict/plain validation and
Sonar passed; Sourcery is separately skipped.
The public RFC 8037 test-vector provenance and deliberately invalid replacement
are recorded in that PR and its docs. The eight manifest-owned contract
artifacts remain unchanged; corpus and validators are commit-addressed.
The existing wallet-v1.6 tag and separate future v1.7 train remain untouched.

Shared checksum repair: [openXfactory #1331](https://github.com/opensoft/openXfactory/pull/1331).
Neutral spec consumption: [openWallet-spec #12](https://github.com/opensoft/openWallet-spec/pull/12).
Provider main admission, shape repair, compatible root/adapter pins, final
complete-source coverage and exact-main gate verification remain pending.

The coverage verifier is adapted from openXfactory@a31e2060e61fcec47a818ccdcd4d8c675a440505.
It binds every nested revision, exhaustive production Python inventory,
unchanged source/configuration and actual branch-coverage reports. Its
54 evidence and provider-boundary tests preserve zero-hit files and refuse missing/forged data,
lost parent execution, changed nested pins and incomplete/weakened gates.
No coverage hits or file identities are synthesized.

The seven primary checkout heads, status, working-diff and staged-diff hashes
still match the prior P1 closeout at the preservation readback. Current bench
session/pane inventories are retained for final comparison. Older session
inventories differ independently; this repair has sent no session input,
restarted no session/bench and restored or overwritten no owner work.


The additional source-conformance job executes both owning legs and immutable
provider assertions against the actual copied files. The CLI provider has 193
exact assertions per consumer copy; the shape selection has 2,223 exact assertions
across 25 modules. Collection fingerprints and per-phase reports refuse omissions,
deselection, expected failures and unrecorded skips. Provider roots remain the
source of their fixtures; production file identities and coverage hits are not
rewritten.

Both jobs prepare the same four-repository source/configuration snapshot. The
analysis job refuses missing or changed snapshots, any failed/missing JUnit
report and missing real branch-data shards before combining actual measurements.
All owned Python files, including zero-hit files, remain in the final inventory.

Upstream supplied-artifact repair is openXfactory #1333 at e0e0b9a31ec8f4d5ec2d611d373ce0a918abb5de;
shape repair is openRepoShape #1331 at 55cc8aeef4a96985d76cddc7a0ee834c97909860.
These remain prepared candidates pending main admission. The current neutral
root candidate is openWallet #13 at 6b0395d37ba8786bc2ea802abbdb2e5e8a594d54;
the adapter will be repinned to accepted publication before landing.


Qualification correction: collection and combination both retain absolute
source identities. Relative-name combination can auto-alias a nested scripts/
path to an outer scripts/ path. The real startup regression runs same-named
sources from the assembly, code and spec working directories and requires their
distinct branch hits to remain separate in the ordinary relative XML/JSON report.
Earlier relative-name data is retained as failed diagnostic evidence and is not
eligible for the final scan.

The privilege launcher passes each fresh task-owned TMPDIR after sudo starts:
sudo's initial secure loader removes that variable before its preserve list.
The original privilege controls, pytest assertions and timeouts remain.


The source-conformance job additionally runs both actual pinned OpenSpec corpora
through the supplied committed tarballs under immutable setup-node v4 / Node 22.
Each currently passes all seven strict items; the existing independent CLI gate
is retained. Both entrypoints still verify SHA-512 and the unchanged 80-package
lock before installation, with lifecycle scripts disabled.
