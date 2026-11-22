"""Explicit P06 composition of existing private enrollment and App issuance ports.

Construction is trusted source selection, not setup or activation. No listeners,
ambient identity, state initialization, retries or remote-measurement dependency.
"""
from contextlib import contextmanager
from dataclasses import asdict
import base64
import os
import socket
from urllib.parse import urlsplit
from threading import RLock
from workload_factory_binding.evidence import BindingError, canonical, digest, require
from ..github_bootstrap.common import Decision, document
from ..hosted._credential_io import parse_target, github_path, vault_route
from ..hosted.credential import credential_request
from ..hosted.enrollment import EnrollmentAuthority
from ..hosted.issuance import (InstallationIssuer, InstallationRetirer, RoleDelivery,
                               selection_record, IssuedToken)
from ..hosted.nonces import ERROR, NonceLedger, Unavailable, identity
from ..hosted.private_http import PrivateHttps
from ..hosted.readback import LIMITS, ReadBudget, _ReadCheckpoint, _read_checkpoint


def private(operation):
    # Raise outside the handler: even retained tracebacks have no private cause.
    try:
        return operation()
    except BaseException as error:
        cancelled = isinstance(error, KeyboardInterrupt)
        unavailable = isinstance(error, Unavailable)
    if cancelled:
        raise KeyboardInterrupt() from None
    if unavailable:
        raise Unavailable(ERROR) from None
    raise BindingError(ERROR) from None


class Opaque:
    __slots__ = ()
    def __getstate__(self):
        raise BindingError(ERROR)
    def __reduce_ex__(self, protocol):
        raise BindingError(ERROR)


def transport_binding(transport):
    require(type(transport) is PrivateHttps
            and all(x is None for x in (transport.observation_origin, transport.agent_origin,
                                       transport.admission_origin, transport.lifecycle_origin)), ERROR)
    expected = [] if transport.fixture_origin is None else ['--fixture-port', str(urlsplit(transport.fixture_origin).port)]
    require(transport.fixture_args == expected, ERROR)
    return (transport, transport.fixture_origin, tuple(transport.fixture_args),
            transport.server_certificate_digest, transport.ca, transport.cert, transport.key,
            transport.exchange, transport.materials())


class Provider(Opaque):
    """Charge each actual closed provider call before any fixture translation."""
    __slots__ = ('selection', 'http', 'decision', 'check', '_binding')
    def __init__(self, selection, transport, decision, check):
        self.selection, self.http, self.decision, self.check = selection, transport, decision, check
        self._binding = self.binding()

    def binding(self):
        return (self.selection, canonical(selection_record(self.selection)),
                transport_binding(self.http), self.decision, self.check)

    def exchange(self, method, url, *, decision, before_send=lambda: None, **kwargs):
        return private(lambda: self._exchange(method, url, decision, before_send, kwargs))

    def _exchange(self, method, url, decision, before_send, kwargs):
        require(decision is self.decision and self.binding() == self._binding, ERROR)
        self.check()
        selected = parse_target(method, url)
        if selected.netloc == 'api.github.com':
            github_path(method, selected.path, selected.query)
            install = '/app/installations/' + str(self.selection.installation_id)
            allowed = {('GET', '/app', ''), ('GET', install, ''),
                       ('POST', install + '/access_tokens', ''),
                       ('GET', '/installation/repositories', 'per_page=2&page=1'),
                       ('DELETE', '/installation/token', '')}
            require((method, selected.path, selected.query) in allowed, ERROR)
            group = 'source' if method == 'GET' else 'control'
        else:
            vault_route(method, selected)
            require(url == self.selection.key_uri + '/sign?api-version=2025-07-01', ERROR)
            group = 'key'
        budget = ReadBudget(decision)
        budget.consume(group)
        budget.consume('private')
        def checkpoint():
            self.check()
            before_send()
            self.check()
            require(self.binding() == self._binding, ERROR)
        checkpoint()
        target = url
        if self.http.fixture_origin is not None:
            target = self.http.fixture_origin + selected.path
            if selected.query:
                target += '?' + selected.query
        result = self.http.exchange(method, target, decision=decision,
                                    before_send=checkpoint, **kwargs)
        self.check()
        require(self.binding() == self._binding, ERROR)
        return result


class Operation(Opaque):
    """Keep the original accounting identities/highwaters across every invocation."""
    __slots__ = ('decision', 'budget', '_checkpoint', '_lock')
    def __init__(self, decision):
        require(type(decision) is Decision, ERROR)
        self._lock = RLock()
        self.decision, self.budget = decision, ReadBudget(decision)
        self._checkpoint = _ReadCheckpoint(decision, self.budget.state)

    def check(self):
        require(self.decision is self.budget.decision is self._checkpoint.decision
                and self.budget.state is self._checkpoint.state, ERROR)
        self._checkpoint.check()
        self.budget.check()
        self._checkpoint.check()
        state = self.budget.state
        limits = dict(LIMITS)
        if state['staging']:
            limits.update(protection=6, source=8, control=4, private=16)
        elif state['finalization']:
            limits['protection'] = 18
        elif state['qualification']:
            limits['private'] = 39
        require(all(state['counts'][name] <= limit for name, limit in limits.items()), ERROR)

    @contextmanager
    def guarded(self):
        with self._lock, _read_checkpoint(self.decision, self.budget.state):
            self.check()
            try:
                yield
            finally:
                self.check()
                self._checkpoint = _ReadCheckpoint(self.decision, self.budget.state)


class Issuance(Operation):
    """Private source-selected actor, bound to one original issuance Decision.

    Current readers are independently selected local capabilities. Readers that
    perform I/O must use existing charged clients under this same Decision.
    The kernel channel is supplied by the trusted embedding; it carries requests
    only. credential_request creates and closes a fresh private reply capability.
    """
    __slots__ = ('enrollment', 'issuer', 'delivery', 'provider', 'channel',
                 '_enrollment_reader', '_issuer_reader', '_binding')
    def __init__(self, *, enrollment, selection, ledger, transport, credential_channel,
                 read_current, current_principal, decision):
        private(lambda: self._initialize(enrollment, selection, ledger, transport,
                    credential_channel, read_current, current_principal, decision))

    def _initialize(self, enrollment, selection, ledger, transport, channel, reader, principal, decision):
        Operation.__init__(self, decision)
        require(type(enrollment) is EnrollmentAuthority and type(ledger) is NonceLedger
                and enrollment.ledger is not ledger
                and enrollment.ledger.identity != ledger.identity
                and callable(reader) and type(channel) is socket.socket
                and channel.family == socket.AF_UNIX
                and channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) == socket.SOCK_SEQPACKET, ERROR)
        channel.getpeername()
        self.channel = channel
        self._enrollment_reader, self._issuer_reader = enrollment.read_current, reader
        self.enrollment = EnrollmentAuthority(selection=enrollment.selection, ledger=enrollment.ledger,
            ca_key=enrollment.key, ca_certificate=enrollment.ca,
            read_current=self._enrollment_current, current_principal=enrollment.principal)
        self.provider = Provider(selection, transport, decision, self.check)
        self.issuer = InstallationIssuer(selection=selection, ledger=ledger,
            transport=self.provider, vault_credential=self._credential,
            read_current=self._issuer_current, current_principal=principal)
        self.delivery = RoleDelivery(enrollment=self.enrollment, issuer=self.issuer)
        self._binding = self.binding()
        self.check()

    def binding(self):
        a, i = self.enrollment, self.issuer
        try:
            require(identity(a.ledger.directory) == a.ledger.identity
                    and identity(i.ledger.directory) == i.ledger.identity, ERROR)
        except Exception:
            raise Unavailable(ERROR) from None
        return (a, a.selection, canonical(asdict(a.selection)), a.selection_digest,
                a.ledger, a.ledger.directory, a.ledger.identity, a.key, a.ca, a.principal,
                a.read_current, self._enrollment_reader,
                i, i.selection, canonical(selection_record(i.selection)), canonical(i.record),
                i.selection_digest, i.ledger, i.ledger.directory, i.ledger.identity,
                i.principal, i.read_current, self._issuer_reader, i.vault_credential,
                i.transport, self.provider, self.provider.binding(),
                self.delivery, self.delivery.enrollment, self.delivery.issuer,
                self.channel, self.channel.fileno(), os.fstat(self.channel.fileno()),
                self.channel.getpeername())

    def check(self):
        Operation.check(self)
        require(self.binding() == self._binding, ERROR)
        Operation.check(self)

    def _current(self, reader, ref, deadline):
        self.check()
        require(deadline <= self.decision.deadline, ERROR)
        with self.guarded():
            result = reader(ref, deadline=deadline)
            self.check()
            return result

    def _enrollment_current(self, ref, *, deadline):
        return self._current(self._enrollment_reader, ref, deadline)

    def _issuer_current(self, ref, *, deadline):
        return self._current(self._issuer_reader, ref, deadline)

    def _credential(self, *, deadline):
        self.check()
        require(deadline <= self.decision.deadline, ERROR)
        with self.guarded():
            self.budget.consume('private')
            raw = credential_request(self.channel,
                canonical({'role': 'issuer', 'operation': 'resolver'}), decision=self.decision)
            self.check()
            value = document(raw, 16384)
            require(type(value) is dict and set(value) == {'status', 'value'}
                    and value['status'] == 'ok' and type(value['value']) is str, ERROR)
            result = base64.b64decode(value['value'], validate=True).decode('ascii')
            require(0 < len(result) <= 8192 and all(32 < ord(c) < 127 for c in result), ERROR)
            return result

    def enroll(self, raw, *, channel):
        return private(lambda: self._enroll(raw, channel))

    def _enroll(self, raw, channel):
        with self.guarded():
            self.budget.consume('private')
            return self.enrollment.enroll(raw, channel=channel, decision=self.decision)

    def deliver(self, raw, *, channel):
        return private(lambda: self._deliver(raw, channel))

    def _deliver(self, raw, channel):
        with self.guarded():
            self.budget.consume('private')
            return self.delivery.deliver(raw, channel=channel, decision=self.decision)

    def pending(self, ref):
        # Cleanup access is private, and may outlive use authority. It never
        # resolves a usable credential or starts another minting attempt.
        def selected():
            require(self.binding() == self._binding, ERROR)
            return self.issuer.pending(ref)
        return private(selected)


class Retirement(Operation):
    """Explicit independent retirement; a new cleanup clock cannot renew use."""
    __slots__ = ('capability', 'writer', 'observer', 'retirer', '_binding')
    def __init__(self, *, capability, selection, writer, observer, decision):
        private(lambda: self._initialize(capability, selection, writer, observer, decision))

    def _initialize(self, capability, selection, writer, observer, decision):
        Operation.__init__(self, decision)
        require(writer is not observer and type(capability) is IssuedToken
                and capability.selection_digest == digest(selection_record(selection))
                and capability.role == selection.role
                and identity(capability.ledger.directory) == capability.ledger.identity, ERROR)
        self.capability = capability
        self.writer = Provider(selection, writer, decision, self.check)
        self.observer = Provider(selection, observer, decision, self.check)
        self.retirer = InstallationRetirer(writer=self.writer, observer=self.observer)
        self._binding = self.binding()
        self.check()

    def binding(self):
        require(identity(self.capability.ledger.directory) == self.capability.ledger.identity, ERROR)
        return (self.capability, self.capability.ledger, self.capability.ledger.directory,
                self.capability.ledger.identity,
                self.writer, self.writer.binding(), self.observer, self.observer.binding(),
                self.retirer, self.retirer.writer, self.retirer.observer)

    def check(self):
        Operation.check(self)
        require(self.binding() == self._binding, ERROR)

    def retire(self):
        return private(lambda: self._retire(False))

    def reconcile(self):
        return private(lambda: self._retire(True))

    def _retire(self, reconcile):
        with self.guarded():
            method = self.retirer.reconcile if reconcile else self.retirer.retire
            return method(self.capability, decision=self.decision)
