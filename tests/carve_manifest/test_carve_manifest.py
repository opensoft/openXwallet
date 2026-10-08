"""`scripts/validate-carve-manifest.py` — every refusal code pinned by a test
that can only pass if that check runs, plus the real manifest's seat.

Shaped on openxFactory's `tests/carve_manifest/test_carve_manifest.py`, the
test of the checker this one mirrors.

WHY A THROWAWAY REPOSITORY. Every refusal is a disagreement between a manifest
and a git tree, and manufacturing one against this repository would mean
editing the repository under the test. So each case builds a fresh repository
under `tmp_path`, commits a handful of files, and GENERATES a manifest from
that tree, so the clean case is clean by construction and every refusal is one
deliberate mutation away from it.

THE SCRIPT IS RUN AS A SUBPROCESS, the way CI and a reader invoke it, so the
exit codes and the printed lines are what is under test. The module is also
loaded by path once, for the constant assertions.

THE REAL-REPOSITORY SEAT BRANCHES ON THE HISTORY IT IS GIVEN, and never skips.
`pytest-suite` checks out at depth 1, which does not carry the carve commit,
so there the seat asserts that the checker REFUSES `carve-revision-mismatch`
naming that commit — fail-closed, never a green run that read nothing. Where
the history is present it asserts the full verdict. A second test reads the
real manifest as a document, with no git at all, so the ruled carve commit and
D7's counts are held on every run, whatever the checkout depth.

Hermetic: no network; git runs with an empty global config and no system
config, and with a repository-local identity.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "validate-carve-manifest.py"

# The named carve commit (`split-openwallet-neutral-core` task 2.3; Brett Heap,
# 2026-10-08, "name 90111df as the carve commit, do 2.4 and 2.5").
CARVE_COMMIT = "90111df262d6f54f7e82651d860adc12345f83f4"

# The vocabulary, restated as a LITERAL: asserting the module's tuple against
# itself would be a tautology, and other code branches by code.
RATIFIED_CODES = (
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

# design.md D7, "The edit classes are closed".
D7_EDIT_CLASSES = ["validator hunks (a)-(e)", "test split",
                   "manifest field edits", "subject lines",
                   "envelope-verify step"]


def _load():
    spec = importlib.util.spec_from_file_location("validate_carve_manifest",
                                                  SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load()


@pytest.fixture(autouse=True)
def _hermetic_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "carve-manifest-test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "carve-test@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "carve-manifest-test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "carve-test@example.invalid")


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    done = subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, check=False)
    assert done.returncode == 0, \
        f"git {' '.join(args)} in {root} failed: {done.stderr}"
    return done


def _write(repo: Path, rel: str, text: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------
# the scratch repository and its placement table
# --------------------------------------------------------------------------

# path -> (content, placement). A placement is either
#   ("moved", destination, retained_here, (classifier leg, rule), override|None,
#    edits|None)
# or ("stays", reason, evidence).
FILES: dict[str, tuple[str, tuple]] = {
    "LICENSE": ("Apache-2.0\n", (
        "moved", "openwallet_root", "kept", ("root", "root-front-door"), None,
        None)),
    "README.md": ("# front door\n", (
        "stays", "stays_openxwallet_front_door", "this repository's own")),
    "contracts/fam/examples/negative/stays.yaml": ("x: 1\n", (
        "stays", "stays_openxwallet_adapter",
        "an adapter negative that stays at its path")),
    "contracts/fam/schema.yaml": ("type: object\n", (
        "moved", "openwallet_code", "shed", ("spec", "spec-governance"),
        "q7-code-leg", None)),
    "contracts/manifest.yaml": ("kind: contract_manifest\n", (
        "moved", "openwallet_root", "kept", ("spec", "spec-governance"),
        "d7-root-release-identity", None)),
    "docs/outside.md": ("# a record that stays\n", (
        "stays", "stays_openxwallet_governance", "a record that stays")),
    "openspec/changes/travel/proposal.md": ("# travelling change\n", (
        "moved", "openwallet_spec", "shed", ("spec", "spec-governance"), None,
        None)),
    "openspec/specs/cap/spec.md": ("openXwallet SHALL hold.\nmore\n", (
        "moved", "openwallet_spec", "retired_by_archive",
        ("spec", "spec-governance"), None,
        [{"class": "subject lines", "lines": [1]}])),
    "scripts/adapter_only.py": ("ADAPTER = 1\n", (
        "stays", "stays_openxwallet_adapter", "the adapter's own reader")),
    "scripts/core.py": ("import envelope\nA = 1\nB = 2\n", (
        "moved", "openwallet_code", "kept", ("code", "code-source-and-tests"),
        None, [{"class": "validator hunks (a)-(e)", "lines": [1],
                "note": "the envelope import leaves the core"}])),
}

MOVED_PATHS = ["LICENSE", "contracts/fam/", "contracts/manifest.yaml",
               "openspec/changes/travel/", "openspec/specs/cap/",
               "scripts/core.py"]


class Scratch:
    """A throwaway repository: the CARVE commit holds every file in `FILES`;
    HEAD adds one file outside the carve surface, so a default run verifies at
    a descendant of the carve commit, the way a pull request does."""

    def __init__(self, repo: Path, carve: str, head: str) -> None:
        self.repo = repo
        self.carve = carve
        self.head = head

    def manifest_path(self) -> Path:
        return self.repo / MODULE.MANIFEST_RELPATH

    def write(self, doc: dict[str, Any]) -> Path:
        path = self.manifest_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
        return path

    def modes(self, commit: str) -> dict[str, str]:
        out: dict[str, str] = {}
        listing = _git(self.repo, "ls-tree", "-r", "--full-tree", commit).stdout
        for record in listing.splitlines():
            meta, _, path = record.partition("\t")
            mode, kind, _oid = meta.split(" ")
            if kind == "blob":
                out[path] = mode
        return out

    def digest(self, commit: str, path: str) -> str:
        raw = subprocess.run(
            ["git", "-C", str(self.repo), "cat-file", "blob",
             f"{commit}:{path}"], capture_output=True, check=True).stdout
        return hashlib.sha256(raw).hexdigest()

    def commit(self, message: str, *pathspecs: str) -> str:
        """`main` moves on. EXPLICIT pathspecs, never `add -A`: the manifest
        is written into this tree's `docs/` and must stay untracked."""
        if pathspecs:
            _git(self.repo, "add", "--", *pathspecs)
        _git(self.repo, "commit", "-q", "-m", message)
        return _git(self.repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def scratch(tmp_path: Path) -> Scratch:
    repo = tmp_path / "scratch"
    repo.mkdir()
    _git(tmp_path, "init", "-q", "-b", "main", str(repo))
    for rel, (content, _placement) in FILES.items():
        _write(repo, rel, content)
    _git(repo, "add", "--", *FILES)
    _git(repo, "commit", "-q", "-m", "the carve commit")
    carve = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _write(repo, "docs/after-the-carve.md", "# grown outside the surface\n")
    _git(repo, "add", "--", "docs/after-the-carve.md")
    _git(repo, "commit", "-q", "-m", "main moves on, outside the surface")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return Scratch(repo, carve, head)


def clean_manifest(scratch: Scratch) -> dict[str, Any]:
    """A manifest that verifies, generated from the carve commit's tree."""
    modes = scratch.modes(scratch.carve)
    assert sorted(modes) == sorted(FILES), modes
    rows: list[dict[str, Any]] = []
    for path in sorted(FILES, key=lambda p: p.encode("utf-8")):
        placement = FILES[path][1]
        if placement[0] == "stays":
            rows.append({"source_path": path, "disposition": "not_moved",
                         "reason": placement[1], "evidence": placement[2],
                         "retained_here": "kept"})
            continue
        _, destination, retained, (leg, rule), override, edits = placement
        row: dict[str, Any] = {
            "source_path": path,
            "disposition": ("moved_with_declared_edit" if edits
                            else "moved_verbatim"),
            "git_mode": modes[path],
            "sha256": scratch.digest(scratch.carve, path),
            "destination": destination,
            "destination_path": path,
            "retained_here": retained,
            "leg_default": {"leg": leg, "rule": rule},
        }
        if override:
            row["leg_override"] = override
        if edits:
            row["edits"] = copy.deepcopy(edits)
        rows.append(row)
    return {
        "schema_version": 1,
        "kind": "openwallet-carve-manifest",
        "phase": "carve",
        "header": "a generated manifest for a scratch repository",
        "carve_commit": scratch.carve,
        "source_repository": "opensoft/openXwallet",
        "digest_algorithm": "sha256",
        "digest_source": "raw_git_blob",
        "path_order": "bytewise_utf8",
        "destinations": {
            "openwallet_code": {"repository": "opensoft/openWallet-code",
                                "leg": "code"},
            "openwallet_root": {"repository": "opensoft/openWallet",
                                "leg": "assembly"},
            "openwallet_spec": {"repository": "opensoft/openWallet-spec",
                                "leg": "spec"},
        },
        "edit_classes": list(D7_EDIT_CLASSES),
        "not_moved_reasons": ["stays_openxwallet_adapter",
                              "stays_openxwallet_front_door",
                              "stays_openxwallet_governance"],
        "leg_classification": {
            "policy_repository": "opensoft/openRepoShape",
            "policy_path": "contracts/path-classification.yaml",
            "classifier": "scripts/path_classify.py",
            "policy_commit": "7f84ca42ca86a8902928345109d2bf6bad87bd91",
            "policy_sha256": "0" * 64,
        },
        "leg_overrides": {
            "q7-code-leg": {"status": "ruled",
                            "overrides_rule": "spec-governance", "leg": "code",
                            "authority": "RULED Q7"},
            "d7-root-release-identity": {
                "status": "proposed", "overrides_rule": "spec-governance",
                "leg": "assembly", "authority": "PROPOSED in design.md D7"},
        },
        "moved_paths": list(MOVED_PATHS),
        "rows": rows,
    }


def row_named(doc: dict[str, Any], path: str) -> dict[str, Any]:
    for row in doc["rows"]:
        if row["source_path"] == path:
            return row
    raise AssertionError(f"no row for {path}")


def run(scratch: Scratch, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(scratch.repo), *args],
        capture_output=True, text=True, check=False)


def verifies(scratch: Scratch, doc: dict[str, Any], *args: str) -> str:
    scratch.write(doc)
    done = run(scratch, *args)
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.startswith("OK "), done.stdout
    return done.stdout


def refuses(scratch: Scratch, doc: dict[str, Any], code: str,
            *args: str) -> str:
    """Write `doc`, run the checker, and assert exactly `code`."""
    scratch.write(doc)
    done = run(scratch, *args)
    combined = done.stdout + done.stderr
    assert done.returncode == 2, combined
    assert f": {code} —" in combined, combined
    assert "Remediation:" in combined, combined
    return combined


# --------------------------------------------------------------------------
# the constants
# --------------------------------------------------------------------------

def test_the_refusal_vocabulary_is_the_ratified_list() -> None:
    assert MODULE.REFUSAL_CODES == RATIFIED_CODES


def test_every_code_the_checker_can_emit_is_in_the_vocabulary() -> None:
    """The closure, scanned from the script's own raise sites with `ast`: no
    code raised but unlisted, and none listed but never raised."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"), filename=str(SCRIPT))
    raised: set[str] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "CarveRefusal"):
            continue
        first = node.args[0] if node.args else None
        assert (isinstance(first, ast.Constant)
                and isinstance(first.value, str)), (
            f"{SCRIPT}:{node.lineno}: a CarveRefusal(...) call does not open "
            "with a string-literal code")
        raised.add(first.value)
    assert len(raised) > 5, raised
    assert sorted(raised) == sorted(MODULE.REFUSAL_CODES)


def test_the_edit_classes_are_design_d7s_five() -> None:
    assert list(MODULE.EDIT_CLASSES) == D7_EDIT_CLASSES
    assert list(MODULE.DISPOSITIONS) == [
        "moved_verbatim", "moved_with_declared_edit", "not_moved"]
    assert list(MODULE.RETAINED) == ["kept", "shed", "retired_by_archive"]
    assert list(MODULE.PHASES) == ["carve", "post-shed"]


def test_the_manifest_path_is_the_packets() -> None:
    """design.md D7 and tasks.md 2.5 name the path verbatim."""
    assert MODULE.MANIFEST_RELPATH == "docs/openwallet-carve-manifest.yaml"


# --------------------------------------------------------------------------
# the clean pass, the absent manifest, JSON
# --------------------------------------------------------------------------

def test_a_generated_manifest_verifies(scratch: Scratch) -> None:
    out = verifies(scratch, clean_manifest(scratch))
    assert "phase carve," in out, out
    assert f"verified at {scratch.head[:12]}" in out, out
    assert ("4 moved_verbatim, 2 moved_with_declared_edit, 4 not_moved"
            in out), out
    assert ("destinations: openwallet_code 2, openwallet_root 2, "
            "openwallet_spec 2") in out, out
    assert "retained_here: kept 7, shed 2, retired_by_archive 1" in out, out
    assert ("leg overrides: d7-root-release-identity 1 (proposed), "
            "q7-code-leg 1 (ruled)") in out, out
    assert "6 digest(s) recomputed" in out, out
    assert "10 tracked path(s) at the carve commit, each in exactly one row" \
        in out, out


def test_at_the_carve_commit_itself_verifies(scratch: Scratch) -> None:
    out = verifies(scratch, clean_manifest(scratch), "--at", scratch.carve)
    assert "verified at" not in out, out


def test_an_absent_manifest_is_not_a_refusal(scratch: Scratch) -> None:
    done = run(scratch)
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.startswith("NO MANIFEST "), done.stdout


def test_a_named_manifest_that_does_not_exist_refuses(
        scratch: Scratch) -> None:
    done = run(scratch, "--manifest", "docs/carve-manifest.yaml")
    combined = done.stdout + done.stderr
    assert done.returncode == 2, combined
    assert ": carve-unreadable —" in combined, combined


def test_json_reports_the_summary(scratch: Scratch) -> None:
    scratch.write(clean_manifest(scratch))
    done = run(scratch, "--json")
    assert done.returncode == 0, done.stdout + done.stderr
    summary = json.loads(done.stdout)
    assert summary["result"] == "ok"
    assert summary["rows"] == 10
    assert summary["retained_here"] == {"kept": 7, "shed": 2,
                                        "retired_by_archive": 1}
    assert summary["leg_overrides"] == {
        "d7-root-release-identity": {"rows": 1, "status": "proposed"},
        "q7-code-leg": {"rows": 1, "status": "ruled"}}


def test_json_reports_the_refusal_code(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "LICENSE")["sha256"] = "0" * 64
    scratch.write(doc)
    done = run(scratch, "--json")
    assert done.returncode == 2
    assert json.loads(done.stdout)["code"] == "carve-digest-mismatch"


# --------------------------------------------------------------------------
# check 1 — shape
# --------------------------------------------------------------------------

def test_a_schema_version_that_is_not_the_integer_one_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["schema_version"] = True
    refuses(scratch, doc, "carve-shape-invalid")


def test_an_unknown_top_level_key_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["moved_path"] = doc["moved_paths"]
    refuses(scratch, doc, "carve-shape-invalid")


def test_a_missing_required_top_level_key_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    del doc["leg_overrides"]
    refuses(scratch, doc, "carve-shape-invalid")


def test_an_unparseable_manifest_is_a_document_defect(
        scratch: Scratch) -> None:
    scratch.manifest_path().parent.mkdir(parents=True, exist_ok=True)
    scratch.manifest_path().write_text("rows: [\n", encoding="utf-8")
    done = run(scratch)
    assert done.returncode == 2
    assert ": carve-shape-invalid —" in done.stderr, done.stderr


def test_an_abbreviated_carve_commit_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["carve_commit"] = scratch.carve[:12]
    refuses(scratch, doc, "carve-shape-invalid")


def test_an_unknown_phase_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["phase"] = "pre-carve"
    refuses(scratch, doc, "carve-shape-invalid")


def test_a_reordered_edit_class_list_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["edit_classes"] = list(reversed(D7_EDIT_CLASSES))
    refuses(scratch, doc, "carve-shape-invalid")


def test_a_declared_sixth_edit_class_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["edit_classes"] = D7_EDIT_CLASSES + ["vocabulary parameterization"]
    refuses(scratch, doc, "carve-shape-invalid")


def test_a_not_moved_row_carrying_a_digest_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "README.md")["sha256"] = "0" * 64
    refuses(scratch, doc, "carve-shape-invalid")


def test_a_moved_row_without_leg_default_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    del row_named(doc, "LICENSE")["leg_default"]
    refuses(scratch, doc, "carve-shape-invalid")


def test_an_unquoted_git_mode_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "LICENSE")["git_mode"] = 100644
    refuses(scratch, doc, "carve-shape-invalid")


def test_a_moved_row_outside_the_watched_surface_refuses(
        scratch: Scratch) -> None:
    """A moved file the surface does not watch could change after the carve
    commit with no refusal at all."""
    doc = clean_manifest(scratch)
    doc["moved_paths"] = [p for p in doc["moved_paths"] if p != "LICENSE"]
    combined = refuses(scratch, doc, "carve-shape-invalid")
    assert "LICENSE" in combined, combined


def test_an_edit_with_no_line_numbers_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "scripts/core.py")["edits"][0]["lines"] = []
    refuses(scratch, doc, "carve-shape-invalid")


def test_an_override_neither_ruled_nor_proposed_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["leg_overrides"]["q7-code-leg"]["status"] = "assumed"
    refuses(scratch, doc, "carve-shape-invalid")


def test_a_not_moved_reason_the_checker_does_not_know_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["not_moved_reasons"].append("superseded_by_split")
    refuses(scratch, doc, "carve-shape-invalid")


# --------------------------------------------------------------------------
# check 2 — revision
# --------------------------------------------------------------------------

def test_a_carve_commit_the_repository_does_not_carry_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["carve_commit"] = "deadbeef" * 5
    combined = refuses(scratch, doc, "carve-revision-mismatch")
    assert "DOES NOT CARRY" in combined, combined


def test_a_revision_the_carve_commit_is_not_an_ancestor_of_refuses(
        scratch: Scratch) -> None:
    _git(scratch.repo, "checkout", "-q", "--orphan", "elsewhere")
    _git(scratch.repo, "rm", "-q", "-r", "--cached", ".")
    _write(scratch.repo, "unrelated.md", "# another line\n")
    other = scratch.commit("an unrelated root", "unrelated.md")
    _git(scratch.repo, "checkout", "-q", "-f", "main")
    combined = refuses(scratch, clean_manifest(scratch),
                       "carve-revision-mismatch", "--at", other)
    assert "NOT AN ANCESTOR" in combined, combined


def test_an_annotated_tag_id_used_as_the_referent_refuses(
        scratch: Scratch) -> None:
    _git(scratch.repo, "tag", "-a", "carve-0", "-m", "a label",
         scratch.carve)
    tag_object = _git(scratch.repo, "rev-parse", "carve-0").stdout.strip()
    assert tag_object != scratch.carve
    doc = clean_manifest(scratch)
    doc["carve_commit"] = tag_object
    combined = refuses(scratch, doc, "carve-revision-mismatch")
    assert "PEELS" in combined, combined


# --------------------------------------------------------------------------
# check 3 — digests
# --------------------------------------------------------------------------

def test_a_drifted_digest_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "contracts/fam/schema.yaml")["sha256"] = "0" * 64
    combined = refuses(scratch, doc, "carve-digest-mismatch")
    assert "DIGEST DRIFT" in combined, combined


def test_a_recorded_mode_the_carve_commit_does_not_carry_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "scripts/core.py")["git_mode"] = "100755"
    combined = refuses(scratch, doc, "carve-digest-mismatch")
    assert "MODE DRIFT" in combined, combined


def test_a_moved_file_changed_since_the_carve_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    _write(scratch.repo, "contracts/fam/schema.yaml", "type: array\n")
    scratch.commit("an edit the carve would not ship",
                   "contracts/fam/schema.yaml")
    combined = refuses(scratch, doc, "carve-digest-mismatch")
    assert "CHANGED SINCE THE CARVE" in combined, combined


def test_a_kept_moved_file_changed_since_the_carve_refuses_before_the_shed(
        scratch: Scratch) -> None:
    """Under `carve` a KEPT moved row is frozen too: it is carved at the carve
    commit, and an edit here before the carve runs is one the destination never
    receives."""
    doc = clean_manifest(scratch)
    _write(scratch.repo, "scripts/core.py", "A = 1\n")
    scratch.commit("the adapter rewrite, too early", "scripts/core.py")
    refuses(scratch, doc, "carve-digest-mismatch")


def test_a_moved_file_deleted_since_the_carve_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    _git(scratch.repo, "rm", "-q", "--", "openspec/changes/travel/proposal.md")
    scratch.commit("a shed with no phase flip")
    combined = refuses(scratch, doc, "carve-path-absent")
    assert "DELETED SINCE THE CARVE" in combined, combined


def test_an_edit_line_past_the_end_of_the_blob_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "scripts/core.py")["edits"][0]["lines"] = [4]
    combined = refuses(scratch, doc, "carve-shape-invalid")
    assert "has 3 line(s)" in combined, combined


def test_an_edit_on_the_last_line_of_the_blob_passes(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "scripts/core.py")["edits"][0]["lines"] = [3]
    verifies(scratch, doc)


# --------------------------------------------------------------------------
# check 4 — surface and completeness
# --------------------------------------------------------------------------

def test_a_vacuous_moved_paths_entry_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["moved_paths"].append("contracts/famliy/")
    refuses(scratch, doc, "carve-surface-vacuous")


def test_a_tracked_path_outside_the_surface_in_no_row_refuses(
        scratch: Scratch) -> None:
    """THE D7 DIFFERENCE from openDox: completeness at the carve commit is the
    WHOLE tree, so a file the carve does not move still needs its row."""
    doc = clean_manifest(scratch)
    doc["rows"] = [r for r in doc["rows"] if r["source_path"] != "README.md"]
    combined = refuses(scratch, doc, "carve-file-undeclared")
    assert "README.md" in combined, combined


def test_a_tracked_path_in_two_rows_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["rows"].insert(1, copy.deepcopy(row_named(doc, "LICENSE")))
    refuses(scratch, doc, "carve-file-duplicated")


def test_a_row_for_a_path_the_carve_commit_does_not_track_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["rows"].append({"source_path": "zz/never-tracked.md",
                        "disposition": "not_moved",
                        "reason": "stays_openxwallet_governance",
                        "evidence": "a row for nothing",
                        "retained_here": "kept"})
    combined = refuses(scratch, doc, "carve-path-absent")
    assert "zz/never-tracked.md" in combined, combined


def test_a_file_appearing_under_the_surface_since_the_carve_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    _write(scratch.repo, "contracts/fam/examples/new.yaml", "y: 2\n")
    scratch.commit("a fixture the carve would never ship",
                   "contracts/fam/examples/new.yaml")
    combined = refuses(scratch, doc, "carve-file-undeclared")
    assert "APPEARED" in combined, combined
    assert "contracts/fam/examples/new.yaml" in combined, combined


def test_a_file_appearing_outside_the_surface_since_the_carve_verifies(
        scratch: Scratch) -> None:
    """`main` growing a file the carve does not touch — this checker, its test,
    the manifest itself — is not the carve's business."""
    doc = clean_manifest(scratch)
    _write(scratch.repo, "scripts/validate-something-new.py", "X = 1\n")
    scratch.commit("a new adapter script", "scripts/validate-something-new.py")
    verifies(scratch, doc)


def test_a_not_moved_row_under_the_surface_deleted_since_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    _git(scratch.repo, "rm", "-q", "--",
         "contracts/fam/examples/negative/stays.yaml")
    scratch.commit("an adapter negative dropped")
    combined = refuses(scratch, doc, "carve-path-absent")
    assert "contracts/fam/examples/negative/stays.yaml" in combined, combined


def test_a_not_moved_row_outside_the_surface_may_change_or_go(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    _write(scratch.repo, "README.md", "# the front door, rewritten\n")
    _git(scratch.repo, "rm", "-q", "--", "scripts/adapter_only.py")
    scratch.commit("this repository's own files move on", "README.md")
    verifies(scratch, doc)


# --------------------------------------------------------------------------
# check 5 — closed vocabularies
# --------------------------------------------------------------------------

@pytest.mark.parametrize("path,key,value", [
    ("LICENSE", "disposition", "moved_somewhere"),
    ("LICENSE", "destination", "openwallet_docs"),
    ("LICENSE", "retained_here", "archived"),
    ("README.md", "reason", "stays_vendored_not_carved"),
    ("LICENSE", "leg_override", "q8-something"),
])
def test_a_value_outside_a_closed_vocabulary_refuses(
        scratch: Scratch, path: str, key: str, value: str) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, path)[key] = value
    refuses(scratch, doc, "carve-vocabulary-unknown")


def test_an_edit_class_outside_d7s_five_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "scripts/core.py")["edits"][0]["class"] = "import rewrites"
    refuses(scratch, doc, "carve-vocabulary-unknown")


def test_a_classifier_leg_outside_its_answers_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "LICENSE")["leg_default"]["leg"] = "assembly"
    refuses(scratch, doc, "carve-vocabulary-unknown")


# --------------------------------------------------------------------------
# check 6 — consistency
# --------------------------------------------------------------------------

def test_a_declared_edit_with_no_edits_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    del row_named(doc, "scripts/core.py")["edits"]
    refuses(scratch, doc, "carve-disposition-inconsistent")


def test_verbatim_with_edits_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "LICENSE")["edits"] = [{"class": "subject lines",
                                           "lines": [1]}]
    refuses(scratch, doc, "carve-disposition-inconsistent")


def test_not_moved_with_edits_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "README.md")["edits"] = [{"class": "subject lines",
                                             "lines": [1]}]
    refuses(scratch, doc, "carve-disposition-inconsistent")


def test_a_not_moved_row_that_is_not_kept_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "README.md")["retained_here"] = "shed"
    refuses(scratch, doc, "carve-retention-inconsistent")


def test_retired_by_archive_outside_the_promoted_specs_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "openspec/changes/travel/proposal.md")["retained_here"] = \
        "retired_by_archive"
    refuses(scratch, doc, "carve-retention-inconsistent")


def test_a_remapped_destination_path_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "scripts/core.py")["destination_path"] = "src/core.py"
    refuses(scratch, doc, "carve-path-remapped")


def test_a_departure_from_the_default_with_no_override_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    del row_named(doc, "contracts/fam/schema.yaml")["leg_override"]
    combined = refuses(scratch, doc, "carve-override-inconsistent")
    assert "spec-governance" in combined, combined


def test_an_override_where_nothing_departs_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "LICENSE")["leg_override"] = "d7-root-release-identity"
    refuses(scratch, doc, "carve-override-inconsistent")


def test_an_override_authorizing_another_leg_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "contracts/fam/schema.yaml")["leg_override"] = \
        "d7-root-release-identity"
    refuses(scratch, doc, "carve-override-inconsistent")


def test_an_override_of_another_rule_refuses(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["leg_overrides"]["q7-code-leg"]["overrides_rule"] = "spec-api-contracts"
    refuses(scratch, doc, "carve-override-inconsistent")


def test_an_ambiguous_default_is_a_departure(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    row_named(doc, "LICENSE")["leg_default"] = {
        "leg": "ambiguous", "rule": "default"}
    refuses(scratch, doc, "carve-override-inconsistent")


def test_rows_out_of_bytewise_order_refuse(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["rows"][0], doc["rows"][1] = doc["rows"][1], doc["rows"][0]
    refuses(scratch, doc, "carve-path-order-violation")


# --------------------------------------------------------------------------
# the two phases
# --------------------------------------------------------------------------

def _shed(scratch: Scratch, *, rewrite_kept: bool = True,
          retire: bool = True) -> str:
    """The adapter rebuild: the `shed` rows deleted, a `kept` moved row
    rewritten in place, and (optionally) the archived spec gone."""
    _git(scratch.repo, "rm", "-q", "--", "contracts/fam/schema.yaml",
         "openspec/changes/travel/proposal.md")
    paths = []
    if rewrite_kept:
        _write(scratch.repo, "scripts/core.py", "from core import *\n")
        paths.append("scripts/core.py")
    if retire:
        _git(scratch.repo, "rm", "-q", "--", "openspec/specs/cap/spec.md")
    return scratch.commit("the shed", *paths)


def test_a_post_shed_manifest_verifies_over_a_shed_tree(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["phase"] = "post-shed"
    _shed(scratch)
    out = verifies(scratch, doc)
    assert "phase post-shed," in out, out


def test_a_post_shed_manifest_may_keep_the_spec_until_the_archive(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["phase"] = "post-shed"
    _shed(scratch, retire=False)
    verifies(scratch, doc)


def test_a_retired_spec_still_present_post_shed_must_be_unchanged(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["phase"] = "post-shed"
    _shed(scratch, retire=False)
    _write(scratch.repo, "openspec/specs/cap/spec.md", "openWallet SHALL.\n")
    scratch.commit("an edit to a spec that leaves by archive",
                   "openspec/specs/cap/spec.md")
    refuses(scratch, doc, "carve-digest-mismatch")


def test_a_post_shed_manifest_over_an_unshed_tree_refuses(
        scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["phase"] = "post-shed"
    combined = refuses(scratch, doc, "carve-shed-incomplete")
    assert "contracts/fam/schema.yaml" in combined, combined


def test_a_kept_moved_row_may_not_go_with_the_shed(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    doc["phase"] = "post-shed"
    _shed(scratch, rewrite_kept=False)
    _git(scratch.repo, "rm", "-q", "--", "LICENSE")
    scratch.commit("a kept row deleted with the shed")
    combined = refuses(scratch, doc, "carve-path-absent")
    assert "LICENSE" in combined, combined


def test_the_shed_refuses_under_the_carve_phase(scratch: Scratch) -> None:
    doc = clean_manifest(scratch)
    _shed(scratch, rewrite_kept=False, retire=False)
    refuses(scratch, doc, "carve-path-absent")


# --------------------------------------------------------------------------
# the real manifest
# --------------------------------------------------------------------------

def _carries(commit: str) -> bool:
    done = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True, check=False)
    return done.returncode == 0


def test_the_real_repository_answers_at_the_ruled_path() -> None:
    """The documented invocation, from the repository root, with no arguments.

    A BRANCH and never a skip. Where the history carries the named carve
    commit, the full verdict; in a depth-1 checkout (the `pytest-suite` job's),
    the checker must REFUSE for want of its referent, naming it — the
    fail-closed answer, asserted rather than skipped.
    """
    done = subprocess.run([sys.executable, str(SCRIPT)], cwd=str(REPO_ROOT),
                          capture_output=True, text=True, check=False)
    manifest = REPO_ROOT / MODULE.MANIFEST_RELPATH
    if not manifest.is_file():
        assert done.returncode == 0, done.stdout + done.stderr
        assert done.stdout.startswith("NO MANIFEST "), done.stdout
        return
    declared = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if not _carries(declared["carve_commit"]):
        combined = done.stdout + done.stderr
        assert done.returncode == 2, combined
        assert ": carve-revision-mismatch —" in combined, combined
        assert declared["carve_commit"] in combined, combined
        return
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.startswith("OK "), done.stdout
    assert f"phase {declared.get('phase', 'carve')}," in done.stdout, \
        done.stdout
    assert "232 tracked path(s) at the carve commit, each in exactly one row" \
        in done.stdout, done.stdout


def test_the_real_manifest_names_the_ruled_carve_commit_and_d7s_counts() -> None:
    """The real document, read with no git at all, so this holds on every run
    whatever the checkout depth."""
    manifest = REPO_ROOT / MODULE.MANIFEST_RELPATH
    if not manifest.is_file():
        return
    doc = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert doc["carve_commit"] == CARVE_COMMIT
    assert doc.get("phase", "carve") == "carve"
    rows = doc["rows"]
    assert len(rows) == 232
    paths = [r["source_path"] for r in rows]
    assert paths == sorted(paths, key=lambda p: p.encode("utf-8"))
    assert len(set(paths)) == len(paths)
    assert doc["edit_classes"] == D7_EDIT_CLASSES

    moved = [r for r in rows if r["disposition"] != "not_moved"]
    assert all(r["destination_path"] == r["source_path"] for r in moved)
    overrides = {}
    for row in moved:
        if row.get("leg_override"):
            overrides.setdefault(row["leg_override"], []).append(
                row["source_path"])
    # design.md D7: 73 contract rows to the code leg under RULED Q7, and 9
    # release-identity rows to the root as PROPOSED.
    assert len(overrides["q7-code-leg"]) == 73
    assert doc["leg_overrides"]["q7-code-leg"]["status"] == "ruled"
    assert len(overrides["d7-root-release-identity"]) == 9
    assert doc["leg_overrides"]["d7-root-release-identity"]["status"] == \
        "proposed"
    assert sorted(overrides) == ["d7-root-release-identity", "q7-code-leg"]

    # The three issuer-anchor negatives stay, at their path.
    for name in ("grant-review-authority-omits-issued-by.yaml",
                 "grant-review-root-issuer-is-a-machine.yaml",
                 "grant-review-root-issuer-says-opensoft.yaml"):
        row = next(r for r in rows if r["source_path"].endswith("/" + name))
        assert row["disposition"] == "not_moved"
        assert row["retained_here"] == "kept"
    # The two promoted specs leave only by the archive.
    retired = sorted(r["source_path"] for r in rows
                     if r["retained_here"] == "retired_by_archive")
    assert retired == ["openspec/specs/openxwallet-agent-profile/spec.md",
                       "openspec/specs/openxwallet/spec.md"]
