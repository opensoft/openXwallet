# The fleet-pinned OpenSpec CLI in this repository

`openspec validate --strict` is the gate every spec delta passes and `openspec
archive` is the act that moves a ratified delta into canon — and until this
change, both ran here on whatever `openspec` happened to be on PATH. No commit
in this repository's history records which version adjudicated any archive.

This change vendors the fleet pin so that CI, at least, is answerable about
which tool ran. It is **rollout B** of `opensoft/openxFactory#754`, on Brett
Heap's rulings of 2026-09-07 — rollout `"Hybrid A+B"`, lane scope
`"openxFactory only; siblings via their lanes"`, the latter allowing that lane
to open the plain PRs in the three repositories that carry no `xfactory:` stack
pin and have no live lane of their own.

## What is here

| File | Role |
| --- | --- |
| `contracts/openspec-cli-pin.yaml` | the pin: package, version, npm SHA-512 integrity and SHA-1, tarball, rollback entry, and the estate's `dispositions:` block |
| `scripts/validate-openspec-cli-pin.py` | the consumer entrypoint — fetches the artifact, recomputes both digests, refuses on mismatch, installs, asserts the reported version, then runs `openspec validate … --strict` through it |
| `scripts/install-pinned-openspec-cli.py` | installs the verified binary and appends it to `$GITHUB_PATH`. An install, never a verdict |
| `.github/workflows/openspec-cli-pin-gate.yml` | runs the entrypoint with `--all --no-cache --tarball <the vendored artifact>` on every pull request to `main` |
| `tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz` | the pinned artifact itself, 477 381 bytes, vendored on Brett Heap's ruling of 2026-09-07 so the gate resolves it without a registry call. The file NAME carries the pin's SHA-1, so a bump cannot silently reuse the path |

Three of the four are **byte-identical** to their openxFactory originals below a
vendoring header block, and the fourth — the workflow — is byte-identical except
for ONE DECLARED DIVERGENCE, its final `run:` line and the comment block above it.
That is deliberate: a copy that can drift silently is worse than no copy, so drift
is one command away.

```bash
# drift check — from a checkout of this repository, with openxFactory reachable
OXF=../openxFactory   # any openxFactory checkout
diff <(tail -n +4 contracts/openspec-cli-pin.yaml)               <(git -C $OXF show 44d8fbaf7d977668973dcd116040c9405416c2ea:contracts/openspec-cli-pin.yaml)
diff <(sed '2,4d'   scripts/validate-openspec-cli-pin.py)        <(git -C $OXF show 44d8fbaf7d977668973dcd116040c9405416c2ea:scripts/validate-openspec-cli-pin.py)
diff <(sed '2,4d'   scripts/install-pinned-openspec-cli.py)      <(git -C $OXF show 44d8fbaf7d977668973dcd116040c9405416c2ea:scripts/install-pinned-openspec-cli.py)
diff <(tail -n +12  .github/workflows/openspec-cli-pin-gate.yml) <(git -C $OXF show 44d8fbaf7d977668973dcd116040c9405416c2ea:.github/workflows/openspec-cli-pin-gate.yml)
```

Empty output from the FIRST THREE means those files are exactly openxFactory's at
`44d8fbaf7d977668973dcd116040c9405416c2ea`. Any output is drift, and the fix is to
re-vendor from openxFactory rather than to edit anything here.

The fourth prints **exactly one expected hunk and nothing else** — the openXwallet
divergence declared in that file's own header: the `# ---- openXwallet DIVERGENCE`
comment block, and

```
<         run: python3 scripts/validate-openspec-cli-pin.py --all --no-cache --tarball tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz
---
>         run: python3 scripts/validate-openspec-cli-pin.py --all --no-cache
```

Anything BEYOND that hunk is drift. Verify the vendored artifact itself in the same
pass — the file name is the claim, and this recomputes it:

```bash
python3 - <<'EOF'
import base64, hashlib, pathlib
b = pathlib.Path("tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz").read_bytes()
print("integrity sha512-" + base64.b64encode(hashlib.sha512(b).digest()).decode())
print("shasum   ", hashlib.sha1(b).hexdigest())
EOF
# must equal `integrity:` and `shasum:` in contracts/openspec-cli-pin.yaml:
#   sha512-oFE2Lj7WVSc87nSibk6qe9HjHIOlxhcPAXbPey44DlLvJzBl5+9BZVrNiozOwv++CQhW+MG0kuP1XLZ/uQrrWw==
#   c844543999f673cdd72445879b86a4abea4c07ef
```

Nothing has to trust this doc for that: the gate recomputes both digests over these
bytes on every run and refuses `pin-integrity-mismatch` before installing anything.

## Why the estate's `dispositions:` are inert here

The pin's `dispositions:` block carries four accepted findings, each naming a
`repo:`. The entrypoint reads the validated tree's identity from
`git config --get remote.origin.url`, so in this repository every one of those
entries is **out of scope**: neither applied nor checked for staleness. The gate
here is therefore strict about this repository's own corpus and silent about
openxFactory's and codexFactory's, which is the behaviour the mechanism was
built for — no edit was needed to obtain it.

## What this delivers, and what it does not

**Delivered — the gate.** Pull requests to `main` are validated `--strict`
through a binary whose bytes were checked against a recorded content address.
The entrypoint and the installer are standard-library-only by design and import
nothing from openxFactory, so they run here unchanged.

**Deferred — governed archive routing.** openxFactory routes `openspec archive`
through `scripts/proposal-support.py`, which does far more than pick a binary:
it runs the origin gate, refuses a change with open task boxes, and packages
supporting documents into a deterministic bundle. That file is ~1900 lines, it
imports `doc_health.pin_sentinels` from openxFactory's `scripts/doc_health/`
package and it needs PyYAML, so lifting it would mean adopting openxFactory's
whole proposal substrate rather than the pin. It is not vendored here.

**Until this repository grows its own routing, archive through openxFactory's
wrapper from a checkout at the pinned commit.** It takes the consuming
repository's root as its first positional argument, and its read-only `verify`
subcommand was exercised against this repository while preparing this change:

```sh
OXF=../openxFactory                     # checked out at openxFactory 44d8fbaf7d977668973dcd116040c9405416c2ea
python3 $OXF/scripts/proposal-support.py . verify            # read-only
python3 $OXF/scripts/proposal-support.py . archive <change>  # the governed act
```

The narrower alternative — the pinned binary and nothing else, without the
origin gate or the bundle — is the installer:

```sh
"$(python3 scripts/install-pinned-openspec-cli.py 2>/dev/null)" archive <change>
```

That fixes *which version* archives. It does not supply the governance checks,
and it should not be mistaken for them.

## Making the check required

The workflow reports; it does not block. Selecting `openspec-cli-pin` as a
required status check is an operator act on a ruleset, and a check is not even
selectable until its workflow has reported once. That act is Brett's console act
and is deliberately not attempted here.

## Readiness of this repository's corpus

Measured 2026-09-07, before this change was written, by running openxFactory's
entrypoint with `--repo` pointed at a clean clone of this repository:

```
change/widen-register-reader-for-a-second-council
  ✗ [ERROR] review-authority-register-reader/spec.md: MODIFIED "Per-seat signing keys are recorded in the register and enforced by its reader" omits scenario(s) the current spec still has: "A seat is recorded twice".
  ✗ [ERROR] review-authority-register-reader/spec.md: MODIFIED "The register's breadth is bounded by invariants rather than a row count, and the key surface is bounded structurally" omits scenario(s) the current spec still has: "A second authority row is still refused".
Totals: 5 passed, 1 failed (6 items)
```

The same corpus is **clean under 1.2.0**, the version actually on PATH here
today: `Totals: 6 passed, 0 failed (6 items)`. So this is not corpus rot — it is
the strictness 1.12 added, and it is precisely the readiness gap that
openxFactory's own `prepare-openspec-1.12-readiness` packet existed to close and
that MedxFactory, AdxFactory and LedgerxFactory self-document as owed.

**This gate is therefore RED on the pull request that introduces it, and that
redness is the measurement rather than a defect in it.** The gate was not scoped
down, not made advisory, and not given a disposition to hide behind. Two lawful
exits exist and both belong to this repository's owner:

1. **Fix the delta** — copy the two named scenarios into the MODIFIED blocks in
   `openspec/changes/widen-register-reader-for-a-second-council/`. A MODIFIED
   requirement replaces its whole block, so 1.12 refuses to let an archive drop
   scenarios the current spec still carries.
2. **Disposition them** — add entries to `dispositions:` in
   `contracts/openspec-cli-pin.yaml` with `repo: openXwallet`, a `cited_to:`
   citation and a `ratified_by:` authority, the way openxFactory dispositioned
   the four declared renames it accepted. Both findings are of the *declared
   rename* family openxFactory's entries already cover, so if these scenarios
   were deliberately re-conditioned rather than dropped, this is the right
   instrument.

**RULED, and exit 1 was taken — in a separate pull request, not this one.** Brett
Heap, 2026-09-07T15:49:10Z, in session, by multiple choice, label verbatim:

> **"This lane authors the readiness fixes"**

opensoft/openXwallet#23 (`chore/openspec-1.12-readiness`) takes exit 1 as **two scenario
HEADINGS in the ratified delta and nothing else** — `One council records a seat
twice` → `A seat is recorded twice`, and `A second row does not resolve end to end`
→ `A second authority row is still refused`. Every requirement body, every
WHEN/THEN/AND bullet, the ADDED/MODIFIED/RENAMED structure, `.openspec.yaml`,
`proposal.md`, `design.md` and `tasks.md` are byte-unchanged, and it reads
`Totals: 6 passed, 0 failed (6 items)` at 1.12.0 and 6/6 at 1.2.0. That pull
request carries the reasoning for why each restored title is true of the block it
now heads, and the reading it invites a veto on.

**Exit 2 was NOT taken, and could not have been here.** A `dispositions:` entry
requires a `cited_to:` citation and a `ratified_by:` authority — and it would have
to be written into `contracts/openspec-cli-pin.yaml`, which arrives in this
repository vendored byte-identical from openxFactory under a `do not edit here`
header. An `openXwallet` entry belongs upstream, in openxFactory, and reaches this
tree by re-vendoring.

**Ordering, so nobody has to infer it: opensoft/openXwallet#23 lands FIRST.** This gate validates
the corpus of the tree it runs on, so it stays RED on this pull request until that
one is in `main` and these checks are re-run.

`openspec/` was not edited by THIS change — the readiness fix is opensoft/openXwallet#23's two
lines, deliberately kept out of the copy-in so each can be read on its own.

## One further finding, recorded not fixed

openxFactory's `proposal-support.py … verify` run against this repository
reports `unknown origin kind 'ruling'` for both
`add-composition-drift-cascade` and
`widen-register-reader-for-a-second-council`. The origin vocabulary this
repository uses and the one openxFactory's wrapper recognises are not the same
set. That matters only if this repository adopts the wrapper's archive routing,
which this change explicitly defers.

## Findings in the vendored code, recorded and NOT fixed here

Review of this change surfaced defects in the vendored files themselves. They are
recorded rather than patched, because a fix applied *here* would fork the
estate's one pin verifier into divergent copies and destroy the single property
that makes vendoring safe — that a `diff` against openxFactory is empty. They
belong upstream, in `opensoft/openxFactory`, and reach this repository by
re-vendoring:

- **`--path-mode` overstates what it checked.** The success message says the
  content address was verified, but that mode resolves `openspec` from PATH and
  only asserts the reported version; it never calls `verify_artifact()`. A
  rebuilt binary that still reports `1.12.0` gets a "verified" result. The gate
  workflow never uses `--path-mode`, so this cannot affect the check here.
- **`resolve_pinned()` can race on a shared cache directory** — one process can
  observe a prefix that another is still writing. The gate runs `--no-cache` on a
  fresh runner, so this cannot affect the check here.
- **`resync_runbook:` and the refusal trailer name `docs/contract-versioning-policy.md`,
  which lives in openxFactory and not in this repository.** The value is declared
  metadata and the trailer is a fixed string; neither is read as a path by any
  code, so nothing breaks — but a reader following the trailer from here finds
  nothing. The pin's own re-vendoring runbook for this repository is this
  document.
- **Comment counts inside the refusal-code block are inconsistent** with the tuple
  they describe.

## SonarCloud

`SonarCloud Code Analysis` fails on the pull request that introduces this change,
on `new_security_rating`. Every finding is in `scripts/validate-openspec-cli-pin.py`
— the vendored file — and they are of two kinds: `python:S4790` on the SHA-1
digest, and the `pythonsecurity:S870x` family on CLI arguments reaching
`subprocess` and the filesystem.

Neither kind is fixable here without breaking byte-identity, and the first is not
a defect at all: npm publishes a SHA-1 `shasum` alongside the SHA-512 integrity,
and checking both is the whole function of a content-addressed pin. Suppressing
or rewriting them here would fork the verifier. SonarCloud is not a required
status check in this repository.

## Rule 4 after the vendoring — RULED, done, and one residual named

`AGENTS.md` states, among the rules that are not negotiable here:

> **Every gate is offline.** No check reads the network, an upstream tree, or
> `contracts/manifest.yaml`. The live manifest cross-check is a sync-time
> obligation.

The first version of this gate broke it: `resolve_pinned()` runs `npm pack` against
`registry.npmjs.org` on every pull request, so a registry outage made the check
refuse before it validated anything. The Codex review of the pull request that
introduced this file raised it and was right.

**RULED.** Brett Heap, 2026-09-07T15:49:10Z, in session, by multiple choice, label
verbatim:

> **"Vendor the tarball into the repo"**

— *the content-addressed 1.12.0 tarball is committed and the gate's installer reads
it locally, integrity still verified by SHA-512.* Exit 2 of the three this document
previously recorded. It is done, in
`tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz`,
and the workflow passes it with `--tarball`.

**No verification was given up to buy it.** `--tarball` is the verifier's own flag,
and `main()` routes it through the SAME `verify_artifact()` as a fetched artifact:
the SHA-512 and the SHA-1 in `contracts/openspec-cli-pin.yaml` are recomputed over
the vendored bytes and a mismatch refuses `pin-integrity-mismatch` BEFORE anything is
installed. The vendored file was obtained with `npm pack @fission-ai/openspec@1.12.0`
and both digests were checked against the pin before it was committed:

```
bytes      477381
integrity  sha512-oFE2Lj7WVSc87nSibk6qe9HjHIOlxhcPAXbPey44DlLvJzBl5+9BZVrNiozOwv++CQhW+MG0kuP1XLZ/uQrrWw==
shasum     c844543999f673cdd72445879b86a4abea4c07ef
```

Both equal `contracts/openspec-cli-pin.yaml`. The name of the file carries the SHA-1,
so a bump that forgets to move the path collides with a name that is already taken.

### The residual, measured rather than argued

**The artifact is vendored. Its DEPENDENCY CLOSURE is not, and that half of rule 4 is
still open.** `install_artifact()` installs the verified tarball with
`npm install --global --prefix … --ignore-scripts <tarball>`, and
`@fission-ai/openspec@1.12.0` declares TEN runtime dependencies — `@inquirer/core`,
`@inquirer/prompts`, `chalk`, `commander`, `diff`, `fast-glob`, `ora`, `yaml` and
`zod` at CARET RANGES, plus `cross-spawn` pinned exactly at `7.0.6` — all of which
npm resolves from the registry. (openxFactory's `install_artifact()` docstring says
"nine dependencies … declared at caret ranges"; nine is the caret-ranged count, ten
is the total, and both are right about different things.) **The caret ranges are a
second finding, not only an offline one: the code this gate executes can change when
a dependency is republished, with no movement in the pin.** openxFactory's pin header
states that shortfall in full and `--ignore-scripts` mitigates rather than repairs it.
The CLI genuinely needs the closure: `node package/bin/openspec.js --version` on the unpacked
tarball alone fails `ERR_MODULE_NOT_FOUND`.

Run in a network namespace with **no** network and a **cold** npm cache — which is
what a fresh GitHub runner is — the gate still refuses:

```
$ unshare -rn env npm_config_cache=<empty dir> \
    python3 scripts/validate-openspec-cli-pin.py --all --no-cache \
    --tarball tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz
REFUSE pin-unresolvable: installing the verified artifact into /tmp/openspec-cli-pin-…/prefix
failed (exit 1, executable absent): npm error code EAI_AGAIN
npm error request to https://registry.npmjs.org/@inquirer%2fcore failed, reason: getaddrinfo EAI_AGAIN
$ echo $?
2
```

The same command with **no** network and a **warm** npm cache passes end to end —
`Totals: 6 passed, 0 failed (6 items)`, exit 0 — which is the proof that the ARTIFACT
half is genuinely offline now: nothing was fetched, and the refusal above is about the
dependencies alone.

**What is missing, stated precisely, because it is an openxFactory follow-on and not
a thing this repository may fix.** `scripts/validate-openspec-cli-pin.py` has
`--tarball` for the artifact and **no equivalent for the artifact's dependency
closure**, and neither of its two resolution paths is offline on a cold cache:

* `--tarball` skips `fetch_artifact()` but ALWAYS calls `install_artifact()` and never
  consults the install cache;
* the cache path (`--cache-dir` / `OPENSPEC_CLI_PIN_CACHE`, prefix
  `<cache>/@fission-ai__openspec-1.12.0-<shasum>/` stamped `.pin-verified`) reuses an
  install, but `resolve_pinned()` reaches it only AFTER `fetch_artifact()` has run, so
  it cannot be pre-seeded without a registry call.

Either of two additions would close it, and both belong upstream: let `--tarball`
honour `cache_root` the way `resolve_pinned()` does, so a pre-seeded, digest-stamped
prefix is used as-is; or add an explicit `--prefix`/`--node-modules` mode that accepts
an already-installed, stamped tree. Vendoring the installed tree here instead is not a
real option — it is 20 MB against the artifact's 477 KB, and nothing in the vendored
installer would look at it.

**So the honest statement of where rule 4 stands:** the referent of the pin is now
verified and resolved entirely from this tree, which is the part the rule is about and
the part the ruling ordered. The gate still needs the registry to assemble the CLI's
dependency tree, exactly as `pytest-suite.yml` and every `npm install` in this
repository do. That is recorded here rather than left to be discovered, and it is
carried to opensoft/openxFactory#754.

Recorded by lane openxfactory-1 for opensoft/openXwallet#20 and
opensoft/openxFactory#754. Raised by the Codex review of the pull request that
introduced this file, and ruled by Brett Heap on 2026-09-07.
