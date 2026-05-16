"""DESi v3.12 + v3.13 frame-tension integration.

* v3.12 (read-only probe): corpus, simulators, scoring, report.
* v3.13 (runtime patch): router + routing ledger + integration
  benchmark.
"""
from __future__ import annotations

from .benchmark import (
    IntegrationCase,
    IntegrationCategory,
    build_integration_benchmark,
    category_counts,
    permitted_events,
)
from .corpus import CorpusCase, build_corpus, corpus_summary
from .enums import CorpusOrigin, InsertionPoint
from .ledger import (
    FrameRoutingLedger,
    FrameRoutingLedgerEntry,
    FrameRoutingLedgerEvent,
)
from .report import (
    IntegrationProbeReport,
    MAX_FALSE_BLOCK_RATE,
    MIN_MANIPULATION_BLOCK_RATE,
    build_integration_report,
)
from .router import (
    FrameTensionRouter,
    RoutingDecision,
    RoutingPipeline,
)
from .scoring import InsertionMetrics, compute_metrics
from .simulators import SimulationOutcome, simulate_all_points

__all__ = [
    "CorpusCase",
    "CorpusOrigin",
    "FrameRoutingLedger",
    "FrameRoutingLedgerEntry",
    "FrameRoutingLedgerEvent",
    "FrameTensionRouter",
    "IntegrationCase",
    "IntegrationCategory",
    "IntegrationProbeReport",
    "InsertionMetrics",
    "InsertionPoint",
    "MAX_FALSE_BLOCK_RATE",
    "MIN_MANIPULATION_BLOCK_RATE",
    "RoutingDecision",
    "RoutingPipeline",
    "SimulationOutcome",
    "build_corpus",
    "build_integration_benchmark",
    "build_integration_report",
    "category_counts",
    "compute_metrics",
    "corpus_summary",
    "permitted_events",
    "simulate_all_points",
]
