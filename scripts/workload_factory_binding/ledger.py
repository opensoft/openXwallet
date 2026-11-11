"""Private durable one-use reservations. Existing state is never reinitialized."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import stat

from .evidence import BindingError, digest, integer, reference, require

SCHEMA = ("CREATE TABLE reservations("
          "token TEXT PRIMARY KEY NOT NULL, challenge TEXT UNIQUE NOT NULL, "
          "reserved_at INTEGER NOT NULL)")


class ReplayLedger:
    def __init__(self, directory):
        self.directory = Path(directory).absolute()
        try:
            self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            info = self.directory.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
                    and not stat.S_IMODE(info.st_mode) & 0o077, "unsafe-state")
            self.path = self.directory / "reservations.sqlite"
            created = False
            try:
                fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            except FileExistsError:
                self._check_file()
            else:
                os.close(fd)
                created = True
            with closing(sqlite3.connect(self.path, timeout=3, isolation_level=None)) as db:
                if created:
                    # Only this newly-created file may initialize. A crash
                    # before commit leaves an unusable file, never a fresh ledger.
                    db.execute("BEGIN EXCLUSIVE")
                    db.execute(SCHEMA)
                    db.execute("PRAGMA user_version=1")
                    db.commit()
                self._check_schema(db)
                require(db.execute("PRAGMA integrity_check(1)").fetchone() == ("ok",),
                        "invalid-state-schema")
        except (OSError, sqlite3.Error):
            raise BindingError("state-unavailable") from None

    def _check_file(self):
        info = self.path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) & 0o077 == 0 and info.st_nlink == 1,
                "unsafe-state")

    @staticmethod
    def _check_schema(db):
        require(db.execute("PRAGMA user_version").fetchone()[0] == 1, "invalid-state-schema")
        objects = db.execute(
            "SELECT type,name,sql FROM sqlite_master ORDER BY type,name").fetchall()
        require(objects == [
            ("index", "sqlite_autoindex_reservations_1", None),
            ("index", "sqlite_autoindex_reservations_2", None),
            ("table", "reservations", SCHEMA),
        ], "invalid-state-schema")

    def reserve(self, *, issuer, jti, challenge_issuer, challenge_id, now):
        require(all(reference(v) for v in (issuer, jti, challenge_issuer, challenge_id))
                and integer(now), "invalid-reservation")
        try:
            self._check_file()
            with closing(sqlite3.connect(self.path, timeout=3, isolation_level=None)) as db:
                db.execute("BEGIN IMMEDIATE")
                try:
                    self._check_schema(db)
                    db.execute("INSERT INTO reservations VALUES(?,?,?)",
                               (digest([issuer, jti]), digest([challenge_issuer, challenge_id]), now))
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
        except sqlite3.IntegrityError:
            raise BindingError("replay-refused") from None
        except (OSError, sqlite3.Error):
            raise BindingError("state-unavailable") from None
