"""DESi v3.58 — method-only resonance.

Replays the v3.50 + v3.54 pair resonance analysis on
the 4-d method subspace and reports both the global
aggregate and the per-corpus result.
"""
from __future__ import annotations

from .probe import (
    GLOBAL_CONTROL_COUNT, METHOD_PROBE_RADIUS,
    MIN_ANCHORS_FOR_PAIRS, MethodPairSummary,
    eligible_corpora, global_control_summary,
    global_plateau_summary, ineligible_corpora,
    per_corpus_control_summary,
    per_corpus_plateau_summary,
)
from .report import (
    V358Report, build_method_resonance_artifact,
    build_report,
)


__all__ = [
    "GLOBAL_CONTROL_COUNT", "METHOD_PROBE_RADIUS",
    "MIN_ANCHORS_FOR_PAIRS", "MethodPairSummary",
    "V358Report",
    "build_method_resonance_artifact",
    "build_report", "eligible_corpora",
    "global_control_summary",
    "global_plateau_summary",
    "ineligible_corpora",
    "per_corpus_control_summary",
    "per_corpus_plateau_summary",
]
