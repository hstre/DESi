"""DESi v3.53 — cross-corpus radius transfer.

Replays the v3.44 radius sweep + v3.49 frame masks on
each reference corpus (v2.3, v3.14, v3.15, v3.16) and
asks whether the semantic-field phenomenon survives
corpus boundaries.
"""
from __future__ import annotations

from .corpus_loader import (
    CorpusKind, REFERENCE_CORPORA,
    corpus_leakage_trajectories, corpus_of,
    corpus_plateau_anchors, corpus_present,
    corpus_trajectories, normalised_prefix,
)
from .radius_transfer import (
    CorpusRadiusRecord, RELATIVE_BREAK_FLOOR,
    leakage_at_radius, per_corpus_critical_radius,
    per_corpus_radius_record,
    plateau_recall_at_radius,
)
from .report import (
    PAPER11_TRANSFER_FLOOR, V353Report,
    build_cross_corpus_radius_artifact, build_report,
)


__all__ = [
    "CorpusKind", "CorpusRadiusRecord",
    "PAPER11_TRANSFER_FLOOR", "REFERENCE_CORPORA",
    "RELATIVE_BREAK_FLOOR", "V353Report",
    "build_cross_corpus_radius_artifact",
    "build_report", "corpus_leakage_trajectories",
    "corpus_of", "corpus_plateau_anchors",
    "corpus_present", "corpus_trajectories",
    "leakage_at_radius", "normalised_prefix",
    "per_corpus_critical_radius",
    "per_corpus_radius_record",
    "plateau_recall_at_radius",
]
