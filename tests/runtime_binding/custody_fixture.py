"""Private isolated custody selection. Metadata is synthetic, not live evidence."""
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import byte_digest, digest
from workload_factory_binding_runtime.custody import (
    ConfinedCustody, CustodyAccess, CustodyMaterial, CustodyTrust,
)
from workload_factory_binding_runtime.loaders import ServiceIdentity
from factory_binding.test_owner_integration import make_pki
from .test_config import encoded


@pytest.fixture
def k(c, tmp_path):
    ca, server, gate, worker = make_pki(tmp_path / "tls")
    c.config["services"]["custody"]["trust_digest"] = byte_digest(ca.read_bytes())
    c.reselect_policy()
    identity = ServiceIdentity(**c.config["services"]["custody"])
    material = CustodyMaterial("https://127.0.0.1:8443", ca, gate[0], gate[1])
    access = CustodyAccess(
        "deployment:gate", "boundary:isolated-fixture", "issuance:gate", "principal:gate",
        digest(c.config), digest(c.config["sources"]), c.config["case_ref"],
        c.config["launch"]["run_id"], c.config["launch"]["run_attempt"], identity,
        "sha256:" + gate[2], byte_digest(material.endpoint.encode()),
        c.h.binding.subject_ref, c.h.binding.key_ref, c.h.binding.custody_ref,
        ("sign",), c.h.now - 1, c.h.now + 25)
    result = SimpleNamespace(c=c, ca=ca, server=server, gate=gate, worker=worker,
                             identity=identity, material=material, access=access,
                             deadlines=[], calls=[], hook=None)

    def read(*, deadline):
        result.deadlines.append(deadline)
        if result.hook:
            result.hook()
        return result.access
    result.trust = CustodyTrust("deployment:gate", "boundary:isolated-fixture", "issuance:gate",
                               "principal:gate", read)

    class Remote:
        def __init__(self, client, *, subject_ref):
            result.calls.append(("construct", subject_ref))

        def sign(self, message):
            result.calls.append(("sign", message))
            return b"s" * 64

    def make(**overrides):
        args = dict(load_config=lambda: encoded(c.config), runtime_trust=c.trust,
                    custody_trust=result.trust, identity=result.identity, material=result.material,
                    tls_client=lambda *args, **kwargs: object(), remote_signer=Remote,
                    subject_ref=c.h.binding.subject_ref)
        args.update(overrides)
        return ConfinedCustody(**args)
    result.make = make
    result.signer = make()
    result.calls.clear()
    result.deadlines.clear()
    return result
