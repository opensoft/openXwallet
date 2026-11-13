#!/usr/bin/env python3
"""Prepared workflow entrypoint. No setup, dispatch, token mint or live client."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workload_factory_binding.evidence import BindingError
from workload_factory_binding_runtime.evidence import safe_error
from workload_factory_binding_runtime.workflow import WorkflowContext, admit, operational_bindings, validate_context


def context_from_environment(environment, source_commit):
    names = ("GITHUB_REPOSITORY", "GITHUB_REPOSITORY_ID", "GITHUB_EVENT_NAME", "GITHUB_REF", "GITHUB_SHA",
             "GITHUB_WORKFLOW_REF", "GITHUB_WORKFLOW_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT",
             "OPENXWALLET_ACCEPTED_COMMIT", "OPENXWALLET_CONFIG_DIGEST", "OPENXWALLET_OPERATION_GRANT_REF")
    return WorkflowContext(*(environment.get(name, "") for name in names), source_commit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("preflight", "qualify", "cleanup"), required=True)
    args = parser.parse_args()
    try:
        source = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True,
                                text=True, timeout=10).stdout.strip()
        context = context_from_environment(os.environ, source)
        validate_context(context)
        # Intentionally blocks before any environment output or OIDC operation.
        # Production binding selection needs a later reviewed source integration.
        bindings = operational_bindings()
        if args.phase != "preflight":
            # T012 prepares admission/job wiring. Live execution and independent
            # cleanup adapters remain gated; never substitute the offline suite.
            raise BindingError("workflow-live-qualification-not-performed")
        admitted = admit(context, bindings=bindings)
        output = Path(os.environ["GITHUB_OUTPUT"])
        with output.open("a", encoding="utf-8") as stream:
            stream.write("ready=true\nenvironment=" + admitted.environment + "\n")
        return 0
    except Exception as error:
        print(safe_error(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
