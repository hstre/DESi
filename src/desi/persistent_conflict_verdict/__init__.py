"""DESi v8.4 - persistent conflict verdict
(read-only)."""
from __future__ import annotations

from .classification import (
    AggregatedPersistentMetrics, aggregate,
    classify, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V84Report, build_report,
    build_persistent_conflict_verdict_artifact,
)
from .taxonomy import (
    PERSISTENT_CONFLICT_CLASSES,
    PersistentConflictClass,
)


__all__ = [
    "AggregatedPersistentMetrics",
    "PERSISTENT_CONFLICT_CLASSES",
    "PersistentConflictClass",
    "V84Report",
    "aggregate",
    "build_persistent_conflict_verdict_artifact",
    "build_report",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
