"""DESi v3.4 frame benchmark."""
from __future__ import annotations

from .case import FrameBenchmarkCase, FrameCategory
from .cases import (
    ALL_FRAME_CASES,
    A_CASES, B_CASES, C_CASES, D_CASES,
    E_CASES, F_CASES, G_CASES, H_CASES,
    cases_by_category,
)
from .metrics import FrameBenchmarkMetrics, compute_frame_metrics
from .runner import (
    FrameBenchmarkResult,
    FrameBenchmarkRun,
    FrameBenchmarkRunner,
)

__all__ = [
    "ALL_FRAME_CASES",
    "A_CASES", "B_CASES", "C_CASES", "D_CASES",
    "E_CASES", "F_CASES", "G_CASES", "H_CASES",
    "FrameBenchmarkCase",
    "FrameBenchmarkMetrics",
    "FrameBenchmarkResult",
    "FrameBenchmarkRun",
    "FrameBenchmarkRunner",
    "FrameCategory",
    "cases_by_category",
    "compute_frame_metrics",
]
