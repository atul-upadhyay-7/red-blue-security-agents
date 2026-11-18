"""Blue agent: reads red-agent findings, explains each one, and applies a
fix by updating the target's patches.json."""
import json
import os
import sys

PLAYBOOK = {
    "open_cors": ("restrict_cors",
                  "Any website can read responses with the user's cookies. "
                  "Fix: stop sending the wildcard Access-Control-Allow-Origin header."),
    "exposed_admin": ("lock_admin",
                      "The admin page answers without authentication. "
                      "Fix: return 403 until a real login is in front of it."),
    "clickjacking": ("block_framing",
                     "Another site can put this page in a hidden frame and trick clicks. "
                     "Fix: send X-Frame-Options DENY and a frame-ancestors policy."),
    "tech_leak": ("hide_powered_by",
                  "The X-Powered-By header tells attackers which framework runs here. "
                  "Fix: remove the header."),
    "weak_cookie": ("harden_cookie",
                    "The session cookie can be read by scripts or sent cross-site. "
                    "Fix: set HttpOnly, Secure, SameSite=Strict and a Max-Age."),
}


def plan(report):
    """What Blue proposes, without changing anything."""
    items = []
    for item in report["findings"]:
        entry = PLAYBOOK.get(item["id"])
        if entry:
            items.append({"finding": item["id"], "severity": item["severity"],
                          "patch": entry[0], "explanation": entry[1]})
        else:
            items.append({"finding": item["id"], "severity": item["severity"],
                          "patch": None, "explanation": "no playbook, needs a human"})
    return items


def log_patch(log_file, action):
    import time
    rec = dict(action, time=time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(log_file, "a") as f:
        f.write(json.dumps(rec) + "\n")


def respond(report, patch_file, log_file=None):
    try:
        with open(patch_file) as f:
            patches = json.load(f)
    except (OSError, ValueError):
        patches = {}
    actions = []
    for item in report["findings"]:
        entry = PLAYBOOK.get(item["id"])
        if not entry:
            actions.append({"finding": item["id"], "action": "no playbook, needs a human"})
            continue
        patch_key, advice = entry
        patches[patch_key] = True
        actions.append({"finding": item["id"], "severity": item["severity"],
                        "explanation": advice, "patch": patch_key})
        if log_file:
            log_patch(log_file, actions[-1])
    with open(patch_file, "w") as f:
        json.dump(patches, f, indent=2)
    return actions


if __name__ == "__main__":
    report = json.load(open(sys.argv[1]))
    print(json.dumps(respond(report, sys.argv[2]), indent=2))
