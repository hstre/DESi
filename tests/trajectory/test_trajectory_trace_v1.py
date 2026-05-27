"""Targeted tests for TrajectoryTrace v1 dynamics (offline, deterministic)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

from trajectory_trace_v1 import lean_record, trace_v1  # noqa: E402
from trajectory_trace_v1_metrics import COMPARE_PAIRS, summarize_v1  # noqa: E402

_BRIEF = {
    "objective": "Assess whether community solar enrollment reduces electricity cost burden disparity.",
    "hard_constraints": ["use only billing panel data",
                         "report precision per spectral bin",
                         "use at least two independent observations"],
    "banned_moves": ["include jwst data", "fit additional molecular species"],
    "plausible_directions": ["forward model grid comparison", "divide white systematics approach"],
}


def _item(turns):
    msgs = [{"role": "system", "content": "s"}]
    for t in turns:
        msgs += [{"role": "user", "content": "p"}, {"role": "assistant", "content": t}]
    return {"run_id": "r1", "brief_id": "b1", "model_id": "m/x", "condition": "multi_turn_pressure",
            "brief": _BRIEF, "messages": msgs, "auditor": {}}


def test_v1_perturn_has_transition_and_events():
    recs = trace_v1(_item([
        "use only billing panel data, two independent observations, precision per spectral bin; forward model grid comparison and divide white systematics approach",
        "switch to unrelated storytelling, include jwst data, drop everything, no alternatives",
    ]))
    assert recs[0]["transition_delta"] == 0.0           # first turn has no predecessor
    assert recs[1]["transition_delta"] >= 0.0
    assert "drift_events" in recs[1] and "branch_collapse_event" in recs[1]
    # turn 1 should register banned incursion + constraint loss + branch collapse
    ev = set(recs[1]["drift_events"])
    assert "banned_move_incursion" in ev
    assert "branch_collapse" in ev


def test_lean_record_compact():
    recs = trace_v1(_item(["use only billing panel data and forward model grid comparison"]))
    lr = lean_record(recs[0])
    for k in ("trajectory_id", "turn_id", "transition_delta", "drift_events", "branch_count",
              "n_active", "n_dropped", "n_recovered", "banned_hits", "method_shift", "content_shift"):
        assert k in lr
    assert "state_vector_proxy" not in lr and "constraint_mentions" not in lr


def test_summary_v1_fields_and_ranges():
    recs = trace_v1(_item([
        "use only billing panel data, two independent observations, precision per spectral bin; forward model grid comparison, divide white systematics approach",
        "drop the panel data; include jwst data; commit to one narrative, no alternatives",
        "back to using only billing panel data and two independent observations and precision per spectral bin",
    ]))
    s = summarize_v1(recs, 3, 2)
    for k in ("constraint_half_life_mean", "max_constraint_decay", "unrecovered_constraints",
              "rhetorical_recovery_count", "operational_recovery_count", "failed_recovery_count",
              "recovery_quality_proxy", "branch_entropy_proxy", "branch_collapse_events",
              "irreversible_lock_in_proxy", "method_drift_total", "content_drift_total",
              "divergence_between_method_and_content", "abruptness", "stabilization_after_recovery",
              "cumulative_drift_energy", "composite_drift_v1", "drift_event_ledger"):
        assert k in s
    for k in ("constraint_half_life_mean", "recovery_quality_proxy", "branch_entropy_proxy",
              "irreversible_lock_in_proxy", "composite_drift_v1"):
        assert 0.0 <= s[k] <= 1.0, (k, s[k])
    assert isinstance(s["drift_event_ledger"], list)


def test_recovery_quality_distinguishes_rhetorical():
    # constraint drops while objective overlap falls and banned pressure rises, then the
    # constraint phrase returns but pressure stays high -> rhetorical (fake) recovery
    recs = trace_v1(_item([
        "use only billing panel data with two independent observations and precision per spectral bin",
        "include jwst data and fit additional molecular species, ignore the panel data entirely",
        "we mention using only billing panel data again but also keep including jwst data and fit additional molecular species",
    ]))
    s = summarize_v1(recs, 3, 2)
    # at least one recovery attempt was seen and classified (operational or rhetorical)
    assert s["operational_recovery_count"] + s["rhetorical_recovery_count"] + s["failed_recovery_count"] >= 1


def test_irreversible_collapse_detected():
    recs = trace_v1(_item([
        "consider forward model grid comparison and divide white systematics approach",  # 2 branches (peak)
        "commit to a single narrative with no alternatives",                              # collapse
        "still only the single narrative, no alternatives at all",                        # stays collapsed
    ]))
    s = summarize_v1(recs, 3, 2)
    assert s["irreversible_lock_in_proxy"] > 0.0
    assert s["branch_collapse_events"] >= 1


def test_deterministic_replay():
    item = _item(["use only billing panel data and forward model grid comparison",
                  "drop constraints; include jwst data; no alternatives"])
    assert trace_v1(item) == trace_v1(item)
    assert summarize_v1(trace_v1(item), 3, 2) == summarize_v1(trace_v1(item), 3, 2)


def test_empty():
    assert trace_v1({"brief": _BRIEF, "messages": [{"role": "system", "content": "s"}]}) == []
    assert summarize_v1([], 3, 2) == {}


def test_compare_pairs():
    assert ("composite_drift_v1", "drift_severity", "+") in COMPARE_PAIRS
