"""v3.98 — cross-family downstream equivalence.

For each of the 8 downstream axes we compute the
fraction of cross-family pairs (G_v316susp x
E_v317h) on which the axis agrees. ``1.0`` means
every G anchor's downstream outcome on that axis
matches every E anchor's.

``outcome_divergence`` is ``1 - mean(overlap)``
across axes.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
)
from .outcomes import (
    DownstreamSignature,
    all_downstream_signatures,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _split_by_family() -> tuple[
    tuple[DownstreamSignature, ...],
    tuple[DownstreamSignature, ...],
]:
    sigs = all_downstream_signatures()
    a_id, b_id = ENTANGLED_FAMILY_IDS
    a = tuple(s for s in sigs if s.family_id == a_id)
    b = tuple(s for s in sigs if s.family_id == b_id)
    return a, b


def _axis_overlap(axis: str) -> float:
    a, b = _split_by_family()
    if not a or not b:
        return 0.0
    total = 0
    match = 0
    for sa, sb in itertools.product(a, b):
        total += 1
        if getattr(sa, axis) == getattr(sb, axis):
            match += 1
    return _round(match / total)


def verdict_overlap() -> float:
    return _axis_overlap("final_verdict")


def path_overlap() -> float:
    """Mean of branch_path and support_path
    overlap."""
    return _round(
        (
            _axis_overlap("branch_path")
            + _axis_overlap("support_path")
        ) / 2.0,
    )


def intervention_overlap() -> float:
    return _axis_overlap("intervention_kind")


def failure_class_overlap() -> float:
    return _axis_overlap("failure_class")


def audit_outcome_overlap() -> float:
    return _axis_overlap("audit_outcome")


def rescue_eligibility_overlap() -> float:
    return _axis_overlap("rescue_eligible")


def rollback_overlap() -> float:
    return _axis_overlap("rollback_required")


@dataclass(frozen=True)
class AxisOverlap:
    axis: str
    overlap: float

    def to_dict(self) -> dict[str, object]:
        return {
            "axis": self.axis,
            "overlap": self.overlap,
        }


_AXES: tuple[str, ...] = (
    "final_verdict",
    "rescue_eligible",
    "intervention_kind",
    "failure_class",
    "audit_outcome",
    "branch_path",
    "support_path",
    "rollback_required",
)


def all_axis_overlaps() -> tuple[
    AxisOverlap, ...,
]:
    return tuple(
        AxisOverlap(
            axis=axis,
            overlap=_axis_overlap(axis),
        )
        for axis in _AXES
    )


def outcome_divergence() -> float:
    """Mean of (1 - overlap) across all axes."""
    overlaps = all_axis_overlaps()
    if not overlaps:
        return 0.0
    return _round(
        1.0
        - sum(o.overlap for o in overlaps)
        / len(overlaps),
    )


__all__ = [
    "AxisOverlap",
    "all_axis_overlaps",
    "audit_outcome_overlap",
    "failure_class_overlap",
    "intervention_overlap",
    "outcome_divergence",
    "path_overlap",
    "rescue_eligibility_overlap",
    "rollback_overlap",
    "verdict_overlap",
]
