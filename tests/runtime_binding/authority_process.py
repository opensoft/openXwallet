"""Test-only independent fixture service process. No provider access."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
from factory_binding.fixture_role import publish_ready
from workload_factory_binding_runtime.reference_authority.store import AuthorityStore, StoreIdentity
from workload_factory_binding_runtime.reference_authority.transport import AuthorityServer


def main():
    selected = json.loads(Path(sys.argv[1]).read_text())
    store = AuthorityStore(selected["directory"], identity=StoreIdentity(**selected["identity"]),
                           controller_public_key=bytes.fromhex(selected["public_key"]), clock=lambda: selected["now"])
    with AuthorityServer(store=store, ca_file=selected["ca_file"], cert_file=selected["cert_file"],
                         key_file=selected["key_file"],
                         permissions={k: frozenset(v) for k, v in selected["permissions"].items()}) as server:
        publish_ready(Path(selected["ready"]), server.server_port)
        server.serve_forever(poll_interval=0.05)


if __name__ == "__main__":
    main()
