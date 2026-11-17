"""Selected private host manager. Reference units are real POSIX sessions.

No systemd/cgroup deployment is claimed. The retained unit precedes start and
PDEATHSIG+no-fork confinement fences an unpersisted child if its manager dies.
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Event,Thread,Lock
import json,os,select,signal,struct,subprocess,sys,time,uuid
from pathlib import Path
from types import MappingProxyType
from workload_factory_binding.evidence import BindingError,canonical,byte_digest,digest,require
from ..launch import ProcessLaunch,_regular,worker_configuration
from .plan import StaticPlan
from .stage_store import StageStore,ERROR
from .staging import StagePolicy,StageAuthority,scope_of

KIND="reference-posix-session-v1"


def await_ready(stream,decision):
    """Bound the entire readiness frame; readable is not a complete line."""
    fd=stream.fileno();blocking=os.get_blocking(fd);os.set_blocking(fd,False)
    end=time.monotonic()+min(2,decision.remaining());value=b"";expected=b"ready\n"
    try:
        while value!=expected:
            remaining=min(end-time.monotonic(),decision.remaining())
            require(remaining>0 and select.select([fd],[],[],remaining)[0],ERROR)
            try:chunk=os.read(fd,len(expected)-len(value))
            except BlockingIOError:continue
            require(chunk,ERROR);value+=chunk;require(expected.startswith(value),ERROR)
        decision.now()
    finally:os.set_blocking(fd,blocking)


def loader_for(executable):
    with Path(executable).open("rb") as stream:
        header=stream.read(64);require(header[:6]==b"\x7fELF\x02\x01",ERROR)
        offset=struct.unpack_from("<Q",header,32)[0];size,count=struct.unpack_from("<HH",header,54)
        require(size==56 and 0<count<=128 and offset<=1048576,ERROR)
        for index in range(count):
            stream.seek(offset+index*size);row=struct.unpack("<IIQQQQQQ",stream.read(size))
            if row[0]==3:
                require(0<row[5]<=4096,ERROR);stream.seek(row[2]);raw=stream.read(row[5])
                require(raw.endswith(b"\0"),ERROR);return Path(os.fsdecode(raw[:-1])).resolve(strict=True)
    raise BindingError(ERROR)


def resolve(roots,spec):
    path=roots[spec["root_ref"]]/spec["path"]
    require(path.resolve()==path and path.is_relative_to(roots[spec["root_ref"]]),ERROR);return path


def relative(roots,path):
    for ref,root in sorted(roots.items(),key=lambda item:len(str(item[1])),reverse=True):
        if path.is_relative_to(root) and path!=root:return {"root_ref":ref,"path":path.relative_to(root).as_posix()}
    raise BindingError(ERROR)


def hosting_selection(measurement,roots,runtime_roots,gid):
    exe=resolve(roots,measurement["executable"]);loader=loader_for(exe)
    require(type(gid) is int and gid>0 and type(runtime_roots) is tuple and 1<=len(runtime_roots)<=4,ERROR)
    return {"uid":measurement["uid"],"manager_kind":KIND,"sandbox_profile":"linux-x86_64-landlock3-seccomp-v1","gid":gid,
            "runtime_roots":[relative(roots,p) for p in runtime_roots],
            "loader":{**relative(roots,loader),"digest":_regular(loader,16777216,hash_only=True)}}


class WorkerSpec:
    def __init__(self,*,plan,context,policy,roots,runtime_roots,gid,private_files):
        require(type(plan) is StaticPlan and type(policy) is StagePolicy,ERROR)
        self.plan,self.context,self.policy=plan,context,policy
        self.roots=MappingProxyType({k:Path(v).resolve(strict=True) for k,v in roots.items()})
        self.runtime=tuple(Path(p).resolve(strict=True) for p in runtime_roots);self.gid=gid
        self.private=tuple(Path(p).absolute() for p in private_files)
        self.binding=canonical({k:str(v) for k,v in self.roots.items()})
        value=plan.value();self.m=value["measurement_plan"];self.scope_raw=canonical(scope_of(plan,context,policy))
        self.selection=canonical(hosting_selection(self.m,self.roots,self.runtime,gid))
        require(digest(json.loads(self.selection))==value["hosting_selection_digest"],ERROR)
        self.paths={k:resolve(self.roots,self.m[k]) for k in ("executable","worker","configuration","cwd")}
        self.artifacts={k:resolve(self.roots,v) for k,v in self.m["artifacts"].items()}
        self.loader=loader_for(self.paths["executable"])
        self.files=tuple(dict.fromkeys([self.paths["executable"],self.loader,self.paths["worker"],self.paths["configuration"],*self.artifacts.values()]))
        require(all(p.is_dir() and not p.stat().st_mode&0o022 for p in self.runtime),ERROR)
        self.projection=worker_configuration({**value["configuration_template"],"launch":{
            **value["configuration_template"]["launch"],"run_id":context.run_id,"run_attempt":context.run_attempt}},value["policy_template"])
        self.config_raw=canonical(self.projection)
        self._protect_private()
        self.parts_binding=canonical({"measurement":self.m,"paths":{k:str(v) for k,v in self.paths.items()},
            "artifacts":{k:str(v) for k,v in self.artifacts.items()},"files":[str(x) for x in self.files]})

    def scope(self):return json.loads(self.scope_raw)

    def _protect_private(self,extra=()):
        for private in (*self.private,*map(Path,extra)):
            require(not any(private==p or (private.exists() and p.exists() and os.path.samefile(private,p)) for p in self.files)
                    and not any(private.is_relative_to(root) for root in self.runtime),ERROR)

    def check(self,decision,*,configuration=True):
        require(self.parts_binding==canonical({"measurement":self.m,"paths":{k:str(v) for k,v in self.paths.items()},
            "artifacts":{k:str(v) for k,v in self.artifacts.items()},"files":[str(x) for x in self.files]})
            and self.m==self.plan.value()["measurement_plan"],ERROR)
        require(self.binding==canonical({k:str(v) for k,v in self.roots.items()})
                and self.selection==canonical(hosting_selection(self.m,self.roots,self.runtime,self.gid)),ERROR)
        self._protect_private()
        for name,path in self.artifacts.items():
            require(_regular(path,1048576,hash_only=True,clock=decision.now,deadline=decision.deadline)==self.m["artifacts"][name]["digest"],ERROR)
        require(_regular(self.paths["executable"],134217728,hash_only=True,clock=decision.now,deadline=decision.deadline)==self.m["executable_digest"],ERROR)
        if configuration:require(_regular(self.paths["configuration"],65536,clock=decision.now,deadline=decision.deadline)==self.config_raw,ERROR)
        decision.now()

    def publish(self,decision):
        self.check(decision,configuration=False);path=self.paths["configuration"]
        require(path.parent.resolve()==path.parent,ERROR)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
        try:
            with os.fdopen(fd,"wb",closefd=False) as stream:stream.write(self.config_raw);stream.flush();os.fsync(fd)
        finally:os.close(fd)
        directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
        self.check(decision)

    def message(self):
        return {"files":[str(x) for x in self.files],"directories":[str(x) for x in self.runtime],
            "execute":[str(self.paths["executable"]),str(self.loader)],
            "argv":[str(self.paths["executable"]),"-I","-B",str(self.paths["worker"]),str(self.paths["configuration"])],
            "uid":self.m["uid"],"gid":self.gid,"parent_pid":os.getpid()}

    def observe(self,pid,start,unit,decision):
        self.check(decision)
        process=ProcessLaunch(pid,start,self.paths["executable"],self.m["executable_digest"],self.paths["worker"],
            self.paths["configuration"],self.paths["cwd"],self.artifacts)
        # Actual source/projection/argv/cwd/PID/start checks, never worker READY data.
        value=self.plan.value();c=value["configuration_template"];c["launch"].update(run_id=self.context.run_id,run_attempt=self.context.run_attempt)
        process.measure(self.projection,c,clock=decision.now,deadline=decision.deadline)
        status={key: value for key, _separator, value in (line.partition(":") for line in (Path("/proc")/str(pid)/"status").read_text().splitlines() if ":" in line)}
        require([int(x) for x in status["Uid"].split()]==[self.m["uid"]]*4 and status["NoNewPrivs"].strip()=="1"
                and [int(x) for x in status["Gid"].split()]==[self.gid]*4
                and set(map(int,status["Groups"].split()))<={self.gid} and int(status["Seccomp"].strip())==2 and all(int(status[x].strip(),16)==0 for x in ("CapInh","CapPrm","CapEff","CapAmb"))
                and int(status["PPid"].strip())==os.getpid() and os.getsid(pid)==pid,ERROR)
        require(Path("/proc/sys/kernel/random/boot_id").read_text().strip()==self.scope()["boot_id"],ERROR)
        return {"unit_digest":digest(unit),"pid":pid,"start_time":start,"session_id":os.getsid(pid),
                "boot_id":self.scope()["boot_id"],"uid":self.m["uid"],"policy_digest":digest(json.loads(self.selection)),
                "cgroup_digest":byte_digest((Path("/proc")/str(pid)/"cgroup").read_bytes())}


class HostAgent:
    def __init__(self,*,worker,store,authority):
        require(type(worker) is WorkerSpec and type(store) is StageStore and store.kind=="host"
                and type(authority) is StageAuthority,ERROR)
        self.worker,self.store,self.authority=worker,store,authority;self.children={}
        # Linux PDEATHSIG follows the creating thread, not merely its process.
        # Keep one owner thread alive across short-lived HTTP request threads.
        self.launch_owner=ThreadPoolExecutor(max_workers=1,thread_name_prefix="stage-launch-owner")
        namespace=Path("/proc/self/ns/pid").stat()
        self.pid_namespace=(namespace.st_dev,namespace.st_ino)
        self.children_lock=Lock();self.reap_stop=Event()
        self.reaper=Thread(target=self._reap,daemon=True,name="stage-owned-child-reaper")
        self.reaper.start()

    def _reap(self):
        while not self.reap_stop.wait(.02):
            with self.children_lock:children=tuple(self.children.values())
            for child in children:child.poll()

    def current(self,decision,unit=None):
        scope=self.worker.scope();grant=self.authority.launch_grant(scope,decision=decision);ack=None
        if unit is not None:
            ack=self.authority.acknowledged(scope,unit,decision=decision)
            stored=self.store.read(scope["launch_ref"],decision=decision)
            require(stored["lease"] is None or canonical(stored["lease"])==canonical(ack),ERROR)
        decision.clip(self.worker.plan.valid_until);return scope,grant,ack

    def register(self,ref,*,decision):
        scope,grant,_=self.current(decision);require(ref==scope["launch_ref"],ERROR)
        require(self.store.reserve(ref,scope,decision=decision,expires_at=grant["expires_at"]),ERROR)
        unit={"manager_kind":KIND,"unit_ref":"unit:"+digest(scope).split(":")[1],
              "invocation_ref":"invocation:"+str(uuid.uuid4()),"scope_digest":digest(scope),
              "host_ref":scope["host_ref"],"incarnation_ref":scope["incarnation_ref"],"boot_id":scope["boot_id"],
              "manager_pid":os.getpid(),"manager_start":int(Path("/proc/self/stat").read_text().rsplit(")",1)[1].split()[19])}
        self.store.transition(ref,"reserved","registered",decision=decision,unit=unit)
        self.worker.publish(decision);self.current(decision)
        return self.status(ref,decision=decision,lease=False)

    def start(self,ref,unit_digest,*,decision):
        scope,_,_=self.current(decision);row=self.store.read(ref,decision=decision);unit=row["unit"]
        decision.clip(row["deadline"])
        require(canonical(row["scope"])==canonical(scope) and unit is not None and digest(unit)==unit_digest,ERROR)
        require(self._unit_current(unit),ERROR)
        self.store.transition(ref,"registered","start-consumed",decision=decision)
        _,_,ack=self.current(decision,unit);self.store.bind_lease(ref,ack,decision=decision);self.worker.check(decision)
        # Irreversible start fence is durable even if later I/O/measurement fails.
        self.current(decision,unit);self.worker.check(decision);process=None
        try:
            def spawn():
                child=subprocess.Popen([str(self.worker.paths["executable"]),"-I","-B",str(Path(__file__).with_name("_launch_exec.py"))],
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True,
                    cwd=self.worker.paths["cwd"],env={"PATH":os.defpath,"LANG":"C.UTF-8"})
                with self.children_lock:self.children[ref]=child
                return child
            process=self.launch_owner.submit(spawn).result(timeout=decision.remaining())
            # Creating the trusted helper may block: no worker instructions cross
            # its pipe until original authority/source are current again.
            self.current(decision,unit);self.worker.check(decision)
            process.stdin.write(canonical(self.worker.message())+b"\n");process.stdin.flush()
            await_ready(process.stdout,decision)
            captured=ProcessLaunch.capture(process,executable=self.worker.paths["executable"],executable_digest=self.worker.m["executable_digest"],
                worker=self.worker.paths["worker"],configuration_file=self.worker.paths["configuration"],cwd=self.worker.paths["cwd"],artifacts=self.worker.artifacts)
            generation=self.worker.observe(captured.pid,captured.start_time,unit,decision)
            self.current(decision,unit);self.store.transition(ref,"start-consumed","running",decision=decision,generation=generation)
            return self.status(ref,decision=decision)
        except BaseException:
            # No resubmission, even if the child started but the response was lost.
            if process is not None and process.poll() is not None:process.communicate()
            raise

    def _unit_current(self,unit):
        return unit["manager_pid"]==os.getpid() and unit["manager_start"]==int(Path("/proc/self/stat").read_text().rsplit(")",1)[1].split()[19])

    def status(self,ref,*,decision,lease=True):
        scope,_,_=self.current(decision);row=self.store.read(ref,decision=decision)
        decision.clip(row["deadline"])
        require(ref==scope["launch_ref"] and canonical(row["scope"])==canonical(scope),ERROR)
        if row["unit"] is not None and not self._unit_current(row["unit"]):
            return {"scope_digest":digest(scope),"state":"indeterminate","unit":row["unit"],"generation":None}
        if row["unit"] is not None and lease and row["lease"] is not None:self.current(decision,row["unit"])
        if row["state"]=="running":
            unit, generation = row["unit"], row["generation"]
            if unit is None or generation is None or row["lease"] is None:
                raise BindingError(ERROR)
            require(self.worker.observe(generation["pid"],generation["start_time"],unit,decision)==generation,ERROR)
        decision.now();return {"scope_digest":digest(scope),"state":row["state"],"unit":row["unit"],"generation":row["generation"]}

    def close(self):
        self.launch_owner.shutdown(wait=True,cancel_futures=True)
        self.reap_stop.set();self.reaper.join(timeout=2)
        require(not self.reaper.is_alive(),ERROR)
        for process in self.children.values():
            if process.poll() is None:process.terminate()
            try:process.communicate(timeout=3)
            except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=3)
