#!/usr/bin/env python3
"""Two Minds — edge gate (Content-Length framing, blocks /admin)."""
import socket
import threading

BACKEND = ('127.0.0.1', 9000)

BLOCKED = (b'HTTP/1.1 403 Forbidden\r\n'
           b'Content-Length: 44\r\n'
           b'Content-Type: text/plain\r\n'
           b'Connection: keep-alive\r\n\r\n'
           b'403 forbidden: /admin is blocked at the edge.\n')


def recv_more(sock, buf, need):
    while len(buf) < need:
        d = sock.recv(4096)
        if not d:
            raise ConnectionError('eof')
        buf += d
    return buf


def next_response(bsock, bbuf):
    """Pull one complete response out of the persistent backend buffer."""
    while b'\r\n\r\n' not in bbuf:
        bbuf = recv_more(bsock, bbuf, len(bbuf) + 1)
    head, rest = bbuf.split(b'\r\n\r\n', 1)
    cl = 0
    for l in head.decode('latin1').split('\r\n')[1:]:
        if l.lower().startswith('content-length:'):
            cl = int(l.split(':', 1)[1].strip())
    while len(rest) < cl:
        rest = recv_more(bsock, rest, cl)
    resp = head + b'\r\n\r\n' + rest[:cl]
    bbuf = rest[cl:]
    return resp, bbuf


def handle(csock):
    try:
        bsock = socket.create_connection(BACKEND, timeout=10)
    except Exception:
        csock.close()
        return
    bbuf = b''
    cbuf = b''
    try:
        while True:
            while b'\r\n\r\n' not in cbuf:
                d = csock.recv(4096)
                if not d:
                    return
                cbuf += d
            head, cbuf = cbuf.split(b'\r\n\r\n', 1)
            lines = head.decode('latin1').split('\r\n')
            parts = lines[0].split(' ')
            path = parts[1] if len(parts) > 1 else '/'
            cl = 0
            for l in lines[1:]:
                if l.lower().startswith('content-length:'):
                    cl = int(l.split(':', 1)[1].strip())
            while len(cbuf) < cl:
                d = csock.recv(4096)
                if not d:
                    return
                cbuf += d
            body, cbuf = cbuf[:cl], cbuf[cl:]
            full = head + b'\r\n\r\n' + body
            if path.startswith('/admin'):
                csock.sendall(BLOCKED)
                continue
            bsock.sendall(full)
            resp, bbuf = next_response(bsock, bbuf)
            csock.sendall(resp)
    except Exception:
        pass
    finally:
        try:
            bsock.close()
        except Exception:
            pass
        try:
            csock.close()
        except Exception:
            pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', 8000))
    srv.listen(128)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()


if __name__ == '__main__':
    main()
