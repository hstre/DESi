"""v3.63 — failure diversity tests."""
from __future__ import annotations

import json
import pathlib

from desi.failure_diversity.diversity import (
    DIVERSITY_AXES, PROBE_RADIUS,
    diversity_activation_correlation,
    failure_diversity_score,
    mean_diversity_by_resonance,
    pair_diversity, per_pair_records,
    redundancy_score,
)
from desi.failure_diversity.failures import (
    FailureProfile, plateau_failure_profiles,
)
from desi.failure_diversity.report import (
    build_failure_diversity_artifact, build_report,
)


def test_probe_radius_matches_v350() -> None:
    assert PROBE_RADIUS == 3.5


def test_diversity_axes_count_is_five() -> None:
    assert len(DIVERSITY_AXES) == 5


def test_plateau_profiles_count() -> None:
    assert len(plateau_failure_profiles()) == 20


def test_all_plateau_primary_cause_uniform() -> None:
    """v3.32 classifies every plateau anchor as
    CONFIDENCE_OSCILLATION - the cause axis contributes
    0 to diversity for any pair."""
    profiles = plateau_failure_profiles()
    causes = {p.primary_cause for p in profiles}
    assert causes == {"CONFIDENCE_OSCILLATION"}


def test_pair_diversity_zero_self_pair() -> None:
    """Wrap-around sanity: a profile compared with
    itself has diversity 0."""
    p = plateau_failure_profiles()[0]
    assert pair_diversity(p, p) == 0


def test_pair_diversity_bounded() -> None:
    profiles = plateau_failure_profiles()
    for a in profiles[:5]:
        for b in profiles[:5]:
            d = pair_diversity(a, b)
            assert 0 <= d <= len(DIVERSITY_AXES)


def test_per_pair_records_count() -> None:
    assert len(per_pair_records()) == 190


def test_per_pair_resonant_total_is_64() -> None:
    """Matches v3.50/v3.60/v3.61/v3.62 totals."""
    assert sum(
        1 for r in per_pair_records() if r.is_resonant
    ) == 64


def test_failure_diversity_score_in_unit_interval() -> None:
    score = failure_diversity_score()
    assert 0.0 <= score <= 1.0


def test_redundancy_complements_diversity() -> None:
    assert (
        redundancy_score() + failure_diversity_score()
    ) == 1.0


def test_mean_diversity_resonant_at_least_non() -> None:
    """Empirical: resonant pairs have at least as
    much failure diversity as non-resonant."""
    res, non = mean_diversity_by_resonance()
    assert res >= non


def test_correlation_is_positive() -> None:
    """Paper-11 v3 gate #4: correlation > 0."""
    assert diversity_activation_correlation() > 0


def test_correlation_is_small_but_positive() -> None:
    """Empirical: correlation is barely positive
    (~0.027). The gate passes by direction, not by
    magnitude."""
    corr = diversity_activation_correlation()
    assert 0.0 < corr < 0.10


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_predicts() -> None:
    assert build_report().recommendation == (
        "DIVERSITY_PREDICTS_ACTIVATION"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DIVERSITY_PREDICTS_ACTIVATION",
        "DIVERSITY_SUPPRESSES_ACTIVATION",
        "DIVERSITY_UNINFORMATIVE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_contains_profiles_and_pairs() -> None:
    art = build_failure_diversity_artifact()
    assert len(art["profiles"]) == 20
    assert len(art["pair_records"]) == 190


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_63" / "report.json").read_text(
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
