"""Exercise the contract pin verifier through its real Python entrypoint."""

import hashlib
import importlib.util
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def contract_pin(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[2] / "scripts/verify-contract-pin.py"
    spec = importlib.util.spec_from_file_location("contract_pin_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "PIN_PATH", tmp_path / "contract_pin.yaml")
    artifact = tmp_path / "contract.yaml"
    artifact.write_bytes(b"kind: fixture-contract\n")
    pin = {
        "commit": "a" * 40,
        "revision_kind": "commit",
        "files": [{"path": artifact.name, "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}],
    }
    return module, pin


def test_verifies_the_recorded_content(contract_pin, capsys):
    verifier, pin = contract_pin
    verifier.PIN_PATH.write_text(yaml.safe_dump(pin), encoding="utf-8")

    assert verifier.main() == 0
    output = capsys.readouterr()
    assert "OK contract.yaml sha256=" in output.out
    assert "1 vendored file(s) match" in output.out
    assert output.err == ""


@pytest.mark.parametrize(("overrides", "expected"), [
    ({"commit": ""}, "records no commit"),
    ({"commit": "main"}, "not a 40-hex commit"),
    ({"revision_kind": "branch"}, "expected 'commit'"),
    ({"files": []}, "lists no files"),
    ({"files": [None]}, "files entry is malformed"),
    ({"files": [{"path": "contract.yaml"}]}, "no sha256 recorded"),
    ({"files": [{"path": "contract.yaml", "sha256": "bad"}]}, "not 64 lowercase hex"),
    ({"files": [{"path": "missing.yaml", "sha256": "0" * 64}]}, "vendored file is MISSING"),
    ({"files": [{"path": "contract.yaml", "sha256": "0" * 64}]}, "DIGEST DRIFT"),
])
def test_refuses_missing_or_inconsistent_evidence(contract_pin, capsys, overrides, expected):
    verifier, pin = contract_pin
    pin.update(overrides)
    verifier.PIN_PATH.write_text(yaml.safe_dump(pin), encoding="utf-8")

    assert verifier.main() == 1
    output = capsys.readouterr()
    assert expected in output.err
    assert "remediation:" in output.err
    assert "OK contract pin verified" not in output.out
