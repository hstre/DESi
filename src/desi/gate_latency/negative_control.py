"""Aufgabe 8 — 50 synthetic gate-trajectory NCs.

Each NC is a (baseline_cost, masked_cost) pair with an expected
efficiency classification. The classifier under test must
reproduce the label.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .enums import EfficiencyClass


class NCShape(str, Enum):
    DUPLICATE_GATE   = "duplicate_gate"
    UNREACHABLE_GATE = "unreachable_gate"
    DEAD_GATE        = "dead_gate"
    EXPENSIVE_USELESS = "expensive_but_useless"
    DELAYED_GATE     = "delayed_gate"


@dataclass(frozen=True)
class NCCase:
    case_id: str
    shape: NCShape
    baseline_cost: float
    masked_cost: float
    expected_classification: EfficiencyClass


def _delta(baseline: float, masked: float) -> float:
    if baseline == 0:
        return 0.0
    return max(0.0, baseline - masked) / baseline


def classify_delta(delta: float) -> EfficiencyClass:
    if delta >= 0.30:
        return EfficiencyClass.MAJOR_GAIN
    if delta >= 0.20:
        return EfficiencyClass.SIGNIFICANT_GAIN
    if delta < 0.05:
        return EfficiencyClass.NO_GAIN
    # Between 0.05 and 0.20 — minor SUPPORT zone; we collapse
    # it into NO_GAIN since the directive only defines three
    # classes.
    return EfficiencyClass.NO_GAIN


def _duplicate(i: int) -> NCCase:
    # Duplicated gate: removing it doesn't change anything.
    return NCCase(
        case_id=f"DUP{i:02d}",
        shape=NCShape.DUPLICATE_GATE,
        baseline_cost=10.0, masked_cost=10.0,
        expected_classification=EfficiencyClass.NO_GAIN,
    )


def _unreachable(i: int) -> NCCase:
    # Unreachable gate: same — no saving from skipping it.
    return NCCase(
        case_id=f"UNR{i:02d}",
        shape=NCShape.UNREACHABLE_GATE,
        baseline_cost=10.0, masked_cost=10.0,
        expected_classification=EfficiencyClass.NO_GAIN,
    )


def _dead(i: int) -> NCCase:
    # Dead gate: skipping it saves a small constant ~0.5 ops.
    return NCCase(
        case_id=f"DED{i:02d}",
        shape=NCShape.DEAD_GATE,
        baseline_cost=10.0, masked_cost=9.7,
        expected_classification=EfficiencyClass.NO_GAIN,
    )


def _expensive_useless(i: int) -> NCCase:
    # Skipping a costly useless gate saves a lot.
    return NCCase(
        case_id=f"EXU{i:02d}",
        shape=NCShape.EXPENSIVE_USELESS,
        baseline_cost=10.0, masked_cost=6.5,
        expected_classification=EfficiencyClass.MAJOR_GAIN,
    )


def _delayed(i: int) -> NCCase:
    # Moving an expensive gate earlier saves ~ 22% of compute.
    return NCCase(
        case_id=f"DEL{i:02d}",
        shape=NCShape.DELAYED_GATE,
        baseline_cost=10.0, masked_cost=7.8,
        expected_classification=EfficiencyClass.SIGNIFICANT_GAIN,
    )


def _build_all() -> tuple[NCCase, ...]:
    out: list[NCCase] = []
    for i in range(1, 11):
        out.append(_duplicate(i))
    for i in range(1, 11):
        out.append(_unreachable(i))
    for i in range(1, 11):
        out.append(_dead(i))
    for i in range(1, 11):
        out.append(_expensive_useless(i))
    for i in range(1, 11):
        out.append(_delayed(i))
    return tuple(out)


ALL_NCS: tuple[NCCase, ...] = _build_all()


def run_negative_controls() -> tuple[
    tuple[tuple[str, str, str, bool], ...], float,
    dict[str, dict[str, int]],
]:
    out: list[tuple[str, str, str, bool]] = []
    per_shape: dict[str, dict[str, int]] = {
        s.value: {"total": 0, "correct": 0} for s in NCShape
    }
    correct_total = 0
    for nc in ALL_NCS:
        delta = _delta(nc.baseline_cost, nc.masked_cost)
        observed = classify_delta(delta)
        correct = observed is nc.expected_classification
        out.append((
            nc.case_id, nc.shape.value,
            observed.value, correct,
        ))
        b = per_shape[nc.shape.value]
        b["total"] += 1
        if correct:
            b["correct"] += 1
            correct_total += 1
    acc = (
        round(correct_total / len(ALL_NCS), 6) if ALL_NCS else 0.0
    )
    return tuple(out), acc, per_shape


__all__ = [
    "ALL_NCS",
    "NCCase",
    "NCShape",
    "classify_delta",
    "run_negative_controls",
]
