"""Bounded selected credential HTTPS; callers own fixed origins and operations."""
import base64
from dataclasses import dataclass
import os
from pathlib import Path
import selectors
import subprocess
import sys
from urllib.parse import urlsplit
from workload_factory_binding.evidence import BindingError,byte_digest,canonical,require
from ..custody import _read
from ..github_bootstrap.common import document
from .nonces import ERROR

@dataclass(frozen=True,repr=False)
class Response:
    status:int
    body:bytes

class PrivateHttps:
    def __init__(self,*,ca_file=None,certificate=None,private_key=None):
        require((certificate is None)==(private_key is None),ERROR)
        self.ca,self.cert,self.key=ca_file,certificate,private_key

    def materials(self):
        return tuple(byte_digest(_read(p,private=i==2)) if p is not None else None
                     for i,p in enumerate((self.ca,self.cert,self.key)))

    def exchange(self,method,url,*,headers,body=b"",decision,before_send=lambda:None):
        process=None
        try:
            u=urlsplit(url)
            require(method in ("GET","POST","DELETE") and u.scheme=="https" and u.hostname
                and u.username is None and u.password is None and not u.fragment and u.path.startswith("/")
                and len(url)<=4096 and all(32<ord(c)<127 for c in url)
                and type(body) is bytes and len(body)<=65536 and type(headers) is dict and len(headers)<=12
                and all(type(x) is str and 0<len(x)<=16384 and all(32<=ord(c)<127 for c in x)
                        for pair in headers.items() for x in pair),ERROR)
            materials=self.materials();decision.now();remaining=decision.remaining();require(remaining>0,ERROR)
            process=subprocess.Popen([sys.executable,"-I","-B",str(Path(__file__).with_name("_credential_io.py"))],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                env={"PATH":os.defpath,"LANG":"C.UTF-8"})
            message={"method":method,"url":url,"headers":headers,"body":base64.b64encode(body).decode(),
                "seconds":remaining,"ca":self.ca,"certificate":self.cert,"key":self.key}
            process.stdin.write(canonical(message)+b"\n");process.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout,selectors.EVENT_READ)
                require(bool(selector.select(min(5,decision.remaining()))),ERROR)
            require(process.stdout.readline(64)==b"READY\n",ERROR)
            before_send();decision.now();require(self.materials()==materials,ERROR)
            raw,_=process.communicate(b"GO\n",timeout=max(.001,decision.remaining()))
            decision.now();require(process.returncode==0 and len(raw)<=1500000 and self.materials()==materials,ERROR)
            result=document(raw,1500000)
            require(type(result) is dict and set(result)=={"status","body"}
                and type(result["status"]) is int and 100<=result["status"]<=599,ERROR)
            payload=base64.b64decode(result["body"],validate=True);require(len(payload)<=1048576,ERROR)
            return Response(result["status"],payload)
        except Exception:raise BindingError(ERROR) from None
        finally:
            if process is not None:
                if process.poll() is None:process.kill()
                process.communicate()
