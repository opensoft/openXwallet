"""Fresh-clock, mutation and concurrent rotation cases for the issuer-only slice."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from workload_factory_binding import BindingError, WorkloadVerifier
from workload_factory_binding_runtime import DISCOVERY_URL, JWKS_URL, IssuerWorkloadVerifier
from .conftest import check, jwk, jwt


def test_token_expiry_during_crypto_is_not_returned(r, monkeypatch):
    original = WorkloadVerifier.verify
    def delayed(core, *args, **kwargs):
        result = original(core, *args, **kwargs)
        r.clock.advance(121)
        return result
    monkeypatch.setattr(WorkloadVerifier, "verify", delayed)
    with pytest.raises(BindingError):
        check(r)


def test_expected_claims_are_captured_before_transport(r):
    r.transport.hook = lambda _url: r.expected.update(environment="changed-during-io")
    assert check(r).claims["environment"] == "qa"


def test_unknown_key_has_only_one_refresh_and_no_retry_loop(r):
    check(r)
    r.clock.advance(30)
    token = jwt(r.h.issuer_key, r.h.claims, {"alg": "RS256", "typ": "JWT", "kid": "missing"})
    with pytest.raises(BindingError, match="^unknown-issuer-key$"):
        check(r, token)
    assert len(r.transport.calls) == 4
    with pytest.raises(BindingError, match="^issuer-refresh-throttled$"):
        check(r, token)
    assert len(r.transport.calls) == 4
    # A fresh valid response for an unknown token does not poison its known keys.
    assert check(r).claims == r.h.claims
    assert len(r.transport.calls) == 4


def test_cache_cannot_outlive_300_second_administrative_cap(r):
    r.h.claims["exp"] = r.h.now + 300
    r.h.reset_evidence()
    r.transport.headers[JWKS_URL] = (("Cache-Control", "max-age=86400"),)
    assert check(r).valid_until == r.h.now + 300
    r.clock.advance(299)
    check(r)
    assert len(r.transport.calls) == 2
    r.clock.advance(1)
    with pytest.raises(BindingError, match="^inactive-token$"):
        check(r)
    assert len(r.transport.calls) == 4


def test_refresh_budget_is_shared_by_both_fetches(r):
    r.transport.hook = lambda _url: r.clock.advance(6)
    with pytest.raises(BindingError, match="^issuer-fetch-unavailable$"):
        check(r)
    assert len(r.transport.calls) == 2


def test_discovery_freshness_can_expire_while_fetching_keys(r):
    r.transport.headers[DISCOVERY_URL] = (("Cache-Control", "max-age=1"),)
    r.transport.hook = lambda url: r.clock.advance(2) if url == JWKS_URL else None
    with pytest.raises(BindingError, match="^issuer-keys-expired$"):
        check(r)


def test_removed_snapshot_cannot_return_after_concurrent_rotation(r, monkeypatch):
    check(r)
    entered, release = Event(), Event()
    old_token = r.h.token
    original = WorkloadVerifier.verify
    def pause(core, token, *args, **kwargs):
        value = original(core, token, *args, **kwargs)
        if token == old_token:
            entered.set()
            assert release.wait(3)
        return value
    monkeypatch.setattr(WorkloadVerifier, "verify", pause)
    with ThreadPoolExecutor(max_workers=1) as pool:
        old = pool.submit(check, r)
        try:
            assert entered.wait(2)
            r.clock.advance(30)
            r.transport.documents[JWKS_URL] = {"keys": [jwk(r.h.issuer_key, "new")]}
            token = jwt(r.h.issuer_key, r.h.claims, {"alg": "RS256", "typ": "JWT", "kid": "new"})
            assert check(r, token).claims == r.h.claims
        finally:
            release.set()
        with pytest.raises(BindingError, match="^issuer-snapshot-changed$"):
            old.result(timeout=3)


def test_failure_precedes_signing_and_does_not_consume_the_challenge(r):
    r.transport.documents[DISCOVERY_URL] = {"issuer": "unapproved", "jwks_uri": JWKS_URL}
    r.h.gate = r.h.make_gate(workload_verifier=r.verifier)
    with pytest.raises(BindingError):
        r.h.run()
    assert r.h.calls == 0
    r.clock.advance(30)
    from workload_factory_binding_runtime import ISSUER
    r.transport.documents[DISCOVERY_URL] = {"issuer": ISSUER, "jwks_uri": JWKS_URL}
    assert r.h.run()["human_approval"] is False
    assert r.h.calls == 1


def test_default_offline_gate_does_not_use_runtime_transport(r, monkeypatch):
    from workload_factory_binding_runtime import HttpsTransport
    def forbidden(*_args, **_kwargs):
        raise AssertionError("default gate attempted networking")
    monkeypatch.setattr(HttpsTransport, "fetch", forbidden)
    assert r.h.run()["human_approval"] is False
    assert not r.transport.calls


def test_one_issuer_source_is_shared_across_audience_verifiers(r):
    check(r)
    other = IssuerWorkloadVerifier(audience="other:audience", source=r.source)
    claims = {**r.h.claims, "aud": "other:audience"}
    assert other.verify(jwt(r.h.issuer_key, claims), r.expected, now=r.h.now).claims == claims
    assert len(r.transport.calls) == 2


def test_opaque_url_shaped_kid_cannot_become_a_destination(r):
    token = jwt(r.h.issuer_key, r.h.claims, {
        "alg": "RS256", "typ": "JWT", "kid": "https://unapproved.invalid/keys"})
    with pytest.raises(BindingError, match="^unknown-issuer-key$"):
        check(r, token)
    assert [url for url, _ in r.transport.calls] == [DISCOVERY_URL, JWKS_URL]


def test_bad_signature_does_not_trigger_a_second_fetch(r):
    from cryptography.hazmat.primitives.asymmetric import rsa
    check(r)
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(BindingError, match="^workload-unverified$"):
        check(r, jwt(other, r.h.claims))
    assert len(r.transport.calls) == 2


@pytest.mark.parametrize("field", ["cache-control", "vary"])
def test_non_reuse_with_quoted_directives_or_vary_star(r, field):
    value = 'private="x, y", no-cache, max-age="100"' if field == "cache-control" else "Accept-Encoding, *"
    r.transport.headers[JWKS_URL] = ((field, value),)
    check(r)
    with pytest.raises(BindingError, match="^issuer-refresh-throttled$"):
        check(r)
    assert len(r.transport.calls) == 2


@pytest.mark.parametrize("bad", [None, True, -1, "time", float("nan"), float("inf")])
def test_invalid_monotonic_clock_refuses(r, bad):
    from workload_factory_binding_runtime import IssuerKeySource
    source = IssuerKeySource(transport=r.transport, clock=r.clock.wall, monotonic=lambda: bad)
    verifier = IssuerWorkloadVerifier(audience="factory:qa", source=source)
    with pytest.raises(BindingError, match="^clock-unavailable$"):
        verifier.verify(r.h.token, r.expected, now=r.h.now)
    assert not r.transport.calls


def test_transport_binding_error_payload_is_also_sanitized(r):
    r.transport.documents[JWKS_URL] = BindingError("CANARY provider error")
    with pytest.raises(BindingError, match="^issuer-unavailable$") as caught:
        check(r)
    assert "CANARY" not in str(caught.value)


def test_expected_policy_is_rejected_before_fetch(r):
    r.expected.pop("job_workflow_sha")
    with pytest.raises(BindingError, match="^invalid-workload-policy$"):
        check(r)
    assert not r.transport.calls
