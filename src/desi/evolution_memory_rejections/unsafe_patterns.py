"""v30.1 - recurring unsafe patterns and escalation.

Surfaces risk types that recur (>= 2 occurrences) and the
escalation cluster (attempts to claim authority or bypass
governance). Surfacing only - no idea is ever auto-blocked on the
basis of this history.
"""
from __future__ import annotations

from .risk_memory import risk_clusters, risk_occurrences

_ESCALATION_RISKS: frozenset[str] = frozenset({
    "authority_escalation",
})


def recurrent_risks() -> tuple[str, ...]:
    """Risk types occurring at least twice."""
    return tuple(
        rt for rt, ms in risk_clusters().items() if len(ms) >= 2
    )


def unsafe_recurrence_visibility() -> float:
    """Fraction of risk types with >=2 occurrences that are
    surfaced as recurrent, in [0, 1]."""
    clusters = risk_clusters()
    recurrent = [rt for rt, ms in clusters.items() if len(ms) >= 2]
    if not recurrent:
        return 1.0
    surfaced = set(recurrent_risks())
    seen = sum(1 for rt in recurrent if rt in surfaced)
    return round(seen / len(recurrent), 6)


def risk_pattern_visibility() -> float:
    """Fraction of risk types surfaced as a cluster, in
    [0, 1]."""
    clusters = risk_clusters()
    if not clusters:
        return 1.0
    # every risk type maps to a non-empty cluster
    surfaced = sum(1 for ms in clusters.values() if ms)
    return round(surfaced / len(clusters), 6)


def escalation_pattern() -> tuple[str, ...]:
    """Mutation ids that attempted authority escalation."""
    return tuple(sorted(
        o.mutation_id for o in risk_occurrences()
        if o.risk_type in _ESCALATION_RISKS
    ))


def auto_blocks_future_ideas() -> bool:
    """The history never blocks a future idea. Constant False -
    there is no policy-learning path here."""
    return False


__all__ = [
    "auto_blocks_future_ideas",
    "escalation_pattern",
    "recurrent_risks",
    "risk_pattern_visibility",
    "unsafe_recurrence_visibility",
]
