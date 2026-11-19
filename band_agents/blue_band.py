"""Blue agent on Band: proposes fixes, waits for a human to approve, then patches."""
import asyncio
import json
import os
import sys

from band import Agent
from band.config import load_agent_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from agents.blue_agent import plan, respond  # noqa: E402
from band_agents.common import (LAB_DIR, PATCH_FILE, RuleAdapter,  # noqa: E402
                                find_human, find_participant)

LOG_FILE = os.path.join(LAB_DIR, "patch_log.jsonl")
pending = {"report": None}


async def handle(msg, tools):
    text = msg.content
    low = text.lower()
    red = find_participant(tools, "red")
    if "FINDINGS" in text and msg.sender_type == "Agent":
        report = json.loads(text[text.index("FINDINGS") + len("FINDINGS"):].strip())
        pending["report"] = report
        lines = [f"- {p['finding']} ({p['severity']}): {p['explanation']}" for p in plan(report)]
        human = find_human(tools)
        await tools.send_message(
            "PROPOSED FIXES, nothing changed yet:\n" + "\n".join(lines)
            + "\nA human must reply `approve` (or `reject`) to me before I patch anything.",
            mentions=[human] if human else None)
    elif msg.sender_type != "Agent" and pending["report"] is not None:
        if "approve" in low:
            os.makedirs(LAB_DIR, exist_ok=True)
            actions = respond(pending["report"], PATCH_FILE, LOG_FILE)
            pending["report"] = None
            lines = [f"- {a['finding']}: patch {a.get('patch')}" for a in actions]
            await tools.send_message(
                "PATCHED after human approval. Patch log:\n" + "\n".join(lines)
                + f"\n(full log: {LOG_FILE}) Please retest.",
                mentions=[red] if red else None)
        elif "reject" in low:
            pending["report"] = None
            human = find_human(tools) or msg.sender_id
            await tools.send_message("REJECTED. No patch was applied.",
                                     mentions=[human] if human else None)


async def main():
    agent_id, api_key = load_agent_config("blue_patcher")
    agent = Agent.create(adapter=RuleAdapter(handle), agent_id=agent_id, api_key=api_key)
    print("blue agent running")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
