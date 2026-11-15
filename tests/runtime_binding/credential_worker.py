"""Private credential-denial fixture; never print returned capability bytes."""
import json
import socket
import struct
import sys
try:
    channel=socket.socket(fileno=int(sys.argv[1]))
    print("ready",flush=True)
    request=sys.stdin.buffer.readline(65537)
    if len(sys.argv)>2 and sys.argv[2]=="passive":
        channel.settimeout(1)
        response=json.loads(channel.recv(65537))
    else:
        reader,writer=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
        try:
            channel.sendmsg([request.strip()],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,struct.pack("i",writer.fileno()))])
            writer.close();reader.settimeout(3)
            response=json.loads(reader.recv(65537))
        finally:reader.close();writer.close()
    print(json.dumps({"status":response.get("status","invalid")}),flush=True)
except Exception:
    print('{"status":"unavailable"}',flush=True)
