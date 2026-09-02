"""wallet-v1.4: a REVOKED review-class grant owes no register row.

THE DEFECT THIS PINS. `check_register`'s docstring and its `register-no-active-row`
message both say the obligation falls on an ACTIVE review-class grant. The
closing loop did not read the grant's `state` at all — it filtered on
`REVIEW_ACT_TOKEN in scope.acts` and nothing else — so a correctly revoked
review-class grant was held to the obligation too. Terminal revocation is the
ratified drift-cascade rule ("a revoked grant SHALL NEVER return to the active
state; authority resumes only as a NEW grant"), and `REGISTER_MVP_SINGLE_ROW`
caps the register at ONE authority row, so the reader was demanding a row it
also forbids: NO re-issuance could be represented in any consuming tree. The
absent-register branch of the same function carried the same gap.

Found by openxFactory's S5 register act (2026-09-02, PR #583): grant-mrc-0001
revoked for declared-composition drift, grant-mrc-0002 issued against the
changed composition, row-mrc-0001 repointed — a correct tree that went red.

THE FIXTURES ARE THAT ACT'S SHAPE, reduced. Same two-grant re-issuance, same
single repointed row, same terminal `revocation` block. Discipline copied from
`tests/per_seat_register_entries/test_top_level_and_seat_keys.py`: drive the
script as a SUBPROCESS so the exit codes the workflows act on are the ones under
test; build every tree under `tmp_path`; and assert on NAMED FINDING CODES
rather than a non-zero exit, because a refusal for the wrong reason is a
different defect wearing the same colour.

Three halves, because the fix has three: the re-issuance shape is CLEAN, the
guard still fires for an ACTIVE review-class grant with no row, and a row
pointing AT a revoked grant is still refused. The exemption is only ever about
a revoked grant that NO row names — a historical record, which is what a
superseded grant is supposed to be.
"""

from __future__ import annotations

import copy
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate-openxwallet.py"

HOLDER = "agent:merge-readiness-council"
WALLET_REF = "wal-agent-mrc-probe"
TARGET = "opensoft/openxFactory"

# The predecessor's expiry and the successor's differ, exactly as they do on the
# live surface: re-issuance is not a renewal of the same instrument.
OLD_EXPIRY = "2026-11-23T12:00:00Z"
NEW_EXPIRY = "2099-06-30T00:00:00Z"

ABSENT_REGISTER_NOTE = "note  no intake register at this tree; nothing to read"
REGISTER_READ_NOTE = re.compile(
    r"^note  intake register read: .*register\.yaml \((\d+) row\(s\)\)$", re.M)

WALLET = {
    "schema_version": 1,
    "kind": "xfactory_wallet_record",
    "wallet_id": WALLET_REF,
    "holder": {"holder_id": HOLDER, "holder_class": "agent"},
    "key_reference": {
        "did": "did:key:z6Mko2FefScUQg9opCriwQmjfcb3Qjnb5bN49hQsEVMo6gee",
        "key_id": "key-mrc-reissuance-probe",
        "signature_algorithm": "ed25519",
    },
    "custody": {"model": "holder_readable", "registry_version": 1},
    "state": "active",
}

_SCOPE = {
    "acts": ["review"],
    "objects": [TARGET],
    "authority_tier": "act",
    "approval_posture": {
        "hermes_approval_required_before_apply": True,
        "authority_agents_may_approve": False,
        "human_escalation_required_for": [],
    },
}

# GRANT A — the revoked predecessor. The `revocation` block is required by the
# grant schema whenever `state: revoked` (and by the reader's own
# `revocation-unrecorded` rule), which is precisely why exempting `revoked` —
# and not the broader `!= "active"` — cannot be used to hide an unexplained
# grant: a bare `state: revoked` is refused before it can claim this exemption.
GRANT_REVOKED = {
    "schema_version": 1,
    "kind": "xfactory_wallet_grant",
    "grant_id": "grant-mrc-probe-a",
    "audience": {"wallet_ref": WALLET_REF, "holder_ref": HOLDER},
    "scope": copy.deepcopy(_SCOPE),
    "expires_at": OLD_EXPIRY,
    "issued_at": "2026-08-25T12:45:00Z",
    "issued_by": "Brett.Heap@opensoft.one",
    "state": "revoked",
    "revocation": {
        "revoked_at": "2026-09-02T13:33:48Z",
        "reason": "DRIFT: declared composition change. Re-issued as "
                  "grant-mrc-probe-b. Terminal: this grant never returns to "
                  "active.",
    },
}

# GRANT B — the successor, a NEW root grant rather than a derivation of A,
# because authority does not resume through a revoked edge.
GRANT_ACTIVE = {
    "schema_version": 1,
    "kind": "xfactory_wallet_grant",
    "grant_id": "grant-mrc-probe-b",
    "audience": {"wallet_ref": WALLET_REF, "holder_ref": HOLDER},
    "scope": copy.deepcopy(_SCOPE),
    "expires_at": NEW_EXPIRY,
    "issued_at": "2026-09-02T13:33:48Z",
    "issued_by": "Brett.Heap@opensoft.one",
    "state": "active",
}

# THE ONE PERMITTED ROW, repointed onto the successor. Its own `state` stays
# `active`: the row is the authority's continuing existence, not the grant's.
ROW = {
    "row_id": "row-mrc-probe",
    "holder_ref": HOLDER,
    "wallet_ref": WALLET_REF,
    "target_repo": TARGET,
    "act": "review",
    "authority_tier": "act",
    "grant_ref": "grant-mrc-probe-b",
    "expires_at": NEW_EXPIRY,
    "state": "active",
}

ATTESTATION = {
    "attestation_id": "attest-custody-" + WALLET_REF,
    "subject_wallet_ref": WALLET_REF,
    "custody_model_attested": "holder_readable",
    "verified_by": {"name": "Brett Heap", "role": "responsible operator",
                    "standing": "Human Escalation Contract"},
    "verified_at": "2026-08-24T12:00:00Z",
    "verified_against": {"method": "operator-minted ed25519 keypair",
                         "isolation_claimed": False},
}


# --------------------------------- helpers ---------------------------------

def _tree(root: Path, *, grants: list[dict], rows: list[dict] | None = None,
          register: bool = True) -> Path:
    """A tree shaped on the live one: wallets and grants beside the register."""
    records = root / "governance" / "wallets"
    records.mkdir(parents=True)
    (records / "wallet.yaml").write_text(yaml.safe_dump(WALLET),
                                         encoding="utf-8")

    ra = root / "governance" / "review-authority"
    (ra / "grants").mkdir(parents=True)
    for grant in grants:
        (ra / "grants" / f"{grant['grant_id']}.yaml").write_text(
            yaml.safe_dump(grant), encoding="utf-8")

    if not register:
        return root

    (ra / "attestations").mkdir(parents=True)
    (ra / "attestations" / "custody-attest.yaml").write_text(
        yaml.safe_dump(ATTESTATION), encoding="utf-8")
    (ra / "register.yaml").write_text(
        yaml.safe_dump({"register_version": 1,
                        "revocation_staleness_bound": "P7D",
                        "rows": [ROW] if rows is None else rows}),
        encoding="utf-8")
    return root


def _run(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the validator exactly as the consumer gate does."""
    return subprocess.run([sys.executable, str(VALIDATOR), str(target), *args],
                          capture_output=True, text=True)


def _codes(out: str) -> set[str]:
    return set(re.findall(r"^ERROR \[([^]]+)]", out, re.M))


# ------------------------- the re-issuance is clean -------------------------

def test_a_revoked_predecessor_beside_its_successor_is_clean(tmp_path):
    """The whole point: the shape the S5 register act produced must validate.

    Before wallet-v1.4 this tree emitted `register-no-active-row` against the
    REVOKED grant — and the single-row cap forbids the row it asked for, so
    there was no edit to this tree that could have made it green.
    """
    root = _tree(tmp_path / "consumer",
                 grants=[GRANT_REVOKED, GRANT_ACTIVE])
    got = _run(root)
    assert "register-no-active-row" not in _codes(got.stdout), got.stdout
    assert got.returncode == 0, got.stdout + got.stderr
    m = REGISTER_READ_NOTE.search(got.stdout)
    assert m and m.group(1) == "1", got.stdout


def test_a_strict_run_of_the_re_issuance_stays_green(tmp_path):
    """LedgerxFactory runs `--strict`, where `report()` reds on warnings too."""
    root = _tree(tmp_path / "consumer",
                 grants=[GRANT_REVOKED, GRANT_ACTIVE])
    got = _run(root, "--strict")
    assert got.returncode == 0, got.stdout + got.stderr


# --------------------------- the guard still fires ---------------------------

def test_an_active_review_grant_with_no_row_still_refuses(tmp_path):
    """Existing behaviour preserved: the headline obligation is untouched for
    the state it was always about."""
    orphan = dict(copy.deepcopy(GRANT_ACTIVE), grant_id="grant-mrc-probe-c")
    root = _tree(tmp_path / "consumer",
                 grants=[GRANT_REVOKED, GRANT_ACTIVE, orphan])
    got = _run(root)
    assert "register-no-active-row" in _codes(got.stdout), got.stdout
    assert "grant-mrc-probe-c" in got.stdout, got.stdout
    # And it names ONLY the active orphan — never the revoked predecessor.
    offending = [ln for ln in got.stdout.splitlines()
                 if "register-no-active-row" in ln]
    assert offending and all("grant-mrc-probe-a" not in ln
                             for ln in offending), got.stdout
    assert got.returncode == 1, got.stdout


def test_a_row_pointing_at_the_revoked_grant_is_still_refused(tmp_path):
    """Protection preserved, the row -> grant direction.

    The exemption is only ever about a revoked grant NO row names. A register
    still pointing at one is refused by `register-grant-mismatch`, which
    appends the grant's state to its mismatch list.
    """
    root = _tree(tmp_path / "consumer",
                 grants=[GRANT_REVOKED],
                 rows=[dict(ROW, grant_ref="grant-mrc-probe-a",
                            expires_at=OLD_EXPIRY)])
    got = _run(root)
    codes = _codes(got.stdout)
    assert "register-grant-mismatch" in codes, got.stdout
    assert "grant state 'revoked'" in got.stdout, got.stdout
    assert got.returncode == 1, got.stdout


# ------------------- the same rule on the absent-register branch -------------

def test_an_absent_register_with_only_a_revoked_grant_is_clean(tmp_path):
    """The two branches must agree, or a consumer's finding would depend on
    whether it has cold-started its register yet."""
    root = _tree(tmp_path / "consumer", grants=[GRANT_REVOKED],
                 register=False)
    got = _run(root)
    assert "register-no-active-row" not in _codes(got.stdout), got.stdout
    assert ABSENT_REGISTER_NOTE in got.stdout, got.stdout
    assert got.returncode == 0, got.stdout + got.stderr


def test_an_absent_register_with_an_active_review_grant_still_refuses(tmp_path):
    """Existing behaviour preserved on that branch too."""
    root = _tree(tmp_path / "consumer",
                 grants=[GRANT_REVOKED, GRANT_ACTIVE], register=False)
    got = _run(root)
    assert "register-no-active-row" in _codes(got.stdout), got.stdout
    assert "grant-mrc-probe-b" in got.stdout, got.stdout
    assert "grant-mrc-probe-a" not in got.stdout.split(
        "register-no-active-row")[1].splitlines()[0], got.stdout
    assert got.returncode == 1, got.stdout
