"""Declared-copy integrity and CLI authority checks; no network or real state."""

import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_REVISION = "7aaa749d2defc6ab7e18ffd428283c1ab8dd19c0"
BODY_DIGESTS = {
    "scripts/validate-openspec-cli-pin.py": "316af08da61959a75c4934e85b4ba2db781fb4f887ecce0ace918b57ef386cb7",
    "scripts/install-pinned-openspec-cli.py": "2ef0067678926da91009344b006d67aa9931a46504982329c1f0c7b7dfec1052",
    "contracts/openspec-cli-pin.yaml": "1bab358ce6d5275fcad6fd1af3a4320aebe42d25c158aa0364d680fd4d8fa482",
    "contracts/openspec-cli-pin.1.12.0.package-lock.json": "696dce86e5e5699007129310d9de532795ce48467218fba03b729d38c829e2ca"
}


def provider_body(path):
    raw = path.read_bytes()
    if path.suffix not in (".py", ".yaml"):
        return raw
    header = (
        f"# VENDORED from opensoft/openXfactory@{PROVIDER_REVISION}; do not edit here.\n"
        "# Everything below this header block is byte-identical to the provider.\n"
        "# Current provenance and hashes: docs/openspec-cli-pin.md.\n"
    ).encode()
    if path.suffix == ".py":
        first, rest = raw.split(b"\n", 1)
        if not rest.startswith(header):
            raise ValueError("consumer header differs from declared comments")
        return first + b"\n" + rest[len(header):]
    if not raw.startswith(header):
        raise ValueError("consumer header differs from declared comments")
    return raw[len(header):]


class OpenSpecConsumption(unittest.TestCase):
    def test_all_declared_bodies_equal_the_published_provider(self):
        for name, expected in BODY_DIGESTS.items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256(provider_body((ROOT / "openWallet/spec" if name.endswith(".py") else ROOT) / name)).hexdigest(), expected)

    def test_pin_addresses_the_complete_committed_dependency_lock(self):
        spec = importlib.util.spec_from_file_location(
            "consumer_pin_verifier", ROOT / "openWallet/spec/scripts/validate-openspec-cli-pin.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        path = ROOT / "contracts/openspec-cli-pin.yaml"
        pin = module.read_pin(path)
        lock, address, count = module.pinned_lockfile(pin, path)
        artifact, _sha1 = module.pinned_integrity(pin)
        raw = module.verify_lockfile(lock, address, count, module.pinned_package(pin), artifact)
        self.assertEqual(raw, lock.read_bytes())
        self.assertEqual(module.pinned_version(pin), "1.12.0")

    def test_model_cannot_select_a_forged_pin_before_package_work(self):
        with tempfile.TemporaryDirectory() as directory:
            forged = Path(directory) / "forged.yaml"
            forged.write_text("must never be parsed", encoding="utf-8")
            environment = dict(
                os.environ,
                XFACTORY_OPENSPEC_PIN_PATH=str(ROOT / "contracts/openspec-cli-pin.yaml"),
                XFACTORY_NPM_BINARY="/unavailable/npm",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/validate-openspec-cli-pin.py"),
                    "--all",
                    "--no-cache",
                    "--pin",
                    str(forged),
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--pin differs from operator-selected", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


    def test_replacement_header_cannot_hide_running_code_from_the_body_digest(self):
        for name, index in (("scripts/validate-openspec-cli-pin.py", 2),
                            ("contracts/openspec-cli-pin.yaml", 1)):
            with self.subTest(path=name), tempfile.TemporaryDirectory() as directory:
                raw = ((ROOT / "openWallet/spec" if name.endswith(".py") else ROOT) / name).read_bytes()
                lines = raw.split(b"\n")
                lines[index] = b"raise RuntimeError('must never execute')"
                forged = Path(directory) / Path(name).name
                forged.write_bytes(b"\n".join(lines))
                # The old blind three-line strip would still accept the body.
                stripped = (b"\n".join(lines[:1] + lines[4:])
                            if forged.suffix == ".py" else b"\n".join(lines[3:]))
                self.assertEqual(hashlib.sha256(stripped).hexdigest(), BODY_DIGESTS[name])
                with self.assertRaises(ValueError):
                    provider_body(forged)
