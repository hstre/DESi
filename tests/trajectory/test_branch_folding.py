"""Targeted tests for semantic branch folding (v1.2) -- offline, deterministic."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

from trajectory_branch_folding import fold_directions, normalize  # noqa: E402
from trajectory_trace_v12_metrics import composite_drift_v12, summarize_v12  # noqa: E402

_BRIEF_DISTINCT = {
    "objective": "Test the atmosphere of an exoplanet.",
    "hard_constraints": ["use archival data", "report per-bin precision", "use two transits"],
    "banned_moves": ["use jwst data"],
    "plausible_directions": [
        "forward-model grid comparison fitting transmission spectra",
        "differential spectrophotometry using a comparison star",
        "ethnographic interviews with telescope operators",
    ],
}


def _item(turns, brief):
    msgs = [{"role": "system", "content": "s"}]
    for t in turns:
        msgs += [{"role": "user", "content": "p"}, {"role": "assistant", "content": t}]
    return {"run_id": "r1", "brief_id": "b1", "model_id": "m/x", "condition": "multi_turn_pressure",
            "brief": brief, "messages": msgs, "auditor": {}}


def test_rhetorical_variants_fold():
    # same design, parameter swap, shared vocabulary -> should fold to 1 cluster
    dirs = ["paired-plot design comparing rye cover crop vs fallow with annual soil cores",
            "paired-plot design comparing crimson clover cover crop vs fallow with annual soil cores"]
    f = fold_directions(dirs)
    assert f["n_clusters"] == 1
    assert f["branch_redundancy_ratio"] > 0.0


def test_real_method_differences_do_not_fold():
    # genuinely different methods, disjoint vocabulary -> stay separate
    dirs = ["controlled randomized clinical trial of the drug",
            "ethnographic fieldwork observing community practices"]
    f = fold_directions(dirs)
    assert f["n_clusters"] == 2
    assert f["branch_redundancy_ratio"] == 0.0


def test_no_false_fold_on_distinct_branches():
    f = fold_directions(_BRIEF_DISTINCT["plausible_directions"])
    assert f["n_clusters"] == 3            # all three distinct
    assert f["branch_novelty_score"] == 1.0


def test_normalize_canonicalises_method_synonyms():
    # study/trial/experiment collapse to the same role token
    assert "STUDY" in normalize("a controlled study")
    assert "STUDY" in normalize("a controlled trial")
    assert "STUDY" in normalize("a controlled experiment")


def test_collapse_after_folding():
    # mention 2 distinct clusters then drop to 1 -> a semantic collapse event
    item = _item([
        "we will use forward-model grid comparison fitting transmission spectra and also differential spectrophotometry using a comparison star",
        "now only forward-model grid comparison fitting transmission spectra, nothing else",
    ], _BRIEF_DISTINCT)
    s = summarize_v12(item)
    assert s["semantic_branch_collapse_events"] >= 1
    assert s["folded_branch_count_final"] <= s["folded_branch_count_mean"] * 2  # sanity


def test_deterministic_replay():
    item = _item(["forward-model grid comparison fitting transmission spectra",
                  "differential spectrophotometry using a comparison star"], _BRIEF_DISTINCT)
    assert summarize_v12(item) == summarize_v12(item)
    assert fold_directions(_BRIEF_DISTINCT["plausible_directions"]) == fold_directions(_BRIEF_DISTINCT["plausible_directions"])


def test_composite_v12_in_range():
    item = _item(["forward-model grid comparison", "differential spectrophotometry"], _BRIEF_DISTINCT)
    v12 = summarize_v12(item)
    fake_v1 = {"turns": 2, "constraint_half_life_mean": 0.5, "unrecovered_constraints": 1,
               "cumulative_drift_energy": 1.0, "recovery_quality_proxy": 0.3}
    cd = composite_drift_v12(fake_v1, 0.2, v12, n_con=3)
    assert 0.0 <= cd <= 1.0


def test_empty():
    assert summarize_v12({"brief": _BRIEF_DISTINCT, "messages": [{"role": "system", "content": "s"}]}) == {}
