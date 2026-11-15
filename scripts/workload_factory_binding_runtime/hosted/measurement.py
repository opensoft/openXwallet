"""Actual Linux generation measurement, with preapproved root-relative paths.

Roots and observer capabilities are protected hosting construction, never wire
inputs. No process is started, signed or stopped here. Host identity/manager data
still require independently authenticated deployed guest/provider qualification.
"""
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from workload_factory_binding.evidence import canonical, digest, integer, require
from ..launch import ProcessLaunch, _regular, worker_configuration
from . import ERROR


@dataclass(frozen=True, repr=False)
class LaunchObservation:
    principal_ref: str
    launch_ref: str
    host_ref: str
    incarnation_ref: str
    boot_id: str
    invocation_ref: str
    process: ProcessLaunch
    observed_at: int
    expires_at: int


@dataclass(frozen=True, repr=False)
class MeasurementBindings:
    principal_ref: str
    roots: object
    observe: object

    def __post_init__(self):
        require(type(self.roots) in (dict, MappingProxyType) and 0 < len(self.roots) <= 16, ERROR)
        object.__setattr__(self, "roots", MappingProxyType({k: Path(v).resolve(strict=True) for k, v in self.roots.items()}))


def _resolve(bindings, spec):
    root = bindings.roots[spec["root_ref"]]
    path = root / spec["path"]
    require(path.resolve(strict=True) == path and path.is_relative_to(root), ERROR)
    return path


def measure(plan, context, bindings, observation, *, decision):
    from ..config import _configuration
    require(type(bindings) is MeasurementBindings and type(observation) is LaunchObservation
            and observation.principal_ref == bindings.principal_ref
            and type(observation.process) is ProcessLaunch, ERROR)
    value = plan.value()
    config, policy, m, s = (value[k] for k in
        ("configuration_template", "policy_template", "measurement_plan", "staging_policy"))
    for k in ("launch_ref", "host_ref", "incarnation_ref", "boot_id"):
        require(getattr(observation, k) == s[k], ERROR)
    require(Path("/proc/sys/kernel/random/boot_id").read_text().strip() == observation.boot_id, ERROR)
    process = observation.process
    status = Path("/proc") / str(process.pid) / "status"
    fields = {key: value for line in status.read_text().splitlines()
              if ":" in line for key, value in [line.split(":", 1)]}
    require([int(n) for n in fields["Uid"].split()] == [m["uid"]] * 4
            and all(int(fields[k].strip(), 16) == 0 for k in ("CapInh", "CapPrm", "CapEff", "CapAmb")), ERROR)
    for attr, field in (("executable", "executable"), ("worker", "worker"),
                        ("configuration_file", "configuration"), ("cwd", "cwd")):
        require(getattr(process, attr) == _resolve(bindings, m[field]), ERROR)
    expected_paths = {name: _resolve(bindings, item) for name, item in m["artifacts"].items()}
    require(dict(process.artifacts) == expected_paths and process.executable_digest == m["executable_digest"], ERROR)
    for name, path in expected_paths.items():
        require(_regular(path, 1024 * 1024, hash_only=True, clock=decision.now, deadline=decision.deadline)
                == m["artifacts"][name]["digest"], ERROR)
    config["launch"].update(run_id=context.run_id, run_attempt=context.run_attempt)
    projection = worker_configuration(config, policy)
    composition = process.measure(projection, config, deadline=decision.deadline, clock=decision.now)
    policy["composition_digest"] = composition
    config["composition_digest"] = composition
    config["authority"]["policy_digest"] = digest(policy)
    _configuration(config)
    from workload_factory_binding.gate import _policy
    _policy(policy, decision.now())
    # Bound complete runtime bytes to the unchanged full-runtime size contract.
    config_raw, policy_raw = canonical(config), canonical(policy)
    require(len(config_raw) <= 16384 and len(policy_raw) <= 16384, ERROR)
    generation = {k: getattr(observation, k) for k in
                  ("launch_ref", "host_ref", "incarnation_ref", "boot_id", "invocation_ref")}
    generation.update(pid=process.pid, start_time=process.start_time)
    decision.now()
    return config_raw, policy_raw, generation
