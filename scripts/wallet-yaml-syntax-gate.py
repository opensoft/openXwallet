#!/usr/bin/env python3
"""Syntax gate over the openxWallet family's YAML surfaces: openXwallet's
ENTRYPOINT to the pinned core's gate (split-openwallet-neutral-core, task 5.3).

The gate is the neutral core's (feature 010-wallet-validator-ci, R7: a
syntax-only complement to the validator's layer 2, which skips a file whose
YAML does not parse). openxFactory's consumer gate invokes
`openXwallet/scripts/wallet-yaml-syntax-gate.py` BY PATH, so this file stays
where it is, with the same command line and the same exit codes:

    python3 scripts/wallet-yaml-syntax-gate.py [PATH]

It holds NO implementation. It path-loads the pinned gate,
`openWallet/code/scripts/wallet-yaml-syntax-gate.py`, and returns its `main()`,
so the bytes that run are the pinned bytes, whatever this file says.

WHY DELEGATE `main()` AND NOT RE-EXPORT `KIND_TO_SCHEMA` (design.md D5 leaves
it to the plan; this is the call). A re-export would keep this file's own walk,
parse and report beside the core's: a second copy of the gate, free to drift
from the one the pin names. Delegating leaves one walk, one parse, one report,
and one kind vocabulary: the pinned gate reads `KIND_TO_SCHEMA` from ITS sibling,
the pinned validator core, which is the vocabulary this repository's validator
runs too, because the adapter adds no kind.

FAIL CLOSED FIRST, as scripts/validate-openxwallet.py does, and under the same
codes for the same facts: an uninitialized `openWallet/` or `openWallet/code/`,
or a pinned gate that does not load, is exit 2 with a named refusal and that
level's remediation. A gate that could not find its implementation must never
read as a gate that found nothing to refuse.

Exit codes: 0 ok, 1 findings, 2 harness error (fail-closed, including an
uninitialized mount and an unloadable pinned gate).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_GATE_PATH = (ROOT / "openWallet" / "code" / "scripts"
                  / "wallet-yaml-syntax-gate.py")

# The remediations, one per level, worded as scripts/validate-openxwallet.py
# words them (design.md D5, "the remediation for THAT level"). Scoped, never
# --recursive: the spec leg carries nothing this gate reads.
ROOT_INIT = "git submodule update --init openWallet"
LEG_INIT = "git -C openWallet submodule update --init code"
VERIFY_PIN = "python3 scripts/verify-openwallet-pin.py"
ROOT_REMEDIATION = (f"Remediation: run `{ROOT_INIT}`, then `{LEG_INIT}` "
                    f"(scoped, never --recursive), then `{VERIFY_PIN}`.")
LEG_REMEDIATION = (f"Remediation: run `{LEG_INIT}` (scoped, never "
                   f"--recursive), then `{VERIFY_PIN}`.")
CORE_REMEDIATION = (f"Remediation: run `{VERIFY_PIN}`, which names what is "
                    f"wrong with the pinned checkout; restore it with "
                    f"`{ROOT_INIT}`, then `{LEG_INIT}` (scoped, never "
                    f"--recursive).")

# Each level of the mount, its refusal code, and that level's remediation.
MOUNT_LEVELS = (
    ("openWallet", "pin-submodule-uninitialized", ROOT_REMEDIATION),
    ("openWallet/code", "pin-leg-uninitialized", LEG_REMEDIATION),
)


def refuse(code: str, detail: str, remediation: str) -> int:
    print(f"REFUSE {code}: {detail}\n{remediation}", file=sys.stderr)
    return 2


def main() -> int:
    for level, code, remediation in MOUNT_LEVELS:
        if not (ROOT / level / ".git").exists():
            return refuse(code, f"{level}/.git does not exist: {level} is not "
                                f"initialized, so the gate this entrypoint runs "
                                f"is not present", remediation)
    shown = CORE_GATE_PATH.relative_to(ROOT)
    spec = importlib.util.spec_from_file_location(
        "openwallet_wallet_yaml_syntax_gate", CORE_GATE_PATH)
    if spec is None or spec.loader is None:
        return refuse("core-unloadable", f"{shown}: no importable module spec",
                      CORE_REMEDIATION)
    gate = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(gate)
    except KeyboardInterrupt:
        raise
    except BaseException as exc:  # noqa: BLE001 - SystemExit too: an exiting gate refuses
        return refuse("core-unloadable",
                      f"{shown} does not load ({type(exc).__name__}: {exc})",
                      CORE_REMEDIATION)
    if not callable(getattr(gate, "main", None)):
        return refuse("core-unloadable", f"{shown} loads but defines no main()",
                      CORE_REMEDIATION)
    return gate.main()


if __name__ == "__main__":
    sys.exit(main())
