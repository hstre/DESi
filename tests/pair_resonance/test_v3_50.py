"""v3.50 — pair resonance matrix tests."""
from __future__ import annotations

import json
import pathlib

from desi.pair_resonance.control import (
    deterministic_control_ids,
)
from desi.pair_resonance.coverage import (
    AnchorCoverage, PROBE_RADIUS,
    control_anchor_coverage, coverage_for_subset,
    per_anchor_coverage,
)
from desi.pair_resonance.matrix import (
    build_pair_records, build_triple_records,
    pair_matrix,
)
from desi.pair_resonance.report import (
    build_pair_resonance_matrix_artifact, build_report,
)


def test_probe_radius_is_three_point_five() -> None:
    """v3.50 uses r=3.5 - inside the discrimination
    band (v3.43 min..max manifold distance 2.93..3.68)
    so per-anchor coverage spreads across {0, 12, 121}
    and pair resonance is observable. At r=4.0 the
    coverage saturates and resonant_pair_count
    collapses to 0."""
    assert PROBE_RADIUS == 3.5


def test_per_anchor_coverage_returns_twenty() -> None:
    assert len(per_anchor_coverage()) == 20


def test_coverage_for_subset_union() -> None:
    cov = per_anchor_coverage()
    first_id = cov[0].anchor_id
    second_id = cov[1].anchor_id
    union = coverage_for_subset(
        cov, (first_id, second_id),
    )
    assert union == (cov[0].coverage | cov[1].coverage)


def test_coverage_for_subset_ignores_unknown_ids() -> None:
    cov = per_anchor_coverage()
    out = coverage_for_subset(cov, ("not_an_id",))
    assert out == frozenset()


def test_deterministic_control_ids_stable() -> None:
    a = deterministic_control_ids(20)
    b = deterministic_control_ids(20)
    assert a == b
    assert len(a) == 20


def test_deterministic_control_ids_clip() -> None:
    """Requesting more than the rescued cohort size
    returns all rescued ids."""
    out = deterministic_control_ids(10000)
    assert len(out) >= 200  # rescued cohort = 228


def test_control_anchor_coverage_count() -> None:
    cov = control_anchor_coverage(
        deterministic_control_ids(20),
    )
    assert len(cov) == 20


def test_pair_count_is_one_ninety() -> None:
    """C(20, 2) = 190 pairs."""
    cov = per_anchor_coverage()
    assert len(build_pair_records(cov)) == 190


def test_pair_matrix_dimensions() -> None:
    cov = per_anchor_coverage()
    pm = pair_matrix(cov)
    assert len(pm) == 20
    for row in pm.values():
        assert len(row) == 20


def test_pair_matrix_diagonal_is_self_coverage() -> None:
    cov = per_anchor_coverage()
    pm = pair_matrix(cov)
    by_id = {c.anchor_id: c.size for c in cov}
    for aid, size in by_id.items():
        assert pm[aid][aid] == size


def test_pair_matrix_symmetric() -> None:
    cov = per_anchor_coverage()
    pm = pair_matrix(cov)
    ids = list(pm.keys())
    for a in ids:
        for b in ids:
            assert pm[a][b] == pm[b][a]


def test_subadditivity_score_positive() -> None:
    """Concept Gate #2: subadditivity_score > 0."""
    assert build_report().plateau_summary.subadditivity_score > 0


def test_resonance_gap_is_positive() -> None:
    """Plateau has many resonant pairs; the random
    control cohort has none. Resonance is a plateau-
    specific structural property."""
    assert build_report().resonance_gap > 0


def test_resonance_pair_count_empirical() -> None:
    """Empirical pinning: 64 of 190 pairs are
    resonant at r=3.5."""
    r = build_report()
    assert r.plateau_summary.resonant_pair_count == 64


def test_control_resonance_is_zero() -> None:
    """Random rescued-cohort anchors are nested or
    saturating - no resonance."""
    assert build_report().control_summary.resonant_pair_count == 0


def test_triple_max_extra_is_zero() -> None:
    """Empirical: triples never add anything beyond
    the best pair union; the field is fully
    pair-determined."""
    assert build_report().triple_max_extra == 0


def test_attribution_stability_is_one() -> None:
    """Concept Gate (sprint #5 surrogate)."""
    assert build_report().attribution_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PAIR_RESONANCE_DETECTED",
        "PAIR_SUBADDITIVE_OVERLAP",
        "PAIR_FULLY_ADDITIVE",
        "HALT_ATTRIBUTION_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_resonance_detected() -> None:
    assert build_report().recommendation == (
        "PAIR_RESONANCE_DETECTED"
    )


def test_pair_resonance_matrix_artifact_present() -> None:
    art = build_pair_resonance_matrix_artifact()
    assert len(art["plateau_pairs"]) == 190
    assert len(art["control_pairs"]) == 190
    assert "pair_matrix" in art


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_50" / "report.json").read_text(
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
