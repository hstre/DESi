"""Closed taxonomy of v3.6 frame-failure classes — Aufgabe 2.

Seven values exactly. Every v3.5 failure is projected onto **one**
``FrameFailureClass``; no free classes, no "other".
"""
from __future__ import annotations

from enum import Enum


class FrameFailureClass(str, Enum):
    SYNONYM_GAP = "synonym_gap"
    POLYSEMY_COLLISION = "polysemy_collision"
    MARKER_DROPOUT = "marker_dropout"
    MULTI_SIGNAL_CONFLICT = "multi_signal_conflict"
    PIPELINE_ROUTING_MISMATCH = "pipeline_routing_mismatch"
    TRUE_FRAME_SHIFT = "true_frame_shift"
    UNKNOWN = "unknown"


__all__ = ["FrameFailureClass"]
