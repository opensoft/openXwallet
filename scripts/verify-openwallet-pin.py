#!/usr/bin/env python3
"""Verify openXwallet's CONSUMPTION of opensoft/openWallet against its pin.

openXwallet no longer carries the wallet standard's core; it RUNS it, in
process, from the gitlink `openWallet/` (split-openwallet-neutral-core, design.md
D5 and D6). `contracts/openwallet-pin.yaml` is the whole of that claim and this
file is the running code that checks it. Everything the pin asserts is checked
here, and nothing it does not assert is inferred.

THE TRUSTED REFERENT IS `commit` PLUS THE EIGHT `sha256`s. `contract_bundle_tag`
is a LABEL printed beside the commit, never the referent. A pin that declares a
`revision_kind` other than `commit`, or a root or leg commit that is not exactly
40 hex, is refused `pin-tag-only` rather than resolved: resolving a movable name
is exactly the network read this tool exists not to perform.

ONE CHAIN, TWO LEVELS (RULED Q2). The gitlink mounts the openWallet ROOT, and
the code leg is reached through the root's own `code` gitlink. So the pin's
`legs.code` is a LOCKSTEP MIRROR, and the mirror is checked against GIT OBJECTS
at the pinned root commit, never against the working tree: the root's `code`
gitlink (`git -C openWallet ls-tree <commit> code`), the `commit:` of the root's
own `contracts/code-pin.yaml` at that commit (`git -C openWallet show
<commit>:contracts/code-pin.yaml`), and `legs.code.commit`. All three equal, or
`pin-leg-lockstep-mismatch`. This is the technique openxFactory uses for its
openDox pin, read one level out.

THE REFUSALS, design.md D6's seven, each under a NAMED code from the fixed
vocabulary `REFUSAL_CODES`:

  1. `pin-submodule-uninitialized` (`openWallet/`) and, SEPARATELY,
     `pin-leg-uninitialized` (`openWallet/code/`): two codes, because the
     remediations differ;
  2. `pin-gitlink-mismatch`: the `openWallet` gitlink recorded at this
     repository's HEAD (or, before the first commit, its index) is not `commit`;
  3. `pin-checkout-mismatch`: the checked-out `openWallet/` is not `commit`;
  4. `pin-leg-lockstep-mismatch`: the three-way mirror above disagrees;
  5. `pin-leg-checkout-mismatch`: the checked-out `openWallet/code/` is not
     `legs.code.commit`;
  6. `pin-digest-mismatch`: a digest drift on any of the eight;
  7. `pin-member-missing`: a digested or `pinned_by_commit_only` member is not
     in the checkout.

and one more in D6's spirit, because a commit pins what a checkout STARTED
as, not what its working tree holds now:

  8. `pin-member-modified`: a `pinned_by_commit_only` member is modified,
     deleted, replaced by a directory, or carries untracked content in the
     working tree of its checkout (`git status --porcelain
     --untracked-files=all -- <member>` is not empty). The eight digested
     members need no such check: their bytes are recomputed.

THE ORDER OF EVALUATION follows dependency, not D6's numbering, and the codes do
not move with it. The shape guards run first, because every later check
compares AGAINST the values they validate: `pin-tag-only` for the referent, and
`pin-unreadable` for a HOLLOWED pin, one whose `files:` is not exactly the eight
or whose `pinned_by_commit_only:` omits the two scripts the entrypoints load.
Then the root, entirely: initialized, recorded, checked out, and the lockstep
read from its objects. Only then the leg: initialized, checked out. Then the
bytes: the digests, then each path-only member present and unmodified. A leg
check made against the wrong root commit would name the leg when the defect is
the root, and the remediation it printed would not fix anything. First
failure, named correctly, beats several failures that need triage.

TWO GITLINK COMPARISONS, NOT ONE, at each level. A stale `git submodule update`
leaves the recorded gitlink right and the checkout wrong; a bumped gitlink with
no update inverts that. The digests in check 6 are recomputed against the
CHECKOUT, so without check 3 a stale checkout would be reported as content
drift.

OFFLINE LAW. This tool reads the pin, the git objects of this repository and of
`openWallet/`, the files under `openWallet/` the pin names, and the working-tree
status of the checkouts that hold them. It never reads
the network, never reads an upstream tree, and never reads a
`contracts/manifest.yaml`, this repository's or the root's: the cross-check
against the root's manifest is a PIN-TIME obligation (the pin's header).

Every refusal carries the one fixed `REMEDIATION` trailer, naming the two-level
scoped init. `--recursive` is deliberately absent and the trailer says so.

`--root PATH` names the repository to verify. It defaults to the repository this
script sits in, and exists so the test suite can verify a throwaway adapter.

Exit codes:
  0  the pin is satisfied at both levels, the eight digests recompute, and
     every path-only member is present and unmodified in its working tree
  2  ANY refusal, and any environment failure: a `git` that cannot be run or
     a file that cannot be read is an `ERROR` line and exit 2, never a
     traceback (whose exit 1 would read as something other than a refusal)

  There is deliberately NO exit 1, following openxFactory's
  `scripts/verify-openxwallet-pin.py`. This repository's sibling
  `scripts/verify-contract-pin.py` splits drift (1) from environment (2); that
  split is not followed here, because this tool answers one question, "may the
  composed validator run against these bytes", and the answer is the same for
  "the pin is stale" and "the leg was never initialized". A two-valued failure
  invites a workflow that treats one of them as a warning, and an unanswerable
  question is never an implicit pass.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
PIN_RELPATH = PurePosixPath("contracts", "openwallet-pin.yaml")

# The one leg this pin records, and the root's own pin file for it
# (`contracts/<role>-pin.yaml`, the root's lockstep grammar).
LEG_ROLE = "code"
ROOT_LEG_PIN = f"contracts/{LEG_ROLE}-pin.yaml"

# The ONE fixed remediation trailer. Scoped, two levels, never the spec leg:
# a recursive init would also fetch `openWallet/spec`, which nothing here reads.
REMEDIATION = (
    "Remediation: run `git submodule update --init openWallet`, then "
    "`git -C openWallet submodule update --init code` (NOT --recursive; the "
    "init is deliberately scoped to the root and its code leg, never the spec "
    "leg). If the pin itself is stale, re-pin in ONE commit: the `openWallet` "
    "gitlink and `commit:` together, with `legs.code.commit` and `files:` "
    "moving only where the new root moved them (contracts/openwallet-pin.yaml)."
)

# The fixed vocabulary, in design.md D6's order, then `pin-member-modified`
# (D6's check 7 carried into the working tree; the module docstring's 8), with
# the referent guard last.
#
# `pin-unreadable` is NOT here, and its absence is the point, as it is in
# openxFactory's verifier: these codes describe a TREE that disagrees with a
# well-formed pin, while `pin-unreadable` describes a pin that cannot be read as
# one. It still exits 2; it is excluded from the vocabulary, not from
# fail-closure.
REFUSAL_CODES: tuple[str, ...] = (
    "pin-submodule-uninitialized",
    "pin-leg-uninitialized",
    "pin-gitlink-mismatch",
    "pin-checkout-mismatch",
    "pin-leg-lockstep-mismatch",
    "pin-leg-checkout-mismatch",
    "pin-digest-mismatch",
    "pin-member-missing",
    "pin-member-modified",
    "pin-tag-only",
)

# design.md D6: `files:` holds the per-file sha256 of "the eight digested
# artifacts". A pin that digests fewer pins fewer bytes than the design says it
# does, and one that digests more names artifacts the design never named; both
# are `pin-unreadable`, never a smaller satisfied claim.
DIGESTED_MEMBER_COUNT = 8

# The bytes this repository's two entrypoints path-load and RUN
# (scripts/validate-openxwallet.py's CORE_PATH and
# scripts/wallet-yaml-syntax-gate.py's CORE_GATE_PATH), relative to
# `submodule_path`. A pin whose `pinned_by_commit_only:` omits either does not
# cover the code that executes, so it is `pin-unreadable`.
LOADED_BY_ENTRYPOINTS: tuple[str, ...] = (
    "code/scripts/validate-openxwallet.py",
    "code/scripts/wallet-yaml-syntax-gate.py",
)

# Exactly 40 / 64 hex; case is normalized to lowercase before any comparison.
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

# A gitlink is mode 160000 in both `ls-tree` and `ls-files -s` output. Matching
# the MODE, not just the path, is what keeps a same-named regular file from
# satisfying a gitlink check.
GITLINK_MODE = "160000"

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR PyYAML is required to read contracts/openwallet-pin.yaml",
          file=sys.stderr)
    sys.exit(2)


class PinRefusal(Exception):
    """A named, remediable refusal. `str()` renders the code, the detail and
    the fixed trailer, and `main()` prints exactly that, so no caller can drop
    the trailer."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(code, detail)

    def __str__(self) -> str:
        return f"REFUSE {self.code}: {self.detail}\n{REMEDIATION}"


class EnvironmentFailure(Exception):
    """The verifier could not ask its question: `git` cannot be run, or a file
    the pin names cannot be read. Not a refusal of the tree, and not a pass:
    `main()` prints one `ERROR` line and exits 2."""


class Verified(NamedTuple):
    """What a satisfied pin established, for the one OK line."""
    commit: str
    leg_commit: str
    gitlink_source: str
    digests: int
    members: int
    tag_label: str


# --------------------------------------------------------------------------
# reading the pin
# --------------------------------------------------------------------------

def load_pin(pin_path: Path) -> dict:
    """The pin as a mapping, or `pin-unreadable`: without a parseable pin
    there is no claim to check, and that is never a conformant tree."""
    if not pin_path.is_file():
        raise PinRefusal(
            "pin-unreadable",
            f"the pin file {pin_path} does not exist; openXwallet consumes "
            "openWallet only through this pin, so its absence is an "
            "unanswerable question, not an unpinned pass")
    try:
        loaded = yaml.safe_load(pin_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PinRefusal(
            "pin-unreadable",
            f"the pin file {pin_path} could not be read as YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise PinRefusal(
            "pin-unreadable",
            f"the pin file {pin_path} is not a mapping")
    return loaded


def _relative_path(raw: object, field: str) -> str:
    """A non-empty RELATIVE path that stays below its base, or
    `pin-unreadable`. A pin cannot name a file outside the checkout it pins."""
    if not isinstance(raw, str) or not raw.strip():
        raise PinRefusal("pin-unreadable",
                         f"the pin's {field} is not a usable path ({raw!r})")
    path = PurePosixPath(raw.strip())
    if path.is_absolute() or ".." in path.parts:
        raise PinRefusal(
            "pin-unreadable",
            f"the pin's {field} {raw!r} leaves the checkout it pins; every "
            "pinned path is relative and stays below its submodule")
    return str(path)


def _commit(raw: object, field: str) -> str:
    """The 40-hex referent, lowercased, or `pin-tag-only`."""
    if not isinstance(raw, str) or not COMMIT_RE.match(raw.strip()):
        raise PinRefusal(
            "pin-tag-only",
            f"the pin records {field} {raw!r}, which is not exactly 40 hex "
            "characters; an abbreviated oid, a branch or a tag is not a "
            "compatibility pin")
    return raw.strip().lower()


def _leg(pin: dict) -> tuple[str, str]:
    """(`legs.code.submodule_path`, `legs.code.commit`). The pin records the
    code leg and nothing else: an unrecorded leg is design.md D6's call, and a
    recorded leg this tool did not check would be an assertion nobody checks."""
    legs = pin.get("legs")
    if not isinstance(legs, dict) or set(legs) != {LEG_ROLE}:
        raise PinRefusal(
            "pin-unreadable",
            f"the pin's `legs` must record exactly the {LEG_ROLE!r} leg (got "
            f"{sorted(legs) if isinstance(legs, dict) else legs!r}); the spec "
            "leg is fixed by the root commit and is never recorded here")
    leg = legs[LEG_ROLE]
    if not isinstance(leg, dict):
        raise PinRefusal("pin-unreadable",
                         f"the pin's legs.{LEG_ROLE} is not a mapping")
    path = _relative_path(leg.get("submodule_path"),
                          f"legs.{LEG_ROLE}.submodule_path")
    return path, _commit(leg.get("commit"), f"legs.{LEG_ROLE}.commit")


def _referent(pin: dict) -> tuple[str, str]:
    """(`submodule_path`, `commit`), the shape guard included. It runs before
    every comparison, because every comparison is made against these values,
    and a malformed referent reported as a tree mismatch would name the wrong
    defect."""
    revision_kind = pin.get("revision_kind")
    if revision_kind != "commit":
        raise PinRefusal(
            "pin-tag-only",
            f"the pin declares revision_kind {revision_kind!r}, not 'commit'; "
            "the trusted referent is a commit plus digests, and resolving a "
            "movable name would need the network read this tool refuses")
    path = _relative_path(pin.get("submodule_path"), "submodule_path")
    return path, _commit(pin.get("commit"), "commit")


# --------------------------------------------------------------------------
# reading git
# --------------------------------------------------------------------------

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """`git -C repo ...`, never taking an optional lock (a verifier writes
    nothing, not even a refreshed index), or EnvironmentFailure when `git`
    itself cannot be run."""
    try:
        return subprocess.run(
            ["git", "--no-optional-locks", "-C", str(repo), *args],
            capture_output=True, text=True, check=False)
    except OSError as exc:
        raise EnvironmentFailure(
            f"git could not be run in {repo}: {exc}") from exc


def _gitlink_from(output: str, path: str) -> str | None:
    """The oid of the `160000` entry for `path` in either output shape:

        ls-tree      160000 commit <oid>\\t<path>
        ls-files -s  160000 <oid> 0\\t<path>
    """
    for line in output.splitlines():
        head, _, entry = line.partition("\t")
        fields = head.split()
        if entry.strip().strip('"') != path or not fields \
                or fields[0] != GITLINK_MODE:
            continue
        for field in fields[1:]:
            if COMMIT_RE.match(field):
                return field.lower()
    return None


def _recorded_gitlink(repo: Path, path: str) -> tuple[str | None, str]:
    """(oid, source): HEAD first, then the index.

    The index is consulted second for the reason openxFactory's verifier gives:
    `ls-tree HEAD` is empty for a gitlink staged and not yet committed, which is
    the state of a fresh `git submodule add`, and a gate unrunnable at the
    moment its author most needs it trains people to skip it. The source is
    reported in the OK line so no reader mistakes which record answered.
    """
    head = _git(repo, "ls-tree", "HEAD", "--", path)
    oid = _gitlink_from(head.stdout, path) if head.returncode == 0 else None
    if oid is not None:
        return oid, "HEAD"
    index = _git(repo, "ls-files", "-s", "--", path)
    oid = _gitlink_from(index.stdout, path) if index.returncode == 0 else None
    if oid is not None:
        return oid, "the index (staged, not yet committed)"
    return None, "nowhere"


def _checked_out(checkout: Path) -> str | None:
    head = _git(checkout, "rev-parse", "HEAD")
    return head.stdout.strip().lower() if head.returncode == 0 else None


def _root_leg_pin_commit(root_checkout: Path, commit: str) -> str | None:
    """`commit:` of the root's own leg pin, read as a git BLOB at `commit`."""
    shown = _git(root_checkout, "show", f"{commit}:{ROOT_LEG_PIN}")
    if shown.returncode != 0:
        return None
    try:
        doc = yaml.safe_load(shown.stdout)
    except yaml.YAMLError:
        return None
    value = doc.get("commit") if isinstance(doc, dict) else None
    return value.strip().lower() if isinstance(value, str) else None


# --------------------------------------------------------------------------
# the checks
# --------------------------------------------------------------------------

def _require_initialized(checkout: Path, shown: str, code: str,
                         init: str) -> None:
    """Check 1, at one level. `.exists()`, never `.is_dir()`: a submodule's
    `.git` is a FILE holding a `gitdir:` line, and a nested clone's is a
    directory; both are initialized checkouts."""
    if not (checkout / ".git").exists():
        raise PinRefusal(
            code,
            f"{shown}/.git does not exist: {shown} is not initialized, so the "
            f"bytes this repository runs are not present to be checked. Run "
            f"`{init}` for this level")


def _require_checkout(checkout: Path, shown: str, expected: str, code: str,
                      pinned_as: str) -> None:
    """Checks 3 and 5: the checked-out revision is the pinned one."""
    actual = _checked_out(checkout)
    if actual != expected:
        raise PinRefusal(
            code,
            f"{shown} is checked out at {actual or '<no resolvable HEAD>'}, "
            f"but the pin records {pinned_as} {expected}; the working "
            "checkout is not the revision this repository consumes")


def _require_recorded_gitlink(root: Path, path: str, commit: str) -> str:
    """Check 2. Returns the source that answered, for the OK line."""
    recorded, source = _recorded_gitlink(root, path)
    if recorded is None:
        raise PinRefusal(
            "pin-gitlink-mismatch",
            f"{root} records no {GITLINK_MODE} gitlink for {path} in HEAD or "
            f"in the index, so nothing fixes the pinned {commit}; a checkout "
            "present on disk but absent from the tree is not a pinned "
            "consumption")
    if recorded != commit:
        raise PinRefusal(
            "pin-gitlink-mismatch",
            f"the gitlink {root} records for {path} (read from {source}) is "
            f"{recorded}, but the pin records {commit}; the tree and the pin "
            "disagree about which openWallet root this repository consumes")
    return source


def _require_lockstep(root_checkout: Path, shown: str, commit: str,
                      leg_path: str, leg_commit: str) -> None:
    """Check 4, from GIT OBJECTS at the pinned root commit, never from the
    working tree: a working-tree read would let an unrelated local edit to the
    root's pin file pass or fail the mirror."""
    listed = _git(root_checkout, "ls-tree", commit, "--", leg_path)
    facts = {
        f"the root's `{leg_path}` gitlink at {commit[:12]}":
            _gitlink_from(listed.stdout, leg_path)
            if listed.returncode == 0 else None,
        f"`commit:` of the root's {ROOT_LEG_PIN} at {commit[:12]}":
            _root_leg_pin_commit(root_checkout, commit),
        f"legs.{LEG_ROLE}.commit in this pin": leg_commit,
    }
    if set(facts.values()) == {leg_commit}:
        return
    stated = "\n".join(f"  {name}: {value or '<absent>'}"
                       for name, value in facts.items())
    raise PinRefusal(
        "pin-leg-lockstep-mismatch",
        f"the {LEG_ROLE} leg is not in lockstep in {shown}:\n{stated}\n"
        "the three are ONE invariant and move in ONE commit; a leg mirror that "
        "disagrees with the root it mirrors names a leg the root does not pin")


def _require_digests(checkout: Path, shown: str, pin: dict) -> int:
    """Check 6, and check 7 for a digested member. Returns the count."""
    entries = pin.get("files")
    if not isinstance(entries, list):
        raise PinRefusal("pin-unreadable",
                         f"the pin's `files:` is not a list ({entries!r})")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise PinRefusal("pin-unreadable",
                             f"the pin's files[{index}] is not a mapping")
        rel = _relative_path(entry.get("path"), f"files[{index}].path")
        recorded = entry.get("sha256")
        if not isinstance(recorded, str) or not SHA256_RE.match(recorded.strip()):
            raise PinRefusal(
                "pin-digest-mismatch",
                f"{shown}/{rel}: the pin records sha256 {recorded!r}, which is "
                "not 64 hex characters; a recomputed digest can never equal a "
                "digest that is not one")
        target = checkout / rel
        if not target.is_file():
            raise PinRefusal(
                "pin-member-missing",
                f"{shown}/{rel} is MISSING from the checkout, but the pin "
                "records a sha256 for it")
        try:
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError as exc:
            raise EnvironmentFailure(
                f"{shown}/{rel} could not be read to recompute its digest: "
                f"{exc}") from exc
        if actual != recorded.strip().lower():
            raise PinRefusal(
                "pin-digest-mismatch",
                f"{shown}/{rel}: DIGEST DRIFT\n"
                f"  recorded   {recorded.strip().lower()}\n"
                f"  recomputed {actual}\n"
                "the bytes on disk are not the bytes this pin consumes")
    return len(entries)


def _require_pin_shape(pin: dict) -> None:
    """The HOLLOWED-PIN guard, a shape check run with the referent's, before
    any tree is read: `files:` digests exactly design.md D6's eight, and
    `pinned_by_commit_only:` covers the bytes the entrypoints run. Without it a
    pin cut to one digest, or one that stopped naming the loaded core, would
    verify clean while pinning less than this repository executes."""
    entries = pin.get("files")
    if not isinstance(entries, list) or len(entries) != DIGESTED_MEMBER_COUNT:
        count = len(entries) if isinstance(entries, list) else entries
        raise PinRefusal(
            "pin-unreadable",
            f"the pin's `files:` holds {count!r} entr(ies), not design.md "
            f"D6's {DIGESTED_MEMBER_COUNT} digested artifacts; a pin that "
            "digests fewer bytes than the design names is a hollowed claim, "
            "not a smaller satisfied one")
    members = pin.get("pinned_by_commit_only")
    if not isinstance(members, list):
        raise PinRefusal("pin-unreadable",
                         f"the pin's `pinned_by_commit_only` is not a list "
                         f"({members!r})")
    listed = {_relative_path(raw, f"pinned_by_commit_only[{index}]")
              for index, raw in enumerate(members)}
    absent = [path for path in LOADED_BY_ENTRYPOINTS if path not in listed]
    if absent:
        raise PinRefusal(
            "pin-unreadable",
            f"the pin's `pinned_by_commit_only:` omits {absent}, the bytes "
            "scripts/validate-openxwallet.py and "
            "scripts/wallet-yaml-syntax-gate.py load and run; a pin that does "
            "not cover the code that executes pins the wrong thing")


def _member_checkout(sub_root: Path, sub_path: str, leg_path: str,
                     rel: str) -> tuple[Path, str, str]:
    """(checkout, path inside it, the checkout as shown) for a member named
    relative to `submodule_path`. A member under the leg lives in the LEG's
    checkout, and only that repository's `git status` sees its working tree:
    the root's status shows the leg as one gitlink, never the files in it."""
    member, leg = PurePosixPath(rel), PurePosixPath(leg_path)
    if member.is_relative_to(leg):
        inside = member.relative_to(leg)
        return sub_root / leg, str(inside), f"{sub_path}/{leg_path}"
    return sub_root, rel, sub_path


def _require_unmodified(checkout: Path, inside: str, shown: str,
                        member: str) -> None:
    """Check 8: the member's working tree is exactly the checked-out commit's.
    `--untracked-files=all` lists every untracked file inside a directory
    member, and a file member replaced by a directory reads as deleted."""
    status = _git(checkout, "status", "--porcelain", "--untracked-files=all",
                  "--", inside)
    if status.returncode != 0:
        raise PinRefusal(
            "pin-member-modified",
            f"{member}: `git status` could not be read in {shown} (exit "
            f"{status.returncode}: {status.stderr.strip()}); a member whose "
            "working tree cannot be read is not known to be the pinned bytes")
    if status.stdout.strip():
        changes = "\n".join(f"  {line}" for line in
                            status.stdout.rstrip("\n").splitlines())
        raise PinRefusal(
            "pin-member-modified",
            f"{member} is MODIFIED in the working tree of {shown}:\n{changes}\n"
            "the pin addresses this member by commit, and the checkout's "
            "commit is right, but these are not the bytes that commit holds")


def _require_path_only(sub_root: Path, sub_path: str, leg_path: str,
                       pin: dict) -> int:
    """Checks 7 and 8 for the path-only members. Identity comes from checks 3
    and 5, which pin both checkouts to their commits; what a commit cannot
    catch is the working tree drifting after checkout. So each member must be
    PRESENT (7) and UNMODIFIED in its own checkout's working tree (8): edited,
    deleted, replaced by a directory, or holding untracked content all refuse.
    Returns the count."""
    members = pin.get("pinned_by_commit_only")
    if not isinstance(members, list):
        raise PinRefusal("pin-unreadable",
                         f"the pin's `pinned_by_commit_only` is not a list "
                         f"({members!r})")
    for index, raw in enumerate(members):
        rel = _relative_path(raw, f"pinned_by_commit_only[{index}]")
        if not (sub_root / rel).exists():
            raise PinRefusal(
                "pin-member-missing",
                f"{sub_path}/{rel} is MISSING from the checkout; the pin "
                "declares it content-addressed by commit, and a member absent "
                "from the working tree is content-addressed by nothing")
        checkout, inside, shown = _member_checkout(sub_root, sub_path,
                                                   leg_path, rel)
        _require_unmodified(checkout, inside, shown, f"{sub_path}/{rel}")
    return len(members)


def verify(root: Path = ROOT) -> Verified:
    """Every check, first failure raised and nothing past it. Prints nothing."""
    pin = load_pin(root / PIN_RELPATH)
    sub_path, commit = _referent(pin)
    leg_path, leg_commit = _leg(pin)
    _require_pin_shape(pin)
    sub_root = root / sub_path
    leg_shown = f"{sub_path}/{leg_path}"

    # The root, entirely.
    _require_initialized(sub_root, sub_path, "pin-submodule-uninitialized",
                         f"git submodule update --init {sub_path}")
    source = _require_recorded_gitlink(root, sub_path, commit)
    _require_checkout(sub_root, sub_path, commit, "pin-checkout-mismatch",
                      "commit")
    _require_lockstep(sub_root, sub_path, commit, leg_path, leg_commit)

    # Then the leg.
    _require_initialized(sub_root / leg_path, leg_shown,
                         "pin-leg-uninitialized",
                         f"git -C {sub_path} submodule update --init {leg_path}")
    _require_checkout(sub_root / leg_path, leg_shown, leg_commit,
                      "pin-leg-checkout-mismatch", f"legs.{LEG_ROLE}.commit")

    # Then the bytes.
    digests = _require_digests(sub_root, sub_path, pin)
    members = _require_path_only(sub_root, sub_path, leg_path, pin)
    tag = pin.get("contract_bundle_tag")
    return Verified(commit, leg_commit, source, digests, members,
                    tag if isinstance(tag, str) and tag else "<none yet>")


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """Print one OK line and return 0, or the refusal on stderr and 2."""
    parser = argparse.ArgumentParser(
        prog="verify-openwallet-pin.py",
        description=("Verify contracts/openwallet-pin.yaml against the "
                     "openWallet gitlink, both checkouts, the leg lockstep and "
                     "the digests. Offline."))
    parser.add_argument(
        "--root", metavar="PATH", type=Path, default=ROOT,
        help=("the repository to verify (default: the repository this script "
              "sits in)"))
    args = parser.parse_args(argv)

    try:
        done = verify(args.root.resolve())
    except PinRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (EnvironmentFailure, OSError) as exc:
        print(f"ERROR verify-openwallet-pin: the question could not be asked: "
              f"{exc}", file=sys.stderr)
        return 2

    print(f"OK openwallet-pin verified: openWallet@{done.commit} (tag label "
          f"{done.tag_label}), gitlink read from {done.gitlink_source}, "
          f"{LEG_ROLE} leg @{done.leg_commit} in lockstep (gitlink, "
          f"{ROOT_LEG_PIN}, legs.{LEG_ROLE}), {done.digests} digest(s) "
          f"recomputed, {done.members} path-only member(s) present and "
          "unmodified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
