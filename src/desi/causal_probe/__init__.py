"""DESi v2.6 causal-chain coverage probe — read-only over v1.5 + v2.3."""
from __future__ import annotations

from .metrics import ProbeMetrics, compute_probe_metrics
from .pattern import (
    BenchmarkSource,
    CausalChainCandidate,
    candidate_replay_hash,
    count_atomic_sequence,
    count_repeated_content,
    hypothetical_trigger,
)
from .report import (
    CausalChainProbeReport,
    build_probe_report,
    compute_report_replay_hash,
)
from .risk import KNOWN_FALSE_POSITIVE_CASE_IDS, RiskFlag
from .runner import CausalChainProbeRunner, CausalProbeRun

__all__ = [
    "BenchmarkSource",
    "CausalChainCandidate",
    "CausalChainProbeReport",
    "CausalChainProbeRunner",
    "CausalProbeRun",
    "KNOWN_FALSE_POSITIVE_CASE_IDS",
    "ProbeMetrics",
    "RiskFlag",
    "build_probe_report",
    "candidate_replay_hash",
    "compute_probe_metrics",
    "compute_report_replay_hash",
    "count_atomic_sequence",
    "count_repeated_content",
    "hypothetical_trigger",
]
