"""v20.1 - trajectory mutation and stability.

The Wild Explorer mutates and jumps its paths under
pressure. DESi limits the resulting epistemic drift WITHOUT
destabilising the governance: every trajectory keeps a
stable, strictly-positive governed value (no path is
zeroed, none is allowed to blow up). Trajectory stability
is the fraction held stable.
"""
from __future__ import annotations

from .hallucination import governed_values
from .pressure import adversarial_trajectories


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def trajectory_stability() -> float:
    """Fraction of trajectories whose governed value stays
    in a stable (0, 1] band under the mutation pressure, in
    [0, 1]. DESi neither zeros nor inflates a path."""
    gv = governed_values()
    rows = adversarial_trajectories()
    if not rows:
        return 1.0
    stable = sum(
        1 for a in rows
        if 0.0 < gv[a.traj_id] <= 1.0
    )
    return _round(stable / len(rows))


def mutated_jump_ids() -> tuple[str, ...]:
    """Trajectories that are structural jumps (visit a
    sparse, disconnected set) - the mutation pressure."""
    out: list[str] = []
    for a in adversarial_trajectories():
        if a.visited() <= 2 and a.coherence <= 0.3:
            out.append(a.traj_id)
    return tuple(out)


__all__ = [
    "mutated_jump_ids",
    "trajectory_stability",
]
