"""Save real active parent coverage when nested measurement tests ran.

Independent coverage API tests disable startup autosaving in coverage.py.
The public save call preserves actual execution without changing collection,
tracing filters or hit data. Runtime subprocess isolation remains unchanged.
"""
import os


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("COVERAGE_PROCESS_START"):
        import coverage

        current = coverage.Coverage.current()
        if current is None:
            raise RuntimeError("coverage requested but no collector is active")
        current.save()
