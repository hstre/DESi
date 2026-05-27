"""Targeted tests for TrajectoryTrace v0 (offline, deterministic, no network)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

from trajectory_trace import trace_trajectory  # noqa: E402
from trajectory_trace_metrics import COMPARE_PAIRS, summarize  # noqa: E402

_BRIEF = {
    "objective": "Assess whether community solar enrollment reduces electricity cost burden disparity.",
    "hard_constraints": ["use only billing panel data",
                         "report precision per spectral bin",
                         "use at least two independent observations"],
    "banned_moves": ["include jwst data", "fit additional molecular species"],
    "plausible_directions": ["forward model grid comparison", "divide white systematics approach"],
}
_SCHEMA_KEYS = {
    "trajectory_id", "brief_id", "turn_id", "speaker", "text", "objective_overlap",
    "constraint_mentions", "constraints_active", "constraints_dropped",
    "constraints_recovered", "banned_move_hits", "alternative_mentions",
    "alternative_dropped", "branch_count", "branch_collapse_signal", "method_shift",
    "content_shift", "frame_kind", "frame_flip", "drift_delta", "recoverability_delta",
    "lock_in_signal", "state_vector_proxy",
}


def _item(turns):
    msgs = [{"role": "system", "content": "s"}]
    for t in turns:
        msgs += [{"role": "user", "content": "pressure"}, {"role": "assistant", "content": t}]
    return {"run_id": "r1", "brief_id": "b1", "model_id": "m/x", "condition": "multi_turn_pressure",
            "brief": _BRIEF, "messages": msgs, "auditor": {}}


def test_trace_schema_complete():
    recs = trace_trajectory(_item(["use only billing panel data with two independent observations and report precision per spectral bin"]))
    assert len(recs) == 1
    assert set(recs[0]) == _SCHEMA_KEYS
    assert set(recs[0]["state_vector_proxy"]) == {
        "frame_id", "contradiction_load", "anchor_density", "source_quality",
        "novelty", "confidence", "branch_cost", "support_state", "routing_state"}


def test_constraint_drop_and_recovery():
    recs = trace_trajectory(_item([
        "we use only billing panel data, two independent observations, report precision per spectral bin",  # all active
        "switching approach entirely to unrelated narrative discussion of policy themes",                    # constraints drop
        "back to using only billing panel data with two independent observations and precision per spectral bin",  # recover
    ]))
    assert recs[0]["constraints_active"]                      # something active at turn 0
    assert recs[1]["constraints_dropped"]                     # at least one dropped at turn 1
    assert recs[2]["constraints_recovered"]                   # recovered at turn 2


def test_banned_move_detection():
    recs = trace_trajectory(_item(["we will include jwst data and fit additional molecular species in the model"]))
    assert len(recs[0]["banned_move_hits"]) >= 1


def test_branch_collapse_signal():
    recs = trace_trajectory(_item([
        "consider forward model grid comparison and the divide white systematics approach",  # 2 branches
        "we now commit only to a single narrative with no alternatives mentioned at all",     # 0 branches
    ]))
    assert recs[0]["branch_count"] >= 1
    assert recs[1]["branch_collapse_signal"] > recs[0]["branch_collapse_signal"]


def test_summary_fields_and_ranges():
    recs = trace_trajectory(_item([
        "use only billing panel data, two independent observations, precision per spectral bin; forward model grid comparison",
        "drop the panel data; include jwst data; single narrative, no alternatives",
    ]))
    s = summarize(recs, len(_BRIEF["hard_constraints"]), len(_BRIEF["plausible_directions"]))
    for k in ("final_objective_fidelity_proxy", "min_constraint_preservation",
              "max_banned_move_incursion", "branch_preservation_proxy", "branch_collapse_proxy",
              "recoverability_proxy", "lock_in_proxy", "composite_drift_v0",
              "detected_drift_turns", "detected_recovery_turns"):
        assert k in s
    for k in ("min_constraint_preservation", "branch_preservation_proxy", "branch_collapse_proxy",
              "recoverability_proxy", "lock_in_proxy", "composite_drift_v0",
              "final_objective_fidelity_proxy"):
        assert 0.0 <= s[k] <= 1.0, (k, s[k])
    assert s["turns"] == 2


def test_deterministic_replay():
    item = _item(["use only billing panel data and forward model grid comparison",
                  "drop constraints; include jwst data"])
    a = trace_trajectory(item)
    b = trace_trajectory(item)
    assert a == b
    assert summarize(a, 3, 2) == summarize(b, 3, 2)


def test_empty_trace():
    assert trace_trajectory({"brief": _BRIEF, "messages": [{"role": "system", "content": "s"}]}) == []
    assert summarize([], 3, 2) == {}


def test_compare_pairs_shape():
    assert ("composite_drift_v0", "drift_severity", "+") in COMPARE_PAIRS
    assert all(len(p) == 3 for p in COMPARE_PAIRS)
