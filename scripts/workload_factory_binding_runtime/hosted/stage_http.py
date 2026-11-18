"""Bounded explicitly constructed HTTPS admission or pinned private mTLS agent."""
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
import ssl,threading
from workload_factory_binding.evidence import byte_digest,canonical,digest,require,valid_digest
from ..github_bootstrap.common import Decision,document
from .host_agent import HostAgent
from .stage_controller import StageController
from .stage_client import PROFILE
from .stage_store import ERROR

PRIVATE={"/stage/register":"register","/stage/start":"start","/stage/status":"status"}
PUBLIC={"/v2/plan":"preflight","/v2/protected":"protected"}


class StageServer(ThreadingMixIn,HTTPServer):
    daemon_threads=False
    block_on_close=True
    request_queue_size=8
    def __init__(self,*,service,principal,cert_file,key_file,clock,monotonic,ca_file=None,permissions=None,listen=("127.0.0.1",0)):
        from ..config import _handle
        _handle(principal);require(type(service) in (HostAgent,StageController),ERROR)
        self.private=type(service) is HostAgent
        require((ca_file is not None and type(permissions) is dict) if self.private else (ca_file is None and permissions is None),ERROR)
        self.service,self.principal,self.clock,self.monotonic=service,principal,clock,monotonic
        if self.private:service.worker._protect_private((key_file,service.authority.grant.transport.key,service.authority.lease.transport.key))
        self.permissions=dict(permissions or {});require(all(valid_digest(k) and type(v) is frozenset and v<=set(PRIVATE.values()) for k,v in self.permissions.items()),ERROR);self.slots=threading.BoundedSemaphore(8)
        self.tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);self.tls.minimum_version=ssl.TLSVersion.TLSv1_2
        if self.private:self.tls.verify_mode=ssl.CERT_REQUIRED;self.tls.load_verify_locations(cafile=ca_file)
        self.tls.load_cert_chain(cert_file,key_file);super().__init__(listen,_Handler)

    def get_request(self):
        request,address=super().get_request();request.settimeout(2);return request,address
    def finish_request(self,request,address):
        with self.tls.wrap_socket(request,server_side=True) as secured:self.RequestHandlerClass(secured,address,self)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False):self.shutdown_request(request);return
        try:super().process_request(request,address)
        except Exception:self.slots.release();raise
    def process_request_thread(self,request,address):
        try:super().process_request_thread(request,address)
        finally:self.slots.release()
    def handle_error(self,request,address):
        # Private request failures intentionally produce no server log payload.
        pass


class _Handler(BaseHTTPRequestHandler):
    server_version="HostedAdmission"
    sys_version=""
    def setup(self):
        super().setup();self.timer=threading.Timer(10,self._expire);self.timer.daemon=True;self.timer.start()
    def _expire(self):
        try:self.connection.shutdown(2)
        except OSError:pass
    def finish(self):self.timer.cancel();self.timer.join(timeout=1);super().finish()
    def log_message(self,*args):
        # Private request metadata is intentionally absent from HTTP logs.
        pass
    def _reply(self,status,value):
        raw=canonical(value);self.send_response(status);self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)));self.send_header("Connection","close");self.end_headers()
        self.wfile.write(raw);self.close_connection=True
    def send_error(self,*args,**kwargs):self._reply(400,{"error":ERROR})
    def _read_body(self):
        require(sum(len(k)+len(v) for k,v in self.headers.items())<=32768
            and self.headers.get_all("Content-Type")==["application/json"] and self.headers.get("Transfer-Encoding") is None,ERROR)
        lengths=self.headers.get_all("Content-Length");require(lengths and len(lengths)==1 and lengths[0].isascii()
            and lengths[0].isdigit() and len(lengths[0])<=5 and 0<int(lengths[0])<=65536,ERROR)
        raw=self.rfile.read(int(lengths[0]));require(len(raw)==int(lengths[0]),ERROR)
        return raw

    def _private_facts(self,operation,arguments,use):
        names={"launch_ref","scope_digest"}|({"unit_digest"} if operation=="start" else set())
        require(type(arguments) is dict and set(arguments)==names and arguments["scope_digest"]==
                digest(self.server.service.worker.scope()),ERROR)
        ref=arguments["launch_ref"]
        if operation=="start":facts=self.server.service.start(ref,arguments["unit_digest"],decision=use)
        elif operation=="register":facts=self.server.service.register(ref,decision=use)
        else:
            self.server.service.store.status_read(ref,decision=use)
            facts=self.server.service.status(ref,decision=use)
        return facts

    def do_POST(self):
        try:
            use=Decision(clock=self.server.clock,monotonic=self.server.monotonic)
            routes=PRIVATE if self.server.private else PUBLIC;require(self.path in routes,ERROR)
            operation=routes[self.path]
            denied=False
            if self.server.private:
                peer=byte_digest(self.connection.getpeercert(binary_form=True))
                denied=operation not in self.server.permissions.get(peer,frozenset())
            raw=self._read_body()
            if denied:self._reply(403,{"error":"hosted-stage-denied"});return
            value=document(raw)
            require(type(value) is dict and set(value)=={"profile","nonce","deadline","arguments"}
                and value["profile"]==PROFILE and type(value["nonce"]) is str and len(value["nonce"])==64
                and all(c in "0123456789abcdef" for c in value["nonce"]),ERROR)
            use.clip(value["deadline"]);arguments=value["arguments"];before=use.now()
            if self.server.private:
                facts=self._private_facts(operation,arguments,use)
            else:
                auth=self.headers.get_all("Authorization");require(auth and len(auth)==1 and auth[0].startswith("Bearer ") and len(auth[0])<=16384,ERROR)
                facts=asdict(self.server.service.handle(operation,arguments,auth[0][7:],decision=use))
            use.now();self._reply(200,{"profile":PROFILE,"principal_ref":self.server.principal,"nonce":value["nonce"],
                "operation":self.path,"facts":facts,"observed_at":before,"expires_at":use.deadline})
        except Exception:
            try:self._reply(400,{"error":ERROR})
            except OSError:pass
