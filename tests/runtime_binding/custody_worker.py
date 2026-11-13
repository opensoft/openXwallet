"""Test-only direct-sign probe process; no gate credential/config paths supplied."""
import base64
from pathlib import Path
import sys


def main():
    # Source is selected by the trusted isolated test parent, not a public API.
    import json
    config = json.loads(Path(sys.argv[1]).read_bytes())
    sys.path.insert(0, config["owner_code"])
    from openwallet_runtime.custody import RemoteRegistry, RemoteSigner, TLSClient
    from openwallet_runtime.proof import ProofError
    client = TLSClient(config["endpoint"], ca_file=config["ca_file"],
                       certificate=config["certificate"], private_key=config["private_key"])
    binding = RemoteRegistry(client).resolve(config["subject_ref"], now=config["now"])
    if binding.key_ref != config["key_ref"]:
        raise RuntimeError("probe binding mismatch")
    try:
        RemoteSigner(client, subject_ref=binding.subject_ref).sign(base64.b64decode(config["message"], validate=True))
    except ProofError as error:
        if str(error) != "service-refused":
            raise RuntimeError("probe failed without authorization denial") from None
    else:
        raise RuntimeError("worker unexpectedly signed valid preimage")
    sys.stdout.write('{"direct_sign_denied":true}')


if __name__ == "__main__":
    main()
