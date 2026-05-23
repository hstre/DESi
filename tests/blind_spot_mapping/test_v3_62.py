"""v3.62 — blind-spot mapping tests."""
from __future__ import annotations

import json
import pathlib

from desi.blind_spot_mapping.blindspots import (
    fully_covered_after, uncovered_after,
    uncovered_before,
)
from desi.blind_spot_mapping.coverage import (
    PROBE_RADIUS, all_anchor_coverages,
    all_leakage_vectors, pair_coverage,
)
from desi.blind_spot_mapping.overlap import (
    all_pair_records, cohort_blindspots,
)
from desi.blind_spot_mapping.report import (
    build_blindspot_mapping_artifact, build_report,
)


def test_probe_radius_matches_v350() -> None:
    assert PROBE_RADIUS == 3.5


def test_all_leakage_vectors_count() -> None:
    assert len(all_leakage_vectors()) == 145


def test_all_anchor_coverages_count() -> None:
    assert len(all_anchor_coverages()) == 20


def test_pair_coverage_basic_properties() -> None:
    covs = all_anchor_coverages()
    p = pair_coverage(covs[0], covs[1])
    assert p.union_size >= max(p.size_a, p.size_b)
    assert p.intersection_size <= min(
        p.size_a, p.size_b,
    )
    assert p.union_size + p.intersection_size == (
        p.size_a + p.size_b
    )
    assert p.symmetric_diff_size == (
        p.union_size - p.intersection_size
    )


def test_uncovered_before_is_145() -> None:
    assert uncovered_before() == 145


def test_uncovered_after_empirical() -> None:
    """Empirical: at r=3.5 the 20 plateau anchors
    collectively cover 133 of 145 leakages; 12 remain
    uncovered."""
    assert uncovered_after() == 12


def test_fully_covered_after_complements() -> None:
    assert fully_covered_after() == 133
    assert (
        uncovered_after() + fully_covered_after()
    ) == uncovered_before()


def test_all_pair_records_count() -> None:
    assert len(all_pair_records()) == 190


def test_cohort_blindspots_split() -> None:
    het, hom = cohort_blindspots()
    assert het.cohort == "heterogeneous"
    assert hom.cohort == "homogeneous"
    assert (
        het.total_pair_count
        + hom.total_pair_count
    ) == 190


def test_cohort_total_counts() -> None:
    """Empirical: 136 heterogeneous + 54 homogeneous
    plateau pairs."""
    het, hom = cohort_blindspots()
    assert het.total_pair_count == 136
    assert hom.total_pair_count == 54


def test_cohort_active_counts() -> None:
    """Active = both anchors non-empty."""
    het, hom = cohort_blindspots()
    assert het.active_pair_count == 88
    assert hom.active_pair_count == 32


def test_coverage_gain_positive() -> None:
    """Paper-11 v3 gate #3: coverage_gain > 0."""
    assert build_report().coverage_gain > 0


def test_heterogeneity_redundancy_delta_positive() -> None:
    """Heterogeneous pairs are less redundant than
    homogeneous pairs (delta = hom_red - het_red)."""
    assert build_report().heterogeneity_redundancy_delta > 0


def test_new_region_fraction_high() -> None:
    """Heterogeneous pairs have new_region_fraction
    above 0.50."""
    assert build_report().new_region_fraction > 0.5


def test_redundancy_score_below_half() -> None:
    """Heterogeneous pairs are below 0.50
    redundancy."""
    assert build_report().redundancy_score < 0.5


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_heterogeneous_less_redundant() -> None:
    assert build_report().recommendation == (
        "HETEROGENEOUS_PAIRS_LESS_REDUNDANT"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "HETEROGENEOUS_PAIRS_LESS_REDUNDANT",
        "COVERAGE_GAIN_POSITIVE",
        "NO_BLINDSPOT_DIFFERENCE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_all_pairs() -> None:
    art = build_blindspot_mapping_artifact()
    assert len(art["pair_records"]) == 190


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_62" / "report.json").read_text(
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
