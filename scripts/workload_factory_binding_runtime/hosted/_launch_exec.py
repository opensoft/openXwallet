"""Private one-shot launcher; source/config refs cross an anonymous pipe."""
import ctypes
import json
import os
from pathlib import Path
import signal
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from worker_sandbox import install,require


def main():
    try:
        value=json.loads(sys.stdin.buffer.readline(65537))
        require(type(value) is dict and set(value)==set("files directories execute argv uid gid parent_pid".split()))
        argv=value["argv"];require(type(argv) is list and len(argv)==5 and argv[1:3]==["-I","-B"]
            and all(type(x) is str and 0<len(x)<=4096 for x in argv) and argv[0] in value["execute"])
        uid,gid=value["uid"],value["gid"];require(type(uid) is int and uid>0 and type(gid) is int and gid>0)
        if os.geteuid()==0:os.setgroups([]);os.setgid(gid);os.setuid(uid)
        require(os.geteuid()==uid and os.getegid()==gid and set(os.getgroups())<={gid})
        libc=ctypes.CDLL(None,use_errno=True)
        # UID changes clear PDEATHSIG: fence only after the final identity change.
        require(libc.prctl(1,signal.SIGKILL,0,0,0)==0 and os.getppid()==value["parent_pid"])
        class Header(ctypes.Structure):_fields_=[("version",ctypes.c_uint32),("pid",ctypes.c_int)]
        class Data(ctypes.Structure):_fields_=[("effective",ctypes.c_uint32),("permitted",ctypes.c_uint32),("inheritable",ctypes.c_uint32)]
        require(libc.capset(ctypes.byref(Header(0x20080522,0)),ctypes.byref((Data*2)()))==0)
        install(files=value["files"],directories=value["directories"],execute=value["execute"])
        os.execve(argv[0],argv,{"PATH":os.defpath,"LANG":"C.UTF-8"})
    except Exception:return 2
    return 2


if __name__=="__main__":raise SystemExit(main())
