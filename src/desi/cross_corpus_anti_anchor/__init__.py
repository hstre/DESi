"""DESi v3.55 — cross-corpus anti-anchor transfer.

Replays the v3.51 leakage-sample anti-anchor probe
inside each reference corpus and asks whether the
suppression mechanism is universal.
"""
from __future__ import annotations

from .anti_anchor_transfer import (
    MIN_SUPPRESSION, MIN_TARGET_RECALL, aggregate,
    transfer_rate, transfers_at,
)
from .report import (
    PAPER11_TRANSFER_FLOOR, V355Report,
    build_cross_corpus_anti_anchor_artifact,
    build_report,
)
from .suppression import (
    ANTI_COUNT, ANTI_RADIUS, PLATEAU_RADIUS,
    CorpusSuppressionRecord,
    all_corpus_suppression_records,
    per_corpus_anti_ids, per_corpus_suppression,
)


__all__ = [
    "ANTI_COUNT", "ANTI_RADIUS",
    "CorpusSuppressionRecord", "MIN_SUPPRESSION",
    "MIN_TARGET_RECALL", "PAPER11_TRANSFER_FLOOR",
    "PLATEAU_RADIUS", "V355Report", "aggregate",
    "all_corpus_suppression_records",
    "build_cross_corpus_anti_anchor_artifact",
    "build_report", "per_corpus_anti_ids",
    "per_corpus_suppression", "transfer_rate",
    "transfers_at",
]
