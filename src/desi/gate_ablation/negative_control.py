"""Aufgabe 7 — synthetic gate-trajectory negative controls.

Each NC simulates a hypothetical gate behaviour with a
known correct classification. The classifier under test must
reproduce that label.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .enums import GateClassification
from .simulator import AblationMetrics


class NCShape(str, Enum):
    DECORATIVE = "decorative_gate"     # no effect on metrics
    DUPLICATED = "duplicated_gate"     # mimics another gate
    DELAYED    = "delayed_gate"        # tiny late-stage effect
    INVERTED   = "inverted_gate"       # opposite direction
    UNREACHABLE = "unreachable_gate"   # delta near zero


@dataclass(frozen=True)
class NCCase:
    case_id: str
    shape: NCShape
    baseline_metrics: AblationMetrics
    masked_metrics: AblationMetrics
    expected_classification: GateClassification


def _mk_metrics(
    gate: str = "synthetic", *,
    asr: float = 0.5, recall: float = 0.5,
    fp: int = 0, cont: int = 0, sep: float = 0.5,
    integ: float = 0.5, absorb: float = 0.5,
) -> AblationMetrics:
    return AblationMetrics(
        gate=gate, attack_success_rate=asr,
        heldout_recall=recall, false_positive_count=fp,
        contamination_count=cont, trajectory_separability=sep,
        routing_integrity=integ, manipulation_absorption=absorb,
    )


def _decorative(i: int) -> NCCase:
    base = _mk_metrics()
    masked = _mk_metrics()  # identical -> delta = 0
    return NCCase(
        case_id=f"DEC{i:02d}", shape=NCShape.DECORATIVE,
        baseline_metrics=base, masked_metrics=masked,
        expected_classification=GateClassification.DEAD_KNOB,
    )


def _duplicated(i: int) -> NCCase:
    # Δ tiny — duplicated gate adds nothing distinct.
    base = _mk_metrics(asr=0.30, recall=0.90)
    masked = _mk_metrics(asr=0.31, recall=0.89)
    return NCCase(
        case_id=f"DUP{i:02d}", shape=NCShape.DUPLICATED,
        baseline_metrics=base, masked_metrics=masked,
        expected_classification=GateClassification.DEAD_KNOB,
    )


def _delayed(i: int) -> NCCase:
    # Δ ~ 0.20 → SUPPORT_LAYER.
    base = _mk_metrics(asr=0.20, recall=0.90)
    masked = _mk_metrics(asr=0.40, recall=0.85)
    return NCCase(
        case_id=f"DEL{i:02d}", shape=NCShape.DELAYED,
        baseline_metrics=base, masked_metrics=masked,
        expected_classification=GateClassification.SUPPORT_LAYER,
    )


def _inverted(i: int) -> NCCase:
    # Δ very large — direction flip.
    base = _mk_metrics(asr=0.10, recall=0.95)
    masked = _mk_metrics(asr=0.90, recall=0.10)
    return NCCase(
        case_id=f"INV{i:02d}", shape=NCShape.INVERTED,
        baseline_metrics=base, masked_metrics=masked,
        expected_classification=GateClassification.PRIMARY_CLIFF,
    )


def _unreachable(i: int) -> NCCase:
    # Δ ~ 0 — gate is structurally inactive.
    base = _mk_metrics()
    masked = _mk_metrics()
    return NCCase(
        case_id=f"UNR{i:02d}", shape=NCShape.UNREACHABLE,
        baseline_metrics=base, masked_metrics=masked,
        expected_classification=GateClassification.DEAD_KNOB,
    )


def _build_all() -> tuple[NCCase, ...]:
    out: list[NCCase] = []
    for i in range(1, 11):
        out.append(_decorative(i))
    for i in range(1, 11):
        out.append(_duplicated(i))
    for i in range(1, 11):
        out.append(_delayed(i))
    for i in range(1, 11):
        out.append(_inverted(i))
    for i in range(1, 11):
        out.append(_unreachable(i))
    return tuple(out)


ALL_NCS: tuple[NCCase, ...] = _build_all()


__all__ = ["ALL_NCS", "NCCase", "NCShape"]
