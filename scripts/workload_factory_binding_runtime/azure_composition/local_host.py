"""Selected local measurement only. No enrollment, provider I/O or default host."""
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
import math
import re
import ssl
import threading
from workload_factory_binding.evidence import BindingError, byte_digest, canonical, digest, require, valid_digest
from ..custody import _read
from ..bootstrap import validate_dispatch_context
from ..github_bootstrap.common import document
from ..hosted.host_agent import HostAgent
from ..hosted.measurement import MeasurementBindings, LaunchObservation, measure
from ..hosted.nonces import NonceLedger
from ..hosted.plan import StaticPlan
from ..launch import ProcessLaunch
from .selection import ref

ERROR = 'azure-measurement-refused'
PROFILE = 'openxfactory-azure-local-measurement-internal-v2'
NONCE = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
REQUEST = frozenset('profile operation request_nonce deployment_ref plan_digest case_ref source_commit run_id run_attempt launch_ref deadline remaining_milliseconds'.split())
RESPONSE = frozenset('profile principal_ref independent_observer_refs deployment_ref plan_digest case_ref source_commit run_id run_attempt launch_ref host_ref incarnation_ref boot_id invocation_ref pid start_time configuration policy observed_at expires_at request_nonce'.split())


def private(operation):
    try:
        return operation()
    except BaseException as error:
        cancelled = isinstance(error, KeyboardInterrupt)
    if cancelled:
        raise KeyboardInterrupt() from None
    raise BindingError(ERROR) from None


class Opaque:
    __slots__ = ()
    def __getstate__(self):
        raise BindingError(ERROR)
    def __reduce_ex__(self, protocol):
        raise BindingError(ERROR)


@dataclass(frozen=True, repr=False)
class Scope:
    plan: StaticPlan
    context: object
    deployment_ref: str
    observer_refs: tuple

    def record(self):
        require(type(self.plan) is StaticPlan and type(self.observer_refs) is tuple
                and len(self.observer_refs) == 2 and len(set(self.observer_refs)) == 2, ERROR)
        validate_dispatch_context(self.context)
        for item in (self.deployment_ref, *self.observer_refs):
            ref(item)
        p = self.plan.value()
        require(self.plan.digest == digest(p) == self.context.selection_digest, ERROR)
        c, s = p['configuration_template'], p['staging_policy']
        require(c['sources']['adapter']['commit'] == self.context.source_commit
                and c['services']['worker_channel']['principal_ref'] not in self.observer_refs, ERROR)
        return dict(independent_observer_refs=list(self.observer_refs),
                    deployment_ref=self.deployment_ref, plan_digest=self.plan.digest,
                    case_ref=c['case_ref'], source_commit=self.context.source_commit,
                    run_id=self.context.run_id, run_attempt=self.context.run_attempt,
                    **{k:s[k] for k in ('launch_ref','host_ref','incarnation_ref','boot_id')})


@dataclass(frozen=True, repr=False)
class PeerApproval:
    principal_ref: str
    role: str
    source_commit: str
    host_ref: str
    incarnation_ref: str
    scope_digest: str
    not_before: int
    expires_at: int


class LocalClock:
    """Subordinate local timer, intentionally not a proof Decision/ledger member."""
    def __init__(self, clock, monotonic, deadline, milliseconds):
        require(type(deadline) is int and type(milliseconds) is int
                and 1 <= milliseconds <= 10000, ERROR)
        self.clock, self.monotonic, self.deadline = clock, monotonic, deadline
        self.last = self.last_mono = None
        self.end = None
        self.now()
        self.end = self.last_mono + milliseconds / 1000

    def now(self):
        wall, mono = self.clock(), self.monotonic()
        require(type(wall) is int and type(mono) in (int,float) and math.isfinite(mono)
                and mono >= 0 and wall < self.deadline
                and (self.last is None or wall >= self.last)
                and (self.last_mono is None or mono >= self.last_mono)
                and (self.end is None or mono < self.end), ERROR)
        self.last, self.last_mono = wall, mono
        return wall

    def remaining(self):
        self.now()
        return min(self.deadline-self.last, self.end-self.last_mono)

    def clip(self, expiry):
        require(type(expiry) is int, ERROR)
        self.deadline = min(self.deadline,expiry)
        self.now()


class LocalObserver(Opaque):
    """Original manager capability and independent actual local reads per request."""
    __slots__ = ('manager','worker','scope','principal','bindings','_scope','_roots','_namespace','_store','_worker_scope','_owner')
    def __init__(self, *, manager, scope, principal):
        private(lambda:self._initialize(manager,scope,principal))

    def _initialize(self,manager,scope,principal):
        ref(principal)
        require(type(manager) is HostAgent and type(scope) is Scope
                and principal in scope.observer_refs, ERROR)
        require(manager.worker.plan.raw == scope.plan.raw and manager.worker.context == scope.context, ERROR)
        self.manager, self.worker, self.scope, self.principal = manager, manager.worker, scope, principal
        self.bindings = MeasurementBindings(principal, dict(self.worker.roots), None)
        self._scope = canonical(scope.record())
        self._roots = canonical({k:str(v) for k,v in self.bindings.roots.items()})
        self._namespace = manager.pid_namespace
        self._store = manager.store
        self._worker_scope = self.worker.scope_raw
        self._owner = manager.launch_owner

    def _row(self, use):
        require(self.manager.worker is self.worker and self.manager.store is self._store
                and self._store.kind == 'host' and self.worker.scope_raw == self._worker_scope
                and self.worker.plan.raw == self.scope.plan.raw and self.worker.context == self.scope.context
                and canonical(self.scope.record()) == self._scope
                and canonical({k:str(v) for k,v in self.bindings.roots.items()}) == self._roots
                and self.bindings.principal_ref == self.principal
                and self.manager.pid_namespace == self._namespace, ERROR)
        row = self.manager.store.read(self.scope.record()['launch_ref'], decision=use)
        require(row['state'] == 'running' and row['unit'] is not None
                and row['generation'] is not None and row['lease'] is not None
                and self.manager._unit_current(row['unit']), ERROR)
        require(canonical(row['scope']) == self._worker_scope
                and row['unit']['manager_kind'] == 'reference-posix-session-v1'
                and row['unit']['scope_digest'] == digest(row['scope'])
                and row['unit']['unit_ref'] == 'unit:'+digest(row['scope']).split(':')[1]
                and all(row['unit'][k] == self.scope.record()[k]
                        for k in ('host_ref','incarnation_ref','boot_id'))
                and row['lease']['scope_digest'] == digest(row['scope'])
                and row['lease']['unit_digest'] == digest(row['unit']), ERROR)
        use.clip(min(row['deadline'],row['lease']['expires_at']))
        with self.manager.children_lock:
            process = self.manager.children.get(self.scope.record()['launch_ref'])
        require(self.manager.launch_owner is self._owner, ERROR)
        owners = tuple(self._owner._threads)
        require(len(owners) == 1 and owners[0].is_alive(), ERROR)
        # Linux PDEATHSIG and this kernel child list belong to the actual
        # persistent creating thread, not a reconstructed manager object.
        children = (Path('/proc/self/task')/str(owners[0].native_id)/'children').read_text().split()
        require(process is not None and str(process.pid) in children and process.poll() is None
                and process.pid == row['generation']['pid'], ERROR)
        for target in ('self',str(process.pid)):
            info = (Path('/proc')/target/'ns/pid').stat()
            require((info.st_dev,info.st_ino) == self._namespace, ERROR)
        require(self.worker.observe(process.pid,row['generation']['start_time'],row['unit'],use)
                == row['generation'], ERROR)
        return row,process

    def read(self, *, use):
        return private(lambda:self._read(use))

    def _read(self,use):
        before, process = self._row(use)
        w = self.worker
        captured = ProcessLaunch.capture(process, executable=w.paths['executable'],
            executable_digest=w.m['executable_digest'], worker=w.paths['worker'],
            configuration_file=w.paths['configuration'], cwd=w.paths['cwd'], artifacts=w.artifacts)
        require(captured.start_time == before['generation']['start_time'], ERROR)
        s = self.scope.record()
        observed = LaunchObservation(self.principal,s['launch_ref'],s['host_ref'],s['incarnation_ref'],
            s['boot_id'],before['unit']['invocation_ref'],captured,use.now(),use.deadline)
        configuration,policy,generation = measure(self.scope.plan,self.scope.context,self.bindings,observed,decision=use)
        after,child = self._row(use)
        require(child is process and canonical(before) == canonical(after), ERROR)
        return configuration,policy,generation


class MeasurementServer(ThreadingMixIn, HTTPServer):
    daemon_threads = False
    block_on_close = True
    request_queue_size = 8
    def __init__(self, *, observer, ledger, peers, cert_file, key_file, ca_file,
                 clock, monotonic, listen=('127.0.0.1',0)):
        require(type(observer) is LocalObserver and type(ledger) is NonceLedger
                and type(peers) is dict and all(valid_digest(k) and type(v) is PeerApproval
                                              for k,v in peers.items()), ERROR)
        self.observer,self.ledger,self.peers = observer,ledger,peers
        self._selected_observer,self._selected_ledger,self._selected_peers = observer,ledger,peers
        self._ledger_identity = (ledger.directory,ledger.identity)
        self._clocks = (clock,monotonic)
        self.clock,self.monotonic = clock,monotonic
        observer.worker._protect_private((key_file,ledger.directory/'issuance.sqlite'))
        self.material_files = (ca_file,cert_file,key_file)
        self.material_pin = self.materials()
        self.tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.tls.minimum_version = ssl.TLSVersion.TLSv1_2
        self.tls.verify_mode = ssl.CERT_REQUIRED
        self.tls.load_verify_locations(cafile=ca_file)
        self.tls.load_cert_chain(cert_file,key_file)
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(listen,Handler)

    def get_request(self):
        request,address = super().get_request()
        request.settimeout(2)
        return request,address

    def finish_request(self, request, address):
        with self.tls.wrap_socket(request,server_side=True) as secured:
            self.RequestHandlerClass(secured,address,self)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request,address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request,address)
        finally:
            self.slots.release()

    def handle_error(self, request, address):
        pass

    def materials(self):
        return tuple(byte_digest(_read(path,private=index==2))
                     for index,path in enumerate(self.material_files))

    def approved(self, fingerprint, use):
        require(self.observer is self._selected_observer and self.ledger is self._selected_ledger
                and self.peers is self._selected_peers
                and (self.ledger.directory,self.ledger.identity) == self._ledger_identity
                and self.clock is self._clocks[0] and self.monotonic is self._clocks[1]
                and self.materials() == self.material_pin, ERROR)
        approval = self.peers.get(fingerprint)
        s = self.observer.scope.record()
        require(type(approval) is PeerApproval and type(approval.role) is str and approval.role == 'control'
                and type(approval.source_commit) is str
                and valid_digest(approval.scope_digest) and approval.scope_digest == digest(s)
                and approval.source_commit == s['source_commit']
                and approval.host_ref == s['host_ref'] and approval.incarnation_ref == s['incarnation_ref']
                and type(approval.not_before) is int and type(approval.expires_at) is int
                and approval.not_before <= use.now() < approval.expires_at, ERROR)
        for value in (approval.principal_ref,approval.host_ref,approval.incarnation_ref):
            ref(value)
        use.clip(approval.expires_at)
        return approval

    def measure(self, raw, fingerprint):
        value = document(raw,4096)
        require(type(value) is dict and canonical(value) == raw and set(value) == REQUEST
                and value['profile'] == PROFILE and value['operation'] == 'measure'
                and type(value['request_nonce']) is str and NONCE.fullmatch(value['request_nonce']), ERROR)
        scope = self.observer.scope.record()
        require(all(value[k] == scope[k] for k in ('deployment_ref','plan_digest','case_ref',
                'source_commit','run_id','run_attempt','launch_ref')), ERROR)
        use = LocalClock(self.clock,self.monotonic,value['deadline'],value['remaining_milliseconds'])
        use.clip(self.observer.scope.plan.valid_until)
        approval = self.approved(fingerprint,use)
        # Existing initialized protected state; durable consumption precedes local observations.
        self.ledger.reserve('measurement:'+value['request_nonce'],value['request_nonce'],
                            digest({'request':value,'peer':fingerprint}),decision=use)
        configuration,policy,generation = self.observer.read(use=use)
        require(self.approved(fingerprint,use) == approval, ERROR)
        reply = dict(profile=PROFILE,principal_ref=self.observer.principal,
                     **scope,
                     invocation_ref=generation['invocation_ref'],pid=generation['pid'],start_time=generation['start_time'],
                     configuration=document(configuration,16384),policy=document(policy,16384),
                     observed_at=use.now(),expires_at=use.deadline,request_nonce=value['request_nonce'])
        require(set(reply) == RESPONSE, ERROR)
        raw = canonical(reply)
        require(len(raw) <= 16384, ERROR)
        use.now()
        return raw


class Handler(BaseHTTPRequestHandler):
    server_version = 'LocalMeasurement'
    sys_version = ''
    def setup(self):
        super().setup()
        self.timer = threading.Timer(10,self._expire)
        self.timer.daemon = True
        self.timer.start()
    def _expire(self):
        try:
            self.connection.shutdown(2)
        except OSError:
            pass
    def finish(self):
        self.timer.cancel()
        self.timer.join(timeout=1)
        super().finish()
    def send_error(self,*arguments,**keywords):
        self.reply(400,canonical({'error':ERROR}))
    def log_message(self,*arguments):
        pass
    def reply(self,status,raw):
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Connection','close')
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True
    def do_POST(self):
        try:
            require(self.path == '/readback' and self.headers.get_all('Content-Type') == ['application/json']
                    and self.headers.get('Transfer-Encoding') is None
                    and sum(len(k)+len(v) for k,v in self.headers.items()) <= 16384, ERROR)
            lengths = self.headers.get_all('Content-Length')
            require(lengths and len(lengths) == 1 and lengths[0].isascii() and lengths[0].isdigit()
                    and len(lengths[0]) <= 4 and 0 < int(lengths[0]) <= 4096, ERROR)
            raw = self.rfile.read(int(lengths[0]))
            require(len(raw) == int(lengths[0]), ERROR)
            peer = byte_digest(self.connection.getpeercert(binary_form=True))
            if peer not in self.server.peers or self.server.peers[peer].role != 'control':
                self.reply(403,canonical({'error':'azure-measurement-denied'}))
                return
            reply = private(lambda:self.server.measure(raw,peer))
            self.reply(200,reply)
        except BaseException:
            try:
                self.reply(400,canonical({'error':ERROR}))
            except OSError:
                pass
