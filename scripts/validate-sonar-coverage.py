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
import sys
from datetime import datetime
import xml.etree.ElementTree as ET

REPOSITORIES = ("", "openWallet", "openWallet/code", "openWallet/spec")
ROOTS = ("scripts", "openwallet_runtime", "specs", "openspec")
REPORT_DIRECTORY = ".coverage-reports"
COVERAGE_JSON = "coverage.json"
COVERAGE_XML = "coverage.xml"
JUNIT_REPORT = "pytest-report.xml"
MEASUREMENT = "measurement.json"
SOURCE_SUITE = "source-suite.json"
CORE_PROBE = "core.json"
MEASURED_JUNIT = "measured-pytest.xml"
CROSS_VERSION = "cross-version.json"
SYS_MONITOR = "SysMonitor"
RUNTIME_DIRECTORY = Path("runtime")
ISOLATED_DIRECTORY = Path("isolated")
ISOLATED_CASE = ("tests/runtime_binding/test_hosted_lifecycle.py::"
                 "test_large_final_manifest_cleans_and_audits_above_aggregate_document_limit"
                 "[large-manifest]")
EXECUTION_ARTIFACTS = (
    SOURCE_SUITE, CORE_PROBE, MEASURED_JUNIT, CROSS_VERSION, MEASUREMENT,
    str(RUNTIME_DIRECTORY / MEASUREMENT), "auxiliary/" + MEASUREMENT,
    str(RUNTIME_DIRECTORY / SOURCE_SUITE), str(RUNTIME_DIRECTORY / JUNIT_REPORT),
    str(ISOLATED_DIRECTORY / SOURCE_SUITE), str(ISOLATED_DIRECTORY / CORE_PROBE),
    str(ISOLATED_DIRECTORY / MEASURED_JUNIT), str(ISOLATED_DIRECTORY / MEASUREMENT),
)
CONFIGS = (".coveragerc", "sonar-project.properties",
           "requirements/sonar-analysis.lock", "requirements/analysis-shape.lock",
           "requirements/analysis-providers.json", "requirements/coverage-workload.lock")
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




def core_probe(root):
    """Prove actual parent and child collectors, without changing hit data."""
    import coverage

    current = coverage.Coverage.current()
    require(current is not None, "measurement collector missing")
    parent = {"python": list(sys.version_info[:3]),
              "coverage_version": coverage.__version__,
              "core": dict(current.sys_info()).get("core")}
    program = (
        "import coverage,json,sys; c=coverage.Coverage.current(); "
        "print(json.dumps({'python':list(sys.version_info[:3]),"
        "'coverage_version':coverage.__version__,"
        "'core':dict(c.sys_info()).get('core') if c else None}))")
    child = json.loads(subprocess.check_output(
        [sys.executable, "-c", program], text=True, timeout=30))
    result = {"parent": parent, "child": child}
    validate_core_probe(result, os.environ.get("WALLET_SOURCE_MEASUREMENT", "coverage"))
    directory = report_directory(root, REPORT_DIRECTORY)
    with (directory / CORE_PROBE).open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    return result


def validate_core_probe(probe, role="coverage"):
    require(set(probe) == {"parent", "child"}, "incomplete collector probe")
    require(role in ("coverage", "isolated"), "invalid collector role")
    version, core = ([3, 14], SYS_MONITOR) if role == "isolated" else ([3, 12], "CTracer")
    for row in probe.values():
        require(row.get("python", [])[:2] == version
                and row.get("coverage_version") == "7.16.2"
                and row.get("core") == core,
                "actual parent/child measurement core differs")


def validate_phases(phases):
    require(phases and all(
        set(p) == {"phase", "outcome", "subtest", "xfail", "context"}
        and p["outcome"] == "passed" and p["xfail"] is False
        and type(p["subtest"]) is bool for p in phases),
        "source assertion failed, skipped or expected-failure")
    for phase in phases:
        context = phase["context"]
        require((isinstance(context, dict)
                 and set(context) == {"message", "parameters"}
                 and (context["message"] is None or isinstance(context["message"], str))
                 and isinstance(context["parameters"], dict)
                 and all(isinstance(key, str) for key in context["parameters"]))
                if phase["subtest"] else context is None,
                "source subtest identity missing or malformed")
    regular = [p["phase"] for p in phases if not p["subtest"]]
    require(regular == ["setup", "call", "teardown"],
            "source assertion phases are incomplete or repeated")
    require(all(p["phase"] == "call" for p in phases if p["subtest"]),
            "invalid subtest phase")


def validate_source_execution(row, role):
    require(role in ("runtime", "coverage", "isolated"), "invalid source role")
    expected = [3, 14] if role == "isolated" else [3, 12]
    core = {"runtime": None, "coverage": "CTracer", "isolated": SYS_MONITOR}[role]
    require(row.get("role") == role and row.get("python", [])[:2] == expected
            and row.get("core") == core
            and row.get("coverage_version") == "7.16.2",
            "source execution role/interpreter/core differs")
    collection, nodes = row.get("collection"), row.get("nodes")
    for names in (collection, nodes):
        require(isinstance(names, list) and names
                and all(isinstance(n, str) for n in names),
                "source collection missing")
        require(names == sorted(set(names)), "duplicate or unordered source identities")
    def fingerprint(names):
        return hashlib.sha256(
            json.dumps(names, separators=(",", ":")).encode()).hexdigest()
    require(row.get("nodeids_sha256") == fingerprint(nodes)
            and row.get("collection_sha256") == fingerprint(collection)
            and row.get("exitstatus") == 0, "source collection or execution did not qualify")
    if role == "runtime":
        selected = collection
    else:
        require(ISOLATED_CASE in collection, "fixed isolated case missing")
        selected = ([ISOLATED_CASE] if role == "isolated"
                    else [name for name in collection if name != ISOLATED_CASE])
    require(nodes == selected
            and row.get("deselected") == sorted(set(collection) - set(selected)),
            "source selection differs from the fixed complete partition")
    reports = row.get("reports", {})
    require(set(reports) == set(nodes), "source assertion report missing")
    for phases in reports.values():
        validate_phases(phases)
    return {"python": row["python"], "coverage_version": row["coverage_version"],
            "core": row["core"], "tests": len(nodes),
            "nodeids_sha256": fingerprint(nodes),
            "collection_sha256": fingerprint(collection)}


def compare_source_executions(runtime, measured, probe, isolated, isolated_probe):
    summary = {role: validate_source_execution(row, role)
               for role, row in (("runtime", runtime), ("coverage", measured),
                                 ("isolated", isolated))}
    require(runtime["collection"] == measured["collection"] == isolated["collection"],
            "runtime and measurement full collections differ")
    require(not set(measured["nodes"]) & set(isolated["nodes"])
            and set(measured["nodes"]) | set(isolated["nodes"]) == set(runtime["nodes"]),
            "measurement partitions are not a disjoint complete union")
    require({**measured["reports"], **isolated["reports"]} == runtime["reports"],
            "runtime and measurement did not execute identical passing assertions")
    for role, row, actual in (("coverage", measured, probe),
                              ("isolated", isolated, isolated_probe)):
        validate_core_probe(actual, role)
        require(actual["parent"]["python"] == row["python"],
                "measurement probe interpreter differs")
        summary[role]["core_probe"] = actual
    return summary



def validate_cross_version(probe):
    require(probe.get("passed") is True
            and probe.get("reporting_python", [])[:2] == [3, 12],
            "cross-version coverage probe did not preserve the target denominator")
    for name, version, core in (("python312", [3, 12], "CTracer"),
                                ("python314", [3, 14], SYS_MONITOR)):
        row = probe.get(name, {})
        require(row.get("python", [])[:2] == version and row.get("core") == core,
                "cross-version coverage probe used the wrong interpreter/core")

def require_parent_shard(directory, row):
    import coverage

    parent = row.get("parent_shard")
    require(isinstance(parent, dict) and set(parent) == {"name", "sha256"},
            "parent measurement shard identity missing")
    name = parent.get("name", "")
    require(isinstance(name, str)
            and re.fullmatch(r"\.coverage\.[A-Za-z0-9_.-]+", name) is not None,
            "parent measurement shard identity missing")
    path = directory / name
    require(path.is_file() and not path.is_symlink()
            and digest(path) == parent.get("sha256"),
            "parent measurement shard missing, linked or changed")
    data = coverage.CoverageData(basename=str(path))
    try:
        data.read()
    except coverage.exceptions.CoverageException:
        raise Refusal("parent measurement shard is not coverage data") from None
    require(data.has_arcs() and any(data.arcs(name) for name in data.measured_files()),
            "parent measurement shard has no observed branch data")


def execution_evidence(directory):
    runtime, isolated = directory / RUNTIME_DIRECTORY, directory / ISOLATED_DIRECTORY
    accepted = read_json(runtime / SOURCE_SUITE)
    measured = read_json(directory / SOURCE_SUITE)
    separate = read_json(isolated / SOURCE_SUITE)
    require_parent_shard(directory, measured)
    require_parent_shard(isolated, separate)
    totals = [junit_counts(path) for path in (
        runtime / JUNIT_REPORT, directory / MEASURED_JUNIT, isolated / MEASURED_JUNIT)]
    require(all(totals[0][key] == totals[1][key] + totals[2][key] for key in totals[0]),
            "runtime and measured JUnit totals differ")
    result = compare_source_executions(
        accepted, measured, read_json(directory / CORE_PROBE),
        separate, read_json(isolated / CORE_PROBE))
    cross_version = read_json(directory / CROSS_VERSION)
    validate_cross_version(cross_version)
    result["cross_version"] = cross_version
    return result


AUXILIARY_REPORTS = (
    "code-pytest.xml", "spec-pytest.xml",
    "openspec-adapter-pytest.xml", "openspec-spec-pytest.xml",
    "shape-pytest.xml",
)


def assemble_measurements(root, directory):
    """Combine genuine same-source runs; retain every original report and shard."""
    directory = report_directory(root, directory)
    state = unchanged(root, directory)
    runtime = directory / RUNTIME_DIRECTORY
    require(not runtime.is_symlink() and runtime.is_dir(),
            "runtime acceptance evidence missing")
    require(read_json(runtime / MEASUREMENT) == state,
            "runtime source/config/revision differs")
    isolated = directory / ISOLATED_DIRECTORY
    require(not isolated.is_symlink() and isolated.is_dir(),
            "isolated measurement evidence missing")
    require(read_json(isolated / MEASUREMENT) == state,
            "isolated source/config/revision differs")
    execution = execution_evidence(directory)
    auxiliary = directory / "auxiliary"
    require(not auxiliary.is_symlink() and auxiliary.is_dir(),
            "auxiliary measurement missing")
    require(read_json(auxiliary / MEASUREMENT) == state,
            "auxiliary source/config/revision differs")
    reports = [runtime / JUNIT_REPORT, directory / MEASURED_JUNIT,
               isolated / MEASURED_JUNIT,
               *(auxiliary / name for name in AUXILIARY_REPORTS)]
    for path in reports:
        require(not path.is_symlink(), "linked test report")
        junit_counts(path)
    for role, folder in (("auxiliary", auxiliary), ("isolated", isolated)):
        shards = sorted(folder.glob(".coverage.*"))
        require(shards and all(p.is_file() and not p.is_symlink() for p in shards),
                role + " branch data missing or linked")
        for index, path in enumerate(shards):
            destination = directory / (".coverage." + role + "." + str(index))
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
    return generate_report(root, directory, execution=execution)


def generate_report(root, directory, *, execution=None):
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
    receipt = dict(state, test_counts=totals, coverage_version=coverage.__version__,
                   reporting_python=list(sys.version_info[:3]))
    names = [COVERAGE_XML, COVERAGE_JSON, JUNIT_REPORT]
    if execution is not None:
        receipt["execution"] = execution
        names.extend(EXECUTION_ARTIFACTS)
    receipt["artifacts"] = {name: digest(directory / name) for name in names}
    (directory / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return check_report(root, directory)



def executable_inventory(root, names, *, require_target):
    """Use the real target compiler; retain every 3.12 executable line."""
    import coverage

    analyzer = coverage.Coverage(data_file=None, config_file=False, branch=True)
    local = {name: set(analyzer.analysis2(str(root / name))[1]) for name in names}
    if not require_target or sys.version_info[:2] == (3, 12):
        return local
    selected = os.environ.get("WALLET_TARGET_PYTHON")
    require(selected and sys.version_info[:2] == (3, 14),
            "independent audit needs the operator-selected Python 3.12")
    program = (
        "import coverage,json,sys; from pathlib import Path; "
        "d=json.load(sys.stdin); "
        "c=coverage.Coverage(data_file=None,config_file=False,branch=True); "
        "print(json.dumps({'python':list(sys.version_info[:3]),"
        "'coverage_version':coverage.__version__,"
        "'files':{n:c.analysis2(str(Path(d['root'])/n))[1] for n in d['names']}}))")
    result = json.loads(subprocess.check_output(
        [selected, "-c", program],
        input=json.dumps({"root": str(root), "names": list(names)}),
        text=True, timeout=60))
    require(result.get("python", [])[:2] == [3, 12]
            and result.get("coverage_version") == "7.16.2"
            and set(result.get("files", {})) == set(names),
            "target compiler identity or inventory differs")
    target = {name: set(lines) for name, lines in result["files"].items()}
    require(all(local[name] <= target[name] for name in names),
            "analysis compiler has executable lines absent from the target")
    return target

def check_report(root, directory, *, require_execution=False):
    directory = report_directory(root, directory)
    receipt = read_json(directory / "receipt.json")
    state = snapshot(root)
    require(all(receipt.get(key) == value for key, value in state.items()),
            "receipt does not match checked-out revision/source/config")
    expected = {COVERAGE_XML, COVERAGE_JSON, JUNIT_REPORT}
    if require_execution or "execution" in receipt:
        expected.update(EXECUTION_ARTIFACTS)
        require(receipt.get("execution") == execution_evidence(directory),
                "source execution evidence changed")
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
    if require_execution:
        require(receipt.get("reporting_python", [])[:2] == [3, 12],
                "production coverage denominator was not reported under Python 3.12")
    statements = executable_inventory(root, names, require_target=require_execution)
    for entry in report.findall(".//class"):
        name = entry.get("filename")
        lines = entry.findall("lines/line")
        require(len({line.get("number") for line in lines}) == len(lines),
                f"duplicate coverage line in {name}")
        recorded = detail["files"][name]
        expected_lines = statements[name]
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
    parser.add_argument("command", choices=("prepare", "verify-source", "core", "assemble", "report", "check", "gate"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    try:
        if args.command == "prepare":
            result = {"directory": str(prepare(root, REPORT_DIRECTORY))}
        elif args.command == "verify-source":
            result = unchanged(root, root / REPORT_DIRECTORY)
        elif args.command == "core":
            result = core_probe(root)
        elif args.command == "assemble":
            require(sys.version_info[:2] == (3, 12),
                    "production reporting requires the target Python 3.12")
            result = assemble_measurements(root, root / REPORT_DIRECTORY)
        elif args.command == "report":
            result = generate_report(root, root / REPORT_DIRECTORY)
        elif args.command == "gate":
            result = verify_server_gate(root)
        else:
            result = check_report(root, root / REPORT_DIRECTORY, require_execution=True)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"coverage evidence refused: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
