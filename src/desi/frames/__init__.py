"""DESi v3.4 — Frame Declaration Layer.

Pre-audit pipeline gating. Frames never decide truth; they decide
which downstream pipeline may even attempt to judge the claim.
"""
from __future__ import annotations

from .compatibility import (
    FrameCompatibilityCheck,
    allowed_pipelines,
    blocked_pipelines,
    check_compatibility,
)
from .declaration import (
    FrameDeclaration,
    compute_frame_replay_hash,
    make_frame_id,
)
from .detector import FrameDetector
from .kinds import DetectionMethod, FrameKind
from .ledger import FrameLedger, FrameLedgerEntry, FrameLedgerEventType

__all__ = [
    "DetectionMethod",
    "FrameCompatibilityCheck",
    "FrameDeclaration",
    "FrameDetector",
    "FrameKind",
    "FrameLedger",
    "FrameLedgerEntry",
    "FrameLedgerEventType",
    "allowed_pipelines",
    "blocked_pipelines",
    "check_compatibility",
    "compute_frame_replay_hash",
    "make_frame_id",
]
