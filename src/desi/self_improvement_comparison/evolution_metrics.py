"""v28.3 - benchmark dimensions and metric vectors.

The comparison dimensions for DESi_current vs DESi_candidate.
The candidate vector is a *projection* of the safe accepted patch
set, not a measurement of a built system: safety invariants are
held equal by construction (the patches only touch allowed,
non-core areas), and only quality dimensions may move up.
"""
from __future__ import annotations

# All comparison dimensions and whether higher is better.
HIGHER_IS_BETTER: dict[str, bool] = {
    "replay_stability": True,
    "false_certainty": False,
    "exploration_diversity": True,
    "novelty": True,
    "hallucination_containment": True,
    "graph_integrity": True,
    "rendering_quality": True,
    "regression_survival": True,
    "governance_integrity": True,
}
DIMENSIONS: tuple[str, ...] = tuple(sorted(HIGHER_IS_BETTER))

# Dimensions that must never degrade (the safety invariants).
SAFETY_INVARIANTS: frozenset[str] = frozenset({
    "replay_stability", "false_certainty",
    "hallucination_containment", "graph_integrity",
    "regression_survival", "governance_integrity",
})
# Dimensions a candidate may improve.
QUALITY_DIMENSIONS: frozenset[str] = frozenset(
    d for d in DIMENSIONS if d not in SAFETY_INVARIANTS
)

_CURRENT: dict[str, float] = {
    "replay_stability": 1.0,
    "false_certainty": 0.0,
    "exploration_diversity": 1.0,
    "novelty": 0.7,
    "hallucination_containment": 1.0,
    "graph_integrity": 1.0,
    "rendering_quality": 0.9,
    "regression_survival": 1.0,
    "governance_integrity": 1.0,
}

# Projected candidate: safety invariants identical; two quality
# dimensions nudged up by the safe patch set.
_CANDIDATE: dict[str, float] = {
    **_CURRENT,
    "novelty": 0.75,
    "rendering_quality": 0.95,
}


def current_vector() -> dict[str, float]:
    return dict(_CURRENT)


def candidate_vector() -> dict[str, float]:
    return dict(_CANDIDATE)


def is_better(dim: str, candidate: float, current: float) -> bool:
    return (
        candidate > current if HIGHER_IS_BETTER[dim]
        else candidate < current
    )


def is_worse(dim: str, candidate: float, current: float) -> bool:
    return (
        candidate < current if HIGHER_IS_BETTER[dim]
        else candidate > current
    )


def delta(dim: str) -> float:
    return round(_CANDIDATE[dim] - _CURRENT[dim], 6)


__all__ = [
    "DIMENSIONS",
    "HIGHER_IS_BETTER",
    "QUALITY_DIMENSIONS",
    "SAFETY_INVARIANTS",
    "candidate_vector",
    "current_vector",
    "delta",
    "is_better",
    "is_worse",
]
