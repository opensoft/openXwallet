"""Selected file generations: durable run anchors and retained inode handles.

The initialized pin directory belongs to the primary retained lifecycle store.
A fresh path-based provider cannot adopt an old provider epoch. No anchor is
created by observation, reopening or cleanup; only first registration may pin.
"""
from contextlib import contextmanager
import fcntl
import os
import stat
import time
from workload_factory_binding.evidence import BindingError, digest, require
from .lifecycle_store import LifecycleStore, ERROR


def instance(info):
    return f"file:{info.st_dev}:{info.st_ino}"


def regular(info):
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid(), ERROR)


def directory_identity(fd, path, expected):
    info, current = os.fstat(fd), path.lstat()
    require(stat.S_ISDIR(info.st_mode)
            and (info.st_dev, info.st_ino) == (current.st_dev, current.st_ino) == expected
            and info.st_uid == os.geteuid() and not info.st_mode & 0o077 and path.resolve() == path, ERROR)


def bounded_lock(fd, decision, until):
    while True:
        decision.now()
        require(time.monotonic() < until, ERROR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            decision.now()
            return
        except BlockingIOError:
            decision.now()
            require(time.monotonic() < until, ERROR)
            time.sleep(min(.005, decision.remaining(), max(0, until - time.monotonic())))


class FilePins:
    def __init__(self, *, selected, roots, store, epoch):
        require(type(store) is LifecycleStore and store.kind == "primary", ERROR)
        self.selected, self.roots, self.store, self.epoch = selected, roots, store, epoch
        self.root = store.directory / "file-pins"
        self.identity = store.identity[-1]
        self.kept, self.closed = {}, False
        try:
            require(self.root.resolve() == self.root, ERROR)
            for ref, value in selected.items():
                require(not value.path.is_relative_to(self.root), ERROR)
                if value.retention == "run":
                    require(roots[ref][0] == self.identity[0], ERROR)
                if value.path.exists():
                    info = value.path.lstat()
                    regular(info)
                    require(info.st_nlink == 1 and (value.retention != "run" or info.st_dev == self.identity[0]), ERROR)
                if value.retention != "run":
                    with self.directory(ref) as fd:
                        pin = os.open(value.path.name, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
                        try:
                            info = os.fstat(pin)
                            regular(info)
                            require(info.st_nlink == 1, ERROR)
                            self.kept[ref] = pin
                        except BaseException:
                            os.close(pin)
                            raise
        except Exception:
            self.close()
            raise BindingError(ERROR) from None

    def close(self):
        if not self.closed:
            self.closed = True
            for fd in self.kept.values():
                os.close(fd)
            self.kept.clear()

    @contextmanager
    def directory(self, ref, *, decision=None, until=None):
        require(not self.closed, ERROR)
        path = self.selected[ref].path.parent
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            directory_identity(fd, path, self.roots[ref])
            if decision is None:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                bounded_lock(fd, decision, until)
            directory_identity(fd, path, self.roots[ref])
            yield fd
        finally:
            os.close(fd)

    @contextmanager
    def pinned(self, ref, decision):
        decision.now()
        # Both acquisitions share one bounded wait and the original Decision.
        # Parent then pins then journal is the only ownership-fence order.
        until = time.monotonic() + min(1, decision.remaining())
        with self.directory(ref, decision=decision, until=until) as parent:
            fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                directory_identity(fd, self.root, self.identity)
                bounded_lock(fd, decision, until)
                directory_identity(fd, self.root, self.identity)
                decision.now()
                yield parent, fd
            finally:
                os.close(fd)

    def slot(self, ref):
        value = self.selected[ref]
        return digest({"epoch": self.epoch, "ref": ref, "parent": self.roots[ref],
                       "name": value.path.name}).split(":")[1]

    @staticmethod
    def info(fd, name):
        try:
            value = os.stat(name, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        regular(value)
        return value

    def retired(self, ref, decision):
        values = [e["data"] for e in self.store.events(decision=decision)
                  if e["kind"] == "file-retired" and e["data"].get("epoch") == self.epoch
                  and e["data"].get("ref") == ref]
        require(len(values) <= 1, ERROR)
        if not values:
            return None
        value = values[0]
        require(set(value) == {"epoch", "ref", "slot", "instance_ref"}
                and value["slot"] == self.slot(ref), ERROR)
        return value

    def inventory(self, ref, *, decision, initialize):
        with self.pinned(ref, decision) as (parent, pins):
            value = self.selected[ref]
            actual = self.info(parent, value.path.name)
            require(actual is not None, ERROR)
            if value.retention != "run":
                original = os.fstat(self.kept[ref])
                require(instance(actual) == instance(original) and actual.st_nlink == 1, ERROR)
                return instance(actual)
            require(self.retired(ref, decision) is None, ERROR)
            anchor = self.info(pins, self.slot(ref))
            if anchor is None:
                require(initialize and actual.st_nlink == 1, ERROR)
                decision.now()
                os.link(value.path.name, self.slot(ref), src_dir_fd=parent, dst_dir_fd=pins, follow_symlinks=False)
                os.fsync(pins)
                anchor = self.info(pins, self.slot(ref))
            current = self.info(parent, value.path.name)
            require(anchor is not None and current is not None
                    and instance(anchor) == instance(current) == instance(actual)
                    and anchor.st_nlink == current.st_nlink == 2, ERROR)
            decision.now()
            return instance(anchor)

    def observe(self, ref, expected, *, decision):
        with self.pinned(ref, decision) as (parent, pins):
            value = self.selected[ref]
            actual = self.info(parent, value.path.name)
            if value.retention != "run":
                original = os.fstat(self.kept[ref])
                regular(original)
                require(instance(original) == expected, ERROR)
                if actual is None:
                    return expected, False
                require(actual.st_nlink == 1, ERROR)
                return instance(actual), True
            marker = self.retired(ref, decision)
            anchor = self.info(pins, self.slot(ref))
            if marker is not None:
                require(marker["instance_ref"] == expected and anchor is None, ERROR)
                # Once the original anchor is retired, any newly present path
                # is a replacement, even if its inode number was recycled.
                return (("file-replacement:" + instance(actual)) if actual else expected), actual is not None
            require(anchor is not None and instance(anchor) == expected and anchor.st_nlink in (1, 2), ERROR)
            if actual is None:
                return expected, True  # the private anchor still retains data
            require(actual.st_nlink == (2 if instance(actual) == expected else 1), ERROR)
            return instance(actual), True

    def retire(self, ref, expected, *, decision, claim=None):
        with self.pinned(ref, decision) as (parent, pins):
            value = self.selected[ref]
            require(value.retention == "run", ERROR)
            marker = self.retired(ref, decision)
            actual, anchor = self.info(parent, value.path.name), self.info(pins, self.slot(ref))
            if marker is not None:
                require(marker["instance_ref"] == expected and actual is None and anchor is None, ERROR)
                return
            require(anchor is not None and instance(anchor) == expected, ERROR)
            if actual is not None:
                require(instance(actual) == expected and actual.st_nlink == anchor.st_nlink == 2, ERROR)
            else:
                require(anchor.st_nlink == 1, ERROR)
            decision.now()
            if claim is not None:
                require(claim(), ERROR)
            decision.now()
            if actual is not None:
                os.unlink(value.path.name, dir_fd=parent)
                os.fsync(parent)
            decision.now()
            os.unlink(self.slot(ref), dir_fd=pins)
            os.fsync(pins)
            decision.now()
            # A crash before this durable marker leaves retirement unknown.
            # Observation never recreates the anchor or repeats an unlink.
            self.store.record("file-retired", {"epoch": self.epoch, "ref": ref,
                "slot": self.slot(ref), "instance_ref": expected}, decision=decision)
