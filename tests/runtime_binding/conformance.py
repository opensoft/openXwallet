"""Fail-closed offline matrix runner. Source conformance only; no live receipt."""
import argparse
from collections import Counter, defaultdict
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "scripts")]

from runtime_binding.isolation import assert_isolated, private_root
from runtime_binding.matrix_contract import CASES, MODULE_COUNTS, ROOTS


class MatrixAudit:
    def __init__(self, counts=None, cases=None):
        self.expected = dict(MODULE_COUNTS if counts is None else counts)
        self.cases = dict(CASES if cases is None else cases)
        self.nodes, self.phases = set(), defaultdict(dict)
        self.violations, self.case_counts = set(), {}

    def collected(self, nodeids):
        values = list(nodeids)
        self.nodes = set(values)
        counts = Counter(node.split("::", 1)[0] for node in values)
        anchors = Counter(node.split("[", 1)[0] for node in values)
        if counts != self.expected or len(values) != len(self.nodes):
            self.violations.add("collection-drift")
        for case, required in self.cases.items():
            if not required or any(not anchors[anchor] for anchor in required):
                self.violations.add("missing-case-" + case)
            self.case_counts[case] = sum(anchors[anchor] for anchor in required)

    def report(self, nodeid, phase, outcome, *, xfail=False):
        if nodeid not in self.nodes:
            self.violations.add("unexpected-report")
        if phase in self.phases[nodeid]:
            self.violations.add("duplicate-report")
        self.phases[nodeid][phase] = outcome
        if outcome != "passed" or xfail:
            self.violations.add("non-passing-case")

    def complete(self):
        expected = {"setup": "passed", "call": "passed", "teardown": "passed"}
        if not self.nodes or any(self.phases[node] != expected for node in self.nodes):
            self.violations.add("incomplete-run")
        return not self.violations


class ConformancePlugin:
    def __init__(self):
        self.audit = MatrixAudit()

    def pytest_collection_finish(self, session):
        self.audit.collected(item.nodeid for item in session.items)
        if self.audit.violations:
            import pytest
            pytest.exit("runtime-conformance-collection-invalid", returncode=2)

    def pytest_deselected(self, items):
        if items:
            self.audit.violations.add("deselected-cases")

    def pytest_runtest_logreport(self, report):
        self.audit.report(report.nodeid, report.when, report.outcome, xfail=hasattr(report, "wasxfail"))

    def pytest_sessionfinish(self, session, exitstatus):
        complete = self.audit.complete()
        if exitstatus != 0:
            self.audit.violations.add("pytest-error")
        if exitstatus != 0 or not complete:
            session.exitstatus = 1

    def pytest_terminal_summary(self, terminalreporter):
        for case, count in sorted(self.audit.case_counts.items()):
            terminalreporter.write_line(f"runtime-conformance {case}: {count} anchored nodes")
        terminalreporter.write_line("runtime-conformance: " + ("PASS" if not self.audit.violations else "FAIL"))


def selected_owner(path):
    if not path or Path(path).resolve(strict=True) != Path(os.environ["WALLET_BINDING_OWNER_CODE"]).resolve(strict=True):
        raise RuntimeError("owning-source-selection-invalid")
    from factory_binding.test_owner_integration import owner_source
    return owner_source()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-code", required=True)
    parser.add_argument("--temp-root", required=True)
    args = parser.parse_args()
    try:
        assert_isolated()
        root = private_root(args.temp_root, os.geteuid())
        temporary = root / "tmp"
        home = private_root(root / "home", os.geteuid())
        if (Path(os.environ["TMPDIR"]) != temporary or Path(os.environ["HOME"]) != home
                or Path(os.environ["GIT_CONFIG_GLOBAL"]) != home / "gitconfig"
                or any(temporary.iterdir()) or any(home.iterdir())):
            raise RuntimeError("offline-temp-root-invalid")
        os.chdir(ROOT)
        # Verify the same native boundary survives isolated Python exec, not just fork.
        code = ("import sys;sys.path.insert(0," + repr(str(ROOT / "tests")) + ");"
                "from runtime_binding.isolation import assert_isolated;assert_isolated()")
        subprocess.run([sys.executable, "-I", "-B", "-c", code], check=True, timeout=10,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        selected_owner(args.owner_code)
    except Exception:
        print("runtime-conformance-preflight-failed", file=sys.stderr)
        return 2
    import pytest
    plugin = ConformancePlugin()
    result = pytest.main([*ROOTS, "-q", "-rs", "-c", os.devnull, "--rootdir=" + str(ROOT),
                          "-o", "addopts=", "-p", "no:cacheprovider",
                          "--basetemp=" + str(temporary / "pytest"), "--junitxml=" + str(root / "matrix.xml")],
                         plugins=[plugin])
    try:
        selected_owner(args.owner_code)
    except Exception:
        return 2
    return int(result) if result else (0 if plugin.audit.complete() else 1)


if __name__ == "__main__":
    raise SystemExit(main())
