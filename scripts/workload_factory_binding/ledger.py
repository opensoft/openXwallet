"""Private durable one-use reservations. No secrets and no signing retries."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import stat

from .evidence import BindingError, digest, integer, reference, require


class ReplayLedger:
    def __init__(self, directory):
        self.directory = Path(directory).absolute()
        try:
            self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            info = self.directory.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
                    and not stat.S_IMODE(info.st_mode) & 0o077, "unsafe-state")
            self.path = self.directory / "reservations.sqlite"
            try:
                fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            except FileExistsError:
                self._check_file()
            else:
                os.close(fd)
            with closing(sqlite3.connect(self.path, timeout=3)) as db:
                db.execute("CREATE TABLE IF NOT EXISTS reservations("
                           "token TEXT PRIMARY KEY, challenge TEXT UNIQUE NOT NULL, "
                           "reserved_at INTEGER NOT NULL)")
                db.commit()
        except (OSError, sqlite3.Error):
            raise BindingError("state-unavailable") from None

    def _check_file(self):
        info = self.path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) & 0o077 == 0 and info.st_nlink == 1,
                "unsafe-state")

    def reserve(self, *, issuer, jti, challenge_issuer, challenge_id, now):
        require(all(reference(v) for v in (issuer, jti, challenge_issuer, challenge_id))
                and integer(now), "invalid-reservation")
        try:
            self._check_file()
            with closing(sqlite3.connect(self.path, timeout=3, isolation_level=None)) as db:
                db.execute("BEGIN IMMEDIATE")
                try:
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
