"""Closed taxonomy of pipeline gates + classification labels."""
from __future__ import annotations

from enum import Enum


class Gate(str, Enum):
    """The seven runtime gates the ablation masks one at a time."""

    BASELINE             = "BASELINE"
    G1_PREMISE_EXTRACTOR = "PremiseExtractor"
    G2_SPL               = "SPL"
    G3_FRAME_DECLARATION = "FrameDeclaration"
    G4_FRAME_TENSION     = "FrameTension"
    G5_ROUTER            = "FrameTensionRouter"
    G6_CAUSAL_CHAIN      = "CAUSAL_CHAIN"
    G7_SUSPENSION_GATE   = "SuspensionGate"


_ABLATED_GATES: tuple[Gate, ...] = (
    Gate.G1_PREMISE_EXTRACTOR,
    Gate.G2_SPL,
    Gate.G3_FRAME_DECLARATION,
    Gate.G4_FRAME_TENSION,
    Gate.G5_ROUTER,
    Gate.G6_CAUSAL_CHAIN,
    Gate.G7_SUSPENSION_GATE,
)


def ablated_gates() -> tuple[Gate, ...]:
    return _ABLATED_GATES


class GateClassification(str, Enum):
    DEAD_KNOB     = "DEAD_KNOB"
    PRIMARY_CLIFF = "PRIMARY_CLIFF"
    SUPPORT_LAYER = "SUPPORT_LAYER"


__all__ = [
    "Gate",
    "GateClassification",
    "ablated_gates",
]
