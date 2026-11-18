"""Shared pieces for the two Band agents.

The agents use no language model. Each one is plain code that reacts to
messages in a Band room, so the whole demo runs for free.
"""
import os

from band.core import SimpleAdapter
from band.core.protocols import HistoryConverter  # noqa: F401  (typing aid)

LAB_DIR = os.environ.get("LAB_DIR", "/tmp/redblue-lab")
PATCH_FILE = os.path.join(LAB_DIR, "patches.json")
TARGET_PORT = int(os.environ.get("TARGET_PORT", "8081"))


class PlainHistory:
    """History converter that keeps nothing; the agents are stateless."""

    def set_agent_name(self, name):
        pass

    def convert(self, raw):
        return []


def field(p, *names):
    for n in names:
        if isinstance(p, dict) and p.get(n):
            return p[n]
        if getattr(p, n, None):
            return getattr(p, n)
    return None


def find_participant(tools, needle):
    """Return the id of the participant whose name or handle contains needle."""
    needle = needle.lower()
    for p in tools.participants:
        text = " ".join(str(field(p, k) or "") for k in ("name", "handle", "username")).lower()
        if needle in text:
            return field(p, "id", "participant_id", "user_id")
    return None


def find_human(tools):
    """Return the id of the first human participant, if the room says who is human."""
    for p in tools.participants:
        kind = str(field(p, "type", "participant_type", "sender_type", "kind") or "").lower()
        if kind in ("user", "human"):
            return field(p, "id", "participant_id", "user_id")
    return None


class RuleAdapter(SimpleAdapter):
    """Calls handler(msg, tools) for every message that mentions the agent."""

    def __init__(self, handler):
        super().__init__(history_converter=PlainHistory())
        self.handler = handler

    async def on_message(self, msg, tools, history, participants_msg, contacts_msg,
                         *, is_session_bootstrap, room_id):
        print("got message:", str(msg.content)[:80], flush=True)
        try:
            await self.handler(msg, tools)
        except Exception as e:
            import traceback; traceback.print_exc()
            print("handler error", e, flush=True)
