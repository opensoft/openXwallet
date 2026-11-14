"""Accepted same-source graph with exactly two OIDC orchestration job classes."""
from dataclasses import dataclass
import yaml
from workload_factory_binding.evidence import BindingError, byte_digest, require
from ..workflow import REUSABLE
from . import ERROR

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


def validate_graph(source, approval):
    try:
        c = approval.configuration
        require(type(source) is GraphSource and source.commit == c["launch"]["sha"], ERROR)
        for role, raw in (("caller_workflow", source.caller), ("reusable_workflow", source.reusable)):
            require(type(raw) is bytes and 0 < len(raw) <= 65536
                    and byte_digest(raw) == c["sources"][role]["digest"], ERROR)
        caller, reusable = (yaml.load(raw, Loader=_Loader) for raw in (source.caller, source.reusable))
        require(set(caller) == {"name", "on", "permissions", "concurrency", "jobs"}
                and set(reusable) == {"name", "on", "permissions", "env", "jobs"}, ERROR)
        require(set(caller["jobs"]) == {"invoke"} and set(reusable["jobs"]) == {"admission", "protected-qualification"}
                and caller["permissions"] == reusable["permissions"] == {}
                and set(caller["on"]) == {"workflow_dispatch"} and set(reusable["on"]) == {"workflow_call"}, ERROR)
        names = {"accepted_commit", "selection_digest", "preauthorization_ref"}
        require(set(caller["on"]["workflow_dispatch"]["inputs"]) == names
                and set(reusable["on"]["workflow_call"]["inputs"]) == names, ERROR)
        invoke = caller["jobs"]["invoke"]
        require(set(invoke) == {"uses", "permissions", "with"}
                and invoke["uses"] == "./" + REUSABLE
                and invoke["permissions"] == {"contents": "read", "id-token": "write"}
                and invoke["with"] == {n: "${{ inputs." + n + " }}" for n in names}, ERROR)
        require(reusable["env"] == {"OPENXWALLET_" + n.upper(): "${{ inputs." + n + " }}" for n in names}, ERROR)
        admission, protected = reusable["jobs"]["admission"], reusable["jobs"]["protected-qualification"]
        require("environment" not in admission and protected["environment"] == {"name": "${{ needs.admission.outputs.environment }}"}
                and protected["needs"] == "admission"
                and admission["outputs"] == {"ready": "${{ steps.admit.outputs.ready }}", "environment": "${{ steps.admit.outputs.environment }}"}, ERROR)
        phase_commands = {"admission": ["preflight"], "protected-qualification": ["protected-admission", "qualify", "cleanup"]}
        for name, job in reusable["jobs"].items():
            allowed = {"if", "runs-on", "timeout-minutes", "permissions", "steps"}
            allowed |= {"outputs"} if name == "admission" else {"needs", "environment"}
            require(set(job) == allowed
                    and job["permissions"] == {"contents": "read", "id-token": "write"}
                    and job["runs-on"] == "ubuntu-24.04" and int(job["timeout-minutes"]) <= 15, ERROR)
            commands = []
            for step in job["steps"]:
                require(set(step) <= {"name", "id", "uses", "with", "run", "if"}
                        and ("uses" in step) != ("run" in step)
                        and ("if" not in step or (step.get("run", "").endswith("--phase cleanup")
                             and step["if"] == "${{ always() }}")), ERROR)
                if "uses" in step:
                    require(step["uses"] in (
                        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
                        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"), ERROR)
                    if step["uses"].startswith("actions/checkout@"):
                        require(step["with"] == {"ref": "${{ github.workflow_sha }}", "persist-credentials": "false", "submodules": "false"}, ERROR)
                    else:
                        require(step.get("with") == {"python-version": "3.12"}, ERROR)
                else:
                    require("with" not in step, ERROR)
                    command = step["run"].strip()
                    if command.startswith("python3 -I -B scripts/prepare-protected-runtime.py --phase "):
                        commands.append(command.rsplit(" ", 1)[1])
                    else:
                        require(command == "pip install --only-binary :all: --require-hashes -r requirements-workload-binding.lock", ERROR)
            require(commands == phase_commands[name], ERROR)
        return True
    except Exception:
        raise BindingError(ERROR) from None
