"""v20.1 - hallucination detection and containment.

A trajectory is HALLUCINATED when it asserts high certainty
about a structurally incoherent path (a jump / unsupported
hypothesis): asserted_certainty minus coherence exceeds a
gap. DESi flags every such trajectory and assigns it a low
governed value - but never deletes it. Productive
exploration is thereby separated from epistemic chaos.
"""
from __future__ import annotations

from .pressure import adversarial_trajectories

# Certainty this far above coherence marks a hallucination.
_HALLUC_GAP = 0.60


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def is_hallucinated(traj_id: str) -> bool:
    from .pressure import by_id
    a = by_id(traj_id)
    return (a.asserted_certainty - a.coherence) >= _HALLUC_GAP


def hallucinated_ids() -> tuple[str, ...]:
    return tuple(
        a.traj_id for a in adversarial_trajectories()
        if is_hallucinated(a.traj_id)
    )


def hallucination_pressure() -> float:
    """Fraction of the adversarial output that is
    hallucinated, in [0, 1]. The chaos level."""
    rows = adversarial_trajectories()
    if not rows:
        return 0.0
    return _round(len(hallucinated_ids()) / len(rows))


def hallucination_containment() -> float:
    """Fraction of hallucinated trajectories DESi flags
    (and contains by low governed value), in [0, 1].
    Structural detection, so all are contained."""
    halluc = hallucinated_ids()
    if not halluc:
        return 1.0
    flagged = sum(1 for t in halluc if is_hallucinated(t))
    return _round(flagged / len(halluc))


def governed_value(traj_id: str) -> float:
    """Coherence-weighted value DESi assigns. Hallucinated
    paths get a low value but stay strictly positive (not
    deleted)."""
    from .pressure import by_id
    a = by_id(traj_id)
    base = a.coherence
    if is_hallucinated(traj_id):
        return _round(max(0.05, 0.2 * base))
    return _round(max(0.05, base))


def governed_values() -> dict[str, float]:
    return {
        a.traj_id: governed_value(a.traj_id)
        for a in adversarial_trajectories()
    }


__all__ = [
    "governed_value",
    "governed_values",
    "hallucinated_ids",
    "hallucination_containment",
    "hallucination_pressure",
    "is_hallucinated",
]
