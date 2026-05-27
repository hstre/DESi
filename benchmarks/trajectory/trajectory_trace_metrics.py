#!/usr/bin/env python3
"""TrajectoryTrace v0 -> per-trajectory summary + auditor comparison helpers.

Deterministic aggregation of the per-turn trace into the v0 summary fields, and
helpers to compare against DriftBench auditor labels. No model calls, no core change.
"""
from __future__ import annotations

import statistics as st

_DRIFT_TURN_THRESH = 0.25     # per-turn drift_delta above which a turn is a drift event
_n = max


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def summarize(records: list, n_constraints: int, n_directions: int) -> dict:
    """Per-trajectory v0 summary from the per-turn trace records."""
    if not records:
        return {}
    active_frac = [r["state_vector_proxy"]["anchor_density"] for r in records]
    objov = [r["objective_overlap"] for r in records]
    branch = [r["branch_count"] for r in records]
    drift = [r["drift_delta"] for r in records]
    dropped_total = sum(len(r["constraints_dropped"]) for r in records)
    recovered_total = sum(len(r["constraints_recovered"]) for r in records)

    final_objective_fidelity_proxy = objov[-1]
    min_constraint_preservation = round(min(active_frac), 3)
    max_banned_move_incursion = max(len(r["banned_move_hits"]) for r in records)
    nd = _n(1, n_directions)
    branch_preservation_proxy = round(_clamp(st.mean(branch) / nd), 3)
    branch_collapse_proxy = round(max(r["branch_collapse_signal"] for r in records), 3)
    recoverability_proxy = round(_clamp(recovered_total / dropped_total) if dropped_total else 1.0, 3)
    lock_in_proxy = round(max(r["lock_in_signal"] for r in records), 3)
    composite_drift_v0 = round(_clamp(st.mean([
        1.0 - min_constraint_preservation,
        1.0 - final_objective_fidelity_proxy,
        branch_collapse_proxy,
        lock_in_proxy,
        st.mean(drift),
    ])), 3)
    detected_drift_turns = [r["turn_id"] for r in records if r["drift_delta"] >= _DRIFT_TURN_THRESH]
    detected_recovery_turns = [r["turn_id"] for r in records if r["recoverability_delta"] > 0]
    return {
        "turns": len(records),
        "final_objective_fidelity_proxy": final_objective_fidelity_proxy,
        "min_constraint_preservation": min_constraint_preservation,
        "max_banned_move_incursion": max_banned_move_incursion,
        "branch_preservation_proxy": branch_preservation_proxy,
        "branch_collapse_proxy": branch_collapse_proxy,
        "recoverability_proxy": recoverability_proxy,
        "lock_in_proxy": lock_in_proxy,
        "composite_drift_v0": composite_drift_v0,
        "detected_drift_turns": detected_drift_turns,
        "detected_recovery_turns": detected_recovery_turns,
        "constraints_dropped_total": dropped_total,
        "constraints_recovered_total": recovered_total,
    }


# (v0 summary metric, auditor dim, expected sign)
COMPARE_PAIRS = [
    ("composite_drift_v0", "drift_severity", "+"),
    ("min_constraint_preservation", "constraint_adherence", "+"),
    ("branch_preservation_proxy", "alternative_coverage", "+"),
    ("recoverability_proxy", "recoverability", "+"),
    ("final_objective_fidelity_proxy", "objective_fidelity", "+"),
    ("lock_in_proxy", "drift_severity", "+"),
]

__all__ = ["COMPARE_PAIRS", "summarize"]
