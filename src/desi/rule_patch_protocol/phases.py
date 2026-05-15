"""Closed enumeration of patch-protocol phases — Aufgabe 1.

Seven values exactly. Adding a phase requires a new directive — the
protocol orchestrator validates that every phase in this enum is
visited in declaration order before a patch is marked
``COMPLETE``.
"""
from __future__ import annotations

from enum import Enum


class PatchPhase(str, Enum):
    DISCOVERY = "discovery"
    RISK_PROBE = "risk_probe"
    GUARD_SYNTHESIS = "guard_synthesis"
    IMPLEMENTATION = "implementation"
    REGRESSION = "regression"
    REPLAY_VERIFICATION = "replay_verification"
    COMPLETE = "complete"


PHASE_ORDER: tuple[PatchPhase, ...] = (
    PatchPhase.DISCOVERY,
    PatchPhase.RISK_PROBE,
    PatchPhase.GUARD_SYNTHESIS,
    PatchPhase.IMPLEMENTATION,
    PatchPhase.REGRESSION,
    PatchPhase.REPLAY_VERIFICATION,
    PatchPhase.COMPLETE,
)


__all__ = ["PHASE_ORDER", "PatchPhase"]
