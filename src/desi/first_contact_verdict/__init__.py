"""DESi v6.4 - first contact verdict
(read-only)."""
from __future__ import annotations

from .classification import (
    AggregatedFirstContactMetrics, aggregate,
    classify, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V64Report,
    build_first_contact_verdict_artifact,
    build_report,
)
from .taxonomy import (
    FIRST_CONTACT_CLASSES, FirstContactClass,
)


__all__ = [
    "AggregatedFirstContactMetrics",
    "FIRST_CONTACT_CLASSES",
    "FirstContactClass",
    "V64Report",
    "aggregate",
    "build_first_contact_verdict_artifact",
    "build_report",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
