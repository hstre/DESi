"""v3.101 - T10 candidate dimension search tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10.candidate import (
    CANDIDATE_DIMS, CandidateDim,
    candidate_values,
)
from desi.t10.report import (
    AUC_THRESHOLD,
    build_report,
    build_t10_dimension_search_artifact,
)
from desi.t10.search import (
    all_candidate_outcomes,
    augmented_vectors,
    best_outcome,
    candidates_above_auc_threshold,
    has_dominant_candidate,
)


def test_six_candidate_dims() -> None:
    """Directive § v3.101 lists six candidate
    dimensions."""
    assert len(CANDIDATE_DIMS) == 6


def test_candidate_enum_matches_taxonomy() -> None:
    enum_values = {c.value for c in CandidateDim}
    assert enum_values == set(CANDIDATE_DIMS)


def test_candidate_values_cover_nineteen() -> None:
    for c in CANDIDATE_DIMS:
        vals = candidate_values(c)
        assert len(vals) == 19


def test_augmented_vector_has_fifty_dims() -> None:
    """45-d residual + 5 broadcast slots."""
    for c in CANDIDATE_DIMS:
        v = augmented_vectors(c)
        sample = next(iter(v.values()))
        assert len(sample) == 50


def test_each_candidate_outcome_recorded() -> None:
    outs = all_candidate_outcomes()
    assert len(outs) == 6
    candidates = {o.candidate for o in outs}
    assert candidates == set(CANDIDATE_DIMS)


def test_best_candidate_is_contradiction_type() -> None:
    """Killerfrage: welche minimale Information
    fehlt? The explicit self-referential
    contradiction marker (G's circular pattern)
    separates G/E perfectly."""
    assert best_outcome().candidate == (
        CandidateDim.CONTRADICTION_TYPE.value
    )


def test_best_candidate_auc_passes_gate() -> None:
    """Concept Gate condition #1: candidate_auc
    >= 0.70."""
    assert best_outcome().auc >= AUC_THRESHOLD


def test_best_candidate_auc_is_one() -> None:
    assert best_outcome().auc == 1.0


def test_best_candidate_purity_is_one() -> None:
    assert best_outcome().purity == 1.0


def test_best_candidate_margin_positive() -> None:
    """Positive margin = fully separable
    populations."""
    assert best_outcome().margin > 0.0


def test_best_candidate_produces_two_clusters() -> None:
    """The 19 anchors split cleanly into the
    family-sized clusters (10 + 9)."""
    best = best_outcome()
    assert best.cluster_count == 2
    assert sorted(best.cluster_sizes) == [9, 10]


def test_at_least_three_candidates_above_threshold() -> None:
    above = candidates_above_auc_threshold(
        AUC_THRESHOLD,
    )
    assert len(above) >= 3


def test_dominant_candidate_detected() -> None:
    assert has_dominant_candidate() is True


def test_contradiction_type_is_binary() -> None:
    """contradiction_type emits 1.0 for the
    circular G family and 0.0 for the syllogism
    E family - the audit's central finding."""
    vals = candidate_values(
        CandidateDim.CONTRADICTION_TYPE.value,
    )
    g_vals = [
        v for tid, v in vals.items()
        if tid.startswith("v316-susp:")
    ]
    e_vals = [
        v for tid, v in vals.items()
        if tid.startswith("v317-h:")
    ]
    assert all(v == 1.0 for v in g_vals)
    assert all(v == 0.0 for v in e_vals)


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_dominant() -> None:
    assert build_report().recommendation == (
        "DOMINANT_CANDIDATE_FOUND"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DOMINANT_CANDIDATE_FOUND",
        "MULTIPLE_CANDIDATES_TIE",
        "NO_CANDIDATE_RESCUES",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_lists_all_six_candidates() -> None:
    art = build_t10_dimension_search_artifact()
    assert len(art["candidate_outcomes"]) == 6


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_101" / "report.json").read_text(
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
