"""`scripts/verify-openwallet-pin.py` — every refusal OBSERVED on a mutated input.

`split-openwallet-neutral-core` task 5.1: the verifier is trusted only once it
has been seen refusing each of design.md D6's seven, a path-only member
modified in its working tree (`pin-member-modified`), a HOLLOWED pin (a
`files:` that is not the eight, each named once, or a path-only list without
the two loaded scripts), a
pin naming a mount the entrypoints do not execute (`pin-mount-mismatch`), a
code leg whose working tree is not its commit as a whole (`pin-leg-dirty`), and
exiting 2 rather than tracebacking when `git` or a file cannot be read. So
each test below is ONE fact away from a world that verifies clean, and the
clean world is itself a
test (without it, every refusal below would pass just as well against a
verifier that refused everything).

Where a guard closes a world that is otherwise CLEAN, the test first verifies
that world IN PROCESS with that one guard replaced by a no-op, and it must
verify OK (`_verified_without`). That is the control: the refusal then observed
is the guard's, and the world is the one the guard exists for.

WHY THROWAWAY REPOSITORIES. Every refusal is a disagreement between the pin and
a git tree two levels deep, and manufacturing one against this repository would
mean editing the repository under test. So a module fixture builds an UPSTREAM
code leg (two commits) and an UPSTREAM root (one commit per lockstep variant,
each recording a `code` gitlink and a `contracts/code-pin.yaml`), and each test
builds its own ADAPTER under `tmp_path`: a repository recording an `openWallet`
gitlink and a pin, with the root and the leg cloned into it at whatever revision
that test needs. The throwaway pin is the REAL pin with its commits and digests
replaced, so its members are the ones this repository actually pins.

THE SCRIPT IS RUN AS A SUBPROCESS with `--root`, the way a reader runs it, so
the exit code and the printed lines are what is under test. The refusal code
vocabulary and the remediation trailer are restated here as LITERALS: asserting
the module's constants against themselves would be a tautology, and other code
branches by code.

Hermetic: no network (local clones only); git runs with an empty global config
and no system config, and each repository sets its own identity.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER = REPO_ROOT / "scripts" / "verify-openwallet-pin.py"
REAL_PIN = REPO_ROOT / "contracts" / "openwallet-pin.yaml"

# design.md D6's seven, in its order, then the working-tree check D6's check 7
# implies (`pin-member-modified`), and the referent guard.
RATIFIED_CODES = (
    "pin-submodule-uninitialized",
    "pin-leg-uninitialized",
    "pin-gitlink-mismatch",
    "pin-checkout-mismatch",
    "pin-leg-lockstep-mismatch",
    "pin-leg-checkout-mismatch",
    "pin-digest-mismatch",
    "pin-member-missing",
    "pin-member-modified",
    "pin-leg-dirty",
    "pin-tag-only",
    "pin-mount-mismatch",
)

# The ONE fixed trailer: the two-level scoped init, never --recursive.
REMEDIATION = (
    "Remediation: run `git submodule update --init openWallet`, then "
    "`git -C openWallet submodule update --init code` (NOT --recursive; the "
    "init is deliberately scoped to the root and its code leg, never the spec "
    "leg). If the pin itself is stale, re-pin in ONE commit: the `openWallet` "
    "gitlink and `commit:` together, with `legs.code.commit` and `files:` "
    "moving only where the new root moved them (contracts/openwallet-pin.yaml)."
)
ROOT_INIT = "git submodule update --init openWallet"
LEG_INIT = "git -C openWallet submodule update --init code"

# design.md D6's eight digested artifacts, as `files:` spells them: the root
# manifest's owned rows, re-pathed under `code/`.
D6_EIGHT = (
    "code/contracts/openxwallet/openxwallet-record.schema.yaml",
    "code/contracts/openxwallet/openxwallet-custody-registry.schema.yaml",
    "code/contracts/openxwallet/openxwallet-custody.registry.yaml",
    "code/contracts/openxwallet/openxwallet-grant.schema.yaml",
    "code/contracts/openxwallet/openxwallet-grant-exercise.schema.yaml",
    "code/contracts/openxwallet/"
    "openxwallet-distinct-holder-constraint.schema.yaml",
    "code/contracts/openxwallet/openxwallet-subject-attestation.schema.yaml",
    "code/contracts/openxwallet-agent-profile/"
    "openxwallet-agent-composition.schema.yaml",
)


@pytest.fixture(autouse=True)
def _hermetic_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=False)
    assert done.returncode == 0, \
        f"git {' '.join(args)} in {repo} failed: {done.stderr}"
    return done.stdout.strip()


def _init(repo: Path) -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "openwallet-pin-test")
    _git(repo, "config", "user.email", "openwallet-pin-test@example.invalid")
    _git(repo, "config", "commit.gpgsign", "false")
    return repo


def _commit(repo: Path, message: str) -> str:
    """Commit what is STAGED. Never `add -A` here: it would stage the deletion
    of a gitlink that has no working directory, and re-add an embedded clone
    as a gitlink a test meant to remove."""
    _git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _write(repo: Path, rel: str, text: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _record_gitlink(repo: Path, path: str, oid: str) -> None:
    """Stage a 160000 entry without the submodule machinery, so nothing
    reaches a network and no `protocol.file` policy is in play."""
    _git(repo, "update-index", "--add", "--cacheinfo", f"160000,{oid},{path}")


# --------------------------------------------------------------------------
# the upstream: one code leg, one root with every lockstep variant
# --------------------------------------------------------------------------

REAL = yaml.safe_load(REAL_PIN.read_text(encoding="utf-8"))
SUB = REAL["submodule_path"]
LEG = REAL["legs"]["code"]["submodule_path"]

# A second, VALID gitlink at each level: the mount a pin could name instead of
# the one the entrypoints execute.
ALT_SUB = "openWallet-alt"
ALT_LEG = "code-alt"


def _leg_relative(member: str) -> str:
    """A pin member is relative to the ROOT checkout and names the leg first."""
    parts = PurePosixPath(member).parts
    assert parts[0] == LEG, f"{member} is not under the {LEG} leg"
    return str(PurePosixPath(*parts[1:]))


@dataclass(frozen=True)
class Upstream:
    leg: Path
    root: Path
    leg_good: str          # the leg commit everything agrees on
    leg_other: str         # a second leg commit, for every disagreement
    root_good: str         # gitlink = code-pin = leg_good
    root_other: str        # also consistent, but a different root commit
    root_gitlink_off: str  # its `code` gitlink names leg_other
    root_pin_off: str      # its contracts/code-pin.yaml names leg_other
    root_second_leg: str   # consistent, and ALSO records ALT_LEG = leg_good
    digests: dict[str, str]


@pytest.fixture(scope="module")
def upstream(tmp_path_factory: pytest.TempPathFactory) -> Upstream:
    with pytest.MonkeyPatch.context() as env:
        env.setenv("GIT_CONFIG_GLOBAL", os.devnull)
        env.setenv("GIT_CONFIG_NOSYSTEM", "1")
        return _build_upstream(tmp_path_factory.mktemp("upstream"))


def _build_upstream(base: Path) -> Upstream:
    leg = _init(base / "openWallet-code")
    # The real leg's ignore rules for what every run writes.
    _write(leg, ".gitignore", "__pycache__/\n*.py[cod]\n")
    digests = {}
    for entry in REAL["files"]:
        text = f"# a digested member: {entry['path']}\n"
        _write(leg, _leg_relative(entry["path"]), text)
        digests[entry["path"]] = hashlib.sha256(text.encode()).hexdigest()
    for member in REAL["pinned_by_commit_only"]:
        rel = _leg_relative(member)
        # A member with no suffix is a directory (the two corpora); give it a
        # file so git tracks it.
        target = rel if PurePosixPath(rel).suffix else f"{rel}/placeholder.yaml"
        _write(leg, target, f"# a path-only member: {member}\n")
    _git(leg, "add", "-A")
    leg_good = _commit(leg, "the leg the root pins")
    _write(leg, "NOTES.md", "a later leg commit\n")
    _git(leg, "add", "-A")
    leg_other = _commit(leg, "a leg commit nothing should pin")

    root = _init(base / "openWallet")

    def root_commit(gitlink: str, pinned: str, label: str,
                    second_leg: str | None = None) -> str:
        _write(root, "contracts/code-pin.yaml",
               yaml.safe_dump({"kind": "pinned_contract_manifest",
                               "leg_role": "code", "submodule_path": LEG,
                               "commit": pinned}))
        _write(root, "README.md", f"{label}\n")
        _git(root, "add", "contracts/code-pin.yaml", "README.md")
        _record_gitlink(root, LEG, gitlink)
        if second_leg is not None:
            _record_gitlink(root, second_leg, gitlink)
        oid = _commit(root, label)
        if second_leg is not None:
            # Out of the index again, so no later variant records it.
            _git(root, "update-index", "--force-remove", second_leg)
        return oid

    variants = {
        "root_good": root_commit(leg_good, leg_good, "consistent"),
        "root_other": root_commit(leg_good, leg_good, "consistent, later"),
        "root_gitlink_off": root_commit(leg_other, leg_good, "gitlink off"),
        "root_pin_off": root_commit(leg_good, leg_other, "code-pin off"),
        "root_second_leg": root_commit(leg_good, leg_good, "a second leg",
                                       second_leg=ALT_LEG),
    }
    return Upstream(leg=leg, root=root, leg_good=leg_good,
                    leg_other=leg_other, digests=digests, **variants)


# --------------------------------------------------------------------------
# the adapter under test: one fact mutated per test
# --------------------------------------------------------------------------

def _pin_for(up: Upstream, root_commit: str) -> dict:
    """The REAL pin with this world's commits and digests."""
    pin = yaml.safe_load(REAL_PIN.read_text(encoding="utf-8"))
    pin["commit"] = root_commit
    pin["legs"]["code"]["commit"] = up.leg_good
    for entry in pin["files"]:
        entry["sha256"] = up.digests[entry["path"]]
    return pin


def _clone_at(source: Path, dest: Path, commit: str) -> None:
    subprocess.run(["git", "clone", "-q", "--no-checkout", str(source),
                    str(dest)], capture_output=True, check=True)
    _git(dest, "checkout", "-q", "--detach", commit)


def build(tmp_path: Path, up: Upstream, *, pinned_root: str | None = None,
          gitlink: str | None = None, root_checkout: str | None = None,
          leg_checkout: str | None = None, init_root: bool = True,
          init_leg: bool = True, pin: dict | None = None) -> Path:
    """An adapter whose every fact defaults to the clean world."""
    pinned_root = pinned_root or up.root_good
    adapter = _init(tmp_path / "adapter")
    _write(adapter, "contracts/openwallet-pin.yaml",
           yaml.safe_dump(pin or _pin_for(up, pinned_root), sort_keys=False))
    _git(adapter, "add", "contracts/openwallet-pin.yaml")
    _record_gitlink(adapter, SUB, gitlink or pinned_root)
    _commit(adapter, "the adapter")
    if init_root:
        _clone_at(up.root, adapter / SUB, root_checkout or pinned_root)
        if init_leg:
            _clone_at(up.leg, adapter / SUB / LEG, leg_checkout or up.leg_good)
    return adapter


def verify(adapter: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(VERIFIER), "--root",
                           str(adapter)],
                          capture_output=True, text=True, cwd=adapter.parent)


def _verified_without(adapter: Path, guard: str):
    """The CONTROL for one guard: this world, verified IN PROCESS with the
    verifier's `guard` replaced by a no-op. It returns the `Verified` of a
    clean world, or the refusal raised shows which other fact is wrong."""
    module = _load_verifier()
    setattr(module, guard, lambda *args, **kwargs: None)
    return module.verify(adapter.resolve())


def assert_refused(done: subprocess.CompletedProcess[str], code: str) -> str:
    """Exit 2, exactly one refusal, under `code`, with the fixed trailer."""
    assert done.returncode == 2, done.stdout + done.stderr
    assert done.stdout == "", done.stdout
    refusals = [line for line in done.stderr.splitlines()
                if line.startswith("REFUSE ")]
    assert len(refusals) == 1, done.stderr
    assert refusals[0].startswith(f"REFUSE {code}: "), done.stderr
    assert done.stderr.rstrip("\n").endswith(REMEDIATION), done.stderr
    return done.stderr


# --------------------------------------------------------------------------
# the clean world, then one refusal per fact
# --------------------------------------------------------------------------

def test_the_clean_world_verifies(tmp_path, upstream):
    done = verify(build(tmp_path, upstream))
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.startswith(
        f"OK openwallet-pin verified: openWallet@{upstream.root_good} "), \
        done.stdout
    assert "gitlink read from HEAD" in done.stdout, done.stdout
    assert f"code leg @{upstream.leg_good} in lockstep" in done.stdout
    assert f"{len(REAL['files'])} digest(s) recomputed" in done.stdout
    assert (f"{len(REAL['pinned_by_commit_only'])} path-only member(s) "
            "present") in done.stdout


def test_an_uninitialized_root_refuses_with_its_own_remediation(
        tmp_path, upstream):
    adapter = build(tmp_path, upstream, init_root=False)
    (adapter / SUB).mkdir()  # what an uninitialized submodule leaves behind
    err = assert_refused(verify(adapter), "pin-submodule-uninitialized")
    assert f"Run `{ROOT_INIT}` for this level" in err, err


def test_an_uninitialized_leg_refuses_with_its_own_remediation(
        tmp_path, upstream):
    adapter = build(tmp_path, upstream, init_leg=False)
    err = assert_refused(verify(adapter), "pin-leg-uninitialized")
    assert f"Run `{LEG_INIT}` for this level" in err, err


def test_a_recorded_gitlink_other_than_the_pin_refuses(tmp_path, upstream):
    adapter = build(tmp_path, upstream, gitlink=upstream.root_other)
    err = assert_refused(verify(adapter), "pin-gitlink-mismatch")
    assert upstream.root_other in err and "read from HEAD" in err, err


def test_a_gitlink_recorded_nowhere_refuses(tmp_path, upstream):
    adapter = build(tmp_path, upstream)
    _git(adapter, "rm", "-q", "--cached", SUB)
    _commit(adapter, "drop the gitlink, keep the checkout")
    assert_refused(verify(adapter), "pin-gitlink-mismatch")


def test_a_staged_gitlink_is_read_from_the_index(tmp_path, upstream):
    """Before the first commit a fresh `git submodule add` is only in the
    index; the verifier must run there, and must say which record answered."""
    adapter = build(tmp_path, upstream)
    _git(adapter, "rm", "-q", "--cached", SUB)
    _commit(adapter, "drop the gitlink")
    _record_gitlink(adapter, SUB, upstream.root_good)
    done = verify(adapter)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "gitlink read from the index (staged, not yet committed)" in \
        done.stdout, done.stdout


def test_a_root_checkout_other_than_the_pin_refuses(tmp_path, upstream):
    adapter = build(tmp_path, upstream, root_checkout=upstream.root_other)
    err = assert_refused(verify(adapter), "pin-checkout-mismatch")
    assert upstream.root_other in err, err


def test_the_roots_code_gitlink_disagreeing_refuses_lockstep(
        tmp_path, upstream):
    adapter = build(tmp_path, upstream, pinned_root=upstream.root_gitlink_off)
    err = assert_refused(verify(adapter), "pin-leg-lockstep-mismatch")
    assert f"the root's `code` gitlink at {upstream.root_gitlink_off[:12]}: " \
        f"{upstream.leg_other}" in err, err


def test_the_roots_code_pin_disagreeing_refuses_lockstep(tmp_path, upstream):
    adapter = build(tmp_path, upstream, pinned_root=upstream.root_pin_off)
    err = assert_refused(verify(adapter), "pin-leg-lockstep-mismatch")
    assert "`commit:` of the root's contracts/code-pin.yaml at " \
        f"{upstream.root_pin_off[:12]}: {upstream.leg_other}" in err, err


def test_the_pins_leg_mirror_disagreeing_refuses_lockstep(tmp_path, upstream):
    pin = _pin_for(upstream, upstream.root_good)
    pin["legs"]["code"]["commit"] = upstream.leg_other
    adapter = build(tmp_path, upstream, pin=pin)
    err = assert_refused(verify(adapter), "pin-leg-lockstep-mismatch")
    assert f"legs.code.commit in this pin: {upstream.leg_other}" in err, err


def test_lockstep_is_read_from_git_objects_not_the_working_tree(
        tmp_path, upstream):
    """A working-tree edit to the root's pin file moves no verdict either way:
    the clean world stays clean, and a disagreeing root stays refused."""
    clean = build(tmp_path / "clean", upstream)
    _write(clean / SUB, "contracts/code-pin.yaml",
           yaml.safe_dump({"commit": upstream.leg_other}))
    assert verify(clean).returncode == 0

    off = build(tmp_path / "off", upstream, pinned_root=upstream.root_pin_off)
    _write(off / SUB, "contracts/code-pin.yaml",
           yaml.safe_dump({"commit": upstream.leg_good}))
    assert_refused(verify(off), "pin-leg-lockstep-mismatch")


def test_a_leg_checkout_other_than_the_pin_refuses(tmp_path, upstream):
    adapter = build(tmp_path, upstream, leg_checkout=upstream.leg_other)
    err = assert_refused(verify(adapter), "pin-leg-checkout-mismatch")
    assert upstream.leg_other in err, err


def _flip(hexdigest: str) -> str:
    return ("1" if hexdigest[0] == "0" else "0") + hexdigest[1:]


def test_a_flipped_digest_byte_in_the_pin_refuses(tmp_path, upstream):
    pin = _pin_for(upstream, upstream.root_good)
    pin["files"][3]["sha256"] = _flip(pin["files"][3]["sha256"])
    err = assert_refused(verify(build(tmp_path, upstream, pin=pin)),
                         "pin-digest-mismatch")
    assert "DIGEST DRIFT" in err and pin["files"][3]["path"] in err, err


def test_a_flipped_byte_on_disk_refuses(tmp_path, upstream):
    adapter = build(tmp_path, upstream)
    target = adapter / SUB / REAL["files"][0]["path"]
    data = bytearray(target.read_bytes())
    data[0] ^= 0x01
    target.write_bytes(bytes(data))
    assert_refused(verify(adapter), "pin-digest-mismatch")


def test_a_missing_digested_member_refuses(tmp_path, upstream):
    adapter = build(tmp_path, upstream)
    (adapter / SUB / REAL["files"][-1]["path"]).unlink()
    assert_refused(verify(adapter), "pin-member-missing")


def test_a_removed_path_only_member_refuses(tmp_path, upstream):
    adapter = build(tmp_path, upstream)
    member = next(m for m in REAL["pinned_by_commit_only"]
                  if m.endswith("README.md"))
    (adapter / SUB / member).unlink()
    err = assert_refused(verify(adapter), "pin-member-missing")
    assert member in err, err


# ---------------- a path-only member drifting in its working tree -------------

def _path_only(suffix: str) -> str:
    return next(m for m in REAL["pinned_by_commit_only"] if m.endswith(suffix))


def test_a_modified_path_only_member_refuses(tmp_path, upstream):
    """The leg is checked out at the pinned commit, so checks 3 and 5 pass, and
    the loaded core gains ONE byte. A commit pins what the checkout started as;
    only the working tree says what runs."""
    adapter = build(tmp_path, upstream)
    member = _path_only("scripts/validate-openxwallet.py")
    with (adapter / SUB / member).open("ab") as handle:
        handle.write(b"#")
    err = assert_refused(verify(adapter), "pin-member-modified")
    assert f"{SUB}/{member} is MODIFIED in the working tree of {SUB}/{LEG}" \
        in err, err
    assert f" M {_leg_relative(member)}" in err, err


def test_a_path_only_member_replaced_by_a_directory_refuses(tmp_path,
                                                            upstream):
    """`exists()` is true of a directory, so presence alone would pass this."""
    adapter = build(tmp_path, upstream)
    member = _path_only("openxwallet/README.md")
    target = adapter / SUB / member
    target.unlink()
    target.mkdir()
    (target / "planted.yaml").write_text("kind: planted\n", encoding="utf-8")
    err = assert_refused(verify(adapter), "pin-member-modified")
    assert f" D {_leg_relative(member)}" in err, err
    assert f"?? {_leg_relative(member)}/planted.yaml" in err, err


def test_untracked_content_in_a_directory_member_refuses(tmp_path, upstream):
    """A corpus directory is a member: a file planted in it is adjudicated by
    the core's corpus loop as if the pinned commit carried it."""
    adapter = build(tmp_path, upstream)
    member = _path_only("openxwallet/examples")
    (adapter / SUB / member / "planted.yaml").write_text(
        "kind: planted\n", encoding="utf-8")
    err = assert_refused(verify(adapter), "pin-member-modified")
    assert f"?? {_leg_relative(member)}/planted.yaml" in err, err


# ------------------ a pin naming a mount nothing executes --------------------

EXECUTED = ("scripts/validate-openxwallet.py and "
            "scripts/wallet-yaml-syntax-gate.py execute the mount")
LOADED = ("openWallet/code/scripts/validate-openxwallet.py and "
          "openWallet/code/scripts/wallet-yaml-syntax-gate.py")


def test_a_pin_naming_another_valid_root_gitlink_refuses(tmp_path, upstream):
    """Codex's case at the root. The adapter records a SECOND gitlink, checked
    out at the pinned root with its leg, and the pin names it. The mount the
    entrypoints execute, `openWallet/`, sits at a root nothing verifies. Every
    check but the mount's would pass against the second checkout."""
    pin = _pin_for(upstream, upstream.root_good)
    pin["submodule_path"] = ALT_SUB
    adapter = build(tmp_path, upstream, pin=pin, gitlink=upstream.root_other,
                    root_checkout=upstream.root_other)
    _record_gitlink(adapter, ALT_SUB, upstream.root_good)
    _commit(adapter, "a second, valid openWallet gitlink")
    _clone_at(upstream.root, adapter / ALT_SUB, upstream.root_good)
    _clone_at(upstream.leg, adapter / ALT_SUB / LEG, upstream.leg_good)
    control = _verified_without(adapter, "_require_executed_mount")
    assert (control.commit, control.digests) == (upstream.root_good, 8)

    err = assert_refused(verify(adapter), "pin-mount-mismatch")
    assert (f"the pin records submodule_path {ALT_SUB!r}, but {EXECUTED} "
            f"'openWallet' ({LOADED}); a pin that names another checkout "
            "authenticates bytes that never run") in err, err


def test_a_pin_naming_another_valid_leg_gitlink_refuses(tmp_path, upstream):
    """Codex's case at the leg. The pinned root records a SECOND leg gitlink,
    in lockstep, checked out at the pinned leg commit, and the pin's leg names
    it. The leg the entrypoints execute, `openWallet/code/`, sits at a leg
    commit nothing verifies."""
    pin = _pin_for(upstream, upstream.root_second_leg)
    pin["legs"]["code"]["submodule_path"] = ALT_LEG
    adapter = build(tmp_path, upstream, pinned_root=upstream.root_second_leg,
                    pin=pin, leg_checkout=upstream.leg_other)
    _clone_at(upstream.leg, adapter / SUB / ALT_LEG, upstream.leg_good)
    control = _verified_without(adapter, "_require_executed_mount")
    assert (control.leg_commit, control.digests) == (upstream.leg_good, 8)

    err = assert_refused(verify(adapter), "pin-mount-mismatch")
    assert (f"the pin records legs.code.submodule_path {ALT_LEG!r}, but "
            f"{EXECUTED} 'code' ({LOADED})") in err, err


# ------------- the code leg's working tree, as a whole ----------------------

PROFILE_DIR = "contracts/openxwallet-agent-profile"
SHADOW = f"{PROFILE_DIR}/openxwallet-grant.schema.yaml"


def test_an_untracked_schema_shadowing_a_digested_one_refuses(tmp_path,
                                                              upstream):
    """Lane 1's case: the core's load_schemas() keys every `*.schema.yaml` in
    both family directories by bare file name, so this untracked file in the
    PROFILE directory replaces the digested grant schema. It is no member and
    no digested path, so checks 6 to 8 all pass."""
    adapter = build(tmp_path, upstream)
    _write(adapter / SUB / LEG, SHADOW,
           "$schema: https://json-schema.org/draft/2020-12/schema\n"
           "$id: shadow\ntype: object\n")
    assert _verified_without(adapter, "_require_leg_clean").digests == 8

    err = assert_refused(verify(adapter), "pin-leg-dirty")
    assert (f"the working tree of {SUB}/{LEG} is not its checked-out commit; "
            f"`git status` lists 1 change(s):\n  ?? {SHADOW}\n") in err, err
    assert f"Inspect it with `git -C {SUB}/{LEG} status`" in err, err


def test_ignored_bytecode_in_the_leg_does_not_refuse(tmp_path, upstream):
    """What every run writes, and the leg's tracked `.gitignore` ignores, is
    not a dirty leg: `git status` gets no `--ignored`, and the unfiltered
    listing under contracts/ and scripts/ exempts bytecode under scripts/.
    Ignored content the core never reads, outside those two, passes too."""
    adapter = build(tmp_path, upstream)
    leg = adapter / SUB / LEG
    _write(leg, ".git/info/exclude", ".venv/\n")
    for rel in ("__pycache__/x.pyc",
                "scripts/__pycache__/x.cpython-312.pyc",
                "scripts/__pycache__/validate-openxwallet.cpython-312.pyc",
                ".venv/bin/python"):
        _write(leg, rel, "bytecode\n")
    done = verify(adapter)
    assert done.returncode == 0, done.stdout + done.stderr


def _hidden_refusal(planted: str) -> str:
    return ("1 untracked file(s) under contracts/ and scripts/, which the core "
            "reads, hidden from `git status` by an ignore rule:\n"
            f"  {planted}\n")


def test_an_example_hidden_by_info_exclude_refuses(tmp_path, upstream):
    """Lane 1's case: `git status` applies the leg's info/exclude, so a
    planted corpus example it hides passes the member check on its examples
    directory and the status read alike, and the core counts it."""
    adapter = build(tmp_path, upstream)
    leg = adapter / SUB / LEG
    _write(leg, ".git/info/exclude", "zz-*.yaml\n")
    planted = "contracts/openxwallet/examples/zz-planted.example.yaml"
    _write(leg, planted, "kind: planted\n")
    assert _git(leg, "status", "--porcelain", "--untracked-files=all") == ""
    assert _verified_without(adapter, "_require_leg_clean").members == 6

    err = assert_refused(verify(adapter), "pin-leg-dirty")
    assert _hidden_refusal(planted) in err, err
    assert "`git status` lists" not in err, err


def test_a_shadowing_schema_hidden_by_an_excludes_file_refuses(tmp_path,
                                                               upstream):
    """The shadowing case again, hidden by a `core.excludesFile`, the route a
    developer's global ignore takes."""
    adapter = build(tmp_path, upstream)
    leg = adapter / SUB / LEG
    excludes = tmp_path / "excludes"
    excludes.write_text("*.schema.yaml\n", encoding="utf-8")
    _git(leg, "config", "core.excludesFile", str(excludes))
    _write(leg, SHADOW, "type: object\n")
    assert _git(leg, "status", "--porcelain", "--untracked-files=all") == ""

    err = assert_refused(verify(adapter), "pin-leg-dirty")
    assert _hidden_refusal(SHADOW) in err, err


def test_bytecode_outside_scripts_refuses(tmp_path, upstream):
    """The bytecode exemption is scoped to scripts/: nothing writes bytecode
    into the contracts the core reads."""
    adapter = build(tmp_path, upstream)
    planted = f"{PROFILE_DIR}/__pycache__/x.cpython-312.pyc"
    _write(adapter / SUB / LEG, planted, "bytecode\n")
    err = assert_refused(verify(adapter), "pin-leg-dirty")
    assert _hidden_refusal(planted) in err, err


def test_a_dirty_leg_names_its_first_entries_and_counts_the_rest(tmp_path,
                                                                 upstream):
    adapter = build(tmp_path, upstream)
    planted = [f"{PROFILE_DIR}/planted-{n}.yaml" for n in range(7)]
    for rel in planted:
        _write(adapter / SUB / LEG, rel, "kind: planted\n")
    err = assert_refused(verify(adapter), "pin-leg-dirty")
    assert "`git status` lists 7 change(s):\n" + "".join(
        f"  ?? {rel}\n" for rel in planted[:5]) + "  ... and 2 more\n" in err, err


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_an_edit_hidden_from_git_status_by_an_index_flag_refuses(tmp_path,
                                                                 upstream,
                                                                 flag):
    """`git status` never reports an edit under assume-unchanged or
    skip-worktree, so the per-member check is blind to it; the loaded core
    gains one byte and would run."""
    adapter = build(tmp_path, upstream)
    member = _path_only("scripts/validate-openxwallet.py")
    _git(adapter / SUB / LEG, "update-index", flag, _leg_relative(member))
    with (adapter / SUB / member).open("ab") as handle:
        handle.write(b"#")
    assert _verified_without(adapter, "_require_leg_clean").members == 6

    err = assert_refused(verify(adapter), "pin-leg-dirty")
    assert ("1 index entr(ies) flagged assume-unchanged or skip-worktree, "
            "whose edits `git status` never reports:\n"
            f"  {_leg_relative(member)}\n") in err, err


# ----------------------- a hollowed pin, and the environment -----------------

def test_a_pin_cut_to_one_digest_refuses(tmp_path, upstream):
    """Fewer digests than design.md D6's eight is a hollowed claim, never a
    smaller satisfied one; the world under it is otherwise clean."""
    pin = _pin_for(upstream, upstream.root_good)
    pin["files"] = pin["files"][:1]
    err = assert_refused(verify(build(tmp_path, upstream, pin=pin)),
                         "pin-unreadable")
    assert "holds 1 entr(ies), not design.md D6's 8" in err, err


def _blob_sha256(repo: Path, commit: str, rel: str) -> str:
    shown = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel}"],
                           capture_output=True, check=True)
    return hashlib.sha256(shown.stdout).hexdigest()


def test_a_duplicate_row_standing_in_for_a_required_one_refuses(tmp_path,
                                                                upstream):
    """Codex's example. Row 1 is replaced by a copy of row 0, VALID digest
    and all: eight rows, eight recomputations, and the custody-registry
    schema pinned by nothing."""
    pin = _pin_for(upstream, upstream.root_good)
    pin["files"][1] = dict(pin["files"][0])
    adapter = build(tmp_path, upstream, pin=pin)
    assert _verified_without(adapter, "_require_digested_set").digests == 8

    err = assert_refused(verify(adapter), "pin-unreadable")
    assert ("holds 8 entr(ies), not design.md D6's 8 digested artifacts each "
            f"named once (missing {[D6_EIGHT[1]]!r}; duplicated "
            f"{[D6_EIGHT[0]]!r})") in err, err


def test_an_unrelated_path_standing_in_for_a_required_one_refuses(tmp_path,
                                                                  upstream):
    """A ninth path for one of the eight: a file the leg really holds, at its
    real digest, in place of the grant schema."""
    unrelated = "code/contracts/openxwallet/README.md"
    pin = _pin_for(upstream, upstream.root_good)
    pin["files"][3] = {"path": unrelated, "sha256": _blob_sha256(
        upstream.leg, upstream.leg_good, _leg_relative(unrelated))}
    adapter = build(tmp_path, upstream, pin=pin)
    assert _verified_without(adapter, "_require_digested_set").digests == 8

    err = assert_refused(verify(adapter), "pin-unreadable")
    assert (f"(missing {[D6_EIGHT[3]]!r}; extra {[unrelated]!r})") in err, err


@pytest.mark.parametrize("dropped", ["code/scripts/validate-openxwallet.py",
                                     "code/scripts/wallet-yaml-syntax-gate.py"])
def test_a_pin_that_stops_naming_a_loaded_script_refuses(tmp_path, upstream,
                                                         dropped):
    pin = _pin_for(upstream, upstream.root_good)
    pin["pinned_by_commit_only"] = [m for m in pin["pinned_by_commit_only"]
                                    if m != dropped]
    err = assert_refused(verify(build(tmp_path, upstream, pin=pin)),
                         "pin-unreadable")
    assert f"omits [{dropped!r}]" in err, err


def test_a_pin_that_is_not_utf8_is_unreadable_never_a_traceback(tmp_path,
                                                                upstream):
    """`read_text` raises UnicodeDecodeError, which is neither an OSError nor
    a YAMLError; uncaught, it was a traceback and exit 1."""
    adapter = build(tmp_path, upstream)
    pin = adapter / "contracts" / "openwallet-pin.yaml"
    pin.write_bytes(b"# \xff\xfe not utf-8\n" + pin.read_bytes())
    done = verify(adapter)
    err = assert_refused(done, "pin-unreadable")
    assert "could not be read as YAML: 'utf-8' codec can't decode" in err, err
    assert "Traceback" not in err, err


def _unsafe_path(pin: dict, field: str) -> str:
    """Sets one pinned path to one that leaves its checkout; returns the
    message the path guard gives it."""
    if field == "files[0].path ../x":
        pin["files"][0]["path"] = value = "../x"
        named = "files[0].path"
    elif field == "files[0].path /etc/passwd":
        pin["files"][0]["path"] = value = "/etc/passwd"
        named = "files[0].path"
    elif field == "pinned_by_commit_only code/../../x":
        value = "code/../../x"
        named = f"pinned_by_commit_only[{len(pin['pinned_by_commit_only'])}]"
        pin["pinned_by_commit_only"].append(value)
    else:
        assert field == "submodule_path ../openWallet", field
        pin["submodule_path"] = value = "../openWallet"
        named = "submodule_path"
    return f"the pin's {named} {value!r} leaves the checkout it pins"


@pytest.mark.parametrize("field", [
    "files[0].path ../x",
    "files[0].path /etc/passwd",
    "pinned_by_commit_only code/../../x",
    "submodule_path ../openWallet",
])
def test_a_pinned_path_that_leaves_its_checkout_is_unreadable(tmp_path,
                                                              upstream, field):
    """The path guard, by ITS message: the closed digest set, the mount guard
    and the member checks would refuse some of these too, under other words
    or codes. `../openWallet` is refused by the path guard, which runs while
    the referent is read, before the mount is compared."""
    pin = _pin_for(upstream, upstream.root_good)
    guarded = _unsafe_path(pin, field)
    err = assert_refused(verify(build(tmp_path, upstream, pin=pin)),
                         "pin-unreadable")
    assert guarded in err, err
    assert "Traceback" not in err, err


def test_a_pin_recording_the_spec_leg_is_unreadable(tmp_path, upstream):
    """The pin records the code leg and nothing else (design.md D6); a spec
    leg would be an assertion nobody checks."""
    pin = _pin_for(upstream, upstream.root_good)
    pin["legs"]["spec"] = {"source_repository": "opensoft/openWallet-spec",
                           "submodule_path": "spec",
                           "commit": upstream.leg_good}
    err = assert_refused(verify(build(tmp_path, upstream, pin=pin)),
                         "pin-unreadable")
    assert "the pin's `legs` must record exactly the 'code' leg (got " \
        "['code', 'spec'])" in err, err
    assert "Traceback" not in err, err


def test_a_git_that_cannot_run_is_exit_2_never_a_traceback(tmp_path,
                                                           upstream):
    """A traceback exits 1, which reads as something other than a refusal."""
    adapter = build(tmp_path, upstream)
    empty = tmp_path / "no-git-here"
    empty.mkdir()
    done = subprocess.run([sys.executable, str(VERIFIER), "--root",
                           str(adapter)], capture_output=True, text=True,
                          cwd=adapter.parent, env=dict(os.environ,
                                                       PATH=str(empty)))
    assert done.returncode == 2, done.stdout + done.stderr
    assert done.stdout == "", done.stdout
    assert done.stderr.startswith("ERROR verify-openwallet-pin: "), done.stderr
    assert "git could not be run" in done.stderr, done.stderr
    assert "Traceback" not in done.stderr, done.stderr


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root reads a mode-000 file, so nothing is "
                           "unreadable to provoke")
def test_an_unreadable_digested_member_is_exit_2_never_a_traceback(
        tmp_path, upstream):
    adapter = build(tmp_path, upstream)
    target = adapter / SUB / REAL["files"][0]["path"]
    target.chmod(0)
    try:
        done = verify(adapter)
    finally:
        target.chmod(0o644)
    assert done.returncode == 2, done.stdout + done.stderr
    assert done.stderr.startswith("ERROR verify-openwallet-pin: "), done.stderr
    assert "could not be read to recompute its digest" in done.stderr
    assert "Traceback" not in done.stderr, done.stderr


@pytest.mark.parametrize("field, value", [
    ("revision_kind", "tag"),
    ("commit", "wallet-v1.6"),
    ("commit", "1c68717f1ae4"),
    ("legs.code.commit", "72313daab1f2"),
])
def test_a_tag_only_or_abbreviated_referent_refuses(tmp_path, upstream,
                                                     field, value):
    pin = _pin_for(upstream, upstream.root_good)
    if field == "legs.code.commit":
        pin["legs"]["code"]["commit"] = value
    else:
        pin[field] = value
    assert_refused(verify(build(tmp_path, upstream, pin=pin)), "pin-tag-only")


# --------------------------------------------------------------------------
# the vocabulary, and the real repository's seat
# --------------------------------------------------------------------------

def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_openwallet_pin",
                                                  VERIFIER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_refusal_vocabulary_is_the_ratified_list():
    module = _load_verifier()
    assert module.REFUSAL_CODES == RATIFIED_CODES
    assert module.REMEDIATION == REMEDIATION


CODE_SHAPE = re.compile(r"pin-[a-z]+(?:-[a-z]+)*")


def test_the_hollowed_pin_guard_is_design_d6s_eight_and_the_loaded_scripts():
    module = _load_verifier()
    assert module.DIGESTED_MEMBER_COUNT == 8 == len(REAL["files"])
    assert module.DIGESTED_MEMBERS == D6_EIGHT == tuple(
        entry["path"] for entry in REAL["files"])
    assert len(set(D6_EIGHT)) == module.DIGESTED_MEMBER_COUNT
    assert set(module.LOADED_BY_ENTRYPOINTS) == {
        "code/scripts/validate-openxwallet.py",
        "code/scripts/wallet-yaml-syntax-gate.py"}
    assert set(module.LOADED_BY_ENTRYPOINTS) <= set(REAL["pinned_by_commit_only"])


# Each entrypoint, and the constant naming the pinned core it path-loads.
ENTRYPOINT_CORES = {
    "scripts/validate-openxwallet.py": "CORE_PATH",
    "scripts/wallet-yaml-syntax-gate.py": "CORE_GATE_PATH",
}


def _module_assignments(script: Path) -> dict[str, ast.expr]:
    """The module-level `NAME = value` nodes of an entrypoint, read from its
    SOURCE. It is not imported: scripts/validate-openxwallet.py loads the
    pinned core at import time and exits 2 where the mount is not
    initialized, and this binding must hold on every checkout."""
    tree = ast.parse(script.read_text(encoding="utf-8"))
    return {node.targets[0].id: node.value for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)}


def _path_below_root(node: ast.expr) -> PurePosixPath:
    """`ROOT / "a" / "b"` as `a/b`; any other shape fails the binding loudly
    rather than being guessed at."""
    parts: list[str] = []
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        assert isinstance(node.right, ast.Constant) \
            and isinstance(node.right.value, str), ast.dump(node.right)
        parts.append(node.right.value)
        node = node.left
    assert isinstance(node, ast.Name) and node.id == "ROOT", ast.dump(node)
    return PurePosixPath(*reversed(parts))


def test_the_executed_mount_is_bound_to_both_entrypoints():
    """The verifier's EXECUTED_ROOT_MOUNT / EXECUTED_LEG_MOUNT are what the two
    entrypoints run: each one's core path sits under `<root>/<leg>/`, its
    MOUNT_LEVELS name those two levels, and the core paths, relative to the
    root mount, are LOADED_BY_ENTRYPOINTS, which are exactly the scripts
    `pinned_by_commit_only` names."""
    module = _load_verifier()
    root, leg = module.EXECUTED_ROOT_MOUNT, module.EXECUTED_LEG_MOUNT
    assert (root, leg) == (SUB, LEG) == ("openWallet", "code")
    assert module.ENTRYPOINTS == tuple(ENTRYPOINT_CORES)
    loaded = set()
    for script, name in ENTRYPOINT_CORES.items():
        assigned = _module_assignments(REPO_ROOT / script)
        core = _path_below_root(assigned[name])
        assert core.parts[:2] == (root, leg), f"{script}: {name} is {core}"
        levels = tuple(level.elts[0].value
                       for level in assigned["MOUNT_LEVELS"].elts)
        assert levels == (root, f"{root}/{leg}"), f"{script}: {levels}"
        loaded.add(str(core.relative_to(root)))
    assert loaded == set(module.LOADED_BY_ENTRYPOINTS)
    assert {member for member in REAL["pinned_by_commit_only"]
            if PurePosixPath(member).suffix == ".py"} == loaded


def test_every_code_the_verifier_can_raise_is_in_the_vocabulary():
    """Every code-shaped string literal in the verifier, whether it is raised
    directly or handed to a helper that raises it. `pin-unreadable` is the one
    code outside the vocabulary, by design: it names a pin that cannot be read,
    not a tree that disagrees with one."""
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    codes = {node.value for node in ast.walk(tree)
             if isinstance(node, ast.Constant) and isinstance(node.value, str)
             and CODE_SHAPE.fullmatch(node.value)}
    assert "pin-unreadable" in codes, "the scan found nothing; it is broken"
    assert codes - {"pin-unreadable"} <= set(RATIFIED_CODES), \
        sorted(codes - set(RATIFIED_CODES))


def test_the_real_repository_verifies():
    """Over THIS checkout, with no arguments, from outside it. Where the mount
    is not initialized the test SKIPS LOUDLY with the two commands, and never
    counts the verifier's refusal as a pass."""
    if not (REPO_ROOT / SUB / LEG / ".git").exists():
        pytest.skip(f"{SUB}/{LEG} is not initialized in this checkout, so the "
                    f"pin cannot be verified here; run `{ROOT_INIT}`, then "
                    f"`{LEG_INIT}` (never --recursive)")
    done = subprocess.run([sys.executable, str(VERIFIER)],
                          capture_output=True, text=True, cwd=REPO_ROOT.parent)
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.startswith(
        f"OK openwallet-pin verified: openWallet@{REAL['commit']} "), \
        done.stdout
    assert f"code leg @{REAL['legs']['code']['commit']} in lockstep" in \
        done.stdout, done.stdout
