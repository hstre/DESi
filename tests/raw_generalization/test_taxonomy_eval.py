"""v5.4 — taxonomy-only metrics on RAW corpus."""
from __future__ import annotations

from desi.raw_generalization.raw_corpus_loader import (
    load_raw_chains,
)
from desi.raw_generalization.report import (
    MAX_DOMINANT_SIZE_SHIFT,
    MAX_TAXONOMY_CROSS_DOMAIN_VARIANCE,
    MAX_TAXONOMY_UNKNOWN_FRACTION,
    MIN_DOMINANT_RANK_STABILITY,
    MIN_TAXONOMY_CONFIDENCE_MEAN,
    MIN_TAXONOMY_COVERAGE,
)
from desi.raw_generalization.taxonomy_eval import (
    evaluate_taxonomy,
)


def _metrics():
    m, _ = evaluate_taxonomy(load_raw_chains())
    return m


def test_channel_is_taxonomy_only() -> None:
    assert _metrics().channel == "taxonomy_only"


def test_taxonomy_coverage_meets_threshold() -> None:
    assert _metrics().taxonomy_coverage >= (
        MIN_TAXONOMY_COVERAGE
    )


def test_taxonomy_unknown_fraction_meets_threshold() -> None:
    assert _metrics().taxonomy_unknown_fraction <= (
        MAX_TAXONOMY_UNKNOWN_FRACTION
    )


def test_taxonomy_confidence_mean_meets_threshold() -> None:
    assert _metrics().taxonomy_confidence_mean >= (
        MIN_TAXONOMY_CONFIDENCE_MEAN
    )


def test_taxonomy_cross_domain_variance_meets_threshold() -> None:
    assert _metrics().taxonomy_cross_domain_variance <= (
        MAX_TAXONOMY_CROSS_DOMAIN_VARIANCE
    )


def test_dominant_rank_stability_meets_threshold() -> None:
    assert _metrics().dominant_cluster_rank_stability >= (
        MIN_DOMINANT_RANK_STABILITY
    )


def test_dominant_size_shift_meets_threshold() -> None:
    assert _metrics().dominant_cluster_size_shift <= (
        MAX_DOMINANT_SIZE_SHIFT
    )


def test_taxonomy_metrics_deterministic() -> None:
    a = _metrics().to_dict()
    b = _metrics().to_dict()
    assert a == b
