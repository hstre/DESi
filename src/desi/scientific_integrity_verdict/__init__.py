"""DESi v13.4 - scientific integrity verdict
(read-only)."""
from __future__ import annotations

from .classification import (
    AggregatedScientificMetrics, aggregate,
    classify, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V134Report,
    build_scientific_integrity_verdict_artifact,
    build_report,
)
from .taxonomy import (
    SCIENTIFIC_INTEGRITY_CLASSES,
    ScientificIntegrityClass,
)


__all__ = [
    "AggregatedScientificMetrics",
    "SCIENTIFIC_INTEGRITY_CLASSES",
    "ScientificIntegrityClass",
    "V134Report",
    "aggregate",
    "build_report",
    "build_scientific_integrity_verdict_artifact",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
