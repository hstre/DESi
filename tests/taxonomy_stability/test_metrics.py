"""v5.1 — stability metrics + dominant-cluster audit."""
from __future__ import annotations

from desi.taxonomy_stability.baseline import (
    load_canonical_baseline,
)
from desi.taxonomy_stability.perturbations import (
    all_perturbation_runs,
)
from desi.taxonomy_stability.report import (
    DOMINANT_CLUSTER_NAME, MAX_DOMINANT_SIZE_VARIANCE,
    MAX_MERGE_RATE, MAX_NOVEL_CLUSTER_FRACTION,
    MAX_SPLIT_RATE, MIN_CROSS_RUN_AGREEMENT,
    MIN_DOMINANT_RANK_STABILITY, MIN_LABEL_OVERLAP,
    MIN_SURVIVAL_RATE,
)
from desi.taxonomy_stability.stability_metrics import (
    compute_stability,
)


def _metrics():
    b = load_canonical_baseline()
    m, _ = compute_stability(
        all_perturbation_runs(), b,
        dominant_name=DOMINANT_CLUSTER_NAME,
    )
    return m


def test_cluster_survival_rate_meets_threshold() -> None:
    assert _metrics().cluster_survival_rate >= (
        MIN_SURVIVAL_RATE
    )


def test_cluster_split_rate_meets_threshold() -> None:
    assert _metrics().cluster_split_rate <= MAX_SPLIT_RATE


def test_cluster_merge_rate_meets_threshold() -> None:
    assert _metrics().cluster_merge_rate <= MAX_MERGE_RATE


def test_label_overlap_meets_threshold() -> None:
    assert _metrics().label_overlap_score >= (
        MIN_LABEL_OVERLAP
    )


def test_cross_run_agreement_meets_threshold() -> None:
    assert _metrics().cross_run_agreement >= (
        MIN_CROSS_RUN_AGREEMENT
    )


def test_dominant_rank_stability_meets_threshold() -> None:
    m = _metrics()
    assert m.dominant_cluster_rank_stability >= (
        MIN_DOMINANT_RANK_STABILITY
    )


def test_dominant_size_variance_meets_threshold() -> None:
    m = _metrics()
    assert m.dominant_cluster_size_variance <= (
        MAX_DOMINANT_SIZE_VARIANCE
    )


def test_novel_cluster_fraction_meets_threshold() -> None:
    assert _metrics().novel_cluster_fraction <= (
        MAX_NOVEL_CLUSTER_FRACTION
    )


def test_metrics_largest_cluster_variance_nonnegative() -> None:
    assert _metrics().largest_cluster_variance >= 0.0


def test_metrics_entropy_variance_nonnegative() -> None:
    assert _metrics().taxonomy_entropy_variance >= 0.0


def test_metrics_deterministic() -> None:
    a = _metrics().to_dict()
    b = _metrics().to_dict()
    assert a == b
