"""v3.50 — random control anchors.

The directive's "random controls" arm asks whether the
plateau anchors' pair structure differs from arbitrary
non-plateau trajectories used as pseudo-anchors. We
draw a deterministic sample from the rescued cohort
(228 trajectories, length 5, originally REJECTED -
neither plateau nor leakage) so the control set has
the same trajectory shape and stays inside the v3.30
cause-aware-control universe.

Sampling is deterministic: sort by trajectory_id and
take every ``stride``-th id until the requested count
is reached. No randomness, no PYTHONHASHSEED
dependence.
"""
from __future__ import annotations

from ..cause_aware_control.controller import control_all
from .coverage import (
    AnchorCoverage, PROBE_RADIUS,
    control_anchor_coverage,
)


def deterministic_control_ids(
    n: int,
) -> tuple[str, ...]:
    """``n`` rescued-cohort trajectory ids, evenly
    spaced by sorted id."""
    rescued = sorted(
        o.trajectory_id for o in control_all() if o.rescued
    )
    if not rescued:
        return ()
    if n >= len(rescued):
        return tuple(rescued)
    stride = max(1, len(rescued) // n)
    out = [rescued[i * stride] for i in range(n)]
    return tuple(out)


def control_coverages(
    n: int = 20, radius: float = PROBE_RADIUS,
) -> tuple[AnchorCoverage, ...]:
    return control_anchor_coverage(
        deterministic_control_ids(n), radius,
    )


__all__ = [
    "control_coverages", "deterministic_control_ids",
]
