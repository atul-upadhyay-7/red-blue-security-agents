"""Small, deliberately weak web app used as the practice target.

It listens on 127.0.0.1 only. Weaknesses are on by default; the blue agent
turns them off by writing to patches.json.
"""
import json
import os
import sys

from flask import Flask, abort, make_response

HERE = os.path.dirname(os.path.abspath(__file__))
PATCH_FILE = os.environ.get("PATCH_FILE", os.path.join(HERE, "patches.json"))

app = Flask(__name__)


def patches():
    try:
        with open(PATCH_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


@app.after_request
def add_headers(resp):
    p = patches()
    if not p.get("restrict_cors"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Credentials"] = "true"
    if p.get("block_framing"):
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    else:
        resp.headers["X-Frame-Options"] = "ALLOWALL"
        resp.headers["Content-Security-Policy"] = "default-src 'self'"
    if not p.get("hide_powered_by"):
        resp.headers["X-Powered-By"] = "Flask/demo"
    return resp


@app.route("/")
def index():
    resp = make_response("demo shop")
    if patches().get("harden_cookie"):
        # written by hand so the flag spelling is exactly what Nettacker looks for
        resp.headers.add("Set-Cookie",
                         "session=demo; Path=/; Max-Age=3600; HttpOnly; secure; SameSite=Strict")
    else:
        resp.set_cookie("session", "demo")
    return resp


@app.route("/admin")
def admin():
    if patches().get("lock_admin"):
        abort(403)
    return "admin panel"


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    app.run("127.0.0.1", port)
