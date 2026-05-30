"""Rehydration: turn the discovered state into the ONLY context a new chat receives."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "claude_compression"))
from state import token_count  # noqa: E402

SYSTEM_PROMPT = (
    "You continue research work. The original chat is NOT included. Below is a discovered "
    "DESi-state (structured entries only; no prose, no narrative). Treat it as authoritative "
    "for active claims, constraints, decisions, open conflicts, and open questions. The state "
    "may be incomplete; if a needed piece is missing, ask. Do not invent history."
)


def rehydrate(discovered_state: dict) -> dict:
    block = json.dumps(discovered_state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": block}],
        "token_size": token_count(SYSTEM_PROMPT) + token_count(block),
        "state_block": block,
    }


def parse(block: str) -> dict:
    return json.loads(block)
