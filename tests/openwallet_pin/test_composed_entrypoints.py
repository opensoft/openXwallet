"""The two entrypoints over the pinned core: they compose, and they fail closed.

`split-openwallet-neutral-core` tasks 5.2 and 5.3 (design.md D5).
`scripts/validate-openxwallet.py` loads the pinned validator core from
`openWallet/code/` and registers openXwallet's rules at its extension points;
`scripts/wallet-yaml-syntax-gate.py` delegates to the pinned gate. Neither may
ever read as green when it could not find what it runs, so each refusal is
OBSERVED here: an uninitialized `openWallet/`, an uninitialized
`openWallet/code/` (each with its own remediation), a core that does not load,
and a core without the names the adapter composes against.

WHY A THROWAWAY ROOT. Both entrypoints resolve everything from their own
location, so a copy of each, placed in a scratch root beside a scratch
`openWallet/`, is the real script over a mount this test controls. Most cases
need no real core: a STUB core proves what the adapter does before and around
`main()`, in a fraction of a second. The cases about the adapter's own
negatives need the REAL pinned core and corpus, copied from this checkout's
mount, and skip loudly where the mount is not initialized.

THE SCRIPTS ARE RUN AS SUBPROCESSES, as the workflows run them, so the exit
code and the printed lines are what is under test.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate-openxwallet.py"
GATE = REPO_ROOT / "scripts" / "wallet-yaml-syntax-gate.py"
ENVELOPE = Path("contracts") / "schemas" / "hermes-job-envelope.schema.yaml"
ADAPTER_NEGATIVES = Path("contracts") / "openxwallet" / "examples" / "negative"
MOUNTED_LEG = REPO_ROOT / "openWallet" / "code"

ROOT_INIT = "git submodule update --init openWallet"
LEG_INIT = "git -C openWallet submodule update --init code"

# A core that loads and exposes every name the adapter reads, and whose main()
# reports what had been registered by the time it was called.
STUB_CORE = '''
import sys
import yaml
REQUIREMENTS = {"OXW-R1": "a core row"}
VOCABULARY_BINDING = None
GRANT_RULES, SELF_TEST_HOOKS, SELF_TEST_TAIL_HOOKS, TREE_CHECKS = [], [], [], []
Findings = Context = validate_record = expected_failure = codes_of = None
lines_for = load_yaml = _mapping = _hashable_set = None
fingerprint_of_public_key = None

def main():
    print("binding", VOCABULARY_BINDING["label"], VOCABULARY_BINDING["pointer"])
    for name in ("GRANT_RULES", "SELF_TEST_HOOKS", "SELF_TEST_TAIL_HOOKS",
                 "TREE_CHECKS"):
        print(name, [hook.__name__ for hook in globals()[name]])
    print("requirements", sorted(REQUIREMENTS))
    print("argv", sys.argv[1:])
    return 0
'''

STUB_GATE = '''
import sys

def main():
    print("delegated", sys.argv[1:])
    return 0
'''


def _scratch_root(base: Path, *, core: str | None = STUB_CORE,
                  gate: str | None = STUB_GATE, init_root: bool = True,
                  init_leg: bool = True) -> Path:
    """The two entrypoints and the envelope, over a scratch mount."""
    root = base / "adapter"
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(VALIDATOR, root / "scripts" / VALIDATOR.name)
    shutil.copy2(GATE, root / "scripts" / GATE.name)
    (root / ENVELOPE).parent.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / ENVELOPE, root / ENVELOPE)
    leg_scripts = root / "openWallet" / "code" / "scripts"
    leg_scripts.mkdir(parents=True)
    if init_root:
        (root / "openWallet" / ".git").write_text("gitdir: x\n",
                                                  encoding="utf-8")
    if init_leg:
        (root / "openWallet" / "code" / ".git").write_text("gitdir: x\n",
                                                           encoding="utf-8")
    if core is not None:
        (leg_scripts / VALIDATOR.name).write_text(core, encoding="utf-8")
    if gate is not None:
        (leg_scripts / GATE.name).write_text(gate, encoding="utf-8")
    return root


def _run(root: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / script.name), *args],
        capture_output=True, text=True, cwd=root.parent)


def _assert_refused(done: subprocess.CompletedProcess, code: str) -> str:
    assert done.returncode == 2, done.stdout + done.stderr
    assert done.stdout == "", done.stdout
    assert done.stderr.startswith(f"REFUSE {code}: "), done.stderr
    return done.stderr


# ------------------------------ fail closed --------------------------------

@pytest.mark.parametrize("script", [VALIDATOR, GATE], ids=["validator", "gate"])
def test_an_uninitialized_root_refuses_with_its_own_remediation(tmp_path,
                                                                script):
    root = _scratch_root(tmp_path, init_root=False)
    err = _assert_refused(_run(root, script, "."),
                          "pin-submodule-uninitialized")
    assert f"Run `{ROOT_INIT}` (never --recursive)" in err, err


@pytest.mark.parametrize("script", [VALIDATOR, GATE], ids=["validator", "gate"])
def test_an_uninitialized_leg_refuses_with_its_own_remediation(tmp_path,
                                                               script):
    root = _scratch_root(tmp_path, init_leg=False)
    err = _assert_refused(_run(root, script, "."), "pin-leg-uninitialized")
    assert f"Run `{LEG_INIT}` (never --recursive)" in err, err


@pytest.mark.parametrize("script", [VALIDATOR, GATE], ids=["validator", "gate"])
def test_a_core_that_does_not_load_refuses(tmp_path, script):
    broken = "raise RuntimeError('the pinned bytes are not a module')\n"
    root = _scratch_root(tmp_path, core=broken, gate=broken)
    err = _assert_refused(_run(root, script, "."), "core-unloadable")
    assert "RuntimeError: the pinned bytes are not a module" in err, err


@pytest.mark.parametrize("script", [VALIDATOR, GATE], ids=["validator", "gate"])
def test_a_core_file_that_is_absent_refuses(tmp_path, script):
    root = _scratch_root(tmp_path, core=None, gate=None)
    _assert_refused(_run(root, script, "."), "core-unloadable")


def test_a_core_without_the_composition_contract_refuses(tmp_path):
    """A core that loads but lacks an extension point is not the core this
    adapter composes against; registering into it would be an AttributeError,
    a traceback and exit 1, which reads as FINDINGS."""
    root = _scratch_root(tmp_path, core="def main():\n    return 0\n")
    err = _assert_refused(_run(root, VALIDATOR, "."), "core-unloadable")
    assert "'GRANT_RULES'" in err and "'SELF_TEST_HOOKS'" in err, err


def test_a_requirement_id_the_core_already_declares_refuses(tmp_path):
    """The adapter ADDS rows to the core's closure and never rewrites one."""
    core = STUB_CORE.replace('{"OXW-R1": "a core row"}',
                             '{"OXWR-R1": "the core claims this id"}')
    root = _scratch_root(tmp_path, core=core)
    err = _assert_refused(_run(root, VALIDATOR, "."), "core-unloadable")
    assert "['OXWR-R1']" in err, err


def test_an_absent_envelope_is_the_hard_exit_it_always_was(tmp_path):
    root = _scratch_root(tmp_path)
    (root / ENVELOPE).unlink()
    done = _run(root, VALIDATOR, ".")
    assert done.returncode == 2, done.stdout + done.stderr
    assert done.stdout == "", done.stdout
    assert done.stderr == (
        f"ERROR {root.resolve() / ENVELOPE} not found; the approval-scope "
        "vocabulary is read from the canonical job envelope\n"), done.stderr


# ------------------------------ composition --------------------------------

def test_the_adapter_registers_before_the_core_runs(tmp_path):
    """By the time the core's main() runs, the envelope is bound, every hook
    is registered at its extension point, the two OXWR rows follow the core's
    own, and the command line is passed through untouched."""
    root = _scratch_root(tmp_path)
    done = _run(root, VALIDATOR, "some/tree", "--strict")
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.splitlines() == [
        "binding contracts/schemas/hermes-job-envelope.schema.yaml "
        "['properties', 'job', 'properties', 'approval_policy', 'properties']",
        "GRANT_RULES ['check_review_issuer']",
        "SELF_TEST_HOOKS ['self_test_review_authority']",
        "SELF_TEST_TAIL_HOOKS ['self_test_register_reader']",
        "TREE_CHECKS ['check_register']",
        "requirements ['OXW-R1', 'OXWR-R1', 'OXWR-R2']",
        "argv ['some/tree', '--strict']",
    ], done.stdout


def test_the_gate_entrypoint_delegates_with_its_command_line(tmp_path):
    root = _scratch_root(tmp_path)
    done = _run(root, GATE, "some/tree")
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout == "delegated ['some/tree']\n", done.stdout


# ------------------- the adapter's negatives are adjudicated ---------------

def _real_root(tmp_path: Path) -> Path:
    """A scratch root over a COPY of the real pinned core and corpus, with
    rule (t)'s three negatives beside it, so they can be mutated here."""
    if not (MOUNTED_LEG / ".git").exists():
        pytest.skip(f"openWallet/code is not initialized in this checkout, so "
                    f"there is no pinned core to copy; run `{ROOT_INIT}`, then "
                    f"`{LEG_INIT}` (never --recursive)")
    root = _scratch_root(tmp_path, core=None, gate=None)
    leg = root / "openWallet" / "code"
    for part in ("scripts", "contracts"):
        shutil.copytree(MOUNTED_LEG / part, leg / part, dirs_exist_ok=True)
    (root / ADAPTER_NEGATIVES).mkdir(parents=True)
    for path in sorted((REPO_ROOT / ADAPTER_NEGATIVES).glob(
            "grant-review-*.yaml")):
        shutil.copy2(path, root / ADAPTER_NEGATIVES / path.name)
    return root


def test_the_copied_mount_reproduces_the_composed_corpus(tmp_path):
    """The control for the two mutations below: unmutated, the scratch root
    reports the composed corpus and validates clean."""
    done = _run(_real_root(tmp_path), VALIDATOR)
    assert done.returncode == 0, done.stdout + done.stderr
    assert ("note  corpus: 21 positive example(s), 45 negative "
            "confirmation(s) across 13/13 requirements") in done.stdout


def test_an_adapter_negative_that_validates_cleanly_is_refused(tmp_path):
    """Counted is not adjudicated: a rule (t) negative whose defect is repaired
    must turn the self-test red, exactly as a core negative would."""
    root = _real_root(tmp_path)
    fixture = root / ADAPTER_NEGATIVES / "grant-review-root-issuer-says-opensoft.yaml"
    text = fixture.read_text(encoding="utf-8")
    assert "issued_by: opensoft" in text, text
    fixture.write_text(text.replace("issued_by: opensoft",
                                    "issued_by: Brett.Heap@opensoft.one"),
                       encoding="utf-8")
    done = _run(root, VALIDATOR)
    assert done.returncode == 1, done.stdout + done.stderr
    assert ("ERROR [negative-should-fail] "
            "negative/grant-review-root-issuer-says-opensoft.yaml: expected "
            "invalid, validated cleanly") in done.stdout, done.stdout


def test_a_missing_adapter_negative_is_named_and_uncounted(tmp_path):
    root = _real_root(tmp_path)
    (root / ADAPTER_NEGATIVES / "grant-review-root-issuer-is-a-machine.yaml"
     ).unlink()
    done = _run(root, VALIDATOR)
    assert done.returncode == 1, done.stdout + done.stderr
    assert ("ERROR [examples-missing] S2 named probe "
            "negative/grant-review-root-issuer-is-a-machine.yaml is absent"
            ) in done.stdout, done.stdout
    assert "44 negative confirmation(s)" in done.stdout, done.stdout
