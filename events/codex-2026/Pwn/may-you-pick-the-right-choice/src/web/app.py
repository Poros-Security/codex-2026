import os
import redis
from flask import Flask, abort, send_file

app = Flask(__name__)
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
INSTANCE_ID = os.environ.get("INSTANCE_ID", "default")
store = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)

IMAGES = {"money": "private/money.png", "longevity": "private/longevity.png", "wise_mind": "private/wise_mind.png", "love": "private/love.png", "food": "private/food.png"}

LOCKED_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Second Chance · Locked</title><style>
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;color:#e8eefc;background:radial-gradient(circle at 20% 10%,#263b70 0,transparent 35%),#0b1020}.card{width:min(92vw,620px);padding:44px;text-align:center;border:1px solid #2d3d68;border-radius:24px;background:rgba(16,25,49,.9);box-shadow:0 24px 80px #0008}.mark{margin:0 auto 20px;width:58px;height:58px;display:grid;place-items:center;border-radius:18px;background:#7c5cff;font-size:28px;box-shadow:0 0 32px #7c5caa}h1{margin:0 0 12px;font-size:clamp(28px,5vw,42px);letter-spacing:-.04em}p{margin:0;color:#9eacce;line-height:1.7}.status{display:inline-flex;gap:8px;align-items:center;margin-top:28px;padding:9px 14px;border-radius:999px;color:#ffc978;background:#3a2b18;font-size:13px}.dot{width:8px;height:8px;border-radius:50%;background:#f5a742;box-shadow:0 0 12px #f5a742}
</style></head><body><main class="card"><div class="mark">✦</div><h1>Second Chance</h1><p>Your result is still locked.<br>Complete the challenge to reveal the choice waiting for you.</p><div class="status"><span class="dot"></span>Awaiting a valid result</div></main></body></html>"""

RESULT_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Second Chance · Result</title><style>
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;color:#e8eefc;background:radial-gradient(circle at 80% 15%,#314b82 0,transparent 35%),#0b1020}.card{width:min(92vw,760px);padding:34px;text-align:center;border:1px solid #2d3d68;border-radius:24px;background:rgba(16,25,49,.92);box-shadow:0 24px 80px #0008}.eyebrow{color:#a99aff;font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}h1{margin:8px 0;font-size:clamp(28px,5vw,44px);letter-spacing:-.04em}p{margin:0 0 26px;color:#9eacce}.result{padding:12px;border-radius:16px;background:#080d1a;border:1px solid #27365d}img{display:block;width:100%;height:auto;border-radius:10px}footer{margin-top:20px;color:#7182a8;font-size:12px}
</style></head><body><main class="card"><div class="eyebrow">Your choice has been recorded</div><h1>The path is revealed</h1><p>Every wish has a consequence. This is yours.</p><div class="result"><img src="/image" alt="Challenge result"></div><footer>Second Chance · Refresh after completing the challenge</footer></main></body></html>"""

@app.get("/")
def index():
    if store.get(f"result:{INSTANCE_ID}") is None:
        return LOCKED_PAGE
    return RESULT_PAGE

@app.get("/image")
def image():
    choice = store.get(f"result:{INSTANCE_ID}")
    if choice is None:
        abort(403)
    path = {b"money": "private/money.png", b"longevity": "private/longevity.png", b"wise_mind": "private/wise_mind.png", b"love": "private/love.png", b"food": "private/food.png"}.get(choice)
    if path is None:
        abort(403)
    response = send_file(path, mimetype="image/png")
    response.headers["Cache-Control"] = "no-store"
    return response