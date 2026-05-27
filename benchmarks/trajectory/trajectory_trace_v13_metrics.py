#!/usr/bin/env python3
"""TrajectoryTrace v1.3 metrics: semantic branch diversity/collapse + composite."""
from __future__ import annotations

import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_trace_v13 import trace_v13  # noqa: E402


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def summarize_v13(item: dict, fold: dict) -> dict:
    recs = trace_v13(item, fold)
    if not recs:
        return {}
    n_clusters = max(1, fold["n_clusters"])
    survival = [r["folded_branch_count"] for r in recs]

    counts = {}
    for r in recs:
        for cid in r["branch_clusters"]:
            counts[cid] = counts.get(cid, 0) + 1
    tot = sum(counts.values())
    if tot and n_clusters > 1:
        ps = [c / tot for c in counts.values()]
        sem_entropy = round(_clamp(-sum(p * math.log(p) for p in ps) / math.log(n_clusters)), 3)
    else:
        sem_entropy = 0.0

    sem_collapse = sum(1 for r in recs if r["semantic_branch_collapse_event"])
    peak, final = max(survival), survival[-1]
    peak_t = survival.index(peak)
    recovered = any(survival[t] >= peak for t in range(peak_t + 1, len(survival)))
    irreversible = round(_clamp((peak - final) / n_clusters) if (peak > final and not recovered) else 0.0, 3)
    preservation = round(_clamp(st.mean(survival) / n_clusters), 3)

    return {
        "semantic_branch_clusters": fold["n_clusters"],
        "n_directions": fold["n_directions"],
        "semantic_branch_redundancy_ratio": fold["semantic_branch_redundancy_ratio"],
        "branch_equivalence_score": fold["branch_equivalence_score"],
        "semantic_branch_entropy": sem_entropy,
        "semantic_branch_collapse_events": sem_collapse,
        "irreversible_semantic_collapse": irreversible,
        "semantic_branch_preservation_proxy_v13": preservation,
        "semantic_branch_survival_curve": survival,
    }


def composite_drift_v13(v1_summary: dict, v11_lock_in: float, v13: dict, n_con: int) -> float:
    """v1.1 composite with the SEMANTIC (sensor-folded) branch entropy substituted."""
    turns = max(2, v1_summary.get("turns", 2))
    n_con = max(1, n_con)
    parts = [
        1.0 - v1_summary["constraint_half_life_mean"],
        _clamp(v1_summary["unrecovered_constraints"] / n_con),
        v11_lock_in,
        _clamp(v1_summary["cumulative_drift_energy"] / (turns - 1)),
        1.0 - v1_summary["recovery_quality_proxy"],
        1.0 - v13["semantic_branch_entropy"],
    ]
    return round(_clamp(st.mean(parts)), 3)


__all__ = ["composite_drift_v13", "summarize_v13"]
