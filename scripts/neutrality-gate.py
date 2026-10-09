#!/usr/bin/env python3
"""THE NEUTRALITY GATE: the carve-commit validator against the composed
adapter, byte for byte (`split-openwallet-neutral-core`, `design.md` D5
"NEUTRALITY BY CONSTRUCTION" and D7 "The proof" part three; `tasks.md` 5.4).

WHAT THIS FILE PROVES. D5 composes the adapter in process over the pinned core
so that "on any tree, the composed run's output is byte-identical to the
pre-split validator's". A property nobody runs is a claim, not a floor, so this
runs it. The PRE-SPLIT VALIDATOR is the BASELINE: `scripts/validate-openxwallet.py`
at the NAMED CARVE COMMIT (`90111df262d6f54f7e82651d860adc12345f83f4`, task
2.3), read as raw git blobs and written into a temporary tree beside that
commit's own `contracts/`. It derives `ROOT` from its own location, so its
corpus, its schemas and the vendored envelope resolve inside that tree and
nowhere else. The COMPOSED ADAPTER is this repository's
`scripts/validate-openxwallet.py`, run where it stands. Both run over the SAME
tree with the SAME argv, plain and `--strict`, and a tree PASSES when, in both
modes, stdout is BYTE-IDENTICAL and the exit codes are EQUAL.

THE THREE TARGETS (D5):

  (i)   THIS REPOSITORY'S TREE, scanned the way `wallet-validation` scans it:
        the working directory is the root and the argv is `.`.
  (ii)  AN EXPORT OF openxFactory's LIVE `governance/` TREE, given as
        `--openxfactory-export DIR`, where DIR holds `governance/`. It is never
        committed here and never run in CI: it carries the operator's email
        and the seats' keys, and every gate here is offline (AGENTS.md rule 4).
        This is the widen packet's method (`widen-register-reader-for-a-second-council`,
        design D0 and D6): a probe copy of the live tree, run locally, its
        output recorded as EVIDENCE in `docs/neutrality-gate.md`.
  (iii) EVERY FIXTURE TREE THE TEST SUITES BUILD: the kept suites under
        `tests/` and the moved suites in the code leg under
        `openWallet/code/tests/`. They build their trees under pytest's
        `tmp_path` and drive the validator as a SUBPROCESS at
        `REPO_ROOT / "scripts" / "validate-openxwallet.py"`, with `REPO_ROOT`
        taken from the test file's own location. So each suite is MIRRORED into
        a temporary root holding the suite root's TRACKED TREE (`git ls-files`)
        as real directories and COPIED files, so that a test that scans its
        mirrored root walks and reads what a scan of the real root does, and
        `Path.resolve()` in a copied test stays inside the mirror. `os.walk`
        never descends a directory LINK, so a mirror of linked directories
        would adjudicate nothing on either side and compare two empty reads.
        Three things are not copied. The suite's own directory is copied
        WHOLE, so a test file not yet added still runs. A GITLINK
        (`openWallet`) is LINKED: the sweep prunes it through the link exactly
        as it prunes the real mount, and the composed adapter reaches the
        real one through its own path, because the shim calls the real
        adapter. Each file under `scripts/` is a FILE link, because a script
        resolves its ROOT from its own location and holds no YAML a scan
        reads. At the mirror's `scripts/validate-openxwallet.py` stands a
        SHIM. For each
        invocation the shim runs the baseline and the composed adapter TWICE
        in the same working directory: over the argv AS GIVEN, and over it
        with `--strict` TOGGLED (added where the suite left it out, removed
        where the suite put it in). So every fixture tree is compared plain
        AND `--strict`, as targets (i) and (ii) are, whichever mode the suite
        happened to ask for. It appends one JSON record per mode to the run's
        report, each carrying its `mode` ("plain" or "strict") and whether it
        is the one `replayed`, and REPLAYS the as-given composed run (stdout,
        stderr and exit code), so the suite sees what the composed adapter
        says to exactly what it asked. The suite's own pass or fail is printed
        as INFORMATION; the verdict is the records, BOTH modes of every
        invocation, every one identical.

THE ONE DECLARED NEW LINE. Relative to the PRE-SPLIT run of THIS tree (the
output D0 recorded at `b7c6e0b`), target (i) gains exactly one line, which D5
declares rather than hides:

    note  nested repositories pruned (not adjudicated): openWallet

The adapter rebuild mounts openWallet as a nested gitlink, and the sweep prune
(wallet-v1.1) finds its `.git`. It is NOT a baseline/composed difference: the
carve-commit validator carries the same prune and prints the same line over
the same tree. So the gate sees it on both sides, reports where it appears,
and names it here so the new line is never mistaken for drift.

THE PLAN'S CALLS (task 5.4 left these open; each is recorded here):

  * The verdict is stdout bytes and the exit code. stderr is captured and
    shown, never compared: a validator's own refusals name its own `ROOT`, and
    the baseline's is a temporary directory.
  * A HELP invocation (`-h`, `--help`) adjudicates no tree. argparse prints the
    module docstring, which D3 deliberately splits between core and adapter,
    so a help invocation runs once, as given, and its record is reported with
    its own identity flag and kept OUT of the verdict. Every other record, in
    both modes, is in it.
  * Before any target, each validator runs once with no path (self-test
    only). Exit 2 there REFUSES the whole run, and the validator's own text is
    printed verbatim. An uninitialized `openWallet/` or `openWallet/code/`
    therefore surfaces as the adapter's own named refusal: never a
    difference, and never masked.
  * Over targets (i) and (ii), exit 2 on either side is a refusal, not a
    comparison: two runs that both failed to adjudicate would compare equal
    and pass vacuously. In a suite record exit 2 is compared like any other
    code, because suites provoke refusals on purpose.
  * A suite is in target (iii) when one of its files spells the quoted literal
    `"validate-openxwallet.py"`, the path it drives. This gate's own suite is
    excluded: it builds trees for toy validators. A suite that names the
    validator but records no tree invocation, or whose pytest run ends in an
    exit code other than 0 or 1, is a refusal, because a target that proves
    nothing is not a pass.
  * The moved suites run only where `openWallet/code` is initialized, and are
    skipped LOUDLY otherwise. They were written for the standalone core, so
    where the composed run differs from the core BY DESIGN (the corpus note
    reads 21 / 45 / 13 of 13 composed, 21 / 42 / 11 of 11 standalone) their
    own assertions fail. That is information, as it is for every suite.
  * The carve commit must be a commit this checkout CARRIES and an ANCESTOR of
    HEAD, the rule `scripts/validate-carve-manifest.py` applies
    (`carve-revision-mismatch`). A depth-1 checkout does not carry it, hence
    `fetch-depth: 0` in `.github/workflows/neutrality-gate.yml`, on the
    precedent of `.github/workflows/carve-manifest.yml`.
  * The shim is generated for each run: a stub that loads THIS file by path
    and calls `shim_main`, so the gate and its shim are one file.
  * Every child runs with `PYTHONDONTWRITEBYTECODE=1` and with `TMPDIR` at a
    directory inside the run's temporary tree, so a temporary file a
    validator or a suite writes is removed with the run and never lands in a
    shared temporary root. Every mirrored suite runs with
    `GIT_CEILING_DIRECTORIES` at the run's temporary root and with pytest's
    `--basetemp` inside it, so a mirror never discovers an enclosing
    repository's history and never touches pytest's shared temporary root.

Exit codes:
  0  every target in every mode, and every suite record, identical
  1  any difference; each is printed, with a unified diff of stdout
  2  a refusal: the carve commit unreachable or malformed, the adapter
     missing, a validator refusing at self-test (its text printed verbatim), a
     target run ending at exit 2, a suite that proved nothing or whose records
     do not pair, an export with no `governance/`, a `--report` that
     normalises to a path outside the working directory, or an
     `--openxfactory-export` that resolves outside the working directory, the
     temporary directory and the home directory
     (`path-outside-allowed-roots`), a `--report` whose directory does not
     exist (`report-parent-missing`)

Run: `python3 scripts/neutrality-gate.py [--carve-commit SHA]
[--openxfactory-export DIR [--openxfactory-export-commit SHA]]
[--no-suite-trees] [--report PATH] [--keep]`. Standard library only; offline;
it writes nothing outside its temporary tree and `--report`. Both paths are
checked before the run starts, and a refusal comes before the gate reads or
writes anything. The report is written BELOW THE INVOCATION'S WORKING
DIRECTORY: `--report` is joined under the working directory, normalised
(`~` expanded, `..` collapsed) and must start with the working directory, so
an absolute path outside it is refused. That containment is LEXICAL: a
symbolic link below the working directory is not followed, and the operator
controls the working directory. The export is RESOLVED (`~` and links
followed) and must sit below the working directory, the temporary directory or
the home directory. Driven by
`tests/neutrality_gate/test_neutrality_gate.py` and
`.github/workflows/neutrality-gate.yml`.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Sequence

GATE = Path(__file__).resolve()
ROOT = GATE.parents[1]
VALIDATOR_NAME = "validate-openxwallet.py"
VALIDATOR_RELPATH = f"scripts/{VALIDATOR_NAME}"

# The named carve commit (task 2.3; Brett Heap, 2026-10-08, "name 90111df as
# the carve commit, do 2.4 and 2.5").
CARVE_COMMIT = "90111df262d6f54f7e82651d860adc12345f83f4"
DECLARED_NEW_LINE = ("note  nested repositories pruned (not adjudicated): "
                     "openWallet")
OWN_WORKFLOW = ".github/workflows/neutrality-gate.yml"
PRECEDENT_WORKFLOW = ".github/workflows/carve-manifest.yml"
INIT_ROOT = "git submodule update --init openWallet"
INIT_CODE = "git -C openWallet submodule update --init code"

ENV_BASELINE = "NEUTRALITY_BASELINE"
ENV_COMPOSED = "NEUTRALITY_COMPOSED"
ENV_REPORT = "NEUTRALITY_REPORT"

STRICT = "--strict"
MODES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("plain", ()), (STRICT, (STRICT,)))
HELP_FLAGS = frozenset({"-h", "--help"})
SELF_SUITE = "neutrality_gate"
DRIVES_VALIDATOR = re.compile(r"""["']validate-openxwallet\.py["']""")
# A revision from the command line is 7 to 40 hexadecimal characters and
# nothing else, gated BEFORE it reaches any git argument (the carve manifest
# checker's REVISION_ARG_RE); what rev-parse hands back is checked to be a full
# object id before it goes back to git.
REVISION_ARG_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
RESOLVED_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
REFUSAL_OUTSIDE_ROOTS = "path-outside-allowed-roots"
KIND_EXPORT = "openxfactory-export"
DIFF_LINE_LIMIT = 200
OUTPUT_LINE_LIMIT = 40
RUN_TIMEOUT = 900       # seconds: one validator over one tree
SUITE_TIMEOUT = 3600    # seconds: one mirrored suite's whole pytest run


class GateRefusal(Exception):
    """A named refusal: the run cannot answer, which is never a pass."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(code, detail)


@dataclass(frozen=True)
class Run:
    """One validator invocation, as bytes."""

    rc: int
    stdout: bytes
    stderr: bytes


def decode(raw: bytes) -> str:
    return raw.decode("utf-8", "backslashreplace")


def identical(baseline: Run, composed: Run) -> bool:
    """THE comparison: stdout byte for byte, and the exit code."""
    return baseline.stdout == composed.stdout and baseline.rc == composed.rc


# Set by `children_tmpdir` for the life of a run's temporary tree. The shim
# is a child too, so the validators it starts inherit the same TMPDIR.
_CHILD_TMPDIR: Path | None = None


@contextlib.contextmanager
def children_tmpdir(scratch: Path) -> Iterator[Path]:
    """TMPDIR for every child of this run, inside its temporary tree."""
    global _CHILD_TMPDIR
    tmp = scratch / "tmp"
    tmp.mkdir()
    _CHILD_TMPDIR = tmp
    try:
        yield tmp
    finally:
        _CHILD_TMPDIR = None


def child_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if _CHILD_TMPDIR is not None:
        env["TMPDIR"] = str(_CHILD_TMPDIR)
    env.update(extra or {})
    return env


def run_validator(script: Path, argv: Sequence[str], cwd: Path,
                  timeout: float | None = None) -> Run:
    done = subprocess.run([sys.executable, str(script), *argv], cwd=cwd,
                          capture_output=True, stdin=subprocess.DEVNULL,
                          env=child_env(), check=False, timeout=timeout)
    return Run(done.returncode, done.stdout, done.stderr)


def run_all(jobs: Sequence[tuple[Path, Sequence[str]]], cwd: Path,
            timeout: float | None = None) -> list[Run]:
    """Each (script, argv) in one directory, concurrently, in order."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [pool.submit(run_validator, script, argv, cwd, timeout)
                   for script, argv in jobs]
        return [future.result() for future in futures]


def run_pair(baseline: Path, composed: Path, argv: Sequence[str], cwd: Path,
             timeout: float | None = None) -> tuple[Run, Run]:
    """Both validators over one argv in one directory, concurrently."""
    first, second = run_all([(baseline, argv), (composed, argv)], cwd,
                            timeout)
    return first, second


def clipped(lines: list[str], limit: int) -> list[str]:
    if len(lines) <= limit:
        return lines
    return lines[:limit] + [f"... ({len(lines) - limit} more line(s))"]


def stdout_diff(baseline: str, composed: str) -> list[str]:
    lines = list(difflib.unified_diff(
        baseline.splitlines(), composed.splitlines(),
        fromfile="baseline stdout", tofile="composed stdout", lineterm=""))
    return clipped(lines, DIFF_LINE_LIMIT)


def indented(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


# --------------------------------------------------------------------------
# the shim (target iii)
# --------------------------------------------------------------------------

SHIM_TEMPLATE = '''#!/usr/bin/env python3
"""GENERATED by scripts/neutrality-gate.py for one run; never committed.

It stands where a mirrored suite expects scripts/validate-openxwallet.py: it
runs the baseline and the composed adapter over the argv as given and with
--strict toggled, records both modes, and replays the as-given composed run.
"""
import importlib.util
import sys

_SPEC = importlib.util.spec_from_file_location("neutrality_gate", {gate!r})
_GATE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _GATE  # dataclasses resolve their module by name
_SPEC.loader.exec_module(_GATE)
sys.exit(_GATE.shim_main(sys.argv[1:]))
'''


def write_shim(dest: Path, gate: Path = GATE) -> Path:
    """Write the shim stub at `dest`; it loads `gate` by path when run."""
    dest.write_text(SHIM_TEMPLATE.format(gate=str(gate)), encoding="utf-8")
    return dest


def _side(run: Run) -> dict[str, Any]:
    return {"rc": run.rc, "stdout": decode(run.stdout),
            "stderr": decode(run.stderr)}


def is_help(argv: Sequence[str]) -> bool:
    return bool(HELP_FLAGS & set(argv))


def _is_strict(arg: str) -> bool:
    """`--strict`, or an abbreviation argparse would take for it."""
    return arg.startswith("--s") and STRICT.startswith(arg)


def mode_of(argv: Sequence[str]) -> str:
    return "strict" if any(_is_strict(arg) for arg in argv) else "plain"


def toggle_strict(argv: Sequence[str]) -> list[str]:
    """The argv in the OTHER mode: `--strict` removed where it is given (with
    any abbreviation of it), appended where it is not."""
    if mode_of(argv) == "strict":
        return [arg for arg in argv if not _is_strict(arg)]
    return [*argv, STRICT]


def make_record(argv: Sequence[str], cwd: Path, baseline: Run,
                composed: Run, replayed: bool = True) -> dict[str, Any]:
    test = os.environ.get("PYTEST_CURRENT_TEST", "")
    return {
        "test": test.rsplit(" (", 1)[0],
        "argv": list(argv),
        "cwd": str(cwd),
        "help": is_help(argv),
        "mode": mode_of(argv),
        "replayed": replayed,
        "identical": identical(baseline, composed),
        "stderr_identical": baseline.stderr == composed.stderr,
        "baseline": _side(baseline),
        "composed": _side(composed),
    }


def shim_main(argv: Sequence[str]) -> int:
    """Run both validators over the argv as given and, unless it asks for
    help, with `--strict` toggled; record one pair per mode; replay the
    as-given composed run."""
    missing = [name for name in (ENV_BASELINE, ENV_COMPOSED, ENV_REPORT)
               if not os.environ.get(name)]
    if missing:
        print(f"neutrality-gate shim: {', '.join(missing)} not set; this shim "
              "runs only under scripts/neutrality-gate.py", file=sys.stderr)
        return 2
    cwd = Path.cwd()
    baseline = Path(os.environ[ENV_BASELINE])
    composed = Path(os.environ[ENV_COMPOSED])
    variants = [list(argv)]
    if not is_help(argv):
        variants.append(toggle_strict(argv))
    runs = run_all([(script, variant) for variant in variants
                    for script in (baseline, composed)], cwd)
    records = [make_record(variant, cwd, runs[2 * index],
                           runs[2 * index + 1], replayed=index == 0)
               for index, variant in enumerate(variants)]
    # ONE write for both records, so a suite's report never holds a mode
    # without its partner.
    with open(os.environ[ENV_REPORT], "a", encoding="utf-8") as report:
        report.write("".join(json.dumps(record) + "\n" for record in records))
    replay = runs[1]
    sys.stdout.buffer.write(replay.stdout)
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(replay.stderr)
    sys.stderr.buffer.flush()
    return replay.rc


# --------------------------------------------------------------------------
# git and the baseline
# --------------------------------------------------------------------------

def git(repo: Path, *args: str,
        stdin: bytes | None = None) -> subprocess.CompletedProcess:
    """git, capturing BYTES. Every revision argument follows
    `--end-of-options`, so no value can be read by git as an option."""
    try:
        return subprocess.run(["git", "-C", str(repo), *args], input=stdin,
                              capture_output=True, check=False)
    except OSError as exc:
        raise GateRefusal("neutrality-git-unavailable",
                          f"git could not be run in {repo}: {exc}") from exc


def git_text(repo: Path, *args: str) -> str | None:
    done = git(repo, *args)
    if done.returncode != 0:
        return None
    return decode(done.stdout).strip()


def unreachable_detail(commit: str) -> str:
    return (f"the carve commit {commit} is not in this checkout's history "
            f"({ROOT}). A depth-1 `actions/checkout` does not carry it: check "
            f"out with `fetch-depth: 0`, as {OWN_WORKFLOW} does on the "
            f"precedent of {PRECEDENT_WORKFLOW}, whose checker refuses the "
            "same way (`carve-revision-mismatch`); locally, `git fetch "
            "--unshallow`. The baseline IS that commit's validator, read from "
            "git objects, so without the commit there is nothing to compare "
            "against")


def resolve_carve(commit: str) -> str:
    """The carve commit, as a full id this checkout carries below HEAD."""
    if not REVISION_ARG_RE.match(commit):
        raise GateRefusal(
            "neutrality-carve-invalid",
            f"--carve-commit {commit!r} is not a commit id: 7 to 40 "
            "hexadecimal characters, refused before it reaches git")
    resolved = git_text(ROOT, "rev-parse", "--verify", "--quiet",
                        "--end-of-options", f"{commit}^{{commit}}")
    if not resolved or not RESOLVED_RE.match(resolved):
        raise GateRefusal("neutrality-carve-unreachable",
                          unreachable_detail(commit))
    if not resolved.startswith(commit.lower()):
        raise GateRefusal(
            "neutrality-carve-unreachable",
            f"{commit} is not a commit object: it peels to {resolved}. An "
            "annotated tag is a label, never the referent; name the commit")
    if git(ROOT, "merge-base", "--is-ancestor", "--end-of-options", resolved,
           "HEAD").returncode != 0:
        raise GateRefusal(
            "neutrality-carve-unreachable",
            f"the carve commit {resolved[:12]} is NOT AN ANCESTOR of HEAD in "
            f"{ROOT}; the baseline would come from an unrelated history")
    return resolved


def _carve_entries(carve: str) -> list[tuple[str, str]]:
    """(object id, path) for every blob the baseline tree needs."""
    done = git(ROOT, "ls-tree", "-r", "-z", "--full-tree", "--end-of-options",
               carve, "contracts", VALIDATOR_RELPATH)
    if done.returncode != 0:
        raise GateRefusal("neutrality-baseline-unreadable",
                          f"`git ls-tree {carve[:12]}` failed: "
                          + decode(done.stderr).strip())
    entries = []
    for record in decode(done.stdout).split("\0"):
        meta, _, path = record.partition("\t")
        fields = meta.split(" ")
        if len(fields) == 3 and fields[1] == "blob":
            entries.append((fields[2], path))
    return entries


def _read_blobs(oids: list[str]) -> list[bytes]:
    """Raw blob bytes from ONE `git cat-file --batch`, in order."""
    done = git(ROOT, "cat-file", "--batch",
               stdin="".join(oid + "\n" for oid in oids).encode())
    out, pos, blobs = done.stdout, 0, []
    for oid in oids:
        end = out.find(b"\n", pos)
        header = out[pos:end].split(b" ")
        if done.returncode != 0 or len(header) != 3 or header[1] != b"blob":
            raise GateRefusal("neutrality-baseline-unreadable",
                              f"git cat-file did not return blob {oid}")
        size = int(header[2])
        blobs.append(out[end + 1:end + 1 + size])
        pos = end + 1 + size + 1
    return blobs


def build_baseline(carve: str, into: Path) -> Path:
    """The carve commit's validator beside the carve commit's `contracts/`."""
    entries = _carve_entries(carve)
    paths = [path for _, path in entries]
    if VALIDATOR_RELPATH not in paths or not any(
            path.startswith("contracts/") for path in paths):
        raise GateRefusal(
            "neutrality-baseline-unreadable",
            f"the carve commit {carve[:12]} carries no {VALIDATOR_RELPATH} "
            "or no contracts/; it is not a validator commit")
    for (_, path), blob in zip(entries, _read_blobs([o for o, _ in entries])):
        parts = PurePosixPath(path).parts
        if ".." in parts or PurePosixPath(path).is_absolute():
            raise GateRefusal("neutrality-baseline-unreadable",
                              f"refusing to write the tree path {path!r}")
        dest = into.joinpath(*parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
    return into / VALIDATOR_RELPATH


# --------------------------------------------------------------------------
# targets (i) and (ii)
# --------------------------------------------------------------------------

@dataclass
class TreeResult:
    name: str
    path: str
    modes: list[dict[str, Any]] = field(default_factory=list)
    declared_line: dict[str, bool] = field(default_factory=dict)

    @property
    def identical(self) -> bool:
        return all(mode["identical"] for mode in self.modes)


def preflight(baseline: Path, composed: Path) -> None:
    """Each validator once, self-test only; exit 2 refuses the run."""
    runs = run_pair(baseline, composed, [], ROOT, RUN_TIMEOUT)
    for label, run in zip(("baseline (carve commit)", "composed adapter"),
                          runs):
        if run.rc == 2:
            words = decode(run.stderr) + decode(run.stdout)
            raise GateRefusal(
                "neutrality-validator-refused",
                f"the {label} refused at its self-test (no path) with exit "
                f"2. Its own words, verbatim:\n{indented(words)}")


def _print_mode(target: str, mode: str, baseline: Run, composed: Run) -> bool:
    same = identical(baseline, composed)
    print(f"{'IDENTICAL' if same else 'DIFFERENT':<9}  target {target}  "
          f"{mode:<8}  rc {baseline.rc}/{composed.rc}  stdout "
          f"{len(composed.stdout)} byte(s)")
    if not same:
        _print_difference(decode(baseline.stdout), decode(composed.stdout),
                          decode(baseline.stderr), decode(composed.stderr))
    return same


def _print_difference(b_out: str, c_out: str, b_err: str, c_err: str) -> None:
    if b_out == c_out:
        print("    stdout byte-identical; the exit codes differ")
    else:
        lines = stdout_diff(b_out, c_out) or [
            "stdout differs only in line endings or a final newline"]
        print(indented("\n".join(lines)))
    for label, err in (("baseline", b_err), ("composed", c_err)):
        if err.strip():
            print(f"    {label} stderr:")
            print(indented("\n".join(clipped(err.splitlines(),
                                             OUTPUT_LINE_LIMIT)), "      "))


def compare_tree(name: str, tree: Path, shown: str, baseline: Path,
                 composed: Path) -> TreeResult:
    """One target tree, plain and --strict, scanned as `.` from inside it."""
    result = TreeResult(name, shown)
    for mode, extra in MODES:
        try:
            b_run, c_run = run_pair(baseline, composed, [".", *extra], tree,
                                    RUN_TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            raise GateRefusal("neutrality-run-refused",
                              f"target {name} {mode}: no answer in "
                              f"{RUN_TIMEOUT}s") from exc
        if 2 in (b_run.rc, c_run.rc):
            words = (f"baseline:\n{indented(decode(b_run.stderr))}\n"
                     f"composed:\n{indented(decode(c_run.stderr))}")
            raise GateRefusal(
                "neutrality-run-refused",
                f"target {name} {mode}: exit {b_run.rc} (baseline) / "
                f"{c_run.rc} (composed). Exit 2 adjudicated nothing, so it is "
                f"never compared. Their own words:\n{words}")
        same = _print_mode(name, mode, b_run, c_run)
        result.modes.append({"mode": mode, "baseline_rc": b_run.rc,
                             "composed_rc": c_run.rc, "identical": same,
                             "stdout_bytes": len(c_run.stdout)})
        result.declared_line = {
            "baseline": DECLARED_NEW_LINE in decode(b_run.stdout).splitlines(),
            "composed": DECLARED_NEW_LINE in decode(c_run.stdout).splitlines()}
    return result


def allowed_roots() -> tuple[str, ...]:
    """The roots a path given on the command line may resolve below, as real
    paths in plain strings: the invocation's working directory, the temporary
    directory and the home directory (left out where the platform cannot name
    one)."""
    roots = [os.path.realpath(os.getcwd()),
             os.path.realpath(tempfile.gettempdir())]
    with contextlib.suppress(RuntimeError):
        roots.append(os.path.realpath(str(Path.home())))
    return tuple(roots)


def contained_path(arg: str, *, kind: str) -> Path:
    """NORMALISE, RESOLVE, then CONTAIN: the `--openxfactory-export` path
    (named by KIND in a refusal) is joined under a trusted root, normalised,
    resolved to its real location (`~` and symbolic links included) and
    accepted only where the resolved string starts with that root. The `Path`
    returned is the string that passed that prefix check, and it is the only
    path used afterwards. A relative argument is anchored at the working
    directory first, so `../x` means what it says there and is never re-read
    against another root. An export needs a `governance/` directory."""
    anchored = os.path.join(os.getcwd(), os.path.expanduser(arg))
    resolved = anchored
    for root in allowed_roots():
        candidate = os.path.normpath(os.path.join(root, anchored))
        resolved = os.path.realpath(candidate)
        if resolved == root:
            return require_governance(Path(root), arg)
        if resolved.startswith(root.rstrip(os.sep) + os.sep):
            return require_governance(Path(resolved), arg)
    raise GateRefusal(
        REFUSAL_OUTSIDE_ROOTS,
        f"--{kind} {arg!r} resolves to {resolved}, outside the "
        "invocation's working directory, the temporary directory and the "
        "home directory; the gate writes and reads only below those roots")


def require_governance(accepted: Path, arg: str) -> Path:
    """What an export needs of a path that is already contained."""
    if not (accepted / "governance").is_dir():
        raise GateRefusal(
            "neutrality-export-invalid",
            f"--openxfactory-export {arg!r} holds no governance/ directory. "
            "Pass the directory that CONTAINS governance/: the register "
            "reader joins the scan target with governance/review-authority, "
            "so a directory that IS governance/ would read no register and "
            "compare two empty reads")
    return accepted


def report_target(arg: str) -> str:
    """Where `--report` writes: ARG joined under the working directory and
    normalised (`~` expanded, `..` collapsed), accepted only where the result
    starts with the working directory, and only where its directory exists.
    The containment is lexical, as the prefix check on a normalised path is:
    a link below the working directory is not followed."""
    root = os.getcwd()
    report_path = os.path.normpath(os.path.join(root, os.path.expanduser(arg)))
    if not report_path.startswith(root.rstrip(os.sep) + os.sep):
        raise GateRefusal(
            REFUSAL_OUTSIDE_ROOTS,
            f"--report {arg!r} normalises to {report_path}, which is not "
            f"below the invocation's working directory {root}; the gate "
            "writes its report only below the working directory")
    if not os.path.isdir(os.path.dirname(report_path)):
        raise GateRefusal(
            "report-parent-missing",
            f"--report {arg!r} normalises to {report_path}, whose directory "
            f"{os.path.dirname(report_path)} does not exist; the gate does "
            "not create it")
    return report_path


def validated_paths(args: argparse.Namespace,
                    ) -> tuple[str | None, Path | None]:
    """The checked `--report` path (a string, normalised and below the
    working directory) and the resolved, contained `--openxfactory-export`
    path (None where a flag was not given). Everything after this uses these
    and never the raw arguments."""
    report = export = None
    if args.report:
        report = report_target(args.report)
    if args.openxfactory_export:
        export = contained_path(args.openxfactory_export, kind=KIND_EXPORT)
    return report, export


def print_declared_line(result: TreeResult) -> None:
    seen = result.declared_line
    if seen.get("baseline") and seen.get("composed"):
        where = "printed by BOTH validators over target root, as declared"
    elif not seen.get("baseline") and not seen.get("composed"):
        where = ("absent from both over target root: this tree has no "
                 "openWallet/ checkout")
    else:
        where = "printed by ONE side only, which is a difference (above)"
    print(f"note  design D5's declared new line {DECLARED_NEW_LINE!r}: "
          f"{where}")


# --------------------------------------------------------------------------
# target (iii): the suites
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Suite:
    leg: str            # "kept" (tests/) or "moved" (openWallet/code/tests/)
    source_root: Path   # the root the suite's REPO_ROOT resolves to
    directory: Path

    @property
    def label(self) -> str:
        return self.directory.relative_to(ROOT).as_posix()


@dataclass
class SuiteResult:
    suite: Suite
    records: list[dict[str, Any]]
    pytest_rc: int | None
    pytest_output: str
    refusal: str | None = None

    @property
    def judged(self) -> list[dict[str, Any]]:
        return [r for r in self.records if not r["help"]]

    @property
    def helps(self) -> list[dict[str, Any]]:
        return [r for r in self.records if r["help"]]

    @property
    def invocations(self) -> int:
        """Tree invocations the suite made: one replayed record each."""
        return sum(1 for r in self.judged if r["replayed"])

    @property
    def paired(self) -> bool:
        """Every tree invocation recorded in both modes, and no more."""
        modes = [r["mode"] for r in self.judged]
        return (len(self.judged) == 2 * self.invocations
                and modes.count("plain") == modes.count("strict"))

    @property
    def differences(self) -> list[dict[str, Any]]:
        return [r for r in self.judged if not r["identical"]]


def drives_validator(directory: Path) -> bool:
    return any(DRIVES_VALIDATOR.search(path.read_text(encoding="utf-8",
                                                      errors="replace"))
               for path in sorted(directory.rglob("*.py")))


def discover_suites(source_root: Path,
                    leg: str) -> tuple[list[Suite], list[tuple[str, str]]]:
    """The suites under `<source_root>/tests/` that drive the validator."""
    suites: list[Suite] = []
    skipped: list[tuple[str, str]] = []
    tests = source_root / "tests"
    if not tests.is_dir():
        return suites, skipped
    for directory in sorted(p for p in tests.iterdir()
                            if p.is_dir() and p.name != "__pycache__"):
        suite = Suite(leg, source_root, directory)
        if leg == "kept" and directory.name == SELF_SUITE:
            skipped.append((suite.label, "this gate's own suite; it drives "
                            "toy validators"))
        elif drives_validator(directory):
            suites.append(suite)
        else:
            skipped.append((suite.label, 'no file spells "validate-openxwallet.py";'
                            " it never invokes the validator"))
    return suites, skipped


def code_leg() -> tuple[Path | None, str | None]:
    """`openWallet/code` when initialized, else why the moved suites skip."""
    code = ROOT / "openWallet" / "code"
    if (code / ".git").exists():
        return code, None
    listed = git_text(ROOT, "ls-files", "--stage", "--", "openWallet")
    if not listed:
        return None, ("this tree records no openWallet/ gitlink (it predates "
                      "the adapter rebuild), so there are no moved suites")
    return None, (f"openWallet/code is not initialized; run `{INIT_ROOT}` "
                  f"then `{INIT_CODE}` (scoped, never --recursive)")


GITLINK_MODE = "160000"


def tracked_entries(source: Path) -> list[tuple[str, PurePosixPath]]:
    """(mode, path) for every path the index of `source` tracks."""
    done = git(source, "ls-files", "--stage", "-z")
    if done.returncode != 0:
        raise GateRefusal(
            "neutrality-mirror-unreadable",
            f"`git ls-files` failed in {source}, so its tracked tree cannot "
            "be mirrored: " + decode(done.stderr).strip())
    entries = []
    for record in done.stdout.split(b"\0"):
        meta, _, raw = record.partition(b"\t")
        if not raw:
            continue
        path = PurePosixPath(os.fsdecode(raw))
        if path.is_absolute() or ".." in path.parts:
            raise GateRefusal("neutrality-mirror-unreadable",
                              f"refusing to mirror the tree path {path}")
        entries.append((meta.split(b" ")[0].decode("ascii"), path))
    return entries


def mirror(suite: Suite, into: Path) -> Path:
    """A root holding the suite root's tracked tree as real directories and
    copied files (the module docstring, target iii): the suite's directory
    copied whole, a gitlink linked, each `scripts/` file linked, and the
    shim at `scripts/validate-openxwallet.py`."""
    source = suite.source_root
    own = PurePosixPath(suite.directory.relative_to(source).as_posix())
    into.mkdir(parents=True)
    for mode, path in tracked_entries(source):
        if path == PurePosixPath(VALIDATOR_RELPATH) or own in path.parents:
            continue    # the shim stands there; the suite is copied below
        src, dest = source.joinpath(*path.parts), into.joinpath(*path.parts)
        if not os.path.lexists(src):
            continue    # deleted in the working tree: absent here as there
        dest.parent.mkdir(parents=True, exist_ok=True)
        if mode == GITLINK_MODE or path.parts[0] == "scripts":
            dest.symlink_to(src)
        else:
            shutil.copy2(src, dest, follow_symlinks=False)
    (into / "scripts").mkdir(exist_ok=True)
    write_shim(into / "scripts" / VALIDATOR_NAME)
    shutil.copytree(suite.directory, into.joinpath(*own.parts),
                    ignore=shutil.ignore_patterns("__pycache__"))
    return into


def read_records(report: Path) -> list[dict[str, Any]]:
    if not report.is_file():
        return []
    return [json.loads(line) for line in
            report.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_suite(suite: Suite, workdir: Path, baseline: Path, composed: Path,
              ceiling: Path) -> SuiteResult:
    root = mirror(suite, workdir / "mirror")
    report = workdir / "records.jsonl"
    env = child_env({ENV_BASELINE: str(baseline), ENV_COMPOSED: str(composed),
                     ENV_REPORT: str(report),
                     "GIT_CEILING_DIRECTORIES": str(ceiling)})
    argv = [sys.executable, "-m", "pytest", "-q", "-rfEs", "-p",
            "no:cacheprovider", f"--basetemp={workdir / 'pytest-tmp'}",
            f"tests/{suite.directory.name}"]
    try:
        done = subprocess.run(argv, cwd=root, env=env, capture_output=True,
                              stdin=subprocess.DEVNULL, check=False,
                              timeout=SUITE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return SuiteResult(suite, read_records(report), None, "",
                           f"pytest gave no answer in {SUITE_TIMEOUT}s")
    result = SuiteResult(suite, read_records(report), done.returncode,
                         decode(done.stdout) + decode(done.stderr))
    if done.returncode not in (0, 1):
        result.refusal = (f"pytest ended at exit {done.returncode}, so the "
                          "suite did not run as written")
    elif not result.judged:
        result.refusal = ("the suite recorded no tree invocation: the shim "
                          "was never reached, so this target proves nothing")
    elif not result.paired:
        result.refusal = (f"the shim's records do not pair: "
                          f"{len(result.judged)} tree record(s) for "
                          f"{result.invocations} invocation(s), where every "
                          "invocation records exactly one plain and one "
                          "strict run")
    return result


def run_suites(suites: list[Suite], scratch: Path, baseline: Path,
               composed: Path) -> list[SuiteResult]:
    workers = max(1, min(len(suites), os.cpu_count() or 1, 4))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_suite, suite,
                               scratch / "suites" / f"{suite.leg}-{index}",
                               baseline, composed, scratch)
                   for index, suite in enumerate(suites)]
        return [future.result() for future in futures]


def _pytest_digest(output: str) -> list[str]:
    lines = [line for line in output.splitlines()
             if line.startswith(("FAILED", "ERROR", "SKIPPED"))]
    tail = [line for line in output.splitlines() if line.strip()][-1:]
    return clipped(lines, OUTPUT_LINE_LIMIT) + tail


def print_suite(result: SuiteResult) -> None:
    judged, helps = result.judged, result.helps
    if result.refusal:
        verdict = "REFUSED"
    elif result.differences:
        verdict = "DIFFERENT"
    else:
        verdict = "IDENTICAL"
    same_help = sum(1 for r in helps if r["identical"])
    help_tally = (f"; help {same_help} of {len(helps)} identical (not a "
                  "tree, outside the verdict)" if helps else "")
    print(f"{verdict:<9}  suite {result.suite.label}  "
          f"{len(judged) - len(result.differences)} of {len(judged)} tree "
          f"record(s) identical: {result.invocations} invocation(s) × 2 "
          f"modes{help_tally}")
    if result.refusal:
        print(f"    {result.refusal}")
    for record in result.differences:
        how = "as given" if record["replayed"] else "--strict toggled"
        print(f"    DIFFERENT  {record['test'] or '(no test id)'}  argv "
              f"{record['argv']}  {record['mode']} ({how})  rc "
              f"{record['baseline']['rc']}/{record['composed']['rc']}")
        _print_difference(record["baseline"]["stdout"],
                          record["composed"]["stdout"],
                          record["baseline"]["stderr"],
                          record["composed"]["stderr"])
    print(f"    pytest (information), exit {result.pytest_rc}:")
    print(indented("\n".join(_pytest_digest(result.pytest_output)), "      "))


def suite_summary(result: SuiteResult) -> dict[str, Any]:
    return {
        "suite": result.suite.label, "leg": result.suite.leg,
        "tree_invocations": result.invocations,
        "modes": 2,
        "tree_records": len(result.judged),
        "identical": len(result.judged) - len(result.differences),
        "help_invocations": len(result.helps),
        "help_identical": sum(1 for r in result.helps if r["identical"]),
        "differences": [{"test": r["test"], "argv": r["argv"],
                         "mode": r["mode"], "replayed": r["replayed"],
                         "baseline_rc": r["baseline"]["rc"],
                         "composed_rc": r["composed"]["rc"]}
                        for r in result.differences],
        "pytest_rc": result.pytest_rc,
        "pytest_summary": (_pytest_digest(result.pytest_output) or [""])[-1],
        "refusal": result.refusal,
    }


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------

def revision_facts() -> dict[str, Any]:
    status = git_text(ROOT, "--no-optional-locks", "status", "--porcelain",
                      "--untracked-files=no")
    facts: dict[str, Any] = {
        "head": git_text(ROOT, "rev-parse", "--verify", "--quiet", "HEAD"),
        "tracked_changes": bool(status)}
    for key, path in (("openwallet", ROOT / "openWallet"),
                      ("openwallet_code", ROOT / "openWallet" / "code")):
        facts[key] = (git_text(path, "rev-parse", "--verify", "--quiet",
                               "HEAD") if (path / ".git").exists() else None)
    return facts


@contextlib.contextmanager
def scratch_dir(keep: bool) -> Iterator[Path]:
    if keep:
        kept = Path(tempfile.mkdtemp(prefix="neutrality-gate-"))
        print(f"note  --keep: this run's temporary tree stays at {kept}")
        yield kept
        return
    with tempfile.TemporaryDirectory(prefix="neutrality-gate-") as name:
        yield Path(name)


def _targets(export: Path | None) -> list[tuple[str, Path, str]]:
    targets = [("root", ROOT, ".")]
    if export is not None:
        targets.append((KIND_EXPORT, export, str(export)))
    return targets


def _suite_phase(args: argparse.Namespace, scratch: Path, baseline: Path,
                 composed: Path, evidence: dict[str, Any]) -> list[SuiteResult]:
    if args.no_suite_trees:
        evidence["skipped"].append({"what": "target (iii), every suite",
                                    "reason": "--no-suite-trees"})
        print("SKIP       target (iii): --no-suite-trees")
        return []
    suites, skipped = discover_suites(ROOT, "kept")
    code, why = code_leg()
    if code is None:
        skipped.append(("openWallet/code/tests (the moved suites)", why or ""))
    else:
        moved, moved_skipped = discover_suites(code, "moved")
        suites += moved
        skipped += moved_skipped
    for what, reason in skipped:
        print(f"SKIP       {what}: {reason}")
        evidence["skipped"].append({"what": what, "reason": reason})
    results = run_suites(suites, scratch, baseline, composed)
    for result in results:
        print_suite(result)
    return results


def gate(args: argparse.Namespace, evidence: dict[str, Any],
         export: Path | None) -> int:
    composed = ROOT / VALIDATOR_RELPATH
    if not composed.is_file():
        raise GateRefusal("neutrality-adapter-missing",
                          f"no composed adapter at {VALIDATOR_RELPATH}")
    carve = resolve_carve(args.carve_commit)
    evidence["carve_commit"] = carve
    evidence["composed"]["sha256"] = hashlib.sha256(
        composed.read_bytes()).hexdigest()
    targets = _targets(export)
    with scratch_dir(args.keep) as scratch, children_tmpdir(scratch):
        baseline = build_baseline(carve, scratch / "baseline")
        evidence["baseline"]["blob"] = git_text(
            ROOT, "rev-parse", "--verify", "--quiet", "--end-of-options",
            f"{carve}:{VALIDATOR_RELPATH}")
        head = (evidence["revision"]["head"] or "?")[:12]
        print(f"neutrality-gate: baseline {VALIDATOR_RELPATH} at the carve "
              f"commit {carve[:12]}; composed {VALIDATOR_RELPATH} at HEAD "
              f"{head}; rc is printed baseline/composed")
        preflight(baseline, composed)
        trees = [compare_tree(name, path, shown, baseline, composed)
                 for name, path, shown in targets]
        print_declared_line(trees[0])
        suites = _suite_phase(args, scratch, baseline, composed, evidence)
    return verdict(trees, suites, evidence)


def verdict(trees: list[TreeResult], suites: list[SuiteResult],
            evidence: dict[str, Any]) -> int:
    evidence["targets"] = [{"target": t.name, "path": t.path,
                            "modes": t.modes, "identical": t.identical}
                           for t in trees]
    evidence["declared_new_line"] = dict(trees[0].declared_line,
                                         text=DECLARED_NEW_LINE)
    evidence["suites"] = [suite_summary(result) for result in suites]
    refused = [r for r in suites if r.refusal]
    if refused:
        raise GateRefusal(
            "neutrality-suite-vacuous",
            "; ".join(f"{r.suite.label}: {r.refusal}" for r in refused))
    runs = sum(len(t.modes) for t in trees)
    invocations = sum(r.invocations for r in suites)
    records = sum(len(r.judged) for r in suites)
    differing = (sum(1 for t in trees for m in t.modes if not m["identical"])
                 + sum(len(r.differences) for r in suites))
    if differing:
        print(f"neutrality-gate: DIFFERENT: {differing} of {runs + records} "
              "comparison(s) differ (above)")
        evidence["result"] = "different"
        return 1
    print(f"neutrality-gate: IDENTICAL: {len(trees)} tree(s) × 2 modes = "
          f"{runs} target run(s), and {invocations} suite invocation(s) × 2 "
          f"modes = {records} suite record(s) over {len(suites)} suite(s); "
          "every stdout byte-identical, every exit code equal")
    evidence["result"] = "identical"
    return 0


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="neutrality-gate.py",
        description=("Run the carve-commit validator and the composed adapter "
                     "over the same trees and require byte-identical stdout "
                     "and equal exit codes (split-openwallet-neutral-core, "
                     "design.md D5)."))
    parser.add_argument("--carve-commit", metavar="SHA", default=CARVE_COMMIT,
                        help=f"the baseline's commit (default: {CARVE_COMMIT})")
    parser.add_argument("--openxfactory-export", metavar="DIR", default=None,
                        help="target (ii): a directory holding an export of "
                             "openxFactory's governance/ tree")
    parser.add_argument("--openxfactory-export-commit", metavar="SHA",
                        default=None,
                        help="the openxFactory commit the export was taken "
                             "at, recorded in --report")
    parser.add_argument("--no-suite-trees", action="store_true",
                        help="skip target (iii), the suites' fixture trees")
    parser.add_argument("--report", metavar="PATH", default=None,
                        help="write a JSON summary of the run here; PATH must "
                             "normalise to a file below the working directory")
    parser.add_argument("--keep", action="store_true",
                        help="keep the run's temporary tree and print where")
    args = parser.parse_args(argv)
    declared = args.openxfactory_export_commit
    if declared is not None and (args.openxfactory_export is None
                                 or not REVISION_ARG_RE.match(declared)):
        parser.error("--openxfactory-export-commit takes 7 to 40 hexadecimal "
                     "characters and needs --openxfactory-export")
    return args


def new_evidence(export: Path | None, declared_commit: str | None,
                 ) -> dict[str, Any]:
    return {
        "gate": "neutrality-gate", "design": "split-openwallet-neutral-core "
        "design.md D5", "result": None, "revision": revision_facts(),
        "carve_commit": None,
        "baseline": {"script": VALIDATOR_RELPATH, "blob": None},
        "composed": {"script": VALIDATOR_RELPATH, "sha256": None},
        "openxfactory_export": (
            {"path": str(export), "declared_commit": declared_commit}
            if export is not None else None),
        "skipped": [], "refusal": None}


def print_refusal(exc: GateRefusal) -> None:
    print(f"neutrality-gate: REFUSED [{exc.code}]: {exc.detail}",
          file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report, export = validated_paths(args)
    except GateRefusal as exc:
        # Before the run: nothing has been read or written, so no evidence.
        print_refusal(exc)
        return 2
    evidence = new_evidence(export, args.openxfactory_export_commit)
    try:
        code = gate(args, evidence, export)
    except GateRefusal as exc:
        print_refusal(exc)
        evidence["result"] = "refused"
        evidence["refusal"] = {"code": exc.code, "detail": exc.detail}
        code = 2
    evidence["exit_code"] = code
    if report is not None:
        with open(report, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(evidence, indent=2) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
