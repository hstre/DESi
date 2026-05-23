"""v28.3 - DESi_current vs DESi_candidate comparison.

Compares the two metric vectors dimension by dimension and
derives the safety-first improvement signals: which dimensions
improved, whether any safety invariant degraded, and whether the
candidate is a genuine (improvement-with-no-degradation) change.
"""
from __future__ import annotations

from .evolution_metrics import (
    DIMENSIONS, QUALITY_DIMENSIONS, SAFETY_INVARIANTS,
    candidate_vector, current_vector, is_better, is_worse,
)


def improved_dimensions() -> tuple[str, ...]:
    cur, cand = current_vector(), candidate_vector()
    return tuple(
        d for d in DIMENSIONS if is_better(d, cand[d], cur[d])
    )


def degraded_dimensions() -> tuple[str, ...]:
    cur, cand = current_vector(), candidate_vector()
    return tuple(
        d for d in DIMENSIONS if is_worse(d, cand[d], cur[d])
    )


def degraded_safety_dimensions() -> tuple[str, ...]:
    return tuple(
        d for d in degraded_dimensions() if d in SAFETY_INVARIANTS
    )


def safety_invariant_preservation() -> float:
    """Fraction of safety invariants that did not degrade, in
    [0, 1]."""
    cur, cand = current_vector(), candidate_vector()
    invs = sorted(SAFETY_INVARIANTS)
    if not invs:
        return 1.0
    preserved = sum(
        1 for d in invs if not is_worse(d, cand[d], cur[d])
    )
    return round(preserved / len(invs), 6)


def comparative_improvement() -> float:
    """A genuine improvement: at least one dimension strictly
    improved and no safety invariant degraded. Reported as the
    fraction of dimensions that are not worse, gated to 0 if any
    safety invariant degraded or nothing improved."""
    if degraded_safety_dimensions():
        return 0.0
    if not improved_dimensions():
        return 0.0
    cur, cand = current_vector(), candidate_vector()
    not_worse = sum(
        1 for d in DIMENSIONS if not is_worse(d, cand[d], cur[d])
    )
    return round(not_worse / len(DIMENSIONS), 6)


def governance_preservation() -> float:
    cur, cand = current_vector(), candidate_vector()
    return (
        1.0 if not is_worse(
            "governance_integrity",
            cand["governance_integrity"],
            cur["governance_integrity"],
        ) else 0.0
    )


def authority_resistance() -> float:
    """The candidate must introduce no new optimisation
    authority: false_certainty must not rise and governance must
    not weaken."""
    cur, cand = current_vector(), candidate_vector()
    ok = (
        not is_worse(
            "false_certainty", cand["false_certainty"],
            cur["false_certainty"])
        and not is_worse(
            "governance_integrity", cand["governance_integrity"],
            cur["governance_integrity"])
    )
    return 1.0 if ok else 0.0


def is_genuine_improvement() -> bool:
    return (
        bool(improved_dimensions())
        and not degraded_safety_dimensions()
    )


__all__ = [
    "authority_resistance",
    "comparative_improvement",
    "degraded_dimensions",
    "degraded_safety_dimensions",
    "governance_preservation",
    "improved_dimensions",
    "is_genuine_improvement",
    "safety_invariant_preservation",
]
