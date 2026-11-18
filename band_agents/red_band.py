"""Red agent on Band: scans the local practice app with Nettacker."""
import asyncio
import json
import os
import subprocess
import sys

from band import Agent
from band.config import load_agent_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from agents.red_agent import scan  # noqa: E402
from band_agents.common import (LAB_DIR, PATCH_FILE, TARGET_PORT,  # noqa: E402
                                RuleAdapter, find_participant)

state = {"requester": None, "before": None}


def start_target():
    os.makedirs(LAB_DIR, exist_ok=True)
    if os.path.exists(PATCH_FILE):
        os.remove(PATCH_FILE)
    env = dict(os.environ, PATCH_FILE=PATCH_FILE)
    return subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "target", "vulnerable_app.py"), str(TARGET_PORT)],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def handle(msg, tools):
    text = msg.content.lower()
    blue = find_participant(tools, "blue")
    if msg.sender_type != "Agent" and "scan" in text:
        state["requester"] = msg.sender_id
        if os.path.exists(PATCH_FILE):
            os.remove(PATCH_FILE)
        report = await asyncio.to_thread(scan, TARGET_PORT)
        state["before"] = report
        await tools.send_message(
            "FINDINGS " + json.dumps(report), mentions=[blue] if blue else None)
    elif "patched" in text and state["before"] is not None:
        after = await asyncio.to_thread(scan, TARGET_PORT)
        before_ids = [f["id"] for f in state["before"]["findings"]]
        after_ids = [f["id"] for f in after["findings"]]
        ok = bool(before_ids) and not after_ids
        await tools.send_message(
            f"RESULT {'PASS' if ok else 'FAIL'}: found {before_ids} before the fix, "
            f"{after_ids} after. Only 127.0.0.1 was scanned.",
            mentions=[state["requester"]] if state["requester"] else None)
        state["before"] = None


async def main():
    target = start_target()
    try:
        agent_id, api_key = load_agent_config("red_scanner")
        agent = Agent.create(adapter=RuleAdapter(handle), agent_id=agent_id, api_key=api_key)
        print("red agent running")
        await agent.run()
    finally:
        target.terminate()


if __name__ == "__main__":
    asyncio.run(main())
