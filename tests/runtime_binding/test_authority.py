"""Retained fixture authority bindings and independently signed observations."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict, replace
import os
import sqlite3

from cryptography.hazmat.primitives.asymmetric import ed25519
import pytest

from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.reference_authority.model import signed_observation
from workload_factory_binding_runtime.reference_authority.store import DATABASE, AuthorityStore, initialize_store
from .authority_fixture import a, approve, assigned, authorization, b, w, c, configuration, l


def test_durable_binding_same_run_refresh_restart_and_revocation(a):
    approve(a)
    value = a.store.read(**assigned(a), bind=True)
    assert value["scope"] == "isolated-fixture"
    assert a.open().read(**assigned(a), bind=False) == value
    a.store.revoke(ref=a.b.context.preauthorization_ref)
    with pytest.raises(BindingError):
        a.open().read(**assigned(a), bind=True)
    with pytest.raises(BindingError):
        a.open().authorize(**authorization(a))
    with sqlite3.connect(a.root / "state" / DATABASE) as db:
        assert db.execute("SELECT revoked, context IS NOT NULL FROM preauthorizations").fetchone() == (1, 1)
        assert db.execute("SELECT count(*) FROM observations").fetchone() == (1,)


def test_concurrent_independent_runs_have_one_persistent_winner(a):
    a.store.authorize(**authorization(a))
    contexts = [replace(a.b.context, run_id=str(800 + i)) for i in range(8)]
    for i, context in enumerate(contexts):
        a.store.observe(envelope=a.envelope(context, "event:" + str(i)))
    def claim(pair):
        i, context = pair
        try:
            a.open().read(context=asdict(context), event_ref="event:" + str(i), bind=True)
            return i
        except BindingError:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        winners = [i for i in pool.map(claim, enumerate(contexts)) if i is not None]
    assert len(winners) == 1
    assert claim((winners[0], contexts[winners[0]])) == winners[0]
    assert all(claim((i, context)) is None for i, context in enumerate(contexts) if i != winners[0])


@pytest.mark.parametrize("field,value", [("run_id", "790"), ("run_attempt", "2"),
    ("repository_id", "999"), ("source_commit", "c" * 40), ("selection_digest", "sha256:" + "f" * 64),
    ("accepted_commit", "c" * 40), ("preauthorization_ref", "preauthorization:other")])
def test_signed_context_cannot_rebind_or_change_selected_source(a, field, value):
    approve(a)
    a.store.read(**assigned(a), bind=True)
    context = replace(a.b.context, **{field: value})
    # Invalid source contexts may fail during signing validation itself.
    with pytest.raises(BindingError):
        a.store.observe(envelope=a.envelope(context, "event:other"))
        a.open().read(context=asdict(context), event_ref="event:other", bind=True)


@pytest.mark.parametrize("change", ["signature", "root", "context", "scope", "profile", "extra", "future", "expired", "long", "event"])
def test_signed_observation_is_closed_current_and_independently_authenticated(a, change):
    a.store.authorize(**authorization(a))
    envelope = deepcopy(a.envelope())
    if change == "signature":envelope["signature"] = "A" * 86
    elif change == "root":envelope = signed_observation(ed25519.Ed25519PrivateKey.generate(), a.b.context,
        event_ref="event:forged", now=a.now, expires_at=a.now + 10)
    elif change == "context":envelope["observation"]["context"]["run_id"] = "999"
    elif change == "scope":envelope["observation"]["scope"] = "production"
    elif change == "profile":envelope["profile"] = "other"
    elif change == "extra":envelope["key"] = "worker-selected"
    elif change == "future":envelope["observation"]["observed_at"] += 1
    elif change == "expired":envelope["observation"]["expires_at"] = a.now
    elif change == "long":envelope["observation"]["expires_at"] = a.now + 61
    elif change == "event":envelope["observation"]["event_ref"] = "event:bad\nvalue"
    with pytest.raises(BindingError):
        a.store.observe(envelope=envelope)
    with pytest.raises(BindingError):
        a.store.read(**assigned(a), bind=True)


def test_operation_read_cannot_create_binding_and_event_cannot_be_replaced(a):
    approve(a)
    with pytest.raises(BindingError):a.store.read(**assigned(a), bind=False)
    a.store.observe(envelope=a.envelope())  # exact retry only
    with pytest.raises(BindingError):
        a.store.observe(envelope=a.envelope(replace(a.b.context, run_id="999")))
    a.store.read(**assigned(a), bind=True)


@pytest.mark.parametrize("change", ["missing", "replacement", "corrupt", "mode", "link", "directory", "root", "schema", "clock"])
def test_lost_replaced_unsafe_or_regressed_state_refuses_without_reset(a, change):
    approve(a)
    a.store.read(**assigned(a), bind=True)
    path = a.root / "state" / DATABASE
    if change == "missing":path.unlink()
    elif change == "replacement":
        raw = path.read_bytes();path.unlink();path.write_bytes(raw);path.chmod(0o600)
        # Avoid inode reuse making this test nondeterministic.
        other = path.with_name("replacement");other.write_bytes(raw);other.chmod(0o600);other.replace(path)
    elif change == "corrupt":path.write_bytes(b"corrupt")
    elif change == "mode":path.chmod(0o644)
    elif change == "link":os.link(path, path.with_name("alias"))
    elif change == "directory":(a.root / "state").chmod(0o755)
    elif change == "root":a.public_key = ed25519.Ed25519PrivateKey.generate().public_key().public_bytes_raw()
    elif change == "schema":
        with sqlite3.connect(path) as db:db.execute("CREATE TABLE extra (x TEXT)")
    elif change == "clock":a.now -= 1
    with pytest.raises(BindingError):
        AuthorityStore(a.root / "state", identity=a.identity, controller_public_key=a.public_key, clock=lambda: a.now)
    with pytest.raises(BindingError):initialize_store(a.root / "state", a.public_key)
    if change == "missing":assert not path.exists()


def test_expired_authorization_and_observation_cannot_refresh_binding(a):
    approve(a)
    a.store.read(**assigned(a), bind=True)
    a.now += 51
    with pytest.raises(BindingError):a.open().read(**assigned(a), bind=True)
    a.store.observe(envelope=a.envelope(event="event:refresh"))
    assert a.store.read(context=asdict(a.b.context), event_ref="event:refresh", bind=True)["bootstrap"]["expires_at"] == a.b.w.c.h.now + 60
    a.now += 10
    with pytest.raises(BindingError):a.open().read(**assigned(a), bind=True)
