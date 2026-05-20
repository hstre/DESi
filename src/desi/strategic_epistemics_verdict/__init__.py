"""DESi v9.4 - strategic epistemics verdict
(read-only)."""
from __future__ import annotations

from .classification import (
    AggregatedStrategicMetrics, aggregate,
    classify, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V94Report, build_report,
    build_strategic_epistemics_verdict_artifact,
)
from .taxonomy import (
    STRATEGIC_EPISTEMICS_CLASSES,
    StrategicEpistemicsClass,
)


__all__ = [
    "AggregatedStrategicMetrics",
    "STRATEGIC_EPISTEMICS_CLASSES",
    "StrategicEpistemicsClass",
    "V94Report",
    "aggregate",
    "build_report",
    "build_strategic_epistemics_verdict_artifact",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
