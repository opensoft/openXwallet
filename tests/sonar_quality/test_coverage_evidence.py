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
    cov.set_option("run:relative_files", True)
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
