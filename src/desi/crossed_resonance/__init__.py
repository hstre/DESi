"""DESi v3.60 — crossed content/method resonance.

Factorial test: every plateau pair is classified into
one of four content x method cells, and v3.50-style
resonance is measured per cell. The best_explanation_
model verdict identifies whether resonance is content-
driven, method-driven, coupling, or null.
"""
from __future__ import annotations

from .conditions import (
    CROSSED_PROBE_RADIUS, ConditionResult,
    CrossedCondition, best_explanation_model,
    interaction_effect, per_condition_results,
)
from .report import (
    V360Report, build_crossed_resonance_artifact,
    build_report,
)
from .transfer import (
    MIN_ANCHORS_FOR_PAIRS,
    corpus_resonance_by_condition,
    crossed_transfer_rate, eligible_corpora,
)


__all__ = [
    "CROSSED_PROBE_RADIUS", "ConditionResult",
    "CrossedCondition", "MIN_ANCHORS_FOR_PAIRS",
    "V360Report", "best_explanation_model",
    "build_crossed_resonance_artifact",
    "build_report",
    "corpus_resonance_by_condition",
    "crossed_transfer_rate", "eligible_corpora",
    "interaction_effect", "per_condition_results",
]
