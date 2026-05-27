#!/usr/bin/env python3
"""TrajectoryTrace v1 per-trajectory dynamics summary + auditor comparison pairs.

Deterministic aggregation of the v1 enriched per-turn records into trajectory
dynamics: constraint half-life, recovery quality (rhetorical vs operational),
branch entropy/collapse, method-vs-content drift divergence, transition-level
abruptness/stabilization, cumulative drift energy, composite_drift_v1, and the
per-turn drift-event ledger. No model calls, no core change.
"""
from __future__ import annotations

import math
import statistics as st


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def _longest_inactive_span(active_turns: set, first: int, last: int) -> int:
    gap = best = 0
    for t in range(first, last + 1):
        if t in active_turns:
            gap = 0
        else:
            gap += 1
            best = max(best, gap)
    return best


def summarize_v1(records: list, n_constraints: int, n_directions: int) -> dict:
    if not records:
        return {}
    n_turns = len(records)
    n_con = max(1, n_constraints)
    n_dir = max(1, n_directions)

    # ---- 1. constraint half-life ----
    active_by_c = {j: set() for j in range(n_constraints)}
    for r in records:
        for j in r["constraints_active"]:
            if j < n_constraints:
                active_by_c[j].add(r["turn_id"])
    final_active = set(records[-1]["constraints_active"])
    half_lives, decays = [], []
    unrecovered = 0
    ever_active = 0
    for j, turns in active_by_c.items():
        if not turns:
            continue
        ever_active += 1
        half_lives.append(len(turns) / n_turns)                 # fraction of trajectory active
        decays.append(_longest_inactive_span(turns, min(turns), max(turns)) / n_turns)
        if j not in final_active:
            unrecovered += 1
    constraint_half_life_mean = round(st.mean(half_lives), 3) if half_lives else 1.0
    max_constraint_decay = round(max(decays), 3) if decays else 0.0

    # ---- 2. recovery quality (rhetorical vs operational) ----
    op = rhet = 0
    for t, r in enumerate(records):
        if not r["constraints_recovered"]:
            continue
        prev = records[t - 1] if t > 0 else r
        objov_ok = r["objective_overlap"] >= prev["objective_overlap"]
        pressure_ok = len(r["banned_move_hits"]) <= len(prev["banned_move_hits"])
        if objov_ok and pressure_ok:
            op += 1
        else:
            rhet += 1
    failed = unrecovered
    denom = op + rhet + failed
    recovery_quality_proxy = round(op / denom, 3) if denom else 1.0

    # ---- 3. branch collapse ----
    branch_seq = [r["branch_count"] for r in records]
    branch_collapse_events = sum(1 for r in records if r.get("branch_collapse_event"))
    dir_counts = [0] * n_directions
    for r in records:
        for d in r["alternative_mentions"]:
            if d < n_directions:
                dir_counts[d] += 1
    tot = sum(dir_counts)
    if tot and n_dir > 1:
        ps = [c / tot for c in dir_counts if c > 0]
        ent = -sum(p * math.log(p) for p in ps) / math.log(n_dir)
        branch_entropy_proxy = round(_clamp(ent), 3)
    else:
        branch_entropy_proxy = 0.0
    peak = max(branch_seq)
    final_b = branch_seq[-1]
    peak_t = branch_seq.index(peak)
    recovered_branch = any(branch_seq[t] >= peak for t in range(peak_t + 1, n_turns))
    irreversible_lock_in_proxy = round(
        _clamp((peak - final_b) / n_dir) if (peak > final_b and not recovered_branch) else 0.0, 3)

    # ---- 4. method vs content drift ----
    method_curve = [r["method_shift"] for r in records]
    content_curve = [r["content_shift"] for r in records]
    method_drift_total = round(sum(method_curve), 3)
    content_drift_total = round(sum(content_curve), 3)
    divergence_between_method_and_content = round(
        st.mean([abs(m - c) for m, c in zip(method_curve, content_curve)]), 3)

    # ---- 6. transition-level state ----
    tdeltas = [r["transition_delta"] for r in records]
    abruptness = round(max(tdeltas), 3)
    cumulative_drift_energy = round(sum(tdeltas), 3)
    rec_turns = [t for t, r in enumerate(records) if r["constraints_recovered"]]
    stab = [1 for r in rec_turns if r + 1 < n_turns and records[r + 1]["transition_delta"] < records[r]["transition_delta"]]
    stabilization_after_recovery = round(len(stab) / len(rec_turns), 3) if rec_turns else 1.0

    # ---- 5. drift event ledger ----
    ledger = [{"turn": r["turn_id"], "events": r["drift_events"]} for r in records if r["drift_events"]]

    composite_drift_v1 = round(_clamp(st.mean([
        1.0 - constraint_half_life_mean,
        unrecovered / n_con,
        irreversible_lock_in_proxy,
        _clamp(cumulative_drift_energy / max(1, n_turns - 1)),
        1.0 - recovery_quality_proxy,
        1.0 - branch_entropy_proxy,
    ])), 3)

    return {
        "turns": n_turns,
        "constraint_half_life_mean": constraint_half_life_mean,
        "max_constraint_decay": max_constraint_decay,
        "unrecovered_constraints": unrecovered,
        "rhetorical_recovery_count": rhet,
        "operational_recovery_count": op,
        "failed_recovery_count": failed,
        "recovery_quality_proxy": recovery_quality_proxy,
        "branch_entropy_proxy": branch_entropy_proxy,
        "branch_collapse_events": branch_collapse_events,
        "irreversible_lock_in_proxy": irreversible_lock_in_proxy,
        "method_drift_total": method_drift_total,
        "content_drift_total": content_drift_total,
        "divergence_between_method_and_content": divergence_between_method_and_content,
        "abruptness": abruptness,
        "stabilization_after_recovery": stabilization_after_recovery,
        "cumulative_drift_energy": cumulative_drift_energy,
        "composite_drift_v1": composite_drift_v1,
        "drift_event_ledger": ledger,
    }


# (v1 metric, auditor dim, expected sign)
COMPARE_PAIRS = [
    ("composite_drift_v1", "drift_severity", "+"),
    ("constraint_half_life_mean", "constraint_adherence", "+"),
    ("recovery_quality_proxy", "recoverability", "+"),
    ("irreversible_lock_in_proxy", "drift_severity", "+"),
    ("cumulative_drift_energy", "drift_severity", "+"),
    ("branch_entropy_proxy", "alternative_coverage", "+"),
    ("divergence_between_method_and_content", "objective_fidelity", "-"),
]

__all__ = ["COMPARE_PAIRS", "summarize_v1"]
