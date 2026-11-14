"""Pinned mTLS authority client and adapter bridge, explicitly fixture-scoped."""
from dataclasses import asdict, replace
import http.client
import ssl
import time
import threading

from workload_factory_binding.evidence import BindingError, canonical, digest, integer, require, valid_digest
from ..bootstrap import BootstrapBindings, BootstrapReadback, selection_digest, selection_document, validate_dispatch_context
from ..config import _configuration
from ..workflow import OperationReadback, WorkflowBindings
from .model import ERROR, PROFILE, SCOPE, closed, window
from .transport import LIMIT, decode_message, fingerprint


class AuthorityClient:
    def __init__(self, *, port, ca_file, cert_file, key_file, server_fingerprint, clock):
        require(type(port) is int and 0 < port <= 65535 and valid_digest(server_fingerprint) and callable(clock), ERROR)
        self.port, self.server_fingerprint, self.clock = port, server_fingerprint, clock
        self.tls = ssl.create_default_context(cafile=ca_file)
        self.tls.minimum_version = ssl.TLSVersion.TLSv1_2
        self.tls.load_cert_chain(cert_file, key_file)

    def request(self, method, *, deadline, **arguments):
        now = self.clock()
        require(integer(now) and integer(deadline) and now < deadline, ERROR)
        budget = time.monotonic() + min(5, deadline - now)
        connection = http.client.HTTPSConnection("127.0.0.1", self.port, context=self.tls,
                                                  timeout=min(2, deadline - now))
        timer = None
        try:
            body = canonical(dict(method=method, arguments=arguments))
            require(len(body) <= LIMIT, ERROR)
            connection.connect()
            require(fingerprint(connection.sock.getpeercert(binary_form=True)) == self.server_fingerprint
                    and time.monotonic() < budget, ERROR)
            active_socket = connection.sock
            def expire():
                try:
                    active_socket.shutdown(2)
                except OSError:
                    pass
            timer = threading.Timer(max(0, budget - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            connection.request("POST", "/", body=body, headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            require(response.getheaders().count(("Content-Type", "application/json")) == 1
                    and response.getheader("Transfer-Encoding") is None, ERROR)
            lengths = response.headers.get_all("Content-Length")
            require(lengths is not None and len(lengths) == 1 and lengths[0].isascii()
                    and lengths[0].isdecimal() and len(lengths[0]) <= 6 and 0 < int(lengths[0]) <= LIMIT, ERROR)
            raw = response.read(LIMIT + 1)
            require(len(raw) == int(lengths[0]) and time.monotonic() < budget
                    and now <= self.clock() < deadline, ERROR)
            value = decode_message(raw)
            if response.status == 403 and value == {"error": "bootstrap-authority-denied"}:
                raise BindingError("bootstrap-authority-denied")
            require(response.status == 200, ERROR)
            return value
        except BindingError as exc:
            if str(exc) == "bootstrap-authority-denied":
                raise
            raise BindingError("workflow-input-unavailable") from None
        except Exception:
            raise BindingError("workflow-input-unavailable") from None
        finally:
            if timer is not None:
                timer.cancel()
                timer.join(timeout=1)
            connection.close()


def probe_worker_denied(worker, *, context, event_ref, deadline):
    """Caller must establish the same positive reader path first. Outage is failure."""
    try:
        worker.request("claim", context=asdict(context), event_ref=event_ref, deadline=deadline)
    except BindingError as exc:
        require(str(exc) == "bootstrap-authority-denied", ERROR)
        return
    raise BindingError(ERROR)


class AuthoritySession:
    """Snapshot configuration plus fresh bootstrap/operation reads on every use.

    Other readbacks, source checks, lease, custody, and runtime replay protection
    remain mandatory and independently selected by the existing adapter.
    """
    def __init__(self, client, *, context, event_ref, deadline,
                 bootstrap_principal="principal:bootstrap", operation_principal="principal:operation-reader"):
        validate_dispatch_context(context)
        self.client, self.context, self.event_ref = client, context, event_ref
        self.bootstrap_principal, self.operation_principal = bootstrap_principal, operation_principal
        self.value = self._read("claim", deadline)
        self.raw = canonical(self.value["configuration"])

    def _read(self, method, deadline):
        try:
            value = self.client.request(method, context=asdict(self.context), event_ref=self.event_ref, deadline=deadline)
            closed(value, "profile scope configuration bootstrap operation")
            require(value["profile"] == PROFILE and value["scope"] == SCOPE, ERROR)
            config = value["configuration"]
            _configuration(config)
            require(selection_digest(selection_document(config)) == self.context.selection_digest, ERROR)
            closed(value["bootstrap"], " ".join(BootstrapReadback.__dataclass_fields__))
            closed(value["operation"], " ".join(OperationReadback.__dataclass_fields__))
            b, o, c = BootstrapReadback(**value["bootstrap"]), OperationReadback(**value["operation"]), self.context
            now = self.client.clock()
            for record in (b, o):
                window(record.observed_at, record.expires_at, now)
            require(b.principal_ref == self.bootstrap_principal and o.principal_ref == self.operation_principal
                    and b.preauthorization_ref == c.preauthorization_ref and b.selection_digest == c.selection_digest
                    and b.accepted_commit == o.accepted_commit == c.accepted_commit
                    and b.repository_id == c.repository_id
                    and b.case_ref == o.case_ref == config["case_ref"]
                    and b.run_id == o.run_id == config["launch"]["run_id"] == c.run_id
                    and b.run_attempt == o.run_attempt == config["launch"]["run_attempt"] == c.run_attempt
                    and b.config_digest == o.config_digest == digest(config)
                    and o.action == "qualify-existing-resources"
                    and b.operation_grant_ref == o.grant_ref
                    and b.operation_grant_ref == "grant:runtime-" + digest(asdict(c)).removeprefix("sha256:"), ERROR)
            if hasattr(self, "value"):
                require(value["configuration"] == self.value["configuration"]
                        and b.operation_grant_ref == self.value["bootstrap"]["operation_grant_ref"], ERROR)
            return value
        except Exception:
            raise BindingError(ERROR) from None

    def bindings(self, workflow):
        require(type(workflow) is WorkflowBindings, ERROR)
        trust = replace(workflow.runtime_trust, approved_config_digest=digest(self.value["configuration"]))
        def read_bootstrap(ref, context, *, deadline):
            require(ref == self.context.preauthorization_ref and context == self.context, ERROR)
            return BootstrapReadback(**self._read("claim", deadline)["bootstrap"])
        def read_authorization(ref, *, deadline):
            record = OperationReadback(**self._read("operation", deadline)["operation"])
            require(ref == record.grant_ref, ERROR)
            return record
        workflow = replace(workflow, load_config=lambda: self.raw, runtime_trust=trust,
                           authorization_principal_ref=self.operation_principal, read_authorization=read_authorization)
        return BootstrapBindings(self.context.selection_digest, self.bootstrap_principal, read_bootstrap, workflow)
