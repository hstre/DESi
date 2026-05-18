"""DESi v3.100 - compression vs information loss
audit for the v3.93 entangled (G+E) pair.
"""
from __future__ import annotations

from .compression import (
    collapsed_anchor_count,
    compression_gain,
    degenerate_vectors,
    dim_a, dim_b,
    distinct_point_count_a,
    distinct_point_count_b,
    separated_vectors,
)
from .loss import (
    downstream_diversity_a,
    downstream_diversity_b,
    downstream_failure_class_set_b,
    downstream_intervention_set_b,
    downstream_verdict_set_b,
    failure_class_delta,
    information_loss,
    predictive_delta,
    reasoning_delta,
)
from .report import (
    INFORMATION_LOSS_THRESHOLD,
    PREDICTIVE_DELTA_THRESHOLD,
    V3100Report,
    build_compression_vs_information_loss_artifact,
    build_report,
)


__all__ = [
    "INFORMATION_LOSS_THRESHOLD",
    "PREDICTIVE_DELTA_THRESHOLD",
    "V3100Report",
    "build_compression_vs_information_loss_artifact",
    "build_report",
    "collapsed_anchor_count",
    "compression_gain",
    "degenerate_vectors",
    "dim_a", "dim_b",
    "distinct_point_count_a",
    "distinct_point_count_b",
    "downstream_diversity_a",
    "downstream_diversity_b",
    "downstream_failure_class_set_b",
    "downstream_intervention_set_b",
    "downstream_verdict_set_b",
    "failure_class_delta",
    "information_loss",
    "predictive_delta",
    "reasoning_delta",
    "separated_vectors",
]
