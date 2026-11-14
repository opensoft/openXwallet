"""In-memory token request against one independently selected job endpoint."""
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit
from workload_factory_binding.evidence import BindingError, reference, require
from . import ERROR, USER_AGENT
from .common import document
from .https import Https, Response

class TokenClient:
    def __init__(self, *, endpoint, audience, transport=None):
        parsed = urlsplit(endpoint)
        query = parse_qsl(parsed.query, keep_blank_values=True)
        require(parsed.scheme == "https" and parsed.hostname and parsed.username is None
                and parsed.password is None and not parsed.fragment and parsed.path.startswith("/")
                and len(query) == len({k for k, _ in query}) and all(k != "audience" for k, _ in query)
                and reference(audience), ERROR)
        self.endpoint, self.audience = endpoint, audience
        self.url = urlunsplit(parsed._replace(query=urlencode(query + [("audience", audience)])))
        self.transport = transport if transport is not None else Https()

    def acquire(self, environment, *, decision):
        try:
            require(environment.get("ACTIONS_ID_TOKEN_REQUEST_URL") == self.endpoint, ERROR)
            credential = environment.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
            require(reference(credential) and len(credential) <= 8192, ERROR)
            response = self.transport.exchange("GET", self.url, headers={
                "Authorization": "Bearer " + credential, "Accept": "application/json",
                "User-Agent": USER_AGENT, "Accept-Encoding": "identity"}, decision=decision)
            decision.now()
            require(type(response) is Response and response.status == 200, ERROR)
            value = document(response.body, 24576)
            # Project the SDK's required external field; bounded provider metadata
            # is ignored, never copied into the closed internal response.
            require(type(value) is dict and type(value.get("value")) is str and 0 < len(value["value"]) <= 16384, ERROR)
            return value["value"]
        except Exception:
            raise BindingError(ERROR) from None
