"""DESi v3.12 frame-tension integration probe — read-only over v3.8/9/10/11."""
from __future__ import annotations

from .corpus import CorpusCase, build_corpus, corpus_summary
from .enums import CorpusOrigin, InsertionPoint
from .report import (
    IntegrationProbeReport,
    MAX_FALSE_BLOCK_RATE,
    MIN_MANIPULATION_BLOCK_RATE,
    build_integration_report,
)
from .scoring import InsertionMetrics, compute_metrics
from .simulators import SimulationOutcome, simulate_all_points

__all__ = [
    "CorpusCase",
    "CorpusOrigin",
    "IntegrationProbeReport",
    "InsertionMetrics",
    "InsertionPoint",
    "MAX_FALSE_BLOCK_RATE",
    "MIN_MANIPULATION_BLOCK_RATE",
    "SimulationOutcome",
    "build_corpus",
    "build_integration_report",
    "compute_metrics",
    "corpus_summary",
    "simulate_all_points",
]
