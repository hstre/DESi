"""Rehydration — render the structured state for a new chat. No prose, no narrative."""
from __future__ import annotations

import json

from state_v2 import DesiStateV2, parse as parse_v2, token_count

SYSTEM_PROMPT = (
    "You continue research work. The original chat is NOT included. Below is a structured "
    "DESi-state (no prose, no narrative). Treat it as authoritative for active claims, "
    "constraints, decisions, conflicts, discarded paths, open questions and evidence labels. "
    "Do not invent history. If a question is not answered by the state, ask."
)


def render(state: DesiStateV2) -> str:
    return state.serialize()


def rehydrate(state: DesiStateV2) -> dict:
    block = render(state)
    return {
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": block}],
        "token_size": token_count(SYSTEM_PROMPT) + token_count(block),
        "state_block": block,
    }


def parse(block: str) -> DesiStateV2:
    return parse_v2(block)
