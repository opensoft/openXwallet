"""Private original-runner capture for one isolated intrinsic admission.

Trusted hosting supplies the original injection and independently accepted policy.
This capability does not authenticate a launcher or activate an operational host.
"""
from dataclasses import dataclass
from collections.abc import Mapping
import re
import threading
from types import MappingProxyType
from urllib.parse import urlencode, urlsplit

from workload_factory_binding.evidence import BindingError, canonical, reference, require
from ..bootstrap import validate_dispatch_context
from ..github_bootstrap import USER_AGENT
from ..github_bootstrap.client import TokenClient
from ..github_bootstrap.common import Decision, SHA
from ..github_bootstrap.https import Https
from ..github_bootstrap.identity import BOOTSTRAP_AUDIENCE
from ..hosted.private_http import PrivateHttps
from ..hosted.readback import ReadBudget
from ..hosted.stage_client import AdmissionClient, Channel

ERROR = "azure-runner-transport-refused"
_URL = "ACTIONS_ID_TOKEN_REQUEST_URL"
_BEARER = "ACTIONS_ID_TOKEN_REQUEST_TOKEN"
_PREFLIGHT = "preflight"
_PROTECTED = "protected-admission"
_SAFE = re.compile(r"[A-Za-z0-9._~-]{1,256}\Z", re.ASCII)


def _private(operation):
    # Raise outside the handler: suppressed display alone still retains context.
    try:
        return operation()
    except BaseException as error:
        cancelled = isinstance(error, KeyboardInterrupt)
    if cancelled:
        raise KeyboardInterrupt() from None
    raise BindingError(ERROR) from None


@dataclass(frozen=True, repr=False)
class RunnerPolicy:
    """Independent trusted selection, never derived from the captured URL."""
    source_commit: str
    phase: str
    origin: str
    path: str
    query: tuple = ()

    def endpoint(self):
        def selected():
            require(type(self.source_commit) is str and SHA.fullmatch(self.source_commit)
                    and self.source_commit != "0" * 40
                    and self.phase in (_PREFLIGHT, _PROTECTED), ERROR)
            require(type(self.origin) is str and len(self.origin) <= 512
                    and all(32 < ord(c) < 127 for c in self.origin), ERROR)
            parsed = urlsplit(self.origin)
            require(parsed.scheme == "https" and parsed.hostname
                    and re.fullmatch(r"[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?", parsed.hostname)
                    and parsed.username is None and parsed.password is None
                    and not parsed.path and not parsed.query and not parsed.fragment
                    and (parsed.port is None or 0 < parsed.port <= 65535), ERROR)
            authority = parsed.hostname + (":" + str(parsed.port) if parsed.port is not None else "")
            require(self.origin == "https://" + authority, ERROR)
            require(type(self.path) is str and self.path.startswith("/")
                    and len(self.path) <= 2048 and all(
                        _SAFE.fullmatch(part) and part not in (".", "..")
                        for part in self.path[1:].split("/")), ERROR)
            require(type(self.query) is tuple and len(self.query) <= 8
                    and all(type(pair) is tuple and len(pair) == 2
                            and all(type(v) is str and _SAFE.fullmatch(v) for v in pair)
                            and pair[0].lower() != "audience" for pair in self.query)
                    and len({p[0] for p in self.query}) == len(self.query), ERROR)
            suffix = "?" + urlencode(self.query) if self.query else ""
            endpoint = self.origin + self.path + suffix
            require(len(endpoint) <= 4096, ERROR)
            return endpoint
        return _private(selected)


class _Opaque:
    __slots__ = ()

    def __reduce_ex__(self, protocol):
        raise BindingError(ERROR)


class _TokenTransport(_Opaque):
    __slots__ = ("_https", "_guard", "_url", "_headers", "_decision", "_ca")

    def __init__(self, https, guard, url, bearer, decision):
        self._https, self._guard, self._url = https, guard, url
        self._decision, self._ca = decision, https.ca_file
        self._headers = {"Authorization": "Bearer " + bearer, "Accept": "application/json",
                         "User-Agent": USER_AGENT, "Accept-Encoding": "identity"}

    def exchange(self, method, url, *, headers, decision):
        def exchange():
            require(method == "GET" and url == self._url and headers == self._headers
                    and decision is self._decision and type(self._https) is Https
                    and self._https.ca_file == self._ca, ERROR)
            return self._https.exchange(method, url, headers=headers, decision=decision,
                                        before_send=self._guard)
        return _private(exchange)


class RunnerCapture(_Opaque):
    """One private URL/bearer capture and one non-renewable GET/POST attempt.

    Original injection is retained only for negative drift detection through GET's
    TLS send checkpoint. The returned token alone authenticates intrinsic POST.
    No worker-supplied overrides, export, retry or default construction route.
    """
    __slots__ = ("_policy", "_endpoint", "_bearer", "_original", "_context", "_context_raw",
                 "_admission", "_admission_binding", "_decision", "_clock", "_monotonic",
                 "_deadline", "_end", "_budget", "_counts", "_token_client", "_used", "_lock")

    def __init__(self, *, policy, context, original_environment, admission, transport, decision):
        _private(lambda: self._initialize(policy, context, original_environment, admission, transport, decision))

    def _initialize(self, policy, context, original, admission, transport, decision):
        require(type(policy) is RunnerPolicy and isinstance(original, Mapping)
                and type(transport) is Https and type(decision) is Decision, ERROR)
        validate_dispatch_context(context)
        endpoint = policy.endpoint()
        require(policy.source_commit == context.source_commit == context.accepted_commit, ERROR)
        require(type(admission) is AdmissionClient and type(admission.channel) is Channel
                and type(admission.channel.transport) is PrivateHttps
                and admission.phase == (_PREFLIGHT if policy.phase == _PREFLIGHT else "protected"), ERROR)
        admission.channel.current()
        bearer = original.get(_BEARER)
        require(original.get(_URL) == endpoint and reference(bearer)
                and len(bearer) <= 512, ERROR)
        from dataclasses import asdict
        self._policy, self._endpoint, self._bearer = policy, endpoint, bearer
        self._original, self._context, self._context_raw = original, context, canonical(asdict(context))
        self._admission, self._decision = admission, decision
        self._admission_binding = self._channel_binding()
        self._clock, self._monotonic = decision.clock, decision.monotonic
        self._deadline, self._end = decision.deadline, decision.end
        self._budget = ReadBudget(decision)
        self._counts = dict(self._budget.state["counts"])
        self._used, self._lock = False, threading.Lock()
        client = TokenClient(endpoint=endpoint, audience=BOOTSTRAP_AUDIENCE)
        client.transport = _TokenTransport(transport, self._capture_current, client.url, bearer, decision)
        self._token_client = client
        self._capture_current()

    def _channel_binding(self):
        client = self._admission
        require(type(client) is AdmissionClient and type(client.channel) is Channel
                and type(client.channel.transport) is PrivateHttps and not client.channel.private, ERROR)
        client.channel.current()
        return (client.channel, client.phase, client.path, client.binding, client.channel.binding)

    def _current(self):
        from dataclasses import asdict
        use = self._decision
        require(use.clock is self._clock and use.monotonic is self._monotonic
                and use.deadline <= self._deadline and use.end <= self._end
                and use._hosted_reads is self._budget.state
                and self._policy.endpoint() == self._endpoint
                and canonical(asdict(self._context)) == self._context_raw
                and self._channel_binding() == self._admission_binding, ERROR)
        self._budget.check()
        counts = self._budget.state["counts"]
        require(set(counts) == set(self._counts)
                and all(type(counts[k]) is int and counts[k] >= v for k, v in self._counts.items()), ERROR)
        self._counts = dict(counts)
        self._deadline, self._end = use.deadline, use.end

    def _capture_current(self):
        self._current()
        require(self._original.get(_URL) == self._endpoint
                and self._original.get(_BEARER) == self._bearer, ERROR)

    def admit(self):
        def admit():
            with self._lock:
                require(not self._used, ERROR)
                self._used = True  # consumed before validation or any possible transmission
            self._capture_current()
            # A fresh private projection, never a reference to mutable injection.
            frozen = MappingProxyType({_URL: self._endpoint, _BEARER: self._bearer})
            token = self._token_client.acquire(frozen, decision=self._decision)
            self._current()  # original injection has no role in the POST route
            require(type(token) is str and 0 < len(token) <= 16377
                    and all(32 < ord(c) < 127 for c in token), ERROR)
            result = self._admission.read(self._context, token, decision=self._decision)
            self._current()
            require(result.state == ("plan-ready" if self._policy.phase == _PREFLIGHT else "running"), ERROR)
            return result
        return _private(admit)
