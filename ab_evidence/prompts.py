"""Deterministic prompt construction for variants A and B.

Variant A: full chat history.
Variant B: system prompt + DESi state JSON only (NO chat).

Both variants receive the SAME follow-up task. The system prompt is identical between variants
where possible (only B mentions that the chat is replaced by the state).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "claude_compression"))
from state import token_count  # noqa: E402  (the same offline tokenizer used everywhere)

from build_state import load_chat, state_for_variant_B
from follow_up_tasks import FOLLOW_UPS

_SYSTEM_BASE = (
    "You are continuing prior work. Answer the user's question using ONLY the context you have. "
    "Do not invent facts. If a category has no entries, write 'none'."
)

_SYSTEM_B_EXTRA = (
    " The original chat is NOT included. Below the question is a structured DESi state with the "
    "active claims, constraints, decisions, open conflicts, and open questions."
)


def variant_A_messages(case_id: str) -> dict:
    chat = load_chat(case_id)
    follow_up = FOLLOW_UPS[case_id]
    messages = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in chat]
    messages.append({"role": "user", "content": follow_up})
    payload = {
        "variant": "A_full_context",
        "system": _SYSTEM_BASE,
        "messages": messages,
        "input_token_estimate": (token_count(_SYSTEM_BASE)
                                 + sum(token_count(m["content"]) for m in messages)),
    }
    return payload


def variant_B_messages(case_id: str) -> dict:
    state = state_for_variant_B(case_id)
    state_block = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    follow_up = FOLLOW_UPS[case_id]
    user = (
        f"{follow_up}\n\n"
        f"---\n"
        f"DESi state:\n{state_block}\n"
        f"---"
    )
    payload = {
        "variant": "B_desi_state",
        "system": _SYSTEM_BASE + _SYSTEM_B_EXTRA,
        "messages": [{"role": "user", "content": user}],
        "input_token_estimate": token_count(_SYSTEM_BASE + _SYSTEM_B_EXTRA) + token_count(user),
    }
    return payload
