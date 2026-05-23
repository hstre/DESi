"""DESi v3.52 — semantic phase transition.

Sweeps {0, 1, 2, 3, 4, 8, 20} active anchors at the
v3.50 discrimination-band radius (3.5) and asks
whether the leakage curve flips discretely or grows
continuously.
"""
from __future__ import annotations

from .curve import (
    PhasePoint, compute_phase_curve,
    coupling_strength, discontinuity_score,
    saturation_point,
)
from .mass import (
    MASS_LEVELS, PROBE_RADIUS, SATURATION_MASS,
    all_mass_levels, first_k_ids, ordered_anchor_ids,
)
from .report import (
    V352Report, build_report,
    build_semantic_phase_curve_artifact,
)


__all__ = [
    "MASS_LEVELS", "PROBE_RADIUS", "PhasePoint",
    "SATURATION_MASS", "V352Report",
    "all_mass_levels", "build_report",
    "build_semantic_phase_curve_artifact",
    "compute_phase_curve", "coupling_strength",
    "discontinuity_score", "first_k_ids",
    "ordered_anchor_ids", "saturation_point",
]
