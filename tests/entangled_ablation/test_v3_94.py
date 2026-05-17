"""v3.94 — exhaustive dim-subset search tests."""
from __future__ import annotations

import json
import pathlib

from desi.entangled_ablation.ablation import (
    baseline_purity, cluster_entangled_with,
    cluster_purity,
    projected_entangled_vectors,
)
from desi.entangled_ablation.report import (
    PURITY_THRESHOLD,
    build_entangled_ablation_artifact,
    build_report,
)
from desi.entangled_ablation.search import (
    MAX_SUBSET_SIZE,
    all_subset_outcomes, best_dim_set,
    best_purity, dimensionality_cost,
    purity_above_baseline_count, stability,
)


def test_subset_count_is_one_hundred_twenty_nine() -> None:
    """C(9,1)+C(9,2)+C(9,3) = 9 + 36 + 84 = 129."""
    assert len(all_subset_outcomes()) == 129


def test_max_subset_size_is_three() -> None:
    assert MAX_SUBSET_SIZE == 3


def test_baseline_purity_is_ten_over_nineteen() -> None:
    """G has 9, E has 10 ⇒ majority = 10/19."""
    assert baseline_purity() == round(10 / 19, 6)


def test_best_purity_in_unit_interval() -> None:
    assert 0.0 <= best_purity() <= 1.0


def test_best_purity_does_not_pass_concept_gate() -> None:
    """Killerfrage: reichen 1-3 zusaetzliche Dims?
    Answer: NO - no subset clears the 0.70
    universality threshold."""
    assert best_purity() < PURITY_THRESHOLD


def test_no_subset_beats_baseline() -> None:
    """If even one subset beat baseline, there
    would be a separating dim. None does, so
    G and E are true doppelgangers in the state-
    vector representation."""
    assert purity_above_baseline_count() == 0


def test_dimensionality_cost_is_one() -> None:
    """Among the tied-at-baseline subsets the
    smallest dim count is 1."""
    assert dimensionality_cost() == 1


def test_stability_is_one() -> None:
    """Every subset ties the ceiling - the search
    is fully degenerate over the state-vector
    space."""
    assert stability() == 1.0


def test_clustering_is_deterministic() -> None:
    a = cluster_entangled_with(
        frozenset({"branch_cost"}),
    )
    b = cluster_entangled_with(
        frozenset({"branch_cost"}),
    )
    assert [c.to_dict() for c in a] == (
        [c.to_dict() for c in b]
    )


def test_projection_zeros_dropped_dims() -> None:
    from desi.epistemic_trajectory.state import (
        DIMENSION_NAMES,
    )
    keep = frozenset({"branch_cost"})
    keep_idx = set()
    for d in keep:
        di = DIMENSION_NAMES.index(d)
        keep_idx.update(
            s * 9 + di for s in range(5)
        )
    vecs = projected_entangled_vectors(keep)
    for tid, v in vecs.items():
        for i, x in enumerate(v):
            if i not in keep_idx:
                assert x == 0.0


def test_recommendation_is_no_separating_set() -> None:
    """No subset beat baseline ⇒ verdict must be
    NO_SEPARATING_DIM_SET."""
    assert build_report().recommendation == (
        "NO_SEPARATING_DIM_SET"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "SEPARATING_DIM_SET_FOUND",
        "WEAK_SEPARATING_DIM_SET",
        "NO_SEPARATING_DIM_SET",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_artifact_lists_all_subsets() -> None:
    art = build_entangled_ablation_artifact()
    assert len(art["subset_outcomes"]) == 129


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_94" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable
