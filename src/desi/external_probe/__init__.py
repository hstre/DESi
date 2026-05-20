"""DESi v4.0 — External Reality Probe (read-only)."""
from __future__ import annotations

from .contamination import (
    ContaminationHit, ContaminationReport,
    SEMANTIC_OVERLAP_THRESHOLD, check,
)
from .corpus import (
    ExternalChain, all_chains, transitions_per_chain,
)
from .enums import (
    Domain, FailureClass, GroundTruth, RecommendationOutcome,
)
from .report import (
    DomainMetrics, ExternalProbeReport, GlobalMetrics,
    MIN_CHAINS, MIN_DOCUMENTS,
    MIN_EXTERNAL_PRECISION, MIN_EXTERNAL_RECALL,
    MIN_NC_DETECTION, MIN_TRANSITIONS,
    build_external_probe_report,
)
from .runner import ChainOutcome, run_all, run_chain

__all__ = [
    "ChainOutcome",
    "ContaminationHit",
    "ContaminationReport",
    "Domain",
    "DomainMetrics",
    "ExternalChain",
    "ExternalProbeReport",
    "FailureClass",
    "GlobalMetrics",
    "GroundTruth",
    "MIN_CHAINS",
    "MIN_DOCUMENTS",
    "MIN_EXTERNAL_PRECISION",
    "MIN_EXTERNAL_RECALL",
    "MIN_NC_DETECTION",
    "MIN_TRANSITIONS",
    "RecommendationOutcome",
    "SEMANTIC_OVERLAP_THRESHOLD",
    "all_chains",
    "build_external_probe_report",
    "check",
    "run_all",
    "run_chain",
    "transitions_per_chain",
]
