"""The register reader represents a SECOND commissioned body — GREEN, converted.

Realizes the openXwallet change `widen-register-reader-for-a-second-council`
(capability `review-authority-register-reader`), ratified 2026-09-06T23:25:11Z,
openxFactory tasks §2 rows 2.2–2.5 of the ratified
`register-gate-rules-council-seats` (PR #717 → `a59f2ae5`).

Lane: hermes-wallet-exercise

WHAT WAS RED, AND WHAT IT BECAME. This module landed with the proposal as the
MEASUREMENT of two live defects: two tests asserted the TARGET behaviour under
`xfail(strict=True)`, and beside each sat a test PINNING THE EXACT REFUSAL the
reader emitted that day. The fix slice (tasks §3.1–§3.3) flipped the first pair
to plain assertions and CONVERTED the second pair rather than deleting them —
deleting a measurement leaves a widened reader with fewer assertions than the
narrow one had. What they assert now:

  * `test_the_retired_row_count_refusal_is_emitted_by_nothing` — was the
    row-count measurement. `register-minimal-shape-exceeded` is RETIRED BY NAME
    (Q-WRR-1), so this asserts the string is emitted on none of the shapes that
    used to trigger it AND is gone from the reader's own source: a retired code
    that still exists in the program is a code that can come back.
  * `test_a_per_council_duplicate_still_refuses_and_names_the_council` — was the
    seat-name measurement. The trigger NARROWED and the refusal stayed, so this
    asserts the surviving half: one council with two answers for one seat is
    still refused, the message names the council, and the OTHER body's
    identically-named seat is untouched.

THE TWO DEFECTS COULD NOT BE ISOLATED BY ONE FIXTURE, and that is itself a
finding, kept here because the fixtures still rest on it. Representing a second
council REQUIRES a second authority row — `_check_seat_keys` refuses an entry
whose `council_ref` is not the authorizing row's `holder_ref` — so any fixture
that exercised the seat-name defect also tripped the row-count defect. They were
separated by DIFFERENCING two fixtures that differ in one respect: the second
body's ONE non-colliding seat (`GRC_DISJOINT`) against all FOUR (`GRC_SEATS`),
which added exactly three refusals and nothing else. Both fixtures now validate
CLEAN, and the difference between them is the three names.

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

import ast
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

RETIRED_ROW_COUNT_CODE = "register-minimal-shape-exceeded"


def test_the_retired_row_count_refusal_is_emitted_by_nothing(tmp_path):
    """CONVERTED from the defect-1 measurement (task §3.3).

    It asserted `register-minimal-shape-exceeded` on a two-row register. Q-WRR-1
    RETIRES that code BY NAME rather than re-scoping it — a pinned finding code
    that changes meaning under a stable string is a worse compatibility break
    than one that disappears, because nothing fails to warn anybody — so what
    survives of the measurement is the retirement itself, asserted two ways.

    The SOURCE assertion is not belt-and-braces. A code absent from every output
    of the fixtures at hand but still present in the program is a code that can
    come back on a shape nobody probed, and the CHANGELOG's removed-refusal note
    would then be false. It is asserted over the reader's STRING LITERALS rather
    than over its text, because the retirement is a decision the reader should
    still be able to NARRATE: a comment or a docstring naming a retired code is
    the record of why it went, while a literal equal to it is something that can
    be emitted by `f.error` or asserted by a self-test probe.
    """
    literals = {node.value
                for node in ast.walk(ast.parse(
                    VALIDATOR.read_text(encoding="utf-8")))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert RETIRED_ROW_COUNT_CODE not in literals, \
        f"{RETIRED_ROW_COUNT_CODE} is still a string literal in {VALIDATOR}"

    # Every shape that used to emit it: the two-row register with one
    # non-colliding seat, and the full act with all eight seats.
    for label, seats in (("disjoint", _mrc_seats() + _grc_seats(GRC_DISJOINT)),
                         ("full act", _mrc_seats() + _grc_seats())):
        root = _tree(tmp_path / label.replace(" ", "-"), second_body=True,
                     seat_keys=seats)
        got = _run(root)
        assert RETIRED_ROW_COUNT_CODE not in got.stdout, (label, got.stdout)
        assert "AUTHORITY rows" not in got.stdout, (label, got.stdout)
        assert got.returncode == 0, (label, got.stdout)


def test_a_second_commissioned_body_resolving_end_to_end_is_admitted(tmp_path):
    """THE TARGET for defect 1, flipped from `xfail(strict=True)` by task §3.3.

    A second body whose row resolves END TO END — its own wallet, its own root
    grant backing that row field for field, its own custody attestation, an
    unexpired computed expiry — and whose one registered seat name collides with
    nothing. Admitted, and the note reports the rows it read.
    """
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + _grc_seats(GRC_DISJOINT))
    got = _run(root)
    assert got.returncode == 0, got.stdout
    assert not _register_codes(got.stdout), got.stdout
    assert _rows_read(got.stdout) == "2", got.stdout


# --------- defect 2: global seat-name uniqueness, isolated by differencing ---

def test_a_per_council_duplicate_still_refuses_and_names_the_council(tmp_path):
    """CONVERTED from the defect-2 measurement (task §3.3).

    It asserted three refusals on the full act, one per name gate-rules shares
    with merge-readiness, and that none of them could name the council. The
    trigger NARROWED and the refusal STAYED, so what the measurement becomes is
    the surviving half, in the shape only a widened reader can take: TWO bodies
    in one register, one of which records a seat TWICE.

    Three assertions, because they are three different facts. The duplicate is
    refused; the message names the council, which is what stops it being read as
    a collision with the other body's seat; and the other body's identically
    named seat is NOT reported — the discriminating power of the pair key, which
    a test asserting only the refusal would not have measured.
    """
    twice = _grc_seats() + [_seat(
        "lead-security", GRC_REF, GRC_ID,
        *_derive(f"openXwallet-probe/{GRC_ID}/lead-security/second-answer")[:2],
        GRC_ROW, key_id=f"key-{GRC_ID}-seat-lead-security-0002")]
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + twice)
    got = _run(root)
    assert got.returncode == 1, got.stdout
    assert _register_codes(got.stdout) == {"register-seat-duplicate"}, got.stdout

    duplicates = _register_lines(got.stdout, "register-seat-duplicate")
    assert len(duplicates) == 1, got.stdout
    assert "seat_id 'lead-security' is already recorded" in duplicates[0], \
        got.stdout
    assert f"under council {GRC_ID!r}" in duplicates[0], duplicates[0]
    # merge-readiness seats `lead-security` too, and is untouched: eight of the
    # nine recorded entries are adjudicated, and the refused one is the ninth.
    assert MRC_ID not in duplicates[0], duplicates[0]
    assert _seats_adjudicated(got.stdout) == ("8", "9"), got.stdout


def test_two_councils_may_seat_the_same_role_name(tmp_path):
    """THE TARGET for defect 2, flipped from `xfail(strict=True)` by task §3.3.

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
    duplicates = _register_lines(got.stdout, "register-seat-duplicate")
    assert any("seat_id 'lead-security' is already recorded" in ln
               for ln in duplicates), got.stdout
    # The message names the council even in a ONE-BODY register: the refusal
    # says which body has two answers, so it is never read as a collision with
    # a different body's seat.
    assert any(f"under council {MRC_ID!r}" in ln for ln in duplicates), \
        got.stdout


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


def test_a_seat_entry_attached_to_another_bodys_row_is_refused(tmp_path):
    """INVARIANT (ii), in the shape only a MULTI-BODY register can take.

    With one authority row this mistake was unreachable — every entry either
    named that row or named nothing. With two, an entry can attach to a row that
    commissions a DIFFERENT body, which would record the second council's seats
    as descending from the first council's authority. That is false rather than
    untidy, and it is the invariant that keeps a WIDER register from being a
    LOOSER one now that nothing counts rows.
    """
    misattached = [dict(entry, authorizing_row=MRC_ROW)
                   for entry in _grc_seats(GRC_DISJOINT)]
    root = _tree(tmp_path / "consumer", second_body=True,
                 seat_keys=_mrc_seats() + misattached)
    got = _run(root)
    assert got.returncode == 1, got.stdout
    assert _register_codes(got.stdout) == {"register-seat-council-mismatch"}, \
        got.stdout
    assert _rows_read(got.stdout) == "2", got.stdout
    # The refused entry is excluded from the adjudicated count, which is what
    # makes the note evidence rather than a restatement of how many were parsed.
    assert _seats_adjudicated(got.stdout) == ("4", "5"), got.stdout


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
