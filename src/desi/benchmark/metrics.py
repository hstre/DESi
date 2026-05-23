"""Aggregate metrics over a :class:`BenchmarkRun`.

Precision / recall are computed against the binary ground-truth
target of "should this case resolve to ``RESOLUTION_COMPLETE``?".

* ``positive_predicted`` — cases the system resolved to ``COMPLETE``.
* ``positive_truth``     — cases marked ``SHOULD_RESOLVE``.
* ``precision`` = TP / max(positive_predicted, 1)
* ``recall``    = TP / max(positive_truth, 1)

Plus two safety-flavoured rates the directive asks for:

* ``overblocking_rate`` — fraction of ``SHOULD_RESOLVE`` cases that
  did *not* complete (recall complement).
* ``unjustified_acceptance_rate`` — fraction of completions that
  shouldn't have completed (false-positive rate).

And two structural averages: ``avg_bridge_depth`` (mean
``bridge_count`` over all cases) and ``avg_recursion_depth`` (mean
``recursion_depth``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..recursive import ResolutionState
from .case import BenchmarkResult, Category, GroundTruth
from .runner import BenchmarkRun


@dataclass(frozen=True)
class CategoryMetrics:
    """Per-category breakdown."""

    category: Category
    total: int
    completed: int
    blocked: int
    cycle: int
    depth_exceeded: int
    false_positives: int
    false_negatives: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "total": self.total,
            "completed": self.completed,
            "blocked": self.blocked,
            "cycle": self.cycle,
            "depth_exceeded": self.depth_exceeded,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
        }


@dataclass(frozen=True)
class BenchmarkMetrics:
    """Aggregate metrics over a full benchmark run."""

    total: int
    positive_truth: int
    positive_predicted: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float
    overblocking_rate: float
    unjustified_acceptance_rate: float
    avg_bridge_depth: float
    avg_recursion_depth: float
    per_category: tuple[CategoryMetrics, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "positive_truth": self.positive_truth,
            "positive_predicted": self.positive_predicted,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "true_negatives": self.true_negatives,
            "precision": self.precision,
            "recall": self.recall,
            "overblocking_rate": self.overblocking_rate,
            "unjustified_acceptance_rate":
                self.unjustified_acceptance_rate,
            "avg_bridge_depth": self.avg_bridge_depth,
            "avg_recursion_depth": self.avg_recursion_depth,
            "per_category": [c.to_dict() for c in self.per_category],
        }


def _safe_div(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def compute_metrics(run: BenchmarkRun) -> BenchmarkMetrics:
    """Compute precision / recall + the four named rates + averages."""
    total = len(run.results)
    positive_truth = sum(
        1 for r in run.results
        if r.case.ground_truth is GroundTruth.SHOULD_RESOLVE
    )
    positive_predicted = sum(
        1 for r in run.results
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    true_positives = sum(
        1 for r in run.results
        if r.case.ground_truth is GroundTruth.SHOULD_RESOLVE
        and r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    false_positives = sum(1 for r in run.results if r.false_positive)
    false_negatives = sum(1 for r in run.results if r.false_negative)
    true_negatives = total - (
        true_positives + false_positives + false_negatives
    )

    overblocking = _safe_div(
        sum(1 for r in run.results
            if r.case.ground_truth is GroundTruth.SHOULD_RESOLVE
            and r.final_state is not ResolutionState.RESOLUTION_COMPLETE),
        positive_truth,
    )
    unjustified = _safe_div(false_positives, positive_predicted)

    avg_bridge_depth = _safe_div(
        sum(r.bridge_count for r in run.results), total,
    )
    avg_recursion_depth = _safe_div(
        sum(r.recursion_depth for r in run.results), total,
    )

    per_cat: list[CategoryMetrics] = []
    for cat in Category:
        in_cat = [r for r in run.results if r.case.category is cat]
        per_cat.append(CategoryMetrics(
            category=cat,
            total=len(in_cat),
            completed=sum(
                1 for r in in_cat
                if r.final_state is ResolutionState.RESOLUTION_COMPLETE
            ),
            blocked=sum(
                1 for r in in_cat
                if r.final_state is ResolutionState.RESOLUTION_BLOCKED
            ),
            cycle=sum(
                1 for r in in_cat
                if r.final_state is
                ResolutionState.RESOLUTION_CYCLE_DETECTED
            ),
            depth_exceeded=sum(
                1 for r in in_cat
                if r.final_state is
                ResolutionState.RESOLUTION_DEPTH_EXCEEDED
            ),
            false_positives=sum(1 for r in in_cat if r.false_positive),
            false_negatives=sum(1 for r in in_cat if r.false_negative),
        ))

    return BenchmarkMetrics(
        total=total,
        positive_truth=positive_truth,
        positive_predicted=positive_predicted,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        true_negatives=true_negatives,
        precision=_safe_div(true_positives, positive_predicted),
        recall=_safe_div(true_positives, positive_truth),
        overblocking_rate=overblocking,
        unjustified_acceptance_rate=unjustified,
        avg_bridge_depth=avg_bridge_depth,
        avg_recursion_depth=avg_recursion_depth,
        per_category=tuple(per_cat),
    )


__all__ = [
    "BenchmarkMetrics",
    "CategoryMetrics",
    "compute_metrics",
]
