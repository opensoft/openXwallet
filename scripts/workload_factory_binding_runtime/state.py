"""Expected-existing replay state under the accepted trusted-host boundary.

Runtime never initializes, replaces, restores or prunes a store. Initialization
identity and recovery status come from protected administration. Inode/integrity
checks detect observable replacement/corruption, not hostile byte edits or a valid
backup restored in place. Active-scope restore is prohibited, not made safe here.
"""
from contextlib import closing, contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
import stat
import time

from workload_factory_binding.evidence import BindingError, digest, integer, reference, require
from workload_factory_binding.ledger import ReplayLedger
from .config import RuntimeTrust, validate_config

_REFS = ("store_ref", "initialization_ref", "retention_ref", "recovery_ref")
_DATABASE = "reservations.sqlite"


@dataclass(frozen=True, repr=False)
class StateSelection:
    store_ref: str
    initialization_ref: str
    retention_ref: str
    recovery_ref: str


@dataclass(frozen=True, repr=False)
class StateIdentity:
    """Protected initialization receipt metadata; never captured implicitly."""
    directory_device: int
    directory_inode: int
    database_device: int
    database_inode: int


@dataclass(frozen=True, repr=False)
class StateAccess:
    """Authenticated hosting readback, not worker input or a public protocol."""
    principal_ref: str
    selection: StateSelection
    initialization: StateIdentity
    config_digest: str
    case_ref: str
    run_id: str
    run_attempt: str
    status: str
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class StateTrust:
    """Independent initialization receipt and authenticated bounded readback.

    load_access(deadline=epoch) must read actual retention/recovery/revocation
    status outside worker control. A restart reuses this same initialization
    receipt. Recovery requires revocation and a new approved store/scope, never
    recapturing a replacement as the old initialization.
    """
    selection: StateSelection
    initialization: StateIdentity
    readback_principal: str
    load_access: object


@dataclass(frozen=True, repr=False)
class StateUse:
    """Internal bridge checkpoint; neither a receipt nor a public wire contract."""
    valid_until: int
    checked_at: int


def _private(info, *, directory=False):
    require((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
            and info.st_uid == os.geteuid() and not stat.S_IMODE(info.st_mode) & 0o077
            and (directory or info.st_nlink == 1), "unsafe-runtime-state")


def _files(directory):
    try:
        folder = directory.lstat()
        _private(folder, directory=True)
        database = (directory / _DATABASE).lstat()
        _private(database)
        for suffix in ("-journal", "-wal", "-shm"):
            try:
                sidecar = (directory / (_DATABASE + suffix)).lstat()
            except FileNotFoundError:
                continue
            _private(sidecar)
            require(suffix == "-journal", "unsupported-runtime-state-mode")
        return StateIdentity(folder.st_dev, folder.st_ino, database.st_dev, database.st_ino)
    except OSError:
        raise BindingError("runtime-state-unavailable") from None


@contextmanager
def _open(directory, *, expected=None, timeout=3):
    identity = _files(directory)
    require(expected is None or identity == expected, "runtime-state-replaced")
    budget = time.monotonic() + min(3, timeout)
    try:
        # mode=rw is essential: sqlite3's default silently creates absent files.
        db = sqlite3.connect((directory / _DATABASE).as_uri() + "?mode=rw",
                             uri=True, timeout=timeout, isolation_level=None)
    except sqlite3.Error:
        raise BindingError("runtime-state-unavailable") from None
    with closing(db):
        db.set_progress_handler(lambda: int(time.monotonic() >= budget), 1000)
        try:
            ReplayLedger._check_schema(db)
            require(db.execute("PRAGMA journal_mode").fetchone() == ("delete",),
                    "unsupported-runtime-state-mode")
            require(db.execute("PRAGMA integrity_check(1)").fetchone() == ("ok",),
                    "invalid-state-schema")
            require(_files(directory) == identity, "runtime-state-replaced")
        except sqlite3.Error:
            raise BindingError("runtime-state-unavailable") from None
        yield db


def inspect_initialized_state(directory):
    """Existing-store initialization inspection for trusted operators, never creation.

    Record this result independently during authorized provisioning. Calling this
    on every restart to approve whatever is present defeats initialization binding.
    SQLite may perform normal hot-journal recovery; this is not a backup restore.
    """
    directory = Path(directory).absolute()
    identity = _files(directory)
    with _open(directory, expected=identity) as db:
        require(not db.in_transaction, "invalid-state-schema")
    require(_files(directory) == identity, "runtime-state-replaced")
    return identity


class _Use:
    def __init__(self, ledger, deadline=None, checked_at=None):
        require(checked_at is None or integer(checked_at), "runtime-state-clock-unavailable")
        self.ledger, self.deadline, self.last = ledger, deadline, checked_at
        self.check()

    def clock(self):
        try:
            now = self.ledger.runtime_trust.clock()
            require(integer(now) and (self.last is None or now >= self.last), "runtime-state-clock-unavailable")
        except Exception:
            raise BindingError("runtime-state-clock-unavailable") from None
        require(self.deadline is None or now < self.deadline, "runtime-state-expired")
        self.last = now
        return now

    def check(self):
        before = self.clock()
        try:
            raw = self.ledger.load_config()
        except Exception:
            raise BindingError("runtime-config-unavailable") from None
        current = validate_config(raw, trust=self.ledger.runtime_trust)
        require(current.checked_at >= before, "runtime-state-clock-unavailable")
        self.last = current.checked_at
        self.deadline = min(self.deadline or current.valid_until, current.valid_until)
        trust, selection = self.ledger.state_trust, current.selection
        require(all(getattr(trust.selection, name) == selection["state"][name] for name in _REFS),
                "runtime-state-binding-mismatch")
        require(trust.readback_principal != selection["services"]["worker_channel"]["principal_ref"],
                "runtime-state-not-independent")
        self.clock()
        try:
            access = trust.load_access(deadline=self.deadline)
        except Exception:
            raise BindingError("runtime-state-readback-unavailable") from None
        now = self.clock()
        require(type(access) is StateAccess and type(access.selection) is StateSelection
                and type(access.initialization) is StateIdentity, "runtime-state-unverified")
        require(access.principal_ref == trust.readback_principal and access.selection == trust.selection
                and access.initialization == trust.initialization and access.config_digest == current.config_digest
                and access.case_ref == selection["case_ref"] and access.run_id == selection["launch"]["run_id"]
                and access.run_attempt == selection["launch"]["run_attempt"], "runtime-state-readback-mismatch")
        require(access.status == "active", "runtime-state-recovery-required")
        require(integer(access.observed_at) and integer(access.expires_at)
                and access.observed_at <= now < access.expires_at <= access.observed_at + 60,
                "runtime-state-expired")
        self.deadline = min(self.deadline, access.expires_at)
        now = self.clock()
        with _open(self.ledger.directory, expected=trust.initialization,
                   timeout=min(3, self.deadline - now)) as db:
            require(not db.in_transaction, "invalid-state-schema")
        self.clock()


class InitializedLedger:
    """Opt-in runtime ledger; no constructor or failure path initializes state."""
    def __init__(self, directory, *, load_config, runtime_trust, state_trust):
        require(type(runtime_trust) is RuntimeTrust and type(state_trust) is StateTrust
                and type(state_trust.selection) is StateSelection
                and type(state_trust.initialization) is StateIdentity
                and reference(state_trust.readback_principal)
                and callable(load_config) and callable(state_trust.load_access), "invalid-runtime-state-trust")
        require(all(reference(getattr(state_trust.selection, name)) for name in _REFS)
                and all(integer(value) for value in vars(state_trust.initialization).values())
                and state_trust.initialization.directory_inode > 0 and state_trust.initialization.database_inode > 0,
                "invalid-runtime-state-trust")
        self.directory = Path(directory).absolute()
        self.load_config, self.runtime_trust, self.state_trust = load_config, runtime_trust, state_trust
        _Use(self)

    def check_for_use(self, *, deadline, checked_at=None):
        require(integer(deadline), "runtime-state-expired")
        use = _Use(self, deadline, checked_at)
        return StateUse(use.deadline, use.last)

    def reserve(self, **kwargs):
        """Standalone trusted compatibility seam; runtime uses reserve_for_use."""
        self._reserve(None, **kwargs)

    def reserve_for_use(self, *, deadline, checked_at=None, **kwargs):
        require(integer(deadline), "runtime-state-expired")
        return self._reserve(deadline, checked_at=checked_at, **kwargs)

    def _reserve(self, deadline, *, issuer, jti, challenge_issuer, challenge_id, now, checked_at=None):
        require(all(reference(v) for v in (issuer, jti, challenge_issuer, challenge_id))
                and integer(now), "invalid-reservation")
        use = _Use(self, deadline, checked_at)
        try:
            with _open(self.directory, expected=self.state_trust.initialization,
                       timeout=min(3, use.deadline - use.clock())) as db:
                db.execute("BEGIN IMMEDIATE")
                try:
                    use.clock()
                    db.execute("INSERT INTO reservations VALUES(?,?,?)",
                               (digest([issuer, jti]), digest([challenge_issuer, challenge_id]), now))
                    use.clock()
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
            # Refusal after durable reservation never erases it.
            use.check()
        except sqlite3.IntegrityError:
            raise BindingError("replay-refused") from None
        except (OSError, sqlite3.Error):
            raise BindingError("runtime-state-unavailable") from None
        return StateUse(use.deadline, use.last)
