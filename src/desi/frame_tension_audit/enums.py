"""Closed enums for v3.10 — Aufgaben 2 + 4."""
from __future__ import annotations

from enum import Enum


class TensionAuditClass(str, Enum):
    """Closed taxonomy of v3.9 FRAME_TENSION outcomes — Aufgabe 2."""

    TRUE_TENSION      = "true_tension"
    FALSE_TENSION     = "false_tension"
    AMBIGUOUS_TENSION = "ambiguous_tension"


class TensionFailureCause(str, Enum):
    """Closed taxonomy of failure causes — Aufgabe 4.

    Exactly one cause per FALSE_TENSION / AMBIGUOUS_TENSION case.
    TRUE_TENSION cases carry no cause (they are not failures).
    """

    INNER_UNDERDETECTION         = "inner_underdetection"
    OUTER_OVERDETECTION          = "outer_overdetection"
    FRAME_COMPATIBILITY_TOO_STRICT = "frame_compatibility_too_strict"
    POLYSEMY_COLLISION           = "polysemy_collision"
    MISSING_BRIDGE_FRAME         = "missing_bridge_frame"
    LABEL_NOISE                  = "label_noise"
    UNKNOWN                      = "unknown"


__all__ = ["TensionAuditClass", "TensionFailureCause"]
