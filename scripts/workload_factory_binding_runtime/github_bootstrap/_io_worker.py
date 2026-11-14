"""Private bounded HTTPS child. Credentials only cross anonymous pipes."""
import base64
import http.client
import json
import signal
import ssl
import sys
from urllib.parse import urlsplit

LIMIT = 1048576

def main():
    connection = None
    try:
        raw = sys.stdin.buffer.readline(196609)
        value = json.loads(raw)
        url = urlsplit(value["url"])
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        if value["ca_file"] is None:
            context.load_default_certs()
        else:
            context.load_verify_locations(cafile=value["ca_file"])
        def expired(_sig, _frame):
            raise TimeoutError
        signal.signal(signal.SIGALRM, expired)
        signal.setitimer(signal.ITIMER_REAL, min(5, value["seconds"]))
        connection = http.client.HTTPSConnection(url.hostname, url.port or 443,
            timeout=min(5, value["seconds"]), context=context)
        connection.connect()
        signal.setitimer(signal.ITIMER_REAL, value["seconds"])
        print("READY", flush=True)
        if sys.stdin.buffer.readline(4) != b"GO\n":
            raise ValueError
        connection.request(value["method"], url.path + ("?" + url.query if url.query else ""),
            body=base64.b64decode(value["body"]), headers=value["headers"])
        response = connection.getresponse()
        headers = response.getheaders()
        if (len(headers) > 64 or sum(len(k) + len(v) for k, v in headers) > 32768
                or response.getheader("Content-Encoding", "identity") != "identity"):
            raise ValueError
        lengths = response.headers.get_all("Content-Length", [])
        encodings = response.headers.get_all("Transfer-Encoding", [])
        if (len(lengths) > 1 or len(encodings) > 1 or (lengths and encodings)
                or (encodings and encodings != ["chunked"])
                or (lengths and (not lengths[0].isascii() or not lengths[0].isdigit()
                    or len(lengths[0]) > 7 or int(lengths[0]) > LIMIT))):
            raise ValueError
        body = response.read(LIMIT + 1)
        if (lengths and len(body) != int(lengths[0])) or not 0 < len(body) <= LIMIT:
            raise ValueError
        print(json.dumps({"status": response.status, "headers": headers,
                          "body": base64.b64encode(body).decode("ascii")}), flush=True)
        return 0
    except BaseException:
        print('{"error":"github-bootstrap-refused"}', flush=True)
        return 2
    finally:
        if connection is not None:
            connection.close()

if __name__ == "__main__":
    raise SystemExit(main())
