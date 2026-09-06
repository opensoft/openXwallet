"""RED FIRST: the register reader cannot represent a SECOND commissioned body.

Measures the openXwallet change `widen-register-reader-for-a-second-council`
(capability `review-authority-register-reader`), openxFactory tasks §2 row 2.2 of
the ratified `register-gate-rules-council-seats` (PR #717 → `a59f2ae5`).

Lane: hermes-wallet-exercise

WHAT IS RED AND HOW. Two tests assert the TARGET behaviour and carry
`xfail(strict=True)`: they fail today, they are recorded as expected failures so
this repository's REQUIRED `pytest-suite` check stays green on a PROPOSAL pull
request that fixes nothing — and `strict=True` means the suite FAILS the moment
the reader is fixed and they start passing, so the fix slice cannot forget to
convert them. Landing them as plain failures instead would red-line a required
check on a candidate whose only exit is `--admin`, which is the ritual this whole
arc exists to end.

Beside each of those sits a test that PINS TODAY'S EXACT REFUSAL by code. Those
pass now and are the MEASUREMENT: `openspec/changes/.../design.md` D0 quotes the
reader's output, and these assert it, so the transcript in the design document is
checkable rather than quotable. Task §3.3 converts both classes in the same
commit as the fix.

THE TWO DEFECTS CANNOT BE ISOLATED BY ONE FIXTURE, and that is itself a finding.
Representing a second council REQUIRES a second authority row — `_check_seat_keys`
refuses an entry whose `council_ref` is not the authorizing row's `holder_ref` —
so any fixture that exercises the seat-name defect also trips the row-count
defect. They are separated here by DIFFERENCING two fixtures that differ in one
respect: with the second body's ONE non-colliding real seat (`GRC_DISJOINT`) the
reader refuses with the row-count code ALONE; with all FOUR of its real seats
(`GRC_SEATS`) it adds exactly three seat-duplicate refusals and nothing else.

Discipline copied from `tests/per_seat_register_entries/test_top_level_and_seat_keys.py`:
drive the script as a SUBPROCESS so the exit codes the workflows act on are the
ones under test, build every fixture under `tmp_path`, and assert NAMED CODES
rather than a non-zero exit, because a refusal for the wrong reason is a
different defect wearing the same colour.

THE FIXTURE KEYS. The merge-readiness halves are the REAL ones, copied from
codexFactory `hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`
(merged `78b8fa2`) — the same bytes openxFactory commits. The gate-rules halves
are DETERMINISTIC SYNTHETIC keys derived in this module: no gate-rules key
exists yet, because minting them is Brett's operator act (openxFactory task
3.2), and a real-looking invented value in this repository would be a key no
ceremony produced. `test_the_probe_keys_recompute` proves both sets rather than
trusting them.
"""

from __future__ import annotations

import base64
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate-openxwallet.py"

ROWS_NOTE = re.compile(
    r"^note  intake register read: (\S+) \((\d+) row\(s\)\)$", re.M)
SEAT_NOTE = re.compile(
    r"^note  intake register: (\d+) of (\d+) per-seat signing key\(s\) "
    r"adjudicated and resolved$", re.M)

# The two spellings of each body, both recorded on purpose: `council_ref` is the
# AUTHORITY ATTACHMENT (it must equal the authorizing row's `holder_ref`), and
# `council_id` is the RUNTIME NAME, carried verbatim into hermes-install's
# projection, which keys its seat lookup on the exact pair
# `(council_id, seat_id)`.
MRC_REF, MRC_ID = "agent:merge-readiness-council", "merge_readiness_council"
GRC_REF, GRC_ID = "agent:gate-rules-council", "gate_rules_council"

# Copied verbatim from the 2026-08-28 mint record.
MRC_MINTED = (
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

# The four seats openxFactory's `register-gate-rules-council-seats` design D1
# registers, read from codexFactory `hermes/domain/review-councils/gate-rules.yaml`
# BY IDENTIFIER. THREE OF THEM COLLIDE with merge-readiness seat names — which is
# defect 2, and which is why two bodies cannot share a global seat namespace.
GRC_SEATS = ("lead-architect", "lead-security", "lead-quality",
             "company-policy-lead")
GRC_COLLIDING = tuple(s for s in GRC_SEATS
                      if s in {m[0] for m in MRC_MINTED})
GRC_DISJOINT = tuple(s for s in GRC_SEATS if s not in GRC_COLLIDING)

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _base58btc(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, rem = divmod(n, 58)
        out = _B58[rem] + out
    for byte in raw:
        if byte != 0:
            break
        out = "1" + out
    return out


def _derive(label: str) -> tuple[str, str, str]:
    """A deterministic 32-byte value, spelled the three ways the tree needs it.

    Returns (public_key as canonical unpadded base64url, `sha256:` fingerprint,
    did:key multibase). Derivation, not invention: nothing here is presented as
    a minted key, and `test_the_probe_keys_recompute` asserts every relation
    this function claims.
    """
    raw = hashlib.sha256(label.encode("utf-8")).digest()
    pub = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    fingerprint = "sha256:" + hashlib.sha256(raw).hexdigest()
    did = "z" + _base58btc(bytes([0xed, 0x01]) + raw)
    return pub, fingerprint, did

GRC_PROBE = {seat: _derive(f"openXwallet-probe/{GRC_ID}/{seat}")
             for seat in GRC_SEATS}
GRC_ROOT = _derive(f"openXwallet-probe/{GRC_ID}/root")
MRC_ROOT_DID = "z6Mko2FefScUQg9opCriwQmjfcb3Qjnb5bN49hQsEVMo6gee"

EXPIRY = "2099-11-23T12:00:00Z"


# --------------------------------- the tree ---------------------------------

def _wallet(wallet_id: str, holder_ref: str, did: str, key_id: str) -> dict:
    return {
        "schema_version": 1,
        "kind": "xfactory_wallet_record",
        "wallet_id": wallet_id,
        "holder": {"holder_id": holder_ref, "holder_class": "agent"},
        "key_reference": {"did": f"did:key:{did}", "key_id": key_id,
                          "signature_algorithm": "ed25519"},
        "custody": {"model": "holder_readable", "registry_version": 1},
        "state": "active",
    }


def _grant(grant_id: str, wallet_ref: str, holder_ref: str,
           **over: object) -> dict:
    grant = {
        "schema_version": 1,
        "kind": "xfactory_wallet_grant",
        "grant_id": grant_id,
        "audience": {"wallet_ref": wallet_ref, "holder_ref": holder_ref},
        "scope": {"acts": ["review"], "authority_tier": "act",
                  "objects": ["opensoft/openxFactory"]},
        "expires_at": EXPIRY,
        "issued_at": "2026-08-25T12:45:00Z",
        "issued_by": "Brett.Heap@opensoft.one",
        "state": "active",
    }
    grant.update(over)
    return grant


def _row(row_id: str, holder_ref: str, wallet_ref: str,
         grant_ref: str) -> dict:
    return {
        "row_id": row_id,
        "holder_ref": holder_ref,
        "wallet_ref": wallet_ref,
        "target_repo": "opensoft/openxFactory",
        "act": "review",
        "authority_tier": "act",
        "grant_ref": grant_ref,
        "expires_at": EXPIRY,
        "state": "active",
    }


def _attestation(wallet_ref: str) -> dict:
    return {
        "attestation_id": f"attest-custody-{wallet_ref}",
        "subject_wallet_ref": wallet_ref,
        "custody_model_attested": "holder_readable",
        "verified_by": {"name": "Brett Heap",
                        "role": "responsible operator",
                        "standing": "Human Escalation Contract"},
        "verified_at": "2026-08-24T12:00:00Z",
        "verified_against": {"method": "operator-minted ed25519 keypair",
                             "isolation_claimed": False},
    }


def _seat(seat_id: str, council_ref: str, council_id: str, public_key: str,
          fingerprint: str, row_id: str, **over: object) -> dict:
    entry = {
        "seat_id": seat_id,
        "council_ref": council_ref,
        "council_id": council_id,
        "key_id": f"key-{council_id}-seat-{seat_id}-0001",
        "public_key": public_key,
        "key_fingerprint": fingerprint,
        "authorizing_row": row_id,
    }
    entry.update(over)
    return entry


MRC_WALLET = "wal-agent-mrc-probe"
GRC_WALLET = "wal-agent-grc-probe"
MRC_GRANT = "grant-mrc-probe"
GRC_GRANT = "grant-grc-probe"
MRC_ROW = "row-mrc-probe"
GRC_ROW = "row-grc-probe"


def _mrc_seats() -> list[dict]:
    """The four entries openxFactory's register carries TODAY."""
    return [_seat(s, MRC_REF, MRC_ID, pub, fp, MRC_ROW)
            for s, pub, fp in MRC_MINTED]


def _grc_seats(seats: tuple[str, ...] = GRC_SEATS) -> list[dict]:
    return [_seat(s, GRC_REF, GRC_ID, GRC_PROBE[s][0], GRC_PROBE[s][1],
                  GRC_ROW) for s in seats]


def _tree(root: Path, *, second_body: bool, seat_keys: list[dict] | None,
          grc_grant_over: dict | None = None) -> Path:
    """A register tree the validator adjudicates, shaped on the LIVE one.

    `second_body` adds the whole second commissioned body — row, wallet, root
    grant and custody attestation — because a second row that resolves to
    nothing would measure the wrong defect: the reader is supposed to refuse
    that one, and does, before and after the widening.
    """
    records = root / "governance" / "wallets"
    records.mkdir(parents=True)
    ra = root / "governance" / "review-authority"
    (ra / "attestations").mkdir(parents=True)

    (records / "wal-mrc.yaml").write_text(
        yaml.safe_dump(_wallet(MRC_WALLET, MRC_REF, MRC_ROOT_DID,
                               "key-mrc-probe")), encoding="utf-8")
    (records / "grant-mrc.yaml").write_text(
        yaml.safe_dump(_grant(MRC_GRANT, MRC_WALLET, MRC_REF)),
        encoding="utf-8")
    (ra / "attestations" / "attest-mrc.yaml").write_text(
        yaml.safe_dump(_attestation(MRC_WALLET)), encoding="utf-8")
    rows = [_row(MRC_ROW, MRC_REF, MRC_WALLET, MRC_GRANT)]

    if second_body:
        (records / "wal-grc.yaml").write_text(
            yaml.safe_dump(_wallet(GRC_WALLET, GRC_REF, GRC_ROOT[2],
                                   "key-grc-probe")), encoding="utf-8")
        (records / "grant-grc.yaml").write_text(
            yaml.safe_dump(_grant(GRC_GRANT, GRC_WALLET, GRC_REF,
                                  **(grc_grant_over or {}))),
            encoding="utf-8")
        (ra / "attestations" / "attest-grc.yaml").write_text(
            yaml.safe_dump(_attestation(GRC_WALLET)), encoding="utf-8")
        rows.append(_row(GRC_ROW, GRC_REF, GRC_WALLET, GRC_GRANT))

    doc: dict = {"register_version": 1, "revocation_staleness_bound": "P7D",
                 "rows": rows}
    if seat_keys is not None:
        doc["seat_keys"] = seat_keys
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


def _register_lines(out: str, code: str) -> list[str]:
    return [ln for ln in out.splitlines() if ln.startswith(f"ERROR [{code}]")]


def _rows_read(out: str) -> str:
    """The `intake register read:` note's row count.

    A separate assertion for "the note is there" and for "it says N", because a
    missing note and a wrong count are different defects and a composite
    assertion would report them as one.
    """
    note = ROWS_NOTE.search(out)
    assert note, out
    return note.group(2)


def _seats_adjudicated(out: str) -> tuple[str, str]:
    """The seat note's (ADJUDICATED, recorded) pair, note-presence asserted first."""
    note = SEAT_NOTE.search(out)
    assert note, out
    return note.group(1), note.group(2)


# ---------------------------- the fixture itself ----------------------------

def test_the_probe_keys_recompute():
    """Asserted independently of the reader.

    A stale table would otherwise let every negative below pass for the wrong
    reason — the reason `test_the_mint_records_four_keys_recompute` exists one
    directory over.
    """
    for seat_id, public_key, fingerprint in MRC_MINTED:
        raw = base64.urlsafe_b64decode(public_key + "=")
        assert len(raw) == 32, seat_id
        assert "sha256:" + hashlib.sha256(raw).hexdigest() == fingerprint, \
            seat_id

    for seat_id, (public_key, fingerprint, did) in GRC_PROBE.items():
        raw = base64.urlsafe_b64decode(public_key + "=")
        assert len(raw) == 32, seat_id
        assert len(public_key) == 43, seat_id
        # CANONICAL, not merely charset-legal: the reader re-encodes and
        # compares, so a probe with trailing bits set would be refused by SHAPE
        # and would measure the wrong defect.
        assert base64.urlsafe_b64encode(raw).decode().rstrip("=") == \
            public_key, seat_id
        assert "sha256:" + hashlib.sha256(raw).hexdigest() == fingerprint, \
            seat_id
        assert did.startswith("z"), seat_id

    # The collision this whole change is about, asserted rather than described.
    assert set(GRC_COLLIDING) == {"lead-security", "lead-quality",
                                  "company-policy-lead"}
    assert GRC_DISJOINT == ("lead-architect",)
    # And the key material never collides, so `key_id` / `key_fingerprint`
    # global uniqueness is not what these fixtures are probing.
    assert len({m[2] for m in MRC_MINTED} |
               {v[1] for v in GRC_PROBE.values()}) == 8


# ------------------- the regression: today's shape, unchanged ----------------

def test_the_live_one_row_register_stays_clean(tmp_path):
    """PASSES TODAY AND MUST PASS AFTER — openxFactory task 2.9's gate.

    One authority row, four per-seat entries under one council: the exact shape
    openxFactory's register carries at `origin/main`, whose measured output at
    the pinned reader is `1 row(s)`, `4 of 4`, zero findings, rc=0 plain and
    under `--strict`.

    This is not hygiene. openxFactory advances its pin BEFORE its register
    moves, and its own task 2.9 requires that advance to be provably NEUTRAL —
    so if the widened reader changed any line of this output, the sequence
    openxFactory ratified would have no valid ordering.
    """
    root = _tree(tmp_path / "consumer", second_body=False,
                 seat_keys=_mrc_seats())
    plain, strict = _run(root), _run(root, "--strict")
    assert plain.returncode == 0, plain.stdout + plain.stderr
    assert strict.returncode == 0, strict.stdout + strict.stderr
    assert "WARN" not in strict.stdout, strict.stdout
    assert not _register_codes(plain.stdout), plain.stdout

    assert _rows_read(plain.stdout) == "1", plain.stdout
    assert _seats_adjudicated(plain.stdout) == ("4", "4"), plain.stdout


# ------------- defect 1: the row-count cap, isolated by differencing ---------

def test_a_second_commissioned_body_is_refused_today(tmp_path):
    """THE MEASUREMENT for defect 1, pinned by code.

    A second body whose row resolves END TO END — its own wallet, its own root
    grant backing that row field for field, its own custody attestation, an
    unexpired computed expiry — and whose one registered seat name collides with
    nothing. The ONLY thing wrong with this register is that it has two rows.

    Converted by task §3.3 when `REGISTER_MVP_SINGLE_ROW` is retired.
    """
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + _grc_seats(GRC_DISJOINT))
    got = _run(root)
    assert got.returncode == 1, got.stdout
    assert _register_codes(got.stdout) == {"register-minimal-shape-exceeded"}, \
        got.stdout
    assert "2 AUTHORITY rows" in got.stdout, got.stdout
    # The second body's seat IS adjudicated: the refusal is about the file's
    # breadth, not about that entry.
    assert _seats_adjudicated(got.stdout) == ("5", "5"), got.stdout


@pytest.mark.xfail(strict=True, reason=(
    "openxFactory register-gate-rules-council-seats task 2.4 / Q-GRC-5: "
    "REGISTER_MVP_SINGLE_ROW refuses a second authority row. Retired in "
    "favour of the three invariants; convert this test in the same commit."))
def test_a_second_commissioned_body_resolving_end_to_end_is_admitted(tmp_path):
    """THE TARGET for defect 1. Fails today; must pass after the fix."""
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + _grc_seats(GRC_DISJOINT))
    got = _run(root)
    assert got.returncode == 0, got.stdout
    assert not _register_codes(got.stdout), got.stdout
    assert _rows_read(got.stdout) == "2", got.stdout


# --------- defect 2: global seat-name uniqueness, isolated by differencing ---

def test_two_councils_seating_one_role_name_are_refused_today(tmp_path):
    """THE MEASUREMENT for defect 2, pinned by code AND by count.

    The FULL ACT Brett's walk would carry: all four gate-rules seats beside all
    four merge-readiness ones. It differs from the fixture above in exactly one
    respect — three more seat entries, whose names another body already records
    — and it adds exactly three refusals, one per colliding name. That
    difference IS the isolation: `register-seat-duplicate` is caused by the
    names and by nothing else in the fixture.

    Converted by task §3.3 when the duplicate table is keyed on the pair.
    """
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + _grc_seats())
    got = _run(root)
    assert got.returncode == 1, got.stdout
    assert _register_codes(got.stdout) == {
        "register-minimal-shape-exceeded", "register-seat-duplicate"}, \
        got.stdout

    duplicates = _register_lines(got.stdout, "register-seat-duplicate")
    assert len(duplicates) == len(GRC_COLLIDING) == 3, got.stdout
    for seat_id in GRC_COLLIDING:
        assert any(f"seat_id {seat_id!r} is already recorded" in ln
                   for ln in duplicates), (seat_id, got.stdout)
        # The defect in one line: the entry it collides with belongs to a
        # DIFFERENT body, and the refusal cannot say so because the table has
        # no council in its key.
        assert not any(GRC_ID in ln for ln in duplicates), got.stdout

    # openxFactory task 2.8 moves its consumer gate's literal assertion to
    # `8 of 8`. Today the reader stands behind five of the eight recorded keys.
    assert _seats_adjudicated(got.stdout) == ("5", "8"), got.stdout


@pytest.mark.xfail(strict=True, reason=(
    "openxFactory register-gate-rules-council-seats task 2.3 / Q-GRC-5: "
    "_check_seat_keys keys its duplicate table on seat_id ALONE across the "
    "whole file, so three of gate-rules' four seats are refused as duplicates "
    "of merge-readiness seats. Re-key on (council_id, seat_id); convert this "
    "test in the same commit."))
def test_two_councils_may_seat_the_same_role_name(tmp_path):
    """THE TARGET for defect 2. Fails today; must pass after the fix.

    Two bodies commonly seat the same ROLE — `lead-security` is a role, not a
    person — and hermes-install's `derive_projection` already keys its own
    duplicate table on `(council_id, seat_id)`. The reader adopts the key its
    consumer already uses.
    """
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + _grc_seats())
    got = _run(root)
    assert got.returncode == 0, got.stdout
    assert not _register_codes(got.stdout), got.stdout
    assert _rows_read(got.stdout) == "2", got.stdout
    assert _seats_adjudicated(got.stdout) == ("8", "8"), got.stdout


# ---------- what the widening must NOT relax: the refusals that stay ---------

def test_one_council_naming_a_seat_twice_is_refused(tmp_path):
    """PASSES TODAY AND MUST PASS AFTER.

    The fix NARROWS this refusal's trigger; it does not remove it. One council
    with two entries for one seat has two answers to "which key is that seat's
    root", and picking either is choosing which authority to believe.
    """
    twice = _mrc_seats()
    twice.append(_seat("lead-security", MRC_REF, MRC_ID,
                       GRC_PROBE["lead-security"][0],
                       GRC_PROBE["lead-security"][1], MRC_ROW,
                       key_id="key-mrc-seat-lead-security-0002"))
    root = _tree(tmp_path / "consumer", second_body=False, seat_keys=twice)
    got = _run(root)
    assert got.returncode == 1, got.stdout
    assert "register-seat-duplicate" in _register_codes(got.stdout), got.stdout
    assert any("seat_id 'lead-security' is already recorded" in ln
               for ln in _register_lines(got.stdout,
                                         "register-seat-duplicate")), got.stdout


@pytest.mark.parametrize("field", ["key_id", "key_fingerprint"])
def test_key_id_and_fingerprint_stay_globally_unique(tmp_path, field):
    """PASSES TODAY AND MUST PASS AFTER — openxFactory task 2.3 says so.

    A key is one key. Two bodies presenting it are two claims on one identity,
    and a per-council key namespace would let one private half sign for two
    bodies with no way to attribute a seat return. So `seat_id` moves to the
    pair and these two do NOT.
    """
    collide = _mrc_seats()[0][field]
    grc = _grc_seats(GRC_DISJOINT)
    grc[0][field] = collide
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + grc)
    got = _run(root)
    assert got.returncode == 1, got.stdout
    assert "register-seat-duplicate" in _register_codes(got.stdout), got.stdout
    assert any(f"{field} {collide!r} is already recorded" in ln
               for ln in _register_lines(got.stdout,
                                         "register-seat-duplicate")), got.stdout


def test_a_second_row_that_does_not_resolve_is_refused(tmp_path):
    """PASSES TODAY AND MUST PASS AFTER — the widening is not a relaxation.

    The second body's grant does not back its row (the grant's audience names
    another wallet), so the row is refused on RESOLUTION and not on breadth.
    This is the probe that makes retiring the count bound safe: after the fix
    the row-count code is gone, and this refusal is what still stands between a
    second row and a register that commissions nothing.
    """
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + _grc_seats(GRC_DISJOINT),
                 grc_grant_over={"audience": {"wallet_ref": MRC_WALLET,
                                              "holder_ref": GRC_REF}})
    got = _run(root)
    assert got.returncode == 1, got.stdout
    assert "register-grant-mismatch" in _register_codes(got.stdout), got.stdout
