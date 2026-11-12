"""Opt-in issuer acquisition only; no service, default activation or human assurance."""
from ._https_worker import DISCOVERY_URL, ISSUER, JWKS_URL
from .issuer import IssuerKeySource, IssuerWorkloadVerifier
from .transport import FetchResponse, HttpsTransport
