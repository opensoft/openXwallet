"""wallet-v1.1's two behaviours, proven the way CI will see them.

Realizes P2b (group 4) of the ratified openxFactory change
`split-openxwallet-repo` — `design.md` D4 (the sweep prunes nested
repositories) and D3 (the register reader emits a durable happy-path NOTE) —
under `clarifications.md` N4. Speckit feature
`specs/013-nested-repo-prune-register-note/`.

Discipline copied from `tests/wallet_yaml_syntax_gate/test_gate.py`: drive the
script as a SUBPROCESS, not an in-process import, so the exit codes the
workflows act on are the ones under test, and build every fixture tree under
`tmp_path` so nothing here can touch the repository.

UNDER COMPOSITION (`split-openwallet-neutral-core`, design.md D2 and D5) the
two behaviours live in different repositories. The sweep prune is the neutral
core's, carved to opensoft/openWallet-code with its tests; this entrypoint runs
that core in process from the pinned `openWallet/` mount. So this file keeps the
REGISTER half (US2, whose reader is openXwallet's), the pinned corpus note of the
COMPOSED corpus, a composed-entrypoint regression of the prune note, and the
FR-009 claim restated against the pre-split validator at the named carve commit.

The prune's whole point is that a nested repository's YAML stops being
adjudicated as a live record of the scanned tree. So the assertions are on the
`repo scan:` note's VALIDATED COUNT — the one number that says how many records
the sweep actually took as real — rather than on the absence of some particular
finding, which a future rule change could make vacuously true.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate-openxwallet.py"

SCAN_NOTE = re.compile(
    r"^note  repo scan: (\d+) openxWallet artifact\(s\) validated, "
    r"(\d+) document\(s\) skipped as another kind$", re.M)
PRUNE_NOTE = re.compile(
    r"^note  nested repositories pruned \(not adjudicated\): (.+)$", re.M)
REGISTER_NOTE = re.compile(
    r"^note  intake register read: (\S+) \((\d+) row\(s\)\)$", re.M)
ABSENT_REGISTER_NOTE = "note  no intake register at this tree; nothing to read"
# wallet-v1.3 (`add-multi-key-wallets`) added four positives and nine negatives
# for the declared key set. The count is LITERAL, not a wildcard, for the same
# reason the register's seat-key count is: a corpus that silently lost a fixture
# and a corpus that passed are both "green" to a pattern. It is the COMPOSED
# count: the pinned core's 21 / 42 / 11 of 11, plus rule (t)'s three negatives
# and the two OXWR rows they probe, which stay in this repository.
CORPUS_NOTE = ("note  corpus: 21 positive example(s), 45 negative "
               "confirmation(s) across 13/13 requirements")

# A minimal VALID wallet record, kept independent of the packaged corpus on
# purpose: a test that copies a corpus example is also a test of the corpus
# exclusion, and those are different questions (the exclusion has its own test
# below). Shaped on the validator's own S4 self-test probe wallet.
WALLET = {
    "schema_version": 1,
    "kind": "xfactory_wallet_record",
    "wallet_id": "wal-prune-probe-0001",
    "holder": {"holder_id": "agent:prune-probe", "holder_class": "agent"},
    "key_reference": {
        "did": "did:key:z6Mko2FefScUQg9opCriwQmjfcb3Qjnb5bN49hQsEVMo6gee",
        "key_id": "key-prune-0001",
        "signature_algorithm": "ed25519",
    },
    "custody": {"model": "holder_readable", "registry_version": 1},
    "state": "active",
}


# --------------------------------- helpers ---------------------------------

def _run(target: Path | str, *args: str,
         script: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Invoke the validator exactly as `wallet-validation` does."""
    cmd = [sys.executable, str(script or VALIDATOR), str(target), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


def _validated(out: str) -> int:
    """The number of records the sweep took as REAL. The assertion target."""
    m = SCAN_NOTE.search(out)
    assert m, f"no `repo scan:` note in output:\n{out}"
    return int(m.group(1))


def _pruned(out: str) -> list[str]:
    m = PRUNE_NOTE.search(out)
    return [p.strip() for p in m.group(1).split(",")] if m else []


def _nested_repo(path: Path, kind: str) -> Path:
    """Make `path` a nested repository, in one of the two real on-disk shapes.

    A submodule checkout (and a `git worktree`) carries a `.git` FILE holding a
    `gitdir:` line; a plain nested clone carries a `.git` DIRECTORY. Both mean
    the same thing for this rule, which is why the prune tests for the entry's
    EXISTENCE and never reads it.
    """
    path.mkdir(parents=True, exist_ok=True)
    if kind == "file":
        (path / ".git").write_text("gitdir: ../.git/modules/x\n", encoding="utf-8")
    elif kind == "dir":
        (path / ".git").mkdir()
    else:  # pragma: no cover - a typo in a test is not a test case
        raise ValueError(kind)
    return path


def _write_wallet(directory: Path, wallet_id: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    dest = directory / "live-record.yaml"
    dest.write_text(yaml.safe_dump(dict(WALLET, wallet_id=wallet_id)),
                    encoding="utf-8")
    return dest


# ------------------- the composed entrypoint: corpus and prune -------------

def test_the_repository_itself_still_reports_its_own_corpus(tmp_path):
    """21 positives and 45 negatives over 13/13 requirements: the core's corpus
    and closure, joined by this repository's three rule (t) negatives and the
    two requirement rows they probe."""
    r = _run(REPO_ROOT)
    assert CORPUS_NOTE in r.stdout, r.stdout + r.stderr
    assert r.returncode == 0, r.stdout + r.stderr


def test_the_composed_entrypoint_prunes_the_mounted_openwallet_root(tmp_path):
    """design.md D5's ONE declared new line. The mount `openWallet/` carries a
    `.git` entry, so the sweep prunes it WHOLE: the pinned core's own corpus,
    schemas and legs are never adjudicated as live records of this tree. The
    line is asserted exactly, because a consumer gate parses it."""
    r = _run(REPO_ROOT)
    assert ("note  nested repositories pruned (not adjudicated): openWallet"
            in r.stdout.splitlines()), r.stdout + r.stderr
    assert _pruned(r.stdout) == ["openWallet"], r.stdout


def test_the_composed_entrypoint_prunes_both_nested_shapes(tmp_path):
    """The regression the adapter keeps of the prune it no longer owns: through
    THIS entrypoint, a `.git` FILE (a submodule) and a `.git` DIRECTORY (a
    nested clone) are both pruned, and the one record outside them is the one
    record adjudicated. The shapes' own tests travel with the core."""
    root = tmp_path / "root"
    root.mkdir()
    _write_wallet(_nested_repo(root / "sub-as-file", "file"), "wal-a-0001")
    _write_wallet(_nested_repo(root / "sub-as-dir", "dir"), "wal-b-0001")
    _write_wallet(root / "own-records", "wal-c-0001")

    r = _run(root)
    assert _validated(r.stdout) == 1, r.stdout + r.stderr
    assert _pruned(r.stdout) == ["sub-as-dir", "sub-as-file"], r.stdout


# ------------------- US2: the durable register-read NOTE -------------------

FUTURE = "2099-06-30T23:59:59Z"
REVIEW_TOKEN = "review"
ROOT_ISSUER = "Brett.Heap@opensoft.one"

REGISTER_WALLET = dict(WALLET, wallet_id="wal-register-probe-0001",
                       holder={"holder_id": "agent:register-probe",
                               "holder_class": "agent"})
REGISTER_GRANT = {
    "schema_version": 1,
    "kind": "xfactory_wallet_grant",
    "grant_id": "grant-register-probe-0001",
    "audience": {"wallet_ref": "wal-register-probe-0001",
                 "holder_ref": "agent:register-probe"},
    "scope": {
        "acts": [REVIEW_TOKEN],
        "authority_tier": "act",
        "objects": ["opensoft/openxFactory"],
        "approval_posture": {
            "hermes_approval_required_before_apply": True,
            "authority_agents_may_approve": False,
            "human_escalation_required_for": ["irreversible_external_effect"],
        },
    },
    "expires_at": FUTURE,
    "issued_at": "2026-08-24T00:00:00Z",
    "state": "active",
    "issued_by": ROOT_ISSUER,
}
REGISTER_ROW = {
    "row_id": "row-register-probe-0001",
    "holder_ref": "agent:register-probe",
    "wallet_ref": "wal-register-probe-0001",
    "target_repo": "opensoft/openxFactory",
    "act": REVIEW_TOKEN,
    "authority_tier": "act",
    "grant_ref": "grant-register-probe-0001",
    "expires_at": FUTURE,
    "state": "active",
}
ATTESTATION = {
    "attestation_id": "attest-custody-wal-register-probe-0001",
    "subject_wallet_ref": "wal-register-probe-0001",
    "custody_model_attested": "holder_readable",
    "verified_by": {"name": "Brett Heap", "role": "responsible operator",
                    "standing": "Human Escalation Contract"},
    "verified_at": "2026-08-24T12:00:00Z",
    "verified_against": {"method": "operator-minted ed25519 keypair",
                         "isolation_claimed": False},
}


def _register_tree(root: Path, rows: list[dict] | None = None) -> Path:
    """A tree whose register reads CLEAN, end to end.

    Shaped on the validator's own S4 self-test fixtures (`_s4_tree`,
    `s4_row`, `s4_grant`, `s4_wallet`, `s4_attest`), which are local to
    `self_test_register_reader()` and so cannot be imported — a
    subprocess-driven test needs them as FILES anyway.
    """
    records = root / "governance" / "wallets"
    records.mkdir(parents=True)
    (records / "wallet.yaml").write_text(
        yaml.safe_dump(REGISTER_WALLET), encoding="utf-8")
    (records / "grant.yaml").write_text(
        yaml.safe_dump(REGISTER_GRANT), encoding="utf-8")

    ra = root / "governance" / "review-authority"
    (ra / "attestations").mkdir(parents=True)
    # wallet-v1.2 (`add-per-seat-register-entries`): the top level is a CLOSED
    # read set and `revocation_staleness_bound` is REQUIRED, so this fixture
    # declares one. wallet-v1.1's two behaviours are unchanged by that — which is
    # what these tests still assert — but a register without the bound is no
    # longer a readable register, and a fixture that pretended otherwise would be
    # testing a shape no consumer can commit.
    (ra / "register.yaml").write_text(
        yaml.safe_dump({"register_version": 1,
                        "revocation_staleness_bound": "P7D",
                        "rows": rows if rows is not None else [REGISTER_ROW]}),
        encoding="utf-8")
    (ra / "attestations" / "custody-attest.yaml").write_text(
        yaml.safe_dump(ATTESTATION), encoding="utf-8")
    return root


def test_a_successful_register_read_says_so_exactly_once(tmp_path):
    """D3's durable positive line, and the whole reason it exists.

    Before this, `check_register` was SILENT on success: the only output naming
    the register was a failure finding, and the absent-register note named no
    path — so "the register was read" could only be inferred from a conjunction
    of absences.
    """
    r = _run(_register_tree(tmp_path / "consumer"))
    hits = REGISTER_NOTE.findall(r.stdout)
    assert len(hits) == 1, r.stdout
    path, rows = hits[0]
    assert path == "governance/review-authority/register.yaml", r.stdout
    assert rows == "1", r.stdout


def test_the_register_note_leaves_a_strict_run_green(tmp_path):
    """S4.5: an `f.note`, NEVER a warning.

    `report()` reds a `--strict` run on warnings and a live consumer runs
    `--strict`, so the CLASS of this line is a compatibility term, not a
    presentation choice.
    """
    root = _register_tree(tmp_path / "consumer")
    plain = _run(root)
    strict = _run(root, "--strict")
    assert plain.returncode == 0, plain.stdout + plain.stderr
    assert strict.returncode == 0, strict.stdout + strict.stderr
    assert REGISTER_NOTE.search(strict.stdout), strict.stdout
    assert "WARN" not in strict.stdout, strict.stdout


def test_the_register_path_is_relative_to_the_scan_root(tmp_path):
    """Relative, so the line is identical on a laptop and on a CI runner.

    The downstream consumer-gate test (D3, landing at P3) asserts on it; an
    absolute path would differ between checkouts and force a substring match.
    """
    root = _register_tree(tmp_path / "deeply" / "nested" / "consumer")
    r = _run(root)
    m = REGISTER_NOTE.search(r.stdout)
    assert m, r.stdout
    assert not Path(m.group(1)).is_absolute(), m.group(1)
    assert str(tmp_path) not in m.group(1), m.group(1)


def test_no_register_keeps_the_ratified_absent_behaviour(tmp_path):
    """Unchanged: absent register + no review grants is a legitimate posture."""
    root = tmp_path / "root"
    _write_wallet(root / "records", "wal-noreg-0001")

    r = _run(root, "--strict")
    assert ABSENT_REGISTER_NOTE in r.stdout, r.stdout
    assert REGISTER_NOTE.search(r.stdout) is None, r.stdout
    assert r.returncode == 0, r.stdout + r.stderr


def test_a_register_inside_a_nested_repo_is_not_read(tmp_path):
    """Both behaviours meeting: the register is resolved from the SCAN ROOT.

    A consumer that pointed the validator at the nested product instead of its
    own root would read the product's register, not its own — which is why
    D4 refused "narrow the scan scope" as the prune's mechanism.
    """
    root = tmp_path / "root"
    root.mkdir()
    _register_tree(_nested_repo(root / "pinned-product", "file"))

    r = _run(root)
    assert REGISTER_NOTE.search(r.stdout) is None, r.stdout
    assert ABSENT_REGISTER_NOTE in r.stdout, r.stdout
    assert _pruned(r.stdout) == ["pinned-product"], r.stdout


# ------------------- US3: nothing a live consumer keys on moves -------------

def test_the_command_line_surface_is_unchanged(tmp_path):
    """S4.3: no `--exclude`. An exclusion the caller supplies can be omitted.

    Both R6's zero-refactor proof and D3's pinned-invocation test key on this
    signature, so it is asserted rather than remembered.
    """
    r = subprocess.run([sys.executable, str(VALIDATOR), "--help"],
                       capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode == 0, r.stderr
    options = set(re.findall(r"(?<![\w-])(--[a-z][a-z-]*)", r.stdout))
    assert options == {"--strict", "--help"}, sorted(options)
    assert "path" in r.stdout


def test_this_repository_adjudicates_with_no_error_and_no_warning(tmp_path):
    """The durable half of the corpus-identity proof, runnable anywhere.

    The self-test adjudicates all 21 positives and all 45 negatives on every
    invocation and asserts each negative fails with its EXPECTED code, so a
    clean summary line over this repository IS the corpus identity statement —
    and unlike the git-based half below, it needs no history.
    """
    r = _run(REPO_ROOT, "--strict")
    assert "validate-openxwallet: 0 error(s), 0 warning(s)" in r.stdout, r.stdout
    assert r.returncode == 0, r.stdout + r.stderr


# The pre-split validator design.md D5's neutrality claim is made against: the
# one at the NAMED CARVE COMMIT (task 2.3; Brett Heap, 2026-10-08, "name 90111df
# as the carve commit, do 2.4 and 2.5").
CARVE_COMMIT = "90111df262d6f54f7e82651d860adc12345f83f4"


def _baseline_script(tmp_path: Path) -> Path | None:
    """The PRE-SPLIT validator, recovered from git history at the carve commit.

    Never by stashing or checking out: this repository's working tree is not
    this test's to mutate. The script is written into a scratch `scripts/`
    directory beside THE CARVE COMMIT'S OWN `contracts/`, because it derives
    `ROOT` from its own location and adjudicates the corpus it finds there.

    WHY NOT "THE PREVIOUS VERSION" ANY MORE. Until the split this test copied the
    current script into a second scratch root and ran it over the previous
    corpus. The composed adapter cannot run from a scratch root: it loads its
    core from `openWallet/` beside it and refuses, exit 2, where there is none.
    Compared that way the refusal would be an empty finding set, equal to the
    baseline's, and the test would pass on a validator that adjudicated nothing.
    So the current entrypoint runs IN PLACE and the baseline is fixed at the
    commit the neutrality claim names, which is also the last pre-split blob.
    """
    current = VALIDATOR.read_text(encoding="utf-8")
    got = subprocess.run(
        ["git", "show", f"{CARVE_COMMIT}:scripts/validate-openxwallet.py"],
        capture_output=True, text=True, cwd=REPO_ROOT)
    # NEVER compare against a blob equal to the working copy: that would compare
    # this version against ITSELF and pass vacuously.
    if got.returncode != 0 or not got.stdout or got.stdout == current:
        return None
    archive = subprocess.run(["git", "archive", CARVE_COMMIT, "contracts"],
                             capture_output=True, cwd=REPO_ROOT)
    if archive.returncode != 0:  # pragma: no cover
        return None
    shadow = tmp_path / "pre-split"
    (shadow / "scripts").mkdir(parents=True)
    dest = shadow / "scripts" / "validate-openxwallet.py"
    dest.write_text(got.stdout, encoding="utf-8")
    subprocess.run(["tar", "-x", "-C", str(shadow)], input=archive.stdout,
                   check=True)
    return dest


def test_the_composed_adapter_adjudicates_as_the_pre_split_validator_did(
        tmp_path):
    """FR-009 under composition: nothing anyone already declares changes verdict.

    THE CLAIM. The pre-split validator at the carve commit, over its own corpus,
    and the composed adapter in place, over the pinned core's corpus plus this
    repository's three rule (t) negatives, print THE SAME BYTES and exit with
    the same code, on the same targets: the self-test alone, this repository
    plain and `--strict`, and a consumer tree whose register reads clean but
    whose second review grant names the legacy org issuer. That last tree is
    what keeps the comparison from being two empty finding sets: its findings
    are asserted PRESENT, so equality there is equality of a real verdict.

    WHY WHOLE OUTPUT AND NOT A FINDING SET. Through `wallet-v1.3` this test
    compared record-level findings and excluded the harness codes, because the
    two runs adjudicated different corpora. Here the corpora are the carve's two
    halves, so nothing needs excluding, and design.md D5 claims byte identity.
    The declared new line, the `openWallet` prune note over this repository, is
    printed by both: the baseline scans the same tree, mount included.
    task 5.4's neutrality gate makes the claim over every fixture tree.

    Skipped LOUDLY, with a reason, where the carve commit is not in this
    checkout's history (a depth-1 CI checkout), and where the recovered baseline
    cannot run; never counted as a pass in either case.
    """
    baseline = _baseline_script(tmp_path)
    if baseline is None:
        pytest.skip(f"the carve commit {CARVE_COMMIT} is not in this "
                    "checkout's history (a depth-1 checkout), so the pre-split "
                    "validator cannot be recovered to compare against")

    consumer = _register_tree(tmp_path / "consumer")
    (consumer / "governance" / "wallets" / "legacy-grant.yaml").write_text(
        yaml.safe_dump(dict(REGISTER_GRANT, grant_id="grant-legacy-0001",
                            issued_by="opensoft")), encoding="utf-8")

    targets = (("the self-test alone", ()),
               ("this repository", (str(REPO_ROOT),)),
               ("this repository, --strict", (str(REPO_ROOT), "--strict")),
               ("a consumer tree with refusals", (str(consumer),)))
    for label, args in targets:
        before = subprocess.run([sys.executable, str(baseline), *args],
                                capture_output=True, text=True, cwd=REPO_ROOT)
        after = subprocess.run([sys.executable, str(VALIDATOR), *args],
                               capture_output=True, text=True, cwd=REPO_ROOT)
        if before.returncode == 2:  # pragma: no cover
            pytest.skip(f"the recovered baseline could not run on {label}: "
                        f"{before.stderr}")
        assert after.returncode != 2, (label, after.stderr)
        assert CORPUS_NOTE in after.stdout, (label, after.stdout)
        assert after.stdout == before.stdout, (
            f"{label}: the composed adapter's output moved.\nBEFORE:\n"
            f"{before.stdout}\nAFTER:\n{after.stdout}")
        assert after.returncode == before.returncode, (label, after.stdout)

    # The refused tree's verdict is REAL: rule (t) and the register reader both
    # bit, through the composed entrypoint, exactly as they did before.
    assert after.returncode == 1, after.stdout
    assert "ERROR [root-issuer-unanchored]" in after.stdout, after.stdout
    assert "ERROR [register-no-active-row]" in after.stdout, after.stdout
