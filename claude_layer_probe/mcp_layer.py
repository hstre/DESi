"""Minimal DESi Claude-Layer — five tool functions, deterministic, replay-hashed.

This is a DESIGN STUB, not a product. It implements the five functions the brief asks for as
real Python with a real in-memory state, a real append-only step log, and a real replay hash
(via the existing desi.core.replay_kernel). It does NOT spin up an MCP server; the same five
functions are what an MCP server (or Claude Code tool) would expose.

Principle (per the brief):
  Claude works.  DESi observes each step.  DESi updates the epistemic state.
  Claude gets, on demand: the current state + cold anchors.  NOT: long chat -> summary.

Cold anchors here are pointers (anchor_id -> raw input/output of step N) so the model can pull
back the exact source span if needed, without putting the prose into context by default.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "state_not_summary"))

from desi.core.replay_kernel import canonical_json, replay_hash  # noqa: E402


@dataclass
class Step:
    step_index: int
    input: str
    model_output: str
    metadata: dict = field(default_factory=dict)
    anchor_id: str = ""


@dataclass
class LayerState:
    run_id: str
    steps: list = field(default_factory=list)            # cold log (append-only)
    state: dict = field(default_factory=lambda: {        # active epistemic state
        "claims": [], "constraints": [], "decisions": [], "conflicts": [], "open_questions": [],
    })
    chain_head: str = ""


# in-memory store keyed by run_id; an MCP server would persist this
_RUNS: dict = {}


def _anchor_id_for(run_id: str, step_index: int, input_text: str) -> str:
    h = hashlib.sha256(f"{run_id}|{step_index}|{input_text}".encode("utf-8")).hexdigest()[:12]
    return f"a-{step_index:04d}-{h}"


def _update_state(state: dict, input_text: str, model_output: str, metadata: dict) -> None:
    """Deterministic, LEXICAL update — no LLM, no embedding. Each step may add at most one
    typed entry per category, identified by 'kind' in metadata (claim|constraint|decision|
    conflict|question). Unknown metadata.kind -> no update (Claude controls the bookkeeping)."""
    kind = (metadata or {}).get("kind", "")
    body = (metadata or {}).get("body") or model_output.strip()[:140]
    if not body:
        return
    if kind == "claim":
        state["claims"].append({"id": f"C{len(state['claims'])+1}", "what": body,
                                "evidence": (metadata or {}).get("evidence", "untested")})
    elif kind == "constraint":
        state["constraints"].append({"id": f"R{len(state['constraints'])+1}", "what": body})
    elif kind == "decision":
        state["decisions"].append({"id": f"D{len(state['decisions'])+1}", "what": body,
                                   "replaces": (metadata or {}).get("replaces", "")})
        # if this decision replaces an earlier one, drop the earlier
        rid = (metadata or {}).get("replaces")
        if rid:
            state["decisions"] = [d for d in state["decisions"] if d["id"] != rid
                                  or d is state["decisions"][-1]]
    elif kind == "conflict":
        state["conflicts"].append({"id": f"K{len(state['conflicts'])+1}", "what": body,
                                   "claim_ids": (metadata or {}).get("claim_ids", [])})
    elif kind == "question":
        state["open_questions"].append({"id": f"Q{len(state['open_questions'])+1}", "what": body,
                                        "blocking": bool((metadata or {}).get("blocking", False))})


# ---------- the five tool functions ----------------------------------------------------

def observe_step(run_id: str, input: str, model_output: str, metadata: dict | None = None) -> dict:
    """Claude calls this AFTER each working step. DESi appends the step to cold storage and
    deterministically updates the active state from metadata (or skips if no 'kind' tag).
    Returns the new chain head + the anchor id for this step."""
    rec = _RUNS.setdefault(run_id, LayerState(run_id=run_id))
    step_index = len(rec.steps)
    anchor_id = _anchor_id_for(run_id, step_index, input or "")
    step = Step(step_index=step_index, input=input or "", model_output=model_output or "",
                metadata=metadata or {}, anchor_id=anchor_id)
    rec.steps.append(step)
    _update_state(rec.state, step.input, step.model_output, step.metadata)
    rec.chain_head = replay_hash({"run_id": run_id, "prev": rec.chain_head, "step": {
        "i": step_index, "input": step.input, "output": step.model_output,
        "meta": step.metadata, "anchor": anchor_id}})
    return {"step_index": step_index, "anchor_id": anchor_id, "chain_head": rec.chain_head}


def current_state(run_id: str) -> dict:
    rec = _RUNS.get(run_id)
    if rec is None:
        return {"run_id": run_id, "claims": [], "constraints": [], "decisions": [],
                "conflicts": [], "open_questions": []}
    return {"run_id": run_id, **rec.state}


def retrieve_cold_anchor(run_id: str, anchor_id: str) -> dict:
    """Pull the exact prose for one step by anchor id (cold storage access). The whole point:
    only retrieve when the active state is not enough."""
    rec = _RUNS.get(run_id)
    if rec is None:
        return {"found": False, "reason": f"no such run_id: {run_id}"}
    for s in rec.steps:
        if s.anchor_id == anchor_id:
            return {"found": True, "step_index": s.step_index, "input": s.input,
                    "model_output": s.model_output, "metadata": s.metadata}
    return {"found": False, "reason": f"no such anchor_id: {anchor_id}"}


def replay_verify(run_id: str) -> dict:
    """Recompute the chain hash from cold storage; must equal the current chain head bit-for-bit."""
    rec = _RUNS.get(run_id)
    if rec is None:
        return {"verified": False, "reason": "unknown run_id"}
    h = ""
    for s in rec.steps:
        h = replay_hash({"run_id": run_id, "prev": h, "step": {
            "i": s.step_index, "input": s.input, "output": s.model_output,
            "meta": s.metadata, "anchor": s.anchor_id}})
    return {"verified": h == rec.chain_head, "recomputed": h, "stored": rec.chain_head,
            "n_steps": len(rec.steps)}


def export_rehydration_prompt(run_id: str) -> dict:
    """Produce the EXACT context a new Claude session would receive in variant B:
    a short system prompt + the current state block. No chat history."""
    state = current_state(run_id)
    block = json.dumps({k: v for k, v in state.items() if k != "run_id"},
                       ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    system = ("You continue research work. The original chat is NOT included. Below is the "
              "active DESi state (no prose). If a needed piece is missing, ask. "
              "If you need a specific source span, request it by anchor_id.")
    from state import token_count  # claude_compression
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "claude_compression"))
    return {"system": system, "state_block": block,
            "token_size": token_count(system) + token_count(block)}


# small helpers for tests/teardown
def _reset_run(run_id: str) -> None:
    _RUNS.pop(run_id, None)
