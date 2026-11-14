"""Closed fixture control-plane observations, signed by an independently selected key."""
from dataclasses import asdict

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from workload_factory_binding.evidence import (
    BindingError, canonical, decode64, decode_object, encode64, integer, require,
)
from ..bootstrap import DispatchContext, validate_dispatch_context

PROFILE = "openxfactory-portable-bootstrap-reference-v1"
SCOPE = "isolated-fixture"
DOMAIN = b"openxfactory-portable-bootstrap-fixture-observation-v1\n"
ERROR = "bootstrap-authority-refused"


def closed(value, fields):
    require(type(value) is dict and set(value) == set(fields.split()), ERROR)


def window(start, end, now):
    require(all(integer(v) for v in (start, end, now)) and start <= now < end <= start + 60, ERROR)


def signed_observation(key, context, *, event_ref, now, expires_at):
    """Fixture controller helper, not a GitHub observation or provider verifier."""
    validate_dispatch_context(context)
    observation = {"scope": SCOPE, "event_ref": event_ref, "context": asdict(context),
                   "observed_at": now, "expires_at": expires_at}
    return {"profile": PROFILE, "observation": observation,
            "signature": encode64(key.sign(DOMAIN + canonical(observation)))}


def verify_observation(envelope, public_key, now):
    try:
        closed(envelope, "profile observation signature")
        require(envelope["profile"] == PROFILE and type(public_key) is bytes and len(public_key) == 32, ERROR)
        observation = envelope["observation"]
        closed(observation, "scope event_ref context observed_at expires_at")
        require(observation["scope"] == SCOPE, ERROR)
        event = observation["event_ref"]
        require(type(event) is str and event.startswith("event:") and 6 < len(event) <= 128
                and all(c.isascii() and (c.isalnum() or c in ":-_") for c in event), ERROR)
        window(observation["observed_at"], observation["expires_at"], now)
        closed(observation["context"], " ".join(DispatchContext.__dataclass_fields__))
        context = DispatchContext(**observation["context"])
        validate_dispatch_context(context)
        signature = decode64(envelope["signature"])
        require(len(signature) == 64, ERROR)
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, DOMAIN + canonical(observation))
        # Bound storage and canonical scalar grammar, including nested context.
        decode_object(canonical(envelope))
        return context, observation
    except Exception:
        raise BindingError(ERROR) from None
