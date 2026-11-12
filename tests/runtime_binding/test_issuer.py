"""I01-I05: real RSA, injected transport/clocks, no public issuer or credentials."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import format_datetime
from threading import Event

import pytest

from workload_factory_binding import BindingError
from workload_factory_binding.evidence import WorkloadEvidence
from workload_factory_binding_runtime import (
    DISCOVERY_URL, ISSUER, JWKS_URL, FetchResponse, IssuerKeySource,
    IssuerWorkloadVerifier,
)
from .conftest import check, jwk, jwt


def test_real_signature_and_cache(r):
    result = check(r)
    assert isinstance(result, WorkloadEvidence)
    assert result.claims == r.h.claims
    assert result.valid_until == r.h.claims["exp"]
    assert [url for url, _ in r.transport.calls] == [DISCOVERY_URL, JWKS_URL]
    assert check(r) == result
    assert len(r.transport.calls) == 2


def test_x5t_is_metadata_and_backdated_nbf_is_allowed(r):
    claims = {**r.h.claims, "nbf": r.h.now - 600}
    token = jwt(r.h.issuer_key, claims, {
        "alg": "RS256", "typ": "JWT", "kid": "fixture-issuer", "x5t": "YWJj"})
    assert check(r, token).claims == claims


def test_64_external_keys_project_into_unchanged_core_limit(r):
    r.transport.documents[JWKS_URL] = {"keys": [
        jwk(r.h.issuer_key, f"other-{i}") for i in range(63)
    ] + [jwk(r.h.issuer_key)]}
    assert check(r).claims == r.h.claims


@pytest.mark.parametrize("field", [
    "repository", "repository_id", "repository_owner", "repository_owner_id",
    "environment", "sub", "ref", "sha", "workflow_ref", "workflow_sha",
    "job_workflow_ref", "job_workflow_sha", "run_id", "run_attempt", "iss", "aud",
])
def test_each_signed_context_mismatch_refuses(r, field):
    claims = {**r.h.claims, field: "different"}
    with pytest.raises(BindingError, match="^workload-mismatch$"):
        check(r, jwt(r.h.issuer_key, claims))
    assert r.h.calls == 0


@pytest.mark.parametrize("field,offset", [("iat", 1), ("nbf", 1), ("exp", 0), ("exp", 301)])
def test_token_time_rules_survive_adapter(r, field, offset):
    claims = {**r.h.claims, "nbf": r.h.now - 600, field: r.h.now + offset}
    with pytest.raises(BindingError, match="^inactive-token$"):
        check(r, jwt(r.h.issuer_key, claims))


@pytest.mark.parametrize("change", [
    {"jku": "https://unapproved.invalid/keys"}, {"x5u": "file:///not-used"},
    {"alg": "HS256"}, {"kid": "*"}, {"crit": ["unknown"]},
])
def test_token_cannot_select_transport_or_algorithm(r, change):
    header = {"alg": "RS256", "typ": "JWT", "kid": "fixture-issuer", **change}
    with pytest.raises(BindingError):
        check(r, jwt(r.h.issuer_key, r.h.claims, header))
    assert not r.transport.calls


@pytest.mark.parametrize("url,value", [
    (DISCOVERY_URL, {"issuer": ISSUER + "/", "jwks_uri": JWKS_URL}),
    (DISCOVERY_URL, {"issuer": ISSUER, "jwks_uri": "https://other.invalid/keys"}),
    (DISCOVERY_URL, b'{"issuer":"a","issuer":"b"}'),
    (DISCOVERY_URL, b"[1,2]"), (JWKS_URL, b'{"keys":[],"keys":[]}'),
    (JWKS_URL, b'{"keys":NaN}'), (JWKS_URL, b"x" * 262145),
    (JWKS_URL, {"keys": []}), (JWKS_URL, {"keys": [None]}),
])
def test_bad_documents_refuse(r, url, value):
    r.transport.documents[url] = value
    with pytest.raises(BindingError):
        check(r)
    assert r.h.calls == 0


@pytest.mark.parametrize("kind", ["duplicate", "private", "exponent", "oversized", "bad-ops"])
def test_key_set_ambiguity_or_incompatible_rsa_refuses(r, kind):
    key = jwk(r.h.issuer_key)
    keys = [key]
    if kind == "duplicate":
        keys *= 2
    elif kind == "private":
        key["d"] = "CANARY"
    elif kind == "exponent":
        key["e"] = "Aw"
    elif kind == "bad-ops":
        key["key_ops"] = ["sign", "verify"]
    else:
        keys = [jwk(r.h.issuer_key, f"key-{i}") for i in range(65)]
    r.transport.documents[JWKS_URL] = {"keys": keys}
    with pytest.raises(BindingError):
        check(r)


@pytest.mark.parametrize("status", [201, 301, 302, 304, 401, 500])
def test_only_fresh_200_is_accepted(r, status):
    r.transport.documents[JWKS_URL] = FetchResponse(status, (), b"CANARY")
    with pytest.raises(BindingError) as caught:
        check(r)
    assert "CANARY" not in str(caught.value)


def test_http_age_shortens_administrative_deadline(r):
    r.transport.headers[JWKS_URL] = (("Cache-Control", "max-age=100"), ("Age", "95"))
    assert check(r).valid_until == r.h.now + 5
    r.clock.advance(5)
    with pytest.raises(BindingError, match="^issuer-refresh-throttled$"):
        check(r)


def test_http_date_expires_shortens_deadline(r):
    date = lambda stamp: format_datetime(datetime.fromtimestamp(stamp, timezone.utc), usegmt=True)
    r.transport.headers[JWKS_URL] = (("Date", date(r.h.now)), ("Expires", date(r.h.now + 7)))
    assert check(r).valid_until == r.h.now + 7


@pytest.mark.parametrize("control", ["no-store, max-age=100", "no-cache, max-age=100"])
def test_non_reusable_response_is_not_cached(r, control):
    r.transport.headers[JWKS_URL] = (("Cache-Control", control),)
    check(r)
    with pytest.raises(BindingError, match="^issuer-refresh-throttled$"):
        check(r)
    assert len(r.transport.calls) == 2
    r.clock.advance(30)
    check(r)
    assert len(r.transport.calls) == 4


@pytest.mark.parametrize("headers", [
    (("Cache-Control", "max-age=0"),),
    (("Cache-Control", "max-age=5"), ("Age", "5")),
    (("Cache-Control", "max-age=100, max-age=200"),),
    (("Cache-Control", "max-age=-1"),), (("Age", "-1"),),
    (("Date", "not-a-date"),), (("Age", "1"), ("Age", "2")),
])
def test_expired_or_ambiguous_http_freshness_refuses(r, headers):
    r.transport.headers[JWKS_URL] = headers
    with pytest.raises(BindingError):
        check(r)


def test_unknown_key_rotates_once_and_removed_key_never_returns(r):
    old = r.h.token
    check(r)
    r.clock.advance(30)
    r.transport.documents[JWKS_URL] = {"keys": [jwk(r.h.issuer_key, "rotated")]}
    token = jwt(r.h.issuer_key, r.h.claims, {"alg": "RS256", "typ": "JWT", "kid": "rotated"})
    assert check(r, token).claims == r.h.claims
    assert len(r.transport.calls) == 4
    with pytest.raises(BindingError, match="^issuer-refresh-throttled$"):
        check(r, old)
    r.clock.advance(30)
    with pytest.raises(BindingError, match="^unknown-issuer-key$"):
        check(r, old)
    assert len(r.transport.calls) == 6


def test_failed_refresh_has_no_stale_fallback_or_error_payload(r):
    r.transport.headers[JWKS_URL] = (("Cache-Control", "max-age=30"),)
    check(r)
    r.clock.advance(30)
    r.transport.documents[JWKS_URL] = OSError("CANARY provider payload")
    with pytest.raises(BindingError, match="^issuer-unavailable$") as caught:
        check(r)
    assert "CANARY" not in str(caught.value)
    with pytest.raises(BindingError, match="^issuer-refresh-throttled$"):
        check(r)


def test_concurrent_initial_verification_coalesces_one_refresh(r):
    entered, release = Event(), Event()
    def block(url):
        if url == DISCOVERY_URL:
            entered.set()
            assert release.wait(3)
    r.transport.hook = block
    with ThreadPoolExecutor(max_workers=8) as pool:
        first = pool.submit(check, r)
        assert entered.wait(2)
        followers = [pool.submit(check, r) for _ in range(7)]
        release.set()
        results = [f.result(timeout=4) for f in [first, *followers]]
    assert all(x.claims == r.h.claims for x in results)
    assert len(r.transport.calls) == 2


def test_expiry_during_fetch_is_checked_before_signer(r):
    r.h.claims["exp"] = r.h.now + 1
    r.h.reset_evidence()
    r.transport.hook = lambda _url: r.clock.advance(1)
    r.h.gate = r.h.make_gate(workload_verifier=r.verifier)
    with pytest.raises(BindingError, match="^inactive-token$"):
        r.h.run()
    assert r.h.calls == 0


def test_existing_proof_gate_accepts_adapter_without_core_changes(r):
    r.h.gate = r.h.make_gate(workload_verifier=r.verifier)
    result = r.h.run()
    assert result["assurance"] == "possession"
    assert result["human_approval"] is False
    assert r.h.calls == 1
    assert len(r.transport.calls) == 2


@pytest.mark.parametrize("bad", [None, True, -1, "1794400000", float("nan"), float("inf")])
def test_bad_clock_is_safe_refusal(r, bad):
    source = IssuerKeySource(transport=r.transport, clock=lambda: bad,
                            monotonic=lambda: r.clock.mono)
    verifier = IssuerWorkloadVerifier(audience="factory:qa", source=source)
    with pytest.raises(BindingError, match="^clock-unavailable$"):
        verifier.verify(r.h.token, r.expected, now=r.h.now)
    assert not r.transport.calls


def test_clock_regression_refuses_without_using_cached_keys(r):
    check(r)
    r.clock.advance(-1)
    with pytest.raises(BindingError, match="^clock-unavailable$"):
        check(r)
