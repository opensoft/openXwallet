"""Current-record/challenge binding at the isolated trusted connector boundary."""
from dataclasses import replace

import pytest

from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.loaders import CurrentLoaders
from workload_factory_binding_runtime.runtime import _Use
from .composition_fixture import c, configuration


def test_current_records_and_challenge_feed_existing_gate(c):
    result = c.run()
    assert c.h.calls == 1
    assert result["human_approval"] is False
    assert result["assurance"] == "possession"
    assert len(c.records.calls) >= 2
    assert len(c.challenge.calls) >= 2
    assert all(x[:2] == ("policy", "policy:fixture") for x in c.records.calls)
    assert all(x[:2] == ("challenge", c.h.challenge.id) for x in c.challenge.calls)


@pytest.mark.parametrize("role", ["records", "challenge", "registry", "custody"])
@pytest.mark.parametrize("field", ["service_ref", "principal_ref", "credential_ref", "trust_digest"])
def test_each_selected_service_identity_field_refuses_before_sign(c, role, field):
    selected = c.services[role]
    changed = replace(selected.identity, **{field: "changed"})
    c.services[role] = replace(selected, identity=changed)
    c.bridge = c.make()
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 0
    assert c.records.calls == []


@pytest.mark.parametrize("field,value", [("policy_ref", "policy:other"), ("revision", 2),
    ("grant_ref", "grant:other"), ("composition_digest", "sha256:" + "f" * 64),
    ("not_before", 9999999999), ("expires_at", 0)])
def test_current_policy_cannot_be_replaced_or_revoked(c, field, value):
    c.records.value[field] = value
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 0


@pytest.mark.parametrize("field,value", [("id", "challenge:other"), ("issuer", "mfa:other"),
    ("subject_ref", "agent:other"), ("issued_at", 9999999999), ("expires_at", 0),
    ("request_digest", "sha256:" + "f" * 64)])
def test_current_challenge_is_bound_to_service_subject_request_and_time(c, field, value):
    c.challenge.value[field] = value
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 0


@pytest.mark.parametrize("role", ["records", "challenge"])
@pytest.mark.parametrize("raw", [b'{"id":1,"id":2}', b"[]", b"{\"x\":NaN}", b" " * 16385, b"{}"])
def test_malformed_current_service_data_refuses(c, role, raw):
    getattr(c, role).value = raw
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 0


def test_current_policy_rechecked_after_sign_and_changed_record_emits_no_result(c):
    c.h.on_sign = lambda: c.records.value.update(revision=2)
    with pytest.raises(BindingError):
        c.run()
    assert c.h.calls == 1


def test_service_outage_exposes_only_fixed_error(c):
    def fail():
        raise OSError("private-token-never-log")
    c.records.hook = fail
    with pytest.raises(BindingError, match="^runtime-service-unavailable$") as caught:
        c.run()
    assert "private-token" not in str(caught.value)
    assert c.h.calls == 0


def test_connector_receives_deadline_after_guarded_preflight_shortens_it(c):
    use = _Use(c.bridge)
    loaders = CurrentLoaders(use=use, records=c.services["records"], challenge=c.services["challenge"],
                             request=c.h.request)
    c.readback["expires_at"] = c.h.now + 10
    loaders.load_policy()
    assert use.valid_until == c.h.now + 10
    assert c.records.calls[0][2] == use.valid_until
