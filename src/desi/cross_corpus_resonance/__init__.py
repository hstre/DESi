"""DESi v3.54 — cross-corpus pair resonance transfer.

Replays the v3.50 pair matrix and control comparator
per corpus and reports whether the resonance
structure is corpus-invariant or v3-aggregate-only.
"""
from __future__ import annotations

from .matrix import (
    all_corpora_pair_matrices,
    per_corpus_pair_matrix,
)
from .pair_transfer import (
    CorpusPairSummary, MIN_ANCHORS_FOR_PAIRS,
    PROBE_RADIUS, eligible_corpora,
    ineligible_corpora,
    per_corpus_control_summary,
    per_corpus_plateau_summary,
    triple_max_extra,
)
from .report import (
    PAPER11_TRANSFER_FLOOR, V354Report,
    build_cross_corpus_resonance_artifact,
    build_report,
)


__all__ = [
    "CorpusPairSummary", "MIN_ANCHORS_FOR_PAIRS",
    "PAPER11_TRANSFER_FLOOR", "PROBE_RADIUS",
    "V354Report",
    "all_corpora_pair_matrices",
    "build_cross_corpus_resonance_artifact",
    "build_report", "eligible_corpora",
    "ineligible_corpora",
    "per_corpus_control_summary",
    "per_corpus_pair_matrix",
    "per_corpus_plateau_summary",
    "triple_max_extra",
]
