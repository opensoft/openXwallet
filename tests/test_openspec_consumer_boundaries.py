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
BODY_DIGESTS = {
    "scripts/validate-openspec-cli-pin.py": "42f966ceb3c2ce9f11e4587f90a956a1afc52b1ca75adc1b5ac17ccc09514e29",
    "scripts/install-pinned-openspec-cli.py": "082d036c18e40e2794e495633680f62a71795115b250ecd38428e451419fb083",
    "contracts/openspec-cli-pin.yaml": "1bab358ce6d5275fcad6fd1af3a4320aebe42d25c158aa0364d680fd4d8fa482",
    "contracts/openspec-cli-pin.1.12.0.package-lock.json": "696dce86e5e5699007129310d9de532795ce48467218fba03b729d38c829e2ca"
}


def provider_body(path):
    raw = path.read_bytes()
    if path.suffix == ".py":
        return b"\n".join(raw.split(b"\n")[:1] + raw.split(b"\n")[4:])
    if path.suffix == ".yaml":
        return b"\n".join(raw.split(b"\n")[3:])
    return raw


class OpenSpecConsumption(unittest.TestCase):
    def test_all_declared_bodies_equal_the_published_provider(self):
        for name, expected in BODY_DIGESTS.items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256(provider_body(ROOT / name)).hexdigest(), expected)

    def test_pin_addresses_the_complete_committed_dependency_lock(self):
        spec = importlib.util.spec_from_file_location(
            "consumer_pin_verifier", ROOT / "scripts/validate-openspec-cli-pin.py"
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
