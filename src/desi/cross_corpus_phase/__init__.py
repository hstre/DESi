"""DESi v3.56 — cross-corpus phase transition transfer.

Replays the v3.52 mass sweep per corpus and reports
whether the discrete tipping behaviour is corpus-
invariant.
"""
from __future__ import annotations

from .phase_transfer import (
    per_corpus_summary, transfer_rate, transfers_at,
)
from .report import (
    PAPER11_TRANSFER_FLOOR, V356Report,
    build_cross_corpus_phase_artifact, build_report,
)
from .transition import (
    MIN_ANCHORS_FOR_DISCONTINUITY, PROBE_RADIUS,
    PhasePoint, coupling_strength,
    discontinuity_score, eligible_corpora,
    ineligible_corpora,
    per_corpus_phase_curve, saturation_point,
)


__all__ = [
    "MIN_ANCHORS_FOR_DISCONTINUITY",
    "PAPER11_TRANSFER_FLOOR", "PROBE_RADIUS",
    "PhasePoint", "V356Report",
    "build_cross_corpus_phase_artifact",
    "build_report", "coupling_strength",
    "discontinuity_score", "eligible_corpora",
    "ineligible_corpora",
    "per_corpus_phase_curve",
    "per_corpus_summary", "saturation_point",
    "transfer_rate", "transfers_at",
]
