"""DESi v3.46 — GAP_DETECTED census.

Identifies and characterises every trajectory in the
corpus that lands in or visits GAP_DETECTED
(support_state = 1.0). Confirms Paper 10's
2 non-rescued GAP cases and surfaces any GAP cases
the controller missed.
"""
from __future__ import annotations

from .extractor import (
    GapCase, collect_gap_cases,
    gap_cases_outside_non_rescued,
    source_corpus_distribution, terminal_gap_cases,
    transient_gap_cases,
)
from .report import (
    V346Report, build_gap_inventory_artifact,
    build_report,
)
from .state import (
    GAP_DETECTED_STATE, GapPattern,
    PAPER10_TERMINAL_GAP_COUNT, classify_gap,
)


__all__ = [
    "GAP_DETECTED_STATE", "GapCase", "GapPattern",
    "PAPER10_TERMINAL_GAP_COUNT", "V346Report",
    "build_gap_inventory_artifact", "build_report",
    "classify_gap", "collect_gap_cases",
    "gap_cases_outside_non_rescued",
    "source_corpus_distribution",
    "terminal_gap_cases", "transient_gap_cases",
]
