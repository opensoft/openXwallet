"""Select the immutable system runtime for stdlib-only inert fixture workers.

The driver may be a writable hosted tool-cache interpreter with test dependencies;
that is not an eligible worker runtime. Do not mutate or weaken that cache's mode.
"""
import os
from pathlib import Path
import shutil
import subprocess


def system_runtime():
    command=shutil.which("python3",path=os.defpath)
    if command is None:raise RuntimeError("fixture-system-runtime-unavailable")
    executable=Path(command).resolve(strict=True)
    raw=subprocess.check_output([str(executable),"-I","-S","-c","import sys;print(sys.base_prefix)"],
        env={"PATH":os.defpath,"LANG":"C.UTF-8"},timeout=5)
    prefix=Path(raw.decode().strip()).resolve(strict=True)
    runtime=(prefix/"lib").resolve(strict=True)
    if not runtime.is_dir() or runtime.stat().st_mode&0o022:
        raise RuntimeError("fixture-system-runtime-unavailable")
    return executable,(runtime,)
