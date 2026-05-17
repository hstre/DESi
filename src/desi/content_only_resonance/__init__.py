"""DESi v3.59 — content-only resonance.

Replays the v3.50 + v3.54 pair resonance analysis on
the 5-d content subspace and reports both the global
aggregate and the per-corpus result.
"""
from __future__ import annotations

from .probe import (
    CONTENT_PROBE_RADIUS, ContentPairSummary,
    GLOBAL_CONTROL_COUNT,
    MIN_ANCHORS_FOR_PAIRS, eligible_corpora,
    global_control_summary, global_plateau_summary,
    ineligible_corpora,
    per_corpus_control_summary,
    per_corpus_plateau_summary,
)
from .report import (
    V359Report, build_content_resonance_artifact,
    build_report,
)


__all__ = [
    "CONTENT_PROBE_RADIUS", "ContentPairSummary",
    "GLOBAL_CONTROL_COUNT",
    "MIN_ANCHORS_FOR_PAIRS", "V359Report",
    "build_content_resonance_artifact",
    "build_report", "eligible_corpora",
    "global_control_summary",
    "global_plateau_summary",
    "ineligible_corpora",
    "per_corpus_control_summary",
    "per_corpus_plateau_summary",
]
