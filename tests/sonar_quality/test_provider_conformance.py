"""Refuse forged providers, changed copies and incomplete conformance runs."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def tool():
    spec = importlib.util.spec_from_file_location(
        "wallet_provider_conformance", ROOT / "scripts/run-provider-conformance.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_forged_provenance_cannot_hide_executable_lines(tool, tmp_path):
    revision = "a" * 40
    path = tmp_path / "copy.py"
    header = (
        f"# VENDORED from opensoft/openXfactory@{revision}; do not edit here.\n"
        "# Everything below this header block is byte-identical to the provider.\n"
        "# Current provenance and hashes: docs/openspec-cli-pin.md.\n")
    body = b"#!/usr/bin/env python3\nprint('synthetic')\n"
    path.write_bytes(body.split(b"\n", 1)[0] + b"\n" + header.encode()
                     + body.split(b"\n", 1)[1])
    assert tool.provider_body(path, revision) == body
    path.write_bytes(path.read_bytes().replace(
        b"# Everything below this header block is byte-identical to the provider.",
        b"raise RuntimeError('hidden execution')"))
    with pytest.raises(ValueError, match="header"):
        tool.provider_body(path, revision)


@pytest.mark.parametrize("fault", ["pending", "dirty", "wrong-head",
                                  "wrong-hash", "wrong-identity", "linked", "unadmitted"])
def test_provider_admission_is_bound_to_clean_immutable_bytes(
        tool, tmp_path, monkeypatch, fault):
    provider = tmp_path / "provider"
    provider.mkdir()
    path = provider / "assertions.py"
    path.write_text("def test_synthetic():\n    assert True\n")
    def git(*args):
        return subprocess.check_output(["git", "-C", str(provider), *args],
                                       text=True).strip()
    git("init", "-q")
    git("-c", "user.name=Synthetic", "-c", "user.email=test@example.invalid",
        "add", "assertions.py")
    git("-c", "user.name=Synthetic", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "synthetic provider")
    revision = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/main", revision)
    record = {"repository": "test/provider", "test_paths": ["assertions.py"],
              "files": {"assertions.py": hashlib.sha256(path.read_bytes()).hexdigest()},
              "commit": revision, "admitted_main": revision,
              "main_admission": "verified"}
    monkeypatch.setitem(tool.PROVIDERS, "openspec", {
        "repository": "test/provider", "environment": "TEST_WALLET_PROVIDER",
        "tests": ["assertions.py"], "assets": ["assertions.py"]})
    monkeypatch.setenv("TEST_WALLET_PROVIDER", str(provider))
    root = tmp_path / "consumer"
    (root / "requirements").mkdir(parents=True)
    monkeypatch.setattr(tool, "ROOT", root)
    metadata = root / "requirements/analysis-providers.json"
    metadata.write_text(json.dumps({"openspec": record}))
    assert tool.provider_checkout("openspec") == (provider, record)
    if fault == "pending":
        record["main_admission"] = "pending"
    elif fault == "dirty":
        path.write_text("raise RuntimeError('changed')\n")
    elif fault == "wrong-head":
        record["commit"] = "0" * 40
    elif fault == "wrong-hash":
        record["files"]["assertions.py"] = "0" * 64
    elif fault == "wrong-identity":
        record["repository"] = "unapproved/provider"
    elif fault == "unadmitted":
        git("-c", "user.name=Synthetic", "-c", "user.email=test@example.invalid",
            "commit", "--allow-empty", "-qm", "unadmitted candidate")
        record["commit"] = record["admitted_main"] = git("rev-parse", "HEAD")
    else:
        outside = tmp_path / "outside.py"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
    metadata.write_text(json.dumps({"openspec": record}))
    with pytest.raises(ValueError):
        tool.provider_checkout("openspec")


@pytest.mark.parametrize("fault", ["none", "xfail", "missing-teardown",
                                  "skip", "duplicate-report", "deselection"])
def test_only_complete_passing_provider_assertions_are_accepted(tool, tmp_path, fault):
    path = tmp_path / "assertions.py"
    module = SimpleNamespace(__file__=str(path))
    # A module object is hashable, as real pytest modules are.
    import types
    module = types.ModuleType("assertions")
    module.__file__ = str(path)
    node = "assertions.py::test_synthetic"
    record = {"expected_test_count": 1, "allowed_skips": [],
              "nodeids_sha256": hashlib.sha256(
                  json.dumps([node], separators=(",", ":")).encode()).hexdigest()}
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setitem(tool.PROVIDERS, "openspec", {"tests": ["assertions.py"]})
    try:
        plugin = tool.CollectionBindings(tmp_path, tmp_path, "openspec", record)
        plugin.pytest_collection_modifyitems(None, None, [
            SimpleNamespace(module=module, nodeid=node)])
        if fault == "deselection":
            with pytest.raises(ValueError, match="deselect"):
                plugin.pytest_deselected([object()])
            return
        for phase in ("setup", "call", "teardown"):
            if fault == "missing-teardown" and phase == "teardown":
                continue
            report = SimpleNamespace(nodeid=node, when=phase,
                                     outcome="skipped" if fault == "skip" else "passed")
            if fault == "xfail":
                report.wasxfail = "unexpectedly waived"
            plugin.pytest_runtest_logreport(report)
            if fault == "duplicate-report":
                plugin.pytest_runtest_logreport(report)
        session = SimpleNamespace(exitstatus=0)
        plugin.pytest_sessionfinish(session, 0)
        assert session.exitstatus == (0 if fault == "none" else 1)
    finally:
        monkeypatch.undo()


def test_shape_redirects_identical_cli_only_and_retains_original_fixture_root(tool, tmp_path):
    provider = tmp_path / "provider"
    target = tmp_path / "target"
    fixture = tmp_path / "fixture"
    for root in (provider, target, fixture):
        (root / "scripts").mkdir(parents=True)
    body = b"print('synthetic CLI')\n"
    source = provider / "scripts/validate-manifest.py"
    source.write_bytes(body)
    copied = fixture / "scripts/validate-manifest.py"
    copied.write_bytes(body)
    tool.PROVIDERS["shape"]["copies"] = {
        "scripts/validate-manifest.py": "scripts/validate-manifest.py"}
    plugin = tool.ShapeBindings(provider, target, {})
    calls = []
    plugin.original_run = lambda *args, **kwargs: calls.append((args, kwargs))
    plugin.run_script(copied, "--strict", cwd=fixture)
    assert calls[-1][0] == (
        target / "scripts/validate-manifest.py", "--root", str(fixture), "--strict")
    copied.write_bytes(b"print('intentionally altered fixture')\n")
    plugin.run_script(copied, cwd=fixture)
    assert calls[-1][0] == (copied,)
    assert plugin.redirected["validate-manifest.py"] == 1
