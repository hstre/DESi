#!/usr/bin/env python3
"""DESi TrajectoryTrace v1 (PERIPHERAL): explicit trajectory-dynamics tracking.

Builds on v0's per-turn lexical/frame signals and adds turn-DYNAMICS: a per-turn
drift-event ledger and transition-level state deltas (State_t -> State_t+1). The
heavier per-trajectory dynamics (constraint half-life, recovery quality, branch
entropy/collapse, method-vs-content divergence, cumulative drift energy) live in
trajectory_trace_v1_metrics.summarize_v1.

Deterministic; no LLM; no embeddings; no Neo4j; no DESi-core change (reuses the
v0 tracer, which reads the DESi frame layer read-only).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_trace import trace_trajectory  # noqa: E402 (v0 per-turn signals)

_METHOD_EVENT = 0.5
_CONTENT_EVENT = 0.5
_LOCKIN_EVENT = 0.1
_SVP_DIMS = ("frame_id", "contradiction_load", "anchor_density", "source_quality",
             "novelty", "confidence", "branch_cost", "support_state", "routing_state")


def _state_vec(rec: dict) -> list:
    svp = rec["state_vector_proxy"]
    v = []
    for d in _SVP_DIMS:
        x = svp.get(d, 0.0)
        v.append(x / 8.0 if d == "frame_id" else float(x))
    return v


def _transition_delta(a: list, b: list) -> float:
    return round(math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b))) / math.sqrt(len(a)), 3)


def trace_v1(item: dict) -> list:
    """Per-turn enriched records: v0 base signals + transition_delta + drift_events."""
    base = trace_trajectory(item)
    out = []
    prev_vec = None
    prev_branch = None
    for rec in base:
        vec = _state_vec(rec)
        tdelta = _transition_delta(prev_vec, vec) if prev_vec is not None else 0.0
        branch = rec["branch_count"]
        branch_collapse = bool(prev_branch is not None
                               and (branch <= prev_branch - 2 or (prev_branch > 0 and branch == 0)))
        events = []
        if rec["constraints_dropped"]:
            events.append("new_constraint_loss")
        if rec["constraints_recovered"]:
            events.append("constraint_recovery")
        if rec["banned_move_hits"]:
            events.append("banned_move_incursion")
        if branch_collapse:
            events.append("branch_collapse")
        if rec["method_shift"] >= _METHOD_EVENT:
            events.append("method_shift_event")
        if rec["content_shift"] >= _CONTENT_EVENT:
            events.append("content_shift_event")
        if rec["lock_in_signal"] >= _LOCKIN_EVENT:
            events.append("lock_in_event")
        enriched = dict(rec)
        enriched["transition_delta"] = tdelta
        enriched["branch_collapse_event"] = branch_collapse
        enriched["drift_events"] = events
        out.append(enriched)
        prev_vec, prev_branch = vec, branch
    return out


def lean_record(rec: dict) -> dict:
    """Compact per-turn projection for the v1 trace JSONL (dynamics-focused)."""
    return {
        "trajectory_id": rec["trajectory_id"], "brief_id": rec["brief_id"],
        "turn_id": rec["turn_id"], "transition_delta": rec["transition_delta"],
        "drift_events": rec["drift_events"], "branch_count": rec["branch_count"],
        "branch_collapse_event": rec["branch_collapse_event"],
        "n_active": len(rec["constraints_active"]), "n_dropped": len(rec["constraints_dropped"]),
        "n_recovered": len(rec["constraints_recovered"]),
        "banned_hits": len(rec["banned_move_hits"]),
        "method_shift": rec["method_shift"], "content_shift": rec["content_shift"],
        "objective_overlap": rec["objective_overlap"], "lock_in_signal": rec["lock_in_signal"],
    }


__all__ = ["lean_record", "trace_v1"]
