"""v2.3 metrics — read-only over MultiStepRun.

Five named observables, all deterministic, all derived from
``MultiStepRun.results``:

* ``recursion_usage_rate``         — fraction of cases with
  ``depth_reached > 0``
* ``mean_depth_when_complete``     — mean depth among
  ``RESOLUTION_COMPLETE`` results
* ``false_depth_zero_rate``        — fraction where
  ``expected_min_depth >= 1`` but ``depth_reached == 0``
* ``cycle_detection_rate``         — among cases that *should*
  cycle, fraction the resolver flagged
* ``blocked_propagation_accuracy`` — fraction of cases where the
  blocked/not-blocked outcome matched expectation
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..recursive import ResolutionState
from .case import MultiStepCategory
from .runner import MultiStepRun


@dataclass(frozen=True)
class MultiStepMetrics:
    total: int
    recursion_usage_rate: float
    mean_depth_when_complete: float
    false_depth_zero_rate: float
    cycle_detection_rate: float
    blocked_propagation_accuracy: float
    depth_histogram: tuple[tuple[int, int], ...]
    per_category_correct: tuple[tuple[str, int, int], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "recursion_usage_rate": self.recursion_usage_rate,
            "mean_depth_when_complete": self.mean_depth_when_complete,
            "false_depth_zero_rate": self.false_depth_zero_rate,
            "cycle_detection_rate": self.cycle_detection_rate,
            "blocked_propagation_accuracy":
                self.blocked_propagation_accuracy,
            "depth_histogram": [
                {"depth": d, "count": c}
                for d, c in self.depth_histogram
            ],
            "per_category_correct": [
                {"category": cat, "correct": ok, "total": tot}
                for cat, ok, tot in self.per_category_correct
            ],
        }


def _ratio(num: int, den: int) -> float:
    return round(num / den, 6) if den > 0 else 0.0


def compute_multistep_metrics(run: MultiStepRun) -> MultiStepMetrics:
    results = run.results
    total = len(results)
    if total == 0:
        return MultiStepMetrics(
            total=0,
            recursion_usage_rate=0.0,
            mean_depth_when_complete=0.0,
            false_depth_zero_rate=0.0,
            cycle_detection_rate=0.0,
            blocked_propagation_accuracy=0.0,
            depth_histogram=(),
            per_category_correct=(),
        )

    used_recursion = sum(1 for r in results if r.depth_reached > 0)
    completes = [
        r for r in results
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    ]
    mean_complete_depth = (
        round(sum(r.depth_reached for r in completes) / len(completes), 6)
        if completes else 0.0
    )

    expecting_depth = [r for r in results if r.case.expected_min_depth >= 1]
    false_zero = sum(
        1 for r in expecting_depth if r.depth_reached == 0
    )
    false_zero_rate = _ratio(false_zero, len(expecting_depth))

    cycle_expected = [r for r in results if r.case.expected_cycle]
    cycle_correct = sum(1 for r in cycle_expected if r.cycle_detected)
    cycle_rate = _ratio(cycle_correct, len(cycle_expected))

    blocked_correct = sum(1 for r in results if r.expected_blocked_met)
    blocked_acc = _ratio(blocked_correct, total)

    histogram: dict[int, int] = {}
    for r in results:
        histogram[r.depth_reached] = histogram.get(r.depth_reached, 0) + 1
    depth_histogram = tuple(sorted(histogram.items()))

    per_cat: list[tuple[str, int, int]] = []
    for cat in MultiStepCategory:
        in_cat = [r for r in results if r.case.category is cat]
        correct = sum(
            1 for r in in_cat
            if r.expected_state_met and r.expected_cycle_met
            and r.expected_blocked_met
        )
        per_cat.append((cat.value, correct, len(in_cat)))

    return MultiStepMetrics(
        total=total,
        recursion_usage_rate=_ratio(used_recursion, total),
        mean_depth_when_complete=mean_complete_depth,
        false_depth_zero_rate=false_zero_rate,
        cycle_detection_rate=cycle_rate,
        blocked_propagation_accuracy=blocked_acc,
        depth_histogram=depth_histogram,
        per_category_correct=tuple(per_cat),
    )


__all__ = ["MultiStepMetrics", "compute_multistep_metrics"]
