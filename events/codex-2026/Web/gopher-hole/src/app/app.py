#!/usr/bin/env python3
"""Gopher Hole — SSRF fetch service."""
import subprocess

from flask import Flask, request

app = Flask(__name__)

BLOCKED = [
    'localhost', '127.', '0.0.0.0', '::1', 'internal', 'metadata',
    '169.254', 'flag', 'admin', 'secret', 'private',
]

INDEX = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gopher Hole — Network Relay</title>
<style>
  :root {
    --bg: #09090b;
    --fg: #fafafa;
    --muted: #a1a1aa;
    --border: #27272a;
    --card: #18181b;
    --accent: #818cf8;
    --accent-2: #a78bfa;
    --ok: #34d399;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      "Inter", "Helvetica Neue", Arial, sans-serif;
    background: var(--bg);
    color: var(--fg);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background-image:
      radial-gradient(circle at 15% 20%, rgba(99,102,241,.16), transparent 40%),
      radial-gradient(circle at 85% 80%, rgba(139,92,246,.16), transparent 40%);
  }
  .card {
    width: 100%;
    max-width: 34rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,.5), 0 8px 24px rgba(0,0,0,.45);
    overflow: hidden;
  }
  .topbar {
    display: flex;
    align-items: center;
    gap: .6rem;
    padding: .9rem 1.25rem;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(180deg, #1c1c1f, #161618);
  }
  .dot { width: .65rem; height: .65rem; border-radius: 9999px; }
  .dot.r { background: #f87171; }
  .dot.y { background: #fbbf24; }
  .dot.g { background: #34d399; }
  .topbar .path {
    margin-left: .5rem;
    font-size: .8rem;
    color: var(--muted);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    letter-spacing: -.01em;
  }
  .body { padding: 2rem 1.75rem 2.25rem; }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: .35rem;
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .04em;
    text-transform: uppercase;
    color: var(--accent);
    background: rgba(129,140,248,.12);
    border: 1px solid rgba(129,140,248,.28);
    border-radius: 9999px;
    padding: .25rem .7rem;
  }
  .badge .pulse {
    width: .4rem; height: .4rem; border-radius: 9999px;
    background: var(--ok);
    box-shadow: 0 0 0 0 rgba(52,211,153,.5);
    animation: ping 2s infinite;
  }
  @keyframes ping {
    0% { box-shadow: 0 0 0 0 rgba(52,211,153,.5); }
    70% { box-shadow: 0 0 0 6px rgba(52,211,153,0); }
    100% { box-shadow: 0 0 0 0 rgba(52,211,153,0); }
  }
  h1 {
    font-size: 1.6rem;
    font-weight: 650;
    letter-spacing: -.02em;
    margin-top: 1rem;
  }
  h1 span {
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
  .sub { color: var(--muted); font-size: .95rem; line-height: 1.6; margin-top: .5rem; }
  form { margin-top: 1.5rem; display: flex; gap: .5rem; }
  input {
    flex: 1;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: .9rem;
    padding: .6rem .85rem;
    border: 1px solid var(--border);
    border-radius: .6rem;
    background: #101012;
    color: var(--fg);
    outline: none;
    transition: border-color .15s, box-shadow .15s;
  }
  input::placeholder { color: #52525b; }
  input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(129,140,248,.18);
  }
  button {
    font-size: .9rem;
    font-weight: 600;
    color: #fff;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    border: none;
    border-radius: .6rem;
    padding: .6rem 1.2rem;
    cursor: pointer;
    transition: filter .15s, transform .05s;
    white-space: nowrap;
  }
  button:hover { filter: brightness(1.05); }
  button:active { transform: translateY(1px); }
  .foot {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px dashed var(--border);
    display: flex;
    justify-content: space-between;
    font-size: .78rem;
    color: var(--muted);
  }
  .foot code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    color: #d4d4d8;
  }
</style>
</head>
<body>
  <div class="card">
    <div class="topbar">
      <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
      <span class="path">relay.gopher-hole.internal — /fetch</span>
    </div>
    <div class="body">
      <span class="badge"><span class="pulse"></span>Network Relay</span>
      <h1>Gopher <span>Hole</span></h1>
      <p class="sub">
        A fetch relay at the edge of the network. Give it a URL and it will
        retrieve the page on your behalf — reaching further than you can.
      </p>
      <form action="/fetch" method="get">
        <input name="url" type="text" placeholder="http://example.com/"
               autofocus spellcheck="false">
        <button type="submit">Fetch</button>
      </form>
      <div class="foot">
        <span>endpoint <code>/fetch?url=...</code></span>
        <span>relay never forgets a page</span>
      </div>
    </div>
  </div>
</body>
</html>
"""


@app.route('/')
def index():
    return INDEX


@app.route('/fetch')
def fetch():
    url = request.args.get('url', '')
    if not url:
        return 'give me ?url=...\n'
    low = url.lower()
    for b in BLOCKED:
        if b in low:
            return 'blocked: %s\n' % b
    if low.startswith('file:') or low.startswith('dict:'):
        return 'blocked scheme\n'
    try:
        out = subprocess.check_output(
            ['curl', '-s', '--max-time', '5', url],
            stderr=subprocess.STDOUT,
            timeout=8,
        )
        return out, 200, {'Content-Type': 'text/plain'}
    except subprocess.CalledProcessError as e:
        return 'curl error: %s\n' % e.output.decode(errors='replace')
    except Exception as e:
        return 'error: %s\n' % e


if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8080')))
