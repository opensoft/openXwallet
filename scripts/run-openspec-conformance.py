#!/usr/bin/env python3
"""Run the complete immutable provider pin suite against actual consumer files.

Repository-specific provider evidence remains at its original published root;
the three verifier/installer/pin bindings select the actual scanned consumer.
No tests are deselected and no coverage filenames or hits are rewritten.
The provider directory is an operator environment selection, not parser data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"adapter": ROOT, "spec": ROOT / "openWallet/spec"}


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True).strip()


def provider_checkout():
    selected = os.environ.get("WALLET_ANALYSIS_PROVIDER_ROOT")
    if not selected:
        raise ValueError("operator-selected analysis provider missing")
    provider = Path(selected).resolve(strict=True)
    record = json.loads(
        (ROOT / "requirements/analysis-providers.json").read_text())["openspec"]
    if record["main_admission"] != "verified":
        raise ValueError("provider main admission is not verified")
    if git(provider, "rev-parse", "--show-toplevel") != str(provider):
        raise ValueError("unexpected provider repository")
    if git(provider, "rev-parse", "HEAD") != record["commit"]:
        raise ValueError("provider revision differs")
    if git(provider, "diff", "--name-only", "HEAD"):
        raise ValueError("provider source changed")
    for name, expected in record["files"].items():
        path = provider / name
        if path.is_symlink() or path.resolve() != path or not path.is_file():
            raise ValueError("non-regular provider test source")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("provider test source differs")
    return provider, record


def provider_body(path):
    data = path.read_bytes()
    if path.suffix == ".py":
        lines = data.splitlines(keepends=True)
        if len(lines) > 3 and lines[1].startswith(b"# VENDORED from "):
            data = lines[0] + b"".join(lines[4:])
    elif path.suffix == ".yaml":
        lines = data.splitlines(keepends=True)
        if lines and lines[0].startswith(b"# VENDORED from "):
            data = b"".join(lines[3:])
    return data


class ConsumerBindings:
    def __init__(self, provider, target):
        self.provider = provider
        self.target = target

    def pytest_collection_modifyitems(self, session, config, items):
        expected = self.provider / "tests/openspec_cli_pin/test_openspec_cli_pin.py"
        modules = {item.module for item in items}
        if not items or any(Path(module.__file__).resolve() != expected
                            for module in modules):
            raise ValueError("unexpected or empty provider test collection")
        for module in modules:
            module.SCRIPT = self.target / "scripts/validate-openspec-cli-pin.py"
            module.INSTALLER = self.target / "scripts/install-pinned-openspec-cli.py"
            module.PIN = self.target / "contracts/openspec-cli-pin.yaml"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=tuple(TARGETS))
    args = parser.parse_args()
    provider, record = provider_checkout()
    target = TARGETS[args.target].resolve(strict=True)
    for name in ("scripts/validate-openspec-cli-pin.py",
                 "scripts/install-pinned-openspec-cli.py",
                 "contracts/openspec-cli-pin.yaml",
                 "contracts/openspec-cli-pin.1.12.0.package-lock.json"):
        consumer = target / name
        if consumer.is_symlink() or consumer.resolve() != consumer:
            raise ValueError("linked consumer pin source")
        if provider_body(consumer) != (provider / name).read_bytes():
            raise ValueError("consumer body differs from admitted provider")
    import pytest

    os.chdir(provider)
    return pytest.main([
        str(provider / record["test_paths"][0]), "-q", "-rs",
        "--junitxml=" + str(ROOT / ".coverage-reports" /
                          ("openspec-" + args.target + "-pytest.xml")),
    ], plugins=[ConsumerBindings(provider, target)])


if __name__ == "__main__":
    raise SystemExit(main())
