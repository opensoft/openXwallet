#!/usr/bin/env python3
"""Install for this adapter through the authenticated shared implementation."""
from _shared_openspec import run


def main(argv=None):
    return run("install-pinned-openspec-cli.py", argv)


if __name__ == "__main__":
    raise SystemExit(main())
