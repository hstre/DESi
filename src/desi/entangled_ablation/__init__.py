"""DESi v3.94 — exhaustive dimension ablation
search on the entangled (G_v316susp + E_v317h)
residual subspace.
"""
from __future__ import annotations

from .ablation import (
    AblationOutcome, baseline_purity,
    cluster_entangled_with, cluster_purity,
    projected_entangled_vectors,
)
from .report import (
    PURITY_THRESHOLD, V394Report,
    build_entangled_ablation_artifact,
    build_report,
)
from .search import (
    MAX_SUBSET_SIZE,
    all_subset_outcomes, best_dim_set,
    best_outcome, best_purity,
    dimensionality_cost,
    purity_above_baseline_count,
    stability,
)


__all__ = [
    "AblationOutcome",
    "MAX_SUBSET_SIZE",
    "PURITY_THRESHOLD",
    "V394Report",
    "all_subset_outcomes",
    "baseline_purity",
    "best_dim_set", "best_outcome",
    "best_purity",
    "build_entangled_ablation_artifact",
    "build_report",
    "cluster_entangled_with",
    "cluster_purity",
    "dimensionality_cost",
    "projected_entangled_vectors",
    "purity_above_baseline_count",
    "stability",
]
