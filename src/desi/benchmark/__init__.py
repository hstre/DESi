"""DESi v1.5 — Real-world benchmark + philosophical stress test.

The benchmark measures whether the v1.2..v1.4 pipeline behaves as
an epistemic engine or as an overfitted formalist. It deliberately
adds no new operators, no new heuristics, no new mutation knobs.

Public surface:

* :class:`BenchmarkCase` / :class:`BenchmarkResult` / :class:`BenchmarkRun`
* :class:`BenchmarkRunner` — runs all 50 cases through v1.4
* :func:`compute_metrics`   — precision / recall + four named rates
* :func:`render_markdown_report`
"""
from __future__ import annotations

from .case import (
    BenchmarkCase,
    BenchmarkResult,
    Category,
    GroundTruth,
    classify_outcome,
)
from .cases import (
    ALL_CASES,
    case_by_id,
    cases_by_category,
)
from .metrics import (
    BenchmarkMetrics,
    CategoryMetrics,
    compute_metrics,
)
from .report import render_markdown_report
from .runner import BenchmarkRun, BenchmarkRunner

__all__ = [
    "ALL_CASES",
    "BenchmarkCase",
    "BenchmarkMetrics",
    "BenchmarkResult",
    "BenchmarkRun",
    "BenchmarkRunner",
    "Category",
    "CategoryMetrics",
    "GroundTruth",
    "case_by_id",
    "cases_by_category",
    "classify_outcome",
    "compute_metrics",
    "render_markdown_report",
]
