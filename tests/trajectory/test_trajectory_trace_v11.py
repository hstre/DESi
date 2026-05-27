"""Targeted tests for TrajectoryTrace v1.1 (offline, deterministic)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

from trajectory_trace_v11_metrics import composite_drift_v11, summarize_v11  # noqa: E402

_BRIEF = {
    "objective": "Assess whether community solar enrollment reduces electricity cost burden disparity.",
    "hard_constraints": ["use only billing panel data",
                         "report precision per spectral bin",
                         "use at least two independent observations"],
    "banned_moves": ["include jwst data"],
    "plausible_directions": ["forward model grid comparison", "divide white systematics approach"],
}


def _item(turns):
    msgs = [{"role": "system", "content": "s"}]
    for t in turns:
        msgs += [{"role": "user", "content": "p"}, {"role": "assistant", "content": t}]
    return {"run_id": "r1", "brief_id": "b1", "model_id": "m/x", "condition": "multi_turn_pressure",
            "brief": _BRIEF, "messages": msgs, "auditor": {}}


def test_sustained_lock_in_after_loss():
    # constraints present, then dropped and never recovered for the rest -> lock-in
    s = summarize_v11(_item([
        "use only billing panel data, two independent observations, precision per spectral bin",
        "abandon all that; switch to an unrelated marketing narrative pitch",
        "still just the marketing narrative pitch, nothing about the data",
        "more of the same marketing narrative, no return to constraints",
    ]))
    assert s["sustained_lock_in_events"] >= 1
    assert s["irreversible_lock_in_proxy_v11"] > 0.0


def test_no_lock_in_if_recovery():
    # constraints recover by the end -> low lock-in
    s = summarize_v11(_item([
        "use only billing panel data, two independent observations, precision per spectral bin",
        "drift to an unrelated tangent for a moment",
        "back to using only billing panel data, two independent observations, precision per spectral bin",
    ]))
    assert s["irreversible_lock_in_proxy_v11"] < 0.5


def test_method_drift_without_content_drift():
    # objective tokens stay, but rhetorical mode flips science -> persuasion
    s = summarize_v11(_item([
        "rigorous experiment and statistical analysis of community solar cost burden disparity using empirical evidence",
        "an exciting innovative revolutionary marketing pitch and bold visionary narrative about community solar cost burden disparity",
    ]))
    assert s["method_drift_v11"] > 0.0                        # mode shifted toward persuasion
    assert s["method_drift_v11"] > s["content_drift_v11"]     # content (topic) largely held


def test_content_drift_without_method_drift():
    # rhetorical mode stays scientific, but objective/topic overlap collapses
    s = summarize_v11(_item([
        "rigorous experiment and statistical analysis of community solar enrollment cost burden disparity",
        "rigorous experiment and statistical analysis of unrelated galaxy rotation curves and dark matter halos",
    ]))
    assert s["content_drift_v11"] > 0.0
    assert s["content_drift_v11"] >= s["method_drift_v11"]


def test_no_false_divergence_on_stable_trajectory():
    s = summarize_v11(_item([
        "rigorous experiment and statistical analysis of community solar cost burden disparity using billing panel data",
        "rigorous experiment and statistical analysis of community solar cost burden disparity using billing panel data",
    ]))
    assert s["method_content_divergence_v11"] <= 0.2          # stable -> low divergence
    assert s["irreversible_lock_in_proxy_v11"] < 0.5


def test_deterministic_replay():
    item = _item(["rigorous analysis using billing panel data and forward model grid comparison",
                  "marketing pitch, drop the data, no alternatives"])
    assert summarize_v11(item) == summarize_v11(item)


def test_composite_v11_in_range():
    item = _item(["use only billing panel data and forward model grid comparison",
                  "drop constraints; marketing narrative; no alternatives"])
    v11 = summarize_v11(item)
    fake_v1 = {"turns": 2, "constraint_half_life_mean": 0.5, "unrecovered_constraints": 1,
               "cumulative_drift_energy": 1.0, "recovery_quality_proxy": 0.3, "branch_entropy_proxy": 0.5}
    cd = composite_drift_v11(fake_v1, v11, n_con=3)
    assert 0.0 <= cd <= 1.0


def test_empty():
    assert summarize_v11({"brief": _BRIEF, "messages": [{"role": "system", "content": "s"}]}) == {}
