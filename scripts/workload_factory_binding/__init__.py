"""Opt-in candidate factory adapter. No network, default trust or activation."""
from .evidence import BindingError, WorkloadVerifier, digest, observe_artifacts
from .gate import ProofGate, request_digest
from .ledger import ReplayLedger
