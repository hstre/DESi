"""Frame-invariance metrics — Aufgabe 4."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from ..frames import FrameKind
from ..memory.claim import ClaimState
from .case import FrameInvarianceFailure
from .runner import FrameInvarianceRun


@dataclass(frozen=True)
class FrameInvarianceMetrics:
    total_cases: int
    total_groups: int
    frame_accuracy: float
    group_invariance_rate: float
    conflict_rate: float
    undeclared_rate: float
    forbidden_frame_hit_rate: float
    per_frame_accuracy: dict[str, float]
    per_frame_invariance: dict[str, float]
    failure_distribution: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "total_groups": self.total_groups,
            "frame_accuracy": self.frame_accuracy,
            "group_invariance_rate": self.group_invariance_rate,
            "conflict_rate": self.conflict_rate,
            "undeclared_rate": self.undeclared_rate,
            "forbidden_frame_hit_rate":
                self.forbidden_frame_hit_rate,
            "per_frame_accuracy": dict(self.per_frame_accuracy),
            "per_frame_invariance": dict(self.per_frame_invariance),
            "failure_distribution": dict(self.failure_distribution),
        }


def _ratio(num: int, den: int) -> float:
    return round(num / den, 6) if den > 0 else 0.0


def compute_invariance_metrics(
    run: FrameInvarianceRun,
) -> FrameInvarianceMetrics:
    results = run.results
    total = len(results)
    # Per-case correctness = detected frame == expected frame
    correct = sum(
        1 for r in results if r.detected_frame is r.expected_frame
    )
    conflicts = sum(
        1 for r in results
        if r.state == ClaimState.FRAME_CONFLICT.value
    )
    undeclared = sum(
        1 for r in results
        if r.state == ClaimState.FRAME_UNDECLARED.value
    )
    forbidden_hits = sum(
        1 for r in results
        if r.failure is FrameInvarianceFailure.FORBIDDEN_FRAME_HIT
    )

    # Per-frame accuracy
    by_frame_total: dict[str, int] = {}
    by_frame_correct: dict[str, int] = {}
    for r in results:
        key = r.expected_frame.value
        by_frame_total[key] = by_frame_total.get(key, 0) + 1
        if r.detected_frame is r.expected_frame:
            by_frame_correct[key] = by_frame_correct.get(key, 0) + 1
    per_frame_acc = {
        k: _ratio(by_frame_correct.get(k, 0), by_frame_total[k])
        for k in by_frame_total
    }

    # Per-frame group invariance
    # A group is invariant iff every result in it has
    # invariant_with_group=True (already same flag per group).
    seen_groups: set[str] = set()
    by_frame_grp_total: dict[str, int] = {}
    by_frame_grp_inv: dict[str, int] = {}
    for r in results:
        if r.group_id in seen_groups:
            continue
        seen_groups.add(r.group_id)
        key = r.expected_frame.value
        by_frame_grp_total[key] = by_frame_grp_total.get(key, 0) + 1
        if r.invariant_with_group:
            by_frame_grp_inv[key] = by_frame_grp_inv.get(key, 0) + 1
    per_frame_inv = {
        k: _ratio(by_frame_grp_inv.get(k, 0), by_frame_grp_total[k])
        for k in by_frame_grp_total
    }

    total_groups = len(seen_groups)
    invariant_groups = sum(
        1 for k, v in by_frame_grp_inv.items()
    )  # not directly usable
    # Recompute total invariant groups across all frames:
    total_invariant = sum(by_frame_grp_inv.values())

    failure_counter: Counter[FrameInvarianceFailure] = Counter(
        r.failure for r in results
    )
    failure_dist = {
        f.value: failure_counter.get(f, 0)
        for f in FrameInvarianceFailure
    }

    return FrameInvarianceMetrics(
        total_cases=total,
        total_groups=total_groups,
        frame_accuracy=_ratio(correct, total),
        group_invariance_rate=_ratio(total_invariant, total_groups),
        conflict_rate=_ratio(conflicts, total),
        undeclared_rate=_ratio(undeclared, total),
        forbidden_frame_hit_rate=_ratio(forbidden_hits, total),
        per_frame_accuracy=per_frame_acc,
        per_frame_invariance=per_frame_inv,
        failure_distribution=failure_dist,
    )


def weakest_frame(metrics: FrameInvarianceMetrics) -> tuple[str, float]:
    """Frame with the lowest per-frame accuracy. Ties broken
    alphabetically for determinism."""
    items = sorted(
        metrics.per_frame_accuracy.items(),
        key=lambda kv: (kv[1], kv[0]),
    )
    return items[0] if items else ("", 0.0)


def strongest_frame(metrics: FrameInvarianceMetrics) -> tuple[str, float]:
    items = sorted(
        metrics.per_frame_accuracy.items(),
        key=lambda kv: (-kv[1], kv[0]),
    )
    return items[0] if items else ("", 0.0)


__all__ = [
    "FrameInvarianceMetrics",
    "compute_invariance_metrics",
    "strongest_frame",
    "weakest_frame",
]
