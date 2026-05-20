"""DESi v3.96a - hash-seed jitter census.

Runs the trajectory extractor under multiple
PYTHONHASHSEED values to measure how often the
StateVector output drifts.
"""
from __future__ import annotations

from .jitter import (
    JitterCensus, REFERENCE_SEED, SEED_CENSUS,
    affected_packages, census, run_with_seed,
)
from .report import (
    V396aReport,
    build_jitter_census_artifact,
    build_report,
)
from .seeds import (
    SHUFFLE_SEEDS, ShuffleOutcome,
    all_shuffle_outcomes,
    shuffle_failure_rate,
)


__all__ = [
    "JitterCensus",
    "REFERENCE_SEED",
    "SEED_CENSUS",
    "SHUFFLE_SEEDS",
    "ShuffleOutcome",
    "V396aReport",
    "affected_packages",
    "all_shuffle_outcomes",
    "build_jitter_census_artifact",
    "build_report",
    "census",
    "run_with_seed",
    "shuffle_failure_rate",
]
