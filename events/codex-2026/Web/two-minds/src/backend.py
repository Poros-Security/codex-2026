#!/usr/bin/env python3
"""Two Minds — origin server (Transfer-Encoding framing, no ACL).

The origin is the "records office" of a government immigration portal.
Public pages: home, about, and a working application-status lookup.
/admin is the internal staff console (holds the flag) — no ACL here.
"""
import socket
import threading
from urllib.parse import parse_qs

FLAG = open('/flag.txt').read().strip().encode()

# In-memory "records" for the public status-lookup function.
RECORDS = {
    'DBMC-2026-0042': 'APPROVED — permit issued',
    'DBMC-2026-0117': 'PENDING — under review',
    'DBMC-2026-0331': 'REJECTED — incomplete documents',
    'DBMC-2026-0505': 'APPROVED — awaiting biometrics',
}

CSS = """
:root{--bg:#0a1220;--panel:#0f1a2e;--panel2:#13213a;--fg:#e8ecf4;
      --muted:#93a1b8;--border:#22334f;--gold:#d4a94a;--gold2:#b8892f;
      --blue:#5b8dd9;--ok:#3fbf7f;--warn:#e0a33b;--bad:#e06a5a}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Georgia,"Times New Roman",serif;background:var(--bg);color:var(--fg);
     min-height:100vh;display:flex;flex-direction:column;
     background-image:radial-gradient(circle at 15% 0%,rgba(91,141,217,.10),transparent 45%),
                      radial-gradient(circle at 90% 100%,rgba(212,169,74,.08),transparent 45%)}
a{color:var(--gold);text-decoration:none}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace}
.topbar{border-bottom:1px solid var(--border);background:linear-gradient(180deg,#0c1626,#0a1220);
        padding:.7rem 2rem;display:flex;align-items:center;gap:.9rem}
.emblem{width:2.2rem;height:2.2rem;border-radius:50%;border:2px solid var(--gold);
        display:flex;align-items:center;justify-content:center;color:var(--gold);
        font-weight:700;font-size:.9rem;letter-spacing:.02em;flex:none}
.agency{font-size:1rem;font-weight:700;letter-spacing:.04em;color:var(--fg)}
.agency small{display:block;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.62rem;
        letter-spacing:.14em;color:var(--muted);font-weight:400}
.nav{margin-left:auto;display:flex;gap:1.4rem;font-size:.86rem;letter-spacing:.03em}
.nav a{padding:.3rem .2rem;border-bottom:1px solid transparent}
.nav a:hover{border-color:var(--gold);color:var(--fg)}
.wrap{width:100%;max-width:64rem;margin:0 auto;padding:2.5rem 2rem;flex:1}
.hero{border-bottom:3px double var(--border);padding-bottom:1.6rem}
.hero .kicker{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.7rem;
        letter-spacing:.2em;color:var(--gold);text-transform:uppercase}
h1{font-size:2.3rem;font-weight:700;letter-spacing:-.01em;margin-top:.6rem;line-height:1.15}
.hero .lede{color:var(--muted);font-size:1rem;line-height:1.7;margin-top:.8rem;max-width:46rem}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-top:2rem}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:.6rem;padding:1.4rem 1.5rem}
.panel h3{font-size:1rem;letter-spacing:.02em;color:var(--fg)}
.panel p{color:var(--muted);font-size:.9rem;line-height:1.65;margin-top:.5rem}
.panel .tag{display:inline-block;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.66rem;
        letter-spacing:.08em;text-transform:uppercase;color:var(--gold);
        border:1px solid var(--border);border-radius:.3rem;padding:.18rem .5rem;margin-top:.8rem}
.notice{margin-top:2rem;background:var(--panel2);border:1px solid var(--border);
        border-radius:.6rem;padding:1.2rem 1.4rem;font-size:.88rem;color:var(--muted);line-height:1.7}
.notice b{color:var(--fg);font-weight:600}
.footer{border-top:1px solid var(--border);padding:1rem 2rem;display:flex;justify-content:space-between;
        font-size:.75rem;color:var(--muted);letter-spacing:.03em;flex-wrap:wrap;gap:.5rem}
form{display:flex;gap:.6rem;margin-top:1rem;flex-wrap:wrap}
input{flex:1;min-width:14rem;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9rem;padding:.6rem .8rem;
      background:#0a1420;border:1px solid var(--border);border-radius:.4rem;color:var(--fg);outline:none}
input:focus{border-color:var(--gold)}
button{font-family:inherit;font-size:.88rem;font-weight:700;letter-spacing:.04em;color:#0a1220;
       background:linear-gradient(135deg,var(--gold),var(--gold2));border:none;border-radius:.4rem;
       padding:.6rem 1.2rem;cursor:pointer}
button:hover{filter:brightness(1.08)}
.result{margin-top:1.1rem;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9rem;
        padding:.9rem 1rem;border-radius:.4rem;border:1px solid var(--border);background:#0a1420}
.result.ok{color:var(--ok)} .result.warn{color:var(--warn)}
.result.bad{color:var(--bad)} .result.none{color:var(--muted)}
"""

def _shell(title, kicker, body_html, foot='records office v1.9'):
    return ("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — Department of Border &amp; Migration Control</title>
<style>%s</style></head><body>
<div class="topbar">
  <div class="emblem">DB</div>
  <div class="agency">Department of Border &amp; Migration Control<small>KEMENTERIAN IMIGRASI — REPUBLIC DIVISION</small></div>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/status">Check Status</a>
    <a href="/about">About</a>
  </div>
</div>
<div class="wrap">%s</div>
<div class="footer">
  <span>&copy; 2026 Department of Border &amp; Migration Control</span>
  <span class="mono">%s</span>
</div>
</body></html>""" % (title, CSS, body_html, foot)).encode()


def home_page():
    body = """
  <div class="hero">
    <div class="kicker">Official Government Portal</div>
    <h1>Every crossing, every record,<br>kept in order.</h1>
    <p class="lede">The Department of Border &amp; Migration Control manages entry
    permits, residency records, and clearance for every traveler who passes the
    national boundary. Submit an application, receive a reference number, and
    track its progress here.</p>
  </div>
  <div class="grid">
    <div class="panel">
      <h3>Check an application</h3>
      <p>Enter the reference number issued at submission. Records are consulted
      live against the central office.</p>
      <form action="/status" method="get">
        <input name="ref" placeholder="DBMC-2026-XXXX" spellcheck="false">
        <button>Check</button>
      </form>
      <span class="tag">public records interface</span>
    </div>
    <div class="panel">
      <h3>Apply for entry</h3>
      <p>New applications are received at the consular counter. Bring a valid
      identity document and a declared purpose of travel.</p>
      <p>Reference numbers are issued within one working day.</p>
      <span class="tag">counter service — weekdays</span>
    </div>
  </div>
  <div class="notice">
    <b>Notice to applicants:</b> all requests are received at the public edge gate
    and forwarded to the records office for processing. The records office is an
    internal system and is not reachable from the public network. Staff access the
    internal console through a dedicated administrative channel.
  </div>
"""
    return _shell('Home', 'Official Government Portal', body, 'gateway v4.2 — records office v1.9')


def about_page():
    body = """
  <div class="hero">
    <div class="kicker">About the Department</div>
    <h1>Two systems. One border.</h1>
    <p class="lede">The department runs on two layers of infrastructure. The
    public edge gate receives every request and decides what may pass to the
    records office. The records office holds the actual data and answers only
    through the gate.</p>
  </div>
  <div class="grid">
    <div class="panel">
      <h3>Edge Gate</h3>
      <p>The outermost boundary. It inspects each request, filters traffic, and
      forwards what is permitted. It never holds records itself.</p>
    </div>
    <div class="panel">
      <h3>Records Office</h3>
      <p>The internal origin. It stores applications, permits, and clearance
      files. It trusts the gate to have vetted whatever reaches it.</p>
    </div>
  </div>
  <div class="notice">
    The two systems were built by different teams and document requests
    differently. Both are maintained for legacy compatibility. This is an
    accepted, known difference in the department's architecture.
  </div>
"""
    return _shell('About', 'About the Department', body)


def status_page(ref=None):
    if ref is None or ref.strip() == '':
        res = '<div class="result none">enter a reference number to begin</div>'
        val_attr = ''
    else:
        key = ref.strip().upper()
        val_attr = ref.strip()
        if key in RECORDS:
            val = RECORDS[key]
            cls = 'ok' if 'APPROVED' in val else ('warn' if 'PENDING' in val else 'bad')
            res = '<div class="result %s">%s — %s</div>' % (cls, key, val)
        else:
            res = '<div class="result none">%s — no record found</div>' % key
    body = """
  <div class="hero">
    <div class="kicker">Records Interface</div>
    <h1>Application status</h1>
    <p class="lede">Consult the central records office for the current state of
    an entry-permit application.</p>
    <form action="/status" method="get">
      <input name="ref" placeholder="DBMC-2026-XXXX" value="%s" spellcheck="false">
      <button>Check</button>
    </form>
    %s
  </div>
""" % (val_attr, res)
    return _shell('Check Status', 'Records Interface', body, 'records consulted live')


def route(method, path):
    path_only = path.split('?', 1)[0]
    query = parse_qs(path.split('?', 1)[1]) if '?' in path else {}
    if path_only == '/admin':
        return b'200 OK', FLAG + b'\n', 'text/plain; charset=utf-8'
    if path_only == '/':
        return b'200 OK', home_page(), 'text/html; charset=utf-8'
    if path_only == '/about':
        return b'200 OK', about_page(), 'text/html; charset=utf-8'
    if path_only == '/status':
        ref = query.get('ref', [None])[0]
        return b'200 OK', status_page(ref), 'text/html; charset=utf-8'
    return b'404 Not Found', b'not found\n', 'text/plain; charset=utf-8'


def read_chunked(sock, buf):
    body = b''
    while True:
        while b'\r\n' not in buf:
            d = sock.recv(4096)
            if not d:
                return body, buf
            buf += d
        line, buf = buf.split(b'\r\n', 1)
        size = int(line.split(b';')[0].strip(), 16)
        if size == 0:
            while len(buf) < 2:
                d = sock.recv(4096)
                if not d:
                    return body, buf
                buf += d
            return body, buf[2:]
        while len(buf) < size + 2:
            d = sock.recv(4096)
            if not d:
                return body, buf
            buf += d
        body += buf[:size]
        buf = buf[size + 2:]


def handle(sock):
    buf = b''
    try:
        while True:
            while b'\r\n\r\n' not in buf:
                d = sock.recv(4096)
                if not d:
                    return
                buf += d
            head, buf = buf.split(b'\r\n\r\n', 1)
            lines = head.decode('latin1').split('\r\n')
            parts = lines[0].split(' ')
            method = parts[0]
            path = parts[1] if len(parts) > 1 else '/'
            headers = {}
            for l in lines[1:]:
                if ':' in l:
                    k, v = l.split(':', 1)
                    headers[k.strip().lower()] = v.strip()
            if 'transfer-encoding' in headers:
                _, buf = read_chunked(sock, buf)
            elif 'content-length' in headers:
                cl = int(headers['content-length'])
                while len(buf) < cl:
                    d = sock.recv(4096)
                    if not d:
                        return
                    buf += d
                buf = buf[cl:]
            status, content, ctype = route(method, path)
            resp = (b'HTTP/1.1 ' + status +
                    b'\r\nContent-Length: ' + str(len(content)).encode() +
                    b'\r\nContent-Type: ' + ctype.encode() +
                    b'\r\nConnection: keep-alive\r\n\r\n' + content)
            sock.sendall(resp)
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', 9000))
    srv.listen(128)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()


if __name__ == '__main__':
    main()
