"""v3.61 — distance vs complementarity tests."""
from __future__ import annotations

import json
import pathlib

from desi.complementarity.complementarity import (
    PROBE_RADIUS, baseline_activation,
    best_explanation_model, combined_activation,
    distance_only_activation,
    heterogeneity_only_activation,
    per_cell_results,
)
from desi.complementarity.distance import (
    distance_bucket, distance_threshold,
    plateau_pair_distances,
)
from desi.complementarity.report import (
    build_complementarity_vs_distance_artifact,
    build_report,
)


def test_probe_radius_matches_v350() -> None:
    assert PROBE_RADIUS == 3.5


def test_plateau_pair_distances_count_is_190() -> None:
    """C(20, 2) = 190 plateau pairs."""
    assert len(plateau_pair_distances()) == 190


def test_distance_threshold_is_median() -> None:
    import statistics
    distances = [
        p.distance for p in plateau_pair_distances()
    ]
    assert distance_threshold() == statistics.median(
        distances,
    )


def test_distance_bucket_classification() -> None:
    """Tiny values are low_d; large values are high_d."""
    t = distance_threshold()
    assert distance_bucket(t * 1.5) == "high_d"
    assert distance_bucket(t * 0.5) == "low_d"


def test_per_cell_results_count() -> None:
    cells = per_cell_results()
    assert len(cells) == 4
    assert {c.condition for c in cells} == {
        "high_d_same_fam", "low_d_same_fam",
        "high_d_diff_fam", "low_d_diff_fam",
    }


def test_per_cell_pair_counts_sum_to_190() -> None:
    cells = per_cell_results()
    assert sum(c.pair_count for c in cells) == 190


def test_per_cell_resonant_counts_sum_to_64() -> None:
    """Same total as v3.50 / v3.60 (64 resonant pairs
    in the full 9-d space at r=3.5)."""
    cells = per_cell_results()
    assert sum(
        c.resonant_pair_count for c in cells
    ) == 64


def test_empirical_per_cell_counts() -> None:
    by = {
        c.condition: c for c in per_cell_results()
    }
    assert by["high_d_same_fam"].pair_count == 28
    assert by["high_d_same_fam"].resonant_pair_count == 14
    assert by["low_d_same_fam"].pair_count == 26
    assert by["low_d_same_fam"].resonant_pair_count == 2
    assert by["high_d_diff_fam"].pair_count == 60
    assert by["high_d_diff_fam"].resonant_pair_count == 38
    assert by["low_d_diff_fam"].pair_count == 76
    assert by["low_d_diff_fam"].resonant_pair_count == 10


def test_combined_activation_is_largest() -> None:
    cells = per_cell_results()
    assert combined_activation(cells) > (
        distance_only_activation(cells)
    )
    assert combined_activation(cells) > (
        heterogeneity_only_activation(cells)
    )


def test_distance_matters_more_than_heterogeneity() -> None:
    """Empirical: 0.42 distance-only vs 0.05
    heterogeneity-only - distance is the dominant
    single factor."""
    cells = per_cell_results()
    assert distance_only_activation(cells) > (
        heterogeneity_only_activation(cells)
    )


def test_combined_strictly_above_distance_only() -> None:
    """Paper-11 v3 gate #2 condition: heterogeneity
    adds to distance alone."""
    cells = per_cell_results()
    assert combined_activation(cells) > (
        distance_only_activation(cells) + 0.05
    )


def test_baseline_activation_low() -> None:
    cells = per_cell_results()
    assert baseline_activation(cells) < 0.20


def test_best_explanation_model_is_combined() -> None:
    cells = per_cell_results()
    assert best_explanation_model(cells) == "COMBINED"


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_complementarity_beyond_distance() -> None:
    assert build_report().recommendation == (
        "COMPLEMENTARITY_BEYOND_DISTANCE"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "COMPLEMENTARITY_BEYOND_DISTANCE",
        "DISTANCE_DOMINATES",
        "HETEROGENEITY_DOMINATES",
        "FACTORS_EQUIVALENT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_contains_cells() -> None:
    art = build_complementarity_vs_distance_artifact()
    assert len(art["cells"]) == 4


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_61" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
