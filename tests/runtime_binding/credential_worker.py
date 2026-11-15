"""Private credential-denial fixture; never print returned capability bytes."""
import json
import socket
import sys
try:
    channel=socket.socket(fileno=int(sys.argv[1]))
    print("ready",flush=True)
    request=sys.stdin.buffer.readline(65537)
    channel.send(request.strip())
    channel.settimeout(3)
    raw=channel.recv(65537)
    response=json.loads(raw)
    print(json.dumps({"status":response.get("status","invalid")}),flush=True)
except Exception:
    print('{"status":"unavailable"}',flush=True)
