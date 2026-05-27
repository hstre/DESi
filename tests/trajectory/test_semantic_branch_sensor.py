"""Targeted tests for the semantic branch sensor + probe + v1.3 (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

import semantic_branch_sensor as sbs  # noqa: E402
from branch_equivalence_probe import PAIRS, _select_threshold  # noqa: E402

_AVAIL = sbs.available()
_need = pytest.mark.skipif(not _AVAIL, reason="semantic sensor (model2vec/potion) unavailable")


def test_model_info_shape():
    info = sbs.model_info()
    assert info["model"] == "minishlab/potion-base-8M"
    assert "available" in info and "deterministic" in info


def test_blocking_behavior_no_fake(monkeypatch):
    # force the loader to report unavailable -> similarity must return None, never fake
    monkeypatch.setattr(sbs, "_loaded", True)
    monkeypatch.setattr(sbs, "_model", None)
    assert sbs.available() is False
    assert sbs.semantic_branch_similarity("a", "b") is None


@_need
def test_similarity_deterministic_and_bounded():
    s1 = sbs.semantic_branch_similarity("randomized controlled trial", "randomized intervention study")
    s2 = sbs.semantic_branch_similarity("randomized controlled trial", "randomized intervention study")
    assert s1 == s2 and -1.0 <= s1 <= 1.0


@_need
def test_equivalent_scores_above_distinct():
    eq = sbs.semantic_branch_similarity("randomized controlled trial", "randomized intervention study")
    ne = sbs.semantic_branch_similarity("marketing campaign", "laboratory assay")
    assert eq > ne


@_need
def test_probe_threshold_selection_high_precision():
    scored = [(lab, sbs.semantic_branch_similarity(a, b)) for lab, a, b in PAIRS]
    thr, f1, (prec, rec) = _select_threshold(scored)
    assert 0.0 < thr < 1.0
    assert f1 >= 0.7            # the probe must be reasonably separable
    assert prec >= 0.8          # threshold should not over-fold distinct pairs


@_need
def test_v13_semantic_fold_keeps_distinct_separate():
    from trajectory_trace_v13 import semantic_fold
    f = semantic_fold(["forward-model grid comparison", "differential spectrophotometry",
                       "ethnographic interviews with operators"], threshold=0.31)
    assert f is not None
    assert f["n_clusters"] == 3          # distinct methods stay separate at the frozen threshold


def test_probe_pairs_balance():
    eq = sum(1 for lab, _, _ in PAIRS if lab == 1)
    ne = sum(1 for lab, _, _ in PAIRS if lab == 0)
    assert eq >= 10 and ne >= 10         # enough of each class for a meaningful probe
