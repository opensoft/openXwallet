"""Disposable root-only Linux UID/file/network fixture, never deployment setup.

Run only in a new network-none, read-only-source container with one private writable
fixture mount. libseccomp is an observed image prerequisite, not a Python dependency.
"""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
from threading import Thread
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from workload_factory_binding.evidence import canonical
from workload_factory_binding_runtime.github_bootstrap.common import Decision
from workload_factory_binding_runtime.hosted.credential import CredentialBroker,KernelPrincipal,credential_channels

PROBE=r"""import ctypes,ctypes.util,errno,http.client,json,os,sys
try:
    operation,target,restrict=sys.argv[1:]
    if restrict=='yes':
        lib=ctypes.CDLL(ctypes.util.find_library('seccomp'))
        lib.seccomp_init.argtypes=[ctypes.c_uint32];lib.seccomp_init.restype=ctypes.c_void_p
        lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
        lib.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
        lib.seccomp_load.argtypes=[ctypes.c_void_p];lib.seccomp_release.argtypes=[ctypes.c_void_p]
        context=lib.seccomp_init(0x7fff0000)
        assert context
        try:
            call=lib.seccomp_syscall_resolve_name(b'connect');assert call>=0
            assert lib.seccomp_rule_add(context,0x50000|errno.EPERM,call,0)==0
            assert lib.seccomp_load(context)==0
        finally:lib.seccomp_release(context)
    if operation=='read':
        with open(target,'rb') as stream:assert stream.read()==b'fixture-only-key'
    elif operation=='write':
        with open(target,'wb') as stream:stream.write(b'fixture-policy')
    else:
        connection=http.client.HTTPConnection('127.0.0.1',int(target),timeout=2)
        try:
            connection.request('GET','/metadata/identity/oauth2/token')
            response=connection.getresponse();assert response.status==200;response.read(1024)
        finally:connection.close()
    result={'status':'ok'}
except OSError as error:
    result={'status':'denied' if error.errno in (errno.EACCES,errno.EPERM) else 'unavailable','errno':error.errno}
except Exception:result={'status':'unavailable'}
print(json.dumps(result),flush=True)
"""


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--temp-root',required=True);args=parser.parse_args()
    root=Path(args.temp_root).absolute()
    assert os.geteuid()==0 and root.resolve()==root and root.is_dir() and not list(root.iterdir())
    root.chmod(0o711)
    private=root/'trusted';private.mkdir(mode=0o700);os.chown(private,1001,1001)
    key=private/'key';policy=private/'policy';key.write_bytes(b'fixture-only-key');policy.write_bytes(b'fixture-policy')
    for path in (key,policy):path.chmod(0o600);os.chown(path,1001,1001)
    public=root/'public';public.mkdir(mode=0o755)
    helper=public/'credential_worker.py';shutil.copyfile(Path(__file__).with_name('credential_worker.py'),helper);helper.chmod(0o444)
    processes=[];generations=[];checks={}
    def start(command,uid,**kwargs):
        p=subprocess.Popen(command,user=uid,group=uid,extra_groups=(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,env={'PATH':os.defpath,'LANG':'C.UTF-8'},**kwargs)
        processes.append(p)
        try:stamp=(Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()[19]
        except FileNotFoundError:stamp=None
        generations.append({'pid':p.pid,'start_time':stamp});return p
    def probe(label,uid,operation,target,restricted,expected):
        p=start(['/usr/bin/python3','-I','-c',PROBE,operation,str(target),'yes' if restricted else 'no'],uid)
        raw,_=p.communicate(timeout=5);assert p.returncode==0
        result=json.loads(raw);checks[label]=result;assert result['status']==expected,label
        return result
    class Metadata(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_GET(self):
            self.send_response(200);self.end_headers();self.wfile.write(b'fixture-provider-response')
    http=ThreadingHTTPServer(('127.0.0.1',0),Metadata);thread=Thread(target=http.serve_forever,daemon=True);thread.start()
    try:
        probe('allowed-key-read',1001,'read',key,False,'ok')
        probe('worker-key-read',1002,'read',key,False,'denied')
        probe('allowed-policy-write',1001,'write',policy,False,'ok')
        probe('worker-policy-write',1002,'write',policy,False,'denied')
        private.chmod(0o711);key.chmod(0o644);policy.chmod(0o666)
        probe('exposed-key-mutation-detected',1002,'read',key,False,'ok')
        probe('writable-policy-mutation-detected',1002,'write',policy,False,'ok')
        private.chmod(0o700);key.chmod(0o600);policy.chmod(0o600)
        probe('allowed-metadata-connect',1001,'network',http.server_port,False,'ok')
        probe('worker-metadata-kernel-denial',1002,'network',http.server_port,True,'denied')
        probe('exposed-network-mutation-detected',1002,'network',http.server_port,False,'ok')
        for uid,label,expected in [(1001,'allowed-kernel-resolver','ok'),(1002,'worker-kernel-resolver','denied')]:
            server,client=credential_channels();p=None;worker=None
            try:
                p=start(['/usr/bin/python3','-I','-B',str(helper),str(client.fileno())],uid,pass_fds=(client.fileno(),))
                assert select.select([p.stdout],[],[],3)[0] and p.stdout.readline()==b'ready\n'
                stamp=int((Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split()[19])
                # Only the actual trusted UID's generation can receive the secret.
                allowed=KernelPrincipal(1001,p.pid,stamp,'issuer')
                service=CredentialBroker(principals=(allowed,),capabilities={'resolver':(('issuer',),lambda **_:b'fixture-only-capability')})
                worker=Thread(target=lambda:service.serve_once(server,decision=Decision(clock=lambda:int(time.time()))));worker.start()
                raw,_=p.communicate(canonical({'role':'issuer','operation':'resolver'})+b'\n',timeout=5)
                result=json.loads(raw);checks[label]=result;assert result['status']==expected
            finally:
                server.close();client.close()
                if worker is not None:worker.join(timeout=5);assert not worker.is_alive()
        for name in ('exposed-key-mutation-detected','writable-policy-mutation-detected','exposed-network-mutation-detected'):
            if checks[name]['status']=='denied':raise AssertionError('exposure incorrectly qualified')
            checks[name]['denial_probe_detected_exposure']=True
    finally:
        http.shutdown();http.server_close();thread.join(timeout=5);assert not thread.is_alive()
        for p in processes:
            if p.poll() is None:p.kill()
            p.communicate()
        assert all(p.poll() is not None for p in processes)
        (root/'result.json').write_text(json.dumps({'scope':'isolated-kernel-fixture','checks':checks,'generations':generations,
            'all_helpers_reaped':all(p.poll() is not None for p in processes)},indent=2))
    print('isolated-kernel-qualification: PASS')


if __name__=='__main__':main()
