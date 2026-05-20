"""DESi v5.4 - adolescence verdict."""
from __future__ import annotations

from .decision import (
    AggregatedMetrics, aggregate_metrics,
    classify, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V54Report,
    build_adolescence_verdict_artifact,
    build_report,
)
from .taxonomy import (
    ADOLESCENCE_CLASSES, AdolescenceClass,
)


__all__ = [
    "ADOLESCENCE_CLASSES",
    "AdolescenceClass",
    "AggregatedMetrics",
    "V54Report",
    "aggregate_metrics",
    "build_adolescence_verdict_artifact",
    "build_report",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
