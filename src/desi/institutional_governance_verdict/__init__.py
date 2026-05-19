"""DESi v10.4 - institutional governance verdict
(read-only)."""
from __future__ import annotations

from .classification import (
    AggregatedInstitutionalMetrics, aggregate,
    classify, gate_failing_conditions,
    gate_passes_all,
)
from .report import (
    V104Report,
    build_institutional_governance_verdict_artifact,
    build_report,
)
from .taxonomy import (
    INSTITUTIONAL_GOVERNANCE_CLASSES,
    InstitutionalGovernanceClass,
)


__all__ = [
    "AggregatedInstitutionalMetrics",
    "INSTITUTIONAL_GOVERNANCE_CLASSES",
    "InstitutionalGovernanceClass",
    "V104Report",
    "aggregate",
    "build_institutional_governance_verdict_artifact",
    "build_report",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
