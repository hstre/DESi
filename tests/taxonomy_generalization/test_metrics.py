"""v5.2 — generalization metrics + dominant audit +
novelty fraction."""
from __future__ import annotations

from desi.taxonomy_generalization.report import (
    MAX_CROSS_DOMAIN_VARIANCE, MAX_DOMINANT_SIZE_SHIFT,
    MAX_TRUE_NOVELTY_FRACTION, MAX_UNKNOWN_FRACTION,
    MIN_CONFIDENCE_MEAN, MIN_DOMINANT_RANK_STABILITY,
    MIN_PROBE_TRANSFER_RATE, MIN_TAXONOMY_COVERAGE,
    build_report,
)


def _R():
    return build_report()


def test_taxonomy_coverage_meets_threshold() -> None:
    assert _R().metrics.taxonomy_coverage >= (
        MIN_TAXONOMY_COVERAGE
    )


def test_unknown_fraction_meets_threshold() -> None:
    assert _R().metrics.unknown_fraction <= (
        MAX_UNKNOWN_FRACTION
    )


def test_cross_domain_variance_meets_threshold() -> None:
    assert _R().metrics.cross_domain_variance <= (
        MAX_CROSS_DOMAIN_VARIANCE
    )


def test_probe_transfer_rate_meets_threshold() -> None:
    assert _R().metrics.probe_transfer_rate >= (
        MIN_PROBE_TRANSFER_RATE
    )


def test_confidence_mean_meets_threshold() -> None:
    assert _R().metrics.confidence_mean >= (
        MIN_CONFIDENCE_MEAN
    )


def test_confidence_variance_nonnegative() -> None:
    assert _R().metrics.confidence_variance >= 0.0


def test_class_balance_shift_in_unit_interval() -> None:
    s = _R().metrics.class_balance_shift
    assert 0.0 <= s <= 1.0


def test_dominant_rank_stability_meets_threshold() -> None:
    assert _R().dominant_audit.rank_generalization_stability >= (
        MIN_DOMINANT_RANK_STABILITY
    )


def test_dominant_size_shift_meets_threshold() -> None:
    assert _R().dominant_audit.size_shift <= (
        MAX_DOMINANT_SIZE_SHIFT
    )


def test_true_novelty_fraction_meets_threshold() -> None:
    assert _R().true_novelty_fraction <= (
        MAX_TRUE_NOVELTY_FRACTION
    )


def test_metrics_deterministic() -> None:
    a = _R().to_dict()
    b = _R().to_dict()
    assert a == b
