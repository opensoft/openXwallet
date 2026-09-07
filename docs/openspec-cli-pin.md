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
| `.github/workflows/openspec-cli-pin-gate.yml` | runs the entrypoint with `--all --no-cache` on every pull request to `main` |

All four are **byte-identical** to their openxFactory originals below a
vendoring header block. That is deliberate: a copy that can drift silently
is worse than no copy, so drift is one command away.

```bash
# drift check — from a checkout of this repository, with openxFactory reachable
OXF=../openxFactory   # any openxFactory checkout
diff <(tail -n +4 contracts/openspec-cli-pin.yaml)               <(git -C $OXF show 44d8fbaf7d977668973dcd116040c9405416c2ea:contracts/openspec-cli-pin.yaml)
diff <(sed '2,4d'   scripts/validate-openspec-cli-pin.py)        <(git -C $OXF show 44d8fbaf7d977668973dcd116040c9405416c2ea:scripts/validate-openspec-cli-pin.py)
diff <(sed '2,4d'   scripts/install-pinned-openspec-cli.py)      <(git -C $OXF show 44d8fbaf7d977668973dcd116040c9405416c2ea:scripts/install-pinned-openspec-cli.py)
diff <(tail -n +6   .github/workflows/openspec-cli-pin-gate.yml) <(git -C $OXF show 44d8fbaf7d977668973dcd116040c9405416c2ea:.github/workflows/openspec-cli-pin-gate.yml)
```

Empty output from all four means this vendored closure is exactly openxFactory's
at `44d8fbaf7d977668973dcd116040c9405416c2ea`. Any output is drift, and the fix is to re-vendor from
openxFactory rather than to edit anything here.

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

Neither was done here. Writing a disposition requires a citation and a named
authority, and inventing one would be worse than a red check.

`openspec/` was not edited by this change.

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

## An unresolved conflict with this repository's rule 4

`AGENTS.md` states, among the rules that are not negotiable here:

> **Every gate is offline.** No check reads the network, an upstream tree, or
> `contracts/manifest.yaml`. The live manifest cross-check is a sync-time
> obligation.

**This gate reads the network.** `resolve_pinned()` runs `npm pack` against
`registry.npmjs.org` on every pull request, so a registry outage makes the check
refuse before it validates anything. That is not an oversight in the workflow —
it is inherent to what the pin refers to. `contract_pin.yaml`'s referent is a
file already in this tree, which can be hashed offline; the OpenSpec CLI pin's
referent is a published npm tarball, and there is no way to verify bytes you have
not fetched.

The conflict is therefore real and is **not resolved by this change**. Three
exits exist, and choosing between them is this repository's call, not the
rollout's:

1. **Read rule 4 as scoped to contract pins** — the rule was written about
   `contract_pin.yaml` and the manifest cross-check, and a tool pin is a
   different kind of referent. This is the smallest change and needs the rule's
   wording amended to say so.
2. **Vendor the tarball** and pass it with `--tarball`, which the verifier already
   supports. That restores offline operation at the cost of committing a
   multi-megabyte binary artifact and re-committing it at every bump.
3. **Decline the gate here** and keep the pin as documentation only, routing
   archives through openxFactory's wrapper as described above.

Recorded by lane openxfactory-1 for opensoft/openXwallet#20 and
opensoft/openxFactory#754. Raised by the Codex review of the pull request that
introduced this file.
