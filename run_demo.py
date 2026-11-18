"""Local red/blue loop: scan, patch, rescan. Attacks 127.0.0.1 only."""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.blue_agent import respond  # noqa: E402
from agents.red_agent import scan  # noqa: E402

PORT = int(os.environ.get("TARGET_PORT", "8081"))
HERE = os.path.dirname(os.path.abspath(__file__))


def wait_up():
    for _ in range(30):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1)
            return
        except Exception:
            time.sleep(0.3)
    raise SystemExit("target did not start")


def main():
    patch_file = os.path.join(tempfile.mkdtemp(), "patches.json")
    env = dict(os.environ, PATCH_FILE=patch_file)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "target", "vulnerable_app.py"), str(PORT)],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_up()
        before = scan(PORT)
        print("RED: findings before patch:", [f["id"] for f in before["findings"]])
        actions = respond(before, patch_file)
        for a in actions:
            print("BLUE:", a["finding"], "->", a.get("patch"))
        after = scan(PORT)
        print("RED (retest): findings after patch:", [f["id"] for f in after["findings"]])
        ok = bool(before["findings"]) and not after["findings"]
        print("RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
