"""Retained lifecycle events with a separately retained commit witness.

Explicit initialization is an operator/fixture capability, never an open fallback.
The witness detects database rollback within the selected private identities; it
is not protection from a trusted administrator restoring both retained stores.
"""
from contextlib import closing
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import secrets
import sqlite3
import stat
import time
from workload_factory_binding.evidence import BindingError, canonical, digest, integer, require
from ..github_bootstrap.common import document

ERROR = "hosted-lifecycle-refused"
DB = "lifecycle.sqlite"
MAX_EVENTS = 2048
KINDS = frozenset({"clock", "registration", "generation", "final-plan", "stage-release",
    "action-claimed", "action-observed", "lease-closed", "stage-intake", "final-intake",
    "stage-ack", "takeover-ack", "cleanup-audit", "cleanup-request", "prestart-closed", "file-retired"})
SCHEMA = (
    "CREATE TABLE metadata (version INTEGER NOT NULL, kind TEXT NOT NULL, nonce TEXT NOT NULL, highwater INTEGER NOT NULL)",
    "CREATE TABLE events (sequence INTEGER PRIMARY KEY, kind TEXT NOT NULL, body BLOB NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL, observed_at INTEGER NOT NULL)",
)


def _private(path, directory=False):
    info = path.lstat()
    require((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
            and info.st_uid == os.geteuid() and not info.st_mode & 0o077, ERROR)
    return info.st_dev, info.st_ino


def _identity(directory, witness):
    require(directory.absolute() == directory.resolve() and witness.absolute() == witness.resolve()
            and directory != witness and not directory.is_relative_to(witness)
            and not witness.is_relative_to(directory), ERROR)
    for suffix in ("-journal", "-wal", "-shm"):
        p = directory / (DB + suffix)
        if suffix == "-journal":
            try:
                _private(p)
            except FileNotFoundError:
                # A concurrent DELETE-mode commit may remove this optional
                # artifact before the ownership lock is acquired.
                pass
        else:
            require(not p.exists() and not p.is_symlink(), ERROR)
    return (_private(directory, True), _private(directory / DB), _private(directory / "journal.lock"),
            _private(witness, True), _private(witness / "00000000.witness"), _private(directory / "file-pins", True))


def _sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_witness(directory, sequence, value):
    fd = os.open(directory / f"{sequence:08d}.witness", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        raw = value.encode("ascii")
        require(os.write(fd, raw) == len(raw), ERROR)
        os.fsync(fd)
    finally:
        os.close(fd)
    _sync_directory(directory)


class LifecycleStore:
    @classmethod
    def initialize(cls, directory, witness, *, kind):
        try:
            require(kind in ("primary", "scheduler", "audit"), ERROR)
            directory, witness = Path(directory).absolute(), Path(witness).absolute()
            require(directory.resolve() == directory and witness.resolve() == witness
                    and directory != witness and not directory.is_relative_to(witness)
                    and not witness.is_relative_to(directory), ERROR)
            directory.mkdir(mode=0o700)
            witness.mkdir(mode=0o700)
            (directory / "file-pins").mkdir(mode=0o700)
            for name in (DB, "journal.lock"):
                fd = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                os.close(fd)
            nonce = secrets.token_hex(32)
            with closing(sqlite3.connect(directory / DB)) as db, db:
                db.execute("PRAGMA synchronous=FULL")
                for sql in SCHEMA:
                    db.execute(sql)
                db.execute("INSERT INTO metadata VALUES (1,?,?,0)", (kind, nonce))
            _write_witness(witness, 0, digest({"version": 1, "kind": kind, "nonce": nonce}))
            _sync_directory(directory)
            return _identity(directory, witness)
        except Exception:
            raise BindingError(ERROR) from None

    def __init__(self, directory, witness, *, identity, kind):
        self.directory, self.witness = Path(directory).absolute(), Path(witness).absolute()
        self.identity, self.kind = identity, kind
        try:
            require(kind in ("primary", "scheduler", "audit")
                    and _identity(self.directory, self.witness) == identity, ERROR)
            with closing(sqlite3.connect((self.directory / DB).as_uri() + "?mode=rw", uri=True)) as db:
                require(db.execute("SELECT version,kind FROM metadata").fetchall() == [(1, kind)], ERROR)
        except Exception:
            raise BindingError(ERROR) from None

    def _load(self, db):
        actual = tuple(x[0] for x in db.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"))
        require(actual == tuple(sorted(SCHEMA, key=lambda x: x.split()[2])), ERROR)
        metadata = db.execute("SELECT version,kind,nonce,highwater FROM metadata").fetchall()
        require(len(metadata) == 1 and metadata[0][:2] == (1, self.kind), ERROR)
        _, _, nonce, highwater = metadata[0]
        require(type(nonce) is str and len(nonce) == 64 and all(c in "0123456789abcdef" for c in nonce)
                and integer(highwater), ERROR)
        previous = digest({"version": 1, "kind": self.kind, "nonce": nonce})
        witnesses = list(self.witness.iterdir())
        rows = db.execute("SELECT sequence,kind,body,previous,digest,observed_at FROM events ORDER BY sequence LIMIT ?", (MAX_EVENTS + 1,)).fetchall()
        require(len(rows) <= MAX_EVENTS and len(witnesses) == len(rows) + 1
                and {p.name for p in witnesses} == {f"{i:08d}.witness" for i in range(len(rows) + 1)}, ERROR)
        require((self.witness / "00000000.witness").read_bytes() == previous.encode("ascii"), ERROR)
        events, last_time = [], 0
        for expected, (sequence, kind, raw, prior, measured, at) in enumerate(rows, 1):
            require(sequence == expected and kind in KINDS and type(raw) is bytes
                    and 0 < len(raw) <= 65536 and integer(at) and last_time <= at <= highwater, ERROR)
            value = document(raw)
            require(type(value) is dict and canonical(value) == raw and prior == previous, ERROR)
            event = {"sequence": sequence, "kind": kind, "data": value, "previous": prior, "observed_at": at}
            require(digest(event) == measured, ERROR)
            p = self.witness / f"{sequence:08d}.witness"
            _private(p)
            require(p.read_bytes() == measured.encode("ascii"), ERROR)
            events.append({"kind": kind, "data": value, "at": at})
            previous, last_time = measured, at
        require(highwater == last_time, ERROR)
        return events, previous, highwater

    def mutate(self, operation, *, decision):
        db, lock = None, None
        try:
            decision.now()
            require(_identity(self.directory, self.witness) == self.identity, ERROR)
            lock = os.open(self.directory / "journal.lock", os.O_RDWR | os.O_NOFOLLOW)
            until = time.monotonic() + min(1, decision.remaining())
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    require(time.monotonic() < until, ERROR)
                    decision.now()
                    time.sleep(.005)
            require(_identity(self.directory, self.witness) == self.identity, ERROR)
            db = sqlite3.connect((self.directory / DB).as_uri() + "?mode=rw", uri=True,
                                 timeout=min(1, decision.remaining()), isolation_level=None)
            db.execute("PRAGMA synchronous=FULL")
            require(db.execute("PRAGMA journal_mode").fetchone() == ("delete",), ERROR)
            end = time.monotonic() + min(1, decision.remaining())
            db.set_progress_handler(lambda: int(time.monotonic() >= end), 100)
            db.execute("BEGIN IMMEDIATE")
            events, previous, highwater = self._load(db)
            original_count = len(events)
            now = decision.now()
            require(now >= highwater, ERROR)
            def append(kind, data):
                nonlocal previous
                limit = MAX_EVENTS if kind == "clock" else MAX_EVENTS - 1
                require(kind in KINDS and type(data) is dict and len(events) < limit, ERROR)
                raw = canonical(data)
                require(0 < len(raw) <= 65536, ERROR)
                value = document(raw)
                sequence = len(events) + 1
                record = {"sequence": sequence, "kind": kind, "data": value, "previous": previous, "observed_at": now}
                measured = digest(record)
                db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)", (sequence, kind, raw, previous, measured, now))
                db.execute("UPDATE metadata SET highwater=?", (now,))
                events.append({"kind": kind, "data": value, "at": now})
                previous = measured
            if now > highwater:
                append("clock", {})
            db.execute("SAVEPOINT business")
            business_count, business_previous = len(events), previous
            error, result = None, None
            try:
                # Exhaustion never admits lifecycle use at an unpersistable time.
                require(len(events) < MAX_EVENTS, ERROR)
                result = operation(events, append)
                decision.now()
                require(_identity(self.directory, self.witness) == self.identity, ERROR)
            except Exception as caught:
                db.execute("ROLLBACK TO business")
                del events[business_count:]
                previous = business_previous
                error = caught
            db.execute("RELEASE business")
            if decision.last > now:
                # Preserve every validated observation, including a refused
                # business operation, without renewing the original Decision.
                now = decision.last
                append("clock", {})
            # A crash after this commit but before its witness leaves the store
            # explicitly indeterminate. Opening never repairs or rolls it back.
            db.execute("COMMIT")
            for sequence, measured in db.execute("SELECT sequence,digest FROM events WHERE sequence>? ORDER BY sequence", (original_count,)):
                _write_witness(self.witness, sequence, measured)
            if error is not None:
                raise error
            return result
        except Exception:
            raise BindingError(ERROR) from None
        finally:
            if db is not None:
                if db.in_transaction:
                    db.rollback()
                db.close()
            if lock is not None:
                os.close(lock)

    def events(self, *, decision):
        # The validated journal may exceed a single event document limit.
        return self.mutate(lambda events, _: deepcopy(events), decision=decision)

    def record(self, kind, data, *, decision):
        require(kind != "clock", ERROR)
        return self.mutate(lambda _, append: append(kind, data), decision=decision)
