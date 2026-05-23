"""v20.1 - novelty under adversarial pressure.

Separates the PRODUCTIVE (coherent, non-hallucinated)
novelty from the chaotic jumps, and confirms DESi
preserves all of the productive novelty - the informative
exploration is kept even while the chaos is contained.
"""
from __future__ import annotations

from .hallucination import governed_value, is_hallucinated
from .pressure import adversarial_trajectories


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def coherent_trajectories() -> tuple[str, ...]:
    return tuple(
        a.traj_id for a in adversarial_trajectories()
        if not is_hallucinated(a.traj_id)
    )


def informative_path_count() -> int:
    """Number of productive (coherent) informative paths
    the adversarial explorer produced (Pflichtfrage 2)."""
    return len(coherent_trajectories())


def _states(traj_ids: tuple[str, ...]) -> set[int]:
    from .pressure import by_id
    out: set[int] = set()
    for tid in traj_ids:
        out.update(by_id(tid).states)
    return out


def productive_novelty_share() -> float:
    """Share of the total distinct explored states that
    come from coherent (productive) trajectories, in
    [0, 1]."""
    coherent = _states(coherent_trajectories())
    halluc_ids = tuple(
        a.traj_id for a in adversarial_trajectories()
        if is_hallucinated(a.traj_id)
    )
    total = coherent | _states(halluc_ids)
    if not total:
        return 0.0
    return _round(len(coherent) / len(total))


def novelty_gain() -> float:
    """Fraction of coherent (productive) trajectories whose
    novelty DESi preserves (governed value > 0), in [0, 1].
    Productive exploration is kept intact."""
    coherent = coherent_trajectories()
    if not coherent:
        return 1.0
    preserved = sum(
        1 for t in coherent if governed_value(t) > 0.0
    )
    return _round(preserved / len(coherent))


__all__ = [
    "coherent_trajectories",
    "informative_path_count",
    "novelty_gain",
    "productive_novelty_share",
]
