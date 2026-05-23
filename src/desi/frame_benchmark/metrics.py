"""FrameBenchmarkMetrics — Aufgabe 11 input."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from ..frames import FrameKind
from ..memory.claim import ClaimState
from .case import FrameCategory
from .runner import FrameBenchmarkRun


@dataclass(frozen=True)
class FrameBenchmarkMetrics:
    total: int
    frame_correct: int
    state_correct: int
    pipeline_correct: int
    fully_correct: int
    conflict_rate: float
    undeclared_rate: float
    pipeline_block_rate: float
    per_category_correct: dict[str, tuple[int, int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "frame_correct": self.frame_correct,
            "state_correct": self.state_correct,
            "pipeline_correct": self.pipeline_correct,
            "fully_correct": self.fully_correct,
            "conflict_rate": self.conflict_rate,
            "undeclared_rate": self.undeclared_rate,
            "pipeline_block_rate": self.pipeline_block_rate,
            "per_category_correct": {
                k: list(v) for k, v in self.per_category_correct.items()
            },
        }


def _ratio(num: int, den: int) -> float:
    return round(num / den, 6) if den > 0 else 0.0


def compute_frame_metrics(run: FrameBenchmarkRun) -> FrameBenchmarkMetrics:
    results = run.results
    total = len(results)
    frame_correct = sum(1 for r in results if r.frame_correct)
    state_correct = sum(1 for r in results if r.state_correct)
    pipeline_correct = sum(1 for r in results if r.pipeline_correct)
    fully_correct = sum(1 for r in results if r.correct)

    conflicts = sum(
        1 for r in results
        if r.actual_state is ClaimState.FRAME_CONFLICT
    )
    undeclared = sum(
        1 for r in results
        if r.actual_state is ClaimState.FRAME_UNDECLARED
    )

    # Pipeline block rate: cases whose declared frame is
    # FRAME_UNDECLARED (no pipeline permitted).
    blocked = sum(
        1 for r in results
        if r.declaration.frame_kind is FrameKind.FRAME_UNDECLARED
    )

    per_cat: dict[str, tuple[int, int]] = {}
    for cat in FrameCategory:
        in_cat = [r for r in results if r.case.category is cat]
        per_cat[cat.value] = (
            sum(1 for r in in_cat if r.correct),
            len(in_cat),
        )

    return FrameBenchmarkMetrics(
        total=total,
        frame_correct=frame_correct,
        state_correct=state_correct,
        pipeline_correct=pipeline_correct,
        fully_correct=fully_correct,
        conflict_rate=_ratio(conflicts, total),
        undeclared_rate=_ratio(undeclared, total),
        pipeline_block_rate=_ratio(blocked, total),
        per_category_correct=per_cat,
    )


__all__ = ["FrameBenchmarkMetrics", "compute_frame_metrics"]
