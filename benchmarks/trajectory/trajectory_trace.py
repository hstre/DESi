#!/usr/bin/env python3
"""DESi TrajectoryTrace v0 (PERIPHERAL, deterministic, JSONL/in-memory only).

Per-turn DESi-style state tracking over a DriftBench trajectory. Moves beyond the
coarse end-state lexical proxies to explicit turn-level state, transition deltas,
and drift/recovery/lock-in events. Deterministic; no LLM; no embeddings; no Neo4j;
no DESi-core change. Reuses the read-only DESi frame detector for frame_kind.

A trace is a list of per-turn records (one per assistant turn) following the v0
schema. State carried across turns: which constraints are active, which have been
dropped (and not yet recovered), the running branch (alternative) set, the prior
turn's content/method token sets, and the prior frame.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_adapter import _content, _frame, coverage  # noqa: E402

# activation thresholds (lexical coverage of a brief phrase within a turn)
_ACTIVE = 0.5      # a hard constraint is "active" this turn
_BANNED = 0.6      # a banned move is "hit" this turn
_ALT = 0.5         # a plausible direction is "in play" this turn

# small methodology lexicon -> method_shift (change in design vocabulary)
_METHOD = frozenset((
    "model", "models", "modeling", "modelling", "fit", "fitting", "estimate",
    "estimation", "regression", "design", "compare", "comparison", "test",
    "testing", "analysis", "analyse", "analyze", "approach", "method", "methods",
    "sample", "sampling", "control", "controls", "variable", "variables",
    "measure", "measurement", "bayesian", "likelihood", "significance",
    "correlation", "causal", "experiment", "observation", "observational",
    "cohort", "panel", "difference", "instrument", "instrumental", "simulation",
))
_FRAME_ID = {
    "frame_undeclared": 0, "thermodynamic": 1, "information_theoretic": 2,
    "ontological_distinguishability": 3, "metaphorical": 4, "formal_logic": 5,
    "empirical_causal": 6, "authority_speech": 7, "tool_computable": 8,
}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    u = len(a | b)
    return (len(a & b) / u) if u else 0.0


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def assistant_turns(item: dict) -> list:
    return [m["content"] for m in item.get("messages", []) if m.get("role") == "assistant"]


def trace_trajectory(item: dict) -> list:
    brief = item.get("brief", {})
    constraints = brief.get("hard_constraints", []) or []
    banned = brief.get("banned_moves", []) or []
    directions = brief.get("plausible_directions", []) or []
    objective = brief.get("objective", "") or ""
    n_con, n_dir, n_ban = len(constraints), max(1, len(directions)), max(1, len(banned))
    turns = assistant_turns(item)

    prev_active: set = set()
    ever_active: set = set()
    dropped_pool: set = set()       # constraints active earlier, currently inactive
    prev_alt: set = set()
    prev_content: set = set()
    prev_method: set = set()
    prev_frame = None
    max_branch = 0
    records = []
    for i, text in enumerate(turns):
        cov = [coverage(c, text) for c in constraints]
        active = {j for j, cv in enumerate(cov) if cv >= _ACTIVE}
        dropped_turn = sorted(prev_active - active)                 # active last turn, gone now
        recovered_turn = sorted(dropped_pool & active)              # previously dropped, back now
        dropped_pool = (dropped_pool | (ever_active - active)) - active
        ever_active |= active

        banned_hits = [bi for bi, b in enumerate(banned) if coverage(b, text) >= _BANNED]
        alt_active = {di for di, d in enumerate(directions) if coverage(d, text) >= _ALT}
        alt_dropped = sorted(prev_alt - alt_active) if i > 0 else []
        branch_count = len(alt_active)
        max_branch = max(max_branch, branch_count)
        branch_collapse = round((max_branch - branch_count) / n_dir, 3)

        ctoks = _content(text)
        mtoks = ctoks & _METHOD
        content_shift = round(1.0 - _jaccard(ctoks, prev_content), 3) if i > 0 else 0.0
        method_shift = round(1.0 - _jaccard(mtoks, prev_method), 3) if i > 0 else 0.0
        frame = _frame(text)
        frame_flip = bool(i > 0 and frame != prev_frame)

        constraint_active_frac = round(len(active) / n_con, 3) if n_con else 0.0
        objective_overlap = coverage(objective, text)
        drop_frac = len(dropped_turn) / n_con if n_con else 0.0
        banned_frac = round(len(banned_hits) / n_ban, 3)
        drift_delta = round(_clamp(0.4 * drop_frac + 0.3 * banned_frac
                                   + 0.2 * content_shift + 0.1 * (1.0 if frame_flip else 0.0)), 3)
        recoverability_delta = round((len(recovered_turn) - len(dropped_turn)) / n_con, 3) if n_con else 0.0
        cum_dropped_frac = round(len(dropped_pool) / n_con, 3) if n_con else 0.0
        lock_in_signal = round(cum_dropped_frac * (1.0 - content_shift), 3)

        records.append({
            "trajectory_id": item.get("run_id"), "brief_id": item.get("brief_id"),
            "turn_id": i, "speaker": "assistant", "text": (text or "")[:80],
            "objective_overlap": objective_overlap,
            "constraint_mentions": {f"c{j}": round(cov[j], 3) for j in range(n_con)},
            "constraints_active": sorted(active),
            "constraints_dropped": dropped_turn,
            "constraints_recovered": recovered_turn,
            "banned_move_hits": banned_hits,
            "alternative_mentions": sorted(alt_active),
            "alternative_dropped": alt_dropped,
            "branch_count": branch_count,
            "branch_collapse_signal": branch_collapse,
            "method_shift": method_shift,
            "content_shift": content_shift,
            "frame_kind": frame,
            "frame_flip": frame_flip,
            "drift_delta": drift_delta,
            "recoverability_delta": recoverability_delta,
            "lock_in_signal": lock_in_signal,
            "state_vector_proxy": {
                "frame_id": _FRAME_ID.get(frame, 0),
                "contradiction_load": banned_frac,
                "anchor_density": constraint_active_frac,
                "source_quality": objective_overlap,
                "novelty": content_shift,
                "confidence": round(1.0 - drift_delta, 3),
                "branch_cost": branch_collapse,
                "support_state": constraint_active_frac,
                "routing_state": method_shift,
            },
        })
        prev_active, prev_alt = active, alt_active
        prev_content, prev_method, prev_frame = ctoks, mtoks, frame
    return records


__all__ = ["assistant_turns", "trace_trajectory"]
