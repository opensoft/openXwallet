"""Atomic retained preauthorizations. No startup/reset/recovery creation path.

Private POSIX files and pinned inode receipts detect observable replacement.
This is not protection against a hostile host or an in-place valid backup restore.
"""
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass
import os
from pathlib import Path
import sqlite3
import stat
import time

from workload_factory_binding.evidence import (
    BindingError, canonical, decode_object, digest, integer, require,
)
from ..bootstrap import BootstrapReadback, DispatchContext, selection_digest, validate_dispatch_context
from ..config import _configuration, _handle
from ..workflow import OperationReadback, REPOSITORY, CALLER, REUSABLE, REF
from .model import ERROR, PROFILE, SCOPE, closed, verify_observation

DATABASE = "authority.sqlite"
SCHEMA = (
    "CREATE TABLE metadata (version INTEGER NOT NULL, controller TEXT NOT NULL, highwater INTEGER NOT NULL)",
    "CREATE TABLE preauthorizations (ref TEXT PRIMARY KEY, selection TEXT NOT NULL, commitment TEXT NOT NULL, start INTEGER NOT NULL, end INTEGER NOT NULL, revoked INTEGER NOT NULL CHECK(revoked IN (0,1)), context TEXT, configuration TEXT, grant_ref TEXT)",
    "CREATE TABLE observations (event TEXT PRIMARY KEY, context TEXT NOT NULL, envelope TEXT NOT NULL)",
)


@dataclass(frozen=True)
class StoreIdentity:
    directory_device: int
    directory_inode: int
    database_device: int
    database_inode: int


def _identity(directory):
    try:
        folder, db = directory.lstat(), (directory / DATABASE).lstat()
        for info, is_dir in ((folder, True), (db, False)):
            require((stat.S_ISDIR(info.st_mode) if is_dir else stat.S_ISREG(info.st_mode))
                    and info.st_uid == os.geteuid() and not stat.S_IMODE(info.st_mode) & 0o077
                    and (is_dir or info.st_nlink == 1), ERROR)
        for suffix in ("-journal", "-wal", "-shm"):
            sidecar = directory / (DATABASE + suffix)
            try:
                info = sidecar.lstat()
            except FileNotFoundError:
                continue
            require(suffix == "-journal" and stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                    and info.st_uid == os.geteuid() and not stat.S_IMODE(info.st_mode) & 0o077, ERROR)
        return StoreIdentity(folder.st_dev, folder.st_ino, db.st_dev, db.st_ino)
    except OSError:
        raise BindingError(ERROR) from None


def initialize_store(directory, controller_public_key):
    """Explicit fixture administration. Requires a NEW directory; never reset/reuse."""
    require(type(controller_public_key) is bytes and len(controller_public_key) == 32, ERROR)
    directory = Path(directory).absolute()
    try:
        directory.mkdir(mode=0o700)
        fd = os.open(directory / DATABASE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with closing(sqlite3.connect(directory / DATABASE)) as db, db:
            db.execute("PRAGMA synchronous=FULL")
            for sql in SCHEMA:
                db.execute(sql)
            db.execute("INSERT INTO metadata VALUES (1, ?, 0)", (controller_public_key.hex(),))
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return _identity(directory)
    except (OSError, sqlite3.Error):
        raise BindingError(ERROR) from None


class AuthorityStore:
    def __init__(self, directory, *, identity, controller_public_key, clock,
                 bootstrap_principal="principal:bootstrap", operation_principal="principal:operation-reader"):
        require(type(identity) is StoreIdentity and callable(clock)
                and type(controller_public_key) is bytes and len(controller_public_key) == 32, ERROR)
        for value in (bootstrap_principal, operation_principal):
            _handle(value)
        self.directory, self.identity = Path(directory).absolute(), identity
        self.public_key, self.clock = controller_public_key, clock
        self.bootstrap_principal, self.operation_principal = bootstrap_principal, operation_principal
        with self._transaction():
            pass  # Validate the selected existing store and persist its current clock.

    @contextmanager
    def _transaction(self):
        require(_identity(self.directory) == self.identity, ERROR)
        db = None
        try:
            db = sqlite3.connect((self.directory / DATABASE).as_uri() + "?mode=rw", uri=True,
                                 isolation_level=None, timeout=2)
            budget = time.monotonic() + 3
            db.set_progress_handler(lambda: int(time.monotonic() >= budget), 1000)
            db.execute("PRAGMA synchronous=FULL")
            require(db.execute("PRAGMA journal_mode").fetchone() == ("delete",)
                    and db.execute("PRAGMA integrity_check(1)").fetchone() == ("ok",), ERROR)
            actual = tuple(row[0] for row in db.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"))
            require(actual == tuple(sorted(SCHEMA, key=lambda s: s.split()[2])), ERROR)
            db.execute("BEGIN IMMEDIATE")
            metadata = db.execute("SELECT version, controller, highwater FROM metadata").fetchall()
            require(len(metadata) == 1 and metadata[0][:2] == (1, self.public_key.hex()), ERROR)
            now = self.clock()
            require(integer(now) and integer(metadata[0][2]) and now >= metadata[0][2], ERROR)
            db.execute("UPDATE metadata SET highwater=?", (now,))
            require(_identity(self.directory) == self.identity, ERROR)
            # Failed business requests must not erase a trusted clock observation.
            # Retain that metadata under the same write lock while rolling back
            # every attempted claim/revoke/observation mutation on refusal.
            db.execute("SAVEPOINT business")
            failed = True
            try:
                yield db, now
                require(_identity(self.directory) == self.identity, ERROR)
                failed = False
            finally:
                if failed:
                    db.execute("ROLLBACK TO business")
                db.execute("RELEASE business")
                db.execute("COMMIT")
        except Exception:
            if db is not None and db.in_transaction:
                db.execute("ROLLBACK")
            raise BindingError(ERROR) from None
        finally:
            if db is not None:
                db.close()

    def authorize(self, *, ref, selection, not_before, expires_at):
        _handle(ref)
        raw = canonical(selection)
        commitment = selection_digest(raw)
        with self._transaction() as (db, now):
            config = selection["configuration"]
            require(all(integer(v) for v in (not_before, expires_at))
                    and now <= not_before < expires_at <= not_before + 3600
                    and config["not_before"] <= not_before < expires_at <= config["expires_at"], ERROR)
            db.execute("INSERT INTO preauthorizations VALUES (?, ?, ?, ?, ?, 0, NULL, NULL, NULL)",
                       (ref, raw.decode(), commitment, not_before, expires_at))
        return {"profile": PROFILE, "scope": SCOPE, "selection_digest": commitment}

    def revoke(self, *, ref):
        _handle(ref)
        with self._transaction() as (db, _):
            require(db.execute("UPDATE preauthorizations SET revoked=1 WHERE ref=?", (ref,)).rowcount == 1, ERROR)
        return {"profile": PROFILE, "scope": SCOPE, "revoked": True}

    def observe(self, *, envelope):
        with self._transaction() as (db, now):
            context, observed = verify_observation(envelope, self.public_key, now)
            raw = canonical(envelope).decode()
            previous = db.execute("SELECT envelope FROM observations WHERE event=?", (observed["event_ref"],)).fetchone()
            require(previous is None or previous == (raw,), ERROR)
            if previous is None:
                db.execute("INSERT INTO observations VALUES (?, ?, ?)",
                           (observed["event_ref"], digest(asdict(context)), raw))
        return {"profile": PROFILE, "scope": SCOPE, "observed": True}

    def read(self, *, context, event_ref, bind):
        require(type(bind) is bool, ERROR)
        context = DispatchContext(**context)
        validate_dispatch_context(context)
        with self._transaction() as (db, now):
            row = db.execute("SELECT selection, commitment, start, end, revoked, context, configuration, grant_ref FROM preauthorizations WHERE ref=?",
                             (context.preauthorization_ref,)).fetchone()
            require(row is not None and row[4] == 0 and row[2] <= now < row[3]
                    and row[1] == context.selection_digest, ERROR)
            observation = db.execute("SELECT envelope FROM observations WHERE event=?", (event_ref,)).fetchone()
            require(observation is not None, ERROR)
            observed_context, observed = verify_observation(decode_object(observation[0].encode()), self.public_key, now)
            require(observed_context == context, ERROR)
            selected = decode_object(row[0].encode())
            require(selection_digest(canonical(selected)) == row[1], ERROR)
            config = selected["configuration"]
            launch, sources = config["launch"], config["sources"]
            require(launch["repository"] == context.repository == REPOSITORY
                    and launch["repository_id"] == context.repository_id and launch["ref"] == context.ref == REF
                    and launch["sha"] == launch["workflow_sha"] == context.accepted_commit
                    and launch["workflow_ref"] == context.workflow_ref
                    and launch["job_workflow_ref"] == REPOSITORY + "/" + REUSABLE + "@" + REF
                    and launch["job_workflow_sha"] == context.source_commit
                    and all(sources[r]["repository"] == REPOSITORY and sources[r]["commit"] == context.source_commit
                            for r in ("worker", "adapter", "caller_workflow", "reusable_workflow"))
                    and sources["caller_workflow"]["path"] == CALLER
                    and sources["reusable_workflow"]["path"] == REUSABLE, ERROR)
            context_hash = digest(asdict(context))
            if row[5] is None:
                require(bind, ERROR)
                config["launch"].update(run_id=context.run_id, run_attempt=context.run_attempt)
                _configuration(config)
                decode_object(canonical(config))
                grant = "grant:runtime-" + context_hash.removeprefix("sha256:")
                db.execute("UPDATE preauthorizations SET context=?, configuration=?, grant_ref=? WHERE ref=? AND context IS NULL",
                           (context_hash, canonical(config).decode(), grant, context.preauthorization_ref))
            else:
                require(row[5] == context_hash, ERROR)
                config, grant = decode_object(row[6].encode()), row[7]
                _configuration(config)
                require(config["launch"]["run_id"] == context.run_id
                        and config["launch"]["run_attempt"] == context.run_attempt, ERROR)
            expiry = min(row[3], observed["expires_at"], config["expires_at"], now + 60)
            require(now < expiry, ERROR)
            configuration_digest = digest(config)
            bootstrap = BootstrapReadback(self.bootstrap_principal, context.preauthorization_ref,
                context.selection_digest, context.accepted_commit, context.repository_id, config["case_ref"],
                context.run_id, context.run_attempt, configuration_digest, grant, now, expiry)
            operation = OperationReadback(self.operation_principal, grant, "qualify-existing-resources",
                configuration_digest, context.accepted_commit, config["case_ref"], context.run_id,
                context.run_attempt, now, expiry)
            return {"profile": PROFILE, "scope": SCOPE, "configuration": config,
                    "bootstrap": asdict(bootstrap), "operation": asdict(operation)}
