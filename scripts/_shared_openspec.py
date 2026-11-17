"""Load the pinned neutral OpenSpec implementation for this adapter.

Only tooling depends on the initialized spec leg. Product validation retains its
existing root/code boundary. Every load verifies the declared root/code pin and
the spec gitlink, then compiles the exact pinned regular source bytes.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("validate-openspec-cli-pin.py", "install-pinned-openspec-cli.py")


class SharedToolRefusal(ValueError):
    """The pinned implementation cannot be executed safely."""


def git(root, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(root), *arguments], stderr=subprocess.PIPE)


def regular_bytes(path):
    if path.is_symlink() or path.resolve(strict=True) != path or not path.is_file():
        raise SharedToolRefusal("linked or missing shared source")
    return path.read_bytes()


def source_module(name, path, raw, bindings=None):
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__spec__ = importlib.util.spec_from_file_location(name, path)
    module.__dict__.update(bindings or {})
    # Dataclasses and other source-level annotations resolve their own module.
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def shared_sources(root=ROOT):
    """Authenticate the complete existing pin and both shared entrypoints."""
    try:
        root = Path(root).absolute()
        path = root / "scripts/verify-openwallet-pin.py"
        verifier = source_module(
            "wallet_shared_pin_verifier", path, regular_bytes(path))
        try:
            verified = verifier.verify(root)
        except verifier.PinRefusal as exc:
            raise SharedToolRefusal("openWallet root/code pin refused") from exc
        neutral = root / "openWallet"
        entry = git(neutral, "ls-tree", verified.commit, "spec").decode().strip()
        fields = entry.split()
        if len(fields) != 4 or fields[0:2] != ["160000", "commit"] or fields[3] != "spec":
            raise SharedToolRefusal("pinned spec gitlink missing")
        revision = fields[2]
        spec = neutral / "spec"
        if (spec.is_symlink() or spec.resolve(strict=True) != spec
                or git(spec, "rev-parse", "--show-toplevel").decode().strip() != str(spec)
                or git(spec, "rev-parse", "HEAD").decode().strip() != revision):
            raise SharedToolRefusal("initialized spec checkout differs from pinned root")
        sources = {}
        for name in SOURCES:
            relative = "scripts/" + name
            path = spec / relative
            metadata = git(spec, "ls-tree", revision, relative).decode().split()
            if (len(metadata) != 4 or metadata[0] not in ("100644", "100755")
                    or metadata[1] != "blob"):
                raise SharedToolRefusal("pinned shared source is not regular")
            raw = regular_bytes(path)
            if raw != git(spec, "show", revision + ":" + relative):
                raise SharedToolRefusal("shared source differs from pinned bytes")
            sources[name] = (path, raw)
        return sources
    except SharedToolRefusal:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise SharedToolRefusal(
            "openWallet root, code and spec must satisfy the declared pin") from exc


def load_shared(name, root=ROOT):
    if name not in SOURCES:
        raise SharedToolRefusal("unknown shared entrypoint")
    sources = shared_sources(root)
    path, raw = sources[SOURCES[0]]
    verifier = source_module("wallet_shared_verifier", path, raw)
    if name == SOURCES[0]:
        return verifier
    path, raw = sources[SOURCES[1]]
    return source_module("wallet_shared_installer", path, raw,
                         {"VERIFIED_VERIFIER": verifier})


def run(name, argv=None):
    try:
        module = load_shared(name)
    except SharedToolRefusal as exc:
        print("REFUSE pin-unresolvable: " + str(exc), file=sys.stderr)
        return 2
    return module.main(argv, consumer_root=ROOT)
