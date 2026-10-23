import time
from pathlib import Path

from flask import Flask, jsonify, render_template

app = Flask(__name__)

FLAG = Path("/flag.txt").read_text(encoding="utf-8").strip()
INITIAL_CREDITS = 100
CLAIM_COST = 100
REQUIRED_CLAIMS = 5

credits = INITIAL_CREDITS
claims = 0


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    return jsonify(credits=credits, claims=claims, claim_cost=CLAIM_COST)


@app.post("/api/claim")
def claim():
    global credits, claims
    if credits < CLAIM_COST:
        return jsonify(ok=False, message="Kredit tidak cukup."), 400

    time.sleep(0.25)
    credits -= CLAIM_COST
    claims += 1
    return jsonify(ok=True, message="Voucher berhasil diklaim.", claims=claims)


@app.get("/reward")
def reward():
    # Re-read in case Whale FLAG was written just before start
    flag = Path("/flag.txt").read_text(encoding="utf-8").strip()
    return render_template("preview.html", unlocked=claims >= REQUIRED_CLAIMS, flag=flag)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
