"""A/B test design for the Claude-Layer Probe.

Variant A: full_context  — Claude gets the entire chat history.
Variant B: desi_state    — Claude gets only system prompt + DESi state + cold anchors on demand.

Measured (against a FROZEN, independently-authored ground truth):
  decision_preservation, constraint_preservation, conflict_visibility,
  open_claims_preserved, false_new_claims, tokens_used,
  workable_in_next_step (BOOLEAN status).

This module BUILDS the side-by-side prompts deterministically so they can be run later in a
real Claude session. It does NOT run them here. The brief mandates: if a second Claude session
is not possible in this environment, mark as UNTESTED_in_this_env. We do exactly that.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[0] / "state_not_summary"))
sys.path.insert(0, str(_HERE.parents[0] / "claude_compression"))

import mcp_layer as layer  # noqa: E402
from state import token_count  # noqa: E402  (the same offline tokenizer used everywhere)


def build_full_context_prompt(chat_history: list) -> dict:
    msgs = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in chat_history]
    return {"variant": "A_full_context",
            "system": "You continue research work. The full chat is included below.",
            "messages": msgs,
            "token_size": token_count("\n".join(m["content"] for m in msgs))}


def build_desi_state_prompt(run_id: str) -> dict:
    p = layer.export_rehydration_prompt(run_id)
    return {"variant": "B_desi_state",
            "system": p["system"],
            "state_block": p["state_block"],
            "token_size": p["token_size"]}


def design_one_pair(fixture_id: str, chat: list, ground_truth: dict) -> dict:
    """Build BOTH prompts for one fixture and document the eval plan.
    The actual A/B requires a second Claude session — flagged UNTESTED here."""
    # build run state by replaying chat through observe_step with NO metadata (the harder case:
    # state can only be built from what Claude annotated in the loop). We deliberately do not
    # auto-classify here; that would be Prototype 3 (which largely failed). For the design
    # demo, we ship a minimal metadata stream so the state is non-empty.
    layer._reset_run(fixture_id)
    for i, msg in enumerate(chat):
        layer.observe_step(fixture_id, input=msg.get("content", ""),
                           model_output="", metadata={})
    a = build_full_context_prompt(chat)
    b = build_desi_state_prompt(fixture_id)
    verify = layer.replay_verify(fixture_id)
    return {
        "fixture_id": fixture_id,
        "variant_A": a,
        "variant_B": b,
        "token_size_A": a["token_size"],
        "token_size_B": b["token_size"],
        "savings_tokens": a["token_size"] - b["token_size"],
        "compression_ratio_B_vs_A": round(1 - b["token_size"] / a["token_size"], 4)
                                    if a["token_size"] else 0.0,
        "replay_verified": verify["verified"],
        "metrics_to_compare": [
            "decision_preservation", "constraint_preservation", "conflict_visibility",
            "open_claims_preserved", "false_new_claims", "tokens_used",
            "workable_in_next_step",
        ],
        "ground_truth_keys": list(ground_truth.keys()),
        "workability_status": "UNTESTED_in_this_env "
                              "(requires a second Claude session this environment cannot run)",
    }
