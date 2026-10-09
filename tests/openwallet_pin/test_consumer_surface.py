"""The entrypoint's module surface: the names its consumers import from it.

`split-openwallet-neutral-core` task 5.2 (design.md D5), a review fix.
openxFactory does not only RUN `scripts/validate-openxwallet.py`: it IMPORTS
it by path and reads the key decoders off the module. Two loaders do, and each
exits, rather than derive a key with arithmetic of its own, when a name is
absent:

  scripts/validate-factory-identity.py   `load_pinned_reader` requires the
      five CONSUMER_NAMES below, and its `derive` mint helper calls all four
      functions and reads PUBLIC_KEY_B64U_LEN
      (scripts/mint-factory-origin-key.py goes through this loader);
  scripts/validate-clearing-dispatch.py  `load_pinned_reader` requires the
      two decoders, and calls both.

The pre-split validator was one file and carried all five. The adapter keeps
that surface: `_decode_public_key` and PUBLIC_KEY_B64U_LEN are its own,
`_fingerprint_of` is its alias of the core's `fingerprint_of_public_key`, and
the two decoders are RE-EXPORTED from the pinned core, whose CORE_CONTRACT
names both, so a core without one refuses at load instead of failing the
entrypoint's import.

LOADED THE WAY THE CONSUMERS LOAD IT: in process, by path, under each loader's
module name, through `spec_from_file_location`, `module_from_spec` and
`exec_module`, with no `sys.modules` registration, and twice in one process,
as one session of openxFactory's tests loads it.

READ BEFORE IT IS RUN. Inside scripts/neutrality-gate.py's mirror the
entrypoint is the gate's generated shim, which runs both validators when it is
executed, so loading it there would record an invocation this suite never
made. The source is read first, and over the shim the test fails at that read
having executed nothing, as this suite's other tests that read the
entrypoint's source do.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate-openxwallet.py"
MOUNTED_LEG = REPO_ROOT / "openWallet" / "code"

ROOT_INIT = "git submodule update --init openWallet"
LEG_INIT = "git -C openWallet submodule update --init code"

# openxFactory's two loaders, by the module name each loads under, and the
# names factory-identity's requires, in its order; clearing-dispatch's two are
# the first two.
FACTORY_IDENTITY_LOADER = "_pinned_openxwallet_reader"
CLEARING_DISPATCH_LOADER = "_pinned_openxwallet_reader_clearing"
CONSUMER_NAMES = ("decode_public_key_multibase", "fingerprint_of_public_key",
                  "_decode_public_key", "_fingerprint_of",
                  "PUBLIC_KEY_B64U_LEN")
RE_EXPORTED = CONSUMER_NAMES[:2]

# ONE KEY IN BOTH SPELLINGS. Seat A of the pinned core's packaged
# `wallet-agent-council-multi-key.example.yaml`, a fixture value nobody holds a
# private half for: its multibase and its fingerprint as recorded there, and
# the same 32 bytes as unpadded base64url, the register reader's spelling.
SEAT_A_MULTIBASE = "z6MkesFwon9Uucr7UuwNmnHg2ci5tXfk5yaJ1jVV33jBaXrd"
SEAT_A_BASE64URL = "BiXToA0xkRiWqxsu_jwuVh3eFJEVezKB3Kc2NAjDkP4"
SEAT_A_FINGERPRINT = ("sha256:6ada99966134615c07adb84cb71a87876c087795552f5e"
                      "b01436a86fb2464c11")


def _core_contract() -> tuple[str, ...]:
    """CORE_CONTRACT, read from the entrypoint's SOURCE, which is not run."""
    tree = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "CORE_CONTRACT"):
            return ast.literal_eval(node.value)
    pytest.fail(f"{VALIDATOR.name} assigns no CORE_CONTRACT, so it is not the "
                f"adapter, and it is not executed here")


def _load_as_consumers_do(name: str) -> ModuleType:
    """openxFactory's `load_pinned_reader`, less its refusals."""
    spec = importlib.util.spec_from_file_location(name, VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_entrypoint_keeps_the_names_consumers_import():
    """openxFactory's factory-identity and clearing-dispatch loaders
    (`load_pinned_reader` in scripts/validate-factory-identity.py and
    scripts/validate-clearing-dispatch.py) both load this entrypoint, and each
    load exposes all five names: the two decoders as the pinned core's own
    objects, `_fingerprint_of` as the same function, and one key, in both its
    spellings, fingerprinting to its recorded value through either pair."""
    contract = _core_contract()
    assert set(RE_EXPORTED) <= set(contract), contract
    if not (MOUNTED_LEG / ".git").exists():
        pytest.skip(f"openWallet/code is not initialized in this checkout, so "
                    f"the entrypoint cannot load its core; run `{ROOT_INIT}`, "
                    f"then `{LEG_INIT}` (never --recursive)")
    for loader in (FACTORY_IDENTITY_LOADER, CLEARING_DISPATCH_LOADER):
        reader = _load_as_consumers_do(loader)
        missing = [name for name in CONSUMER_NAMES
                   if not hasattr(reader, name)]
        assert not missing, f"{loader}: the entrypoint has no {missing}"
        for name in RE_EXPORTED:
            assert getattr(reader, name) is getattr(reader.core, name), \
                f"{loader}: {name} is not the core's own"
        assert reader._fingerprint_of is reader.fingerprint_of_public_key, \
            loader
        assert reader.PUBLIC_KEY_B64U_LEN == len(SEAT_A_BASE64URL), loader

        from_multibase = reader.decode_public_key_multibase(SEAT_A_MULTIBASE)
        from_base64url = reader._decode_public_key(SEAT_A_BASE64URL)
        assert from_multibase is not None, loader
        assert from_multibase == from_base64url, loader
        assert (reader.fingerprint_of_public_key(from_multibase)
                == reader._fingerprint_of(from_base64url)
                == SEAT_A_FINGERPRINT), loader
