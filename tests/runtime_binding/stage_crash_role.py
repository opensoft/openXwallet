"""Test-only manager crash, with a private subreaper to leave no orphan/zombie."""
import ctypes,json,os,select,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))


def manager(path):
    from workload_factory_binding.evidence import digest,canonical
    from workload_factory_binding_runtime.bootstrap import DispatchContext
    from workload_factory_binding_runtime.github_bootstrap.common import Decision
    from workload_factory_binding_runtime.hosted.plan import validate_plan
    from workload_factory_binding_runtime.hosted.readback import ObservationClient,ReadScope
    from workload_factory_binding_runtime.hosted.private_http import PrivateHttps
    from workload_factory_binding_runtime.hosted.staging import StageAuthority,StagePolicy
    from workload_factory_binding_runtime.hosted.stage_store import StageStore
    from workload_factory_binding_runtime.hosted.host_agent import WorkerSpec,HostAgent
    v=json.loads(path.read_bytes());now=v["now"]
    def client(value):
        transport=PrivateHttps(**value["transport"])
        return ObservationClient(origin=value["origin"],principal_ref=value["principal_ref"],scope=ReadScope(**value["scope"]),transport=transport)
    authority=StageAuthority(grant=client(v["grant"]),lease=client(v["lease"]),grant_ref=v["grant_ref"])
    policy=v["policy"];policy["reviewer_ids"]=tuple(policy["reviewer_ids"])
    worker=WorkerSpec(plan=validate_plan(canonical(v["plan"]),approved_digest=digest(v["plan"]),now=now),
        context=DispatchContext(**v["context"]),policy=StagePolicy(**policy),roots=v["roots"],
        runtime_roots=tuple(map(Path,v["runtime"])),gid=v["gid"],private_files=v["private"])
    store=StageStore(v["directory"],identity=tuple(v["identity"]),kind="host")
    agent=HostAgent(worker=worker,store=store,authority=authority)
    use=lambda:Decision(clock=lambda:now)
    ref=worker.scope()["launch_ref"];unit=agent.register(ref,decision=use())["unit"]
    print(json.dumps(unit),flush=True)
    assert sys.stdin.readline()=="start\n"
    original=store.transition
    def crash(ref,old,new,**kwargs):
        if new=="running":
            if v.get("persist_generation", False):
                original(ref,old,new,**kwargs)
            generation=kwargs["generation"]
            fd=os.open(v["receipt"],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            try:os.write(fd,canonical(generation));os.fsync(fd)
            finally:os.close(fd)
            # Existing scenario crashes before persistence; the lifecycle
            # scenario also qualifies actual manager death after persistence.
            os._exit(73)
        return original(ref,old,new,**kwargs)
    store.transition=crash
    try:agent.start(ref,digest(unit),decision=use())
    finally:agent.close()
    raise AssertionError("crash injection did not run")


def supervisor(path):
    assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
    p=subprocess.Popen([sys.executable,"-I","-B",__file__,"manager",str(path)],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,close_fds=True)
    pid=None
    try:
        assert select.select([p.stdout],[],[],8)[0]
        line=p.stdout.readline();assert line;print(line,end="",flush=True)
        assert sys.stdin.readline()=="start\n";p.stdin.write("start\n");p.stdin.flush()
        code=p.wait(timeout=12);v=json.loads(path.read_bytes());g=json.loads(Path(v["receipt"]).read_bytes());pid=g["pid"]
        limit=time.monotonic()+5;result=None
        while time.monotonic()<limit:
            actual,status=os.waitpid(pid,os.WNOHANG)
            if actual==pid:result=status;break
            time.sleep(.01)
        assert result is not None,"worker survived manager death"
        print(json.dumps({"manager_exit":code,"worker_pid":pid,"start_time":g["start_time"],
            "worker_reaped":True,"worker_signal":os.WTERMSIG(result) if os.WIFSIGNALED(result) else None}),flush=True)
    finally:
        if p.poll() is None:p.kill()
        p.communicate(timeout=3)
        # Only this supervisor's adopted children; never other fixture processes.
        limit=time.monotonic()+3
        while time.monotonic()<limit:
            try:actual,status=os.waitpid(-1,os.WNOHANG)
            except ChildProcessError:break
            if actual==0:
                if pid is not None:
                    try:os.kill(pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                time.sleep(.01)


if __name__=="__main__":
    {"manager":manager,"supervisor":supervisor}[sys.argv[1]](Path(sys.argv[2]))
