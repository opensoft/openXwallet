"""Initialized retained dispatch attempts; consumption is never undone by failure."""
from contextlib import closing, contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
import stat
import time
from workload_factory_binding.evidence import BindingError, canonical, integer, reference, require
from . import ERROR
from .approval import Approval
from .common import number

DATABASE = "github-dispatch.sqlite"
SCHEMA = (
    "CREATE TABLE metadata (identity TEXT NOT NULL, highwater INTEGER NOT NULL)",
    "CREATE TABLE attempts (ref TEXT PRIMARY KEY, commitment TEXT NOT NULL, request TEXT NOT NULL, initiating_user TEXT NOT NULL, broker_actor TEXT NOT NULL, run_id TEXT UNIQUE, scope TEXT NOT NULL)",
)

@dataclass(frozen=True, repr=False)
class JournalIdentity:
    directory_device: int
    directory_inode: int
    database_device: int
    database_inode: int
    name: str


def _files(directory):
    folder, db = directory.lstat(), (directory / DATABASE).lstat()
    for info, is_dir in ((folder, True), (db, False)):
        require((stat.S_ISDIR(info.st_mode) if is_dir else stat.S_ISREG(info.st_mode))
                and info.st_uid == os.geteuid() and not stat.S_IMODE(info.st_mode) & 0o077
                and (is_dir or info.st_nlink == 1), ERROR)
    for suffix in ("-journal", "-wal", "-shm"):
        file = directory / (DATABASE + suffix)
        if file.exists() or file.is_symlink():
            info = file.lstat()
            require(suffix == "-journal" and stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                    and info.st_uid == os.geteuid() and not stat.S_IMODE(info.st_mode) & 0o077, ERROR)
    return folder.st_dev, folder.st_ino, db.st_dev, db.st_ino


def initialize(directory, *, identity_name):
    """Explicit isolated/operator initialization. Requires a new private directory."""
    require(reference(identity_name), ERROR)
    directory = Path(directory).absolute()
    try:
        directory.mkdir(mode=0o700)
        fd = os.open(directory / DATABASE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with closing(sqlite3.connect(directory / DATABASE)) as db, db:
            db.execute("PRAGMA synchronous=FULL")
            for sql in SCHEMA:
                db.execute(sql)
            db.execute("INSERT INTO metadata VALUES (?, 0)", (identity_name,))
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        return JournalIdentity(*_files(directory), identity_name)
    except Exception:
        raise BindingError(ERROR) from None

class Journal:
    def __init__(self, directory, *, identity, clock):
        require(type(identity) is JournalIdentity and callable(clock), ERROR)
        self.directory, self.identity, self.clock = Path(directory).absolute(), identity, clock
        with self._transaction():
            pass

    @contextmanager
    def _transaction(self):
        db = None
        try:
            require(_files(self.directory) == (self.identity.directory_device, self.identity.directory_inode,
                self.identity.database_device, self.identity.database_inode), ERROR)
            db = sqlite3.connect((self.directory / DATABASE).as_uri() + "?mode=rw", uri=True,
                                 isolation_level=None, timeout=2)
            end = time.monotonic() + 3
            db.set_progress_handler(lambda: int(time.monotonic() >= end), 1000)
            db.execute("PRAGMA synchronous=FULL")
            require(db.execute("PRAGMA journal_mode").fetchone() == ("delete",)
                    and db.execute("PRAGMA integrity_check(1)").fetchone() == ("ok",), ERROR)
            require(tuple(x[0] for x in db.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"))
                    == tuple(sorted(SCHEMA, key=lambda s: s.split()[2])), ERROR)
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT identity, highwater FROM metadata").fetchall()
            now = self.clock()
            require(len(rows) == 1 and rows[0][0] == self.identity.name
                    and integer(now) and integer(rows[0][1]) and now >= rows[0][1], ERROR)
            db.execute("UPDATE metadata SET highwater=?", (now,))
            db.execute("SAVEPOINT business")
            succeeded = False
            try:
                yield db, now
                require(_files(self.directory) == (self.identity.directory_device, self.identity.directory_inode,
                    self.identity.database_device, self.identity.database_inode), ERROR)
                succeeded = True
            finally:
                if not succeeded:
                    db.execute("ROLLBACK TO business")
                db.execute("RELEASE business")
                db.execute("COMMIT")
        except BaseException as exc:
            if db is not None and db.in_transaction:
                db.execute("ROLLBACK")
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise BindingError(ERROR) from None
        finally:
            if db is not None:
                db.close()

    def reserve(self, approval, request):
        require(type(approval) is Approval and type(request) is dict, ERROR)
        with self._transaction() as (db, now):
            approval.current(now)
            require(request == approval.request, ERROR)
            db.execute("INSERT INTO attempts VALUES (?, ?, ?, ?, ?, NULL, ?)", (approval.ref,
                approval.commitment, canonical(request).decode(), approval.initiating_user_id,
                approval.broker_actor_id, canonical(approval.journal_scope).decode()))

    def record_run(self, approval, run_id):
        require(number(run_id), ERROR)
        with self._transaction() as (db, now):
            approval.current(now)
            require(db.execute("UPDATE attempts SET run_id=? WHERE ref=? AND commitment=? AND run_id IS NULL AND request=? AND scope=?",
                (run_id, approval.ref, approval.commitment, canonical(approval.request).decode(),
                 canonical(approval.journal_scope).decode())).rowcount == 1, ERROR)

    def read(self, approval):
        require(type(approval) is Approval, ERROR)
        with self._transaction() as (db, now):
            approval.current(now)
            rows = db.execute("SELECT commitment, initiating_user, broker_actor, run_id, request, scope FROM attempts WHERE ref=?",
                              (approval.ref,)).fetchall()
            require(len(rows) == 1 and rows[0][:3] == (approval.commitment,
                    approval.initiating_user_id, approval.broker_actor_id)
                    and rows[0][4] == canonical(approval.request).decode()
                    and rows[0][5] == canonical(approval.journal_scope).decode(), ERROR)
            return rows[0][3]  # None means consumed/indeterminate, never permission to retry.
