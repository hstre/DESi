"""DESi v4.3 — External Audit Marker Extension Patch.

The runtime change lives in ``desi.logic.inference``: three new
marker tuples (``_V43_NEGATION_EXTENSIONS``,
``_V43_QUANTIFIER_EXTENSIONS``, ``_V43_AUTHORITY_LIKE_VERBS``)
and three new guards inside ``_try_causal_chain`` that
suspend on those tokens.

This package is the *non-runtime* surface: it mirrors the
marker tuples, runs the contamination + effect + NC checks,
and assembles the v4.3 report.
"""
from __future__ import annotations

from .contamination import (
    ContaminationReport, TokenContamination, check as contamination_check,
)
from .effect import EffectReport, PerClassEffect, measure as effect_measure
from .extensions import (
    AUTHORITY_CONTAMINATION_EXTENSIONS,
    HIDDEN_NEGATION_EXTENSIONS, PATCHED_CLUSTERS,
    QUANTIFIER_DRIFT_EXTENSIONS, UNPATCHED_CLUSTERS_FROM_V42,
    all_extensions,
)
from .negative_controls import PatchNC, all_patch_ncs
from .report import (
    FALSE_SUPPORT_BEFORE, FALSE_SUPPORT_TARGET_AFTER,
    MIN_NC_COUNT, MIN_NC_DETECTION, NCOutcome,
    RecommendationOutcome, V40_PRE_V43_REPLAY_HASH,
    V41_PRE_V43_REPLAY_HASH, V42_PRE_V43_REPLAY_HASH,
    V43Report, build_v43_report,
)


__all__ = [
    "AUTHORITY_CONTAMINATION_EXTENSIONS",
    "ContaminationReport",
    "EffectReport",
    "FALSE_SUPPORT_BEFORE",
    "FALSE_SUPPORT_TARGET_AFTER",
    "HIDDEN_NEGATION_EXTENSIONS",
    "MIN_NC_COUNT",
    "MIN_NC_DETECTION",
    "NCOutcome",
    "PATCHED_CLUSTERS",
    "PatchNC",
    "PerClassEffect",
    "QUANTIFIER_DRIFT_EXTENSIONS",
    "RecommendationOutcome",
    "TokenContamination",
    "UNPATCHED_CLUSTERS_FROM_V42",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43Report",
    "all_extensions",
    "all_patch_ncs",
    "build_v43_report",
    "contamination_check",
    "effect_measure",
]
