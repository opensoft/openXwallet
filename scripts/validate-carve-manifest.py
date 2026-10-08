#!/usr/bin/env python3
"""Verify `docs/openwallet-carve-manifest.yaml` — the DECLARED PATH MAPPING of
the openWallet carve (`split-openwallet-neutral-core`, `design.md` D7 "The
carve manifest", `tasks.md` 2.5).

WHAT THIS FILE IS. D7 asks for "one row per tracked path at the carve commit"
and says that "a tracked path in no row, or in two rows, REFUSES". A manifest
nothing checks is a claim, not a floor, so this is the check. It MIRRORS
openxFactory's `scripts/validate-carve-manifest.py` — the openDox carve's floor
part one, whose grammar D7 adopts — with the same six ordered checks, the same
refusal vocabulary and the same two phases, adapted where D7's manifest
differs from openDox's. It imports nothing from openxFactory: it is
standard-library plus PyYAML (already a `pytest-suite` dependency), reads
nothing but this repository's own git objects, and resolves every path from its
own location, so it runs offline under AGENTS.md rule 4.

HOW IT DIFFERS FROM openDox's CHECKER, and why each difference is D7's:

  * THE COMPLETENESS SURFACE AT THE CARVE COMMIT IS THE WHOLE TREE. openDox
    walked its `moved_paths:` prefixes; D7 asks for every tracked path. So at
    the referent every path `git ls-tree -r` lists must be in exactly one row,
    and no row may name a path it does not list. `moved_paths:` survives with a
    narrower job: it is the SURFACE WATCHED AT THE REVISION UNDER TEST, where a
    file that APPEARS under it after the carve commit refuses and a file `main`
    grows elsewhere — this checker, its test, the manifest itself — does not.
    Every MOVED row must lie inside it, or the watch would miss the very file
    the carve takes.
  * `retained_here:` ON EVERY ROW (`kept`, `shed`, `retired_by_archive`). A
    `not_moved` row is always `kept`; `retired_by_archive` is a promoted spec
    (`openspec/specs/…`) that leaves only by the change's archive; `shed` rows
    are exactly what the adapter rebuild removes (`tasks.md` 5.5), and they are
    what `phase: post-shed` requires ABSENT.
  * `destination_path` EQUALS `source_path` ON EVERY MOVED ROW (D7: within each
    leg every carved path keeps its repository-relative path). A remapped row
    refuses `carve-path-remapped`.
  * THE LEG-CLASSIFICATION OVERRIDES ARE DECLARED. Every moved row records
    `leg_default:`, openRepoShape's classifier verdict for that path; a row
    whose destination leg departs from it must name a `leg_overrides:` entry
    whose `leg` is that destination leg and whose `overrides_rule` is that
    verdict's rule, and a row that does not depart must name none
    (`carve-override-inconsistent`). The verdicts themselves were computed at
    authoring time against the policy `leg_classification:` pins by commit and
    digest; this checker holds the document to them and cannot re-run
    openRepoShape offline, which is stated rather than hidden.
  * THE EDIT CLASSES ARE D7's FIVE, closed in `EDIT_CLASSES` below and asserted
    EQUAL to the manifest's own list, so a manifest cannot declare a sixth.
  * THE `not_moved` REASONS are this repository's, closed in
    `KNOWN_NOT_MOVED_REASONS`; the manifest declares the subset it uses. There
    is no replica reason here, so `edits:` on a `not_moved` row always refuses.

SIX ORDERED CHECKS, FIRST FAILURE WINS (openDox's order):

  1. SHAPE — the document's closed key sets, consts, a 40-lowercase-hex
     `carve_commit`, the closed maps (`destinations:`, `leg_overrides:`,
     `leg_classification:`), each row's per-disposition key set, `edits[]`
     entries, and every moved row inside `moved_paths:`
     (`carve-shape-invalid`).
  2. REVISION — `carve_commit` is a COMMIT OBJECT this repository carries (not
     an annotated tag's id, which git would peel) and an ANCESTOR of the
     revision under test (`carve-revision-mismatch`). A depth-1 checkout does
     not carry it, and that refuses: an unreachable referent is unverifiable,
     whatever the reason it is unreachable.
  3. DIGEST — pass 1 at the carve commit: each moved row's mode and the sha256
     of its RAW GIT BLOB equal the row's (`carve-digest-mismatch`), its path
     exists there (`carve-path-absent`), and its declared lines exist in that
     blob (`carve-shape-invalid`). Pass 2 at the revision under test, per
     phase: under `carve` every moved row is still present and byte-for-byte
     and mode-for-mode the carve's; under `post-shed` a `shed` row is ABSENT
     (`carve-shed-incomplete` if not), a `retired_by_archive` row is absent or
     unchanged, and a `kept` moved row is not compared — the adapter rewrites
     those at the same paths.
  4. SURFACE — every `moved_paths:` entry matches a file at the carve commit
     (`carve-surface-vacuous`); no path in two rows and no two rows arriving at
     one real destination path (`carve-file-duplicated`); at the carve commit
     the rows equal the WHOLE tree (`carve-file-undeclared` /
     `carve-path-absent`); at the revision under test nothing has appeared
     under the surface (`carve-file-undeclared`) and no row under it has
     vanished (`carve-path-absent`), the shed set and an archived spec excepted
     under `post-shed`.
  5. CLOSED VOCABULARIES — `disposition`, `destination`, `edits[].class`,
     `reason`, `retained_here`, `leg_override` and `leg_default.leg`
     (`carve-vocabulary-unknown`).
  6. CONSISTENCY — dispositions against edits
     (`carve-disposition-inconsistent`), `retained_here` against the
     disposition and the path (`carve-retention-inconsistent`),
     `destination_path` against `source_path` (`carve-path-remapped`), the
     overrides against the verdicts (`carve-override-inconsistent`), and the
     rows' bytewise order (`carve-path-order-violation`).

A LINE is a `\\n`-terminated record of the raw bytes, 1-based, with a trailing
newline closing the last record rather than opening another — openxFactory's
`scripts/carve_lines.py` definition (RULED Q-L8 (c) there), which is what
`grep -n`, `sed -n` and `git diff` show and what the manifest's line numbers
were written in. It is restated in `count_lines` below rather than imported,
because nothing from openxFactory is imported here.

THE SEAT-HOLDING PASS. Given no manifest at the DEFAULT path, the checker
prints `NO MANIFEST <path> (nothing to validate)` and exits 0, as openDox's
does; a `--manifest` the caller NAMED and that is absent refuses
(`carve-unreadable`), so a typo is never indistinguishable from "not yet
written".

Exit codes:
  0  the manifest verifies, or there is no manifest at the default path
  2  ANY refusal, and any environment failure

  There is deliberately no exit 1, on openDox's reasoning: the only question is
  whether the carve may proceed, and "a digest drifted" and "the bytes could
  not be read" answer it the same way.

Run: `python3 scripts/validate-carve-manifest.py` (optionally `--at <sha>`,
`--json`). Driven on every `pytest-suite` run by
`tests/carve_manifest/test_carve_manifest.py`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs PyYAML
    print("ERROR PyYAML is required", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]

# The path `design.md` D7 and `tasks.md` 2.5 name verbatim. Relative, so
# `--repo` moves the whole question to another tree without moving the path.
MANIFEST_RELPATH = "docs/openwallet-carve-manifest.yaml"

SCHEMA_VERSION = 1
KIND = "openwallet-carve-manifest"

# openDox's three consts, borrowed in turn from openxFactory's release-digest
# inventory, so a reader of one manifest already knows how to read the other.
CONSTS: dict[str, str] = {
    "digest_algorithm": "sha256",
    "digest_source": "raw_git_blob",
    "path_order": "bytewise_utf8",
}

# design.md D7, "The edit classes are closed", in its order. Five.
EDIT_CLASSES: tuple[str, ...] = (
    "validator hunks (a)-(e)",
    "test split",
    "manifest field edits",
    "subject lines",
    "envelope-verify step",
)

PHASE_CARVE = "carve"
PHASE_POST_SHED = "post-shed"
PHASES: tuple[str, ...] = (PHASE_CARVE, PHASE_POST_SHED)

DISPOSITIONS: tuple[str, ...] = ("moved_verbatim", "moved_with_declared_edit",
                                 "not_moved")
MOVED_DISPOSITIONS: tuple[str, ...] = ("moved_verbatim",
                                       "moved_with_declared_edit")

# design.md D7, "One field openDox did not need, `retained_here`".
RETAINED_KEPT = "kept"
RETAINED_SHED = "shed"
RETAINED_RETIRED = "retired_by_archive"
RETAINED: tuple[str, ...] = (RETAINED_KEPT, RETAINED_SHED, RETAINED_RETIRED)

# Only an OpenSpec archive retires a capability spec, and a promoted spec lives
# here; a `retired_by_archive` row anywhere else is a claim no archive can keep.
RETIRABLE_PREFIX = "openspec/specs/"

# This repository's own reasons a tracked path does not travel (design.md D2
# and D7 "Stays here"). CLOSED here; the manifest declares the subset it uses.
KNOWN_NOT_MOVED_REASONS: tuple[str, ...] = (
    "stays_openxwallet_adapter",
    "stays_openxwallet_front_door",
    "stays_openxwallet_governance",
    "stays_vendored_not_carved",
)

# The legs of openRepoShape's three-leg shape, which `destinations:` names.
LEGS: tuple[str, ...] = ("code", "spec", "assembly")

# openRepoShape's classifier speaks of `root` where the shape speaks of the
# `assembly` leg, and answers `ambiguous` where it does not know. An ambiguous
# default is a departure from every leg: a human must dispose of it.
CLASSIFIER_LEGS: dict[str, str | None] = {
    "spec": "spec", "code": "code", "root": "assembly", "ambiguous": None,
}

OVERRIDE_STATUSES: tuple[str, ...] = ("ruled", "proposed")

# The refusal vocabulary, FIXED, COMPLETE and ordered by the check that raises
# it: openDox's twelve, then the three D7's manifest needs. Callers branch on
# the code; `tests/carve_manifest/test_carve_manifest.py` restates this tuple
# as a literal and scans this file's raise sites, so no code can be added,
# dropped, reordered or raised outside it in silence.
REFUSAL_CODES: tuple[str, ...] = (
    "carve-shape-invalid",
    "carve-revision-mismatch",
    "carve-digest-mismatch",
    "carve-path-absent",
    "carve-file-undeclared",
    "carve-file-duplicated",
    "carve-surface-vacuous",
    "carve-vocabulary-unknown",
    "carve-disposition-inconsistent",
    "carve-path-order-violation",
    "carve-shed-incomplete",
    "carve-unreadable",
    "carve-path-remapped",
    "carve-retention-inconsistent",
    "carve-override-inconsistent",
)

REMEDIATION = (
    "Remediation: re-cut the manifest AT the carve commit — recompute every "
    "sha256 from the real bytes (`git cat-file blob <carve_commit>:<path> | "
    "sha256sum`), never edit a digest to make this pass — or, where the tree "
    "has moved under the carve surface since, have a NEW carve commit named "
    "and recompute the whole file: a re-cut never carries digests forward. "
    "Verify at a specific revision with `--at <sha>`. Under `phase: "
    "post-shed` the remedy for `carve-shed-incomplete` is the opposite one: "
    "the manifest declares the shed done and the tree still carries the file, "
    "so the deletion and the flip must land together."
)

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
MODE_RE = re.compile(r"^(100644|100755|120000)$")
KEY_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

TOP_LEVEL_REQUIRED = frozenset({
    "schema_version", "kind", "carve_commit", "source_repository",
    "digest_algorithm", "digest_source", "path_order", "destinations",
    "edit_classes", "not_moved_reasons", "leg_classification", "leg_overrides",
    "moved_paths", "rows",
})
# `header:` is prose, `phase:` defaults to `carve`, and `carve_tag:` is a
# human label beside the commit — none was cut for this carve, so it is
# optional rather than required as in openDox.
TOP_LEVEL_OPTIONAL = frozenset({"header", "phase", "carve_tag"})
TOP_LEVEL_KEYS = TOP_LEVEL_REQUIRED | TOP_LEVEL_OPTIONAL

DESTINATION_KEYS = frozenset({"repository", "leg"})
LEG_CLASSIFICATION_KEYS = frozenset({
    "policy_repository", "policy_path", "classifier", "policy_commit",
    "policy_sha256"})
LEG_OVERRIDE_KEYS = frozenset({"status", "overrides_rule", "leg", "authority"})
LEG_DEFAULT_KEYS = frozenset({"leg", "rule"})
EDIT_KEYS = frozenset({"class", "lines", "note"})

# THE ROW GRAMMAR, PER DISPOSITION. A moved row carries its bytes' address and
# its arrival; a `not_moved` row carries why it stays, and no digest — a digest
# is the claim that bytes arrive somewhere. `edits` is grammatically legal on
# every disposition so that check 6 can name a disagreement precisely.
ROW_REQUIRED_BY_DISPOSITION: dict[str, frozenset[str]] = {
    "moved_verbatim": frozenset({
        "source_path", "disposition", "git_mode", "sha256", "destination",
        "destination_path", "retained_here", "leg_default"}),
    "moved_with_declared_edit": frozenset({
        "source_path", "disposition", "git_mode", "sha256", "destination",
        "destination_path", "retained_here", "leg_default"}),
    "not_moved": frozenset({
        "source_path", "disposition", "reason", "evidence", "retained_here"}),
}
ROW_OPTIONAL_BY_DISPOSITION: dict[str, frozenset[str]] = {
    "moved_verbatim": frozenset({"edits", "leg_override"}),
    "moved_with_declared_edit": frozenset({"edits", "leg_override"}),
    "not_moved": frozenset({"edits"}),
}
ROW_KEYS: frozenset[str] = frozenset().union(
    *ROW_REQUIRED_BY_DISPOSITION.values(),
    *ROW_OPTIONAL_BY_DISPOSITION.values())


class CarveRefusal(Exception):
    """A named, remediable refusal: a machine `code` and a human `detail`."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(code, detail)

    def render(self, manifest: Path) -> str:
        return f"FAIL {manifest}: {self.code} — {self.detail}\n{REMEDIATION}"


def _shown(items: list[str], limit: int = 10) -> str:
    return ", ".join(items[:limit]) + (" …" if len(items) > limit else "")


# --------------------------------------------------------------------------
# git
# --------------------------------------------------------------------------

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """git, capturing BYTES — blob contents must not pass through a decoder."""
    try:
        return subprocess.run(["git", "-C", str(repo), *args],
                              capture_output=True, check=False)
    except OSError as exc:  # pragma: no cover - no git on the host
        raise CarveRefusal("carve-unreadable",
                           f"git could not be run in {repo}: {exc}") from exc


def resolve_revision(repo: Path, at: str | None) -> str:
    """The revision this run asks about: `--at <sha>`, or `HEAD`."""
    ref = at if at is not None else "HEAD"
    done = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if done.returncode != 0 or not done.stdout.strip():
        if at is not None:
            raise CarveRefusal(
                "carve-revision-mismatch",
                f"--at {at!r} does not resolve to a commit in {repo}")
        raise CarveRefusal(
            "carve-unreadable",
            f"{repo} has no resolvable HEAD; the checker reads the carve "
            "commit's tree out of a real git repository")
    return done.stdout.decode("utf-8", "replace").strip()


class TreeEntry(NamedTuple):
    """One blob at one revision: its file mode and git's own object id."""

    mode: str
    oid: str


def tree_at(repo: Path, commit: str) -> dict[str, TreeEntry]:
    """`{path: TreeEntry}` for every BLOB at `commit`, from one `ls-tree`."""
    done = _git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    if done.returncode != 0:
        raise CarveRefusal(
            "carve-unreadable",
            f"`git ls-tree -r {commit[:12]}` failed in {repo}: "
            + done.stderr.decode("utf-8", "replace").strip())
    tree: dict[str, TreeEntry] = {}
    for record in done.stdout.decode("utf-8", "surrogateescape").split("\0"):
        if not record:
            continue
        meta, _, path = record.partition("\t")
        fields = meta.split(" ")
        if len(fields) != 3:  # pragma: no cover - git's format is stable
            raise CarveRefusal("carve-unreadable",
                               f"unparseable ls-tree record {record!r}")
        mode, kind, oid = fields
        if kind == "blob":
            tree[path] = TreeEntry(mode, oid)
    return tree


def blob_at(repo: Path, commit: str, path: str) -> bytes | None:
    """The RAW bytes of `path` at `commit`, or None where it is not a blob."""
    done = _git(repo, "cat-file", "blob", f"{commit}:{path}")
    if done.returncode != 0:
        return None
    return done.stdout


def count_lines(content: bytes) -> int:
    """The number of `\\n`-terminated records in `content` (see the module
    docstring): a trailing newline closes the last record and opens none, and
    empty content has no lines."""
    parts = content.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return len(parts)


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def read_manifest(path: Path) -> dict[str, Any]:
    """The manifest as a document. READING failures are `carve-unreadable`
    (no document exists); PARSING failures are `carve-shape-invalid` (a
    document defect a reviewer acts on)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise CarveRefusal("carve-unreadable",
                           f"the manifest could not be read: {exc}") from exc
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        at = (f" at line {mark.line + 1} column {mark.column + 1}"
              if mark is not None else "")
        raise CarveRefusal(
            "carve-shape-invalid",
            f"the manifest is not parseable YAML{at}: {exc}") from exc
    if not isinstance(doc, dict):
        raise CarveRefusal(
            "carve-shape-invalid",
            f"the manifest is not a mapping (parsed as {type(doc).__name__})")
    return doc


def _require_str(doc: dict, key: str, where: str) -> str:
    value = doc.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CarveRefusal(
            "carve-shape-invalid",
            f"{where} declares `{key}: {value!r}`; a non-empty string is "
            "required")
    return value


def _closed_mapping(value: Any, keys: frozenset[str], where: str,
                    required: frozenset[str] | None = None) -> dict:
    if not isinstance(value, dict):
        raise CarveRefusal("carve-shape-invalid",
                           f"{where} is not a mapping ({value!r})")
    stray = sorted(set(value) - keys, key=repr)
    if stray:
        raise CarveRefusal(
            "carve-shape-invalid",
            f"{where} carries the unknown key(s) {stray!r}; it is closed to "
            f"{sorted(keys)!r}")
    for key in sorted(required if required is not None else keys):
        if key not in value:
            raise CarveRefusal("carve-shape-invalid",
                               f"{where} lacks the required key `{key}`")
    return value


# --------------------------------------------------------------------------
# check 1 — shape
# --------------------------------------------------------------------------

def check_shape(doc: dict[str, Any]) -> None:
    """Everything answerable from the document alone, before any git call."""
    version = doc.get("schema_version")
    if (not isinstance(version, int) or isinstance(version, bool)
            or version != SCHEMA_VERSION):
        raise CarveRefusal(
            "carve-shape-invalid",
            f"`schema_version: {version!r}`; the INTEGER {SCHEMA_VERSION} only "
            "(`true` and `1.0` both equal 1 in Python)")
    if doc.get("kind") != KIND:
        raise CarveRefusal("carve-shape-invalid",
                           f"`kind: {doc.get('kind')!r}`, not {KIND!r}")
    stray = sorted(set(doc) - TOP_LEVEL_KEYS, key=repr)
    if stray:
        raise CarveRefusal(
            "carve-shape-invalid",
            f"the manifest carries the unknown top-level key(s) {stray!r}; the "
            "document grammar is closed, so a mistyped `moved_path:` refuses "
            "here rather than being ignored in silence")
    missing = sorted(TOP_LEVEL_REQUIRED - set(doc))
    if missing:
        raise CarveRefusal(
            "carve-shape-invalid",
            f"the manifest lacks the required top-level key(s) {missing!r}")
    for key, expected in CONSTS.items():
        if doc.get(key) != expected:
            raise CarveRefusal(
                "carve-shape-invalid",
                f"`{key}: {doc.get(key)!r}` is not the const {expected!r}")
    phase = doc.get("phase", PHASE_CARVE)
    if phase not in PHASES:
        raise CarveRefusal(
            "carve-shape-invalid",
            f"`phase: {phase!r}` is not one of {list(PHASES)!r}; absent means "
            f"{PHASE_CARVE!r}, and a named phase must be one this checker "
            "implements, because it decides whether a missing source path is a "
            "refusal or the declared outcome")
    commit = doc.get("carve_commit")
    if not isinstance(commit, str) or not COMMIT_RE.match(commit):
        raise CarveRefusal(
            "carve-shape-invalid",
            f"`carve_commit: {commit!r}` is not 40 lowercase hex characters; "
            "the referent is a commit, and an abbreviation, a branch or a tag "
            "is a movable name")
    if "carve_tag" in doc:
        _require_str(doc, "carve_tag", "the manifest")
    if "header" in doc:
        _require_str(doc, "header", "the manifest")
    source = _require_str(doc, "source_repository", "the manifest")
    if not REPO_RE.match(source):
        raise CarveRefusal("carve-shape-invalid",
                           f"`source_repository: {source!r}` is not `owner/name`")

    destinations = doc["destinations"]
    if not isinstance(destinations, dict) or not destinations:
        raise CarveRefusal("carve-shape-invalid",
                           f"`destinations:` is not a non-empty mapping "
                           f"({destinations!r})")
    for key, entry in destinations.items():
        if not isinstance(key, str) or not KEY_RE.match(key):
            raise CarveRefusal(
                "carve-shape-invalid",
                f"`destinations` carries the key {key!r}, which is not a "
                "lowercase label; a row's `destination` is always a string, so "
                "a key this pattern rejects can never be referenced")
        _closed_mapping(entry, DESTINATION_KEYS, f"`destinations.{key}`")
        repository = _require_str(entry, "repository", f"`destinations.{key}`")
        if not REPO_RE.match(repository):
            raise CarveRefusal(
                "carve-shape-invalid",
                f"`destinations.{key}.repository: {repository!r}` is not "
                "`owner/name`")
        if entry.get("leg") not in LEGS:
            raise CarveRefusal(
                "carve-shape-invalid",
                f"`destinations.{key}.leg: {entry.get('leg')!r}` is not one of "
                f"{list(LEGS)!r}")

    classes = doc["edit_classes"]
    if not isinstance(classes, list) or tuple(classes) != EDIT_CLASSES:
        raise CarveRefusal(
            "carve-shape-invalid",
            f"`edit_classes: {classes!r}` is not design.md D7's closed list "
            f"{list(EDIT_CLASSES)!r}, verbatim and in order")

    reasons = doc["not_moved_reasons"]
    if not isinstance(reasons, list) or not reasons:
        raise CarveRefusal("carve-shape-invalid",
                           f"`not_moved_reasons:` is not a non-empty list "
                           f"({reasons!r})")
    unknown = [r for r in reasons if r not in KNOWN_NOT_MOVED_REASONS]
    if unknown:
        raise CarveRefusal(
            "carve-shape-invalid",
            f"`not_moved_reasons:` declares {unknown!r}, which this checker "
            f"does not know; the known set is {list(KNOWN_NOT_MOVED_REASONS)!r}"
            " — declared AND known, so a file may not widen it by declaring it")

    classification = _closed_mapping(doc["leg_classification"],
                                     LEG_CLASSIFICATION_KEYS,
                                     "`leg_classification:`")
    for key in sorted(LEG_CLASSIFICATION_KEYS):
        _require_str(classification, key, "`leg_classification:`")
    if not REPO_RE.match(classification["policy_repository"]):
        raise CarveRefusal("carve-shape-invalid",
                           "`leg_classification.policy_repository` is not "
                           "`owner/name`")
    if not COMMIT_RE.match(classification["policy_commit"]):
        raise CarveRefusal("carve-shape-invalid",
                           "`leg_classification.policy_commit` is not 40 "
                           "lowercase hex characters")
    if not SHA256_RE.match(classification["policy_sha256"]):
        raise CarveRefusal("carve-shape-invalid",
                           "`leg_classification.policy_sha256` is not 64 "
                           "lowercase hex characters")

    overrides = doc["leg_overrides"]
    if not isinstance(overrides, dict) or not overrides:
        raise CarveRefusal("carve-shape-invalid",
                           f"`leg_overrides:` is not a non-empty mapping "
                           f"({overrides!r})")
    for key, entry in overrides.items():
        where = f"`leg_overrides.{key}`"
        if not isinstance(key, str) or not KEY_RE.match(key):
            raise CarveRefusal("carve-shape-invalid",
                               f"`leg_overrides` carries the key {key!r}, "
                               "which is not a lowercase label")
        _closed_mapping(entry, LEG_OVERRIDE_KEYS, where)
        for field in ("status", "overrides_rule", "leg", "authority"):
            _require_str(entry, field, where)
        if entry["status"] not in OVERRIDE_STATUSES:
            raise CarveRefusal(
                "carve-shape-invalid",
                f"{where}.status: {entry['status']!r} is not one of "
                f"{list(OVERRIDE_STATUSES)!r}; an override is RULED or it is "
                "PROPOSED, and the manifest says which")
        if entry["leg"] not in LEGS:
            raise CarveRefusal("carve-shape-invalid",
                               f"{where}.leg: {entry['leg']!r} is not one of "
                               f"{list(LEGS)!r}")

    moved_paths = doc["moved_paths"]
    if not isinstance(moved_paths, list) or not moved_paths:
        raise CarveRefusal("carve-shape-invalid",
                           f"`moved_paths:` is not a non-empty list "
                           f"({moved_paths!r})")
    for entry in moved_paths:
        if not isinstance(entry, str) or not entry.strip():
            raise CarveRefusal("carve-shape-invalid",
                               f"`moved_paths:` holds a non-path entry "
                               f"({entry!r})")

    rows = doc["rows"]
    if not isinstance(rows, list) or not rows:
        raise CarveRefusal("carve-shape-invalid",
                           f"`rows:` is not a non-empty list ({rows!r})")
    for index, row in enumerate(rows):
        _check_row_shape(index, row, moved_paths)


def _check_row_shape(index: int, row: Any, moved_paths: list[str]) -> None:
    where = f"rows[{index}]"
    if not isinstance(row, dict):
        raise CarveRefusal("carve-shape-invalid",
                           f"{where} is not a mapping ({row!r})")
    stray = sorted(set(row) - ROW_KEYS, key=repr)
    if stray:
        raise CarveRefusal(
            "carve-shape-invalid",
            f"{where} carries the unknown key(s) {stray!r}; the row grammar is "
            "closed, so a field nobody validates is a field nobody reads")
    source_path = _require_str(row, "source_path", where)
    where = f"{where} ({source_path})"
    disposition = row.get("disposition")
    if not isinstance(disposition, str) or not disposition:
        raise CarveRefusal("carve-shape-invalid",
                           f"{where} declares `disposition: {disposition!r}`")
    _require_str(row, "retained_here", where)
    if disposition not in DISPOSITIONS:
        # The vocabulary miss is check 5's to report.
        return
    allowed = (ROW_REQUIRED_BY_DISPOSITION[disposition]
               | ROW_OPTIONAL_BY_DISPOSITION[disposition])
    for key in sorted(set(row) - allowed):
        raise CarveRefusal(
            "carve-shape-invalid",
            f"{where} is `{disposition}` and carries `{key}:`. A moved row "
            "carries its bytes' address and its arrival; a `not_moved` row "
            "carries why it stays and no digest, mode or destination — those "
            "are the claim that bytes arrive somewhere")
    for key in sorted(ROW_REQUIRED_BY_DISPOSITION[disposition]):
        if key not in row:
            raise CarveRefusal("carve-shape-invalid",
                               f"{where} is `{disposition}` and lacks `{key}:`")
    if disposition in MOVED_DISPOSITIONS:
        mode = row.get("git_mode")
        if not isinstance(mode, str) or not MODE_RE.match(mode):
            raise CarveRefusal(
                "carve-shape-invalid",
                f"{where} declares `git_mode: {mode!r}`; a QUOTED git file mode "
                "is required (an unquoted 100644 parses as an int)")
        digest = row.get("sha256")
        if not isinstance(digest, str) or not SHA256_RE.match(digest):
            raise CarveRefusal(
                "carve-shape-invalid",
                f"{where} declares `sha256: {digest!r}`, which is not 64 "
                "lowercase hex characters")
        _require_str(row, "destination", where)
        _require_str(row, "destination_path", where)
        default = _closed_mapping(row.get("leg_default"), LEG_DEFAULT_KEYS,
                                  f"{where}.leg_default")
        _require_str(default, "leg", f"{where}.leg_default")
        _require_str(default, "rule", f"{where}.leg_default")
        if "leg_override" in row:
            _require_str(row, "leg_override", where)
        if not in_surface(source_path, moved_paths):
            raise CarveRefusal(
                "carve-shape-invalid",
                f"{where} is `{disposition}` and lies under no `moved_paths:` "
                "entry; the surface is what is watched at the revision under "
                "test, and a moved file outside it could change after the "
                "carve commit without any refusal")
    else:
        _require_str(row, "reason", where)
        _require_str(row, "evidence", where)
    if "edits" in row:
        _check_edits_shape(where, row["edits"])


def _check_edits_shape(where: str, edits: Any) -> None:
    if not isinstance(edits, list):
        raise CarveRefusal("carve-shape-invalid",
                           f"{where} declares `edits:` as {edits!r}; a list "
                           "is required")
    for position, edit in enumerate(edits):
        at = f"{where}.edits[{position}]"
        _closed_mapping(edit, EDIT_KEYS, at, required=frozenset({"class",
                                                                 "lines"}))
        if not isinstance(edit.get("class"), str) or not edit["class"]:
            raise CarveRefusal("carve-shape-invalid",
                               f"{at} declares `class: {edit.get('class')!r}`")
        lines = edit.get("lines")
        if not isinstance(lines, list) or not lines:
            raise CarveRefusal(
                "carve-shape-invalid",
                f"{at} declares `lines: {lines!r}`; at least one line number at "
                "the carve commit is required, or `moved_with_declared_edit` "
                "is only a label")
        for line in lines:
            if not isinstance(line, int) or isinstance(line, bool) or line < 1:
                raise CarveRefusal(
                    "carve-shape-invalid",
                    f"{at} declares the line {line!r}; line numbers are "
                    "positive integers")
        if "note" in edit and (not isinstance(edit["note"], str)
                               or not edit["note"].strip()):
            raise CarveRefusal("carve-shape-invalid",
                               f"{at} declares `note: {edit['note']!r}`; a "
                               "note is prose or it is absent")


def in_surface(path: str, moved_paths: list[str]) -> bool:
    """Is `path` one of the entries, or under one? Segment-aware, so
    `openspec/specs/openxwallet` does not swallow
    `openspec/specs/openxwallet-agent-profile/spec.md`."""
    for entry in moved_paths:
        prefix = entry.rstrip("/")
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


# --------------------------------------------------------------------------
# check 2 — revision
# --------------------------------------------------------------------------

def check_revision(repo: Path, doc: dict, at: str | None) -> str:
    """The revision under test, returned; `carve_commit` must be a commit
    object this repository carries and an ANCESTOR of it."""
    resolved = resolve_revision(repo, at)
    carve_commit = doc["carve_commit"]
    asked = f"--at {at}" if at is not None else "HEAD"
    known = _git(repo, "rev-parse", "--verify", "--quiet",
                 f"{carve_commit}^{{commit}}")
    peeled = known.stdout.decode("utf-8", "replace").strip()
    if known.returncode != 0 or not peeled:
        raise CarveRefusal(
            "carve-revision-mismatch",
            f"the manifest names carve_commit {carve_commit}, which {repo} "
            "DOES NOT CARRY as a commit. Whether the commit is wrong or the "
            "checkout is too shallow to reach it (a depth-1 `actions/checkout` "
            "is), a digest taken at a commit this repository cannot resolve is "
            "unverifiable here")
    if peeled != carve_commit:
        raise CarveRefusal(
            "carve-revision-mismatch",
            f"carve_commit {carve_commit} is not a COMMIT object in {repo}: it "
            f"PEELS to {peeled}. A 40-hex id that must be peeled to reach a "
            "commit is an annotated tag, and a tag is a label, never the "
            f"referent. Record the commit id itself: {peeled}")
    ancestor = _git(repo, "merge-base", "--is-ancestor", carve_commit, resolved)
    if ancestor.returncode != 0:
        raise CarveRefusal(
            "carve-revision-mismatch",
            f"carve_commit {carve_commit[:12]} is NOT AN ANCESTOR of {asked} "
            f"({resolved}); every comparison below would measure two unrelated "
            "histories against each other. Verify the carve's own line with "
            f"`--at {carve_commit[:12]}`")
    return resolved


# --------------------------------------------------------------------------
# check 3 — digests
# --------------------------------------------------------------------------

def check_digests(repo: Path, doc: dict, referent: dict[str, TreeEntry],
                  tested: dict[str, TreeEntry], verified_at: str,
                  phase: str) -> int:
    """Pass 1 at the carve commit, then pass 2 at the revision under test.

    Two passes rather than one row loop, because the ORDER between the two
    kinds of finding is itself a finding (openDox's reasoning): a manifest that
    lies about its own referent is a document defect, and it is reported even
    when some other row also moved on `main` afterwards.
    """
    commit = doc["carve_commit"]
    recomputed = 0
    for index, row in enumerate(doc["rows"]):
        if row.get("disposition") not in MOVED_DISPOSITIONS:
            continue
        path = row["source_path"]
        if path not in referent:
            raise CarveRefusal(
                "carve-path-absent",
                f"rows[{index}] records a sha256 for {path}, which "
                f"{doc['source_repository']}@{commit[:12]} does not carry as a "
                "file; a digest of nothing is not a digest")
        if referent[path].mode != row["git_mode"]:
            raise CarveRefusal(
                "carve-digest-mismatch",
                f"{path}: MODE DRIFT — the manifest records git_mode "
                f"{row['git_mode']} and the tree at {commit[:12]} carries "
                f"{referent[path].mode}")
        content = blob_at(repo, commit, path)
        if content is None:  # pragma: no cover - ls-tree already said blob
            raise CarveRefusal("carve-path-absent",
                               f"{path} could not be read as a blob at "
                               f"{commit[:12]}")
        actual = hashlib.sha256(content).hexdigest()
        recomputed += 1
        if actual != row["sha256"]:
            raise CarveRefusal(
                "carve-digest-mismatch",
                f"{path}: DIGEST DRIFT\n"
                f"  recorded   {row['sha256']}\n"
                f"  recomputed {actual}\n"
                f"the bytes at {commit[:12]} are not the bytes this row "
                "promises the destination")
        total = count_lines(content)
        for position, edit in enumerate(row.get("edits") or []):
            for line in edit["lines"]:
                if line > total:
                    raise CarveRefusal(
                        "carve-shape-invalid",
                        f"rows[{index}].edits[{position}] ({path}) names line "
                        f"{line}, and the blob at {commit[:12]} has {total} "
                        "line(s); a declared edit at a line the file does not "
                        "have cannot be checked at the destination")

    for index, row in enumerate(doc["rows"]):
        if row.get("disposition") not in MOVED_DISPOSITIONS:
            continue
        path = row["source_path"]
        retained = row.get("retained_here")
        if phase == PHASE_POST_SHED:
            if retained == RETAINED_SHED:
                if path in tested:
                    raise CarveRefusal(
                        "carve-shed-incomplete",
                        f"{path}: STILL PRESENT UNDER A POST-SHED MANIFEST — "
                        f"rows[{index}] declares it `retained_here: shed`, the "
                        f"manifest declares `phase: {PHASE_POST_SHED}`, and "
                        f"{verified_at[:12]} still carries it. Either this "
                        "commit is missing the deletion, or the phase was "
                        "flipped ahead of the shed")
                continue
            if retained == RETAINED_RETIRED:
                if path not in tested:
                    continue
            else:
                # A `kept` moved row: the adapter rebuild rewrites these at the
                # same path (the validator, the syntax-gate entrypoint, the
                # manifest, the CHANGELOG, the workflows), so after the shed
                # they are this repository's again. Presence is check 4's.
                continue
        if path not in tested:
            raise CarveRefusal(
                "carve-path-absent",
                f"{path}: DELETED SINCE THE CARVE — rows[{index}] declares it "
                f"`{row['disposition']}` at {commit[:12]}, and "
                f"{verified_at[:12]} no longer carries it. A source the tree "
                "has dropped is a move nobody can review at the destination: "
                "have a new carve commit named, or — if this is the adapter "
                f"rebuild's shed — declare `phase: {PHASE_POST_SHED}` in the "
                "SAME commit")
        if tested[path].mode != referent[path].mode:
            raise CarveRefusal(
                "carve-digest-mismatch",
                f"{path}: MODE DRIFT SINCE THE CARVE — {row['git_mode']} at "
                f"{commit[:12]}, {tested[path].mode} at {verified_at[:12]}")
        if tested[path].oid == referent[path].oid:
            continue
        content = blob_at(repo, verified_at, path)
        moved_to = (hashlib.sha256(content).hexdigest()
                    if content is not None else "<unreadable>")
        raise CarveRefusal(
            "carve-digest-mismatch",
            f"{path}: CHANGED SINCE THE CARVE\n"
            f"  at carve_commit {commit[:12]}  {row['sha256']}\n"
            f"  at {verified_at[:12]}              {moved_to}\n"
            "the carve ships the bytes at the carve commit, so an edit made on "
            "`main` since is an edit the destination never receives")
    return recomputed


# --------------------------------------------------------------------------
# check 4 — surface and completeness
# --------------------------------------------------------------------------

def check_surface(doc: dict, referent: dict[str, TreeEntry],
                  tested: dict[str, TreeEntry], verified_at: str,
                  phase: str) -> int:
    """The rows equal the WHOLE tree at the carve commit; the watched surface
    has neither grown nor lost a row's file at the revision under test."""
    commit = doc["carve_commit"]
    destinations = doc["destinations"]
    moved_paths = doc["moved_paths"]

    for entry in moved_paths:
        if not any(in_surface(path, [entry]) for path in referent):
            raise CarveRefusal(
                "carve-surface-vacuous",
                f"`moved_paths:` declares {entry!r}, which matches NO file at "
                f"{commit[:12]}; a dead entry reads as coverage and watches "
                "nothing")

    seen: dict[str, int] = {}
    for index, row in enumerate(doc["rows"]):
        path = row["source_path"]
        if path in seen:
            raise CarveRefusal(
                "carve-file-duplicated",
                f"{path} appears in rows[{seen[path]}] AND rows[{index}]; a "
                "tracked path has exactly one row")
        seen[path] = index

    arrivals: dict[tuple[str, ...], int] = {}
    for index, row in enumerate(doc["rows"]):
        if row.get("disposition") not in MOVED_DISPOSITIONS:
            continue
        entry = destinations.get(row["destination"])
        if entry is not None:
            arrival: tuple[str, ...] = (entry["repository"], entry["leg"],
                                        row["destination_path"])
            where = f"{entry['repository']} ({entry['leg']})"
        else:
            arrival = (row["destination"],)
            where = row["destination"]
        if arrival in arrivals:
            raise CarveRefusal(
                "carve-file-duplicated",
                f"rows[{arrivals[arrival]}] AND rows[{index}] both send a file "
                f"to {where}:{row['destination_path']}; one would overwrite "
                "the other and the manifest does not say which")
        arrivals[arrival] = index

    tree = set(referent)
    undeclared = sorted(tree - set(seen))
    if undeclared:
        raise CarveRefusal(
            "carve-file-undeclared",
            f"the carve commit {commit[:12]} tracks {len(undeclared)} path(s) "
            f"that NO row declares: {_shown(undeclared)} — design.md D7: a "
            "tracked path in no row REFUSES")
    absent = sorted(set(seen) - tree)
    if absent:
        raise CarveRefusal(
            "carve-path-absent",
            f"the manifest declares {len(absent)} row(s) for path(s) the carve "
            f"commit {commit[:12]} does not track: {_shown(absent)}")

    surface = {p for p in referent if in_surface(p, moved_paths)}
    tested_surface = {p for p in tested if in_surface(p, moved_paths)}
    appeared = sorted(tested_surface - surface)
    if appeared:
        raise CarveRefusal(
            "carve-file-undeclared",
            f"{len(appeared)} file(s) have APPEARED under the carve surface "
            f"since {commit[:12]} and no row declares them at "
            f"{verified_at[:12]}: {_shown(appeared)} — the carve takes the "
            "tree at the carve commit, so a file added here since would never "
            "reach its destination")

    excused: set[str] = set()
    if phase == PHASE_POST_SHED:
        excused = {row["source_path"] for row in doc["rows"]
                   if row.get("retained_here") in (RETAINED_SHED,
                                                   RETAINED_RETIRED)}
    vanished = sorted((surface - tested_surface) - excused)
    if vanished:
        raise CarveRefusal(
            "carve-path-absent",
            f"{len(vanished)} row(s) under the carve surface name path(s) "
            f"DELETED SINCE THE CARVE — present at {commit[:12]}, absent at "
            f"{verified_at[:12]}: {_shown(vanished)}. Check 3 reports a moved "
            "row with its digest; this is what reports a `not_moved` row the "
            "surface holds, and, under `post-shed`, a `kept` moved row")
    return len(tree)


# --------------------------------------------------------------------------
# check 5 — closed vocabularies
# --------------------------------------------------------------------------

def check_vocabularies(doc: dict) -> None:
    destinations = doc["destinations"]
    declared_reasons = doc["not_moved_reasons"]
    overrides = doc["leg_overrides"]
    for index, row in enumerate(doc["rows"]):
        where = f"rows[{index}] ({row['source_path']})"
        if row["disposition"] not in DISPOSITIONS:
            raise CarveRefusal(
                "carve-vocabulary-unknown",
                f"{where} declares `disposition: {row['disposition']!r}`; the "
                f"list is CLOSED at {list(DISPOSITIONS)!r}")
        if row["retained_here"] not in RETAINED:
            raise CarveRefusal(
                "carve-vocabulary-unknown",
                f"{where} declares `retained_here: {row['retained_here']!r}`; "
                f"the list is CLOSED at {list(RETAINED)!r} (design.md D7)")
        destination = row.get("destination")
        if destination is not None and destination not in destinations:
            raise CarveRefusal(
                "carve-vocabulary-unknown",
                f"{where} declares `destination: {destination!r}`, which is "
                f"not a key of `destinations:` ({sorted(destinations)!r})")
        for position, edit in enumerate(row.get("edits") or []):
            if edit["class"] not in EDIT_CLASSES:
                raise CarveRefusal(
                    "carve-vocabulary-unknown",
                    f"{where}.edits[{position}] declares `class: "
                    f"{edit['class']!r}`, which is not one of "
                    f"{list(EDIT_CLASSES)!r}; an edit in no class is an "
                    "undeclared movement")
        reason = row.get("reason")
        if reason is not None and reason not in declared_reasons:
            raise CarveRefusal(
                "carve-vocabulary-unknown",
                f"{where} declares `reason: {reason!r}`, which the manifest's "
                f"own `not_moved_reasons:` ({list(declared_reasons)!r}) does "
                "not carry")
        default = row.get("leg_default")
        if default is not None and default["leg"] not in CLASSIFIER_LEGS:
            raise CarveRefusal(
                "carve-vocabulary-unknown",
                f"{where} declares `leg_default.leg: {default['leg']!r}`; "
                "openRepoShape's classifier answers one of "
                f"{sorted(CLASSIFIER_LEGS)!r}")
        override = row.get("leg_override")
        if override is not None and override not in overrides:
            raise CarveRefusal(
                "carve-vocabulary-unknown",
                f"{where} declares `leg_override: {override!r}`, which is not "
                f"a key of `leg_overrides:` ({sorted(overrides)!r})")


# --------------------------------------------------------------------------
# check 6 — consistency
# --------------------------------------------------------------------------

def check_consistency(doc: dict) -> None:
    destinations = doc["destinations"]
    overrides = doc["leg_overrides"]
    for index, row in enumerate(doc["rows"]):
        path = row["source_path"]
        where = f"rows[{index}] ({path})"
        disposition = row["disposition"]
        edits = row.get("edits") or []
        retained = row["retained_here"]
        if disposition == "moved_with_declared_edit" and not edits:
            raise CarveRefusal(
                "carve-disposition-inconsistent",
                f"{where} is `moved_with_declared_edit` with no `edits:`; that "
                "is `moved_verbatim` mislabelled")
        if disposition == "moved_verbatim" and edits:
            raise CarveRefusal(
                "carve-disposition-inconsistent",
                f"{where} is `moved_verbatim` and declares {len(edits)} "
                "edit(s); verbatim means the destination's bytes equal this "
                "digest")
        if disposition == "not_moved" and edits:
            raise CarveRefusal(
                "carve-disposition-inconsistent",
                f"{where} is `not_moved` and declares {len(edits)} edit(s); a "
                "file that arrives nowhere takes no carve edit")

        if disposition == "not_moved" and retained != RETAINED_KEPT:
            raise CarveRefusal(
                "carve-retention-inconsistent",
                f"{where} is `not_moved` and declares `retained_here: "
                f"{retained}`; a file that does not travel and then left this "
                "repository would be lost, so a `not_moved` row is `kept`")
        if retained == RETAINED_RETIRED and not path.startswith(
                RETIRABLE_PREFIX):
            raise CarveRefusal(
                "carve-retention-inconsistent",
                f"{where} declares `retained_here: {RETAINED_RETIRED}` outside "
                f"`{RETIRABLE_PREFIX}`; only an OpenSpec archive retires a "
                "capability spec, and a promoted spec lives there")

        if disposition not in MOVED_DISPOSITIONS:
            continue
        if row["destination_path"] != path:
            raise CarveRefusal(
                "carve-path-remapped",
                f"{where} arrives at `{row['destination_path']}`; design.md D7 "
                "keeps every carved path's repository-relative path inside its "
                "leg, which is what keeps the carve a pure copy per leg")

        dest_leg = destinations[row["destination"]]["leg"]
        default = row["leg_default"]
        default_leg = CLASSIFIER_LEGS[default["leg"]]
        override_key = row.get("leg_override")
        if default_leg == dest_leg:
            if override_key is not None:
                raise CarveRefusal(
                    "carve-override-inconsistent",
                    f"{where} names `leg_override: {override_key}` but goes to "
                    f"the `{dest_leg}` leg, which is the classifier's own "
                    f"default ({default['rule']}); nothing is overridden")
            continue
        if override_key is None:
            raise CarveRefusal(
                "carve-override-inconsistent",
                f"{where} goes to the `{dest_leg}` leg and the classifier's "
                f"default is `{default['leg']}` under `{default['rule']}`, and "
                "the row names no `leg_override:`. design.md D7: a departure "
                "from the default is DECLARED, with its authority, not implied")
        entry = overrides[override_key]
        if entry["leg"] != dest_leg:
            raise CarveRefusal(
                "carve-override-inconsistent",
                f"{where} goes to the `{dest_leg}` leg under "
                f"`leg_override: {override_key}`, which authorizes the "
                f"`{entry['leg']}` leg")
        if entry["overrides_rule"] != default["rule"]:
            raise CarveRefusal(
                "carve-override-inconsistent",
                f"{where} departs from `{default['rule']}`, and "
                f"`leg_override: {override_key}` overrides "
                f"`{entry['overrides_rule']}`")

    paths = [row["source_path"] for row in doc["rows"]]
    ordered = sorted(paths, key=lambda p: p.encode("utf-8", "surrogateescape"))
    if paths != ordered:
        first = next(i for i, (a, b) in enumerate(zip(paths, ordered))
                     if a != b)
        raise CarveRefusal(
            "carve-path-order-violation",
            f"the rows are not in `path_order: bytewise_utf8`; rows[{first}] "
            f"is {paths[first]!r} where the order puts {ordered[first]!r}")


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------

def _tally(rows: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        if value is not None:
            out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def validate(manifest_path: Path, repo: Path, at: str | None) -> dict[str, Any]:
    """The six checks in order, first failure wins."""
    doc = read_manifest(manifest_path)
    check_shape(doc)
    phase = doc.get("phase", PHASE_CARVE)
    verified_at = check_revision(repo, doc, at)
    commit = doc["carve_commit"]
    referent = tree_at(repo, commit)
    tested = referent if verified_at == commit else tree_at(repo, verified_at)
    recomputed = check_digests(repo, doc, referent, tested, verified_at, phase)
    tracked = check_surface(doc, referent, tested, verified_at, phase)
    check_vocabularies(doc)
    check_consistency(doc)

    rows = doc["rows"]
    overrides = _tally(rows, "leg_override")
    return {
        "result": "ok",
        "manifest": str(manifest_path),
        "phase": phase,
        "carve_commit": commit,
        "verified_at": verified_at,
        "source_repository": doc["source_repository"],
        "rows": len(rows),
        "tracked_paths": tracked,
        "dispositions": {d: sum(1 for r in rows if r["disposition"] == d)
                         for d in DISPOSITIONS},
        "destinations": _tally(rows, "destination"),
        "retained_here": {v: sum(1 for r in rows if r["retained_here"] == v)
                          for v in RETAINED},
        "leg_overrides": {key: {"rows": overrides.get(key, 0),
                                "status": doc["leg_overrides"][key]["status"]}
                          for key in sorted(doc["leg_overrides"])},
        "digests_recomputed": recomputed,
        "edited_rows": sum(1 for r in rows if r.get("edits")),
        "declared_lines": sum(len(e["lines"]) for r in rows
                              for e in r.get("edits") or []),
    }


def _human(summary: dict[str, Any], manifest_path: Path) -> str:
    counts = summary["dispositions"]
    where = (f"{summary['source_repository']}@{summary['carve_commit'][:12]}")
    if summary["verified_at"] != summary["carve_commit"]:
        where += f", verified at {summary['verified_at'][:12]}"
    destinations = ", ".join(f"{k} {v}"
                             for k, v in summary["destinations"].items())
    retained = ", ".join(f"{k} {v}" for k, v in summary["retained_here"].items())
    overrides = ", ".join(f"{k} {v['rows']} ({v['status']})"
                          for k, v in summary["leg_overrides"].items())
    return (f"OK {manifest_path}: phase {summary['phase']}, "
            f"{summary['rows']} row(s) at {where} — "
            f"{counts['moved_verbatim']} moved_verbatim, "
            f"{counts['moved_with_declared_edit']} moved_with_declared_edit, "
            f"{counts['not_moved']} not_moved; destinations: {destinations}; "
            f"retained_here: {retained}; leg overrides: {overrides}; "
            f"{summary['digests_recomputed']} digest(s) recomputed; "
            f"{summary['declared_lines']} declared edit line(s) on "
            f"{summary['edited_rows']} row(s); "
            f"{summary['tracked_paths']} tracked path(s) at the carve commit, "
            "each in exactly one row")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate-carve-manifest.py",
        description=("Verify docs/openwallet-carve-manifest.yaml — the "
                     "declared path mapping of the openWallet carve "
                     "(split-openwallet-neutral-core, design.md D7)."))
    parser.add_argument(
        "--manifest", metavar="PATH", default=None,
        help=f"the manifest to verify (default: <repo>/{MANIFEST_RELPATH})")
    parser.add_argument(
        "--repo", metavar="DIR", default=None,
        help="the git repository the digests are taken in (default: this one)")
    parser.add_argument(
        "--at", metavar="SHA", default=None,
        help=("verify against this revision instead of HEAD; the manifest's "
              "carve_commit must be an ANCESTOR of it"))
    parser.add_argument(
        "--json", action="store_true",
        help="print one JSON object on stdout instead of the human line")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve() if args.repo else ROOT
    if args.manifest:
        manifest_arg = Path(args.manifest)
        manifest_path = (manifest_arg if manifest_arg.is_absolute()
                         else repo / manifest_arg).resolve()
    else:
        manifest_path = (repo / MANIFEST_RELPATH).resolve()

    if args.manifest is None and not manifest_path.is_file():
        if args.json:
            print(json.dumps({"result": "no-manifest",
                              "manifest": str(manifest_path)}))
        else:
            print(f"NO MANIFEST {manifest_path} (nothing to validate)")
        return 0

    try:
        if not manifest_path.is_file():
            raise CarveRefusal(
                "carve-unreadable",
                f"--manifest {args.manifest!r} names {manifest_path}, which is "
                "not a file; the seat-holding pass covers the DEFAULT path "
                "only, so a typo is never indistinguishable from `not yet "
                "written`")
        summary = validate(manifest_path, repo, args.at)
    except CarveRefusal as exc:
        if args.json:
            print(json.dumps({"result": "refused", "code": exc.code,
                              "detail": exc.detail,
                              "manifest": str(manifest_path)}))
        else:
            print(exc.render(manifest_path), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary))
    else:
        print(_human(summary, manifest_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
