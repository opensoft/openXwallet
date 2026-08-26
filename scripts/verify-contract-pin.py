#!/usr/bin/env python3
"""Verify the vendored openxFactory artifact against contract_pin.yaml.

openXwallet vendors exactly ONE artifact it does not own:
``contracts/schemas/hermes-job-envelope.schema.yaml``, from which
``scripts/validate-openxwallet.py`` rule (g) reads the approval-scope
vocabulary. ``main()`` in that validator checks only
``ENVELOPE_SCHEMA_PATH.is_file()`` -- PRESENCE, not identity -- so a swapped or
edited copy would silently redefine the vocabulary the gate enforces. This tool
closes that gap, and it runs as the FIRST step of the ``wallet-validation`` job,
before the syntax gate and before the validator.

FAIL-CLOSED PRE-SYNC (openAvatar's doctrine, ``openAvatar/contract_pin.yaml``):

  rule 1  an empty or absent ``commit`` is not content-addressed -> reject
  rule 2  a recomputed digest can never equal an empty recorded digest
          -> drift -> fail BEFORE any test runs

OFFLINE LAW. This tool reads ``contract_pin.yaml`` and the files it names. It
never reads the network, never reads an upstream tree, and never reads
``contracts/manifest.yaml`` -- the live manifest cross-check is a SYNC-TIME
obligation (``docs/pin-resync-runbook.md``), never a CI read.

Every refusal carries its remediation, because a refusal that names what is
wrong without naming what to run puts the exit in tribal memory instead of in
the message.

Exit codes:
  0  every pinned file present and its recomputed sha256 equals the recorded one
  1  drift, a missing file, a missing/empty digest, or a bad/absent commit
  2  environment: contract_pin.yaml absent, unparseable, or PyYAML unavailable
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / "contract_pin.yaml"
RESYNC_RUNBOOK = "docs/pin-resync-runbook.md"
SUBMODULE_REMEDIATION = "git submodule update --init openXwallet"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR PyYAML is required to read contract_pin.yaml", file=sys.stderr)
    sys.exit(2)


def refuse(*findings: str) -> int:
    """Print every finding, then the remediation trailer, and return 1.

    The remediation is part of the refusal (clarification N1): each refusal
    names the submodule init AND the path of the re-sync runbook, so the exit
    is in the message rather than in tribal memory.
    """
    for finding in findings:
        print(f"REFUSED {finding}", file=sys.stderr)
    print(f"  remediation: {SUBMODULE_REMEDIATION}", file=sys.stderr)
    print(f"  remediation: see {RESYNC_RUNBOOK}", file=sys.stderr)
    return 1


def main() -> int:
    if not PIN_PATH.is_file():
        print(f"ERROR {PIN_PATH.relative_to(ROOT)} not found", file=sys.stderr)
        return 2
    try:
        pin = yaml.safe_load(PIN_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"ERROR {PIN_PATH.relative_to(ROOT)} does not parse: {exc}",
              file=sys.stderr)
        return 2
    if not isinstance(pin, dict):
        print(f"ERROR {PIN_PATH.relative_to(ROOT)} is not a mapping",
              file=sys.stderr)
        return 2

    findings: list[str] = []

    # ---- rule 1: the pin must be content-addressed at all -------------------
    commit = str(pin.get("commit") or "").strip()
    if not commit:
        findings.append(
            "contract_pin.yaml records no commit; a pin without a commit is "
            "not content-addressed (fail-closed rule 1)")
    elif not COMMIT_RE.match(commit):
        findings.append(
            f"contract_pin.yaml commit {commit!r} is not a 40-hex commit; a "
            "movable branch or tag is not a compatibility pin")
    if str(pin.get("revision_kind") or "").strip() != "commit":
        findings.append(
            f"contract_pin.yaml revision_kind is "
            f"{pin.get('revision_kind')!r}, expected 'commit'")

    entries = pin.get("files")
    if not isinstance(entries, list) or not entries:
        findings.append("contract_pin.yaml lists no files: nothing is pinned")
        return refuse(*findings)

    # ---- rule 2: recompute every digest ------------------------------------
    checked = 0
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("path"):
            findings.append(f"contract_pin.yaml files entry is malformed: {entry!r}")
            continue
        rel = str(entry["path"])
        recorded = str(entry.get("sha256") or "").strip()
        target = ROOT / rel

        if not recorded:
            # A recomputed digest can never equal an empty recorded digest.
            findings.append(
                f"{rel}: no sha256 recorded in contract_pin.yaml; a recomputed "
                "digest can never equal an empty one (fail-closed rule 2)")
            continue
        if not SHA256_RE.match(recorded):
            findings.append(
                f"{rel}: recorded sha256 {recorded!r} is not 64 lowercase hex")
            continue
        if not target.is_file():
            findings.append(
                f"{rel}: vendored file is MISSING; the pinned openxFactory "
                "artifact is not present in this checkout")
            continue

        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        checked += 1
        if actual != recorded:
            findings.append(
                f"{rel}: DIGEST DRIFT\n"
                f"          recorded   {recorded}\n"
                f"          recomputed {actual}\n"
                f"        the vendored copy is not the openxFactory artifact "
                f"pinned at {commit or '<no commit>'}")
        else:
            print(f"OK {rel} sha256={actual} verified against contract_pin.yaml "
                  f"(openxFactory@{commit[:12]}, bundle "
                  f"{pin.get('pinned_bundle', '<unrecorded>')})")

    if findings:
        return refuse(*findings)

    print(f"OK contract pin verified: {checked} vendored file(s) match "
          f"contract_pin.yaml at openxFactory@{commit[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
