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
}


def respond(report, patch_file):
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
    with open(patch_file, "w") as f:
        json.dump(patches, f, indent=2)
    return actions


if __name__ == "__main__":
    report = json.load(open(sys.argv[1]))
    print(json.dumps(respond(report, sys.argv[2]), indent=2))
