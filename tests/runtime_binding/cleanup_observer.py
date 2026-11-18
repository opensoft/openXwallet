"""Test-only fresh observer process; selected audit inputs come from its parent."""
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def main():
    from workload_factory_binding.evidence import canonical, decode_object, require
    from workload_factory_binding_runtime.bootstrap import DispatchContext
    from workload_factory_binding_runtime.hosted.lifecycle import run_plan
    from workload_factory_binding_runtime.hosted.lifecycle_service import LifecycleClient
    from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
    from workload_factory_binding_runtime.hosted.qualification import RegisteredCleanupClient
    from workload_factory_binding_runtime.loaders import ServiceIdentity
    from workload_factory_binding_runtime.workflow import QualificationWorkflowBindings, WorkflowContext, qualify_hosted
    try:
        value = decode_object(Path(sys.argv[1]).read_bytes())
        require(set(value) == {"plan", "context", "dispatch", "identity", "audit", "now"}, "fixture-refused")
        status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
        require(os.geteuid() != 0 and not os.getgroups() and status["NoNewPrivs"].strip() == "1"
                and all(int(status[k].strip(),16) == 0 for k in ("CapEff","CapPrm","CapAmb","CapBnd")), "fixture-refused")
        selected = value["audit"]
        transport = PrivateHttps(ca_file=selected["ca"], certificate=selected["certificate"],
            private_key=selected["key"], lifecycle_origin=selected["origin"],
            server_certificate_digest=selected["server_certificate_digest"])
        audit = LifecycleClient(origin=selected["origin"], principal=selected["principal"],
            scope=selected["scope"], transport=transport)
        plan = run_plan(value["plan"])
        client = RegisteredCleanupClient(context=WorkflowContext(**value["context"]), plan=plan,
            audit=audit, identity=ServiceIdentity(**value["identity"]),
            clock=lambda:value["now"], monotonic=time.monotonic)
        checked = qualify_hosted(DispatchContext(**value["dispatch"]),
            bindings=QualificationWorkflowBindings(client), phase="cleanup")
        sys.stdout.buffer.write(canonical({"verified":checked.plan_digest == plan.digest,"outcome":checked.outcome}))
        return 0
    except BaseException:
        print("fixture-cleanup-observer-refused", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
