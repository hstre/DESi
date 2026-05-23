"""DESi v5.1 — taxonomy stability probe.

Read-only stress test of the v5.0 discovered taxonomy
under representation, weighting, ordering, and corpus
perturbations. No runtime patching, no taxonomy
relabeling, no v5.0 artifact rewrites.
"""
from __future__ import annotations

from .baseline import (
    CanonicalBaseline, CanonicalCluster,
    load_canonical_baseline,
)
from .cluster_mapper import (
    PerturbClusterMapping, RunMapping,
    build_cluster_mapping_matrix, map_run_to_canonical,
)
from .enums import (
    NCKind, PerturbationFamily, StabilityRecommendation,
)
from .negative_controls import (
    StabilityNC, all_stability_ncs,
    classification_accuracy, classify_nc,
)
from .perturbations import (
    PerturbationRun, all_perturbation_runs,
    baseline_failure_samples,
    p1_runs, p2_runs, p3_runs, p4_runs, p5_runs,
)
from .report import (
    DOMINANT_CLUSTER_NAME, MAX_DOMINANT_SIZE_VARIANCE,
    MAX_MERGE_RATE, MAX_NOVEL_CLUSTER_FRACTION,
    MAX_SPLIT_RATE, MIN_CROSS_RUN_AGREEMENT,
    MIN_DOMINANT_RANK_STABILITY, MIN_LABEL_OVERLAP,
    MIN_NC_ACCURACY, MIN_SURVIVAL_RATE,
    PARTIAL_FLOOR_SURVIVAL, V51Report, build_report,
    build_cluster_mapping_matrix_artifact,
)
from .stability_metrics import (
    RunCharacterisation, StabilityMetrics,
    characterise_run, compute_stability,
)


__all__ = [
    "CanonicalBaseline", "CanonicalCluster",
    "DOMINANT_CLUSTER_NAME",
    "MAX_DOMINANT_SIZE_VARIANCE", "MAX_MERGE_RATE",
    "MAX_NOVEL_CLUSTER_FRACTION", "MAX_SPLIT_RATE",
    "MIN_CROSS_RUN_AGREEMENT",
    "MIN_DOMINANT_RANK_STABILITY", "MIN_LABEL_OVERLAP",
    "MIN_NC_ACCURACY", "MIN_SURVIVAL_RATE", "NCKind",
    "PARTIAL_FLOOR_SURVIVAL", "PerturbClusterMapping",
    "PerturbationFamily", "PerturbationRun",
    "RunCharacterisation", "RunMapping",
    "StabilityMetrics", "StabilityNC",
    "StabilityRecommendation", "V51Report",
    "all_perturbation_runs", "all_stability_ncs",
    "baseline_failure_samples",
    "build_cluster_mapping_matrix",
    "build_cluster_mapping_matrix_artifact",
    "build_report", "characterise_run",
    "classification_accuracy", "classify_nc",
    "compute_stability", "load_canonical_baseline",
    "map_run_to_canonical", "p1_runs", "p2_runs",
    "p3_runs", "p4_runs", "p5_runs",
]
