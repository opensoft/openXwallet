"""Required analysis-only calibration with real 3.12/3.14 branch data."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import coverage


def main():
    assert sys.version_info[:2] == (3, 12), "report with the target compiler"
    python312 = os.environ["WALLET_PROBE_PYTHON312"]
    python314 = os.environ["WALLET_PROBE_PYTHON314"]
    root = Path(__file__).resolve().parents[2]
    reports = root / ".coverage-reports"
    directory = reports / "cross-version"
    directory.mkdir(mode=0o700)
    fixture = Path(tempfile.mkdtemp(prefix="source-", dir=directory))
    paths = ["scripts/same.py", "openWallet/code/scripts/same.py",
             "namespace/uncovered.py"]
    for index, name in enumerate(paths):
        path = fixture / name
        path.parent.mkdir(parents=True, exist_ok=True)
        source = ("class Record:\n    value: str\n"
                  "def choose(value):\n    if value:\n        return 1\n    return 2\n")
        if index < 2:
            source += "choose(" + ("True" if index == 0 else "False") + ")\n"
            source += (
                "import coverage,json,sys\n"
                "print(json.dumps({'python':list(sys.version_info[:3]),"
                "'core':dict(coverage.Coverage.current().sys_info())['core']}))\n")
        path.write_text(source)
    config = fixture / "coverage.ini"
    config.write_text("[run]\nbranch=True\nparallel=True\nrelative_files=False\n")
    data_file = fixture / ".coverage"
    observed = {}
    for label, executable, name, core in [
            ("python312", python312, paths[0], "ctrace"),
            ("python314", python314, paths[1], "sysmon")]:
        environment = dict(os.environ, COVERAGE_FILE=str(data_file), COVERAGE_CORE=core)
        environment.pop("COVERAGE_PROCESS_START", None)
        environment.pop("COVERAGE_PROCESS_CONFIG", None)
        path = fixture / name
        output = subprocess.check_output([
            executable, "-m", "coverage", "run", "--rcfile", str(config),
            str(path)], cwd=path.parent.parent, env=environment, text=True, timeout=30)
        observed[label] = json.loads(output)
    assert observed["python312"]["python"][:2] == [3, 12]
    assert observed["python312"]["core"] == "CTracer"
    assert observed["python314"]["python"][:2] == [3, 14]
    assert observed["python314"]["core"] == "SysMonitor"
    previous = Path.cwd()
    try:
        os.chdir(fixture)
        cov = coverage.Coverage(data_file=str(data_file),
                                config_file=False, branch=True)
        cov.set_option("run:relative_files", False)
        cov.set_option("report:include_namespace_packages", True)
        cov.combine(data_paths=[str(fixture)], strict=True, keep=True)
        cov.json_report(morfs=paths, outfile=str(fixture / "coverage.json"))
    finally:
        os.chdir(previous)
    files = json.loads((fixture / "coverage.json").read_text())["files"]
    assert set(files) == set(paths)
    assert 2 in files[paths[0]]["executed_lines"]
    assert 2 in files[paths[1]]["missing_lines"]
    assert 5 in files[paths[0]]["executed_lines"]
    assert 6 in files[paths[0]]["missing_lines"]
    assert 5 in files[paths[1]]["missing_lines"]
    assert 6 in files[paths[1]]["executed_lines"]
    assert not files[paths[2]]["executed_lines"]
    observed["passed"] = True
    observed["reporting_python"] = list(sys.version_info[:3])
    with (reports / "cross-version.json").open("x") as stream:
        json.dump(observed, stream, indent=2)
        stream.write("\n")
    print(json.dumps(observed, indent=2))


if __name__ == "__main__":
    main()
