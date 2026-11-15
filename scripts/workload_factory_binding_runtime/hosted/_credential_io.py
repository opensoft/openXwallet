"""Private anonymous-pipe HTTPS helper. No inherited credentials or redirects.

Nonsecret routing is selected by the trusted parent before spawning the helper.
Only TLS material references, headers and body cross its private anonymous stdin.
"""
import base64
import http.client
import json
import signal
import ssl
import sys
from urllib.parse import urlsplit
LIMIT=1048576


def route():
    method,url=sys.argv[1:]
    target=urlsplit(url)
    if (method not in ("GET","POST","DELETE") or len(url)>4096
            or not all(32<ord(c)<127 for c in url) or target.scheme!="https"
            or not target.hostname or target.username is not None or target.password is not None
            or target.fragment or not target.path.startswith("/")):
        raise ValueError
    return method,target


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
        method,target=route()
        value=json.loads(sys.stdin.buffer.readline(196609));context=tls_context(value)
        signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,min(5,value["seconds"]))
        connection=http.client.HTTPSConnection(target.hostname,target.port or 443,context=context,timeout=min(5,value["seconds"]))
        connection.connect();signal.setitimer(signal.ITIMER_REAL,value["seconds"])
        print("READY",flush=True)
        if sys.stdin.buffer.readline(4)!=b"GO\n":raise ValueError
        path=target.path+("?"+target.query if target.query else "")
        connection.request(method,path,body=base64.b64decode(value["body"],validate=True),headers=value["headers"])
        print(json.dumps(read_response(connection)),flush=True)
        return 0
    except Exception:return 2
    finally:
        if connection is not None:connection.close()


if __name__=="__main__":raise SystemExit(main())
