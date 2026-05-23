"""DESi v3.18 — Causal Naturalness Probe (read-only)."""
from __future__ import annotations

from .corpus import ChainEntry, all_input_chains
from .detector import (
    AnomalyVerdict,
    MIN_OUTLIER_FEATURES,
    ManifoldStats,
    build_manifold,
    classify_all,
    classify_anomaly,
    valid_manifold_subset,
)
from .features import NaturalnessVector, compute_vector
from .negative_control import ALL_NC_CHAINS, NCChain, NCShape
from .report import (
    CorpusDistribution,
    CorpusPairSeparation,
    MAX_FALSE_ALARM_RATE,
    MIN_ADVERSARIAL_DETECTION_RATE,
    MIN_CHAIN_COUNT,
    MIN_HELDOUT_SURVIVAL,
    MIN_LINK_COUNT,
    MIN_VALID_ACCEPT_RATE,
    NCResult,
    NaturalnessReport,
    build_naturalness_report,
)

__all__ = [
    "ALL_NC_CHAINS",
    "AnomalyVerdict",
    "ChainEntry",
    "CorpusDistribution",
    "CorpusPairSeparation",
    "MAX_FALSE_ALARM_RATE",
    "MIN_ADVERSARIAL_DETECTION_RATE",
    "MIN_CHAIN_COUNT",
    "MIN_HELDOUT_SURVIVAL",
    "MIN_LINK_COUNT",
    "MIN_OUTLIER_FEATURES",
    "MIN_VALID_ACCEPT_RATE",
    "ManifoldStats",
    "NCChain",
    "NCResult",
    "NCShape",
    "NaturalnessReport",
    "NaturalnessVector",
    "all_input_chains",
    "build_manifold",
    "build_naturalness_report",
    "classify_all",
    "classify_anomaly",
    "compute_vector",
    "valid_manifold_subset",
]
