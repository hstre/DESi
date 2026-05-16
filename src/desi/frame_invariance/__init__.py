"""DESi v3.5 frame-invariance audit — read-only over v3.4 frames."""
from __future__ import annotations

from .case import (
    FrameInvarianceFailure,
    FrameInvarianceResult,
    ParaphraseGroup,
)
from .cases import (
    ALL_GROUPS,
    AUTHORITY_GROUPS,
    EMPIRICAL_GROUPS,
    FORMAL_LOGIC_GROUPS,
    INFORMATION_GROUPS,
    METAPHORICAL_GROUPS,
    NEGATIVE_CONTROLS,
    NegativeControl,
    ONTOLOGICAL_GROUPS,
    THERMODYNAMIC_GROUPS,
    TOOL_GROUPS,
)
from .metrics import (
    FrameInvarianceMetrics,
    compute_invariance_metrics,
    strongest_frame,
    weakest_frame,
)
from .report import FrameInvarianceReport, build_invariance_report
from .runner import (
    FrameInvarianceRun,
    FrameInvarianceRunner,
    NegativeControlResult,
)

__all__ = [
    "ALL_GROUPS",
    "AUTHORITY_GROUPS",
    "EMPIRICAL_GROUPS",
    "FORMAL_LOGIC_GROUPS",
    "FrameInvarianceFailure",
    "FrameInvarianceMetrics",
    "FrameInvarianceReport",
    "FrameInvarianceResult",
    "FrameInvarianceRun",
    "FrameInvarianceRunner",
    "INFORMATION_GROUPS",
    "METAPHORICAL_GROUPS",
    "NEGATIVE_CONTROLS",
    "NegativeControl",
    "NegativeControlResult",
    "ONTOLOGICAL_GROUPS",
    "ParaphraseGroup",
    "THERMODYNAMIC_GROUPS",
    "TOOL_GROUPS",
    "build_invariance_report",
    "compute_invariance_metrics",
    "strongest_frame",
    "weakest_frame",
]
