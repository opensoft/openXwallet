"""Real miniature execution and refusal tests for transferable coverage evidence."""
from __future__ import annotations

import importlib.util
import json
import os
import hashlib
import sys
from pathlib import Path
import runpy
import subprocess
import xml.etree.ElementTree as ET

import coverage
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate-sonar-coverage.py"


@pytest.fixture
def tool():
    spec = importlib.util.spec_from_file_location("_sonar_coverage", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REPOSITORIES = ("",)
    return module


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True)


@pytest.fixture
def repository(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    for name in ("scripts", "xfactory", "experiments", "specs", "openspec", "tests"):
        (root / name).mkdir()
    (root / "scripts/covered.py").write_text(
        "def choose(value):\n    if value:\n        return 1\n    return 2\nchoose(True)\n")
    (root / "scripts/namespace").mkdir()
    (root / "scripts/namespace/unreached.py").write_text(
        "def untouched(value):\n    if value:\n        return 3\n    return 4\n")
    (root / "tests/test_fixture.py").write_text("def test_fixture():\n    assert True\n")
    for name in (".coveragerc", "sonar-project.properties", ".gitignore"):
        (root / name).write_bytes((ROOT / name).read_bytes())
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Synthetic")
    git(root, "config", "user.email", "synthetic@example.invalid")
    git(root, "add", ".")
    git(root, "commit", "-qm", "synthetic source")
    monkeypatch.chdir(root)
    return root


def measured(tool, root):
    directory = tool.prepare(root, ".coverage-reports")
    cov = coverage.Coverage(data_file=str(directory / ".coverage"),
                            data_suffix=True, branch=True, config_file=False)
    cov.set_option("run:relative_files", False)
    cov.set_option("run:include", [str(root / "scripts/*")])
    cov.start()
    try:
        runpy.run_path(str(root / "scripts/covered.py"))
    finally:
        cov.stop()
        cov.save()
    (root / "pytest-report.xml").write_text(
        '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0">'
        '<testcase classname="synthetic" name="executed"/></testsuite></testsuites>')
    tool.generate_report(root, directory)
    return directory


def test_real_execution_keeps_zero_hit_namespace_files(tool, repository):
    directory = measured(tool, repository)
    report = ET.parse(directory / "coverage.xml")
    files = {c.attrib["filename"]: c for c in report.findall(".//class")}
    assert set(files) == {"scripts/covered.py", "scripts/namespace/unreached.py"}
    assert any(int(line.attrib["hits"]) > 0
               for line in files["scripts/covered.py"].findall("lines/line"))
    assert all(int(line.attrib["hits"]) == 0
               for line in files["scripts/namespace/unreached.py"].findall("lines/line"))
    assert any(line.attrib.get("branch") == "true"
               for line in files["scripts/namespace/unreached.py"].findall("lines/line"))
    receipt = tool.check_report(repository, directory)
    assert len(receipt["sources"]) == 2
    assert receipt["test_counts"]["failures"] == 0


def test_missing_production_file_in_xml_refuses(tool, repository):
    directory = measured(tool, repository)
    report = ET.parse(directory / "coverage.xml")
    package = report.find(".//classes")
    package.remove(package.findall("class")[-1])
    report.write(directory / "coverage.xml")
    with pytest.raises(tool.Refusal):
        tool.check_report(repository, directory)


def test_source_edit_after_measurement_refuses(tool, repository):
    directory = measured(tool, repository)
    (repository / "scripts/covered.py").write_text("different = 1\n")
    with pytest.raises(tool.Refusal):
        tool.check_report(repository, directory)


def test_report_directory_cannot_escape_root(tool, repository, tmp_path):
    outside = tmp_path / "outside"
    with pytest.raises(tool.Refusal):
        tool.prepare(repository, str(outside))
    assert not outside.exists()


def test_existing_measurement_is_not_reused(tool, repository):
    tool.prepare(repository, ".coverage-reports")
    with pytest.raises(tool.Refusal):
        tool.prepare(repository, ".coverage-reports")


def test_unclassified_python_is_not_silently_omitted(tool, repository):
    (repository / "unclassified.py").write_text("value = 1\n")
    git(repository, "add", "unclassified.py")
    git(repository, "commit", "-qm", "new unclassified source")
    with pytest.raises(tool.Refusal, match="unclassified"):
        tool.prepare(repository, ".coverage-reports")


def test_failed_test_report_cannot_qualify_coverage(tool, repository):
    directory = tool.prepare(repository, ".coverage-reports")
    (repository / "pytest-report.xml").write_text(
        '<testsuite tests="1" failures="1" errors="0" skipped="0"/>')
    with pytest.raises(tool.Refusal):
        tool.generate_report(repository, directory)


def valid_gate():
    limits = {
        "new_security_rating": ("GT", "1", "1"),
        "new_reliability_rating": ("GT", "1", "1"),
        "new_maintainability_rating": ("GT", "1", "1"),
        "new_coverage": ("LT", "80", "82.5"),
        "new_duplicated_lines_density": ("GT", "3", "0.3"),
        "new_security_hotspots_reviewed": ("LT", "100", "100"),
    }
    definition = {"id": 9, "name": "Sonar way", "conditions": [
        {"metric": metric, "op": op, "error": threshold}
        for metric, (op, threshold, _) in limits.items()]}
    status = {"status": "OK", "ignoredConditions": False,
              "periods": [{"index": 1, "mode": "manual_baseline",
                           "date": "2026-08-27T11:16:42Z"}],
              "conditions": [
                  {"metricKey": metric, "comparator": op, "errorThreshold": threshold,
                   "actualValue": actual, "status": "OK"}
                  for metric, (op, threshold, actual) in limits.items()]}
    return status, definition


def test_main_requires_all_existing_evaluated_conditions(tool):
    status, definition = valid_gate()
    tool.validate_gate(status, definition, main=True)


@pytest.mark.parametrize("change", ["missing-coverage", "low-coverage", "different-period",
                                   "lower-threshold", "ignored", "neutral", "nonfinite"])
def test_incomplete_or_weakened_gate_refuses(tool, change):
    status, definition = valid_gate()
    if change == "missing-coverage":
        status["conditions"] = [c for c in status["conditions"] if c["metricKey"] != "new_coverage"]
    elif change == "low-coverage":
        next(c for c in status["conditions"] if c["metricKey"] == "new_coverage")["actualValue"] = "79.9"
    elif change == "different-period":
        status["periods"][0]["date"] = "2026-11-14T00:00:00Z"
    elif change == "lower-threshold":
        next(c for c in definition["conditions"] if c["metric"] == "new_coverage")["error"] = "70"
    elif change == "ignored":
        status["ignoredConditions"] = True
    elif change == "nonfinite":
        status["conditions"][0]["actualValue"] = "NaN"
    else:
        status["status"] = "NONE"
    with pytest.raises(tool.Refusal):
        tool.validate_gate(status, definition, main=True)

def test_subprocess_startup_records_real_child_execution(tool, repository):
    directory = tool.prepare(repository, ".coverage-reports")
    env = dict(os.environ, COVERAGE_PROCESS_START=str(repository / ".coveragerc"),
               COVERAGE_ROOT=str(repository), COVERAGE_FILE=str(directory / ".coverage"))
    # A nested measurement must not inherit the outer run's serialized config.
    # Its real child records to this synthetic repository, while the outer
    # tracer continues to measure the production report/refusal code.
    env.pop("COVERAGE_PROCESS_CONFIG", None)
    subprocess.run([sys.executable, str(repository / "scripts/covered.py")],
                   cwd=repository, env=env, check=True)
    (repository / "pytest-report.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0"/>')
    tool.generate_report(repository, directory)
    detail = json.loads((directory / "coverage.json").read_text())["files"]
    assert 3 in detail["scripts/covered.py"]["executed_lines"]
    assert 4 in detail["scripts/covered.py"]["missing_lines"]
    assert detail["scripts/namespace/unreached.py"]["executed_lines"] == []


def test_matching_forged_reports_cannot_remove_executable_source(tool, repository):
    directory = measured(tool, repository)
    detail = json.loads((directory / "coverage.json").read_text())
    detail["files"]["scripts/namespace/unreached.py"]["missing_lines"].remove(4)
    (directory / "coverage.json").write_text(json.dumps(detail))
    xml = ET.parse(directory / "coverage.xml")
    for entry in xml.findall(".//class"):
        if entry.get("filename") == "scripts/namespace/unreached.py":
            lines = entry.find("lines")
            lines.remove(next(line for line in lines if line.get("number") == "4"))
    xml.write(directory / "coverage.xml")
    receipt = json.loads((directory / "receipt.json").read_text())
    for name in ("coverage.xml", "coverage.json"):
        receipt["artifacts"][name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()
    (directory / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(tool.Refusal, match="executable source omitted"):
        tool.check_report(repository, directory)


@pytest.mark.parametrize("failure", [None, "wrong-revision", "moved-baseline", "empty-denominator",
                                   "uncomputed-gate", "wrong-task-project"])
def test_server_gate_binds_main_revision_reference_and_real_measurement(
        tool, repository, monkeypatch, failure):
    """Exercise the real gate reader against recorded API response shapes."""
    import io
    from urllib.parse import urlsplit, parse_qs

    (repository / ".coverage-reports").mkdir()
    scanner = repository / ".scannerwork"
    scanner.mkdir()
    (scanner / "report-task.txt").write_text(
        "serverUrl=https://sonarcloud.io\nprojectKey=opensoft_openXwallet\nceTaskId=synthetic-task\n")
    monkeypatch.setenv("SONAR_TOKEN", "synthetic-never-transmitted")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    status, definition = valid_gate()
    revision = git(repository, "rev-parse", "HEAD").strip()
    reference = {"key": "d434a8d1-6d41-4cfe-9413-e1868fc1c18d",
                 "date": "2026-08-27T07:16:42-04:00",
                 "manualNewCodePeriodBaseline": failure != "moved-baseline"}

    def response(request, timeout):
        parts = urlsplit(request.full_url)
        assert parts.scheme == "https"
        assert parts.netloc == "sonarcloud.io"
        query = parse_qs(parts.query)
        if parts.path == "/api/ce/task":
            result = {"task": {"status": "SUCCESS", "analysisId": "analysis-044",
                              "componentKey": ("other" if failure == "wrong-task-project"
                                               else "opensoft_openXwallet")}}
        elif parts.path == "/api/qualitygates/project_status":
            assert query["analysisId"] == ["analysis-044"]
            result = {"projectStatus": dict(status, status="NONE")
                      if failure == "uncomputed-gate" else status}
        elif parts.path == "/api/qualitygates/show":
            result = definition
        elif parts.path == "/api/qualitygates/get_by_project":
            result = {"qualityGate": {"id": "9"}}
        elif parts.path == "/api/project_analyses/search":
            result = {"analyses": [reference] if "from" in query else [
                {"key": "analysis-044", "revision": "0" * 40
                 if failure == "wrong-revision" else revision}]}
        elif parts.path == "/api/measures/component":
            result = {"component": {"measures": [
                {"metric": "new_lines_to_cover", "periods": [
                    {"index": 1, "value": "0" if failure == "empty-denominator" else "123"}]},
                {"metric": "new_coverage", "periods": [{"index": 1, "value": "82.5"}]},
            ]}}
        else:
            pytest.fail(f"unexpected endpoint: {parts.path}")
        return io.StringIO(json.dumps(result))

    monkeypatch.setattr(tool.urllib.request, "urlopen", response)
    if failure:
        with pytest.raises(tool.Refusal):
            tool.verify_server_gate(repository)
    else:
        result = tool.verify_server_gate(repository)
        assert result["revision"] == revision
        assert result["analysis_id"] == "analysis-044"
        saved = (repository / ".coverage-reports/gate.json").read_text()
        assert "synthetic-never-transmitted" not in saved
        assert json.loads(saved)["baseline_analysis"] == reference


def test_nested_measurement_preserves_real_parent_execution(tmp_path):
    """The required pytest invocation must save its own real production hits."""
    data_file = tmp_path / "parent.coverage"
    env = dict(os.environ, COVERAGE_PROCESS_START=str(ROOT / ".coveragerc"),
               COVERAGE_ROOT=str(ROOT), COVERAGE_FILE=str(data_file))
    env.pop("COVERAGE_PROCESS_CONFIG", None)
    child = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/sonar_quality/test_coverage_evidence.py::test_real_execution_keeps_zero_hit_namespace_files",
         "-q"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert child.returncode == 0, child.stdout + child.stderr
    seen = set()
    for path in [data_file, *tmp_path.glob("parent.coverage.*")]:
        if path.is_file():
            data = coverage.CoverageData(basename=str(path))
            data.read()
            seen.update(data.measured_files())
    assert SCRIPT.resolve() in {(ROOT / name).resolve() for name in seen}, seen


@pytest.mark.parametrize("existing", ["regular", "symlink", "directory"])
def test_gate_receipt_never_overwrites_existing_evidence(tool, repository, tmp_path, existing):
    directory = repository / ".coverage-reports"
    directory.mkdir()
    outside = tmp_path / "original.json"
    outside.write_text("original evidence")
    target = directory / "gate.json"
    if existing == "regular":
        target.write_text("existing receipt")
    elif existing == "symlink":
        target.symlink_to(outside)
    else:
        target.mkdir()
    with pytest.raises(OSError):
        tool.write_gate_receipt(repository, {"untrusted": "../../original.json"})
    assert outside.read_text() == "original evidence"
    if existing == "regular":
        assert target.read_text() == "existing receipt"


def test_gate_json_content_cannot_select_an_output_path(tool, repository, tmp_path):
    directory = repository / ".coverage-reports"
    directory.mkdir()
    content = {"untrusted": "../../outside.json", "path": str(tmp_path / "outside.json")}
    tool.write_gate_receipt(repository, content)
    assert json.loads((directory / "gate.json").read_text()) == content
    assert (directory / "gate.json").stat().st_mode & 0o777 == 0o600
    assert not (tmp_path / "outside.json").exists()




def full_assembly(tool, repository):
    """Independent miniature repositories with genuine nested Git links."""
    for prefix in ("openWallet/code", "openWallet/spec", "openWallet"):
        checkout = repository / prefix
        checkout.mkdir(parents=True, exist_ok=True)
        (checkout / "README.md").write_text("Synthetic assembly fixture.\n")
        git(checkout, "init", "-q", "-b", "main")
        git(checkout, "config", "user.name", "Synthetic")
        git(checkout, "config", "user.email", "synthetic@example.invalid")
        git(checkout, "add", "README.md")
        if prefix == "openWallet":
            git(checkout, "add", "code", "spec")
        git(checkout, "commit", "-qm", "synthetic nested source")
    git(repository, "add", "openWallet")
    git(repository, "commit", "-qm", "synthetic assembly pin")
    tool.REPOSITORIES = ("", "openWallet", "openWallet/code", "openWallet/spec")
    return tool.snapshot(repository)


def test_complete_assembly_receipt_binds_each_git_revision(tool, repository):
    state = full_assembly(tool, repository)
    assert set(state["repositories"]) == {".", "openWallet", "openWallet/code",
                                           "openWallet/spec"}


def test_dirty_nested_repository_cannot_supply_analysis(tool, repository):
    full_assembly(tool, repository)
    (repository / "openWallet/spec/README.md").write_text("Changed.\n")
    with pytest.raises(tool.Refusal, match="tracked source differs"):
        tool.snapshot(repository)


def test_unpinned_nested_revision_cannot_supply_analysis(tool, repository):
    full_assembly(tool, repository)
    child = repository / "openWallet/code"
    (child / "README.md").write_text("Advanced.\n")
    git(child, "add", "README.md")
    git(child, "commit", "-qm", "different synthetic source")
    with pytest.raises(tool.Refusal, match="nested pin differs"):
        tool.snapshot(repository)


def test_missing_nested_repository_cannot_be_silently_omitted(tool, repository):
    full_assembly(tool, repository)
    (repository / "openWallet/spec").rename(repository / "parked-spec")
    with pytest.raises(tool.Refusal, match="missing or linked"):
        tool.snapshot(repository)


def auxiliary(tool, root, directory):
    import shutil

    selected = directory / "auxiliary"
    selected.mkdir()
    shutil.copyfile(directory / "measurement.json", selected / "measurement.json")
    for name in tool.AUXILIARY_REPORTS:
        shutil.copyfile(root / "pytest-report.xml", selected / name)
    for shard in directory.glob(".coverage.*"):
        shutil.copyfile(shard, selected / shard.name)
    runtime = directory / "runtime"
    runtime.mkdir()
    shutil.copyfile(directory / "measurement.json", runtime / "measurement.json")
    shutil.copyfile(root / "pytest-report.xml", runtime / "pytest-report.xml")
    shutil.copyfile(root / "pytest-report.xml", directory / tool.MEASURED_JUNIT)
    isolated = directory / "isolated"
    isolated.mkdir()
    shutil.copyfile(directory / "measurement.json", isolated / "measurement.json")
    shutil.copyfile(root / "pytest-report.xml", isolated / tool.MEASURED_JUNIT)
    for shard in directory.glob(".coverage.*"):
        shutil.copyfile(shard, isolated / shard.name)
    (runtime / "pytest-report.xml").write_text(
        '<testsuite tests="2" failures="0" errors="0" skipped="0"/>')
    phases = [{"phase": phase, "outcome": "passed", "subtest": False,
               "xfail": False, "context": None}
              for phase in ("setup", "call", "teardown")]
    rows, probes = execution_rows(tool, phases)
    for role, folder in (("runtime", runtime), ("coverage", directory),
                         ("isolated", isolated)):
        if role != "runtime":
            parent = next(folder.glob(".coverage.*"))
            rows[role]["parent_shard"] = {"name": parent.name, "sha256": tool.digest(parent)}
        (folder / tool.SOURCE_SUITE).write_text(json.dumps(rows[role]))
        if role != "runtime":
            (folder / tool.CORE_PROBE).write_text(json.dumps(probes[role]))
    cross = {"passed": True, "reporting_python": [3, 12, 0], "python312": {"python": [3, 12, 0], "core": "CTracer"},
             "python314": {"python": [3, 14, 0], "core": "SysMonitor"}}
    (directory / tool.CROSS_VERSION).write_text(json.dumps(cross))
    return selected


def test_same_source_auxiliary_runs_combine_real_arcs_and_all_reports(tool, repository):
    directory = measured(tool, repository)
    auxiliary(tool, repository, directory)
    receipt = tool.assemble_measurements(repository, directory)
    assert receipt["test_counts"] == {
        "tests": 9, "failures": 0, "errors": 0, "skipped": 0}
    assert set(receipt["sources"]) == {
        "scripts/covered.py", "scripts/namespace/unreached.py"}
    assert (directory / "auxiliary/measurement.json").is_file()


@pytest.mark.parametrize("fault", ["source", "missing-report", "failed-test",
                                  "missing-shards", "linked-report"])
def test_auxiliary_evidence_cannot_omit_checks_or_mix_source(
        tool, repository, fault):
    directory = measured(tool, repository)
    selected = auxiliary(tool, repository, directory)
    if fault == "source":
        state = json.loads((selected / "measurement.json").read_text())
        state["revision"] = "0" * 40
        (selected / "measurement.json").write_text(json.dumps(state))
    elif fault == "missing-report":
        (selected / tool.AUXILIARY_REPORTS[0]).unlink()
    elif fault == "failed-test":
        (selected / tool.AUXILIARY_REPORTS[0]).write_text(
            '<testsuites><testsuite tests="1" failures="1">'
            '<testcase name="failed"><failure/></testcase></testsuite></testsuites>')
    elif fault == "missing-shards":
        for path in selected.glob(".coverage.*"):
            path.unlink()
    else:
        path = selected / tool.AUXILIARY_REPORTS[0]
        path.unlink()
        path.symlink_to(repository / "pytest-report.xml")
    with pytest.raises(tool.Refusal):
        tool.assemble_measurements(repository, directory)
    assert not list(directory.glob(".coverage.auxiliary.*"))



def test_nested_startup_keeps_same_named_sources_and_hits_distinct(
        tool, repository):
    roots = (repository, repository / "openWallet/code",
             repository / "openWallet/spec")
    for index, root in enumerate(roots):
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts/collision.py").write_text(
            "def choose(value):\n    if value:\n        return 1\n"
            "    return 2\nchoose(" + ("False" if index == 1 else "True") + ")\n")
    full_assembly(tool, repository)
    for root in reversed(roots[1:]):
        git(root, "add", "scripts/collision.py")
        git(root, "commit", "-qm", "synthetic distinct source")
    git(repository / "openWallet", "add", "code", "spec")
    git(repository / "openWallet", "commit", "-qm", "synthetic leg pins")
    git(repository, "add", "scripts/collision.py", "openWallet")
    git(repository, "commit", "-qm", "synthetic complete source")
    directory = tool.prepare(repository, ".coverage-reports")
    environment = dict(os.environ, COVERAGE_PROCESS_START=str(repository / ".coveragerc"),
                       COVERAGE_ROOT=str(repository),
                       COVERAGE_FILE=str(directory / ".coverage"))
    environment.pop("COVERAGE_PROCESS_CONFIG", None)
    for root in roots:
        subprocess.run([sys.executable, "scripts/collision.py"], cwd=root,
                       env=environment, check=True, timeout=30)
    (repository / "pytest-report.xml").write_text(
        '<testsuite tests="3" failures="0" errors="0" skipped="0"/>')
    tool.generate_report(repository, directory)
    files = json.loads((directory / "coverage.json").read_text())["files"]
    names = ("scripts/collision.py", "openWallet/code/scripts/collision.py",
             "openWallet/spec/scripts/collision.py")
    assert set(names) <= set(files)
    assert 3 in files[names[0]]["executed_lines"]
    assert 3 in files[names[1]]["missing_lines"]
    assert 4 in files[names[1]]["executed_lines"]
    assert 4 in files[names[2]]["missing_lines"]



@pytest.mark.parametrize("fault", [
    "core-fallback", "wrong-interpreter", "deselected", "skip", "xfail",
    "missing-phase", "repeated-phase", "different-identities", "missing-report",
    "failed-runtime", "changed-runtime-source",
])
def test_full_source_execution_cannot_be_weakened_or_mislabelled(
        tool, repository, fault):
    directory = measured(tool, repository)
    auxiliary(tool, repository, directory)
    runtime = directory / "runtime"
    path = directory / tool.SOURCE_SUITE
    row = json.loads(path.read_text())
    node = row["nodes"][0]
    if fault == "core-fallback":
        row["core"] = "SysMonitor"
    elif fault == "wrong-interpreter":
        row["python"] = [3, 14, 0]
    elif fault == "deselected":
        row["deselected"] = True
    elif fault == "skip":
        row["reports"][node][1]["outcome"] = "skipped"
    elif fault == "xfail":
        row["reports"][node][1]["xfail"] = True
    elif fault == "missing-phase":
        row["reports"][node].pop()
    elif fault == "repeated-phase":
        row["reports"][node].append(row["reports"][node][-1])
    elif fault == "different-identities":
        new = "synthetic::renamed"
        row["nodes"] = [new]
        row["reports"] = {new: row["reports"].pop(node)}
        row["nodeids_sha256"] = hashlib.sha256(json.dumps(
            [new], separators=(",", ":")).encode()).hexdigest()
    elif fault == "missing-report":
        row["reports"] = {}
    elif fault == "failed-runtime":
        accepted = json.loads((runtime / tool.SOURCE_SUITE).read_text())
        accepted["exitstatus"] = 1
        (runtime / tool.SOURCE_SUITE).write_text(json.dumps(accepted))
    else:
        state = json.loads((runtime / "measurement.json").read_text())
        state["revision"] = "0" * 40
        (runtime / "measurement.json").write_text(json.dumps(state))
    path.write_text(json.dumps(row))
    with pytest.raises(tool.Refusal):
        tool.assemble_measurements(repository, directory)
    assert not list(directory.glob(".coverage.auxiliary.*"))


def execution_rows(tool, phases):
    collection = sorted(["synthetic::test_fixture", tool.ISOLATED_CASE])
    fingerprint = lambda names: hashlib.sha256(
        json.dumps(names, separators=(",", ":")).encode()).hexdigest()
    rows, probes = {}, {}
    for role, version, core in (("runtime", [3, 12, 0], None),
                                 ("coverage", [3, 12, 0], "CTracer"),
                                 ("isolated", [3, 14, 0], "SysMonitor")):
        selected = (collection if role == "runtime" else
                    [tool.ISOLATED_CASE] if role == "isolated" else
                    ["synthetic::test_fixture"])
        rows[role] = {
            "role": role, "python": version, "core": core,
            "coverage_version": "7.16.2", "collection": collection,
            "collection_sha256": fingerprint(collection),
            "nodes": selected, "nodeids_sha256": fingerprint(selected),
            "reports": {node: phases for node in selected}, "exitstatus": 0,
            "deselected": sorted(set(collection) - set(selected)),
        }
        probes[role] = {kind: {"python": version, "core": core,
                               "coverage_version": "7.16.2"}
                        for kind in ("parent", "child")}
    return json.loads(json.dumps(rows)), probes


@pytest.mark.parametrize("fault", [
    "missing", "changed", "linked", "invalid-database", "empty-branch-database", "missing-metadata",
])
def test_primary_parent_shard_must_survive_with_secondary_data(tool, repository, fault):
    directory = measured(tool, repository)
    auxiliary(tool, repository, directory)
    assert list((directory / "auxiliary").glob(".coverage.*"))
    assert list((directory / "isolated").glob(".coverage.*"))
    row = json.loads((directory / tool.SOURCE_SUITE).read_text())
    parent = directory / row["parent_shard"]["name"]
    if fault == "missing":
        for shard in directory.glob(".coverage.*"):
            shard.unlink()
    elif fault == "changed":
        parent.write_bytes(parent.read_bytes() + b"changed")
    elif fault == "invalid-database":
        parent.write_bytes(b"not real branch data")
        row["parent_shard"]["sha256"] = tool.digest(parent)
        (directory / tool.SOURCE_SUITE).write_text(json.dumps(row))
    elif fault == "empty-branch-database":
        parent.unlink()
        data = coverage.CoverageData(basename=str(parent))
        data.add_arcs({})
        data.touch_file(str(repository / "scripts/covered.py"))
        data.write()
        assert data.has_arcs() and data.measured_files() and not data.arcs(
            str(repository / "scripts/covered.py"))
        row["parent_shard"]["sha256"] = tool.digest(parent)
        (directory / tool.SOURCE_SUITE).write_text(json.dumps(row))
    elif fault == "missing-metadata":
        row.pop("parent_shard")
        (directory / tool.SOURCE_SUITE).write_text(json.dumps(row))
    else:
        saved = parent.with_name("retained-parent")
        parent.rename(saved)
        parent.symlink_to(saved)
    with pytest.raises(tool.Refusal, match="parent measurement shard"):
        tool.assemble_measurements(repository, directory)
    assert not list(directory.glob(".coverage.auxiliary.*"))


@pytest.mark.parametrize("mismatch", ["missing", "parameters", "message"])
def test_passing_subtests_are_preserved_and_must_match_both_measurements(tool, mismatch):
    phases = [{"phase": phase, "outcome": "passed", "subtest": False,
               "xfail": False, "context": None}
              for phase in ("setup", "call", "teardown")]
    phases.insert(1, {"phase": "call", "outcome": "passed", "subtest": True,
                      "xfail": False, "context": {
                          "message": None, "parameters": {"value": "0"}}})
    rows, probes = execution_rows(tool, phases)
    def compare():
        return tool.compare_source_executions(
            rows["runtime"], rows["coverage"], probes["coverage"],
            rows["isolated"], probes["isolated"])
    assert compare()["runtime"]["tests"] == 2
    selected = rows["coverage"]["reports"]["synthetic::test_fixture"]
    if mismatch == "missing":
        selected.pop(1)
    elif mismatch == "parameters":
        selected[1]["context"]["parameters"]["value"] = "1"
    else:
        selected[1]["context"]["message"] = "different case"
    with pytest.raises(tool.Refusal, match="identical"):
        compare()


@pytest.mark.parametrize("fault", [
    "missing-isolated", "overlap", "isolated-core", "isolated-version",
    "collection-drift", "unexpected-deselection", "missing-isolated-assertion",
])
def test_fixed_partition_cannot_omit_overlap_or_relabel_cases(tool, fault):
    phases = [{"phase": phase, "outcome": "passed", "subtest": False,
               "xfail": False, "context": None}
              for phase in ("setup", "call", "teardown")]
    rows, probes = execution_rows(tool, phases)
    isolated = rows["isolated"]
    if fault == "missing-isolated":
        isolated["nodes"] = []
    elif fault == "overlap":
        isolated["nodes"] = rows["runtime"]["nodes"]
    elif fault == "isolated-core":
        isolated["core"] = "CTracer"
    elif fault == "isolated-version":
        isolated["python"] = [3, 12, 0]
    elif fault == "collection-drift":
        isolated["collection"] = [tool.ISOLATED_CASE]
    elif fault == "unexpected-deselection":
        isolated["deselected"] = []
    else:
        isolated["reports"] = {}
    with pytest.raises(tool.Refusal):
        tool.compare_source_executions(
            rows["runtime"], rows["coverage"], probes["coverage"],
            isolated, probes["isolated"])


def test_real_partition_receipt_preserves_subtests_and_ignores_nested_subset(tool, tmp_path):
    roles = ("runtime", "coverage") if sys.version_info[:2] == (3, 12) else ("isolated",)
    for role in roles:
        import shutil
        root = tmp_path / role
        (root / "tests/runtime_binding").mkdir(parents=True)
        (root / ".coverage-reports").mkdir(mode=0o700)
        shutil.copyfile(ROOT / "tests/conftest.py", root / "tests/conftest.py")
        (root / "tests/probe_child.py").write_text("def test_child():\n    assert True\n")
        (root / "tests/test_sample.py").write_text("def test_sample():\n    assert True\n")
        (root / "tests/runtime_binding/test_hosted_lifecycle.py").write_text(
            "import subprocess,sys,pytest\n"
            "@pytest.mark.parametrize('size',['large-manifest'])\n"
            "def test_large_final_manifest_cleans_and_audits_above_aggregate_document_limit(size,subtests):\n"
            "    for value in (1,2):\n"
            "        with subtests.test(value=value):\n"
            "            assert value>0\n"
            "    subprocess.run([sys.executable,'-m','pytest','tests/probe_child.py','-q'],"
            "check=True,timeout=30)\n")
        environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        for key in ("COVERAGE_PROCESS_START", "COVERAGE_PROCESS_CONFIG", "COVERAGE_ROOT",
                    "COVERAGE_FILE", "COVERAGE_CORE", "PYTEST_CURRENT_TEST"):
            environment.pop(key, None)
        environment["WALLET_SOURCE_MEASUREMENT"] = role
        if role != "runtime":
            config = root / "coverage.ini"
            config.write_text("[run]\nbranch=True\nparallel=True\nrelative_files=False\n")
            environment.update(COVERAGE_PROCESS_START=str(config),
                               COVERAGE_CORE="sysmon" if role == "isolated" else "ctrace",
                               COVERAGE_FILE=str(root / ".coverage-reports/.coverage"))
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q",
             "--rootdir=" + str(root), "--confcutdir=" + str(root)],
            cwd=root, env=environment, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stdout + result.stderr
        row = json.loads((root / ".coverage-reports/source-suite.json").read_text())
        assert len(row["collection"]) == 2
        if role != "runtime":
            tool.require_parent_shard(root / ".coverage-reports", row)
        count = 2 if role == "runtime" else 1
        assert tool.validate_source_execution(row, role)["tests"] == count
        contexts = [report["context"] for phases in row["reports"].values()
                    for report in phases if report["subtest"]]
        expected_contexts = [{"message": None, "parameters": {"value": str(value)}}
                             for value in (1, 2)]
        assert contexts == ([] if role == "coverage" else expected_contexts)
        assert row["deselected"] == (
            [] if role == "runtime" else [tool.ISOLATED_CASE] if role == "coverage"
            else ["tests/test_sample.py::test_sample"])



def test_analysis_wheel_closure_preserves_every_runtime_package_version():
    import re

    def versions(name):
        return {package.lower().replace("_", "-"): version
                for package, version in re.findall(
                    r"^([A-Za-z0-9_.-]+)==([^\s\\]+)",
                    (ROOT / name).read_text(), re.M)}
    runtime = versions("requirements-workload-binding.lock")
    analysis = versions("requirements/coverage-workload.lock")
    assert len(runtime) == 18
    assert analysis == runtime



@pytest.mark.parametrize("fault", ["none", "wrong-runtime", "missing-file", "missing-line"])
def test_secondary_auditor_uses_the_real_target_compiler_contract(
        tool, repository, monkeypatch, fault):
    from types import SimpleNamespace

    names = list(tool.inventory(repository))
    expected = tool.executable_inventory(repository, names, require_target=False)
    result = {"python": [3, 12, 3], "coverage_version": "7.16.2",
              "files": {name: sorted(lines) for name, lines in expected.items()}}
    if fault == "wrong-runtime":
        result["python"] = [3, 14, 7]
    elif fault == "missing-file":
        result["files"].pop(names[0])
    elif fault == "missing-line":
        result["files"][names[0]].pop()
    monkeypatch.setattr(tool, "sys", SimpleNamespace(version_info=(3, 14, 7)))
    monkeypatch.setenv("WALLET_TARGET_PYTHON", "/operator-selected/python312")
    calls = []

    def compiler(argv, **kwargs):
        calls.append((argv, json.loads(kwargs["input"])))
        return json.dumps(result)

    monkeypatch.setattr(tool, "subprocess", SimpleNamespace(check_output=compiler))
    if fault == "none":
        assert tool.executable_inventory(
            repository, names, require_target=True) == expected
        assert calls[0][0][:2] == ["/operator-selected/python312", "-c"]
        assert calls[0][1] == {"root": str(repository), "names": names}
    else:
        with pytest.raises(tool.Refusal):
            tool.executable_inventory(repository, names, require_target=True)


def test_production_denominator_cannot_be_reported_under_the_analysis_version(
        tool, repository):
    directory = measured(tool, repository)
    auxiliary(tool, repository, directory)
    tool.assemble_measurements(repository, directory)
    path = directory / "receipt.json"
    row = json.loads(path.read_text())
    row["reporting_python"] = [3, 14, 7]
    path.write_text(json.dumps(row))
    with pytest.raises(tool.Refusal, match="denominator"):
        tool.check_report(repository, directory, require_execution=True)
