"""Closed enumeration of frame kinds (Aufgabe 1).

Nine values exactly. A frame is a **pre-audit declaration** of
*which kind of evidence the claim invites*. Frames never decide
truth — they decide which pipeline may even attempt to judge the
claim.

Adding a new frame requires a new directive: ``FrameKind`` is
closed at v3.4.
"""
from __future__ import annotations

from enum import Enum


class FrameKind(str, Enum):
    THERMODYNAMIC = "thermodynamic"
    INFORMATION_THEORETIC = "information_theoretic"
    ONTOLOGICAL_DISTINGUISHABILITY = "ontological_distinguishability"
    METAPHORICAL = "metaphorical"
    FORMAL_LOGIC = "formal_logic"
    EMPIRICAL_CAUSAL = "empirical_causal"
    AUTHORITY_SPEECH = "authority_speech"
    TOOL_COMPUTABLE = "tool_computable"
    FRAME_UNDECLARED = "frame_undeclared"


class DetectionMethod(str, Enum):
    EXPLICIT_MARKER = "explicit_marker"
    RULE_BASED = "rule_based"
    DEFAULT_UNDECLARED = "default_undeclared"


__all__ = ["DetectionMethod", "FrameKind"]
