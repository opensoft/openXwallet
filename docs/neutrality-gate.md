# The neutrality gate

`scripts/neutrality-gate.py` is task 5.4 of `split-openwallet-neutral-core`. It
is the check behind `design.md` D5's central claim: the adapter loads the
pinned openWallet core in process and adds rule (t) and the register reader
at extension points, and so "on any tree, the composed run's output is
byte-identical to the pre-split validator's". D7's proof, part three, calls
for this gate to come back empty over the composed adapter. The gate runs the
claim instead of restating it.

## What it compares

| Side | What runs | Where its `ROOT` is |
| --- | --- | --- |
| **baseline** | `scripts/validate-openxwallet.py` at the named carve commit `90111df262d6f54f7e82651d860adc12345f83f4`, read as raw git blobs | a temporary tree holding that commit's `contracts/` beside it, so its corpus, schemas and vendored envelope resolve there |
| **composed** | this repository's `scripts/validate-openxwallet.py`, run where it stands | after the rebuild, the core's `ROOT` is `openWallet/code` |

Both sides get the same argv in the same working directory, once plain and once
with `--strict`: each tree of targets (i) and (ii) in both modes, and each suite
invocation of target (iii) as the suite gave it and again with `--strict`
toggled. A tree **passes** when stdout is byte-identical in both modes and the
exit codes are equal. stderr is shown but not compared, because a
validator's own refusals name its own `ROOT`, and the baseline's `ROOT` is a
temporary directory.

## The three targets

1. **This repository's tree**, scanned the way `wallet-validation` scans it:
   the working directory is the root and the argv is `.`.
2. **An export of openxFactory's live `governance/` tree**, passed as
   `--openxfactory-export DIR`. It is run locally and recorded as evidence;
   CI never runs it (see "Target (ii)" below).
3. **Every fixture tree the test suites build.** This covers the kept suites
   under `tests/` and the moved suites under `openWallet/code/tests/`. Each
   suite builds its trees under pytest's `tmp_path` and runs the validator as
   a subprocess at `REPO_ROOT / "scripts" / "validate-openxwallet.py"`. The
   gate therefore mirrors each suite into a temporary root:
   - the test files are copied;
   - every other top-level entry is linked;
   - a **shim** stands at `scripts/validate-openxwallet.py`.

   For each invocation, the shim runs both validators twice: over the argv
   as given, and with `--strict` toggled (added where the suite left it out,
   removed where the suite put it in). It records each pair as one JSON line
   carrying its `mode` (`plain` or `strict`) and whether it is the one
   `replayed`, and then replays the as-given composed run (stdout, stderr
   and exit code). The suite therefore asserts on exactly what the composed
   adapter says to what it asked, and every fixture tree is still compared in
   both modes, whichever one its suite asked for. The suite's own pass or
   fail is printed as information. The verdict comes from the records, both
   modes of every invocation: every one must be identical, and a suite whose
   records do not pair refuses. Each suite's line reads `N invocation(s) × 2
   modes`.

   A suite counts as a target when one of its files contains the quoted literal
   `"validate-openxwallet.py"`. Suites that never invoke the validator are
   listed as skipped, with that reason. The gate's own suite is also skipped,
   because it drives toy validators.

## The one declared new line

Compared with the pre-split run of this tree (D0's output at `b7c6e0b`), target
(i) gains exactly one line:

```
note  nested repositories pruned (not adjudicated): openWallet
```

The rebuild mounts openWallet as a nested gitlink, and the wallet-v1.1 sweep
prune finds its `.git`. This line is **not** a difference between the
baseline and the composed adapter: the carve-commit validator has the same
prune and prints the same line over the same tree. The gate reports which
side printed it. D5 declares the line so that nobody mistakes it for drift.
A consumer's output does not change, because a consumer's sweep already
prunes `openXwallet/` whole.

## Before the shed: one expected difference

`repo_scan` skips the custody registry when its path is the validator's own
`CUSTODY_REGISTRY_PATH`, which is derived from `ROOT`
(`scripts/validate-openxwallet.py:3442` at the carve commit). Until the shed
(task 5.5), this tree still contains
`contracts/openxwallet/openxwallet-custody.registry.yaml`:

- The validator at `scripts/` has this tree as its `ROOT`, so it skips the
  registry.
- The baseline's `ROOT` is elsewhere, so it counts the registry as a record.

Target (i) then shows `1 openxWallet artifact(s) validated` against `0`. The
gate reports this as a difference and prints a note that names the cause.

After the shed, the registry is gone from this tree. The composed core's
`ROOT` is then `openWallet/code`, which the sweep prunes whole, so no target
scans either validator's registry. The test's real-repository seat skips
loudly until then.

## Help invocations

`--help` scans no tree. argparse prints the module docstring, and D3 splits
that docstring between the core and the adapter on purpose. So a help
invocation runs once, as given, and its record is reported, with its own
identity count, and is **kept out of the verdict**.

## Running it

```bash
python3 scripts/neutrality-gate.py                      # targets (i) and (iii)
python3 scripts/neutrality-gate.py --no-suite-trees     # target (i) only
python3 scripts/neutrality-gate.py --report run.json    # plus a JSON summary
```

| Flag | Meaning |
| --- | --- |
| `--carve-commit SHA` | the baseline's commit (default: the named carve commit); 7 to 40 hex characters, checked before git sees it |
| `--openxfactory-export DIR` | target (ii); `DIR` must **contain** `governance/` |
| `--openxfactory-export-commit SHA` | the openxFactory commit the export was taken at, recorded in `--report` |
| `--no-suite-trees` | skip target (iii) |
| `--report PATH` | write a JSON summary: the result, the revision tested (HEAD, uncommitted tracked changes, the `openWallet` and `code` checkouts), the carve commit, the baseline blob, the composed adapter's sha256, every target and mode with both exit codes, every suite's counts and differences, and every skip |
| `--keep` | keep the run's temporary tree and print where it is |

| Exit | Meaning |
| --- | --- |
| 0 | every target in every mode, and every suite record, identical |
| 1 | some difference; each one is printed, with a unified diff of stdout |
| 2 | a refusal, where the run cannot give an answer (cases below) |

A run refuses (exit 2) when:

- the carve commit is not in this checkout's history;
- the adapter is missing;
- a validator refuses at self-test (its own text is printed verbatim);
- a target run exits 2 on either side;
- a suite records no tree invocation, its records do not pair one plain with
  one strict run, or its pytest run ends in a code other than 0 or 1;
- the export holds no `governance/`.

### Uninitialized submodules

The composed adapter needs both levels of openWallet. In `.github/workflows/neutrality-gate.yml`,
the init steps are:

```bash
git submodule update --init openWallet
git -C openWallet submodule update --init code
```

These two levels are always named. A recursive init is never used, because it
would also fetch the spec leg, which the gate does not read (design D6).

If either level is missing, the adapter refuses with exit 2 and names the
remediation, and the gate prints that refusal verbatim. The moved suites are
skipped, loudly, wherever `openWallet/code` is not initialized.

### Full history

The baseline comes from the carve commit, so a depth-1 checkout makes the gate
refuse. The message names `fetch-depth: 0`, following the precedent of
`.github/workflows/carve-manifest.yml`. In `pytest-suite`'s depth-1 run, the
test's real-repository seat skips loudly and names `neutrality-gate.yml`.

## Target (ii): the openxFactory export, as evidence

The export contains the operator's email and the seats' keys. It is **never
committed here**, and CI never runs it, because every gate here is offline
(AGENTS.md rule 4). The method is the one the widen packet used
(`widen-register-reader-for-a-second-council`, design D0 and D6): take a probe
copy of the live tree, run it locally, and record the output.

1. Name the openxFactory commit **before** fetching: 40 hex characters,
   normally `main` at the time of the run.
2. Fetch that commit's tarball into a new, empty directory, and extract only
   `governance/` into another new, empty directory:

   ```bash
   SHA=<the openxFactory commit, 40 hex>
   WORK=$(mktemp -d)
   mkdir "$WORK/tarball" "$WORK/export"
   gh api "repos/opensoft/openxFactory/tarball/$SHA" > "$WORK/tarball/oxf.tar.gz"
   tar -xzf "$WORK/tarball/oxf.tar.gz" -C "$WORK/export" \
       --strip-components=1 --wildcards '*/governance/*'
   ```

3. Run the gate over it from this repository's root:

   ```bash
   python3 scripts/neutrality-gate.py --no-suite-trees \
       --openxfactory-export "$WORK/export" \
       --openxfactory-export-commit "$SHA" \
       --report "$WORK/neutrality-report.json"
   ```

4. Record the openxFactory commit and the gate's summary line in the table
   below. Then delete `$WORK`.

## Evidence

Each row is one run of the gate. Record the openXwallet revision the run
tested and the openxFactory commit of the export it read. The orchestrator
adds rows after the composed run.

| Date | openXwallet revision | Carve commit | openxFactory export commit | Targets | Result |
| --- | --- | --- | --- | --- | --- |
| _pending_ | _pending: the composed, shed branch_ | `90111df262d6f54f7e82651d860adc12345f83f4` | _pending_ | (i), (ii), (iii) | _pending_ |
