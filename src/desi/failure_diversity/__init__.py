"""DESi v3.63 — failure diversity audit.

Per-plateau failure profile (cause / corpus / final-
state pattern) and per-pair diversity score; reports
the Pearson correlation between diversity and
resonance.
"""
from __future__ import annotations

from .diversity import (
    DIVERSITY_AXES, PROBE_RADIUS,
    PairDiversityRecord,
    diversity_activation_correlation,
    failure_diversity_score,
    mean_diversity_by_resonance, pair_diversity,
    per_pair_records, redundancy_score,
)
from .failures import (
    FailureProfile, plateau_failure_profiles,
)
from .report import (
    V363Report, build_failure_diversity_artifact,
    build_report,
)


__all__ = [
    "DIVERSITY_AXES", "FailureProfile",
    "PROBE_RADIUS", "PairDiversityRecord",
    "V363Report",
    "build_failure_diversity_artifact",
    "build_report",
    "diversity_activation_correlation",
    "failure_diversity_score",
    "mean_diversity_by_resonance",
    "pair_diversity",
    "per_pair_records",
    "plateau_failure_profiles",
    "redundancy_score",
]
