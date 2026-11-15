"""Child-only Linux x86-64 Landlock + seccomp restrictions. No host policy changes.

Filesystem read rules select exact artifacts/config/runtime roots; no write right
is granted. Seccomp reduces kernel/network/control surface; this is not a claim
of hostile-root security or generic model-behavior attestation.
"""
import ctypes
import errno
import os
from pathlib import Path
import platform
import stat

# Linux v6.6 arch/x86/entry/syscalls/syscall_64.tbl; reject x32/foreign ABIs.
DENIED=(56,57,58,109,112,435,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,62,90,91,92,93,94,101,132,
        155,165,166,188,189,190,197,198,199,200,234,235,248,249,250,260,261,268,272,
        280,288,298,299,304,307,308,310,311,321,424,425,426,427,428,429,430,431,432,438,442,452)


def require(ok):
    if not ok:raise RuntimeError("worker-sandbox-refused")


class Rule(ctypes.Structure):
    _fields_=[("fs",ctypes.c_uint64)]


class PathRule(ctypes.Structure):
    _pack_=1
    _fields_=[("access",ctypes.c_uint64),("parent",ctypes.c_int32)]


class Filter(ctypes.Structure):
    _fields_=[("code",ctypes.c_ushort),("jt",ctypes.c_ubyte),("jf",ctypes.c_ubyte),("k",ctypes.c_uint32)]


class Program(ctypes.Structure):
    _fields_=[("length",ctypes.c_ushort),("filters",ctypes.POINTER(Filter))]


def install(*,files,directories,execute):
    require(platform.machine()=="x86_64" and type(files) is list and type(directories) is list
            and type(execute) is list and 1<=len(files)<=64 and 1<=len(directories)<=8 and 1<=len(execute)<=4)
    require(len(set(files))==len(files) and set(execute)<=set(files))
    libc=ctypes.CDLL(None,use_errno=True);libc.syscall.restype=ctypes.c_long
    require(libc.prctl(38,1,0,0,0)==0)
    require(libc.syscall(444,ctypes.c_void_p(),0,1)>=3)
    ruleset=libc.syscall(444,ctypes.byref(Rule((1<<15)-1)),ctypes.sizeof(Rule),0)
    require(ruleset>=0)
    try:
        for value,is_directory in [(p,False) for p in files]+[(p,True) for p in directories]:
            path=Path(value);require(path.is_absolute() and path.resolve()==path)
            fd=os.open(path,os.O_PATH|os.O_CLOEXEC|os.O_NOFOLLOW)
            try:
                info=os.fstat(fd);require(stat.S_ISDIR(info.st_mode) if is_directory else stat.S_ISREG(info.st_mode))
                rights=12 if is_directory else (5 if value in execute else 4)
                require(libc.syscall(445,ruleset,1,ctypes.byref(PathRule(rights,fd)),0)==0)
            finally:os.close(fd)
        require(libc.syscall(446,ruleset,0)==0)
    finally:os.close(ruleset)
    instructions=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(0x06,0,0,0x80000000),
                  (0x20,0,0,0),(0x35,0,1,0x40000000),(0x06,0,0,0x80000000)]
    # Keep PDEATHSIG immutable after installation; read-only prctl queries remain.
    instructions.extend(((0x15,0,4,157),(0x20,0,0,16),(0x15,0,1,1),
                         (0x06,0,0,0x50000|errno.EPERM),(0x20,0,0,0)))
    for number in DENIED:instructions.extend(((0x15,0,1,number),(0x06,0,0,0x50000|errno.EPERM)))
    instructions.append((0x06,0,0,0x7fff0000))
    array=(Filter*len(instructions))(*(Filter(*row) for row in instructions));program=Program(len(array),array)
    require(libc.prctl(22,2,ctypes.byref(program))==0)
