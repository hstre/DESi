"""DESi v32.2 - Blind Evolution Evaluation (read-only).

The frozen baseline and the mutated v31 version are compared under
neutral anonymous labels. The evaluator scores only by the measured
recompute count and never sees which version is the mutated one:
no version-aware scoring, no mutation favouritism, no branch bias.
The blind winner is verified post-hoc to be the mutated version.
"""
from __future__ import annotations

from .anonymous_versions import (
    TRUE_BASELINE, TRUE_MUTATED, AnonObservation, anon_observations,
    sealed_map,
)
from .bias_control import bias_resistance, blindness_integrity
from .blind_runner import observed_labels, replay_stability, run_blind
from .evaluation import (
    blind_ranking, blind_winner, blind_winner_is_mutated, margin,
)
from .report import (
    BLIND_EVALUATION, REPORT_VERDICTS, VERDICT_BLIND_BETTER,
    VERDICT_BLIND_NEUTRAL, VERDICT_HALT, V322Report,
    build_blind_artifact, build_report,
)


__all__ = [
    "BLIND_EVALUATION",
    "REPORT_VERDICTS",
    "TRUE_BASELINE",
    "TRUE_MUTATED",
    "VERDICT_BLIND_BETTER",
    "VERDICT_BLIND_NEUTRAL",
    "VERDICT_HALT",
    "AnonObservation",
    "V322Report",
    "anon_observations",
    "bias_resistance",
    "blind_ranking",
    "blind_winner",
    "blind_winner_is_mutated",
    "blindness_integrity",
    "build_blind_artifact",
    "build_report",
    "margin",
    "observed_labels",
    "replay_stability",
    "run_blind",
    "sealed_map",
]
