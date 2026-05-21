"""DESi v34.3 - Scientific Rendering & Citation Benchmark Run.

Runs citation / rendering checks against the v25 output ports: every
external claim is referenced, phantom citations are rejected, numbers
are derived/traceable, limitations are surfaced and the paper port is
compliant. Read-only; no new rendering logic.
"""
from __future__ import annotations

from .citation_runner import (
    citation_completeness, naked_claims, no_naked_claims,
    result_traceability, usage_integrity,
)
from .paper_quality_scorecard import (
    PaperQualityScorecard, limitation_visibility,
    metric_derivation_visibility, paper_port_compliance,
    paper_quality_scorecard,
)
from .phantom_citation_check import (
    live_phantoms, orphans, phantom_citation_resistance,
)
from .rendering_tasks import PAPER_PORT, RENDERING_CHECKS, paper_port
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V343Report, build_rendering_artifact, build_report,
    rendering_metrics, replay_stability,
)


__all__ = [
    "PAPER_PORT",
    "RENDERING_CHECKS",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "PaperQualityScorecard",
    "V343Report",
    "build_rendering_artifact",
    "build_report",
    "citation_completeness",
    "limitation_visibility",
    "live_phantoms",
    "metric_derivation_visibility",
    "naked_claims",
    "no_naked_claims",
    "orphans",
    "paper_port",
    "paper_port_compliance",
    "paper_quality_scorecard",
    "phantom_citation_resistance",
    "rendering_metrics",
    "replay_stability",
    "result_traceability",
    "usage_integrity",
]
