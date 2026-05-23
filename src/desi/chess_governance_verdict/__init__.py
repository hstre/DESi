"""DESi v11.4 - chess governance verdict
(read-only)."""
from __future__ import annotations

from .classification import (
    AggregatedChessMetrics, aggregate,
    classify, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V114Report,
    build_chess_governance_verdict_artifact,
    build_report,
)
from .taxonomy import (
    CHESS_GOVERNANCE_CLASSES,
    ChessGovernanceClass,
)


__all__ = [
    "AggregatedChessMetrics",
    "CHESS_GOVERNANCE_CLASSES",
    "ChessGovernanceClass",
    "V114Report",
    "aggregate",
    "build_chess_governance_verdict_artifact",
    "build_report",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
