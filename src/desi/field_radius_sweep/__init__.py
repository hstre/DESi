"""DESi v3.44 — field-radius sweep.

Replaces v3.39's single-feature pre-audit gate with a
geometric ball around the plateau manifold. The closed
radius set {0.25, 0.5, 1.0, 2.0, 4.0, ∞} answers the
directive's "minimal effective radius" question.
"""
from __future__ import annotations

from .ablation import (
    RadiusOutcome, run_all_radii, run_at_radius,
)
from .curve import (
    MIN_PLATEAU_RECALL, RadiusPoint, compute_curve,
    pick_largest_clean_radius, pick_optimal_radius,
)
from .radius import (
    RADII, radius_label, selector_for_radius,
)
from .report import (
    MIN_LEAKAGE_REDUCTION, V344Report,
    build_radius_sweep_artifact, build_report,
)


__all__ = [
    "MIN_LEAKAGE_REDUCTION", "MIN_PLATEAU_RECALL",
    "RADII", "RadiusOutcome", "RadiusPoint",
    "V344Report", "build_radius_sweep_artifact",
    "build_report", "compute_curve",
    "pick_largest_clean_radius",
    "pick_optimal_radius", "radius_label",
    "run_all_radii", "run_at_radius",
    "selector_for_radius",
]
