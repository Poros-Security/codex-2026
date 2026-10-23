#!/usr/bin/env python3
"""
Whisper Well
------------
An ancient well that echoes whatever you whisper into it.
"""
import subprocess

from flask import Flask, request, render_template_string

app = Flask(__name__)

# The well's guard: it refuses the obvious shell metacharacters.
FORBIDDEN = [';', '&', '|', '>', '<']


def inspector(utterance):
    return not any(ch in utterance for ch in FORBIDDEN)


INDEX_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Whisper Well</title>
  <style>
    body { font-family: monospace; background: #0d1117; color: #c9d1d9;
           display: flex; flex-direction: column; align-items: center;
           padding-top: 3rem; }
    pre { color: #58a6ff; line-height: 1.15; }
    form { margin-top: 1.5rem; }
    input[type=text] { width: 24rem; padding: .4rem .6rem; font-family: monospace;
                       background: #161b22; color: #c9d1d9; border: 1px solid #30363d;
                       border-radius: 4px; }
    button { padding: .4rem .9rem; margin-left: .4rem; font-family: monospace;
             background: #238636; color: #fff; border: none; border-radius: 4px;
             cursor: pointer; }
    .muted { color: #8b949e; margin-top: 2rem; font-size: .85rem; }
  </style>
</head>
<body>
<pre>
        .
       / \
      |   |
       \_/
     .--|--.
    /   |   \
   ~ Whisper Well ~
</pre>
<p>Speak into the well and it shall echo back.</p>
<form method="post" action="/whisper">
  <input type="text" name="msg" placeholder="type your whisper..." autofocus>
  <button type="submit">Whisper</button>
</form>
<p class="muted">The well remembers every word. It never forgets.</p>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/whisper', methods=['GET', 'POST'])
def whisper():
    msg = request.form.get('msg') or request.args.get('msg') or ''
    if not msg:
        return 'The well waits in silence...\n'
    if not inspector(msg):
        return 'The well rejects your utterance: forbidden character.\n'
    try:
        out = subprocess.check_output(
            'echo ' + msg,
            shell=True,
            stderr=subprocess.STDOUT,
            timeout=3,
        )
        return out.decode(errors='replace')
    except Exception as e:
        return 'The well chokes: %s\n' % e


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
