"""DESi v3.64 — causal complementarity test.

Systematically ablates four factors (distance,
corpus heterogeneity, failure diversity, coverage
gain) and measures the resulting drop in resonant
pair counts. Reports causal_importance per factor
and emits a closed verdict over which factors are
necessary / sufficient.
"""
from __future__ import annotations

from .ablation import (
    AblationResult, MIN_SUBSET_FOR_INFERENCE,
    NECESSARY_IMPORTANCE_FLOOR, PROBE_RADIUS,
    PairFactors, all_pair_factors,
    baseline_pair_count, baseline_resonance,
    necessary_factors, run_ablations,
    sufficient_factors,
)
from .causal import aggregate, rank_by_importance
from .report import (
    V364Report,
    build_causal_complementarity_artifact,
    build_report,
)


__all__ = [
    "AblationResult", "MIN_SUBSET_FOR_INFERENCE",
    "NECESSARY_IMPORTANCE_FLOOR", "PROBE_RADIUS",
    "PairFactors", "V364Report", "aggregate",
    "all_pair_factors",
    "baseline_pair_count", "baseline_resonance",
    "build_causal_complementarity_artifact",
    "build_report", "necessary_factors",
    "rank_by_importance", "run_ablations",
    "sufficient_factors",
]
