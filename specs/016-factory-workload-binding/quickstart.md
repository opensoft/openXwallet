# Isolated qualification

Run in the owning bench from a fresh feature checkout. No provider credentials
are needed. Initialize only the declared neutral root/code mounts before testing;
the canonical-record compatibility case needs both. Use a fresh virtual environment
and the complete pinned dependency file.

```bash
git submodule update --init openWallet
git -C openWallet submodule update --init code
python3 -m pip install --only-binary :all: -r requirements-workload-binding.txt
python3 -m pytest tests/factory_binding -q
```

The self-contained matrix exercises real RSA/Ed25519 signatures and a private
SQLite ledger. Optional owning-source integration requires explicit accepted
wallet code selection; it must fail, not skip, when requested incorrectly:

```bash
WALLET_BINDING_OWNER_CODE=<accepted-wallet-code-checkout> \
  python3 -m pytest tests/factory_binding/test_owner_integration.py -q
```

The checkout identity must be `bb0e9dae89a771b05f6c235d0a77237288b95c85`
from accepted openWallet assembly `32aa09af5e4c28e1b3772b74fb8ddc08321db366`.
No installed package or arbitrary PYTHONPATH substitutes for that checked source.
The integration launches only loopback mutual-TLS reference custody and a separate
observer with disposable keys. Worker credentials permit resolve but not sign.
It checks the resulting proof with the owning verifier and checks cleanup after
success/failure. This is same-user reference process separation, not hostile OS
isolation or actual GitHub issuer qualification.

Run the existing adapter gates in AGENTS.md's order before publication. Current
neutral submodules are initialized only through the two declared scoped lines.
Do not alter those pins to make this candidate pass. Evidence records source,
tests and cleanup separately; no live deployment or approval is performed.
