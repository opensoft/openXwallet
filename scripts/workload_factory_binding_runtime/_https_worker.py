"""Fixed-endpoint, public-metadata-only HTTPS helper. No token enters this process."""
import base64
import http.client
import json
import os
import ssl
import sys
import time

ISSUER = "https://token.actions.githubusercontent.com"
DISCOVERY_URL = ISSUER + "/.well-known/openid-configuration"
JWKS_URL = ISSUER + "/.well-known/jwks"
CONNECT_SECONDS = 5.0
FETCH_SECONDS = 10.0
MAX_BODY = 256 * 1024
MAX_FRAME = 512 * 1024
HOST = "token.actions.githubusercontent.com"
PORT = 443


def tls_context(ca_file):
    # Do not load ambient SSL_CERT_FILE/SSL_CERT_DIR or enable SSLKEYLOGFILE.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_alpn_protocols(["http/1.1"])
    if ca_file:
        context.load_verify_locations(cafile=ca_file)
    else:
        defaults = ssl.get_default_verify_paths()
        file = defaults.openssl_cafile
        directory = defaults.openssl_capath
        file = file if file and os.path.isfile(file) else None
        directory = directory if directory and os.path.isdir(directory) else None
        if not file and not directory:
            raise ValueError("no-selected-ca")
        context.load_verify_locations(cafile=file, capath=directory)
    return context


def exchange(url, ca_file, budget, output):
    if url not in (DISCOVERY_URL, JWKS_URL) or not 0 < budget <= FETCH_SECONDS:
        raise ValueError("invalid-fetch")
    deadline = time.monotonic() + budget
    connection = http.client.HTTPSConnection(
        HOST, PORT, timeout=min(CONNECT_SECONDS, budget), context=tls_context(ca_file))
    try:
        connection.connect()
        output.write(b"C")  # Parent bounds DNS, connection and verified TLS together.
        output.flush()
        connection.sock.settimeout(max(0.001, deadline - time.monotonic()))
        connection.request("GET", url[len(ISSUER):], headers={
            "Accept": "application/json, application/jwk-set+json",
            "Accept-Encoding": "identity", "Cache-Control": "no-cache",
            "User-Agent": "openXwallet-issuer",
        })
        with connection.getresponse() as response:
            headers = response.getheaders()
            if len(headers) > 64 or sum(len(k) + len(v) for k, v in headers) > 32768:
                raise ValueError("oversized-headers")
            encoding = response.getheader("Content-Encoding", "identity").strip().lower()
            if encoding != "identity":
                raise ValueError("unsupported-encoding")
            lengths = [v for k, v in headers if k.lower() == "content-length"]
            transfer = [v for k, v in headers if k.lower() == "transfer-encoding"]
            if (len(lengths) > 1 or len(transfer) > 1 or (lengths and transfer)
                    or (transfer and transfer[0].strip().lower() != "chunked")):
                raise ValueError("ambiguous-framing")
            if lengths and (not lengths[0].isascii() or not lengths[0].isdigit()
                            or len(lengths[0]) > 10 or int(lengths[0]) > MAX_BODY):
                raise ValueError("oversized-body")
            body = bytearray()
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError
                # The parent also bounds header parsing, slow-drip reads and DNS.
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(min(8192, MAX_BODY + 1 - len(body)))
                body.extend(chunk)
                if len(body) > MAX_BODY:
                    raise ValueError("oversized-body")
                if not chunk:
                    break
            frame = json.dumps({"status": response.status, "headers": headers,
                                "body": base64.b64encode(body).decode("ascii")},
                               separators=(",", ":")).encode("ascii")
            if len(frame) > MAX_FRAME or time.monotonic() >= deadline:
                raise ValueError("invalid-fetch-result")
            output.write(frame)
            output.flush()
    finally:
        connection.close()


def main():
    try:
        if len(sys.argv) != 4:
            return 1
        exchange(sys.argv[1], sys.argv[2] or None, float(sys.argv[3]), sys.stdout.buffer)
        return 0
    except Exception:
        # Never print certificate/provider payloads or paths in error output.
        return 1


if __name__ == "__main__":
    sys.exit(main())
