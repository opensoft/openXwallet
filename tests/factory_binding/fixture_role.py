"""Test-only subprocess roles. All config paths are selected by the trusted test parent."""
import argparse
from copy import deepcopy
import os
import subprocess
from pathlib import Path
import sys
from types import SimpleNamespace

from cryptography.hazmat.primitives import serialization

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from workload_factory_binding.evidence import artifact_digest, canonical, decode_object, observe_artifacts


def worker_configuration(worker):
    """Measure actual source selection and public transport/binding configuration."""
    if set(worker) != {"owner_code", "endpoint", "ca_file", "certificate", "private_key",
                       "binding", "challenge_digest", "now"}:
        raise RuntimeError("unsupported worker configuration")
    source = Path(worker["owner_code"]).resolve(strict=True)
    revision = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True, timeout=5).stdout.strip()
    status = subprocess.run(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"],
                            check=True, capture_output=True, text=True, timeout=5).stdout
    if status:
        raise RuntimeError("worker source changed")
    return {
        "role": "worker", "owner_commit": revision, "tools": [],
        "transport": {
            "endpoint": worker["endpoint"],
            "credentials_digest": artifact_digest(
                {"ca": worker["ca_file"], "certificate": worker["certificate"]}, {}),
        },
        "binding": deepcopy(worker["binding"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("custody", "observe", "worker"))
    parser.add_argument("config")
    args = parser.parse_args()
    config = decode_object(Path(args.config).read_bytes())
    if args.role == "observe":
        key = serialization.load_pem_private_key(Path(config["private_key"]).read_bytes(), password=None)
        # The trusted supervisor selects and launches the exact measured worker,
        # rather than signing a measurement supplied by that worker.
        measured = artifact_digest(config["artifacts"], config["configuration"])
        supplied = decode_object(Path(config["worker_config"]).read_bytes())
        if (supplied["challenge_digest"] != config["challenge"]["digest"]
                or type(supplied["now"]) is not int or supplied["now"] != config["now"]
                or worker_configuration(supplied) != config["configuration"]):
            raise RuntimeError("worker context changed")
        if measured != config["policy"]["composition_digest"]:
            raise RuntimeError("approved composition changed")
        worker_file = Path(config["worker_config"]).with_name("verified-worker.json")
        frozen = canonical(supplied)
        fd = os.open(worker_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(frozen)
        worker = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "worker", str(worker_file)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={"PATH": os.defpath, "LANG": "C.UTF-8", "PYTHONNOUSERSITE": "1",
                 "PYTHONDONTWRITEBYTECODE": "1"}, umask=0o077)
        try:
            output, _errors = worker.communicate(timeout=10)
            if worker.returncode != 0:
                raise RuntimeError("reference worker failed")
            worker_result = decode_object(output)
            if worker_result != {"direct_sign_denied": True}:
                raise RuntimeError("reference worker authorization changed")
            if (worker_file.read_bytes() != frozen
                    or worker_configuration(supplied) != config["configuration"]
                    or artifact_digest(config["artifacts"], config["configuration"]) != measured):
                raise RuntimeError("worker artifact changed")
        finally:
            if worker.poll() is None:
                worker.kill()
                worker.wait(timeout=5)
            if worker.stdout:
                worker.stdout.close()
            if worker.stderr:
                worker.stderr.close()
        result = observe_artifacts(
            policy=config["policy"], request=config["request"], token=config["token"],
            challenge=SimpleNamespace(**config["challenge"]), artifacts=config["artifacts"],
            configuration=config["configuration"], private_key=key,
            now=config["now"], expires_at=config["now"] + 60)
        sys.stdout.buffer.write(canonical({"observation": result, "worker": worker_result,
                                          "worker_exited": worker.poll() is not None}))
        return
    sys.path.insert(0, config["owner_code"])
    from openwallet_runtime.custody import RemoteRegistry, RemoteSigner, TLSClient
    from openwallet_runtime.proof import ProofError, create_proof
    from openwallet_runtime.registry import BindingRegistry, binding_from_record
    from openwallet_runtime.reference_service import CustodyApplication, ReferenceServer, server_context
    if args.role == "custody":
        app = CustodyApplication(BindingRegistry(config["registry_directory"]),
                                 key_directory=config["key_directory"], policies=config["policies"],
                                 clock=lambda: config["now"])
        context = server_context(ca_file=config["ca_file"], certificate=config["certificate"],
                                 private_key=config["private_key"])
        with ReferenceServer(("127.0.0.1", 0), context=context, application=app) as server:
            Path(config["ready"]).write_text(str(server.server_port))
            server.serve_forever()
        return
    # The worker gets only its resolve-only transport credential and public binding.
    client = TLSClient(config["endpoint"], ca_file=config["ca_file"],
                       certificate=config["certificate"], private_key=config["private_key"])
    binding = binding_from_record(config["binding"])
    if RemoteRegistry(client).resolve(binding.subject_ref, now=config["now"]) != binding:
        raise RuntimeError("worker resolve preflight failed")
    try:
        create_proof(config["challenge_digest"], binding,
                     RemoteSigner(client, subject_ref=binding.subject_ref), now=config["now"])
    except ProofError:
        sys.stdout.write('{"direct_sign_denied":true}')
    else:
        raise RuntimeError("worker unexpectedly signed")


if __name__ == "__main__":
    main()
