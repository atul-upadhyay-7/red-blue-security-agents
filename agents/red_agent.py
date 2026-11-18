"""Red agent: runs OWASP Nettacker modules against the local target and
writes structured findings."""
import json
import os
import subprocess
import sys
import tempfile

MODULES = {
    "http_cors_vuln": ("open_cors", "Wildcard CORS with credentials allowed", "medium"),
    "admin_scan": ("exposed_admin", "Admin page reachable without login", "high"),
}


def run_module(module, port):
    out = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    os.unlink(out)
    subprocess.run(
        ["nettacker", "-i", "127.0.0.1", "-m", module, "-g", str(port),
         "--skip-service-discovery", "-o", out, "-t", "5"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    try:
        with open(out) as f:
            events = json.load(f)
    except (OSError, ValueError):
        events = []
    finally:
        if os.path.exists(out):
            os.unlink(out)
    return events


def confirmed(module, events):
    """Keep only events that show a real problem.

    admin_scan also reports 403 pages and the site root, so for it we keep
    an event only when an admin-looking path answered 200.
    """
    if module != "admin_scan":
        return events
    keep = []
    for e in events:
        je = e.get("json_event", {})
        res = je.get("response", {}).get("conditions_results", {})
        codes = res.get("status_code", [])
        url = je.get("url", "")
        if "200" in codes and not url.rstrip("/").endswith(("8081", "8082", "8083")) \
                and url.rstrip("/").count("/") > 2:
            keep.append(e)
    return keep


def scan(port=8081):
    findings = []
    for module, (key, title, severity) in MODULES.items():
        events = confirmed(module, run_module(module, port))
        if events:
            url = events[0].get("json_event", {}).get("url", "")
            findings.append({"id": key, "module": module, "title": title,
                             "severity": severity, "evidence_url": url})
    return {"target": f"127.0.0.1:{port}", "findings": findings}


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    print(json.dumps(scan(port), indent=2))
