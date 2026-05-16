"""DESi v3.11 — FRAME_TENSION_LAYER runtime gate.

First runtime patch in the frame line. Gates context inheritance
through the v3.9 consistency taxonomy realised on top of the
v3.4 FrameDetector. No truth decisions — pipeline gating only.
"""
from __future__ import annotations

from .benchmark import ALL_LAYER_CASES, LayerCase
from .consistency import (
    ConsistencyVerdict,
    FrameConsistency,
    FrameSide,
    evaluate_consistency,
)
from .layer import FrameTensionLayer, LayerDecision
from .ledger import (
    FrameTensionLedger,
    FrameTensionLedgerEntry,
    FrameTensionLedgerEvent,
)

__all__ = [
    "ALL_LAYER_CASES",
    "ConsistencyVerdict",
    "FrameConsistency",
    "FrameSide",
    "FrameTensionLayer",
    "FrameTensionLedger",
    "FrameTensionLedgerEntry",
    "FrameTensionLedgerEvent",
    "LayerCase",
    "LayerDecision",
    "evaluate_consistency",
]
