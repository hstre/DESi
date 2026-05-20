"""DESi v3.77 — missing claim negative controls.

Applies four closed null-space perturbation kinds
(random jitter, frame drift, branch variation, noise
only) to the v3.73 test set WITHOUT removing any
claim and reports false_missing_claim_rate.
"""
from __future__ import annotations

from .negative_controls import (
    false_missing_claim_rate,
    noise_rejection_rate, null_stability,
    total_false_missing, total_perturbations,
)
from .null_space import (
    NullControlKind, NullControlOutcome,
    all_null_control_outcomes,
    perturb_vector, run_one_null_control,
)
from .report import (
    NEPTUN_FALSE_MISSING_CEILING, V377Report,
    build_missing_claim_negative_controls_artifact,
    build_report,
)


__all__ = [
    "NEPTUN_FALSE_MISSING_CEILING",
    "NullControlKind", "NullControlOutcome",
    "V377Report",
    "all_null_control_outcomes",
    "build_missing_claim_negative_controls_artifact",
    "build_report",
    "false_missing_claim_rate",
    "noise_rejection_rate", "null_stability",
    "perturb_vector", "run_one_null_control",
    "total_false_missing",
    "total_perturbations",
]
