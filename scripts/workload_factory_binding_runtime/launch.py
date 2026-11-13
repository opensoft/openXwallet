"""Bounded Linux controlled-launch measurement; not memory/host attestation.

The independent controller selects the process, paths and executable digest.
Deployment must keep launch files/control outside worker writes. Before/after
snapshots detect observable changes; they do not prove arbitrary in-memory code,
continuous liveness, hostile-host safety or changes restored between snapshots.
"""
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
from types import MappingProxyType

from workload_factory_binding.evidence import (
    BindingError, decode_object, digest, integer, reference, require, valid_digest,
)


def _plain(value):
    if isinstance(value, Mapping):
        return {name: _plain(item) for name, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def worker_configuration(selection, policy):
    """Internal non-secret launch projection; excludes self-referential hashes."""
    return {"profile": "openxfactory-supervisor-launch-internal-v1",
            **{name: _plain(selection[name]) for name in
               ("case_ref", "launch", "sources", "dependency_digest", "services")},
            "binding": _plain(policy["binding"]),
            "authority": {name: policy[name] for name in ("policy_ref", "revision", "grant_ref")},
            "supervisor_public_key": policy["supervisor_public_key"]}


def _fresh(clock, deadline):
    try:
        now = clock()
        require(integer(now) and integer(deadline) and now < deadline, "launch-measurement-expired")
        return now
    except BindingError:
        raise
    except Exception:
        raise BindingError("launch-clock-unavailable") from None


def _stamp(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _regular(path, limit, *, hash_only=False, follow=False, clock=None, deadline=None):
    flags = os.O_RDONLY | os.O_NONBLOCK
    if not follow:
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= limit, "invalid-launch-file")
        if hash_only:
            hashed, count = hashlib.sha256(), 0
            while chunk := stream.read(65536):
                count += len(chunk)
                require(count <= limit, "invalid-launch-file")
                hashed.update(chunk)
                if clock is not None:
                    _fresh(clock, deadline)
            value = "sha256:" + hashed.hexdigest()
        else:
            value = stream.read(limit + 1)
            require(len(value) <= limit, "invalid-launch-file")
        require(_stamp(before) == _stamp(os.fstat(stream.fileno())), "launch-file-changed")
        return value


def _kernel(path, limit):
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(0 < len(raw) <= limit, "invalid-launch-process")
    return raw


def _generation(pid):
    raw = _kernel(Path("/proc") / str(pid) / "stat", 4096)
    fields = raw.rpartition(b")")[2].split()
    require(len(fields) > 19 and fields[0] not in (b"Z", b"X", b"x")
            and fields[19].isdigit(), "invalid-launch-process")
    start = int(fields[19])
    require(integer(start) and start > 0, "invalid-launch-process")
    return start


@dataclass(frozen=True, repr=False)
class ProcessLaunch:
    """Protected controller selection for one isolated-Python script generation.

    No launch/spawn/kill operation or worker-selected PID/path is exposed here.
    Executable digest is an explicit approved input, never trust-on-first-use.
    """
    pid: int
    start_time: int
    executable: object
    executable_digest: str
    worker: object
    configuration_file: object
    cwd: object
    artifacts: object

    def __post_init__(self):
        require(integer(self.pid) and self.pid > 0 and integer(self.start_time) and self.start_time > 0
                and valid_digest(self.executable_digest), "invalid-launch-selection")
        for name in ("executable", "worker", "configuration_file", "cwd"):
            object.__setattr__(self, name, Path(getattr(self, name)).resolve())
        require(isinstance(self.artifacts, Mapping), "invalid-launch-selection")
        artifacts = {name: Path(path).resolve() for name, path in self.artifacts.items()}
        artifacts["measurement_module"] = Path(__file__).resolve()
        require(0 < len(artifacts) <= 32 and all(reference(name) for name in artifacts)
                and artifacts.get("worker") == self.worker and "supervisor" in artifacts,
                "invalid-launch-selection")
        object.__setattr__(self, "artifacts", MappingProxyType(artifacts))

    @classmethod
    def capture(cls, process, **selection):
        try:
            require(process.poll() is None, "invalid-launch-process")
            return cls(pid=process.pid, start_time=_generation(process.pid), **selection)
        except BindingError:
            raise
        except Exception:
            raise BindingError("launch-measurement-unavailable") from None

    @property
    def argv(self):
        return (str(self.executable), "-I", "-B", str(self.worker), str(self.configuration_file))

    def expected_configuration(self, configuration):
        return {"worker_configuration": _plain(configuration), "process": {
            "pid": self.pid, "start_time": self.start_time, "argv": list(self.argv),
            "cwd": str(self.cwd), "executable_digest": self.executable_digest}}

    def _process(self, clock, deadline):
        proc = Path("/proc") / str(self.pid)
        require(_generation(self.pid) == self.start_time, "launch-generation-mismatch")
        raw = _kernel(proc / "cmdline", 16384)
        require(raw.endswith(b"\0"), "invalid-launch-process")
        argv = tuple(os.fsdecode(part) for part in raw[:-1].split(b"\0"))
        require(argv == self.argv and os.readlink(proc / "cwd") == str(self.cwd)
                and os.readlink(proc / "exe") == str(self.executable), "launch-process-mismatch")
        actual_executable = _regular(proc / "exe", 32 * 1024 * 1024, hash_only=True,
                                     follow=True, clock=clock, deadline=deadline)
        require(actual_executable == self.executable_digest, "launch-executable-mismatch")
        return {"pid": self.pid, "start_time": self.start_time, "argv": list(argv),
                "cwd": str(self.cwd), "executable_digest": actual_executable}

    def measure(self, configuration, selection, *, deadline, clock):
        try:
            _fresh(clock, deadline)
            before = self._process(clock, deadline)
            actual = decode_object(_regular(self.configuration_file, 16384))
            require(digest(actual) == digest(configuration), "launch-configuration-mismatch")
            measured = {name: _regular(path, 1024 * 1024, hash_only=True, clock=clock, deadline=deadline)
                        for name, path in self.artifacts.items()}
            require(all(measured[name] == selection["sources"][name]["digest"]
                        for name in ("worker", "supervisor")), "launch-source-mismatch")
            after = self._process(clock, deadline)
            require(before == after, "launch-process-changed")
            _fresh(clock, deadline)
            # Exactly the accepted artifact_digest structure, with real process metadata.
            return digest({"artifacts": measured, "configuration": {
                "worker_configuration": actual, "process": after}})
        except BindingError:
            raise
        except Exception:
            raise BindingError("launch-measurement-unavailable") from None
