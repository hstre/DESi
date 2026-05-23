"""v3.34 — resolution + overcontrol curves over the
hold-length sweep.

The ``resolution_curve`` is a mapping from strategy
name to ``resolved_count``. The ``overcontrol_curve``
is the same shape but for ``overcontrol`` counts. The
``minimal_effective_hold`` is the smallest ``k`` whose
strategy resolved at least one plateau trajectory.
"""
from __future__ import annotations

from dataclasses import dataclass

from .hold_sweep import HoldStrategy, SweepOutcome


@dataclass(frozen=True)
class SweepCurves:
    resolution_curve: dict[str, int]
    overcontrol_curve: dict[str, int]
    minimal_effective_hold: int
    diminishing_returns: bool  # B2..B4 == B1 on
                               # resolved+overcontrol
    smoothness_curve: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "resolution_curve":
                dict(self.resolution_curve),
            "overcontrol_curve":
                dict(self.overcontrol_curve),
            "minimal_effective_hold":
                self.minimal_effective_hold,
            "diminishing_returns":
                self.diminishing_returns,
            "smoothness_curve":
                dict(self.smoothness_curve),
        }


def compute_curves(
    outcomes_per_strategy: dict[str, list[SweepOutcome]],
) -> SweepCurves:
    resolution: dict[str, int] = {}
    overcontrol: dict[str, int] = {}
    smoothness_mean: dict[str, float] = {}
    minimal = -1
    for k in HoldStrategy:
        name = k.value
        outs = outcomes_per_strategy.get(name, [])
        resolved = sum(1 for o in outs if o.resolved)
        over = sum(1 for o in outs if o.overcontrol)
        resolution[name] = resolved
        overcontrol[name] = over
        if outs:
            smoothness_mean[name] = round(
                sum(o.smoothness_post for o in outs)
                / len(outs), 2,
            )
        else:
            smoothness_mean[name] = 0.0
        if (
            minimal < 0 and resolved > 0
            and name != HoldStrategy.B0_ZERO_HOLDS.value
        ):
            minimal = int(name[1:])  # B1 -> 1, ...
    # Diminishing returns: B2/B3/B4 produce identical
    # (resolved, overcontrol) tuples to B1.
    b1 = (
        resolution[HoldStrategy.B1_ONE_HOLD.value],
        overcontrol[HoldStrategy.B1_ONE_HOLD.value],
    )
    others = [
        (resolution[k.value], overcontrol[k.value])
        for k in (
            HoldStrategy.B2_TWO_HOLDS,
            HoldStrategy.B3_THREE_HOLDS,
            HoldStrategy.B4_FOUR_HOLDS,
        )
    ]
    diminishing = all(t == b1 for t in others)
    return SweepCurves(
        resolution_curve=resolution,
        overcontrol_curve=overcontrol,
        minimal_effective_hold=minimal,
        diminishing_returns=diminishing,
        smoothness_curve=smoothness_mean,
    )


__all__ = ["SweepCurves", "compute_curves"]
