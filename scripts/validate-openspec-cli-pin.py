#!/usr/bin/env python3
"""Validate this adapter with the authenticated shared OpenSpec implementation."""
from _shared_openspec import run


def main(argv=None):
    return run("validate-openspec-cli-pin.py", argv)


if __name__ == "__main__":
    raise SystemExit(main())
