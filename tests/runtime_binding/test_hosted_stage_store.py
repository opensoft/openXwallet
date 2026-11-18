"""Real DELETE-journal retirement preserves private retained staging identity."""
from contextlib import closing
import errno
import os
from pathlib import Path
import shutil
import sqlite3

import pytest

from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.stage_store import DB, StageStore, store_identity


def use(now=1002):
    return Decision(clock=lambda: now, monotonic=lambda: 0.)


def existing(tmp_path):
    root = tmp_path / "state"
    identity = StageStore.initialize(root, kind="controller")
    store = StageStore(root, identity=identity, kind="controller")
    assert store.reserve("launch:old", {"source": "fixed"}, decision=use())
    return root, identity, store


@pytest.mark.parametrize("access", ["construct", "reserve", "read"])
def test_real_delete_commit_before_sidecar_snapshot_preserves_durable_access(tmp_path, monkeypatch, access):
    root, identity, store = existing(tmp_path)
    journal = root / (DB + "-journal")
    committed = []
    original = Path.lstat
    with closing(sqlite3.connect(root / DB, isolation_level=None)) as other:
        other.execute("BEGIN IMMEDIATE")
        other.execute("UPDATE metadata SET highwater=1003")
        assert journal.exists()
        def retire(path, *args, **kwargs):
            if path == journal and not committed:
                other.execute("COMMIT")
                committed.append(True)
            return original(path, *args, **kwargs)
        monkeypatch.setattr(Path, "lstat", retire)
        try:
            if access == "construct":
                current = StageStore(root, identity=identity, kind="controller")
                assert current.read("launch:old", decision=use(1004))["state"] == "reserved"
            elif access == "reserve":
                assert store.reserve("launch:new", {"source": "fixed"}, decision=use(1004))
                assert store.read("launch:new", decision=use(1004))["state"] == "reserved"
            else:
                assert store.read("launch:old", decision=use(1004))["state"] == "reserved"
            assert committed == [True]
            assert not journal.exists()
            assert store_identity(root) == identity
            reopened = StageStore(root, identity=identity, kind="controller")
            assert not reopened.reserve("launch:old", {"source": "fixed"}, decision=use(1004))
        finally:
            if other.in_transaction:
                other.rollback()


def test_valid_active_private_delete_journal_is_allowed(tmp_path):
    root, identity, _ = existing(tmp_path)
    with closing(sqlite3.connect(root / DB, isolation_level=None)) as other:
        other.execute("BEGIN IMMEDIATE")
        other.execute("UPDATE metadata SET highwater=1003")
        try:
            journal = root / (DB + "-journal")
            assert journal.is_file()
            assert journal.stat().st_mode & 0o777 == 0o600
            StageStore(root, identity=identity, kind="controller")
        finally:
            other.rollback()
    assert store_identity(root) == identity


UNSAFE = [(suffix, shape) for suffix in ("-journal", "-wal", "-shm")
          for shape in (("symlink", "dangling", "directory", "fifo", "owner", "mode", "hardlink")
                        if suffix == "-journal" else
                        ("private", "symlink", "dangling", "directory", "fifo", "owner", "mode", "hardlink"))]


@pytest.mark.parametrize("suffix,shape", UNSAFE, ids=[s[1:] + "-" + k for s, k in UNSAFE])
def test_every_observed_unsafe_sidecar_is_refused(tmp_path, monkeypatch, suffix, shape):
    root, identity, _ = existing(tmp_path)
    sidecar = root / (DB + suffix)
    target = tmp_path / "private-target"
    target.write_bytes(b"isolated-sidecar-control")
    target.chmod(0o600)
    if shape == "directory":
        sidecar.mkdir(mode=0o700)
    elif shape == "fifo":
        os.mkfifo(sidecar, 0o600)
    elif shape in ("symlink", "dangling"):
        sidecar.symlink_to(target if shape == "symlink" else tmp_path / "missing")
    elif shape == "hardlink":
        os.link(target, sidecar)
    else:
        sidecar.write_bytes(b"isolated-sidecar-control")
        sidecar.chmod(0o644 if shape == "mode" else 0o600)
    if shape == "owner":
        original = Path.lstat
        def wrong_owner(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path == sidecar:
                fields = list(info)
                fields[4] = os.geteuid() + 1
                return os.stat_result(fields)
            return info
        monkeypatch.setattr(Path, "lstat", wrong_owner)
    with pytest.raises(BindingError, match="^hosted-stage-refused$"):
        StageStore(root, identity=identity, kind="controller")


@pytest.mark.parametrize("suffix", ["-journal", "-wal", "-shm"], ids=["journal", "wal", "shm"])
@pytest.mark.parametrize("error_type,error_number", [(PermissionError, errno.EACCES),
                         (NotADirectoryError, errno.ENOTDIR), (OSError, errno.EIO)],
                         ids=["permission", "not-a-directory", "io"])
def test_non_enoent_sidecar_lookup_errors_refuse(tmp_path, monkeypatch, suffix, error_type, error_number):
    root, identity, _ = existing(tmp_path)
    sidecar = root / (DB + suffix)
    original = Path.lstat
    def failed_lookup(path, *args, **kwargs):
        if path == sidecar:
            raise error_type(error_number, "isolated-sidecar-error")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", failed_lookup)
    with pytest.raises(BindingError, match="^hosted-stage-refused$"):
        StageStore(root, identity=identity, kind="controller")


@pytest.mark.parametrize("change", ["directory-removed", "directory-replaced", "directory-permissions",
                         "directory-symlink", "database-removed", "database-replaced",
                         "database-permissions", "database-symlink", "database-hardlink"])
def test_main_loss_replacement_or_unsafe_metadata_during_sidecar_lookup_refuses(tmp_path, monkeypatch, change):
    root, identity, _ = existing(tmp_path)
    database = root / DB
    journal = root / (DB + "-journal")
    original = Path.lstat
    changed = []
    def main_changed(path, *args, **kwargs):
        if path == journal and not changed:
            changed.append(True)
            if change.startswith("directory-"):
                if change == "directory-permissions":
                    root.chmod(0o755)
                else:
                    retained = tmp_path / "retained-state"
                    root.rename(retained)
                    if change == "directory-replaced":
                        root.mkdir(mode=0o700)
                        shutil.copyfile(retained / DB, database)
                        database.chmod(0o600)
                    elif change == "directory-symlink":
                        root.symlink_to(retained, target_is_directory=True)
            elif change == "database-permissions":
                database.chmod(0o644)
            elif change == "database-hardlink":
                os.link(database, tmp_path / "database-alias")
            else:
                retained = tmp_path / "retained.sqlite"
                database.rename(retained)
                if change == "database-replaced":
                    shutil.copyfile(retained, database)
                    database.chmod(0o600)
                elif change == "database-symlink":
                    database.symlink_to(retained)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", main_changed)
    with pytest.raises(BindingError, match="^hosted-stage-refused$"):
        StageStore(root, identity=identity, kind="controller")
    assert changed == [True]
    if change == "directory-removed":
        assert not root.exists()
        assert (tmp_path / "retained-state" / DB).is_file()
    elif change == "database-removed":
        assert not database.exists()
        assert (tmp_path / "retained.sqlite").is_file()


@pytest.mark.parametrize("suffix", ["-journal", "-wal", "-shm"], ids=["journal", "wal", "shm"])
def test_unsafe_observed_snapshot_still_refuses_after_sidecar_disappears(tmp_path, monkeypatch, suffix):
    root, identity, _ = existing(tmp_path)
    sidecar = root / (DB + suffix)
    sidecar.write_bytes(b"isolated-unsafe-snapshot")
    sidecar.chmod(0o644 if suffix == "-journal" else 0o600)
    original = Path.lstat
    removed = []
    def disappear_after_snapshot(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if path == sidecar and not removed:
            sidecar.unlink()
            removed.append(True)
        return info
    monkeypatch.setattr(Path, "lstat", disappear_after_snapshot)
    with pytest.raises(BindingError, match="^hosted-stage-refused$"):
        StageStore(root, identity=identity, kind="controller")
    assert removed == [True]
    assert not sidecar.exists()
