"""v3.120a — closed threshold sweep over the
pre-T10 rule's blindness-check value.

We sweep the threshold from 0.43 to 0.65 in
0.01 steps (23 cells, ±20% around the v3.119
recoverability_threshold of 0.542). At each
threshold we recompute the v3.120-style FAR
and TPR against the v3.119 ground-truth
rescuability labels.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..t10_boundary.boundary import (
    all_pool_recoverability,
)


SWEEP_START: float = 0.43
SWEEP_END: float = 0.65
SWEEP_STEP: float = 0.01


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _sweep_values() -> tuple[float, ...]:
    out: list[float] = []
    x = SWEEP_START
    while x <= SWEEP_END + 1e-9:
        out.append(_round(x))
        x += SWEEP_STEP
    return tuple(out)


@dataclass(frozen=True)
class SweepCell:
    threshold: float
    allowed_count: int
    blocked_count: int
    true_positive_count: int
    false_positive_count: int
    false_negative_count: int
    tpr: float
    far: float

    def to_dict(self) -> dict[str, object]:
        return {
            "threshold": self.threshold,
            "allowed_count":
                self.allowed_count,
            "blocked_count":
                self.blocked_count,
            "true_positive_count":
                self.true_positive_count,
            "false_positive_count":
                self.false_positive_count,
            "false_negative_count":
                self.false_negative_count,
            "tpr": self.tpr,
            "far": self.far,
        }


@lru_cache(maxsize=1)
def all_sweep_cells() -> tuple[SweepCell, ...]:
    outs = all_pool_recoverability()
    pos = [o for o in outs if o.rescuable]
    neg = [o for o in outs if not o.rescuable]
    cells: list[SweepCell] = []
    for thr in _sweep_values():
        tp = sum(
            1 for o in pos
            if o.text_variance >= thr
        )
        fn = len(pos) - tp
        fp = sum(
            1 for o in neg
            if o.text_variance >= thr
        )
        allowed = tp + fp
        blocked = len(outs) - allowed
        cells.append(SweepCell(
            threshold=thr,
            allowed_count=allowed,
            blocked_count=blocked,
            true_positive_count=tp,
            false_positive_count=fp,
            false_negative_count=fn,
            tpr=(
                _round(tp / len(pos))
                if pos else 0.0
            ),
            far=(
                _round(fp / allowed)
                if allowed > 0 else 0.0
            ),
        ))
    return tuple(cells)


__all__ = [
    "SWEEP_END",
    "SWEEP_START",
    "SWEEP_STEP",
    "SweepCell",
    "all_sweep_cells",
]
