"""DESi v3.99 - counterfactual divergence audit
on the v3.93 entangled (G_v316susp + E_v317h)
pair under five closed perturbation kinds.
"""
from __future__ import annotations

from .counterfactual import (
    NO_CHAOS_SENTINEL,
    PerturbationOutcome,
    SEPARATION_THRESHOLD,
    all_perturbation_outcomes,
    baseline_auc,
    chaos_threshold,
    coupling_stability,
    perturbation_divergence,
    separation_rate,
)
from .perturb import (
    MAGNITUDE_GRID, PERTURBATION_KINDS,
    PerturbationKind,
    baseline_vectors,
    perturbed_vectors,
)
from .report import (
    SEPARATION_RATE_THRESHOLD,
    V399Report,
    build_counterfactual_divergence_artifact,
    build_report,
)


__all__ = [
    "MAGNITUDE_GRID",
    "NO_CHAOS_SENTINEL",
    "PERTURBATION_KINDS",
    "PerturbationKind",
    "PerturbationOutcome",
    "SEPARATION_RATE_THRESHOLD",
    "SEPARATION_THRESHOLD",
    "V399Report",
    "all_perturbation_outcomes",
    "baseline_auc",
    "baseline_vectors",
    "build_counterfactual_divergence_artifact",
    "build_report",
    "chaos_threshold",
    "coupling_stability",
    "perturbation_divergence",
    "perturbed_vectors",
    "separation_rate",
]
