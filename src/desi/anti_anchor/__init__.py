"""DESi v3.51 — anti-anchor probe.

Tests whether adding selected claims to an "anti"
position (must be FAR from the trajectory under test)
can locally suppress the v3.44 radius gate's leakage
while preserving plateau recall.
"""
from __future__ import annotations

from .ablation import (
    AntiOutcome, PLATEAU_RADIUS, run_all_anti_kinds,
    run_under_anti,
)
from .anchors import (
    ANTI_COUNT, ANTI_RADIUS, AntiAnchorKind,
    anti_anchor_vectors, select_anti_anchor_ids,
)
from .report import (
    AntiKindResult, V351Report,
    build_anti_anchor_effects_artifact, build_report,
)


__all__ = [
    "ANTI_COUNT", "ANTI_RADIUS", "AntiAnchorKind",
    "AntiKindResult", "AntiOutcome", "PLATEAU_RADIUS",
    "V351Report", "anti_anchor_vectors",
    "build_anti_anchor_effects_artifact",
    "build_report", "run_all_anti_kinds",
    "run_under_anti", "select_anti_anchor_ids",
]
