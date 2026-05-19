"""DESi v12.0 - wild exploration sandbox
(read-only; no breakthrough claims)."""
from __future__ import annotations

from .explorer import (
    HYPOTHESIS_SHAPES, Hypothesis,
    HypothesisShape, fixture, shape_counts,
    status_counts,
)
from .governance import (
    GovernedHypothesis,
    classification_accuracy, classify,
    governed_hypotheses,
    overreach_rejection_rate,
    replay_reuse_rate,
)
from .hypotheses import (
    EPISTEMIC_STATUSES, EpistemicStatus,
)
from .mutation import (
    MUTATION_OPS, MutationEvent, MutationOp,
    mutation_events, op_counts,
)
from .report import (
    V120Report, branch_growth, build_report,
    build_wild_sandbox_artifact,
    exploration_diversity,
    hallucination_pressure, redundancy_rate,
)


__all__ = [
    "EPISTEMIC_STATUSES",
    "EpistemicStatus",
    "GovernedHypothesis",
    "HYPOTHESIS_SHAPES",
    "Hypothesis",
    "HypothesisShape",
    "MUTATION_OPS",
    "MutationEvent",
    "MutationOp",
    "V120Report",
    "branch_growth",
    "build_report",
    "build_wild_sandbox_artifact",
    "classification_accuracy",
    "classify",
    "exploration_diversity",
    "fixture",
    "governed_hypotheses",
    "hallucination_pressure",
    "mutation_events",
    "op_counts",
    "overreach_rejection_rate",
    "redundancy_rate",
    "replay_reuse_rate",
    "shape_counts",
    "status_counts",
]
