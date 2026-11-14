"""One isolated portable-authority → admission → owning-wallet → cleanup flow.

Real local cryptography, mTLS and separate janitor/readback processes; issuer and
GitHub/control-plane observations remain simulated. No live qualification claim.
"""
from dataclasses import asdict, replace
import multiprocessing
import sqlite3
import time
from types import SimpleNamespace

import pytest

from workload_factory_binding.evidence import BindingError, digest
from workload_factory_binding_runtime.bootstrap import DispatchContext, bootstrap, selection_document, selection_digest
from workload_factory_binding_runtime.reference_authority.client import AuthoritySession, probe_worker_denied
from workload_factory_binding_runtime.reference_authority.store import DATABASE
from workload_factory_binding_runtime.workflow import SchedulerReadback
from .authority_fixture import a, authorization
from .composition_fixture import c
from .custody_fixture import k
from .lifecycle_process_fixture import p
from .test_config import configuration
from .test_lifecycle import l
from .test_workflow import w
from .test_custody import _owning_run
from .test_lifecycle_process import assert_removed


@pytest.mark.parametrize("outcome", ["success", "failure", "cancel", "hard-exit"])
def test_portable_authority_owning_wallet_and_independent_cleanup(k, w, request, tmp_path, outcome):
    retained = {}
    def before_proof(c, create_proof):
        # Owning registry/key/custody preparation has finished. Only now freeze
        # static approval; no late reapproval or config mutation manufactures a pass.
        document = selection_document(c.config)
        context = DispatchContext(**{name: getattr(w.context, name) for name in (
            "repository", "repository_id", "event_name", "ref", "sha", "workflow_ref", "workflow_sha",
            "run_id", "run_attempt", "accepted_commit", "source_commit")},
            selection_digest=selection_digest(document), preauthorization_ref="preauthorization:integrated")
        fixture = a.__wrapped__(SimpleNamespace(w=w, document=document, context=context), tmp_path)
        authority = next(fixture)
        retained.update(fixture=fixture, authority=authority, context=context)
        service = authority.launch()
        service.clients["operator"].request("authorize", deadline=c.h.now + 10, **authorization(authority))
        service.clients["controller"].request("observe", deadline=c.h.now + 10, envelope=authority.envelope())
        session = AuthoritySession(service.clients["reader"], context=context, event_ref="event:assigned", deadline=c.h.now + 10)
        assert session.value["configuration"] == c.config
        janitor = request.getfixturevalue("p")
        retained["janitor"] = janitor
        scheduler = SchedulerReadback(w.scheduler.principal_ref, c.config["lifecycle"]["cleanup_ref"],
            janitor.plan.digest, janitor.life.readback.identity.principal_ref, c.h.now, c.h.now + 20)
        bindings = session.bindings(replace(w.bindings, runtime_trust=c.trust, lifecycle=janitor.life,
                                           read_scheduler=lambda ref, deadline: scheduler))
        admitted = bootstrap(context, bindings=bindings)
        assert admitted.config_digest == digest(c.config)
        assert c.h.calls == 0
        probe_worker_denied(service.clients["worker"], context=context, event_ref="event:assigned", deadline=c.h.now + 10)
        c.bridge = c.make(load_config=lambda: session.raw, trust=bindings.workflow.runtime_trust,
                          create_proof=create_proof, lifecycle=janitor.life)
        retained["shared"] = (janitor.root / "shared").read_bytes()
        retained["replay_refusals"] = []
        reserve = c.h.ledger.reserve
        def observe_reservation(**arguments):
            try:
                return reserve(**arguments)
            except BindingError as exc:
                retained["replay_refusals"].append(str(exc))
                raise
        c.h.ledger.reserve = observe_reservation

    def one_use(run):
        result = run()
        # Prove replay refusal while the lease/credential are still active,
        # before cleanup could mask it with an unrelated lease failure.
        with pytest.raises(BindingError, match="^runtime-service-unavailable$"):
            run()
        assert retained["replay_refusals"] == ["replay-refused"]
        return result

    def perform(run):
        janitor = retained["janitor"]
        if outcome == "hard-exit":
            context = multiprocessing.get_context("fork")
            parent, child = context.Pipe(duplex=False)
            def runner():
                one_use(run)
                child.send_bytes(b"proof-complete")
                time.sleep(300)
            process = context.Process(target=runner)
            process.start()
            try:
                assert parent.poll(8)
                assert parent.recv_bytes() == b"proof-complete"
                process.kill();process.join(timeout=4)
                assert not process.is_alive()
                k.c.h.now = janitor.plan.expires_at
                janitor.clock.value = janitor.plan.expires_at
                deadline = time.monotonic() + 5
                while True:
                    readback = janitor.audit.read_cleanup(janitor.plan.ref, deadline=janitor.clock.value + 10)
                    if readback.lease_status == "closed" and all(not r.present for r in readback.resources[:3]):
                        break
                    assert time.monotonic() < deadline
                    time.sleep(0.03)
                janitor.life.finalize("cancel")
            finally:
                if process.is_alive():process.kill();process.join(timeout=3)
                process.close();parent.close();child.close()
            raise RuntimeError("runner-hard-exit-observed")
        def operation():
            result = one_use(run)
            from openwallet_runtime.proof import verify_proof
            verified = verify_proof(result["proof"], expected_digest=k.c.h.challenge.digest,
                                    binding=k.c.h.binding, now=k.c.h.now)
            assert verified.subject_ref == k.c.h.binding.subject_ref
            assert result["human_approval"] is False
            if outcome == "failure":raise RuntimeError("after-proof")
            if outcome == "cancel":raise KeyboardInterrupt()
            return result
        return janitor.life.run(operation)

    # The fixture issuer independently signs the selected workflow launch claims.
    k.c.h.claims.update(k.c.config["launch"])
    k.c.h.policy["claims"].update({name: k.c.config["launch"][name] for name in k.c.h.policy["claims"]})
    k.access = replace(k.access, sources_digest=digest(k.c.config["sources"]))
    directory = tmp_path / "owning-custody"
    directory.mkdir(mode=0o700)
    try:
        if outcome == "success":
            _owning_run(k, directory, before_proof=before_proof, perform=perform)
        else:
            expected = {"failure": BindingError, "cancel": KeyboardInterrupt, "hard-exit": RuntimeError}[outcome]
            with pytest.raises(expected):
                _owning_run(k, directory, before_proof=before_proof, perform=perform)
        janitor, authority = retained["janitor"], retained["authority"]
        assert_removed(janitor)
        assert (janitor.root / "shared").read_bytes() == retained["shared"]
        with sqlite3.connect(k.c.h.ledger.path) as db:
            assert db.execute("SELECT count(*) FROM reservations").fetchone() == (1,)
        with sqlite3.connect(authority.root / "state" / DATABASE) as db:
            assert db.execute("SELECT context IS NOT NULL, revoked FROM preauthorizations").fetchone() == (1, 0)
            assert db.execute("SELECT count(*) FROM observations").fetchone() == (1,)
    finally:
        if "fixture" in retained:
            retained["fixture"].close()
            assert all(process.poll() is not None and process.stdout.closed and process.stderr.closed
                       for process in retained["authority"].processes)
