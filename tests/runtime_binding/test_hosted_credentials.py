"""Actual per-message Linux credential checks, including inherited sockets."""
import base64
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
from threading import Thread
import time
from types import SimpleNamespace
import pytest
from .hosted_fixture import child_generations
from workload_factory_binding.evidence import BindingError,canonical
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.credential import KernelPrincipal,CredentialBroker,credential_channels

OPS=("imds","resolver","sign","control","policy")


def d():return Decision(clock=lambda:int(time.time()))


def broker(principals):
    return CredentialBroker(principals=tuple(principals),capabilities={op:(("issuer","controller"),lambda **_:b"fixture-private-capability") for op in OPS})


def parent_call(operation):
    server,client=credential_channels();service=broker([KernelPrincipal.current("issuer")])
    thread=Thread(target=lambda:service.serve_once(server,decision=d()));thread.start()
    try:
        client.send(canonical({"role":"issuer","operation":operation}));client.settimeout(3)
        response=json.loads(client.recv(65537));assert response["status"]=="ok"
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
    with pytest.raises(AssertionError,match="worker capability denial was not established"):
        require_worker_denied(worker_call(operation,grant_worker=True))


def test_outage_is_not_worker_denial():
    with pytest.raises(AssertionError,match="worker capability denial was not established"):
        require_worker_denied(worker_call("resolver",outage=True))
