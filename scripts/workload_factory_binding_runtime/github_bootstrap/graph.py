"""Accepted same-source graph with exactly two OIDC orchestration job classes."""
from dataclasses import dataclass
import yaml
from workload_factory_binding.evidence import BindingError, byte_digest, require
from ..workflow import REUSABLE
from . import ERROR

CHECKOUT = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
PYTHON = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
INSTALL = "pip install --only-binary :all: --require-hashes -r requirements-workload-binding.lock"
PREPARE = "python3 -I -B scripts/prepare-protected-runtime.py --phase "
ADMISSION_GUARD = "${{ github.repository == 'opensoft/openXwallet' && github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' && github.workflow_ref == 'opensoft/openXwallet/.github/workflows/protected-runtime-qualification.yml@refs/heads/main' }}"
PROTECTED_GUARD = "${{ needs.admission.result == 'success' && needs.admission.outputs.ready == 'true' }}"
PHASES = {"admission": ("preflight",), "protected-qualification": ("protected-admission", "qualify", "cleanup")}

@dataclass(frozen=True, repr=False)
class GraphSource:
    commit: str
    caller: bytes
    reusable: bytes

class _Loader(yaml.BaseLoader):
    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(k, deep=deep) for k, _ in node.value]
        require(all(type(x) is str for x in keys) and len(set(keys)) == len(keys), ERROR)
        return super().construct_mapping(node, deep)


def _documents(source, approval):
    config = approval.configuration
    require(type(source) is GraphSource and source.commit == config["launch"]["sha"], ERROR)
    for role, raw in (("caller_workflow", source.caller), ("reusable_workflow", source.reusable)):
        require(type(raw) is bytes and 0 < len(raw) <= 65536
                and byte_digest(raw) == config["sources"][role]["digest"], ERROR)
    return tuple(yaml.load(raw, Loader=_Loader) for raw in (source.caller, source.reusable))


def _interfaces(caller, reusable):
    require(set(caller) == {"name", "on", "permissions", "concurrency", "jobs"}
            and set(reusable) == {"name", "on", "permissions", "env", "jobs"}, ERROR)
    require(set(caller["jobs"]) == {"invoke"} and set(reusable["jobs"]) == set(PHASES)
            and caller["permissions"] == reusable["permissions"] == {}
            and set(caller["on"]) == {"workflow_dispatch"} and set(reusable["on"]) == {"workflow_call"}, ERROR)
    names = {"accepted_commit", "selection_digest", "preauthorization_ref"}
    require(set(caller["on"]["workflow_dispatch"]["inputs"]) == names
            and set(reusable["on"]["workflow_call"]["inputs"]) == names, ERROR)
    invoke = caller["jobs"]["invoke"]
    require(set(invoke) == {"uses", "permissions", "with"} and invoke["uses"] == "./" + REUSABLE
            and invoke["permissions"] == {"contents": "read", "id-token": "write"}
            and invoke["with"] == {n: "${{ inputs." + n + " }}" for n in names}, ERROR)
    require(reusable["env"] == {"OPENXWALLET_" + n.upper(): "${{ inputs." + n + " }}" for n in names}, ERROR)
    admission, protected = reusable["jobs"]["admission"], reusable["jobs"]["protected-qualification"]
    require("environment" not in admission and protected["environment"] == {"name": "${{ needs.admission.outputs.environment }}"}
            and protected["needs"] == "admission"
            and admission["outputs"] == {"ready": "${{ steps.admit.outputs.ready }}", "environment": "${{ steps.admit.outputs.environment }}"}, ERROR)


def _action(step, action, selected):
    require(type(step) is dict and set(step) <= {"name", "uses", "with"}
            and step.get("uses") == action and step.get("with") == selected, ERROR)


def _command(step, command, *, phase=None):
    allowed = {"name", "run"} | ({"if"} if phase == "cleanup" else set()) | ({"id"} if phase == "preflight" else set())
    require(type(step) is dict and set(step) <= allowed and type(step.get("run")) is str
            and step["run"].strip() == command, ERROR)
    if phase == "cleanup":
        require(step.get("if") == "${{ always() }}", ERROR)
    if phase == "preflight":
        require(step.get("id") == "admit", ERROR)


def _job(name, job):
    admission = name == "admission"
    allowed = {"if", "runs-on", "timeout-minutes", "permissions", "steps"}
    allowed |= {"outputs"} if admission else {"needs", "environment"}
    require(set(job) == allowed and job["permissions"] == {"contents": "read", "id-token": "write"}
            and job["runs-on"] == "ubuntu-24.04" and 1 <= int(job["timeout-minutes"]) <= 15
            and job["if"] == (ADMISSION_GUARD if admission else PROTECTED_GUARD), ERROR)
    phases, steps = PHASES[name], job["steps"]
    require(type(steps) is list and len(steps) == 3 + len(phases), ERROR)
    _action(steps[0], CHECKOUT, {"ref": "${{ github.workflow_sha }}", "persist-credentials": "false", "submodules": "false"})
    _action(steps[1], PYTHON, {"python-version": "3.12"})
    _command(steps[2], INSTALL)
    for step, phase in zip(steps[3:], phases):
        _command(step, PREPARE + phase, phase=phase)


def validate_graph(source, approval):
    try:
        caller, reusable = _documents(source, approval)
        _interfaces(caller, reusable)
        for name, job in reusable["jobs"].items():
            _job(name, job)
        return True
    except Exception:
        raise BindingError(ERROR) from None
