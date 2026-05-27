#!/usr/bin/env python3
"""TrajectoryTrace v1.2 metrics: semantic branch diversity / collapse + composite.

Deterministic aggregation of the folded (v1.2) trace. No LLM, no core change.
"""
from __future__ import annotations

import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_trace_v12 import trace_v12  # noqa: E402


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def summarize_v12(item: dict) -> dict:
    recs, fold = trace_v12(item)
    if not recs:
        return {}
    n_clusters = max(1, fold["n_clusters"])
    survival = [r["folded_branch_count"] for r in recs]

    # semantic branch entropy over CLUSTER mentions across turns
    counts = {}
    for r in recs:
        for cid in r["branch_clusters"]:
            counts[cid] = counts.get(cid, 0) + 1
    tot = sum(counts.values())
    if tot and n_clusters > 1:
        ps = [c / tot for c in counts.values()]
        semantic_branch_entropy = round(_clamp(-sum(p * math.log(p) for p in ps) / math.log(n_clusters)), 3)
    else:
        semantic_branch_entropy = 0.0

    sem_collapse_events = sum(1 for r in recs if r["semantic_branch_collapse_event"])
    peak, final = max(survival), survival[-1]
    peak_t = survival.index(peak)
    recovered = any(survival[t] >= peak for t in range(peak_t + 1, len(survival)))
    irreversible_semantic_collapse = round(
        _clamp((peak - final) / n_clusters) if (peak > final and not recovered) else 0.0, 3)

    return {
        "folded_branch_count_mean": round(st.mean(survival), 3),
        "folded_branch_count_final": final,
        "n_clusters": fold["n_clusters"],
        "n_directions": fold["n_directions"],
        "branch_equivalence_score": fold["branch_equivalence_score"],
        "branch_redundancy_ratio": fold["branch_redundancy_ratio"],
        "branch_novelty_score": fold["branch_novelty_score"],
        "semantic_branch_entropy": semantic_branch_entropy,
        "semantic_branch_collapse_events": sem_collapse_events,
        "irreversible_semantic_collapse": irreversible_semantic_collapse,
        "branch_survival_curve": survival,
    }


def composite_drift_v12(v1_summary: dict, v11_lock_in: float, v12: dict, n_con: int) -> float:
    """v1.1 composite with SEMANTIC branch entropy replacing lexical branch entropy."""
    turns = max(2, v1_summary.get("turns", 2))
    n_con = max(1, n_con)
    parts = [
        1.0 - v1_summary["constraint_half_life_mean"],
        _clamp(v1_summary["unrecovered_constraints"] / n_con),
        v11_lock_in,
        _clamp(v1_summary["cumulative_drift_energy"] / (turns - 1)),
        1.0 - v1_summary["recovery_quality_proxy"],
        1.0 - v12["semantic_branch_entropy"],     # SEMANTIC, folded
    ]
    return round(_clamp(st.mean(parts)), 3)


__all__ = ["composite_drift_v12", "summarize_v12"]
