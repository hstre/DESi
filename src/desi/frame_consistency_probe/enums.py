"""Closed enums for the v3.9 consistency probe — Aufgaben 4 + 5."""
from __future__ import annotations

from enum import Enum


class FrameConsistency(str, Enum):
    """Closed taxonomy of inner/outer-frame relations."""

    FRAME_CONFIRMED   = "frame_confirmed"
    FRAME_TENSION     = "frame_tension"
    FRAME_CONFLICT    = "frame_conflict"
    FRAME_UNDECIDABLE = "frame_undecidable"


class CorpusGroup(str, Enum):
    """The three corpus partitions — Aufgabe 1."""

    GROUP_A = "outer_eq_inner"        # consistent
    GROUP_B = "outer_neq_inner"       # intentionally misleading
    GROUP_C = "outer_ambiguous"       # polysemy / entropy


__all__ = ["CorpusGroup", "FrameConsistency"]
