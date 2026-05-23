"""DESi v3.61 — distance vs complementarity.

Splits the 190 plateau-anchor pairs by (distance
bucket × family bucket) and reports which factor
drives v3.50's resonance.
"""
from __future__ import annotations

from .complementarity import (
    ConditionCell, PROBE_RADIUS,
    baseline_activation, best_explanation_model,
    combined_activation,
    distance_only_activation,
    heterogeneity_only_activation,
    per_cell_results,
)
from .distance import (
    PairDistance, distance_bucket,
    distance_threshold, plateau_pair_distances,
)
from .report import (
    V361Report,
    build_complementarity_vs_distance_artifact,
    build_report,
)


__all__ = [
    "ConditionCell", "PROBE_RADIUS",
    "PairDistance", "V361Report",
    "baseline_activation",
    "best_explanation_model",
    "build_complementarity_vs_distance_artifact",
    "build_report", "combined_activation",
    "distance_bucket",
    "distance_only_activation",
    "distance_threshold",
    "heterogeneity_only_activation",
    "per_cell_results",
    "plateau_pair_distances",
]
