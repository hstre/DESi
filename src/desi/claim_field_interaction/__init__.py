"""DESi v3.45 — claim-field interaction.

Varies the number of activated plateau anchors used
by the v3.44 radius-bounded selector and asks whether
the resulting leakage curve is additive, saturating,
or interfering.
"""
from __future__ import annotations

from .attribution import (
    AnchorContribution, dominant_anchors,
    per_anchor_leakage,
)
from .interaction import (
    InterferenceFinding, MassOutcome,
    interference_findings, run_all_masses,
    run_at_mass,
)
from .mass import (
    MASS_LEVELS, PROBE_RADIUS, SATURATION_MASS,
    active_anchor_subset, active_anchor_vectors,
    mass_levels_with_saturation,
    ordered_plateau_anchors,
)
from .report import (
    MassPoint, V345Report,
    build_claim_field_effects_artifact,
    build_field_leakage_claims_artifact, build_report,
)


__all__ = [
    "AnchorContribution", "InterferenceFinding",
    "MASS_LEVELS", "MassOutcome", "MassPoint",
    "PROBE_RADIUS", "SATURATION_MASS", "V345Report",
    "active_anchor_subset", "active_anchor_vectors",
    "build_claim_field_effects_artifact",
    "build_field_leakage_claims_artifact",
    "build_report", "dominant_anchors",
    "interference_findings",
    "mass_levels_with_saturation",
    "ordered_plateau_anchors", "per_anchor_leakage",
    "run_all_masses", "run_at_mass",
]
