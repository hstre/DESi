"""Closed taxonomies for v4.1 — strategy id + failure class +
recommendation outcome."""
from __future__ import annotations

from enum import Enum


class InferenceStrategy(str, Enum):
    """Closed list of inference strategies probed in v4.1."""

    F1_MARKER_LEXICAL       = "F1_marker_lexical"
    F2_NEAREST_NEIGHBOR     = "F2_nearest_neighbor"
    F3_SENTENCE_COOCCURRENCE = "F3_sentence_cooccurrence"
    F4_CONTEXT_WINDOW       = "F4_context_window"


class FrameInferenceFailure(str, Enum):
    """Closed failure taxonomy (Aufgabe 9). Every misprediction
    falls into exactly one class."""

    FALSE_FRAME            = "FALSE_FRAME"
    NO_FRAME               = "NO_FRAME"
    MULTI_FRAME_COLLISION  = "MULTI_FRAME_COLLISION"
    CONTEXT_LEAK           = "CONTEXT_LEAK"
    DOMAIN_SHIFT           = "DOMAIN_SHIFT"
    ROUTING_MISMATCH       = "ROUTING_MISMATCH"
    UNKNOWN                = "UNKNOWN"


class RecommendationOutcome(str, Enum):
    """Closed list of recommendations (Aufgabe 11)."""

    CONFIRMED = "IMPLICIT_FRAME_INGRESS_CONFIRMED"
    PARTIAL   = "IMPLICIT_FRAME_INGRESS_PARTIAL"
    FAILED    = "IMPLICIT_FRAME_INGRESS_FAILED"
    NONE      = "NONE"


__all__ = [
    "FrameInferenceFailure",
    "InferenceStrategy",
    "RecommendationOutcome",
]
