"""`scripts/neutrality-gate.py` (`split-openwallet-neutral-core` task 5.4,
`design.md` D5): the gate observed failing before it is trusted, and the real
repository's seat.

WHY TOY VALIDATORS. The gate's whole job is to say DIFFERENT when two
validators disagree, and this repository holds no second validator that
disagrees with the first on purpose. So each case builds a throwaway
repository under `tmp_path`: a copy of the gate at `scripts/neutrality-gate.py`
(it derives `ROOT` from its own location), a `contracts/` directory, and a toy
`scripts/validate-openxwallet.py` committed as the "carve commit". A second
commit replaces the toy with the "composed adapter", one behaviour away from
it. Agreeing toys must pass; a stdout difference, an exit-code difference, a
refusal at self-test, a refusal over a tree and a suite that never reaches
the shim must each fail with their own exit code. A help-text difference must
be reported and kept out of the verdict (the gate's docstring says why).

THE SHIM is tested directly as well: it must record both validators in BOTH
modes, the argv as given and with `--strict` toggled, and replay the as-given
composed run byte for byte, because a suite run through it asserts on what it
replays. A suite that never asks for `--strict` must still be compared under
it: the gate's claim is "plain and `--strict`" over every fixture tree.

THE GATE IS RUN AS A SUBPROCESS, the way CI and a reader invoke it, so the
exit codes and printed lines are what is under test. The module is also loaded
by path, for `write_shim`, the mirror and the skip conditions.

THE REAL-REPOSITORY SEAT needs the carve commit in history and an initialized
`openWallet/code` where this tree records the gitlink. Where either is missing
it SKIPS LOUDLY, naming what is missing and how to get it; it never counts a
refusal as a pass. Otherwise it runs the gate over this tree and asserts exit
0.

Hermetic: no network; git runs with an empty global config, no system config
and a repository-local identity.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = REPO_ROOT / "scripts" / "neutrality-gate.py"
CARVE_COMMIT = "90111df262d6f54f7e82651d860adc12345f83f4"
FULL_HISTORY_WORKFLOW = ".github/workflows/neutrality-gate.yml"
PRECEDENT_WORKFLOW = ".github/workflows/carve-manifest.yml"
INIT_LINES = ("git submodule update --init openWallet",
              "git -C openWallet submodule update --init code")


def _load():
    spec = importlib.util.spec_from_file_location("neutrality_gate", GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module by name
    spec.loader.exec_module(module)
    return module


MODULE = _load()


@pytest.fixture(autouse=True)
def _hermetic_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "neutrality-gate-test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "neutrality-test@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "neutrality-gate-test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "neutrality-test@example.invalid")


# --------------------------------------------------------------------------
# toys
# --------------------------------------------------------------------------

# One toy validator; BEHAVIOUR, prepended per file, is the one way a
# "composed" toy departs from the "baseline" one. Its output imitates the real
# validator's shape: a self-test note, a scan note over a path, a summary.
TOY_BODY = '''
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    argv = sys.argv[1:]
    if "--help" in argv:
        extra = " (composed)" if BEHAVIOUR == "help-differs" else ""
        print("usage: toy validator" + extra)
        return 0
    if BEHAVIOUR == "refuses":
        print("ERROR openWallet/code is not initialized; run the scoped init",
              file=sys.stderr)
        return 2
    if not (ROOT / "contracts").is_dir():
        print("ERROR contracts not found", file=sys.stderr)
        return 2
    print("note  toy self-test: 1 positive example(s)")
    paths = [a for a in argv if not a.startswith("-")]
    if paths:
        if BEHAVIOUR == "refuses-trees":
            print("ERROR harness failure: toy", file=sys.stderr)
            return 2
        target = Path(paths[0]).resolve()
        found = [p for p in target.rglob("*.yaml") if ".git" not in p.parts]
        extra = " (and one more)" if BEHAVIOUR == "scan-differs" else ""
        if (BEHAVIOUR == "strict-scan-differs" and "--strict" in argv
                and found):
            extra = " (strict only)"
        print(f"note  repo scan: {len(found)} yaml file(s){extra}")
    print("")
    print("validate-toy: 0 error(s)")
    strict = "--strict" in argv
    return 1 if strict and BEHAVIOUR == "strict-rc-differs" else 0


sys.exit(main())
'''

# A suite shaped like the real ones: REPO_ROOT from its own location, the
# validator driven as a subprocess, a fixture tree under tmp_path.
TOY_SUITE = '''
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate-openxwallet.py"


def _run(*args):
    return subprocess.run([sys.executable, str(VALIDATOR), *args],
                          capture_output=True, text=True)


def test_a_fixture_tree(tmp_path):
    (tmp_path / "record.yaml").write_text("kind: toy\\n", encoding="utf-8")
    r = _run(str(tmp_path), "--strict")
    assert "repo scan: 1 yaml file(s)" in r.stdout, r.stdout + r.stderr


def test_the_help_text():
    assert _run("--help").stdout.startswith("usage: toy validator")
'''

# The same shape, but it never asks for --strict. Its assertion holds only
# for the PLAIN output, so it also proves the replay is the as-given run.
PLAIN_SUITE = '''
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate-openxwallet.py"


def test_a_fixture_tree_scanned_plain(tmp_path):
    (tmp_path / "record.yaml").write_text("kind: toy\\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(VALIDATOR), str(tmp_path)],
                       capture_output=True, text=True)
    assert "note  repo scan: 1 yaml file(s)" in r.stdout.splitlines(), \\
        r.stdout + r.stderr
'''

QUIET_SUITE = '''
def test_nothing_drives_a_validator():
    assert True
'''

# TOY_SUITE with the validator's path respelled as lane 1 respelled one in
# tests/register_reissuance: it still runs the validator, but no file spells
# the quoted literal discovery looks for.
RESPELLED_SUITE = TOY_SUITE.replace(
    'REPO_ROOT / "scripts" / "validate-openxwallet.py"',
    'REPO_ROOT / "scripts/validate-openxwallet.py"')
assert RESPELLED_SUITE != TOY_SUITE

# TOY_SUITE plus a validator-driving test that SKIPS before it builds a tree,
# as a test needing git history skips inside the gate's mirror.
SKIPPING_SUITE = TOY_SUITE + '''

def test_a_tree_the_mirror_cannot_build(tmp_path):
    import pytest
    pytest.skip("needs git history the mirror does not have")
    _run(str(tmp_path))
'''

# Names the validator in a quoted literal but never runs it.
HOLLOW_SUITE = '''
NAME = "validate-openxwallet.py"


def test_names_but_never_runs():
    assert NAME
'''


def _toy(behaviour: str) -> str:
    return f"BEHAVIOUR = {behaviour!r}\n" + TOY_BODY


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, check=False)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


def _write(root: Path, rel: str, text: str) -> None:
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def _gate_source(expected: Sequence[str]) -> str:
    """The gate, with the toy repository's own EXPECTED_SUITES in place of
    this repository's. The constant is the gate's pinned value, so a toy
    declares its set in its own copy of the gate, never through a runtime
    override the real gate would also honour."""
    source = GATE.read_text(encoding="utf-8")
    start = source.index("EXPECTED_SUITES: tuple[str, ...] = (\n")
    end = source.index("\n)\n", start) + len("\n)\n")
    return (source[:start] + "EXPECTED_SUITES: tuple[str, ...] = "
            f"{tuple(expected)!r}\n" + source[end:])


def _repo(tmp_path: Path, composed: str = "same",
          suites: dict[str, str] | None = None,
          files: dict[str, str] | None = None,
          expected: Sequence[str] | None = None) -> tuple[Path, str]:
    """A throwaway repository: the toy baseline committed as the carve
    commit, then the composed toy committed over it. Returns (repo, carve).
    EXPECTED pins the toy's suite set; by default, the suites that spell the
    literal discovery looks for."""
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    if expected is None:
        expected = [f"tests/{name}" for name, source in (suites or {}).items()
                    if MODULE.DRIVES_VALIDATOR.search(source)]
    _write(repo, "scripts/neutrality-gate.py", _gate_source(expected))
    _write(repo, "contracts/README.md", "toy contracts\n")
    _write(repo, "scripts/validate-openxwallet.py", _toy("same"))
    for name, source in (suites or {}).items():
        _write(repo, f"tests/{name}/test_{name}.py", source)
    for rel, text in (files or {}).items():
        _write(repo, rel, text)
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "the carve commit")
    carve = _git(repo, "rev-parse", "HEAD")
    # Different BYTES even when the behaviour is the same: the gate compares
    # what the validators say, never their source.
    _write(repo, "scripts/validate-openxwallet.py",
           _toy(composed) + "\n# the composed adapter\n")
    _git(repo, "commit", "-q", "-am", "the composed adapter")
    return repo, carve


def _gate(repo: Path, *args: str,
          cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo / "scripts" / "neutrality-gate.py"), *args],
        cwd=cwd or repo, capture_output=True, text=True, check=False)


def _report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mode_line(verdict: str, target: str, mode: str) -> re.Pattern[str]:
    return re.compile(rf"^{verdict}\s+target {target}\s+{re.escape(mode)}\s",
                      re.M)


# --------------------------------------------------------------------------
# (a) the shim records and replays
# --------------------------------------------------------------------------

def _run_shim(tmp_path: Path, baseline: str, composed: str,
              argv: tuple[str, ...] = (".", "--strict"),
              ) -> tuple[subprocess.CompletedProcess[bytes],
                         list[dict[str, Any]]]:
    for side, behaviour in (("baseline", baseline), ("composed", composed)):
        _write(tmp_path, f"{side}/contracts/README.md", "toy\n")
        _write(tmp_path, f"{side}/scripts/validate-openxwallet.py",
               _toy(behaviour))
    shim = MODULE.write_shim(tmp_path / "shim.py")
    tree = tmp_path / "tree"
    _write(tree, "a.yaml", "kind: toy\n")
    report = tmp_path / "records.jsonl"
    env = dict(os.environ,
               NEUTRALITY_BASELINE=str(
                   tmp_path / "baseline/scripts/validate-openxwallet.py"),
               NEUTRALITY_COMPOSED=str(
                   tmp_path / "composed/scripts/validate-openxwallet.py"),
               NEUTRALITY_REPORT=str(report))
    done = subprocess.run([sys.executable, str(shim), *argv],
                          cwd=tree, env=env, capture_output=True, check=False)
    records = [json.loads(line) for line in
               report.read_text(encoding="utf-8").splitlines()]
    return done, records


def _replayed(records: list[dict[str, Any]]) -> dict[str, Any]:
    [record] = [r for r in records if r["replayed"]]
    return record


def test_the_shim_records_two_validators_that_agree_and_replays(
        tmp_path: Path) -> None:
    done, records = _run_shim(tmp_path, "same", "same")
    assert len(records) == 2, records
    as_given, toggled = records
    assert (as_given["argv"], as_given["mode"], as_given["replayed"]) == \
        ([".", "--strict"], "strict", True)
    assert (toggled["argv"], toggled["mode"], toggled["replayed"]) == \
        (["."], "plain", False)
    for record in records:
        assert record["identical"] is True
        assert record["help"] is False
        assert record["cwd"] == str(tmp_path / "tree")
        assert record["baseline"]["stdout"] == record["composed"]["stdout"]
        assert "repo scan: 1 yaml file(s)" in record["composed"]["stdout"]
    # The replay IS the as-given composed run.
    assert done.returncode == as_given["composed"]["rc"] == 0
    assert done.stdout.decode() == as_given["composed"]["stdout"]


def test_the_shim_records_a_disagreement_and_replays_the_composed_run(
        tmp_path: Path) -> None:
    done, records = _run_shim(tmp_path, "same", "strict-rc-differs")
    record = _replayed(records)
    assert record["identical"] is False
    assert record["baseline"]["rc"] == 0
    assert record["composed"]["rc"] == 1
    assert done.returncode == 1  # the composed code, replayed
    assert done.stdout.decode() == record["composed"]["stdout"]
    [toggled] = [r for r in records if not r["replayed"]]
    assert (toggled["mode"], toggled["identical"]) == ("plain", True)


def test_the_shim_compares_the_mode_a_suite_never_asked_for(
        tmp_path: Path) -> None:
    """A plain argv is also run with --strict added, and that run is
    recorded, never replayed: the suite still sees the plain run."""
    done, records = _run_shim(tmp_path, "same", "strict-rc-differs",
                              argv=(".",))
    as_given, toggled = records
    assert (as_given["argv"], as_given["mode"], as_given["replayed"],
            as_given["identical"]) == (["."], "plain", True, True)
    assert (toggled["argv"], toggled["mode"], toggled["replayed"],
            toggled["identical"]) == ([".", "--strict"], "strict", False,
                                      False)
    assert done.returncode == 0  # the as-given composed run, replayed
    assert done.stdout.decode() == as_given["composed"]["stdout"]


def test_the_shim_runs_a_help_invocation_once(tmp_path: Path) -> None:
    done, records = _run_shim(tmp_path, "same", "same", argv=("--help",))
    [record] = records
    assert (record["help"], record["replayed"]) == (True, True)
    assert done.stdout.decode() == record["composed"]["stdout"]


@pytest.mark.parametrize("argv, other", [
    ([".", "--strict"], ["."]),
    (["--strict", "."], ["."]),
    (["."], [".", "--strict"]),
    ([".", "--str"], ["."]),  # argparse takes an abbreviation for the flag
    ([], ["--strict"]),
])
def test_strict_is_toggled_both_ways(argv: list[str],
                                     other: list[str]) -> None:
    assert MODULE.toggle_strict(argv) == other
    assert {MODULE.mode_of(argv), MODULE.mode_of(other)} == {"plain",
                                                              "strict"}


def test_the_shim_replays_stderr_and_a_refusal(tmp_path: Path) -> None:
    done, records = _run_shim(tmp_path, "same", "refuses")
    assert [r["identical"] for r in records] == [False, False]
    record = _replayed(records)
    assert done.returncode == 2
    assert done.stdout == b""
    assert b"openWallet/code is not initialized" in done.stderr
    assert done.stderr.decode() == record["composed"]["stderr"]


def test_records_that_do_not_pair_are_a_refusal(tmp_path: Path) -> None:
    """Every tree invocation records one plain and one strict run. A report
    holding only one of them would let a mode go uncompared."""
    suite = MODULE.Suite("kept", tmp_path, tmp_path / "tests" / "toy")
    one = {"help": False, "replayed": True, "mode": "plain",
           "identical": True}
    pair = [one, dict(one, replayed=False, mode="strict")]
    assert MODULE.SuiteResult(suite, pair, 0, "").paired is True
    assert MODULE.SuiteResult(suite, [one], 0, "").paired is False
    assert MODULE.SuiteResult(suite, [one, dict(one, replayed=False)], 0,
                              "").paired is False


def test_the_mirror_is_the_tracked_tree_as_real_directories(
        tmp_path: Path) -> None:
    """A suite that scans its own REPO_ROOT scans the mirror. `os.walk` never
    descends a directory link, so a mirror of linked directories reads no
    nested YAML on either side: identical, and empty. The mirror is the
    tracked tree as real directories and copied files; a gitlink is linked
    (the sweep prunes it through the link, as it prunes the real mount);
    each `scripts/` file is a file link; the shim stands at the validator."""
    repo, _ = _repo(tmp_path, "same", {"toy_suite": TOY_SUITE},
                    {"contracts/deep/record.yaml": "kind: toy\n"})
    nested = repo / "mounted"
    nested.mkdir()
    _git(nested, "init", "-q")
    _git(nested, "commit", "-q", "--allow-empty", "-m", "a nested root")
    _git(repo, "add", "mounted")            # recorded as a gitlink
    _git(repo, "commit", "-q", "-m", "mount a nested repository")
    _write(repo, "untracked.yaml", "kind: toy\n")
    _write(repo, "tests/toy_suite/test_not_yet_added.py", "")
    suite = MODULE.Suite("kept", repo, repo / "tests" / "toy_suite")
    root = MODULE.mirror(suite, tmp_path / "mirror")
    walked = {Path(d, f).relative_to(root).as_posix()
              for d, _, names in os.walk(root) for f in names}
    assert "contracts/deep/record.yaml" in walked, sorted(walked)
    assert "untracked.yaml" not in walked, sorted(walked)
    # The suite's own directory is copied whole, a file not yet added too.
    assert {"tests/toy_suite/test_toy_suite.py",
            "tests/toy_suite/test_not_yet_added.py"} <= walked
    for rel in ("contracts", "contracts/deep", "tests/toy_suite"):
        assert not (root / rel).is_symlink(), rel
    record = root / "contracts" / "deep" / "record.yaml"
    assert not record.is_symlink()
    assert record.resolve() == root.resolve() / "contracts/deep/record.yaml"
    assert (root / "mounted").is_symlink()
    assert (root / "mounted" / ".git").exists()     # so the sweep prunes it
    assert (root / "scripts" / "neutrality-gate.py").is_symlink()
    shim = root / "scripts" / "validate-openxwallet.py"
    assert not shim.is_symlink()
    assert "_GATE.shim_main" in shim.read_text(encoding="utf-8")


def test_every_child_gets_a_tmpdir_inside_the_run(tmp_path: Path) -> None:
    """A temporary file a validator or a suite writes is removed with the
    run's tree, never left in a shared temporary root."""
    with MODULE.children_tmpdir(tmp_path) as tmp:
        assert tmp.parent == tmp_path and tmp.is_dir()
        assert MODULE.child_env()["TMPDIR"] == str(tmp)
        # The shim's children inherit it from the shim's own environment.
        assert MODULE.child_env({"X": "1"})["TMPDIR"] == str(tmp)
    assert MODULE.child_env().get("TMPDIR") == os.environ.get("TMPDIR")


def test_the_shim_refuses_outside_a_gate_run(tmp_path: Path) -> None:
    shim = MODULE.write_shim(tmp_path / "shim.py")
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("NEUTRALITY_")}
    done = subprocess.run([sys.executable, str(shim), "."], env=env,
                          capture_output=True, text=True, check=False)
    assert done.returncode == 2
    assert "NEUTRALITY_BASELINE" in done.stderr, done.stderr


# --------------------------------------------------------------------------
# (b) the carve commit must be reachable
# --------------------------------------------------------------------------

def test_an_unreachable_carve_commit_refuses_and_names_full_history(
        tmp_path: Path) -> None:
    """The default carve commit is not in a throwaway repository, exactly as
    it is not in a depth-1 checkout."""
    repo, _ = _repo(tmp_path)
    done = _gate(repo, "--no-suite-trees")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "[neutrality-carve-unreachable]" in done.stderr, done.stderr
    assert CARVE_COMMIT in done.stderr
    assert "fetch-depth: 0" in done.stderr
    assert PRECEDENT_WORKFLOW in done.stderr
    assert FULL_HISTORY_WORKFLOW in done.stderr


def test_a_carve_commit_that_is_not_an_ancestor_refuses(tmp_path: Path) -> None:
    repo, _ = _repo(tmp_path)
    home = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _git(repo, "checkout", "-q", "--orphan", "elsewhere")
    _git(repo, "commit", "-q", "-m", "an unrelated root")
    stranger = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", home)
    done = _gate(repo, f"--carve-commit={stranger}", "--no-suite-trees")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "NOT AN ANCESTOR of HEAD" in done.stderr, done.stderr


@pytest.mark.parametrize("value", ["main", "HEAD~1", "--output=probe", "abc12",
                                   "z" * 40])
def test_a_carve_commit_that_is_not_hex_is_refused_before_git(
        tmp_path: Path, value: str) -> None:
    repo, _ = _repo(tmp_path)
    done = _gate(repo, f"--carve-commit={value}", "--no-suite-trees")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "[neutrality-carve-invalid]" in done.stderr, done.stderr
    assert not (repo / "probe").exists()


# --------------------------------------------------------------------------
# the verdict, end to end over toys
# --------------------------------------------------------------------------

def test_agreeing_validators_pass_over_the_tree_and_a_suite(
        tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path, "same", {"toy_suite": TOY_SUITE,
                                           "quiet_suite": QUIET_SUITE})
    report = repo / "report.json"
    done = _gate(repo, f"--carve-commit={carve}", f"--report={report}")
    assert done.returncode == 0, done.stdout + done.stderr
    for mode in ("plain", "--strict"):
        assert _mode_line("IDENTICAL", "root", mode).search(done.stdout), \
            done.stdout
    assert re.search(r"^IDENTICAL\s+suite tests/toy_suite\s+2 of 2 tree "
                     r"record\(s\) identical: 1 invocation\(s\) × 2 modes; "
                     r"help 1 of 1 identical", done.stdout, re.M), done.stdout
    assert "SKIP       tests/quiet_suite: no file spells" in done.stdout
    assert "SKIP       openWallet/code/tests (the moved suites)" in done.stdout
    assert ("neutrality-gate: IDENTICAL: 1 tree(s) × 2 modes = 2 target "
            "run(s), and 1 suite invocation(s) × 2 modes = 2 suite record(s) "
            "over 1 suite(s)") in done.stdout, done.stdout
    assert "note  0 test(s) skipped inside the mirror, in 0 of 1 suite(s)" \
        in done.stdout, done.stdout
    evidence = _report(report)
    assert evidence["result"] == "identical"
    assert evidence["exit_code"] == 0
    assert evidence["carve_commit"] == carve
    assert evidence["revision"]["head"] == _git(repo, "rev-parse", "HEAD")
    [suite] = evidence["suites"]
    assert (suite["suite"], suite["tree_invocations"], suite["modes"],
            suite["tree_records"], suite["identical"],
            suite["pytest_rc"]) == ("tests/toy_suite", 1, 2, 2, 2, 0)


def test_a_stdout_difference_fails_with_its_diff(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path, "scan-differs", {"toy_suite": TOY_SUITE})
    report = repo / "report.json"
    done = _gate(repo, f"--carve-commit={carve}", f"--report={report}")
    assert done.returncode == 1, done.stdout + done.stderr
    for mode in ("plain", "--strict"):
        assert _mode_line("DIFFERENT", "root", mode).search(done.stdout)
    assert "+note  repo scan: 0 yaml file(s) (and one more)" in done.stdout
    assert "-note  repo scan: 0 yaml file(s)" in done.stdout
    assert re.search(r"^DIFFERENT\s+suite tests/toy_suite\s+0 of 2",
                     done.stdout, re.M), done.stdout
    evidence = _report(report)
    assert evidence["result"] == "different"
    differences = evidence["suites"][0]["differences"]
    assert [d["mode"] for d in differences] == ["strict", "plain"]
    assert all(d["test"].endswith("::test_a_fixture_tree")
               for d in differences)


def test_a_suite_that_never_asks_for_strict_is_compared_under_strict(
        tmp_path: Path) -> None:
    """The composed toy departs ONLY under --strict, and only over a tree
    holding YAML. The toy root holds none, so target (i) agrees in both
    modes, and the suite asks only for plain runs, which agree too. The one
    difference is the mode the suite never asked for, and the gate must see
    it."""
    repo, carve = _repo(tmp_path, "strict-scan-differs",
                        {"plain_suite": PLAIN_SUITE})
    report = repo / "report.json"
    done = _gate(repo, f"--carve-commit={carve}", f"--report={report}")
    assert done.returncode == 1, done.stdout + done.stderr
    for mode in ("plain", "--strict"):
        assert _mode_line("IDENTICAL", "root", mode).search(done.stdout), \
            done.stdout
    assert re.search(r"^DIFFERENT\s+suite tests/plain_suite\s+1 of 2 tree "
                     r"record\(s\) identical: 1 invocation\(s\) × 2 modes",
                     done.stdout, re.M), done.stdout
    assert "strict (--strict toggled)" in done.stdout, done.stdout
    assert "+note  repo scan: 1 yaml file(s) (strict only)" in done.stdout
    assert "neutrality-gate: DIFFERENT: 1 of 4 comparison(s)" in done.stdout
    [suite] = _report(report)["suites"]
    [difference] = suite["differences"]
    assert (difference["mode"], difference["replayed"]) == ("strict", False)
    # The suite itself passed: it was replayed the plain run it asked for.
    assert suite["pytest_rc"] == 0, suite


def test_an_exit_code_difference_alone_fails(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path, "strict-rc-differs")
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees")
    assert done.returncode == 1, done.stdout + done.stderr
    assert _mode_line("IDENTICAL", "root", "plain").search(done.stdout)
    assert _mode_line("DIFFERENT", "root", "--strict").search(done.stdout)
    assert "stdout byte-identical; the exit codes differ" in done.stdout


def test_a_help_text_difference_is_reported_outside_the_verdict(
        tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path, "help-differs", {"toy_suite": TOY_SUITE})
    report = repo / "report.json"
    done = _gate(repo, f"--carve-commit={carve}", f"--report={report}")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "help 0 of 1 identical" in done.stdout, done.stdout
    suite = _report(report)["suites"][0]
    assert (suite["help_invocations"], suite["help_identical"]) == (1, 0)


def test_a_refusal_at_self_test_is_surfaced_verbatim(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path, "refuses")
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "[neutrality-validator-refused]" in done.stderr
    assert "the composed adapter refused" in done.stderr
    assert ("ERROR openWallet/code is not initialized; run the scoped init"
            in done.stderr), done.stderr
    assert "DIFFERENT" not in done.stdout


def test_a_refusal_over_a_tree_is_never_compared(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path, "refuses-trees")
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "[neutrality-run-refused]" in done.stderr, done.stderr
    assert "ERROR harness failure: toy" in done.stderr


def test_a_suite_that_never_reaches_the_shim_refuses(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path, "same", {"hollow_suite": HOLLOW_SUITE})
    done = _gate(repo, f"--carve-commit={carve}")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "[neutrality-suite-vacuous]" in done.stderr, done.stderr
    assert "tests/hollow_suite" in done.stderr


def test_a_suite_respelled_out_of_discovery_refuses(tmp_path: Path) -> None:
    """Lane 1's case. The respelled suite still runs the validator, but
    discovery skips it with a false reason. UNPINNED (the control) the gate
    then passes over fewer suites; pinned, it refuses before any suite
    runs."""
    unpinned, carve = _repo(tmp_path / "unpinned", "same",
                            {"toy_suite": RESPELLED_SUITE}, expected=[])
    done = _gate(unpinned, f"--carve-commit={carve}")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "SKIP       tests/toy_suite: no file spells" in done.stdout
    assert "over 0 suite(s)" in done.stdout, done.stdout

    pinned, carve = _repo(tmp_path / "pinned", "same",
                          {"toy_suite": RESPELLED_SUITE},
                          expected=["tests/toy_suite"])
    report = pinned / "report.json"
    done = _gate(pinned, f"--carve-commit={carve}", f"--report={report}")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "SKIP       tests/toy_suite: no file spells" in done.stdout
    assert ("neutrality-gate: REFUSED [neutrality-suite-set-mismatch]: "
            "target (iii) discovered 0 suite(s), not the 1 pinned in "
            "EXPECTED_SUITES: missing (each skipped above, with the reason "
            "discovery gave) ['tests/toy_suite'].") in done.stderr, done.stderr
    assert "suite tests/toy_suite" not in done.stdout, done.stdout
    evidence = _report(report)
    assert evidence["refusal"]["code"] == "neutrality-suite-set-mismatch"
    assert evidence["suite_set"] == {"expected": ["tests/toy_suite"],
                                     "discovered": []}


def test_a_suite_the_pin_does_not_name_refuses(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path, "same", {"toy_suite": TOY_SUITE},
                        expected=[])
    done = _gate(repo, f"--carve-commit={carve}")
    assert done.returncode == 2, done.stdout + done.stderr
    assert ("[neutrality-suite-set-mismatch]: target (iii) discovered 1 "
            "suite(s), not the 0 pinned in EXPECTED_SUITES: unexpected "
            "['tests/toy_suite'].") in done.stderr, done.stderr


def test_the_pinned_suite_set_is_this_repositorys() -> None:
    """The seven suites, and the ones discovery finds in this checkout: the
    kept suites always, the moved ones where the code leg is initialized."""
    assert MODULE.EXPECTED_SUITES == (
        "tests/nested_repo_prune", "tests/openwallet_pin",
        "tests/per_seat_register_entries", "tests/register_reissuance",
        "tests/widen_register_reader",
        "openWallet/code/tests/multi_key_wallets",
        "openWallet/code/tests/nested_repo_prune")
    kept, _ = MODULE.discover_suites(REPO_ROOT, "kept")
    assert [s.label for s in kept] == [
        label for label in MODULE.EXPECTED_SUITES
        if label.startswith("tests/")]
    code, why = MODULE.code_leg()
    if code is None:
        pytest.skip(f"the moved suites cannot be discovered here: {why}")
    moved, _ = MODULE.discover_suites(code, "moved")
    assert [s.label for s in moved] == [
        label for label in MODULE.EXPECTED_SUITES
        if label.startswith("openWallet/")]


def test_a_test_that_skips_inside_the_mirror_is_named_not_judged(
        tmp_path: Path) -> None:
    """A skipped test builds no tree in the mirror, so none is compared. The
    gate names it under its suite, in its output and its report, and leaves
    the verdict as the trees it did compare make it."""
    repo, carve = _repo(tmp_path, "same", {"toy_suite": SKIPPING_SUITE})
    report = repo / "report.json"
    done = _gate(repo, f"--carve-commit={carve}", f"--report={report}")
    assert done.returncode == 0, done.stdout + done.stderr
    assert re.search(
        r"^SKIPPED\s+in suite tests/toy_suite: 1 test\(s\) skipped inside the "
        r"mirror and built no tree there, so none of their trees is "
        r"compared; first: tests/toy_suite/test_toy_suite\.py:\d+: needs git "
        r"history the mirror does not have$", done.stdout, re.MULTILINE), \
        done.stdout
    assert ("note  1 test(s) skipped inside the mirror, in 1 of 1 suite(s)"
            in done.stdout), done.stdout
    assert re.search(r"^IDENTICAL\s+suite tests/toy_suite\s+2 of 2 tree "
                     r"record\(s\) identical", done.stdout, re.MULTILINE), \
        done.stdout
    evidence = _report(report)
    assert (evidence["result"], evidence["skipped_tests"]) == ("identical", 1)
    [suite] = evidence["suites"]
    assert suite["skipped_tests"] == 1
    [line] = suite["skip_lines"]
    assert line.startswith("SKIPPED [1] tests/toy_suite/test_toy_suite.py:")
    assert line.endswith(": needs git history the mirror does not have")


def test_the_export_target_needs_a_governance_directory(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path)
    (tmp_path / "export" / "governance").mkdir(parents=True)
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 f"--openxfactory-export={tmp_path / 'export' / 'governance'}")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "[neutrality-export-invalid]" in done.stderr, done.stderr


def test_the_export_target_runs_and_records_its_commit(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path)
    export = tmp_path / "export"
    _write(export, "governance/review-authority/register.yaml", "rows: []\n")
    report = repo / "report.json"
    declared = "c8dde1315e3f4cfdbcc75872306493cb88c9cd2d"
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 f"--openxfactory-export={export}",
                 f"--openxfactory-export-commit={declared}",
                 f"--report={report}")
    assert done.returncode == 0, done.stdout + done.stderr
    for mode in ("plain", "--strict"):
        assert _mode_line("IDENTICAL", "openxfactory-export",
                          mode).search(done.stdout), done.stdout
    evidence = _report(report)
    assert evidence["openxfactory_export"]["declared_commit"] == declared
    assert [t["target"] for t in evidence["targets"]] == \
        ["root", "openxfactory-export"]


# A root that exists on no machine: outside every allowed root, whatever the
# working directory, the temporary directory and the home directory are.
OUTSIDE_ROOT = "/nonexistent-root-xyz"


def _refused_before_the_run(done: subprocess.CompletedProcess[str],
                            code: str) -> None:
    assert done.returncode == 2, done.stdout + done.stderr
    assert f"neutrality-gate: REFUSED [{code}]" in done.stderr, done.stderr
    assert "neutrality-gate: baseline" not in done.stdout, done.stdout


def test_a_relative_report_is_written_below_the_working_directory(
        tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path)
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 "--report=out.json")
    assert done.returncode == 0, done.stdout + done.stderr
    assert _report(repo / "out.json")["result"] == "identical"


def test_a_report_that_climbs_and_comes_back_is_accepted(
        tmp_path: Path) -> None:
    """The check is on the NORMALISED path: `sub/../out-in.json` collapses to
    `out-in.json` in the working directory itself, which is below it."""
    repo, carve = _repo(tmp_path)
    (repo / "sub").mkdir()
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 "--report=sub/../out-in.json")
    assert done.returncode == 0, done.stdout + done.stderr
    assert _report(repo / "out-in.json")["result"] == "identical"


def test_a_report_in_the_parent_of_the_working_directory_is_refused(
        tmp_path: Path) -> None:
    """Run from `repo/sub`, `../out-up.json` lands in `repo`, which is NOT
    below the working directory, so it is refused and nothing is written."""
    repo, carve = _repo(tmp_path)
    (repo / "sub").mkdir()
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 "--report=../out-up.json", cwd=repo / "sub")
    _refused_before_the_run(done, "path-outside-allowed-roots")
    assert not (repo / "out-up.json").exists()


@pytest.mark.parametrize("report", [
    f"{OUTSIDE_ROOT}/out.json", "../outside.json",
    "../../../../../etc/x.json", "sub/../../outside.json"],
    ids=["absolute", "one-up", "far-up", "down-then-up"])
def test_a_report_outside_the_working_directory_is_refused(
        tmp_path: Path, report: str) -> None:
    repo, carve = _repo(tmp_path)
    (repo / "sub").mkdir()
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 f"--report={report}")
    _refused_before_the_run(done, "path-outside-allowed-roots")
    assert "--report" in done.stderr, done.stderr
    assert not (tmp_path / "outside.json").exists()
    assert not Path(OUTSIDE_ROOT).exists()


def test_the_temporary_directory_is_not_a_root_for_the_report(
        tmp_path: Path) -> None:
    """The report is written below the working directory only: an absolute
    path under the temporary directory, which the export may use, is refused
    when the working directory is elsewhere."""
    repo, carve = _repo(tmp_path)
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 f"--report={tmp_path / 'report.json'}")
    _refused_before_the_run(done, "path-outside-allowed-roots")
    assert not (tmp_path / "report.json").exists()


def test_a_report_whose_directory_is_missing_is_refused(tmp_path: Path) -> None:
    """A clearly named code of its own, `report-parent-missing`: the path is
    below the working directory, so it is not an outside-the-directory
    refusal. The gate does not create the directory."""
    repo, carve = _repo(tmp_path)
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 "--report=missing-dir/out.json")
    _refused_before_the_run(done, "report-parent-missing")
    assert not (repo / "missing-dir").exists()


def test_an_export_outside_the_allowed_roots_is_refused(tmp_path: Path) -> None:
    repo, carve = _repo(tmp_path)
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 f"--openxfactory-export={OUTSIDE_ROOT}")
    _refused_before_the_run(done, "path-outside-allowed-roots")
    assert "--openxfactory-export" in done.stderr, done.stderr


def test_the_filesystem_root_is_never_an_allowed_root(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """A container user without a home directory has HOME=/. Its prefix,
    `/`, would admit every absolute path, so only the governance/ check
    would stop an export of `/usr`."""
    monkeypatch.setenv("HOME", "/")
    roots = MODULE.allowed_roots()
    assert os.sep not in roots, roots
    assert all(os.path.dirname(root) != root for root in roots), roots
    if any("/usr".startswith(root.rstrip(os.sep) + os.sep) for root in roots):
        pytest.skip(f"/usr is below an allowed root here ({roots})")
    with pytest.raises(MODULE.GateRefusal) as refused:
        MODULE.contained_path("/usr", kind=MODULE.KIND_EXPORT)
    assert refused.value.code == "path-outside-allowed-roots", \
        refused.value.detail


@pytest.mark.skipif(not Path("/usr").is_dir() or any(
    Path("/usr").is_relative_to(base) for base in MODULE.allowed_roots()),
    reason="needs a directory outside every allowed root")
def test_an_export_link_out_of_the_allowed_roots_is_followed_before_containing(
        tmp_path: Path) -> None:
    """The export's containment check is on the RESOLVED path: a link below
    the temporary directory that points out of the allowed roots does not
    pass. (The report's check is lexical and does not follow links.)"""
    repo, carve = _repo(tmp_path)
    (tmp_path / "escape").symlink_to("/usr", target_is_directory=True)
    done = _gate(repo, f"--carve-commit={carve}", "--no-suite-trees",
                 f"--openxfactory-export={tmp_path / 'escape'}")
    _refused_before_the_run(done, "path-outside-allowed-roots")
    assert "resolves to /usr," in done.stderr, done.stderr


# --------------------------------------------------------------------------
# (c) the real repository
# --------------------------------------------------------------------------

def _carries(commit: str) -> bool:
    done = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True, check=False)
    return done.returncode == 0


def test_the_real_repository_is_neutral_over_its_own_tree(
        tmp_path: Path) -> None:
    """Target (i) over THIS checkout, plain and --strict: exit 0. In CI the
    seat runs in `neutrality-gate.yml`, at full history with both openWallet
    levels initialized."""
    if not _carries(CARVE_COMMIT):
        pytest.skip(f"the carve commit {CARVE_COMMIT} is not in this "
                    "checkout's history (a depth-1 checkout, as "
                    f"pytest-suite's is); {FULL_HISTORY_WORKFLOW} (job "
                    "`neutrality-gate`) runs the gate and this test with "
                    "fetch-depth: 0")
    code, why = MODULE.code_leg()
    if code is None and "not initialized" in (why or ""):
        pytest.skip("openWallet/code is not initialized, so the composed "
                    f"adapter cannot load its core; run `{INIT_LINES[0]}` "
                    f"then `{INIT_LINES[1]}`")
    report = tmp_path / "report.json"
    done = subprocess.run(
        [sys.executable, str(GATE), "--no-suite-trees", f"--report={report}"],
        cwd=tmp_path, capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stdout + done.stderr
    for mode in ("plain", "--strict"):
        assert _mode_line("IDENTICAL", "root", mode).search(done.stdout), \
            done.stdout
    evidence = _report(report)
    assert evidence["result"] == "identical"
    assert evidence["carve_commit"] == CARVE_COMMIT
    if code is not None:
        # D5's declared new line: both sides prune the mounted openWallet/.
        assert evidence["declared_new_line"]["baseline"] is True
        assert evidence["declared_new_line"]["composed"] is True


def test_the_full_history_workflow_runs_the_gate_at_fetch_depth_zero() -> None:
    """The loud skips above are honest only while something runs the seat
    with the carve commit in history and both levels of openWallet
    initialized. Pin the workflow that does."""
    workflow = yaml.safe_load(
        (REPO_ROOT / FULL_HISTORY_WORKFLOW).read_text(encoding="utf-8"))
    triggers = workflow.get("on", workflow.get(True))  # YAML 1.1 reads `on`
    assert triggers == {"pull_request": {"branches": ["main"]}}, triggers
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["neutrality-gate"]
    assert "name" not in job, job
    steps = job["steps"]
    checkout = next(s for s in steps
                    if str(s.get("uses", "")).startswith("actions/checkout@"))
    assert checkout["with"]["fetch-depth"] == 0, checkout
    assert checkout["with"]["submodules"] is False, checkout
    runs = [s["run"] for s in steps if "run" in s]
    assert runs[:2] == list(INIT_LINES), runs
    assert not any("--recursive" in r for r in runs), runs
    assert "python3 scripts/neutrality-gate.py" in runs, runs
    # FR-009 (tests/nested_repo_prune) needs the carve commit too.
    assert ("python3 -m pytest tests/neutrality_gate tests/nested_repo_prune "
            "-q") in runs, runs
    pip = next(r for r in runs if r.startswith("pip install"))
    words = pip.split()
    assert words[2:4] == ["--only-binary", ":all:"], pip
    assert all("==" in p and p.split("==")[1] for p in words[4:]), pip
