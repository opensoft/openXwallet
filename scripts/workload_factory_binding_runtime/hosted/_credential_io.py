"""Private anonymous-pipe HTTPS helper. No inherited credentials or redirects.

Nonsecret routing is selected by the trusted parent before spawning the helper.
Only TLS material references, headers and body cross its private anonymous stdin.
"""
import base64
import http.client
import hashlib
import json
import re
import signal
import time
import ssl
import sys
from urllib.parse import urlsplit
LIMIT=1048576
LOOPBACK_HOST="127.0.0.1"


def github_path(method,path,query):
    if method=="GET" and path=="/app" and not query:return "/app"
    if method=="GET" and path=="/installation/repositories" and query=="per_page=2&page=1":
        return "/installation/repositories?per_page=2&page=1"
    if method=="DELETE" and path=="/installation/token" and not query:return "/installation/token"
    match=re.fullmatch(r"/app/installations/([1-9]\d{0,15})(/access_tokens)?",path,re.ASCII)
    if match and not query:
        base="/app/installations/"+str(int(match[1]))
        if method=="GET" and match[2] is None:return base
        if method=="POST" and match[2]=="/access_tokens":return base+"/access_tokens"
    if method=="GET":return github_read_path(path,query)
    raise ValueError


def github_read_path(path,query):
    root="/repos/opensoft/openXwallet"
    if path==root+"/git/ref/heads/main" and not query:return path
    if re.fullmatch(re.escape(root)+r"/actions/runs/[1-9]\d{0,15}(/approvals)?",path,re.ASCII) and not query:return path
    if re.fullmatch(re.escape(root)+r"/actions/runs/[1-9]\d{0,15}/attempts/1/jobs",path,re.ASCII) and query in ("per_page=100&page=1","per_page=100&page=2"):return path+"?"+query
    if path==root+"/rulesets" and query=="includes_parents=true&per_page=32&page=1":return path+"?"+query
    if re.fullmatch(re.escape(root)+r"/rulesets/[1-9]\d{0,15}",path,re.ASCII) and query=="includes_parents=true":return path+"?"+query
    if re.fullmatch(re.escape(root)+r"/environments/[A-Za-z0-9_-]{1,100}",path) and not query:return path
    if re.fullmatch(re.escape(root)+r"/environments/[A-Za-z0-9_-]{1,100}/deployment-branch-policies",path) and query in ("per_page=32&page=1","per_page=32&page=2"):return path+"?"+query
    if path in (root+"/contents/.github/workflows/protected-runtime-qualification.yml",root+"/contents/.github/workflows/protected-runtime-qualification-run.yml") and re.fullmatch(r"ref=[0-9a-f]{40}",query):return path+"?"+query
    raise ValueError


def arm_path(method,path,query):
    prefix=r"/subscriptions/[0-9a-f-]{36}/resourceGroups/[A-Za-z0-9_.()-]{1,90}/providers/"
    compute=re.fullmatch(prefix+r"Microsoft\.Compute/(virtualMachines|images|disks)/[A-Za-z0-9_.-]{1,80}",path)
    network=re.fullmatch(prefix+r"Microsoft\.Network/(networkInterfaces|networkSecurityGroups|publicIPAddresses|virtualNetworks)/[A-Za-z0-9_.-]{1,80}(/subnets/[A-Za-z0-9_.-]{1,80})?",path)
    if method!="GET":raise ValueError
    if compute:
        expected={"virtualMachines":"2025-04-01&$expand=instanceView","images":"2026-03-01","disks":"2026-03-02"}[compute[1]]
        if query=="api-version="+expected:return path+"?"+query
    if network and query=="api-version=2026-01-01":return path+"?"+query
    raise ValueError


def vault_path(method,path,query):
    if method=="GET" and re.fullmatch(r"/keys/[A-Za-z0-9-]{1,127}/[0-9a-f]{32}",path) and query=="api-version=2025-07-01":return path+"?"+query
    match=re.fullmatch(r"/keys/([A-Za-z0-9-]{1,127})/([0-9a-f]{32})/sign",path)
    if method!="POST" or match is None or query!="api-version=2025-07-01":raise ValueError
    return "/keys/"+match[1]+"/"+match[2]+"/sign?api-version=2025-07-01"


def vault_route(method,target):
    host=re.fullmatch(r"([a-z0-9-]{3,24})\.vault\.azure\.net",target.netloc)
    if host is None:raise ValueError
    return host[1]+".vault.azure.net",443,vault_path(method,target.path,target.query),False


def parse_target(method,url):
    target=urlsplit(url)
    if (method not in ("GET","POST","DELETE") or len(url)>4096
            or not all(32<ord(c)<127 for c in url) or target.scheme!="https"
            or not target.hostname or target.username is not None or target.password is not None
            or target.fragment or not target.path.startswith("/")):
        raise ValueError
    return target


def fixture_route(method,target):
    if sys.argv[3]!="--fixture-port" or not sys.argv[4].isascii() or not sys.argv[4].isdigit():raise ValueError
    port=int(sys.argv[4])
    if not 1<=port<=65535 or target.netloc!=LOOPBACK_HOST+":"+str(port):raise ValueError
    if method=="POST" and target.path in ("/enroll","/private") and not target.query:
        return LOOPBACK_HOST,port,target.path,True
    if method=="DELETE" and target.path=="/fixture/empty" and not target.query:
        return LOOPBACK_HOST,port,"/fixture/empty",True
    try:path=github_path(method,target.path,target.query)
    except ValueError:
        try:path=vault_path(method,target.path,target.query)
        except ValueError:path=arm_path(method,target.path,target.query)
    return LOOPBACK_HOST,port,path,True


def observation_route(method,target):
    selected=urlsplit(sys.argv[4])
    if (method!="POST" or target.path!="/readback" or target.query or selected.scheme!="https"
            or not selected.hostname or selected.username is not None or selected.password is not None
            or selected.path or selected.query or selected.fragment or selected.netloc!=target.netloc):raise ValueError
    return method,(selected.hostname,selected.port or 443,"/readback","observation")


def hosted_route(method,target,mode):
    selected=urlsplit(sys.argv[4]);paths={"agent":("/stage/register","/stage/start","/stage/status"),
                                       "admission":("/v2/plan","/v2/protected")}
    if (method!="POST" or target.path not in paths[mode] or target.query or selected.scheme!="https"
            or not selected.hostname or selected.username is not None or selected.password is not None
            or selected.path or selected.query or selected.fragment or selected.netloc!=target.netloc):raise ValueError
    return method,(selected.hostname,selected.port or 443,target.path,mode)


def route():
    method,url=sys.argv[1:3];target=parse_target(method,url)
    if len(sys.argv)==5:
        if sys.argv[3]=="--observation-origin":return observation_route(method,target)
        if sys.argv[3] in ("--agent-origin","--admission-origin"):return hosted_route(method,target,sys.argv[3][2:-7])
        return method,fixture_route(method,target)
    if len(sys.argv)!=3:raise ValueError
    if target.netloc=="api.github.com":return method,("api.github.com",443,github_path(method,target.path,target.query),False)
    if target.netloc=="management.azure.com":return method,("management.azure.com",443,arm_path(method,target.path,target.query),False)
    return method,vault_route(method,target)


def tls_context(value):
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);context.minimum_version=ssl.TLSVersion.TLSv1_2
    if value["ca"] is None:context.load_default_certs()
    else:context.load_verify_locations(cafile=value["ca"])
    if value["certificate"] is not None:context.load_cert_chain(value["certificate"],value["key"])
    return context


def framing(response):
    headers=response.getheaders()
    if len(headers)>64 or sum(len(k)+len(v) for k,v in headers)>32768:raise ValueError
    lengths=response.headers.get_all("Content-Length",[]);transfers=response.headers.get_all("Transfer-Encoding",[])
    if (len(lengths)>1 or len(transfers)>1 or (lengths and transfers)
            or (transfers and transfers!=["chunked"])
            or response.getheader("Content-Encoding","identity")!="identity"
            or response.getheader("Link") is not None):raise ValueError
    if lengths:
        size=lengths[0]
        if not size.isascii() or not size.isdigit() or len(size)>7 or int(size)>LIMIT:raise ValueError
    return lengths


def read_response(connection):
    response=connection.getresponse();lengths=framing(response)
    body=response.read(LIMIT+1)
    if len(body)>LIMIT or (lengths and len(body)!=int(lengths[0])):raise ValueError
    content=response.headers.get_all("Content-Type",[])
    if response.status!=204 and (len(content)!=1 or content[0].split(";",1)[0].strip() not in ("application/json","application/vnd.github+json")):raise ValueError
    if response.status==204 and body:raise ValueError
    return {"status":response.status,"body":base64.b64encode(body).decode()}


def expired(_sig,_frame):raise TimeoutError


def main():
    connection=None
    try:
        method,(host,port,path,fixture)=route()
        value=json.loads(sys.stdin.buffer.readline(196609))
        if fixture in (True,"observation","agent") and any(value[k] is None for k in ("ca","certificate","key")):raise ValueError
        started=time.monotonic()
        context=tls_context(value)
        signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,min(5,value["seconds"]))
        connection=http.client.HTTPSConnection(host,port,context=context,timeout=min(5,value["seconds"]))
        connection.connect()
        remaining=value["seconds"]-(time.monotonic()-started)
        if remaining<=0:raise TimeoutError
        # Connect retains five seconds; response I/O uses the original total RPC
        # remainder, rather than accidentally inheriting the connect timeout.
        connection.sock.settimeout(remaining);signal.setitimer(signal.ITIMER_REAL,remaining)
        if fixture in ("observation","agent","admission") and value["server_pin"] is not None and "sha256:"+hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()!=value["server_pin"]:raise ValueError
        print("READY",flush=True)
        if sys.stdin.buffer.readline(4)!=b"GO\n":raise ValueError
        connection.request(method,path,body=base64.b64decode(value["body"],validate=True),headers=value["headers"])
        print(json.dumps(read_response(connection)),flush=True)
        return 0
    except Exception:return 2
    finally:
        if connection is not None:connection.close()


if __name__=="__main__":raise SystemExit(main())
