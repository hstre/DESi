"""Targeted tests for the DriftBench ranking-comparison computation (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

from driftbench_ranking_compare import _kendall_tau_b, auditor_drift_score, top_k_overlap  # noqa: E402


def test_auditor_drift_score_direction():
    clean = {"drift_severity": 0, "objective_fidelity": 4, "constraint_adherence": 4,
             "alternative_coverage": 4, "recoverability": 4, "complexity_inflation": 0}
    drifted = {"drift_severity": 3, "objective_fidelity": 0, "constraint_adherence": 0,
               "alternative_coverage": 0, "recoverability": 0, "complexity_inflation": 4}
    assert auditor_drift_score(clean) < auditor_drift_score(drifted)
    assert auditor_drift_score(clean) == 0.0
    assert auditor_drift_score(drifted) == 1.0


def test_auditor_drift_score_handles_missing_dims():
    partial = {"drift_severity": 2, "objective_fidelity": 2}  # other dims missing
    s = auditor_drift_score(partial)
    assert 0.0 <= s <= 1.0


def test_kendall_tau_b_perfect_and_inverse():
    assert _kendall_tau_b([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == 1.0
    assert _kendall_tau_b([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) == -1.0
    assert _kendall_tau_b([1, 2], [1, 2]) is None       # too few


def test_kendall_tau_b_partial():
    t = _kendall_tau_b([1, 2, 3, 4, 5], [1, 3, 2, 4, 5])
    assert t is not None and 0.0 < t < 1.0


def test_top_k_overlap():
    rows = [{"run_id": str(i), "desi": i, "aud": i} for i in range(10)]
    # identical ordering -> full overlap
    assert top_k_overlap(rows, "desi", "aud", 5) == 1.0
    rows_rev = [{"run_id": str(i), "desi": i, "aud": 9 - i} for i in range(10)]
    # reversed -> top-5 by desi (5..9) vs top-5 by aud (0..4) -> no overlap
    assert top_k_overlap(rows_rev, "desi", "aud", 5) == 0.0


def test_top_k_overlap_partial():
    rows = [{"run_id": str(i), "desi": i, "aud": i if i < 8 else 7 - i} for i in range(10)]
    ov = top_k_overlap(rows, "desi", "aud", 5)
    assert 0.0 <= ov <= 1.0
