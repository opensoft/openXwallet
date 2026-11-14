"""Fixed-version, authenticated bounded reads; response URLs never select requests."""
from workload_factory_binding.evidence import BindingError, reference, require
from . import ERROR, USER_AGENT
from .broker import API, VERSION
from .common import document, number
from .https import Https, Response

RUNS_PATH = "/actions/runs/"

class ProviderReader:
    def __init__(self, *, credential, transport=None):
        self.credential = credential
        self.transport = transport if transport is not None else Https()

    def decision(self, repository, decision):
        require(repository == "opensoft/openXwallet", ERROR)
        return _Reads(self, repository, decision)

class _Reads:
    def __init__(self, reader, repository, decision):
        self.reader, self.repository, self.use = reader, repository, decision
        self.count = 0

    def _get(self, suffix):
        try:
            require(self.use.api_requests < 4, ERROR)
            self.count += 1
            self.use.api_requests += 1
            token = self.reader.credential(deadline=self.use.deadline)
            self.use.now()
            require(reference(token) and len(token) <= 8192, ERROR)
            response = self.reader.transport.exchange("GET", API + "/repos/" + self.repository + suffix,
                headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                    "User-Agent": USER_AGENT, "Accept-Encoding": "identity", "X-GitHub-Api-Version": VERSION}, decision=self.use)
            self.use.now()
            require(type(response) is Response and response.status == 200, ERROR)
            return document(response.body, 1048576)
        except Exception:
            raise BindingError(ERROR) from None

    def run(self, run_id):
        require(number(run_id), ERROR)
        return self._get(RUNS_PATH + run_id)

    def jobs(self, run_id, attempt):
        require(number(run_id) and number(attempt), ERROR)
        result, total = [], None
        for page in (1, 2):
            value = self._get(RUNS_PATH + run_id + "/attempts/" + attempt + "/jobs?per_page=100&page=" + str(page))
            require(type(value) is dict and type(value.get("total_count")) is int
                    and 0 < value["total_count"] <= 200 and type(value.get("jobs")) is list
                    and 0 < len(value["jobs"]) <= 100, ERROR)
            require(total is None or value["total_count"] == total, ERROR)
            total = value["total_count"]
            result.extend(value["jobs"])
            require(len(result) <= total, ERROR)
            if len(result) == total:
                require(all(type(x) is dict and type(x.get("id")) is int and number(str(x["id"])) for x in result)
                        and len({x["id"] for x in result}) == len(result), ERROR)
                return result
            require(len(value["jobs"]) == 100, ERROR)
        raise BindingError(ERROR)

    def reviews(self, run_id):
        require(number(run_id), ERROR)
        value = self._get(RUNS_PATH + run_id + "/approvals")
        require(type(value) is list and 0 < len(value) <= 100, ERROR)
        return value
