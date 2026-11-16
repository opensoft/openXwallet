"""Record complete source runs and preserve actual active parent coverage."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODE = os.environ.get("WALLET_SOURCE_MEASUREMENT")
# Nested pytest probes inherit the current-test marker. They must not publish
# a subset in place of the top-level full-suite receipt.
ACTIVE = bool(MODE) and "PYTEST_CURRENT_TEST" not in os.environ
NODES = []
REPORTS = {}
DESELECTED = False
START_CORE = None


def active_core():
    import coverage

    current = coverage.Coverage.current()
    return dict(current.sys_info()).get("core") if current else None


def pytest_sessionstart():
    global START_CORE
    if ACTIVE:
        if MODE not in ("runtime", "coverage"):
            raise RuntimeError("unknown full-source execution role")
        START_CORE = active_core()
        expected = (3, 12) if MODE == "runtime" else (3, 14)
        if sys.version_info[:2] != expected:
            raise RuntimeError("source execution interpreter differs")
        core = None if MODE == "runtime" else "SysMonitor"
        if START_CORE != core:
            raise RuntimeError("source measurement core differs")


def pytest_collection_finish(session):
    if ACTIVE:
        if session.config.args != ["tests/"]:
            raise RuntimeError("full-source execution must select tests/")
        NODES.extend(sorted(item.nodeid for item in session.items))


def pytest_deselected(items):
    global DESELECTED
    if ACTIVE and items:
        DESELECTED = True


def pytest_runtest_logreport(report):
    if ACTIVE:
        context = getattr(report, "context", None)
        identity = None if context is None else json.loads(json.dumps({
            "message": context.msg, "parameters": dict(context.kwargs),
        }, sort_keys=True, allow_nan=False))
        REPORTS.setdefault(report.nodeid, []).append({
            "phase": report.when, "outcome": report.outcome,
            "subtest": context is not None, "context": identity,
            "xfail": hasattr(report, "wasxfail"),
        })


def pytest_sessionfinish(exitstatus):
    if os.environ.get("COVERAGE_PROCESS_START"):
        import coverage

        current = coverage.Coverage.current()
        if current is None:
            raise RuntimeError("coverage requested but no collector is active")
        # Nested Coverage API tests disable startup autosaving. This public
        # call retains the real parent execution without changing its hits.
        current.save()
    if ACTIVE:
        import coverage

        end_core = active_core()
        if end_core != START_CORE:
            raise RuntimeError("source measurement core changed")
        result = {
            "role": MODE, "python": list(sys.version_info[:3]),
            "coverage_version": coverage.__version__, "core": START_CORE,
            "nodes": NODES, "nodeids_sha256": hashlib.sha256(
                json.dumps(NODES, separators=(",", ":")).encode()).hexdigest(),
            "reports": REPORTS, "deselected": DESELECTED,
            "exitstatus": int(exitstatus),
        }
        with (ROOT / ".coverage-reports/source-suite.json").open("x") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
