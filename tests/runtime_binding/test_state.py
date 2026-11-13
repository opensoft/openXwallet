"""Expected-existing runtime state. Provisioning is a separate fixture/operator act."""
from dataclasses import asdict, replace
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import os
import shutil
import sqlite3

import pytest

from workload_factory_binding.evidence import BindingError, digest
from workload_factory_binding.ledger import ReplayLedger
from workload_factory_binding_runtime.runtime import StateBinding
from workload_factory_binding_runtime.state import (
    InitializedLedger, StateAccess, StateSelection, StateTrust, inspect_initialized_state,
)
from .composition_fixture import c
from .test_config import configuration, encoded


@pytest.fixture
def s(c):
    # Harness provisioning used the existing offline initializer before runtime.
    selection = StateSelection(**c.config["state"])
    initialization = inspect_initialized_state(c.h.ledger.directory)
    access = StateAccess("principal:state-admin", selection, initialization,
                         digest(c.config), c.config["case_ref"], c.config["launch"]["run_id"],
                         c.config["launch"]["run_attempt"], "active", c.h.now - 1, c.h.now + 20)
    from types import SimpleNamespace
    result = SimpleNamespace(c=c, directory=c.h.ledger.directory, access=access,
                             calls=[], hook=None, selection=selection, initialization=initialization)
    def read(*, deadline):
        result.calls.append(deadline)
        if result.hook:
            result.hook()
        return result.access
    result.trust = StateTrust(selection, initialization, "principal:state-admin", read)
    def make(**overrides):
        args = dict(directory=result.directory, load_config=lambda: encoded(c.config),
                    runtime_trust=c.trust, state_trust=result.trust)
        args.update(overrides)
        return InitializedLedger(**args)
    result.make = make
    result.ledger = make()
    result.calls.clear()
    c.state = StateBinding(**c.config["state"], ledger=result.ledger)
    c.bridge = c.make()
    return result


def test_initialized_store_survives_restart_and_replay_stays_consumed(s):
    c = s.c
    result = c.run()
    assert result["human_approval"] is False
    restarted = s.make()
    c.state = replace(c.state, ledger=restarted)
    c.bridge = c.make()
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 1
    assert inspect_initialized_state(s.directory) == s.initialization


def test_runtime_never_creates_missing_store(s, tmp_path):
    missing = tmp_path / "never-initialized"
    with pytest.raises(BindingError):
        s.make(directory=missing)
    assert not missing.exists()


def test_runtime_never_recreates_removed_database(s):
    path = s.directory / "reservations.sqlite"
    path.unlink()
    with pytest.raises(BindingError):
        s.make()
    assert not path.exists()


def test_missing_initialization_receipt_never_becomes_automatic_capture(s):
    trust = replace(s.trust, initialization=None)
    with pytest.raises(BindingError, match="^invalid-runtime-state-trust$"):
        s.make(state_trust=trust)


def test_owning_proof_accepts_initialized_state_and_restart_refuses_reuse(s):
    from factory_binding.test_owner_integration import owner_source
    owner_source()
    from openwallet_runtime.proof import TrustedKeyBinding, create_proof, verify_proof
    c = s.c
    c.h.binding = TrustedKeyBinding(**asdict(c.h.binding))
    c.bridge = c.make(create_proof=create_proof)
    result = c.run()
    checked = verify_proof(result["proof"], expected_digest=c.h.challenge.digest, binding=c.h.binding, now=c.h.now)
    assert checked.subject_ref == c.h.binding.subject_ref
    assert result["human_approval"] is False
    c.state = replace(c.state, ledger=s.make())
    c.bridge = c.make(create_proof=create_proof)
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 1


def reserve(s, ledger=None, *, jti="token:one", challenge_id="challenge:one"):
    (ledger or s.ledger).reserve(issuer="issuer:fixture", jti=jti,
                                challenge_issuer="challenge:fixture", challenge_id=challenge_id, now=s.c.h.now)


@pytest.mark.parametrize("kind", ["empty", "corrupt", "schema", "version", "wal"])
def test_uninitialized_corrupt_or_changed_store_refuses_without_repair(s, kind):
    path = s.directory / "reservations.sqlite"
    if kind in ("empty", "corrupt"):
        path.write_bytes(b"" if kind == "empty" else b"not a database")
    else:
        with sqlite3.connect(path) as db:
            if kind == "schema":
                db.execute("DROP TABLE reservations")
            elif kind == "version":
                db.execute("PRAGMA user_version=2")
            else:
                db.execute("PRAGMA journal_mode=WAL")
    before = path.read_bytes()
    with pytest.raises(BindingError):
        s.make()
    assert path.read_bytes() == before


@pytest.mark.parametrize("kind", ["directory", "database", "symlink", "hardlink", "fifo", "journal", "shm"])
def test_unsafe_state_refuses_without_signing_or_blocking(s, tmp_path, kind):
    path = s.directory / "reservations.sqlite"
    if kind == "directory":
        s.directory.chmod(0o755)
    elif kind == "database":
        path.chmod(0o644)
    elif kind in ("symlink", "fifo"):
        path.unlink()
        if kind == "symlink":
            path.symlink_to(tmp_path / "absent-target")
        else:
            os.mkfifo(path)
    elif kind == "hardlink":
        os.link(path, tmp_path / "extra-link")
    else:
        (s.directory / ("reservations.sqlite-" + kind)).symlink_to(tmp_path / "absent-target")
    with pytest.raises(BindingError):
        s.c.run()
    assert s.c.h.calls == 0


def test_valid_database_replacement_is_not_the_recorded_initialization(s):
    path = s.directory / "reservations.sqlite"
    replacement = s.directory / "replacement.sqlite"
    shutil.copyfile(path, replacement)
    replacement.chmod(0o600)
    replacement.replace(path)
    with pytest.raises(BindingError, match="^runtime-state-replaced$"):
        s.make()
    assert s.initialization.database_inode != path.stat().st_ino


@pytest.mark.parametrize("field", ["store_ref", "initialization_ref", "retention_ref", "recovery_ref"])
def test_each_current_state_selection_must_match_initialization_receipt(s, field):
    s.access = replace(s.access, selection=replace(s.selection, **{field: "changed:reference"}))
    with pytest.raises(BindingError, match="^runtime-state-readback-mismatch$"):
        s.ledger.check_for_use(deadline=s.c.h.now + 10)


@pytest.mark.parametrize("field,value", [
    ("principal_ref", "principal:worker_channel"), ("config_digest", "sha256:" + "f" * 64),
    ("case_ref", "case:other"), ("run_id", "9999"), ("run_attempt", "2"),
])
def test_each_current_scope_binding_refuses(s, field, value):
    s.access = replace(s.access, **{field: value})
    with pytest.raises(BindingError, match="^runtime-state-readback-mismatch$"):
        s.ledger.check_for_use(deadline=s.c.h.now + 10)


@pytest.mark.parametrize("status", ["revoked", "restored", "recovery-required", "uninitialized", True])
def test_recovery_or_revocation_is_not_an_active_scope(s, status):
    s.access = replace(s.access, status=status)
    with pytest.raises(BindingError, match="^runtime-state-recovery-required$"):
        s.make()


def test_worker_body_cannot_provide_initialization_or_recovery(s):
    s.access = {"initialized": True, "recovered": True}
    with pytest.raises(BindingError, match="^runtime-state-unverified$"):
        s.make()


@pytest.mark.parametrize("field,delta", [("observed_at", 1), ("observed_at", -61),
                                      ("expires_at", 0), ("expires_at", 60)])
def test_stale_future_or_overlong_state_readback_refuses(s, field, delta):
    s.access = replace(s.access, **{field: s.c.h.now + delta})
    with pytest.raises(BindingError, match="^runtime-state-expired$"):
        s.make()


def test_state_readback_is_independent_and_failures_are_safe(s):
    trust = replace(s.trust, readback_principal=s.c.config["services"]["worker_channel"]["principal_ref"])
    with pytest.raises(BindingError, match="^runtime-state-not-independent$"):
        s.make(state_trust=trust)
    def unavailable():
        raise RuntimeError("sensitive-state-reference")
    s.hook = unavailable
    with pytest.raises(BindingError, match="^runtime-state-readback-unavailable$") as caught:
        s.make()
    assert "sensitive" not in str(caught.value)


def test_latest_config_clock_checkpoint_is_retained(s):
    now = s.c.h.now
    samples = iter([now, now, now + 2, now + 1])
    s.ledger.runtime_trust = replace(s.c.trust, clock=lambda: next(samples))
    with pytest.raises(BindingError, match="^runtime-state-clock-unavailable$"):
        s.ledger.check_for_use(deadline=now + 10)


def test_readback_clock_regression_refuses(s):
    s.hook = lambda: setattr(s.c.h, "now", s.c.h.now - 1)
    with pytest.raises(BindingError, match="^runtime-state-clock-unavailable$"):
        s.ledger.check_for_use(deadline=s.c.h.now + 10)


def test_child_latest_clock_checkpoint_survives_return_to_bridge(s):
    now = s.c.h.now
    s.ledger.runtime_trust = replace(s.c.trust, clock=lambda: now + 2)
    with pytest.raises(BindingError):
        s.c.run()  # child observed N+2, parent must not subsequently accept N
    assert s.c.h.calls == 0


def test_parent_latest_clock_checkpoint_reaches_state_before_io(s):
    from workload_factory_binding_runtime.runtime import _Use
    now = s.c.h.now
    s.c.h.now = now + 2
    s.ledger.runtime_trust = replace(s.c.trust, clock=lambda: now)
    use = _Use(s.c.bridge)
    with pytest.raises(BindingError):
        use.check_state()
    assert s.calls == []


def test_reservation_clock_checkpoint_refuses_parent_regression_and_stays_consumed(s):
    original, now = s.ledger.reserve_for_use, s.c.h.now
    def reserve_with_later_clock(**kwargs):
        trust = s.ledger.runtime_trust
        s.ledger.runtime_trust = replace(trust, clock=lambda: now + 2)
        try:
            return original(**kwargs)
        finally:
            s.ledger.runtime_trust = trust
    s.ledger.reserve_for_use = reserve_with_later_clock
    with pytest.raises(BindingError):
        s.c.run()
    assert s.c.h.calls == 0
    with sqlite3.connect(s.directory / "reservations.sqlite") as db:
        assert db.execute("SELECT count(*) FROM reservations").fetchone() == (1,)
    s.c.state = replace(s.c.state, ledger=s.make())
    s.c.bridge = s.c.make()
    with pytest.raises(BindingError):
        s.c.run()
    assert s.c.h.calls == 0


def test_outer_deadline_reaches_state_preflight_and_prevents_reservation(s):
    now = s.c.h.now
    s.c.context = replace(s.c.context, expires_at=now + 2)
    s.hook = lambda: setattr(s.c.h, "now", now + 3)
    with pytest.raises(BindingError):
        s.c.run()
    assert s.calls == [now + 2]
    assert s.c.h.calls == 0
    with sqlite3.connect(s.directory / "reservations.sqlite") as db:
        assert db.execute("SELECT count(*) FROM reservations").fetchone() == (0,)


def test_state_deadline_survives_later_proof_io(s):
    s.access = replace(s.access, expires_at=s.c.h.now + 2)
    s.c.records.hook = lambda: setattr(s.c.h, "now", s.c.h.now + 3)
    with pytest.raises(BindingError):
        s.c.run()
    assert s.c.h.calls == 0


def test_ambiguous_custody_failure_stays_consumed_after_restart(s):
    def ambiguous(message):
        s.c.h.calls += 1
        raise OSError("remote may already have signed")
    s.c.h.sign = ambiguous
    with pytest.raises(BindingError):
        s.c.run()
    assert s.c.h.calls == 1
    s.c.state = replace(s.c.state, ledger=s.make())
    s.c.bridge = s.c.make()
    with pytest.raises(BindingError):
        s.c.run()
    assert s.c.h.calls == 1


def test_failure_after_durable_reservation_never_resets_it(s):
    def revoked_after_commit():
        with sqlite3.connect(s.directory / "reservations.sqlite") as db:
            if db.execute("SELECT count(*) FROM reservations").fetchone()[0]:
                s.access = replace(s.access, status="revoked")
    s.hook = revoked_after_commit
    with pytest.raises(BindingError, match="^runtime-state-recovery-required$"):
        reserve(s)
    s.hook = None
    s.access = replace(s.access, status="active")  # fixture-only return of readback
    restarted = s.make()
    with pytest.raises(BindingError, match="^replay-refused$"):
        reserve(s, restarted)


def test_concurrent_reservations_have_exactly_one_winner(s):
    def attempt(_):
        try:
            reserve(s, s.make())
            return "reserved"
        except BindingError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, range(4)))
    assert sorted(results) == ["replay-refused"] * 3 + ["reserved"]


def test_process_exit_after_commit_is_consumed_on_restart(s):
    def child():
        reserve(s, s.make())
        os._exit(0)  # simulate no application response after durable commit
    process = multiprocessing.get_context("fork").Process(target=child)
    process.start()
    try:
        process.join(timeout=10)
        assert process.exitcode == 0
        restarted = s.make()
        with pytest.raises(BindingError, match="^replay-refused$"):
            reserve(s, restarted)
    finally:
        if process.is_alive():
            process.kill()
            process.join(timeout=5)
        process.close()


def test_observable_loss_between_preflight_and_sqlite_open_never_creates(s, monkeypatch):
    original, calls = sqlite3.connect, []
    path = s.directory / "reservations.sqlite"
    def missing_on_open(*args, **kwargs):
        calls.append(True)
        path.unlink()
        return original(*args, **kwargs)
    monkeypatch.setattr(sqlite3, "connect", missing_on_open)
    with pytest.raises(BindingError, match="^runtime-state-unavailable$"):
        s.ledger.check_for_use(deadline=s.c.h.now + 10)
    assert calls == [True]
    assert not path.exists()


def test_expiry_while_acquiring_write_lock_refuses_before_insert(s, monkeypatch):
    connect, now = sqlite3.connect, s.c.h.now
    class DelayedBegin:
        def __init__(self, db):
            self.db = db
        def __getattr__(self, name):
            return getattr(self.db, name)
        def execute(self, sql, *args):
            result = self.db.execute(sql, *args)
            if sql == "BEGIN IMMEDIATE":
                s.c.h.now = now + 3
            return result
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: DelayedBegin(connect(*args, **kwargs)))
    arguments = dict(deadline=now + 2, issuer="issuer:fixture", jti="token:one",
                     challenge_issuer="challenge:fixture", challenge_id="challenge:one", now=now)
    with pytest.raises(BindingError, match="^runtime-state-expired$"):
        s.ledger.reserve_for_use(**arguments)
    with connect(s.directory / "reservations.sqlite") as db:
        assert db.execute("SELECT count(*) FROM reservations").fetchone() == (0,)


def test_integrity_progress_honors_shorter_enclosing_budget(s, monkeypatch):
    import workload_factory_binding_runtime.state as state
    connect, elapsed, callbacks = sqlite3.connect, [0.0], []
    class ObservedConnection:
        def __init__(self, db):
            self.db = db
        def __getattr__(self, name):
            return getattr(self.db, name)
        def set_progress_handler(self, callback, steps):
            callbacks.append(callback)
            self.db.set_progress_handler(callback, steps)
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: ObservedConnection(connect(*args, **kwargs)))
    monkeypatch.setattr(state.time, "monotonic", lambda: elapsed[0])
    with state._open(s.directory, expected=s.initialization, timeout=1):
        elapsed[0] = 1.5
        assert callbacks[0]() == 1, "integrity work outlived its enclosing budget"


def test_recovery_requires_new_approved_scope_and_initialization(s, tmp_path):
    reserve(s)
    old = s.directory / "reservations.sqlite"
    s.access = replace(s.access, status="revoked")
    with pytest.raises(BindingError):
        s.make()
    replacement = tmp_path / "new-authorized-scope"
    ReplayLedger(replacement)  # explicit fixture/operator provisioning, never runtime
    initialization = inspect_initialized_state(replacement)
    selection = replace(s.selection, store_ref="store:new-scope", initialization_ref="init:new-scope")
    s.c.config["state"] = vars(selection)
    s.c.config["case_ref"] = "case:new-scope"
    s.c.config["launch"]["run_id"] = "9999"
    s.c.reselect_policy()  # explicitly approve a different synthetic configuration
    s.c.context = replace(s.c.context, case_ref="case:new-scope", run_id="9999")
    s.access = replace(s.access, selection=selection, initialization=initialization,
                       config_digest=digest(s.c.config), case_ref="case:new-scope", run_id="9999", status="active")
    trust = replace(s.trust, selection=selection, initialization=initialization)
    recovered = s.make(directory=replacement, state_trust=trust)
    s.c.state = StateBinding(**vars(selection), ledger=recovered)
    s.c.bridge = s.c.make()
    with pytest.raises(BindingError):
        s.c.run()  # the old request/workload is not the newly approved scope
    with sqlite3.connect(old) as db:
        assert db.execute("SELECT count(*) FROM reservations").fetchone() == (1,)
