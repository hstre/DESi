"""DESi v4.5 — Bidirectional Cycle Check Patch.

The runtime change lives in ``desi.logic.inference``: one
new ``_bidirectional_cycle`` helper and one new guard inside
``_try_causal_chain`` (Guard 18). Pure structural; no marker
tuple, no synonym list, no content vocabulary.

This package is the non-runtime surface: it mirrors the
predicate, runs the contamination + effect + NC checks, and
assembles the v4.5 report.
"""
from __future__ import annotations

from .contamination import (
    ContaminationReport, check as contamination_check,
)
from .effect import (
    EffectReport, PerClassEffect, measure as effect_measure,
)
from .negative_controls import CycleNC, all_structural_ncs
from .report import (
    EXPECTED_REDUCTION, MAX_FALSE_CYCLE_RATE, MIN_NC_COUNT,
    MIN_NC_DETECTION, NCOutcome, RecommendationOutcome,
    TARGET_AFTER_COUNT, TARGET_BEFORE_COUNT, TARGET_CLUSTER,
    V40_PRE_V43_REPLAY_HASH, V41_PRE_V43_REPLAY_HASH,
    V42_PRE_V43_REPLAY_HASH, V43_REPLAY_HASH, V44_REPLAY_HASH,
    V45Report, build_v45_report,
)
from .structural_check import (
    MIN_OVERLAP_PREMISES, MIN_OVERLAP_TOTAL,
    fires_on_text, overlap_signature,
)


__all__ = [
    "ContaminationReport",
    "CycleNC",
    "EXPECTED_REDUCTION",
    "EffectReport",
    "MAX_FALSE_CYCLE_RATE",
    "MIN_NC_COUNT",
    "MIN_NC_DETECTION",
    "MIN_OVERLAP_PREMISES",
    "MIN_OVERLAP_TOTAL",
    "NCOutcome",
    "PerClassEffect",
    "RecommendationOutcome",
    "TARGET_AFTER_COUNT",
    "TARGET_BEFORE_COUNT",
    "TARGET_CLUSTER",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43_REPLAY_HASH",
    "V44_REPLAY_HASH",
    "V45Report",
    "all_structural_ncs",
    "build_v45_report",
    "contamination_check",
    "effect_measure",
    "fires_on_text",
    "overlap_signature",
]
