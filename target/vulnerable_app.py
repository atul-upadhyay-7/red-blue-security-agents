"""Small, deliberately weak web app used as the practice target.

It listens on 127.0.0.1 only. Weaknesses are on by default; the blue agent
turns them off by writing to patches.json.
"""
import json
import os
import sys

from flask import Flask, abort

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
    return resp


@app.route("/")
def index():
    return "demo shop"


@app.route("/admin")
def admin():
    if patches().get("lock_admin"):
        abort(403)
    return "admin panel"


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    app.run("127.0.0.1", port)
