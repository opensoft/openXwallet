"""Kernel per-message capability authentication, including inherited descriptors.

This port establishes the actual sender UID/PID/generation, not deployed filesystem,
IMDS firewall or hostile same-UID isolation. Those remain hosting qualification.
"""
import base64
from dataclasses import dataclass
import os
from pathlib import Path
import selectors
import socket
import struct
from types import MappingProxyType
from workload_factory_binding.evidence import BindingError,canonical,integer,require
from ..config import _handle
from ..github_bootstrap.common import document
from .nonces import ERROR


def credential_channels():
    server,client=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
    server.setsockopt(socket.SOL_SOCKET,socket.SO_PASSCRED,1)
    return server,client


def observed(pid,uid):
    require(integer(pid) and pid>0 and integer(uid) and uid>0,ERROR)
    root=Path("/proc")/str(pid)
    before=(root/"stat").read_text().rsplit(")",1)[1].split()
    fields={k:v for line in (root/"status").read_text().splitlines() if ":" in line for k,v in [line.split(":",1)]}
    after=(root/"stat").read_text().rsplit(")",1)[1].split()
    require(before[19]==after[19] and after[0] not in ("Z","X")
        and [int(v) for v in fields["Uid"].split()]==[uid]*4
        and all(int(fields[k].strip(),16)==0 for k in ("CapInh","CapPrm","CapEff","CapAmb")),ERROR)
    return int(after[19]),int(fields["Gid"].split()[0])


@dataclass(frozen=True,repr=False)
class KernelPrincipal:
    uid:int
    pid:int
    start_time:int
    role:str

    @classmethod
    def current(cls,role):
        try:
            _handle("role:"+role);start,_=observed(os.getpid(),os.getuid())
            return cls(os.getuid(),os.getpid(),start,role)
        except Exception:raise BindingError(ERROR) from None


class _Denied(Exception):pass


class CredentialBroker:
    def __init__(self,*,principals,capabilities):
        require(type(principals) is tuple and 0<len(principals)<=16 and type(capabilities) is dict and 0<len(capabilities)<=16,ERROR)
        for p in principals:
            require(type(p) is KernelPrincipal and p.role in ("issuer","controller")
                and integer(p.uid) and p.uid>0 and integer(p.pid) and p.pid>0 and integer(p.start_time) and p.start_time>0,ERROR)
        require(len({(p.uid,p.pid,p.start_time) for p in principals})==len(principals),ERROR)
        for name,value in capabilities.items():
            _handle("operation:"+name)
            require(type(value) is tuple and len(value)==2 and type(value[0]) is tuple
                and value[0] and set(value[0])<={"issuer","controller"} and callable(value[1]),ERROR)
        self.principals=principals;self.capabilities=MappingProxyType(dict(capabilities))

    def serve_once(self,channel,*,decision):
        response={"status":"unavailable"};reply=None
        try:
            try:
                raw,peer,reply=receive_request(channel,decision)
                pid,uid,gid=peer;start,actual_gid=observed(pid,uid);require(gid==actual_gid,ERROR)
                selected=next((p for p in self.principals if (p.uid,p.pid,p.start_time)==(uid,pid,start)),None)
                if selected is None:raise _Denied
                value=document(raw,65536)
                if (type(value) is not dict or set(value)!={"role","operation"} or value["role"]!=selected.role
                        or type(value["operation"]) is not str or value["operation"] not in self.capabilities):raise _Denied
                roles,operation=self.capabilities[value["operation"]]
                if selected.role not in roles:raise _Denied
                decision.now();result=operation(deadline=decision.deadline);decision.now()
                require(type(result) is bytes and 0<len(result)<=8192 and observed(pid,uid)==(start,gid),ERROR)
                response={"status":"ok","value":base64.b64encode(result).decode()}
            except _Denied:response={"status":"denied"}
            except Exception:pass  # An outage/expiry/malformed channel is not an authenticated denial.
            if reply is not None:
                try:
                    reply.settimeout(min(1,max(.001,decision.remaining())))
                    reply.send(canonical(response))
                except Exception:pass
        finally:
            if reply is not None:reply.close()


def receive_request(channel,decision):
    """Consume exactly one private reply capability; close every received FD on error."""
    descriptors=[];reply=None
    try:
        require(type(channel) is socket.socket and channel.family==socket.AF_UNIX
            and channel.getsockopt(socket.SOL_SOCKET,socket.SO_TYPE)==socket.SOCK_SEQPACKET
            and channel.getsockopt(socket.SOL_SOCKET,socket.SO_PASSCRED)==1,ERROR)
        with selectors.DefaultSelector() as selector:
            selector.register(channel,selectors.EVENT_READ);require(bool(selector.select(decision.remaining())),ERROR)
        raw,ancillary,flags,_=channel.recvmsg(65537,socket.CMSG_SPACE(struct.calcsize("3i"))+socket.CMSG_SPACE(16*struct.calcsize("i")),socket.MSG_CMSG_CLOEXEC)
        credentials=[]
        for level,kind,data in ancillary:
            if level==socket.SOL_SOCKET and kind==socket.SCM_RIGHTS:
                require(len(data)%struct.calcsize("i")==0,ERROR)
                descriptors.extend(struct.unpack("i"*(len(data)//struct.calcsize("i")),data))
            elif level==socket.SOL_SOCKET and kind==socket.SCM_CREDENTIALS:credentials.append(data)
        decision.now();require(0<len(raw)<=65536 and not flags&(socket.MSG_TRUNC|socket.MSG_CTRUNC)
            and len(ancillary)==2 and len(credentials)==1 and len(credentials[0])==struct.calcsize("3i")
            and len(descriptors)==1,ERROR)
        reply=socket.socket(fileno=descriptors[0]);descriptors.clear()
        require(reply.family==socket.AF_UNIX and reply.getsockopt(socket.SOL_SOCKET,socket.SO_TYPE)==socket.SOCK_SEQPACKET,ERROR)
        reply.getpeername()  # Unconnected/listener descriptors are not reply capabilities.
        result=(raw,struct.unpack("3i",credentials[0]),reply);reply=None;return result
    finally:
        if reply is not None:reply.close()
        for descriptor in descriptors:os.close(descriptor)


def credential_request(channel,raw,*,decision):
    """Create the private reply pair in this caller, after untrusted inheritance.

    Never inherit/share the receive endpoint with a worker. The request endpoint
    carries requests only and never receives credential replies.
    """
    reader,writer=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
    try:
        channel.settimeout(min(3,decision.remaining()))
        channel.sendmsg([raw],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,struct.pack("i",writer.fileno()))])
        writer.close();reader.settimeout(min(3,decision.remaining()))
        result=reader.recv(65537);decision.now();return result
    finally:reader.close();writer.close()
