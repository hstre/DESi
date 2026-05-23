"""DESi v37.1 - Semantic Audit Risk Benchmark (read-only).

Surfaces semantic audit risks from explicit scenario signals: revenue
recognition, going concern, cashflow-vs-narrative, debt/footnote
inconsistency, implicit inconsistencies and narrative tensions. Every
risk is a flag that requires evidence - never a fraud assertion.
"""
from __future__ import annotations

from .cashflow_semantic_checks import cashflow_vs_narrative_risk
from .going_concern_analysis import going_concern_risk
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V371Report, build_report, build_risk_artifact,
    implicit_inconsistency_detection, narrative_tension_detection,
    replay_stability, risk_metrics, semantic_risk_visibility,
    uncertainty_preservation,
)
from .revenue_recognition_checks import revenue_recognition_risk
from .risk_detector import (
    RISK_TYPES, RiskFlag, all_flags, detect_flags, detect_types,
    provenance, risk_scenarios,
)


__all__ = [
    "REPORT_VERDICTS",
    "RISK_TYPES",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "RiskFlag",
    "V371Report",
    "all_flags",
    "build_report",
    "build_risk_artifact",
    "cashflow_vs_narrative_risk",
    "detect_flags",
    "detect_types",
    "going_concern_risk",
    "implicit_inconsistency_detection",
    "narrative_tension_detection",
    "provenance",
    "replay_stability",
    "revenue_recognition_risk",
    "risk_metrics",
    "risk_scenarios",
    "semantic_risk_visibility",
    "uncertainty_preservation",
]
