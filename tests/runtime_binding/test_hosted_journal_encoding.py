"""Independent RFC8785 oracle and frozen pre-optimization v1 journal controls."""
import json
import os
from pathlib import Path
import sqlite3

import pytest

from workload_factory_binding.evidence import BindingError, byte_digest, canonical, digest
from workload_factory_binding_runtime.github_bootstrap.common import Decision, document, document_with_canonical
from workload_factory_binding_runtime.hosted.lifecycle_store import LifecycleStore, KINDS, _identity, _event_bytes

LEGACY = json.loads(Path(__file__).with_name("lifecycle-journal-v1.json").read_text())
LEGACY_KINDS = tuple(row["kind"] for row in LEGACY["rows"])
BODIES = [
    pytest.param({}, id="empty"),
    pytest.param({"nested": [{}, [], {"a": [None, True, False]}]}, id="nested"),
    pytest.param({"😀": "supplementary", "\ue000": {"é": "雪"}}, id="unicode"),
    pytest.param({"text": 'quote" slash\\ newline\n tab\t backspace\b'}, id="escaping"),
    pytest.param({"numbers": [-0.0, 1.0, 1e-7, 1e21, 9007199254740991]}, id="numbers"),
    pytest.param({"items": [{"value": "x" * 128, "index": i} for i in range(64)]}, id="larger"),
]


@pytest.mark.parametrize("kind", LEGACY_KINDS)
@pytest.mark.parametrize("body", BODIES)
def test_event_bytes_and_hash_equal_independent_canonical_oracle(kind, body):
    assert set(LEGACY_KINDS) == KINDS
    raw = canonical(body)
    decoded, encoded = document_with_canonical(raw)
    assert decoded == document(raw)
    assert encoded == raw
    event = {"sequence": 2048, "kind": kind, "data": decoded,
             "previous": "sha256:" + "a" * 64, "observed_at": 9007199254740991}
    result = _event_bytes(event["sequence"], kind, raw, event["previous"], event["observed_at"])
    assert result == canonical(event)
    assert byte_digest(result) == digest(event)


@pytest.mark.parametrize("raw", [b' {"z":0,"a":1} ', b'{"n":1.0}', rb'{"text":"\u0061"}', b' [ {}, null, true ] '])
def test_document_decoded_api_keeps_noncanonical_json_acceptance(raw):
    value = document(raw)
    decoded, encoded = document_with_canonical(raw)
    assert decoded == value
    assert encoded == canonical(value)
    assert encoded != raw


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'\xff'])
def test_both_document_apis_keep_same_malformed_refusal(raw):
    with pytest.raises(BindingError) as first:
        document(raw)
    with pytest.raises(BindingError) as second:
        document_with_canonical(raw)
    assert type(first.value) is type(second.value)
    assert first.value.args == second.value.args


def _old_journal(tmp_path):
    directory, witness = tmp_path/"primary", tmp_path/"primary-witness"
    directory.mkdir(mode=0o700); witness.mkdir(mode=0o700)
    (directory/"file-pins").mkdir(mode=0o700)
    for name in ("lifecycle.sqlite", "journal.lock"):
        fd = os.open(directory/name, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600); os.close(fd)
    with sqlite3.connect(directory/"lifecycle.sqlite") as db:
        for sql in LEGACY["schema"]:
            db.execute(sql)
        db.execute("INSERT INTO metadata VALUES (?,?,?,?)", LEGACY["metadata"])
        for row in LEGACY["rows"]:
            db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)", (row["sequence"], row["kind"],
                row["raw"].encode(), row["previous"], row["digest"], row["observed_at"]))
    values = [LEGACY["genesis"], *(row["digest"] for row in LEGACY["rows"])]
    for i, value in enumerate(values):
        fd = os.open(witness/f"{i:08d}.witness", os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as out:
            out.write(value.encode("ascii"))
    identity = _identity(directory, witness)
    return LifecycleStore(directory, witness, identity=identity, kind="primary"), directory, witness, identity


def test_frozen_old_journal_reopens_and_new_append_keeps_v1_hash_and_detached_copy(tmp_path):
    store, directory, witness, identity = _old_journal(tmp_path)
    expected = [{"kind":r["kind"], "data":json.loads(r["raw"]), "at":r["observed_at"]} for r in LEGACY["rows"]]
    assert store.events(decision=Decision(clock=lambda:1000)) == expected
    data = {"mutable": [1]}
    store.mutate(lambda events, append:append("action-observed", data), decision=Decision(clock=lambda:1000))
    data["mutable"].append(2)
    reopened = LifecycleStore(directory, witness, identity=identity, kind="primary")
    assert reopened.events(decision=Decision(clock=lambda:1000)) == [*expected, {"kind":"action-observed", "data":{"mutable":[1]}, "at":1000}]
    sequence = len(expected)+1
    old_oracle = digest({"sequence":sequence,"kind":"action-observed","data":{"mutable":[1]},
                         "previous":LEGACY["rows"][-1]["digest"],"observed_at":1000})
    with sqlite3.connect(directory/"lifecycle.sqlite") as db:
        assert db.execute("SELECT digest FROM events WHERE sequence=?", (sequence,)).fetchone() == (old_oracle,)
    assert (witness/f"{sequence:08d}.witness").read_bytes() == old_oracle.encode()


@pytest.mark.parametrize("raw", [b' {"a":1}', b'{"z":0,"a":1}', b'{"n":1.0}', rb'{"text":"\u0061"}',
    b'{"a":1,"a":2}', b'{"a":NaN}', b'[]'])
def test_forged_raw_hash_and_matching_witness_never_admit_noncanonical_or_invalid_body(tmp_path, raw):
    store, directory, witness, identity = _old_journal(tmp_path)
    row = LEGACY["rows"][-1]
    # Deliberately forge a self-consistent raw splice without using the new helper.
    # Strict body parsing/canonical equality must reject it BEFORE trusting hashes.
    header = canonical({"kind":row["kind"],"observed_at":row["observed_at"],
                        "previous":row["previous"],"sequence":row["sequence"]})
    forged = byte_digest(b'{"data":'+raw+b','+header[1:])
    with sqlite3.connect(directory/"lifecycle.sqlite") as db:
        db.execute("UPDATE events SET body=?,digest=? WHERE sequence=?", (raw, forged, row["sequence"]))
    (witness/f"{row['sequence']:08d}.witness").write_bytes(forged.encode())
    with pytest.raises(BindingError):
        store.events(decision=Decision(clock=lambda:1000))


@pytest.mark.parametrize("field", ["previous", "digest", "witness"])
def test_old_journal_chain_digest_and_witness_corruption_still_refuse(tmp_path, field):
    store, directory, witness, identity = _old_journal(tmp_path)
    row = LEGACY["rows"][-1];bad = "sha256:"+"0"*64
    if field == "witness":
        (witness/f"{row['sequence']:08d}.witness").write_bytes(bad.encode())
    else:
        with sqlite3.connect(directory/"lifecycle.sqlite") as db:
            db.execute("UPDATE events SET "+field+"=? WHERE sequence=?", (bad, row["sequence"]))
    with pytest.raises(BindingError):
        store.events(decision=Decision(clock=lambda:1000))
