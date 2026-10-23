import os
import redis
from flask import Flask, abort, request
app = Flask(__name__)
KEY = os.environ["RESULT_KEY"]
INSTANCE_ID = os.environ.get("INSTANCE_ID", "default")
store = redis.Redis(host=os.environ.get("REDIS_HOST", "redis"), port=int(os.environ.get("REDIS_PORT", "6379")), decode_responses=False)
ALLOWED = {"money", "longevity", "wise_mind", "love", "food"}
@app.post("/internal/result/<choice>")
def set_result(choice: str):
    if request.headers.get("X-Internal-Key") != KEY: abort(403)
    if choice not in ALLOWED: abort(404)
    store.set(f"result:{INSTANCE_ID}", choice)
    return "", 204
@app.get("/health")
def health(): return "ok", 200