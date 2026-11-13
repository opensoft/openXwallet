"""Linux CI namespace boundary. This is test tooling, not pilot deployment.

Invoke as root only *after* unshare --net (or in a private network-none container).
The child drops all capabilities/groups and cannot regain privileges on exec.
"""
import argparse
import ctypes
import fcntl
import os
from pathlib import Path
import socket
import stat
import struct
import sys

ENVIRONMENT = {"PATH", "LANG", "HOME", "TMPDIR", "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
               "PYTHONDONTWRITEBYTECODE", "WALLET_BINDING_OWNER_CODE", "GIT_CONFIG_NOSYSTEM",
               "GIT_CONFIG_GLOBAL", "GIT_OPTIONAL_LOCKS", "LC_CTYPE"}


def validate_boundary(names, status, uid, groups, environment):
    if (set(names) != {"lo"} or uid == 0 or groups or status.get("NoNewPrivs") != "1"
            or any(int(status.get(key, "1"), 16) != 0 for key in ("CapEff", "CapPrm", "CapAmb", "CapBnd"))
            or set(environment) - ENVIRONMENT):
        raise RuntimeError("offline-boundary-invalid")


def assert_isolated():
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    status = {name: value.strip() for name, value in status.items()}
    validate_boundary([name for _, name in socket.if_nameindex()], status, os.geteuid(), os.getgroups(), os.environ)


def private_root(path, uid):
    path = Path(path).absolute()
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700
            or info.st_uid != uid or path.resolve() != path):
        raise RuntimeError("offline-temp-root-invalid")
    return path


def bootstrap(uid, python, temp_root, owner):
    if os.geteuid() != 0 or uid <= 0 or {name for _, name in socket.if_nameindex()} != {"lo"}:
        raise RuntimeError("offline-bootstrap-invalid")
    root = private_root(temp_root, uid)
    home, temporary = root / "home", root / "tmp"
    for directory in (home, temporary):
        directory.mkdir(mode=0o700)  # must be new; never reuse/delete a supplied tree
        os.chown(directory, uid, 65534)
    # Linux SIOCGIFFLAGS/SIOCSIFFLAGS, IFF_UP. No iproute package dependency.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as control:
        request = struct.pack("16sh", b"lo", 0)
        flags = struct.unpack("16sh", fcntl.ioctl(control.fileno(), 0x8913, request))[1]
        if not flags & 1:
            fcntl.ioctl(control.fileno(), 0x8914, struct.pack("16sh", b"lo", flags | 1))
    libc = ctypes.CDLL(None, use_errno=True)
    for capability in range(int(Path("/proc/sys/kernel/cap_last_cap").read_text()) + 1):
        if libc.prctl(24, capability, 0, 0, 0) != 0:  # PR_CAPBSET_DROP
            raise RuntimeError("offline-capability-drop-failed")
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise RuntimeError("offline-privilege-drop-failed")
    os.setgroups([])
    os.setgid(65534)
    os.setuid(uid)
    os.umask(0o022)  # retain deliberate unsafe-permission negative fixtures
    environment = {"PATH": os.defpath, "LANG": "C.UTF-8", "HOME": str(home), "TMPDIR": str(temporary),
                   "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1",
                   "WALLET_BINDING_OWNER_CODE": str(Path(owner).absolute()), "GIT_CONFIG_NOSYSTEM": "1",
                   "GIT_CONFIG_GLOBAL": str(home / "gitconfig"), "GIT_OPTIONAL_LOCKS": "0"}
    repo = Path(__file__).resolve().parents[2]
    os.chdir(repo)
    executable = str(Path(python).absolute())  # preserve venv symlink context
    os.execve(executable, [executable, "-I", "-B", str(repo / "tests/runtime_binding/conformance.py"),
                          "--owner-code", environment["WALLET_BINDING_OWNER_CODE"], "--temp-root", str(root)], environment)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uid", required=True, type=int)
    parser.add_argument("--python", required=True)
    parser.add_argument("--temp-root", required=True)
    parser.add_argument("--owner-code", required=True)
    args = parser.parse_args()
    try:
        bootstrap(args.uid, args.python, args.temp_root, args.owner_code)
    except Exception:
        print("offline-bootstrap-failed", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
