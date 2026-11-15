"""Actual per-message Linux credential checks, including inherited sockets."""
import base64
import asyncio
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import struct
import sys
from threading import Thread
import time
from types import SimpleNamespace
import pytest
from .hosted_fixture import child_generations
from workload_factory_binding.evidence import BindingError,canonical
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.credential import KernelPrincipal,CredentialBroker,credential_channels,credential_request

OPS=("imds","resolver","sign","control","policy")


def d():return Decision(clock=lambda:int(time.time()))


def broker(principals):
    return CredentialBroker(principals=tuple(principals),capabilities={op:(("issuer","controller"),lambda **_:b"fixture-private-capability") for op in OPS})


def parent_call(operation):
    server,client=credential_channels();service=broker([KernelPrincipal.current("issuer")])
    thread=Thread(target=lambda:service.serve_once(server,decision=d()));thread.start()
    try:
        response=json.loads(credential_request(client,canonical({"role":"issuer","operation":operation}),decision=d()));assert response["status"]=="ok"
        assert base64.b64decode(response["value"])==b"fixture-private-capability"
    finally:
        server.close();client.close();thread.join(timeout=5);assert not thread.is_alive()


def worker_call(operation,*,grant_worker=False,outage=False):
    server,client=credential_channels();process=None;thread=None
    try:
        process=subprocess.Popen([sys.executable,"-I","-B",str(Path(__file__).with_name("credential_worker.py")),str(client.fileno())],
            pass_fds=(client.fileno(),),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            env={"PATH":os.defpath,"LANG":"C.UTF-8"})
        assert select.select([process.stdout],[],[],3)[0]
        assert process.stdout.readline()==b"ready\n"
        principals=[KernelPrincipal.current("issuer")]
        if grant_worker:
            fields=(Path("/proc")/str(process.pid)/"stat").read_text().rsplit(")",1)[1].split()
            principals.append(KernelPrincipal(os.getuid(),process.pid,int(fields[19]),"issuer"))
        service=broker(principals)
        if outage:server.close()
        else:
            thread=Thread(target=lambda:service.serve_once(server,decision=d()));thread.start()
        raw,_=process.communicate(canonical({"role":"issuer","operation":operation})+b"\n",timeout=5)
        assert process.returncode==0
        return json.loads(raw)["status"]
    finally:
        server.close();client.close()
        if process is not None:
            if process.poll() is None:process.kill()
            process.communicate()
        if thread is not None:thread.join(timeout=5);assert not thread.is_alive()


def require_worker_denied(status):
    assert status=="denied","worker capability denial was not established"


@pytest.mark.parametrize("operation",OPS)
def test_kernel_authenticated_allowed_controller_and_worker_denial(operation):
    parent_call(operation)
    require_worker_denied(worker_call(operation))


@pytest.mark.parametrize("operation",OPS)
def test_exposing_each_host_capability_breaks_denial_qualification(operation):
    parent_call(operation)
    worker_status=worker_call(operation, grant_worker=True)
    with pytest.raises(AssertionError, match='worker capability denial was not established'):
        require_worker_denied(worker_status)


def test_outage_is_not_worker_denial():
    worker_status=worker_call('resolver', outage=True)
    with pytest.raises(AssertionError, match='worker capability denial was not established'):
        require_worker_denied(worker_status)


def test_passive_inherited_request_socket_cannot_read_issuer_reply():
    server,client=credential_channels();process=None;thread=None
    try:
        process=subprocess.Popen([sys.executable,"-I","-B",str(Path(__file__).with_name("credential_worker.py")),str(client.fileno()),"passive"],
            pass_fds=(client.fileno(),),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            env={"PATH":os.defpath,"LANG":"C.UTF-8"})
        assert select.select([process.stdout],[],[],3)[0]
        assert process.stdout.readline()==b"ready\n"
        process.stdin.write(b"observe\n");process.stdin.flush()
        service=broker([KernelPrincipal.current("issuer")])
        thread=Thread(target=lambda:service.serve_once(server,decision=d()));thread.start()
        response=json.loads(credential_request(client,canonical({"role":"issuer","operation":"resolver"}),decision=d()))
        assert response["status"]=="ok"
        assert base64.b64decode(response["value"])==b"fixture-private-capability"
        raw,_=process.communicate(timeout=4)
        assert process.returncode==0
        assert json.loads(raw)["status"]=="unavailable"
        client.settimeout(.05)
        with pytest.raises(socket.timeout):client.recv(65537)
    finally:
        server.close();client.close()
        if process is not None:
            if process.poll() is None:process.kill()
            process.communicate()
        if thread is not None:thread.join(timeout=5);assert not thread.is_alive()


@pytest.mark.parametrize("kind",["missing","extra","pipe","datagram","unconnected","truncated"])
def test_malformed_reply_capability_is_closed_without_delivery(kind):
    server,client=credential_channels();owned=[];calls=[]
    try:
        if kind=="pipe":owned.extend(os.pipe())
        elif kind=="unconnected":owned.append(socket.socket(socket.AF_UNIX,socket.SOCK_SEQPACKET))
        elif kind!="missing":
            for _ in range(16 if kind=="truncated" else 1):
                owned.extend(socket.socketpair(socket.AF_UNIX,socket.SOCK_DGRAM if kind=="datagram" else socket.SOCK_SEQPACKET))
        fds=[item if type(item) is int else item.fileno() for item in owned]
        if kind in ("pipe","datagram"):fds=fds[:1]
        ancillary=[(socket.SOL_SOCKET,socket.SCM_RIGHTS,struct.pack("i"*len(fds),*fds))] if fds else []
        service=CredentialBroker(principals=(KernelPrincipal.current("issuer"),),capabilities={"resolver":(("issuer",),lambda **_:calls.append(True) or b"fixture")})
        before=len(list(Path("/proc/self/fd").iterdir()))
        client.sendmsg([canonical({"role":"issuer","operation":"resolver"})],ancillary)
        service.serve_once(server,decision=d())
        assert len(list(Path("/proc/self/fd").iterdir()))==before
        assert calls==[]
        client.settimeout(.05)
        with pytest.raises(socket.timeout):client.recv(65537)
    finally:
        server.close();client.close()
        for item in owned:
            if type(item) is int:os.close(item)
            else:item.close()


@pytest.mark.parametrize("cancellation",[KeyboardInterrupt,SystemExit,asyncio.CancelledError])
def test_cancellation_closes_private_reply_before_traceback_is_released(cancellation):
    server,client=credential_channels();reader,writer=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
    def cancelled(**_):raise cancellation()
    service=CredentialBroker(principals=(KernelPrincipal.current("issuer"),),capabilities={"resolver":(("issuer",),cancelled)})
    request=canonical({"role":"issuer","operation":"resolver"});request_decision=d()
    try:
        client.sendmsg([request],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,struct.pack("i",writer.fileno()))]);writer.close()
        before=len(list(Path("/proc/self/fd").iterdir()))
        with pytest.raises(cancellation) as caught:service.serve_once(server,decision=request_decision)
        assert caught.value.__traceback__ is not None
        assert len(list(Path("/proc/self/fd").iterdir()))==before
        reader.settimeout(.2)
        assert reader.recv(65537)==b""
    finally:server.close();client.close();reader.close();writer.close()
