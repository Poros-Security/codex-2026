#!/usr/bin/env python3
"""Flowforge — AI workflow platform (vulnerable).

Modeled on CVE-2026-33017: the public "marketplace build" endpoint executes
attacker-supplied Python code unsandboxed.
"""
import contextlib
import io
import time
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)

FLAG = open('/flag.txt').read().strip()

TOKENS = set()
FLOWS = {}
STARTED = time.time()

BLACKLIST = [
    'os.system', 'subprocess', 'open(', '__', 'eval', 'exec', 'importlib',
]

TEMPLATES = {
    'hello-world': {
        'id': 'hello-world',
        'name': 'Hello World',
        'description': 'The simplest possible flow. Prints a greeting.',
        'author': 'flowforge-team',
        'category': 'getting-started',
        'data': {'nodes': [{'id': 'node-1', 'data': {'type': 'code',
                 'template': {'code': {'value': "print('hello, world')"}}}}]},
    },
    'csv-cleaner': {
        'id': 'csv-cleaner',
        'name': 'CSV Cleaner',
        'description': 'Normalizes a CSV string by trimming whitespace.',
        'author': 'rhea',
        'category': 'data',
        'data': {'nodes': [
            {'id': 'n-in', 'data': {'type': 'input', 'template': {'name': {'value': 'raw_csv'}}}},
            {'id': 'n-code', 'data': {'type': 'code',
             'template': {'code': {'value': "print('cleaning csv...')"}}}},
        ]},
    },
    'webhook-ping': {
        'id': 'webhook-ping',
        'name': 'Webhook Ping',
        'description': 'Responds to a webhook with a status message.',
        'author': 'devon',
        'category': 'integrations',
        'data': {'nodes': [
            {'id': 'n-hook', 'data': {'type': 'webhook', 'template': {'path': {'value': '/ping'}}}},
            {'id': 'n-code', 'data': {'type': 'code',
             'template': {'code': {'value': "print('pong')"}}}},
        ]},
    },
}

MARKETPLACE = [
    {'id': 'invoice-parser', 'name': 'Invoice Parser', 'author': 'meredith',
     'desc': 'Extract line items from invoice PDFs and push them to a spreadsheet.',
     'tags': ['python', 'ocr'], 'runs': 18420, 'hot': False},
    {'id': 'support-triage', 'name': 'Support Triage', 'author': 'devon',
     'desc': 'Route inbound tickets to the right team by reading intent.',
     'tags': ['nlp', 'slack'], 'runs': 33902, 'hot': True},
    {'id': 'lead-scorer', 'name': 'Lead Scorer', 'author': 'priya',
     'desc': 'Score and rank incoming leads every hour.',
     'tags': ['python', 'crm'], 'runs': 8812, 'hot': False},
    {'id': 'sentiment-watch', 'name': 'Sentiment Watch', 'author': 'kofi',
     'desc': 'Track brand sentiment across feeds and alert on spikes.',
     'tags': ['nlp', 'alerts'], 'runs': 27110, 'hot': True},
    {'id': 'data-sweeper', 'name': 'Data Sweeper', 'author': 'rhea',
     'desc': 'Deduplicate and normalize messy CSV dumps.',
     'tags': ['python'], 'runs': 15903, 'hot': False},
    {'id': 'oncall-router', 'name': 'Oncall Router', 'author': 'jules',
     'desc': 'Page the engineer on call based on error signatures.',
     'tags': ['python', 'pager'], 'runs': 4210, 'hot': False},
]

CSS = """
:root{--bg:#0b0f17;--panel:#111827;--panel2:#162032;--fg:#e7ecf5;
      --muted:#8ea0bb;--border:#23304a;--teal:#2dd4bf;--teal2:#0ea5e9;
      --violet:#8b5cf6;--amber:#f59e0b;--pink:#ec4899}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,sans-serif;
     background:var(--bg);color:var(--fg);min-height:100vh;display:flex;flex-direction:column;
     background-image:radial-gradient(circle at 12% 0%,rgba(45,212,191,.10),transparent 45%),
                      radial-gradient(circle at 90% 100%,rgba(139,92,246,.10),transparent 45%)}
a{color:var(--teal);text-decoration:none}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace}
.topbar{border-bottom:1px solid var(--border);padding:.8rem 2rem;display:flex;align-items:center;gap:.7rem;flex-wrap:wrap}
.logo{width:2rem;height:2rem;border-radius:.45rem;background:linear-gradient(135deg,var(--teal),var(--teal2));
      display:flex;align-items:center;justify-content:center;font-weight:800;color:#04121a;flex:none}
.brand{font-weight:700;letter-spacing:-.01em}
.brand small{display:block;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.6rem;
        letter-spacing:.14em;color:var(--muted);font-weight:400}
.nav{margin-left:auto;display:flex;gap:1.2rem;font-size:.84rem;letter-spacing:.02em;flex-wrap:wrap}
.nav a{padding:.3rem .15rem;border-bottom:1px solid transparent;color:var(--muted)}
.nav a:hover{border-color:var(--teal);color:var(--fg)}
.nav a.on{color:var(--fg);border-color:var(--teal)}
.wrap{max-width:68rem;margin:0 auto;padding:2.6rem 2rem;flex:1;width:100%}
.kicker{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.7rem;letter-spacing:.2em;
        color:var(--teal);text-transform:uppercase}
h1{font-size:2.5rem;font-weight:800;letter-spacing:-.03em;margin-top:.6rem;line-height:1.1}
h1 span{background:linear-gradient(90deg,var(--teal),var(--violet));
        -webkit-background-clip:text;background-clip:text;color:transparent}
.lede{color:var(--muted);font-size:1.03rem;line-height:1.7;margin-top:.9rem;max-width:48rem}
.cta{margin-top:1.4rem;display:flex;gap:.8rem;flex-wrap:wrap}
.btn{display:inline-block;font-size:.9rem;font-weight:700;letter-spacing:.02em;padding:.6rem 1.3rem;
     border-radius:.5rem;cursor:pointer}
.btn.primary{color:#04121a;background:linear-gradient(135deg,var(--teal),var(--teal2))}
.btn.ghost{color:var(--fg);border:1px solid var(--border);background:transparent}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1.1rem;margin-top:2.4rem}
.grid.two{grid-template-columns:1fr 1fr}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:.7rem;padding:1.3rem 1.4rem}
.panel .ic{font-size:1.2rem}
.panel h3{font-size:1rem;letter-spacing:.01em;margin-top:.5rem}
.panel p{color:var(--muted);font-size:.88rem;line-height:1.6;margin-top:.45rem}
.tag{display:inline-block;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.63rem;
        letter-spacing:.08em;text-transform:uppercase;color:var(--amber);
        border:1px solid var(--border);border-radius:.3rem;padding:.18rem .5rem;margin-top:.8rem}
.steps{margin-top:2.4rem;display:grid;grid-template-columns:repeat(3,1fr);gap:1.1rem}
.step{background:var(--panel);border:1px solid var(--border);border-radius:.7rem;padding:1.3rem 1.4rem;position:relative}
.step .n{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.7rem;color:var(--teal);letter-spacing:.1em}
.step h4{font-size:.95rem;margin-top:.5rem}
.step p{color:var(--muted);font-size:.85rem;line-height:1.6;margin-top:.4rem}
.doc{margin-top:1.4rem;background:var(--panel2);border:1px solid var(--border);border-radius:.7rem;padding:1.4rem 1.5rem}
.doc h3{font-size:.9rem;letter-spacing:.04em;text-transform:uppercase;color:var(--teal)}
.doc p{color:var(--muted);font-size:.9rem;line-height:1.7;margin-top:.6rem}
.doc pre{background:#0a0f18;border:1px solid var(--border);border-radius:.5rem;padding:1rem 1.1rem;
     margin-top:.8rem;overflow-x:auto;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.8rem;
     line-height:1.55;color:#cbd5e1}
.doc code.inline{font-family:ui-monospace,Menlo,Consolas,monospace;color:#cbd5e1;font-size:.85em}
table{width:100%;border-collapse:collapse;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.82rem}
td{padding:.45rem .35rem;border-bottom:1px solid var(--border);color:var(--muted)}
td:first-child{color:var(--fg)}
tr:last-child td{border-bottom:none}
.mkt{display:grid;grid-template-columns:repeat(3,1fr);gap:1.1rem;margin-top:1.6rem}
.flowcard{background:var(--panel);border:1px solid var(--border);border-radius:.7rem;padding:1.2rem 1.3rem}
.flowcard .nm{font-weight:700;font-size:.95rem}
.flowcard .by{color:var(--muted);font-size:.78rem;margin-top:.25rem}
.flowcard .desc{color:var(--muted);font-size:.85rem;line-height:1.55;margin-top:.6rem}
.flowcard .meta{margin-top:.8rem;display:flex;gap:.5rem;flex-wrap:wrap}
.flowcard .runs{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.7rem;color:var(--muted);margin-top:.7rem}
.pill{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.63rem;letter-spacing:.06em;
      text-transform:uppercase;color:var(--teal);border:1px solid var(--border);
      border-radius:9999px;padding:.16rem .55rem}
.pill.hot{color:var(--amber)}
.statusbar{display:flex;align-items:center;gap:.5rem;margin-top:1.6rem;padding:1rem 1.2rem;
        background:var(--panel);border:1px solid var(--border);border-radius:.7rem;font-size:.85rem;color:var(--muted)}
.statusbar .dot{width:.55rem;height:.55rem;border-radius:9999px;background:#3fbf7f;animation:blink 1.6s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
.pricing{display:grid;grid-template-columns:repeat(3,1fr);gap:1.1rem;margin-top:2rem}
.plan{background:var(--panel);border:1px solid var(--border);border-radius:.7rem;padding:1.5rem 1.4rem;position:relative}
.plan.hot{border-color:var(--teal)}
.plan .nm{font-weight:700;font-size:1rem}
.plan .price{font-size:1.9rem;font-weight:800;letter-spacing:-.02em;margin-top:.6rem}
.plan .per{color:var(--muted);font-size:.8rem}
.plan ul{margin-top:1rem;list-style:none}
.plan li{color:var(--muted);font-size:.86rem;line-height:1.6;padding:.28rem 0}
.plan li::before{content:"\\2713 ";color:var(--teal);font-weight:700}
.plan .btn{margin-top:1.2rem;width:100%;text-align:center}
.badge-hot{position:absolute;top:-.6rem;right:1rem;background:var(--amber);color:#04121a;
        font-size:.62rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
        border-radius:9999px;padding:.2rem .6rem}
.builder{display:grid;grid-template-columns:2fr 1fr;gap:1.2rem;margin-top:1.8rem}
.canvas{background:var(--panel2);border:1px solid var(--border);border-radius:.7rem;padding:1.4rem;min-height:22rem;position:relative}
.cnode{background:var(--panel);border:1px solid var(--border);border-radius:.6rem;padding:1rem;max-width:20rem}
.cnode .nt{font-size:.78rem;font-weight:700;letter-spacing:.03em}
.cnode .nt.code{color:var(--amber)}
.cnode .nt.in{color:var(--teal)}
.cnode .nt.out{color:var(--violet)}
.cnode .nbody{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.72rem;color:var(--muted);
        margin-top:.5rem;line-height:1.5;word-break:break-all}
.edge{height:1.5rem;border-left:2px solid var(--border);margin:.2rem 0 .2rem 1rem}
.sidebar{background:var(--panel);border:1px solid var(--border);border-radius:.7rem;padding:1.3rem 1.4rem;height:fit-content}
.sidebar h4{font-size:.85rem;letter-spacing:.03em;text-transform:uppercase;color:var(--teal)}
.sidebar .palt{margin-top:.8rem;display:flex;flex-direction:column;gap:.5rem}
.pal{background:var(--panel2);border:1px solid var(--border);border-radius:.5rem;padding:.55rem .7rem;
        font-size:.82rem;color:var(--muted);cursor:pointer}
.pal:hover{border-color:var(--teal);color:var(--fg)}
.pal .k{font-weight:700;color:var(--fg)}
.uptime{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.82rem;color:var(--muted);margin-top:.6rem}
.footer{border-top:1px solid var(--border);padding:1rem 2rem;font-size:.75rem;color:var(--muted);
        display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem}
@media(max-width:760px){.grid,.steps,.mkt,.pricing,.builder{grid-template-columns:1fr}.grid.two{grid-template-columns:1fr}}
"""

NAV_LINKS = [('/', 'Home'), ('/builder', 'Builder'), ('/templates', 'Templates'),
             ('/marketplace', 'Marketplace'), ('/docs', 'Docs'),
             ('/pricing', 'Pricing'), ('/status', 'Status')]


def _page(title, kicker, inner, foot='forge v1.8.2'):
    nav_items = []
    for path, label in NAV_LINKS:
        cls = ' class="on"' if request.path == path else ''
        nav_items.append('<a href="%s"%s>%s</a>' % (path, cls, label))
    nav = ("""<div class="topbar">
  <div class="logo">F</div>
  <div class="brand">Flowforge<small>AI AUTOMATION FOR TEAMS</small></div>
  <div class="nav">%s</div>
</div>""" % ''.join(nav_items))
    return ("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — Flowforge</title>
<style>%s</style></head><body>
%s
<div class="wrap">%s</div>
<div class="footer">
  <span>&copy; 2026 Flowforge Inc. — San Francisco, CA</span>
  <span class="mono">%s</span>
</div>
</body></html>""" % (title, CSS, nav, inner, foot)).encode()


def home():
    inner = """
  <div class="kicker">AI automation platform</div>
  <h1>Forge the workflows that <span>run your business</span>.</h1>
  <p class="lede">Flowforge is where teams build, wire, and publish AI pipelines.
  Drag blocks together, drop in a little Python where you need it, and ship a
  working automation to production in minutes — not months.</p>
  <div class="cta">
    <a class="btn primary" href="/builder">Open the builder</a>
    <a class="btn ghost" href="/templates">Browse templates</a>
  </div>
  <div class="grid">
    <div class="panel">
      <div class="ic">&#9650;</div>
      <h3>Drag-and-drop builder</h3>
      <p>A flow is a graph of nodes. Wire inputs to outputs and the platform
      handles the plumbing.</p>
      <span class="tag">graph engine</span>
    </div>
    <div class="panel">
      <div class="ic">&#9851;</div>
      <h3>Custom code components</h3>
      <p>Every node can carry a custom component — a snippet of Python the
      platform runs for you when it assembles the flow.</p>
      <span class="tag">custom components</span>
    </div>
    <div class="panel">
      <div class="ic">&#8645;</div>
      <h3>One-click publish</h3>
      <p>Send a flow to the public marketplace and it is built and packaged for
      anyone to run. No login required to publish.</p>
      <span class="tag">public marketplace</span>
    </div>
  </div>
  <div class="steps">
    <div class="step"><div class="n">01 / CREATE</div>
      <h4>Start a flow</h4><p>Register a flow and get back a flow id. Takes one
      request.</p></div>
    <div class="step"><div class="n">02 / CONFIGURE</div>
      <h4>Write your nodes</h4><p>Fill each node's template. The
      <code class="inline">code</code> field is where custom logic lives.</p></div>
    <div class="step"><div class="n">03 / BUILD</div>
      <h4>Publish to the market</h4><p>The public build endpoint assembles the
      flow. Building runs the code.</p></div>
  </div>
"""
    return _page('Home', 'AI automation platform', inner)


def builder():
    inner = """
  <div class="kicker">Visual builder</div>
  <h1>Assemble your <span>flow</span>.</h1>
  <p class="lede">A flow is a graph. Add nodes from the palette, then wire them
  together. Custom code components carry a <code class="inline">code</code> field.</p>
  <div class="builder">
    <div class="canvas">
      <div class="cnode">
        <div class="nt in">INPUT — webhook</div>
        <div class="nbody">template.path = "/ping"</div>
      </div>
      <div class="edge"></div>
      <div class="cnode">
        <div class="nt code">CODE — custom component</div>
        <div class="nbody">template.code.value = "print('pong')"</div>
      </div>
      <div class="edge"></div>
      <div class="cnode">
        <div class="nt out">OUTPUT — response</div>
        <div class="nbody">template.status = 200</div>
      </div>
    </div>
    <div class="sidebar">
      <h4>Palette</h4>
      <div class="palt">
        <div class="pal"><span class="k">Input</span> — webhook, http, file</div>
        <div class="pal"><span class="k">Code</span> — custom component (Python)</div>
        <div class="pal"><span class="k">Model</span> — LLM call</div>
        <div class="pal"><span class="k">Output</span> — response, email, webhook</div>
      </div>
      <p class="uptime">graph engine — operational</p>
    </div>
  </div>
"""
    return _page('Builder', 'Visual builder', inner)


def templates():
    cards = ''
    for t in TEMPLATES.values():
        cards += ('<div class="flowcard"><div class="nm">%s</div><div class="by">by @%s</div>'
                  '<div class="desc">%s</div><div class="meta">'
                  '<span class="pill">%s</span><span class="pill">GET /api/v1/templates/%s</span>'
                  '</div></div>' % (t['name'], t['author'], t['description'],
                                    t['category'], t['id']))
    inner = """
  <div class="kicker">Template library</div>
  <h1>Start from a <span>template</span>.</h1>
  <p class="lede">Ready-made flow structures. Fetch any template's full
  definition from the API and remix it.</p>
  <div class="mkt">%s</div>
  <div class="doc">
    <h3>Fetch a template</h3>
    <p>Every template is exposed as a JSON object with the same shape a flow
    uses — including its <code class="inline">code</code> field:</p>
    <pre>GET /api/v1/templates/hello-world</pre>
  </div>
""" % cards
    return _page('Templates', 'Template library', inner)


def marketplace():
    cards = ''
    for f in MARKETPLACE:
        pills = ''.join('<span class="pill%s">%s</span>' % (' hot' if f['hot'] else '', t) for t in f['tags'])
        cards += ('<div class="flowcard"><div class="nm">%s</div><div class="by">by @%s</div>'
                  '<div class="desc">%s</div><div class="meta">%s</div>'
                  '<div class="runs">%d runs</div></div>'
                  % (f['name'], f['author'], f['desc'], pills, f['runs']))
    inner = """
  <div class="kicker">Marketplace</div>
  <h1>Public flows, <span>ready to run</span>.</h1>
  <p class="lede">Flows published by the community. Every one of them was built
  through the public build endpoint — assembled and packaged for anyone to use.</p>
  <div class="mkt">%s</div>
""" % cards
    return _page('Marketplace', 'Marketplace', inner)


def docs():
    inner = """
  <div class="kicker">Documentation</div>
  <h1>The <span>flow format</span>.</h1>
  <p class="lede">Everything on Flowforge is a flow: a JSON object with a list
  of nodes. Each node has a template, and a custom component template carries a
  <code class="inline">code</code> field containing Python.</p>
  <div class="doc">
    <h3>Flow object</h3>
    <pre>{
  "id": "&lt;flow_id&gt;",
  "name": "my-flow",
  "data": {
    "nodes": [
      {
        "id": "node-1",
        "data": {
          "type": "code",
          "template": {
            "code": { "value": "print('hello world')" }
          }
        }
      }
    ]
  }
}</pre>
    <p>The <code class="inline">code.value</code> string is executed when the
    flow is built. Standard library imports are permitted.</p>
  </div>
  <div class="doc">
    <h3>API reference</h3>
    <table>
      <tr><td>GET /api/v1/auto_login</td><td>obtain a session token</td></tr>
      <tr><td>POST /api/v1/flows/</td><td>create a flow (Bearer token)</td></tr>
      <tr><td>GET /api/v1/flows/&lt;id&gt;</td><td>read a flow's structure</td></tr>
      <tr><td>POST /api/v1/flows/&lt;id&gt;/run</td><td>run a flow</td></tr>
      <tr><td>POST /api/v1/flows/&lt;id&gt;/validate</td><td>validate a flow structure</td></tr>
      <tr><td>POST /api/v1/build_public_tmp/&lt;id&gt;/flow</td><td>build a flow for the marketplace</td></tr>
      <tr><td>GET /api/v1/templates/&lt;id&gt;</td><td>fetch a template</td></tr>
      <tr><td>GET /api/v1/marketplace</td><td>list marketplace flows</td></tr>
    </table>
    <p>The build endpoint asks for no token. It assembles a flow for public
    release. If you pass a <code class="inline">data</code> body, your flow
    definition is used instead of the stored one.</p>
  </div>
  <div class="doc">
    <h3>Safety filter</h3>
    <p>To keep dangerous code out of the marketplace, custom components are
    screened against a list of forbidden patterns before they run.</p>
  </div>
"""
    return _page('Docs', 'Documentation', inner)


def pricing():
    inner = """
  <div class="kicker">Pricing</div>
  <h1>Plans for <span>every team</span>.</h1>
  <p class="lede">Start free. Scale when you need to. Every plan includes
  unlimited public marketplace builds.</p>
  <div class="pricing">
    <div class="plan">
      <div class="nm">Starter</div>
      <div class="price">$0</div><div class="per">forever</div>
      <ul>
        <li>Up to 3 flows</li>
        <li>Public marketplace publishing</li>
        <li>Community support</li>
      </ul>
      <a class="btn ghost" href="/builder">Start free</a>
    </div>
    <div class="plan hot">
      <div class="badge-hot">Popular</div>
      <div class="nm">Team</div>
      <div class="price">$49</div><div class="per">per seat / month</div>
      <ul>
        <li>Unlimited flows</li>
        <li>Custom code components</li>
        <li>Team workspaces</li>
        <li>Priority support</li>
      </ul>
      <a class="btn primary" href="/builder">Choose Team</a>
    </div>
    <div class="plan">
      <div class="nm">Enterprise</div>
      <div class="price">Custom</div><div class="per">annual</div>
      <ul>
        <li>SSO &amp; audit logs</li>
        <li>Private marketplace</li>
        <li>Dedicated cluster</li>
        <li>99.99% SLA</li>
      </ul>
      <a class="btn ghost" href="/status">Contact sales</a>
    </div>
  </div>
"""
    return _page('Pricing', 'Pricing', inner)


def status():
    up = int(time.time() - STARTED)
    d, h = up // 86400, (up % 86400) // 3600
    m, s = (up % 3600) // 60, up % 60
    uptime = '%dd %dh %dm %ds' % (d, h, m, s) if d else '%dh %dm %ds' % (h, m, s)
    inner = """
  <div class="kicker">System status</div>
  <h1>All systems <span>operational</span>.</h1>
  <p class="lede">Current health of the Flowforge platform.</p>
  <div class="statusbar"><span class="dot"></span> Graph engine — operational</div>
  <div class="statusbar"><span class="dot"></span> Build pipeline — operational</div>
  <div class="statusbar"><span class="dot"></span> Public marketplace — operational</div>
  <div class="statusbar"><span class="dot"></span> Template library — operational</div>
  <div class="doc">
    <h3>Health &amp; version</h3>
    <table>
      <tr><td>uptime</td><td>%s</td></tr>
      <tr><td>version</td><td>forge v1.8.2</td></tr>
      <tr><td>GET /api/v1/health</td><td>machine-readable health</td></tr>
      <tr><td>GET /api/v1/version</td><td>machine-readable version</td></tr>
    </table>
  </div>
""" % uptime
    return _page('Status', 'System status', inner)


def check_code(code):
    c = code.lower()
    for b in BLACKLIST:
        if b in c:
            return b
    return None


def make_flow(name):
    fid = uuid.uuid4().hex
    FLOWS[fid] = {
        'id': fid,
        'name': name,
        'data': {
            'nodes': [
                {
                    'id': 'node-1',
                    'data': {
                        'type': 'code',
                        'template': {'code': {'value': '', 'type': 'code'}},
                    },
                }
            ],
        },
    }
    return FLOWS[fid]


def extract_code(flow):
    codes = []
    try:
        for node in flow['data']['nodes']:
            c = node['data']['template']['code']['value']
            if c and c.strip():
                codes.append(c)
    except Exception:
        pass
    return codes


def run_build(flow):
    codes = extract_code(flow)
    if not codes:
        return 'flow built — no custom code', ''
    out = io.StringIO()
    for code in codes:
        bad = check_code(code)
        if bad:
            return 'build refused: blocked pattern %r' % bad, ''
        try:
            with contextlib.redirect_stdout(out):
                exec(compile(code, '<flow-node>', 'exec'), {'__name__': '__main__'})
        except Exception as e:
            return 'build failed: %s' % e, out.getvalue()
    return 'flow built successfully', out.getvalue()


@app.route('/')
def index():
    return home(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/builder')
def builder_page():
    return builder(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/templates')
def templates_page():
    return templates(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/marketplace')
def marketplace_page():
    return marketplace(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/docs')
def docs_page():
    return docs(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/pricing')
def pricing_page():
    return pricing(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/status')
def status_page():
    return status(), 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/api/v1/health')
def health():
    return jsonify({'status': 'ok', 'uptime_seconds': int(time.time() - STARTED),
                    'version': 'forge v1.8.2'})


@app.route('/api/v1/version')
def version():
    return jsonify({'name': 'flowforge', 'version': '1.8.2', 'channel': 'stable'})


@app.route('/api/v1/templates/<tid>')
def get_template(tid):
    if tid not in TEMPLATES:
        return jsonify({'error': 'template not found'}), 404
    return jsonify(TEMPLATES[tid])


@app.route('/api/v1/marketplace')
def marketplace_api():
    return jsonify({'flows': MARKETPLACE})


@app.route('/api/v1/me')
def me():
    auth = request.headers.get('Authorization', '')
    tok = auth[7:].strip() if auth.startswith('Bearer ') else ''
    if tok in TOKENS:
        return jsonify({'authenticated': True, 'plan': 'starter', 'flows': len(FLOWS)})
    return jsonify({'authenticated': False, 'plan': 'guest'})


@app.route('/api/v1/auto_login')
def auto_login():
    tok = uuid.uuid4().hex
    TOKENS.add(tok)
    return jsonify({'access_token': tok, 'token_type': 'bearer'})


@app.route('/api/v1/flows/', methods=['POST'])
def create_flow():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer ') or auth[7:].strip() not in TOKENS:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    flow = make_flow(data.get('name', 'untitled'))
    return jsonify({'id': flow['id'], 'name': flow['name']})


@app.route('/api/v1/flows/<fid>')
def get_flow(fid):
    if fid not in FLOWS:
        return jsonify({'error': 'not found'}), 404
    return jsonify(FLOWS[fid])


@app.route('/api/v1/flows/<fid>/run', methods=['POST'])
def run_flow(fid):
    if fid not in FLOWS:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'run_id': uuid.uuid4().hex, 'status': 'scheduled',
                    'message': 'flow queued for execution'})


@app.route('/api/v1/flows/<fid>/validate', methods=['POST'])
def validate_flow(fid):
    body = request.get_json(silent=True) or {}
    nodes = (body.get('data') or {}).get('nodes', [])
    errors = []
    if not nodes:
        errors.append('no nodes')
    for n in nodes:
        t = (n.get('data') or {}).get('type')
        if t not in ('code', 'input', 'output', 'webhook', 'model'):
            errors.append('node %s: unknown type' % n.get('id', '?'))
    if errors:
        return jsonify({'valid': False, 'errors': errors}), 422
    return jsonify({'valid': True, 'nodes': len(nodes)})


@app.route('/api/v1/build_public_tmp/<fid>/flow', methods=['POST'])
def build_public(fid):
    body = request.get_json(silent=True) or {}
    if 'data' in body:
        flow = {'id': fid, 'data': body['data']}
    elif fid in FLOWS:
        flow = FLOWS[fid]
    else:
        return jsonify({'error': 'not found'}), 404
    status, log = run_build(flow)
    return jsonify({'build_id': uuid.uuid4().hex, 'status': status, 'log': log})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
