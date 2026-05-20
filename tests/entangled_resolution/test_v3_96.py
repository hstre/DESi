"""v3.96 — entanglement resolution tests."""
from __future__ import annotations

import json
import pathlib

from desi.entangled_resolution.predict import (
    MAX_SEARCH_SIZE,
    all_resolution_outcomes,
    auc_for, baseline_frame_normalized_auc,
    baseline_frame_normalized_fpr,
    best_feature_set, best_outcome,
    cluster_for, fpr_for,
    purity_for, resolved_auc,
    resolved_fpr, resolved_purity,
)
from desi.entangled_resolution.report import (
    AUC_THRESHOLD, PURITY_THRESHOLD,
    build_entangled_resolution_artifact,
    build_report,
)
from desi.entangled_resolution.resolve import (
    FeatureSpec, RESIDUAL_DIMS,
    TEMPORAL_DIMS, feature_vector_for_spec,
)


def test_residual_dims_are_state_dims() -> None:
    """RESIDUAL_DIMS must equal the closed nine
    state dimensions."""
    from desi.epistemic_trajectory.state import (
        DIMENSION_NAMES,
    )
    assert RESIDUAL_DIMS == DIMENSION_NAMES


def test_temporal_dims_prefixed() -> None:
    """Each TEMPORAL_DIMS entry mirrors one state
    dim, prefixed with 'temporal_'."""
    from desi.epistemic_trajectory.state import (
        DIMENSION_NAMES,
    )
    for d in DIMENSION_NAMES:
        assert f"temporal_{d}" in TEMPORAL_DIMS


def test_feature_vector_size_matches_spec() -> None:
    """A spec with R residual + T temporal dims
    yields a vector with 5*R + T entries kept
    nonzero (rest zero in the residual padding)."""
    spec = FeatureSpec(
        residual_dims=("branch_cost",),
        temporal_dims=("temporal_frame_id",),
    )
    vecs = feature_vector_for_spec(spec)
    assert len(vecs) == 19
    sample = next(iter(vecs.values()))
    assert len(sample) == 45 + 1


def test_candidate_spec_count_is_three_hundred_forty_eight() -> None:
    """129 residual + 129 temporal + 81 (1x1
    cross) + 9 (full + temporal) = 348."""
    assert len(all_resolution_outcomes()) == 348


def test_resolved_purity_in_unit_interval() -> None:
    assert 0.0 <= resolved_purity() <= 1.0


def test_resolved_purity_does_not_pass_gate() -> None:
    """Concept Gate condition #2 fails - true
    doppelganger."""
    assert resolved_purity() < PURITY_THRESHOLD


def test_resolved_auc_in_unit_interval() -> None:
    assert 0.0 <= resolved_auc() <= 1.0


def test_resolved_auc_does_not_pass_gate() -> None:
    """Concept Gate condition #3 fails - true
    doppelganger."""
    assert resolved_auc() < AUC_THRESHOLD


def test_resolved_fpr_in_unit_interval() -> None:
    assert 0.0 <= resolved_fpr() <= 1.0


def test_best_outcome_metrics_consistent_with_best_set() -> None:
    best = best_outcome()
    assert best.purity == resolved_purity()
    assert best.auc == resolved_auc()
    assert best.fpr == resolved_fpr()


def test_best_feature_set_is_feature_spec() -> None:
    assert isinstance(best_feature_set(), FeatureSpec)


def test_recommendation_is_entanglement_persists() -> None:
    """All four discrimination conditions fail
    despite the augmented feature space."""
    assert build_report().recommendation == (
        "ENTANGLEMENT_PERSISTS"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ENTANGLEMENT_RESOLVED",
        "ENTANGLEMENT_PARTIALLY_RESOLVED",
        "ENTANGLEMENT_PERSISTS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_baselines_match_v392() -> None:
    """v3.96 imports the v3.92 metrics, never
    recomputes them."""
    from desi.frame_normalized_predictive.forecast import (
        frame_normalized_auc, frame_normalized_fpr,
        optimal_threshold,
    )
    assert (
        baseline_frame_normalized_auc()
        == frame_normalized_auc()
    )
    assert (
        baseline_frame_normalized_fpr()
        == frame_normalized_fpr(optimal_threshold())
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_artifact_lists_all_outcomes() -> None:
    art = build_entangled_resolution_artifact()
    assert len(art["resolution_outcomes"]) == 348


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_96" / "report.json").read_text(
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
