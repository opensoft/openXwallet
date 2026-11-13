"""Mutation tests for the gate itself; no provider or external network use."""
from types import SimpleNamespace
import os
from pathlib import Path
import subprocess
import sys

import pytest

from .conformance import ConformancePlugin, MatrixAudit, node_digest, selected_owner
from .isolation import ENVIRONMENT, bootstrap, private_root, validate_boundary

NODES = ("module.py::test_required[a]", "module.py::test_required[b]")


def audit(nodes=NODES):
    result = MatrixAudit({"module.py": 2}, {"I01": ("module.py::test_required",)})
    result.collected(nodes)
    return result


def finish(result):
    for node in result.nodes:
        for phase in ("setup", "call", "teardown"):
            result.report(node, phase, "passed")
    return result.complete()


def test_complete_parametrized_matrix_passes():
    result = audit()
    assert finish(result)
    assert result.case_counts == {"I01": 2}


@pytest.mark.parametrize("nodes", [(), NODES[:1], NODES + ("module.py::test_other",),
                                  (NODES[0], NODES[0]), ("other.py::test_required[a]", "other.py::test_required[b]")])
def test_missing_empty_extra_duplicate_or_wrong_module_cannot_pass(nodes):
    assert not finish(audit(nodes))


def test_renamed_anchor_cannot_hide_behind_same_count():
    assert not finish(audit(("module.py::test_other[a]", "module.py::test_other[b]")))


def test_compensated_parameter_loss_cannot_preserve_collection():
    contract = {"module.py": node_digest(NODES)}
    result = MatrixAudit({"module.py": 2}, {"I04": ("module.py::test_required",)}, digests=contract)
    result.collected(reversed(NODES))
    assert finish(result)  # collection order is immaterial
    result = MatrixAudit({"module.py": 2}, {"I04": ("module.py::test_required",)}, digests=contract)
    result.collected((NODES[0], "module.py::test_unrelated"))
    assert not finish(result)
    assert "collection-identity-drift" in result.violations


@pytest.mark.parametrize("phase", ["setup", "call", "teardown"])
@pytest.mark.parametrize("outcome", ["failed", "skipped"])
def test_any_phase_failure_or_skip_fails_conformance(phase, outcome):
    result = audit()
    for node in result.nodes:
        for current in ("setup", "call", "teardown"):
            result.report(node, current, outcome if current == phase else "passed")
    assert not result.complete()


def test_expected_failure_and_unexpected_pass_do_not_qualify():
    result = audit()
    result.report(NODES[0], "call", "passed", xfail=True)
    assert "non-passing-case" in result.violations


@pytest.mark.parametrize("missing", ["setup", "call", "teardown"])
def test_missing_report_never_qualifies(missing):
    result = audit()
    for node in result.nodes:
        for phase in ("setup", "call", "teardown"):
            if phase != missing:
                result.report(node, phase, "passed")
    assert not result.complete()


def test_duplicate_and_unknown_reports_fail():
    result = audit()
    result.report(NODES[0], "call", "passed")
    result.report(NODES[0], "call", "passed")
    result.report("uncollected", "call", "passed")
    assert "duplicate-report" in result.violations
    assert "unexpected-report" in result.violations


def test_empty_case_contract_fails():
    result = MatrixAudit({"module.py": 2}, {"I01": ()})
    result.collected(NODES)
    assert not finish(result)


def test_deselection_remains_a_failure_after_valid_collection():
    plugin = ConformancePlugin()
    plugin.audit = audit()
    plugin.pytest_deselected([SimpleNamespace(nodeid=NODES[0])])
    assert not finish(plugin.audit)


def test_nonzero_pytest_exit_cannot_print_success():
    plugin = ConformancePlugin()
    plugin.audit = audit()
    assert finish(plugin.audit)
    session = SimpleNamespace(exitstatus=0)
    plugin.pytest_sessionfinish(session, 2)
    assert session.exitstatus != 0
    assert "pytest-error" in plugin.audit.violations


def test_collection_drift_aborts_before_tests_execute():
    plugin = ConformancePlugin()
    plugin.audit = MatrixAudit({"module.py": 2}, {"I01": ("module.py::test_required",)})
    session = SimpleNamespace(items=[SimpleNamespace(nodeid=NODES[0])])
    with pytest.raises(pytest.exit.Exception):
        plugin.pytest_collection_finish(session)


def boundary(**changes):
    values = dict(names=["lo"], status={"NoNewPrivs": "1", "CapEff": "0", "CapPrm": "0", "CapAmb": "0", "CapBnd": "0"},
                  uid=1000, groups=[], environment={key: "fixture" for key in ENVIRONMENT})
    values.update(changes)
    return values


def test_unprivileged_loopback_boundary_passes():
    validate_boundary(**boundary())


@pytest.mark.parametrize("changes", [{"names": ["lo", "eth0"]}, {"names": []}, {"uid": 0}, {"groups": [1001]},
                                     {"environment": {"GITHUB_TOKEN": "synthetic-canary"}},
                                     {"environment": {"PYTEST_ADDOPTS": "-k nothing"}}])
def test_external_network_root_groups_or_ambient_options_refuse(changes):
    arguments = boundary(**changes)
    with pytest.raises(RuntimeError, match="^offline-boundary-invalid$"):
        validate_boundary(**arguments)


@pytest.mark.parametrize("field", ["CapEff", "CapPrm", "CapAmb", "CapBnd", "NoNewPrivs"])
def test_each_native_privilege_control_is_required(field):
    arguments = boundary()
    arguments["status"][field] = "0" if field == "NoNewPrivs" else "1"
    with pytest.raises(RuntimeError, match="^offline-boundary-invalid$"):
        validate_boundary(**arguments)


@pytest.mark.parametrize("kind", ["public", "symlink", "wrong-owner"])
def test_temp_root_must_be_private_owned_and_not_a_symlink(tmp_path, kind):
    root = tmp_path / "matrix"
    root.mkdir(mode=0o700)
    selected, uid = root, os.geteuid()
    if kind == "public":root.chmod(0o755)
    elif kind == "symlink":
        selected = tmp_path / "alias"
        selected.symlink_to(root)
    else:uid += 1
    with pytest.raises(RuntimeError, match="^offline-temp-root-invalid$"):
        private_root(selected, uid)


def test_bootstrap_refuses_non_root_before_touching_resources(tmp_path):
    assert os.geteuid() != 0
    with pytest.raises(RuntimeError, match="^offline-bootstrap-invalid$"):
        bootstrap(os.geteuid(), "unused", tmp_path / "absent", "unused")
    assert not (tmp_path / "absent").exists()


def test_owner_selection_must_be_explicit_and_match_environment(tmp_path, monkeypatch):
    root = tmp_path / "owner"
    root.mkdir()
    monkeypatch.setenv("WALLET_BINDING_OWNER_CODE", str(root))
    with pytest.raises(RuntimeError, match="^owning-source-selection-invalid$"):
        selected_owner(None)


@pytest.mark.parametrize("mutation", ["none", "skip", "setup-skip", "teardown-skip", "xfail", "xpass",
                                      "deselect", "empty", "renamed", "parameter-loss", "failure", "parameter-substitution"])
def test_real_pytest_reports_cannot_hide_nonconformance(tmp_path, mutation):
    source = "import pytest\n\ndef test_one():\n    assert True\n"
    if mutation == "skip":
        source = source.replace("assert True", "pytest.skip('fixture')")
    elif mutation in {"setup-skip", "teardown-skip"}:
        body = "pytest.skip('fixture')\n    yield" if mutation == "setup-skip" else "yield\n    pytest.skip('fixture')"
        source += "\n@pytest.fixture(autouse=True)\ndef fixture():\n    " + body + "\n"
    elif mutation in {"xfail", "xpass"}:
        source = source.replace("def test_one", "@pytest.mark.xfail(strict=False)\ndef test_one")
        if mutation == "xfail":
            source = source.replace("assert True", "assert False")
    elif mutation == "empty":
        source = ""
    elif mutation == "renamed":
        source = source.replace("test_one", "test_other")
    elif mutation == "failure":
        source = source.replace("assert True", "assert False")
    elif mutation == "parameter-substitution":
        source = ("import pytest\n@pytest.mark.parametrize('value', ['a'])\n"
                  "def test_one(value):\n    pass\n\ndef test_unrelated():\n    pass\n")
    (tmp_path / "test_sample.py").write_text(source)
    root = Path(__file__).resolve().parents[2]
    # Only this harness overrides the audit contract, in a tiny synthetic corpus.
    # The production CLI has no selection or contract override.
    expected_count = 2 if mutation in {"parameter-loss", "parameter-substitution"} else 1
    digests = {"test_sample.py": node_digest(["test_sample.py::test_one[a]", "test_sample.py::test_one[b]"])} if mutation == "parameter-substitution" else None
    program = "\n".join([
        "import os, sys, pytest",
        "sys.path.insert(0, " + repr(str(root / "tests")) + ")",
        "from runtime_binding.conformance import ConformancePlugin, MatrixAudit",
        "plugin = ConformancePlugin()",
        "plugin.audit = MatrixAudit({'test_sample.py': " + str(expected_count)
        + "}, {'I01': ('test_sample.py::test_one',)}, digests=" + repr(digests) + ")",
        "raise SystemExit(pytest.main(" + repr([str(tmp_path / "test_sample.py"), "-q", "-c", os.devnull,
                                               "--rootdir=" + str(tmp_path), "-p", "no:cacheprovider"]
                                              + (["-k", "absent"] if mutation == "deselect" else []))
        + ", plugins=[plugin]))",
    ])
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    result = subprocess.run([sys.executable, "-I", "-B", "-c", program], cwd=tmp_path,
                            env=environment, text=True, capture_output=True, timeout=20)
    assert (result.returncode == 0) == (mutation == "none"), result.stdout + result.stderr
    if mutation == "none":
        assert "runtime-conformance: PASS" in result.stdout
    else:
        assert "runtime-conformance: PASS" not in result.stdout
