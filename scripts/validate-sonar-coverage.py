#!/usr/bin/env python3
"""Bind real branch coverage to the complete pinned wallet assembly.

Adapted from openXfactory@a31e2060e61fcec47a818ccdcd4d8c675a440505.
Adaptations: complete nested repository inventory, wallet project/baseline and
exact nested gitlink receipts. Coverage and gate refusal checks are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import urllib.parse
import urllib.request
import re
import subprocess
from datetime import datetime
import xml.etree.ElementTree as ET

REPOSITORIES = ("", "openWallet", "openWallet/code", "openWallet/spec")
ROOTS = ("scripts", "openwallet_runtime", "specs", "openspec")
REPORT_DIRECTORY = ".coverage-reports"
COVERAGE_JSON = "coverage.json"
COVERAGE_XML = "coverage.xml"
JUNIT_REPORT = "pytest-report.xml"
MEASUREMENT = "measurement.json"
CONFIGS = (".coveragerc", "sonar-project.properties",
           "requirements/sonar-analysis.lock", "requirements/analysis-shape.lock",
           "requirements/analysis-providers.json")
LIMITS = {
    "new_security_rating": ("GT", "1"),
    "new_reliability_rating": ("GT", "1"),
    "new_maintainability_rating": ("GT", "1"),
    "new_coverage": ("LT", "80"),
    "new_duplicated_lines_density": ("GT", "3"),
    "new_security_hotspots_reviewed": ("LT", "100"),
}


class Refusal(ValueError):
    """Evidence cannot establish measured acceptance."""


def require(condition, message):
    if not condition:
        raise Refusal(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def test_source(name):
    parts = Path(name).parts
    return "tests" in parts or Path(name).name == "conftest.py"


def inventory(root):
    sources = {}
    for prefix in REPOSITORIES:
        checkout = root / prefix
        paths = git(checkout, "ls-files", "-z").split("\0")
        for name in paths:
            if not name.endswith(".py") or test_source(name):
                continue
            require(name.split("/")[0] in ROOTS,
                    f"unclassified Python source: {prefix}/{name}")
            relative = str(Path(prefix) / name)
            path = root / relative
            require(not path.is_symlink() and path.is_file(),
                    f"non-regular source: {relative}")
            require(path.resolve().is_relative_to(root),
                    f"source escaped assembly: {relative}")
            sources[relative] = digest(path)
    require(sources, "empty production inventory")
    return sources


def snapshot(root):
    repositories = {}
    for prefix in REPOSITORIES:
        checkout = root / prefix
        require(checkout.is_dir() and not checkout.is_symlink(),
                f"missing or linked repository: {prefix}")
        require(git(checkout, "rev-parse", "--show-toplevel") == str(checkout),
                f"uninitialized or unexpected repository: {prefix}")
        require(not git(checkout, "diff", "--name-only", "HEAD",
                        "--ignore-submodules"),
                f"tracked source differs from HEAD: {prefix}")
        revision = git(checkout, "rev-parse", "HEAD")
        if prefix:
            parent = Path(prefix).parent
            role = Path(prefix).name
            expected = git(root / parent, "rev-parse", f"HEAD:{role}")
            require(revision == expected, f"nested pin differs: {prefix}")
        repositories[prefix or "."] = {
            "revision": revision, "tree": git(checkout, "rev-parse", "HEAD^{tree}")}
    return {
        "revision": repositories["."]["revision"],
        "tree": repositories["."]["tree"],
        "repositories": repositories,
        "sources": inventory(root),
        "configs": {name: digest(root / name) for name in CONFIGS
                    if (root / name).is_file()},
    }


def report_directory(root, name):
    root = root.resolve()
    target = (root / name).resolve()
    require(target == root / REPORT_DIRECTORY, "report directory must be .coverage-reports")
    require(not (root / REPORT_DIRECTORY).is_symlink(), "symlink report directory")
    return target


def read_json(path):
    require(path.is_file() and path.stat().st_size < 100_000_000, "missing/oversized JSON")
    return json.loads(path.read_text())


def read_xml(path):
    require(path.is_file() and path.stat().st_size < 100_000_000, "missing/oversized XML")
    data = path.read_bytes()
    require(b"<!DOCTYPE" not in data and b"<!ENTITY" not in data, "XML declarations refused")
    return ET.fromstring(data)


def junit_counts(path):
    node = read_xml(path)
    require(node.tag in ("testsuites", "testsuite"), "not JUnit")
    suites = [node] if node.tag == "testsuite" else list(node)
    totals = {key: sum(int(s.get(key, 0)) for s in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    require(totals["tests"] > totals["skipped"] >= 0 and
            totals["failures"] == totals["errors"] == 0, "test suite did not pass")
    require(not node.findall(".//failure") and not node.findall(".//error"),
            "test failure in report")
    return totals


def prepare(root, name):
    directory = report_directory(root, name)
    state = snapshot(root)
    require(not directory.exists(), "existing measurement cannot be reused")
    directory.mkdir(mode=0o700)
    (directory / MEASUREMENT).write_text(json.dumps(state, indent=2) + "\n")
    return directory


def unchanged(root, directory):
    before = read_json(directory / MEASUREMENT)
    require(before == snapshot(root), "source/config/revision changed after measurement")
    return before



AUXILIARY_REPORTS = (
    "code-pytest.xml", "spec-pytest.xml",
    "openspec-adapter-pytest.xml", "openspec-spec-pytest.xml",
    "shape-pytest.xml",
)


def assemble_measurements(root, directory):
    """Combine genuine same-source runs; retain every original report and shard."""
    directory = report_directory(root, directory)
    state = unchanged(root, directory)
    auxiliary = directory / "auxiliary"
    require(not auxiliary.is_symlink() and auxiliary.is_dir(),
            "auxiliary measurement missing")
    require(read_json(auxiliary / MEASUREMENT) == state,
            "auxiliary source/config/revision differs")
    reports = [directory / JUNIT_REPORT,
               *(auxiliary / name for name in AUXILIARY_REPORTS)]
    for path in reports:
        require(not path.is_symlink(), "linked test report")
        junit_counts(path)
    shards = sorted(auxiliary.glob(".coverage.*"))
    require(shards and all(p.is_file() and not p.is_symlink() for p in shards),
            "auxiliary branch data missing or linked")
    for index, path in enumerate(shards):
        destination = directory / (".coverage.auxiliary." + str(index))
        require(not destination.exists(), "measurement already assembled")
        shutil.copyfile(path, destination)
    combined = ET.Element("testsuites")
    for path in reports:
        source = read_xml(path)
        suites = [source] if source.tag == "testsuite" else list(source)
        for suite in suites:
            combined.append(suite)
    ET.ElementTree(combined).write(root / JUNIT_REPORT, encoding="utf-8",
                                   xml_declaration=True)
    return generate_report(root, directory)


def generate_report(root, directory):
    import coverage

    directory = report_directory(root, directory)
    state = unchanged(root, directory)
    totals = junit_counts(root / JUNIT_REPORT)
    cov = coverage.Coverage(data_file=str(directory / ".coverage"),
                            config_file=False, branch=True)
    cov.set_option("run:relative_files", False)
    cov.set_option("report:include_namespace_packages", True)
    cov.combine(data_paths=[str(directory)], strict=True, keep=True)
    require(cov.get_data().has_arcs(), "no real branch data")
    cov.save()
    # Public morfs enumerates zero-hit files once, including namespace packages.
    # No CoverageData hit fabrication and no source/coverage omit list.
    morfs = list(state["sources"])
    cov.xml_report(morfs=morfs, outfile=str(directory / COVERAGE_XML))
    cov.json_report(morfs=morfs, outfile=str(directory / COVERAGE_JSON))
    shutil.copyfile(root / JUNIT_REPORT, directory / JUNIT_REPORT)
    receipt = dict(state, test_counts=totals, coverage_version=coverage.__version__)
    receipt["artifacts"] = {name: digest(directory / name)
                            for name in (COVERAGE_XML, COVERAGE_JSON, JUNIT_REPORT)}
    (directory / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return check_report(root, directory)


def check_report(root, directory):
    import coverage

    directory = report_directory(root, directory)
    receipt = read_json(directory / "receipt.json")
    state = snapshot(root)
    require(all(receipt.get(key) == value for key, value in state.items()),
            "receipt does not match checked-out revision/source/config")
    expected = {COVERAGE_XML, COVERAGE_JSON, JUNIT_REPORT}
    require(set(receipt.get("artifacts", {})) == expected, "incomplete artifacts")
    require(all(digest(directory / name) == value
                for name, value in receipt["artifacts"].items()), "artifact hash mismatch")
    require(junit_counts(directory / JUNIT_REPORT) == receipt["test_counts"],
            "JUnit count mismatch")
    report = read_xml(directory / COVERAGE_XML)
    names = [entry.get("filename") for entry in report.findall(".//class")]
    require(len(names) == len(set(names)) and set(names) == set(state["sources"]),
            "coverage XML must contain every owned production Python file exactly once")
    detail = read_json(directory / COVERAGE_JSON)
    require(detail.get("meta", {}).get("branch_coverage") is True, "branch coverage missing")
    require(set(detail.get("files", {})) == set(names), "JSON/XML inventories differ")
    analyzer = coverage.Coverage(config_file=False, branch=True)
    for entry in report.findall(".//class"):
        name = entry.get("filename")
        lines = entry.findall("lines/line")
        require(len({line.get("number") for line in lines}) == len(lines),
                f"duplicate coverage line in {name}")
        recorded = detail["files"][name]
        expected_lines = set(analyzer.analysis2(str(root / name))[1])
        require((set(recorded["executed_lines"]) | set(recorded["missing_lines"])) ==
                expected_lines, f"executable source omitted in {name}")
        require({int(line.get("number")) for line in lines} == expected_lines,
                f"missing executable lines in {name}")
        require(all((int(line.get("hits")) > 0) ==
                    (int(line.get("number")) in recorded["executed_lines"])
                    for line in lines), f"hit mismatch in {name}")
    return receipt


def validate_gate(status, definition, *, main):
    require(str(definition.get("id")) == "9", "quality gate identity changed")
    declared = {c["metric"]: (c["op"], c["error"]) for c in definition["conditions"]}
    require(declared == LIMITS and len(definition["conditions"]) == len(LIMITS),
            "quality gate conditions changed")
    require(status.get("status") == "OK" and status.get("ignoredConditions") is False,
            "gate is not fully evaluated and green")
    conditions = {c["metricKey"]: c for c in status.get("conditions", [])}
    if main:
        require(set(conditions) == set(LIMITS), "main has unevaluated conditions")
        periods = status.get("periods") or [status.get("period", {})]
        require(any(p.get("mode") == "manual_baseline" and
                    datetime.fromisoformat(p.get("date", "").replace("Z", "+00:00")) ==
                    datetime.fromisoformat("2026-08-27T11:16:42+00:00")
                    for p in periods), "original new-code baseline changed")
    for metric, condition in conditions.items():
        require(metric in LIMITS, "unexpected gate condition")
        op, threshold = LIMITS[metric]
        require((condition.get("comparator"), condition.get("errorThreshold")) ==
                (op, threshold), "evaluated gate threshold changed")
        actual = float(condition["actualValue"])
        require(math.isfinite(actual) and condition.get("status") == "OK" and
                (actual >= float(threshold) if op == "LT" else actual <= float(threshold)),
                f"condition not satisfied: {metric}")




def write_gate_receipt(root, result):
    """Create a fixed receipt through a directory descriptor, never following links."""
    directory = report_directory(root, REPORT_DIRECTORY)
    require(directory.is_dir(), "verified coverage artifact missing")
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        output_fd = os.open("gate.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                            0o600, dir_fd=directory_fd)
        with os.fdopen(output_fd, "w", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    finally:
        os.close(directory_fd)


def verify_server_gate(root):
    """Verify the completed scanner task belongs to this exact source/project."""
    task_file = root / ".scannerwork/report-task.txt"
    require(task_file.is_file(), "scanner task receipt missing")
    task = {line.split("=", 1)[0]: line.split("=", 1)[1]
            for line in task_file.read_text().splitlines() if "=" in line}
    require(task.get("serverUrl") == "https://sonarcloud.io" and
            task.get("projectKey") == "opensoft_openXwallet",
            "scanner server/project changed")
    task_id = task.get("ceTaskId", "")
    require(re.fullmatch(r"[A-Za-z0-9_-]{1,100}", task_id), "invalid task identity")
    token = os.environ.get("SONAR_TOKEN")
    if not token:
        raise Refusal("analysis credential missing")

    def api(endpoint, **params):
        url = "https://sonarcloud.io/api/" + endpoint + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)

    completed = api("ce/task", id=task_id)["task"]
    require(completed.get("status") == "SUCCESS" and
            completed.get("componentKey") == "opensoft_openXwallet",
            "analysis task incomplete or wrong project")
    analysis = completed["analysisId"]
    status = api("qualitygates/project_status", analysisId=analysis)["projectStatus"]
    definition = api("qualitygates/show", organization="opensoft", id="9")
    assigned = api("qualitygates/get_by_project", organization="opensoft",
                   project="opensoft_openXwallet")["qualityGate"]
    require(str(assigned["id"]) == "9", "project gate assignment changed")
    is_main = os.environ.get("GITHUB_REF") == "refs/heads/main"
    validate_gate(status, definition, main=is_main)
    result = {"analysis_id": analysis, "revision": git(root, "rev-parse", "HEAD"),
              "main": is_main, "gate": status, "definition": definition}
    if is_main:
        history = api("project_analyses/search", project="opensoft_openXwallet",
                      branch="main", ps="100")["analyses"]
        matching = [a for a in history if a["key"] == analysis]
        require(len(matching) == 1 and matching[0].get("revision") == result["revision"],
                "main analysis source differs from checked-out main")
        reference = api("project_analyses/search", project="opensoft_openXwallet",
                        branch="main", ps="100", **{"from": "2026-08-27", "to": "2026-08-28"})["analyses"]
        require(len(reference) == 1 and
                reference[0]["key"] == "d434a8d1-6d41-4cfe-9413-e1868fc1c18d" and
                reference[0].get("manualNewCodePeriodBaseline") is True and
                datetime.fromisoformat(reference[0]["date"]) ==
                datetime.fromisoformat("2026-08-27T11:16:42+00:00"),
                "original baseline analysis identity/history changed")
        measures = api("measures/component", component="opensoft_openXwallet", branch="main",
                       metricKeys="new_lines_to_cover,new_coverage")["component"]["measures"]
        values = {m["metric"]: float(m.get("value", next((p["value"] for p in m.get("periods", []) if p["index"] == 1), "nan")))
                  for m in measures}
        require(math.isfinite(values.get("new_lines_to_cover", float("nan"))) and
                values["new_lines_to_cover"] > 0 and
                math.isfinite(values.get("new_coverage", float("nan"))) and
                values["new_coverage"] >= 80, "main lacks real qualifying new coverage")
        result["measures"] = measures
        result["baseline_analysis"] = reference[0]
    write_gate_receipt(root, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "assemble", "report", "check", "gate"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    try:
        if args.command == "prepare":
            result = {"directory": str(prepare(root, REPORT_DIRECTORY))}
        elif args.command == "assemble":
            result = assemble_measurements(root, root / REPORT_DIRECTORY)
        elif args.command == "report":
            result = generate_report(root, root / REPORT_DIRECTORY)
        elif args.command == "gate":
            result = verify_server_gate(root)
        else:
            result = check_report(root, root / REPORT_DIRECTORY)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"coverage evidence refused: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
