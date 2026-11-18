"""Blue agent on Band: reads findings from the red agent and patches the app."""
import asyncio
import json
import os
import sys

from band import Agent
from band.config import load_agent_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from agents.blue_agent import respond  # noqa: E402
from band_agents.common import LAB_DIR, PATCH_FILE, RuleAdapter, find_participant  # noqa: E402


async def handle(msg, tools):
    if "FINDINGS" not in msg.content:
        return
    body = msg.content[msg.content.index("FINDINGS") + len("FINDINGS"):].strip()
    report = json.loads(body)
    os.makedirs(LAB_DIR, exist_ok=True)
    actions = respond(report, PATCH_FILE)
    lines = [f"- {a['finding']}: {a.get('explanation') or a.get('action')}" for a in actions]
    red = find_participant(tools, "red")
    await tools.send_message(
        "PATCHED. Fixes applied:\n" + "\n".join(lines) + "\nPlease retest.",
        mentions=[red] if red else None)


async def main():
    agent_id, api_key = load_agent_config("blue_patcher")
    agent = Agent.create(adapter=RuleAdapter(handle), agent_id=agent_id, api_key=api_key)
    print("blue agent running")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
