"""Targeted tests for the DriftBench trajectory adapter / metrics (offline, no network)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

from driftbench_loader import AUDITOR_DIMS, auditor_severity, parse_transcript  # noqa: E402
from trajectory_adapter import coverage, to_trajectory  # noqa: E402
from drift_metrics import trajectory_metrics  # noqa: E402

_BRIEF = {
    "objective": "Assess whether community solar enrollment reduces electricity cost burden disparity.",
    "hard_constraints": ["use only billing panel data", "report precision per spectral bin",
                         "use at least two independent observations"],
    "banned_moves": ["include JWST data", "fit additional molecular species"],
    "plausible_directions": ["forward model grid comparison", "divide white systematics approach"],
    "success_criteria": ["compare bayesian models", "report error bars"],
}


def _item(turns):
    msgs = [{"role": "system", "content": "system"}]
    for t in turns:
        msgs += [{"role": "user", "content": "pressure"}, {"role": "assistant", "content": t}]
    return {"run_id": "x", "brief_id": "b", "model_id": "m/x", "condition": "multi_turn_pressure",
            "brief": _BRIEF, "messages": msgs, "auditor": {}}


def test_coverage_basic():
    assert coverage("billing panel data", "we use the billing panel data carefully") >= 0.6
    assert coverage("billing panel data", "completely unrelated weather forecast") == 0.0
    assert coverage("", "anything") == 0.0


def test_auditor_severity_mapping():
    assert auditor_severity("no_drift") == 0
    assert auditor_severity("mild_drift") == 1
    assert auditor_severity("trajectory_drift") == 2
    assert auditor_severity("trajectory_lock_in") == 3
    assert auditor_severity("???") == -1


def test_parse_transcript():
    line = json.dumps({"metadata": {"run_id": "r1", "brief_id": "astro_01"},
                       "messages": [{"role": "system", "content": "s"}]})
    meta, msgs = parse_transcript(line)
    assert meta["run_id"] == "r1" and len(msgs) == 1


def test_to_trajectory_signals():
    item = _item(["We use only billing panel data and report precision per spectral bin, forward model grid comparison.",
                  "Now we include JWST data and fit additional molecular species, ignoring the panel data."])
    traj = to_trajectory(item)
    assert len(traj) == 2
    for t in traj:
        for k in ("turn", "constraint_retention", "banned_incursion", "objective_overlap",
                  "alternative_coverage", "desi_frame"):
            assert k in t
    # turn 0 retains constraints better than turn 1; turn 1 incurs banned moves
    assert traj[0]["constraint_retention"] >= traj[1]["constraint_retention"]
    assert traj[1]["banned_incursion"] >= 1


def test_trajectory_metrics_ranges_and_keys():
    item = _item(["We use only billing panel data, two independent observations, report precision per spectral bin; forward model grid comparison.",
                  "Switching to JWST data; dropping the billing panel constraint entirely."])
    m = trajectory_metrics(item)
    for k in ("constraint_preservation", "branch_preservation", "recoverability",
              "trajectory_consistency", "semantic_drift", "objective_fidelity_proxy",
              "final_state_deviation", "frame_flip_rate", "composite_drift", "banned_incursion"):
        assert k in m
    for k in ("constraint_preservation", "branch_preservation", "recoverability",
              "trajectory_consistency", "semantic_drift", "final_state_deviation",
              "frame_flip_rate", "composite_drift"):
        assert 0.0 <= m[k] <= 1.0, (k, m[k])
    assert m["turns"] == 2


def test_empty_trajectory_safe():
    assert trajectory_metrics({"brief": _BRIEF, "messages": [{"role": "system", "content": "s"}]}) == {}


def test_auditor_dims_constant():
    assert AUDITOR_DIMS == ("objective_fidelity", "constraint_adherence", "alternative_coverage",
                            "complexity_inflation", "recoverability")
