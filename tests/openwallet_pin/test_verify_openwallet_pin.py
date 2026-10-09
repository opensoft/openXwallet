"""`scripts/verify-openwallet-pin.py` — every refusal OBSERVED on a mutated input.

`split-openwallet-neutral-core` task 5.1: the verifier is trusted only once it
has been seen refusing each of design.md D6's seven, so each test below is ONE
fact away from a world that verifies clean, and the clean world is itself a
test (without it, every refusal below would pass just as well against a
verifier that refused everything).

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

# design.md D6's seven, in its order, and the referent guard.
RATIFIED_CODES = (
    "pin-submodule-uninitialized",
    "pin-leg-uninitialized",
    "pin-gitlink-mismatch",
    "pin-checkout-mismatch",
    "pin-leg-lockstep-mismatch",
    "pin-leg-checkout-mismatch",
    "pin-digest-mismatch",
    "pin-member-missing",
    "pin-tag-only",
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
    digests: dict[str, str]


@pytest.fixture(scope="module")
def upstream(tmp_path_factory: pytest.TempPathFactory) -> Upstream:
    with pytest.MonkeyPatch.context() as env:
        env.setenv("GIT_CONFIG_GLOBAL", os.devnull)
        env.setenv("GIT_CONFIG_NOSYSTEM", "1")
        return _build_upstream(tmp_path_factory.mktemp("upstream"))


def _build_upstream(base: Path) -> Upstream:
    leg = _init(base / "openWallet-code")
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

    def root_commit(gitlink: str, pinned: str, label: str) -> str:
        _write(root, "contracts/code-pin.yaml",
               yaml.safe_dump({"kind": "pinned_contract_manifest",
                               "leg_role": "code", "submodule_path": LEG,
                               "commit": pinned}))
        _write(root, "README.md", f"{label}\n")
        _git(root, "add", "contracts/code-pin.yaml", "README.md")
        _record_gitlink(root, LEG, gitlink)
        return _commit(root, label)

    variants = {
        "root_good": root_commit(leg_good, leg_good, "consistent"),
        "root_other": root_commit(leg_good, leg_good, "consistent, later"),
        "root_gitlink_off": root_commit(leg_other, leg_good, "gitlink off"),
        "root_pin_off": root_commit(leg_good, leg_other, "code-pin off"),
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
