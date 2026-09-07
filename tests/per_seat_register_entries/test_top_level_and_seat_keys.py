"""wallet-v1.2: the register's top level is read, and per-seat keys are enforced.

Realizes the openXwallet change `add-per-seat-register-entries` (capability
`review-authority-register-reader`) — Speckit feature
`specs/014-per-seat-register-entries/`.

Discipline copied from `tests/nested_repo_prune/test_prune_and_register_note.py`
and `tests/wallet_yaml_syntax_gate/test_gate.py`: drive the script as a
SUBPROCESS so the exit codes the workflows act on are the ones under test, and
build every fixture tree under `tmp_path` so nothing here can touch the
repository or the packaged corpus.

WHY THE ASSERTIONS ARE WHAT THEY ARE. This change exists because a REQUIRED
check parsed a governed declaration and never adjudicated it, so "no finding was
emitted" is not evidence of anything here. Every positive assertion is on the
ADJUDICATED COUNT the reader notes — the one number that says how many recorded
keys the reader stood behind — and every negative asserts a NAMED CODE rather
than a non-zero exit, because a refusal for the wrong reason is a different
defect wearing the same colour.

The four public halves and fingerprints are the REAL ones, copied from
codexFactory `hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`
(merged `78b8fa2`) — the same bytes openxFactory commits to its register. A
transcription slip therefore fails HERE, in this repository's own suite, and
never on a permanently human-only governed surface.
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

SEAT_NOTE = re.compile(
    r"^note  intake register: (\d+) of (\d+) per-seat signing key\(s\) "
    r"adjudicated and resolved$", re.M)
ABSENT_SEATS_NOTE = ("note  intake register: no per-seat signing key is "
                     "recorded; a runtime projection built from this register "
                     "can authorize no seat")

# The live spellings, both of them. openxFactory's register names the holder
# `agent:merge-readiness-council`; hermes-install's projection keys its seat
# lookup on `council_id: merge_readiness_council`. Neither is derivable from the
# other by a declared rule, which is why the entry carries both.
COUNCIL_REF = "agent:merge-readiness-council"
COUNCIL_ID = "merge_readiness_council"

# Copied verbatim from the 2026-08-28 mint record. Every fingerprint recomputes
# from the key beside it; `test_the_mint_records_four_keys_recompute` proves it
# rather than trusting this table.
MINTED = (
    ("lead-quality",
     "bqJJdpCO4dx31e21t6UA4v7b0r0JaxaqmebrjvhK4OI",
     "sha256:a78d5d8fc075a0c771db521f6e4dd5ebec1ae9c76c5209a3bd54983fccb5e781"),
    ("lead-security",
     "pJn1q--LChggWG1x8j50r3yLzGhIvzaq7aWJB-RIc-U",
     "sha256:39f3088f6072d111cd64147cdd171c7efd75423e225c1d4b8c00445af21f878e"),
    ("lead-integration",
     "WBLjZ2fFHGTjw-2XKHFQxzACyuo4yDDOFbeHMfsZMNs",
     "sha256:4d40ee511f5ede92c3843d530eb9d46efa42dbdd22bce07961688ab14004d1f4"),
    ("company-policy-lead",
     "zwKZNuvovOXl_FpGW9Oxjs0IATnlzstlFdT1GlqSvpY",
     "sha256:0b6ad4ab29f2371cc635e392635c796f103a589dab7f5a3dd22b5ca44a504bbb"),
)

WALLET = {
    "schema_version": 1,
    "kind": "xfactory_wallet_record",
    "wallet_id": "wal-agent-mrc-probe",
    "holder": {"holder_id": COUNCIL_REF, "holder_class": "agent"},
    "key_reference": {
        "did": "did:key:z6Mko2FefScUQg9opCriwQmjfcb3Qjnb5bN49hQsEVMo6gee",
        "key_id": "key-mrc-probe",
        "signature_algorithm": "ed25519",
    },
    "custody": {"model": "holder_readable", "registry_version": 1},
    "state": "active",
}
GRANT = {
    "schema_version": 1,
    "kind": "xfactory_wallet_grant",
    "grant_id": "grant-mrc-probe",
    "audience": {"wallet_ref": "wal-agent-mrc-probe", "holder_ref": COUNCIL_REF},
    "scope": {"acts": ["review"], "authority_tier": "act",
              "objects": ["opensoft/openxFactory"]},
    "expires_at": "2099-11-23T12:00:00Z",
    "issued_at": "2026-08-25T12:45:00Z",
    "issued_by": "Brett.Heap@opensoft.one",
    "state": "active",
}
ROW = {
    "row_id": "row-mrc-probe",
    "holder_ref": COUNCIL_REF,
    "wallet_ref": "wal-agent-mrc-probe",
    "target_repo": "opensoft/openxFactory",
    "act": "review",
    "authority_tier": "act",
    "grant_ref": "grant-mrc-probe",
    "expires_at": "2099-11-23T12:00:00Z",
    "state": "active",
}
ATTESTATION = {
    "attestation_id": "attest-custody-wal-agent-mrc-probe",
    "subject_wallet_ref": "wal-agent-mrc-probe",
    "custody_model_attested": "holder_readable",
    "verified_by": {"name": "Brett Heap", "role": "responsible operator",
                    "standing": "Human Escalation Contract"},
    "verified_at": "2026-08-24T12:00:00Z",
    "verified_against": {"method": "operator-minted ed25519 keypair",
                         "isolation_claimed": False},
}


# --------------------------------- helpers ---------------------------------

def _seat(seat: str, pub: str, fp: str, **over: object) -> dict:
    # The positional names are deliberately NOT the field names: every override
    # below is passed by FIELD name through **over, so a parameter called
    # `public_key` would collide with `_seat(*MINTED[0], public_key=...)` — which
    # is exactly the override the private-seed and non-canonical probes need.
    entry = {
        "seat_id": seat,
        "council_ref": COUNCIL_REF,
        "council_id": COUNCIL_ID,
        "key_id": f"key-seat-{seat}-0001",
        "public_key": pub,
        "key_fingerprint": fp,
        "authorizing_row": ROW["row_id"],
    }
    entry.update(over)
    return entry


def _seats() -> list[dict]:
    return [_seat(*m) for m in MINTED]


def _tree(root: Path, *, rows: list | None = None, top: dict | None = None,
          drop: tuple[str, ...] = ()) -> Path:
    """A register tree the validator will adjudicate, shaped on the live one."""
    records = root / "governance" / "wallets"
    records.mkdir(parents=True)
    (records / "wallet.yaml").write_text(yaml.safe_dump(WALLET),
                                         encoding="utf-8")
    (records / "grant.yaml").write_text(yaml.safe_dump(GRANT), encoding="utf-8")

    ra = root / "governance" / "review-authority"
    (ra / "attestations").mkdir(parents=True)
    (ra / "attestations" / "custody-attest.yaml").write_text(
        yaml.safe_dump(ATTESTATION), encoding="utf-8")

    doc: dict = {"register_version": 1, "revocation_staleness_bound": "P7D",
                 "rows": [ROW] if rows is None else rows}
    doc.update(top or {})
    for key in drop:
        doc.pop(key, None)
    (ra / "register.yaml").write_text(yaml.safe_dump(doc), encoding="utf-8")
    return root


def _run(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the validator exactly as the consumer gate does."""
    return subprocess.run([sys.executable, str(VALIDATOR), str(target), *args],
                          capture_output=True, text=True)


def _codes(out: str) -> set[str]:
    return set(re.findall(r"^ERROR \[([^]]+)]", out, re.M))


def _register_codes(out: str) -> set[str]:
    return {c for c in _codes(out) if c.startswith("register-")}


# ------------------------------- the positive -------------------------------

def test_the_mint_records_four_keys_recompute(tmp_path):
    """The one property the reader enforces that touches key material.

    Asserted independently of the reader, so a table that went stale cannot make
    every negative below pass for the wrong reason.
    """
    import base64
    import hashlib
    for seat_id, public_key, fingerprint in MINTED:
        raw = base64.urlsafe_b64decode(public_key + "=")
        assert len(raw) == 32, seat_id
        assert "sha256:" + hashlib.sha256(raw).hexdigest() == fingerprint, seat_id


def test_the_four_real_seat_keys_validate(tmp_path):
    """One authority row, four per-seat keys: the shape openxFactory commits."""
    root = _tree(tmp_path / "consumer", top={"seat_keys": _seats()})
    got = _run(root)
    assert got.returncode == 0, got.stdout + got.stderr
    m = SEAT_NOTE.search(got.stdout)
    assert m, got.stdout
    assert m.group(1) == m.group(2) == "4", got.stdout


def test_the_note_counts_adjudicated_keys_not_parsed_ones(tmp_path):
    """The count is EVIDENCE, and a count of `len(seat_keys)` would not be.

    A consumer gate asserts on this line to prove the register was adjudicated,
    so a refused entry must not be counted. Otherwise a green-looking note would
    once again prove parsing and nothing else, which is the defect this whole
    capability exists to close.
    """
    seats = _seats()
    seats[2] = _seat(*MINTED[2], authorizing_row="row-nobody-0001")
    root = _tree(tmp_path / "consumer", top={"seat_keys": seats})
    got = _run(root)
    assert got.returncode == 1
    m = SEAT_NOTE.search(got.stdout)
    assert m, got.stdout
    assert (m.group(1), m.group(2)) == ("3", "4"), got.stdout


def test_an_absent_seat_surface_is_accepted_and_visible(tmp_path):
    """Design D10: optional, and the absence is a NOTE rather than silence.

    This is what keeps every landing order of the two-repository wave green,
    and the note is what keeps that from being leniency.
    """
    root = _tree(tmp_path / "consumer")
    got = _run(root)
    assert got.returncode == 0, got.stdout + got.stderr
    assert ABSENT_SEATS_NOTE in got.stdout, got.stdout
    assert not SEAT_NOTE.search(got.stdout), got.stdout


def test_a_strict_run_stays_green(tmp_path):
    """LedgerxFactory runs `--strict`, where `report()` reds on warnings.

    So the CLASS of every new line is a compatibility term, not a presentation
    choice: notes and errors only, never a warning.
    """
    root = _tree(tmp_path / "consumer", top={"seat_keys": _seats()})
    plain, strict = _run(root), _run(root, "--strict")
    assert plain.returncode == 0, plain.stdout
    assert strict.returncode == 0, strict.stdout
    assert "WARN" not in strict.stdout, strict.stdout


# ------------------------------ the top level -------------------------------

def test_an_unread_top_level_declaration_is_refused(tmp_path):
    """The class, not the field.

    A governed `revocation_staleness_bound` sat in the live register
    unadjudicated because the reader read only `register_version` and `rows`.
    Closing the set is what makes the next such addition impossible without a
    reader edit.
    """
    root = _tree(tmp_path / "consumer",
                 top={"an_unread_declaration": "P1D"})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-top-level-unknown"}
    assert "an_unread_declaration" in got.stdout


def test_the_staleness_bound_is_required(tmp_path):
    root = _tree(tmp_path / "consumer", drop=("revocation_staleness_bound",))
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-staleness-bound-missing"}


@pytest.mark.parametrize("bound", ["P1Y", "P1M", "7 days", "P", "PT", "P0D",
                                   "PT0S", "", "P1DT"])
def test_a_malformed_or_zero_bound_is_refused(tmp_path, bound):
    """Years and months: a window whose width depends on the calendar is not a
    bound. Zero: not "revocation is instant" but "no projection may ever be
    read", which disables the gate while looking like tightening it."""
    root = _tree(tmp_path / "consumer",
                 top={"revocation_staleness_bound": bound})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-staleness-bound-malformed"}


@pytest.mark.parametrize("bound", ["P7D", "P1D", "P1W", "PT12H", "P1DT6H30M",
                                   "PT30S"])
def test_a_well_formed_bound_is_accepted(tmp_path, bound):
    """`P7D` is the live register's value. The grammar is hermes-install's, so a
    value accepted here is one its projection schema can carry."""
    root = _tree(tmp_path / "consumer",
                 top={"revocation_staleness_bound": bound})
    got = _run(root)
    assert got.returncode == 0, got.stdout + got.stderr


# ------------------------------- the negatives ------------------------------

@pytest.mark.parametrize("shape", [[], "P7D", {}, 4])
def test_a_malformed_seat_surface_is_refused(tmp_path, shape):
    """An empty surface and an absent one are the same declaration, and the
    absent one is said by omitting the key."""
    root = _tree(tmp_path / "consumer", top={"seat_keys": shape})
    got = _run(root)
    assert got.returncode == 1
    assert "register-seat-keys-malformed" in _register_codes(got.stdout)


def test_an_unknown_field_on_an_entry_is_refused(tmp_path):
    """The register has no schema, so THIS reader is the shape and it is strict
    — the same discipline `REGISTER_ROW_FIELDS` imposes on rows."""
    root = _tree(tmp_path / "consumer", top={
        "seat_keys": [_seat(*MINTED[0], minted_at="2026-08-28T00:00:00Z")]})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-seat-keys-malformed"}
    assert "minted_at" in got.stdout


@pytest.mark.parametrize("field", sorted(
    {"seat_id", "council_ref", "council_id", "key_id", "public_key",
     "key_fingerprint", "authorizing_row"}))
def test_a_missing_field_on_an_entry_is_refused(tmp_path, field):
    entry = _seat(*MINTED[0])
    entry.pop(field)
    root = _tree(tmp_path / "consumer", top={"seat_keys": [entry]})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-seat-keys-malformed"}
    assert field in got.stdout


def test_a_private_seed_pasted_where_a_public_half_belongs_is_refused(tmp_path):
    """Design R2, and the reason the 43-character check is load-bearing beyond
    correctness: the PRIVATE halves of these same keys are stored as 64
    lowercase hex characters, so the most plausible catastrophic paste into a
    governed file is refused BY SHAPE inside the required check."""
    root = _tree(tmp_path / "consumer",
                 top={"seat_keys": [_seat(*MINTED[0], public_key="a" * 64)]})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-seat-key-malformed"}


def test_a_non_canonical_public_key_is_refused(tmp_path):
    """43 legal characters whose final sextet carries trailing bits decode to a
    DIFFERENT key than they spell. Two spellings of one key is the defect."""
    bad = MINTED[0][1][:-1] + "P"
    assert bad != MINTED[0][1]
    root = _tree(tmp_path / "consumer",
                 top={"seat_keys": [_seat(*MINTED[0], public_key=bad)]})
    got = _run(root)
    assert got.returncode == 1
    assert "register-seat-key-malformed" in _register_codes(got.stdout)


def test_a_malformed_fingerprint_is_refused(tmp_path):
    root = _tree(tmp_path / "consumer", top={
        "seat_keys": [_seat(*MINTED[0], key_fingerprint="sha256:NOTHEX")]})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {
        "register-seat-fingerprint-malformed"}


def test_a_fingerprint_that_does_not_recompute_is_refused(tmp_path):
    """Another REAL seat's fingerprint: legal shape, wrong key. This is the
    refusal that makes the register a single source a projection is derived
    from rather than two facts that can drift."""
    root = _tree(tmp_path / "consumer", top={
        "seat_keys": [_seat(*MINTED[0], key_fingerprint=MINTED[1][2])]})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {
        "register-seat-fingerprint-mismatch"}


@pytest.mark.parametrize("field", ["seat_id", "key_id", "key_fingerprint"])
def test_a_duplicate_entry_is_refused(tmp_path, field):
    """Refused, never resolved by file order: a register naming one seat twice
    has two answers to "which key is this seat's root"."""
    clash = _seat(*MINTED[1])
    clash[field] = _seat(*MINTED[0])[field]
    root = _tree(tmp_path / "consumer",
                 top={"seat_keys": [_seat(*MINTED[0]), clash]})
    got = _run(root)
    assert got.returncode == 1
    assert "register-seat-duplicate" in _register_codes(got.stdout)


def test_an_entry_naming_no_row_is_refused(tmp_path):
    root = _tree(tmp_path / "consumer", top={
        "seat_keys": [_seat(*MINTED[0], authorizing_row="row-nobody-0001")]})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-seat-row-unresolved"}


def test_an_entry_on_an_expired_row_is_refused(tmp_path):
    """A key descending from no LIVE authority descends from nothing, and the
    row's COMPUTED expiry decides that — never its stored `state` (N8)."""
    expired = dict(ROW, expires_at="2026-08-01T12:00:00Z")
    root = _tree(tmp_path / "consumer", rows=[expired],
                 top={"seat_keys": [_seat(*MINTED[0])]})
    got = _run(root)
    assert got.returncode == 1
    assert "register-seat-row-unresolved" in _register_codes(got.stdout)


def test_an_entry_naming_an_uncommissioned_body_is_refused(tmp_path):
    """Design D8: the enforceable meaning of "an unknown seat" here. The
    council's seat ROSTER is governed in codexFactory and this reader has no
    read path into it, so the check is against the body this register
    commissions."""
    root = _tree(tmp_path / "consumer", top={"seat_keys": [
        _seat(*MINTED[0], council_ref="agent:some-other-council",
              council_id="some_other_council")]})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-seat-council-mismatch"}


def test_two_spellings_naming_different_bodies_are_refused(tmp_path):
    """`council_ref` anchors the authority in this register; `council_id` is
    projected VERBATIM into the runtime, which keys its seat lookup on it. A
    disagreement between them is a projection naming a body this row does not
    commission — the failure that would silently turn the operator's projection
    step back into a translation."""
    root = _tree(tmp_path / "consumer", top={
        "seat_keys": [_seat(*MINTED[0], council_id="some_other_council")]})
    got = _run(root)
    assert got.returncode == 1
    assert _register_codes(got.stdout) == {"register-seat-council-spelling"}


# ------------------- the cap, WITHDRAWN and replaced (v1.5) ------------------

def test_a_second_authority_row_is_not_refused_on_count(tmp_path):
    """AMENDED at wallet-v1.5, and the amendment is why this test still exists.

    It read `test_a_second_authority_row_is_still_refused` and asserted
    `register-minimal-shape-exceeded`. The change
    `widen-register-reader-for-a-second-council` (ratified 2026-09-06) amends
    this suite's own requirement — the count bound is WITHDRAWN and replaced by
    three invariants, and the refusal is RETIRED BY NAME (Q-WRR-1) — because
    openxFactory's ratified register act commissions a SECOND body that cannot
    descend from the first row. Deleting the test would leave the widened reader
    with one assertion fewer than the narrow one had, so it is converted: the
    withdrawn half is asserted ABSENT, and the half that replaced it is asserted
    PRESENT.

    The first fixture's second row commissions the SAME holder as the first.
    That shape has never been adjudicated by this reader and this change adds no
    code for it, so the assertion here is narrowly about the withdrawn COUNT
    refusal; `tests/widen_register_reader/` carries the two-BODY probes.
    """
    root = _tree(tmp_path / "consumer",
                 rows=[ROW, dict(ROW, row_id="row-mrc-probe-2")],
                 top={"seat_keys": _seats()})
    got = _run(root)
    assert "register-minimal-shape-exceeded" not in got.stdout, got.stdout
    assert "AUTHORITY rows" not in got.stdout, got.stdout

    # ...and what stands in its place: a second row that does NOT resolve end to
    # end is still refused, on RESOLUTION rather than on breadth. This is the
    # probe that makes withdrawing the count safe.
    unresolved = dict(ROW, row_id="row-mrc-probe-2",
                      holder_ref="agent:a-body-this-grant-does-not-name")
    root = _tree(tmp_path / "unresolved", rows=[ROW, unresolved],
                 top={"seat_keys": _seats()})
    got = _run(root)
    assert got.returncode == 1, got.stdout
    assert "register-grant-mismatch" in _register_codes(got.stdout), got.stdout


def test_the_consumer_gate_conjunction_still_holds(tmp_path):
    """openxFactory's positive-proof step, asserted here so a reader edit cannot
    silently de-advise it.

    That step greps for the `repo scan:` note, the anchored `intake register
    read:` note, the ABSENCE of the "no intake register at this tree" note, and
    the absence of any `[register-*]` finding. Every new code in this change is
    inside `register-[a-z-]+`, so the negative half reaches them with no edit in
    that repository.
    """
    root = _tree(tmp_path / "consumer", top={"seat_keys": _seats()})
    got = _run(root)
    assert got.returncode == 0, got.stdout
    assert re.search(r"^note  repo scan: \d+ openxWallet artifact",
                     got.stdout, re.M), got.stdout
    assert re.search(r"^note  intake register read: "
                     r"governance/review-authority/register\.yaml "
                     r"\(\d+ row\(s\)\)$", got.stdout, re.M), got.stdout
    assert "no intake register at this tree" not in got.stdout
    assert not re.search(r"\[register-[a-z-]+\]", got.stdout), got.stdout

    for code in ("register-top-level-unknown",
                 "register-staleness-bound-missing",
                 "register-staleness-bound-malformed",
                 "register-seat-keys-malformed",
                 "register-seat-key-malformed",
                 "register-seat-fingerprint-malformed",
                 "register-seat-fingerprint-mismatch",
                 "register-seat-duplicate",
                 "register-seat-row-unresolved",
                 "register-seat-council-mismatch",
                 "register-seat-council-spelling"):
        assert re.fullmatch(r"register-[a-z-]+", code), code
