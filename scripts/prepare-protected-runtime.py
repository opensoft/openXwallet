#!/usr/bin/env python3
"""Protected workflow source entrypoint; operational hosting remains unselected."""
import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.evidence import safe_error
from workload_factory_binding_runtime.bootstrap import DispatchContext, bootstrap, validate_dispatch_context
from workload_factory_binding_runtime.workflow import operational_bindings, GithubWorkflowBindings, admit_github, HostedWorkflowBindings, admit_hosted, QualificationWorkflowBindings, qualify_hosted


def context_from_environment(environment, source_commit):
    names = ("GITHUB_REPOSITORY", "GITHUB_REPOSITORY_ID", "GITHUB_EVENT_NAME", "GITHUB_REF", "GITHUB_SHA",
             "GITHUB_WORKFLOW_REF", "GITHUB_WORKFLOW_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT",
             "OPENXWALLET_ACCEPTED_COMMIT", "OPENXWALLET_SELECTION_DIGEST", "OPENXWALLET_PREAUTHORIZATION_REF")
    return DispatchContext(*(environment.get(name, "") for name in names), source_commit)


class _PrivateParser(argparse.ArgumentParser):
    def error(self, _message):
        # argparse's default error echoes arbitrary invalid arguments before the
        # runtime boundary. Keep invalid input on the same fixed-code contract.
        raise BindingError("workflow-input-unavailable") from None


def _prepare(args):
    source = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True,
                            text=True, timeout=10).stdout.strip()
    context = context_from_environment(os.environ, source)
    validate_dispatch_context(context)
    # Intentionally blocks before any environment output or OIDC operation.
    # Production binding selection needs a later reviewed source integration.
    bindings = operational_bindings()
    if type(bindings) is QualificationWorkflowBindings:
        report = qualify_hosted(context, bindings=bindings, phase=args.phase)
        if args.phase == "qualify":
            sys.stdout.buffer.write(report + b"\n")
        return
    if args.phase not in ("preflight", "protected-admission"):
        # T012 prepares admission/job wiring. Live execution and independent
        # cleanup adapters remain gated; never substitute the offline suite.
        raise BindingError("workflow-live-qualification-not-performed")
    if type(bindings) is HostedWorkflowBindings:
        admitted = admit_hosted(context, bindings=bindings, phase=args.phase, environment=os.environ)
    elif type(bindings) is GithubWorkflowBindings:
        admitted = admit_github(context, bindings=bindings, phase=args.phase, environment=os.environ)
    elif args.phase == "preflight":
        admitted = bootstrap(context, bindings=bindings)
    else:
        raise BindingError("workflow-admission-refused")
    output = Path(os.environ["GITHUB_OUTPUT"])
    with output.open("a", encoding="utf-8") as stream:
        stream.write("ready=true\nenvironment=" + admitted.environment + "\n")


def main():
    parser = _PrivateParser(description=__doc__)
    parser.add_argument("--phase", choices=("preflight", "protected-admission", "qualify", "cleanup"), required=True)
    status = 0
    parsing = True

    def finish_command(_kind, error, _traceback):
        nonlocal status
        if error is None:
            return False
        if parsing and type(error) is SystemExit and type(error.code) is int and error.code == 0:
            return True  # argparse help completed before context or binding lookup.
        print(safe_error(error), file=sys.stderr)
        status = 2 if isinstance(error, Exception) else 130
        return True

    # The executable boundary translates failures into a fixed process status
    # and redacted stderr, including interruptions during parsing or execution.
    with ExitStack() as command:
        command.push(finish_command)
        args = parser.parse_args()
        parsing = False
        _prepare(args)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
