"""rehydrate(state) — turn a compact DesiState into the ONLY context the new chat sees.

The new chat receives exactly:
  1) a system prompt (fixed, short)
  2) the rehydrated DESi-state block

It does NOT receive the original chat history. The block is structured, labelled, and uses
the brief's section names verbatim so a human (and a model) can pick up cold.
"""
from __future__ import annotations

import json
from state import DesiState, token_count

SYSTEM_PROMPT = (
    "You are continuing prior research work. The original chat is NOT included. "
    "Below is a compact DESi-state — the active epistemic state of the project. "
    "Treat it as authoritative for what is already decided, open, confirmed, discarded, "
    "or in conflict. Ask before re-opening a discarded hypothesis or a settled decision."
)

_LABELS = {
    "active_goals": "Active goals",
    "open_problems": "Open problems",
    "confirmed_findings": "Confirmed findings",
    "discarded_hypotheses": "Discarded hypotheses",
    "architecture_decisions": "Architecture decisions",
    "open_conflicts": "Open conflicts",
    "references": "References",
}


def render(state: DesiState) -> str:
    out = ["[DESi-state v1]"]
    for field, label in _LABELS.items():
        items = getattr(state, field)
        if items:
            out.append(f"## {label}")
            for x in items:
                out.append(f"- {x}")
    return "\n".join(out)


def rehydrate(state: DesiState) -> dict:
    """Return the messages payload that should bootstrap the new chat (and nothing else)."""
    block = render(state)
    return {
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": block}],
        "token_size": token_count(SYSTEM_PROMPT) + token_count(block),
        "state_block": block,
    }


def parse(block: str) -> DesiState:
    """Read a rendered block back into a DesiState — used to verify reconstruction sanity."""
    state = DesiState()
    field_by_label = {v: k for k, v in _LABELS.items()}
    current = None
    for line in block.splitlines():
        line = line.rstrip()
        if line.startswith("## "):
            current = field_by_label.get(line[3:].strip())
        elif line.startswith("- ") and current:
            getattr(state, current).append(line[2:].strip())
    return state
