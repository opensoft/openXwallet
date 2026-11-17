#!/usr/bin/env python3
"""Run immutable provider assertions against actual scanned consumer source.

OpenSpec retains its provider data/evidence root and binds verifier/installer/pin
to the consumer. Shape imports the actual shared reader and redirects unchanged
copied CLI bytes to the consumer, with the original fixture root explicit.
All selected assertions run; coverage filenames and hits are never rewritten.
"""
from __future__ import annotations

import argparse
from functools import partial
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NEUTRAL_SPEC_ROOT = "openWallet/spec"
VERIFIER = 'scripts/validate-openspec-cli-pin.py'
INSTALLER = 'scripts/install-pinned-openspec-cli.py'
CLI_PIN = 'contracts/openspec-cli-pin.yaml'
CLI_LOCK = 'contracts/openspec-cli-pin.1.12.0.package-lock.json'
SHAPE_READER = 'scripts/repo_shape.py'
NAMING_CLI = 'scripts/validate-repository-naming.py'
MODES = {"openspec-adapter": ("openspec", ""),
         "openspec-spec": ("openspec", NEUTRAL_SPEC_ROOT),
         "shape": ("shape", "openWallet")}
PROVIDERS = {
    "openspec": {
        "repository": "opensoft/openXfactory",
        "environment": "WALLET_ANALYSIS_PROVIDER_ROOT",
        "tests": [
            "tests/openspec_cli_pin/test_openspec_cli_pin.py"
        ],
        "copies": {
            VERIFIER: VERIFIER,
            INSTALLER: INSTALLER,
            CLI_PIN: CLI_PIN,
            CLI_LOCK: CLI_LOCK
        },
        "assets": [
            "tests/openspec_cli_pin/test_openspec_cli_pin.py",
            "tests/openspec_cli_pin/fixtures/openspec-1.12.0-validate-changes-strict-report-findings.json",
            "tests/openspec_cli_pin/fixtures/openspec-1.12.0-validate-one-change-strict.json",
            VERIFIER,
            INSTALLER,
            CLI_PIN,
            CLI_LOCK
        ]
    },
    "shape": {
        "repository": "opensoft/openRepoShape",
        "environment": "WALLET_ANALYSIS_SHAPE_ROOT",
        "tests": [
            "tests/test_bootstrap_after_bump.py",
            "tests/test_bootstrap_branch_bytes.py",
            "tests/test_bootstrap_casefold_twin.py",
            "tests/test_bootstrap_create_twins.py",
            "tests/test_bootstrap_leg_moves.py",
            "tests/test_bootstrap_non_utf8_branch.py",
            "tests/test_bootstrap_pasteable_lines.py",
            "tests/test_bootstrap_placement_texts.py",
            "tests/test_bootstrap_ref_store.py",
            "tests/test_bootstrap_refusal_exit.py",
            "tests/test_bootstrap_spelling.py",
            "tests/test_bootstrap_upstream_notice.py",
            "tests/test_bootstrap_without_git.py",
            "tests/test_cli_yaml_boundaries.py",
            "tests/test_load_yaml_refusals.py",
            "tests/test_manifest_validator.py",
            "tests/test_naming_policy.py",
            "tests/test_pin_validator.py",
            "tests/test_yaml_block_scalar_keys.py",
            "tests/test_yaml_flow_brackets.py",
            "tests/test_yaml_flow_mappings.py",
            "tests/test_yaml_flow_quotes.py",
            "tests/test_yaml_indicator_openers.py",
            "tests/test_yaml_quote_boundaries.py",
            "tests/test_yaml_reader_spaces.py"
        ],
        "copies": {
            SHAPE_READER: SHAPE_READER,
            NAMING_CLI: NAMING_CLI,
            "scripts/validate-manifest.py": "templates/assembly-root/scripts/validate-manifest.py",
            "scripts/validate-pins.py": "templates/assembly-root/scripts/validate-pins.py",
            "scripts/bootstrap.py": "templates/assembly-root/scripts/bootstrap.py"
        },
        "assets": [
            SHAPE_READER,
            NAMING_CLI,
            "templates/assembly-root/scripts/bootstrap.py",
            "templates/assembly-root/scripts/validate-manifest.py",
            "templates/assembly-root/scripts/validate-pins.py",
            "tests/conftest.py",
            "tests/test_bootstrap_after_bump.py",
            "tests/test_bootstrap_branch_bytes.py",
            "tests/test_bootstrap_casefold_twin.py",
            "tests/test_bootstrap_create_twins.py",
            "tests/test_bootstrap_leg_moves.py",
            "tests/test_bootstrap_non_utf8_branch.py",
            "tests/test_bootstrap_pasteable_lines.py",
            "tests/test_bootstrap_placement_texts.py",
            "tests/test_bootstrap_ref_store.py",
            "tests/test_bootstrap_refusal_exit.py",
            "tests/test_bootstrap_spelling.py",
            "tests/test_bootstrap_upstream_notice.py",
            "tests/test_bootstrap_without_git.py",
            "tests/test_cli_yaml_boundaries.py",
            "tests/test_load_yaml_refusals.py",
            "tests/test_manifest_validator.py",
            "tests/test_naming_policy.py",
            "tests/test_pin_validator.py",
            "tests/test_yaml_block_scalar_keys.py",
            "tests/test_yaml_flow_brackets.py",
            "tests/test_yaml_flow_mappings.py",
            "tests/test_yaml_flow_quotes.py",
            "tests/test_yaml_indicator_openers.py",
            "tests/test_yaml_quote_boundaries.py",
            "tests/test_yaml_reader_spaces.py"
        ]
    }
}


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True).strip()


def provider_checkout(role):
    rules = PROVIDERS[role]
    selected = os.environ.get(rules["environment"])
    if not selected:
        raise ValueError("operator-selected analysis provider missing")
    provider = Path(selected).resolve(strict=True)
    record = json.loads(
        (ROOT / "requirements/analysis-providers.json").read_text())[role]
    if (record["repository"] != rules["repository"]
            or record["test_paths"] != rules["tests"]
            or set(record["files"]) != set(rules["assets"])):
        raise ValueError("provider identity or asset selection differs")
    if (record["main_admission"] != "verified"
            or not re.fullmatch(r"[0-9a-f]{40}", record["commit"])
            or not re.fullmatch(r"[0-9a-f]{40}", record.get("admitted_main", ""))):
        raise ValueError("provider main admission is not verified")
    if git(provider, "rev-parse", "--show-toplevel") != str(provider):
        raise ValueError("unexpected provider repository")
    if git(provider, "rev-parse", "HEAD") != record["commit"]:
        raise ValueError("provider revision differs")
    if git(provider, "diff", "--name-only", "HEAD"):
        raise ValueError("provider source changed")
    try:
        git(provider, "merge-base", "--is-ancestor",
            record["admitted_main"], "refs/remotes/origin/main")
    except subprocess.CalledProcessError as exc:
        raise ValueError("provider admission is not on fetched main") from exc
    git(provider, "merge-base", "--is-ancestor",
        record["commit"], record["admitted_main"])
    git(provider, "diff", "--exit-code", record["commit"],
        record["admitted_main"], "--", *rules["assets"])
    for name, expected in record["files"].items():
        path = provider / name
        if path.is_symlink() or path.resolve() != path or not path.is_file():
            raise ValueError("non-regular provider source")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("provider source differs")
    return provider, record


def provider_body(path, revision):
    data = path.read_bytes()
    if path.suffix not in (".py", ".yaml"):
        return data
    header = (
        f"# VENDORED from opensoft/openXfactory@{revision}; do not edit here.\n"
        "# Everything below this header block is byte-identical to the provider.\n"
        "# Current provenance and hashes: docs/openspec-cli-pin.md.\n"
    ).encode()
    if path.suffix == ".py":
        first, rest = data.split(b"\n", 1)
        if not first.startswith(b"#!") or not rest.startswith(header):
            raise ValueError("consumer header differs")
        return first + b"\n" + rest[len(header):]
    if not data.startswith(header):
        raise ValueError("consumer header differs")
    return data[len(header):]


def verify_copies(provider, target, role, revision):
    copies = PROVIDERS[role]["copies"]
    # There is one executable implementation: the pinned neutral spec leg.
    # Adapter configuration remains independently authenticated in its own root.
    for local, remote in copies.items():
        source_root = (ROOT / NEUTRAL_SPEC_ROOT
                       if role == "openspec" and local in (VERIFIER, INSTALLER)
                       else target)
        path = source_root / local
        if path.is_symlink() or path.resolve() != path or not path.is_file():
            raise ValueError("linked or missing consumer source")
        body = provider_body(path, revision) if role == "openspec" else path.read_bytes()
        if body != (provider / remote).read_bytes():
            raise ValueError("consumer differs from admitted provider")


class CollectionBindings:
    def __init__(self, provider, target, role, record):
        self.provider, self.target, self.role, self.record = provider, target, role, record
        self.nodes, self.phases, self.problems = set(), {}, []

    def pytest_collection_modifyitems(self, items):
        expected = {self.provider / name for name in PROVIDERS[self.role]["tests"]}
        modules = {item.module for item in items}
        actual = {Path(module.__file__).resolve() for module in modules}
        nodes = [item.nodeid for item in items]
        fingerprint = hashlib.sha256(
            json.dumps(sorted(nodes), separators=(",", ":")).encode()).hexdigest()
        if (not items or actual != expected or len(nodes) != len(set(nodes))
                or len(nodes) != self.record["expected_test_count"]
                or fingerprint != self.record["nodeids_sha256"]):
            raise ValueError("provider conformance collection differs")
        self.nodes = set(nodes)
        if self.role == "openspec":
            for module in modules:
                shared = ROOT / NEUTRAL_SPEC_ROOT
                module.SCRIPT = shared / VERIFIER
                module.INSTALLER = shared / INSTALLER
                module.PIN = self.target / CLI_PIN
                original = module._load
                context = self.target

                def load(name, path, original=original, context=context):
                    loaded = original(name, path)
                    loaded.main = partial(loaded.main, consumer_root=context)
                    return loaded

                module._load = load

    def pytest_deselected(self, items):
        if items:
            raise ValueError("provider conformance cannot deselect assertions")

    def pytest_runtest_logreport(self, report):
        phases = self.phases.setdefault(report.nodeid, {})
        if report.nodeid not in self.nodes or report.when in phases:
            self.problems.append("unexpected or repeated report")
        phases[report.when] = report.outcome
        if hasattr(report, "wasxfail"):
            self.problems.append("expected-failure reporting is not acceptance")

    def pytest_sessionfinish(self, session):
        permitted = set(self.record["allowed_skips"])
        passed = {"setup": "passed", "call": "passed", "teardown": "passed"}
        skipped = {"setup": "skipped", "teardown": "passed"}
        for node in self.nodes:
            phases = self.phases.get(node, {})
            if phases != passed and not (node in permitted and phases == skipped):
                self.problems.append("non-passing or incomplete assertion: " + node)
        if self.problems or not self.nodes:
            session.exitstatus = 1

    def pytest_terminal_summary(self, terminalreporter):
        for problem in self.problems:
            terminalreporter.write_line("provider-conformance: " + problem)
        terminalreporter.write_line(
            f"provider-conformance {self.role}: {len(self.nodes)} exact assertions; "
            + ("FAIL" if self.problems or not self.nodes else "PASS"))


class ShapeBindings(CollectionBindings):
    def __init__(self, provider, target, record):
        super().__init__(provider, target, "shape", record)
        self.redirected = Counter()
        self.conftest = self.original_run = None
        self.bodies = {Path(local).name: (provider / remote).read_bytes()
                       for local, remote in PROVIDERS["shape"]["copies"].items()
                       if Path(local).name != "repo_shape.py"}

    def pytest_configure(self):
        module = sys.modules.get("conftest")
        expected = self.provider / "tests/conftest.py"
        if module is None or Path(module.__file__).resolve() != expected:
            raise ValueError("unexpected provider fixture module")
        self.conftest, self.original_run = module, module.run_script
        module.run_script = self.run_script

    def pytest_unconfigure(self):
        if self.conftest is not None:
            self.conftest.run_script = self.original_run

    def run_script(self, script, *args, **kwargs):
        path = Path(script)
        if not path.is_absolute():
            path = Path(kwargs.get("cwd") or Path.cwd()) / path
        expected = self.bodies.get(path.name)
        # Altered/symlink fixtures keep their original behavior and source.
        regular = (expected is not None and path.is_file() and not path.is_symlink()
                   and path.resolve() == path and path.stat().st_size == len(expected))
        if not regular or path.read_bytes() != expected:
            return self.original_run(script, *args, **kwargs)
        selected = self.target / "scripts" / path.name
        if path.name != "validate-repository-naming.py" and not any(
                str(arg) == "--root" or str(arg).startswith("--root=") for arg in args):
            args = ("--root", str(path.parent.parent), *args)
        self.redirected[path.name] += 1
        return self.original_run(selected, *args, **kwargs)


def import_actual_reader(target):
    path = target / SHAPE_READER
    spec = importlib.util.spec_from_file_location("repo_shape", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["repo_shape"] = module
    spec.loader.exec_module(module)


def verify_integration(record):
    declared = record.get("integration", {})
    expected = {VERIFIER, INSTALLER, "scripts/_shared_openspec.py"}
    if set(declared) != expected:
        raise ValueError("shared integration source selection differs")
    for name, digest in declared.items():
        path = ROOT / name
        if (path.is_symlink() or path.resolve() != path or not path.is_file()
                or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
            raise ValueError("shared integration source differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=tuple(MODES))
    args = parser.parse_args()
    role, relative = MODES[args.mode]
    provider, record = provider_checkout(role)
    target = (ROOT / relative).resolve(strict=True)
    if role == "openspec":
        verify_integration(record)
    verify_copies(provider, target, role, record["commit"])
    if role == "shape":
        import_actual_reader(target)
        plugin = ShapeBindings(provider, target, record)
    else:
        plugin = CollectionBindings(provider, target, role, record)
    import pytest

    os.chdir(provider)
    result = pytest.main([
        *[str(provider / name) for name in record["test_paths"]], "-q", "-rs",
        "--rootdir=" + str(provider), "--confcutdir=" + str(provider),
        "--junitxml=" + str(ROOT / ".coverage-reports" /
                          (args.mode + "-pytest.xml")),
    ], plugins=[plugin])
    if role == "shape":
        print("Actual consumer CLI executions:", json.dumps(plugin.redirected, sort_keys=True))
        if not all(plugin.redirected[name] for name in (
                "validate-manifest.py", "validate-pins.py",
                "validate-repository-naming.py", "bootstrap.py")):
            raise ValueError("a copied CLI was not exercised")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
