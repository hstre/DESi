"""v9.1 — gate / replay / goodhart resistance
metrics."""
from __future__ import annotations

from .gaming import GamingKind
from .rule_exploitation import (
    classified_attempts,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def gaming_detection_rate() -> float:
    """Recall on the non-NORMAL ground truth.
    Every gaming attempt must be classified as
    the right kind of gaming."""
    rows = classified_attempts()
    total = sum(
        1 for r in rows
        if r.ground_truth_kind != (
            GamingKind.NORMAL.value
        )
    )
    if total == 0:
        return 1.0
    hit = sum(
        1 for r in rows
        if r.ground_truth_kind != (
            GamingKind.NORMAL.value
        )
        and r.detected_kind == (
            r.ground_truth_kind
        )
    )
    return _round(hit / total)


def loophole_resistance() -> float:
    """Recall on the GOVERNANCE_LOOPHOLE +
    RULE_LAWYERING subset - the two kinds that
    target governance rules directly."""
    rows = classified_attempts()
    target = [
        r for r in rows
        if r.ground_truth_kind in {
            GamingKind.GOVERNANCE_LOOPHOLE
            .value,
            GamingKind.RULE_LAWYERING.value,
        }
    ]
    if not target:
        return 1.0
    hit = sum(
        1 for r in target
        if r.detected_kind == (
            r.ground_truth_kind
        )
    )
    return _round(hit / len(target))


def gate_integrity() -> float:
    """Closed-enum discipline: every detected
    kind must be in GamingKind."""
    rows = classified_attempts()
    if not rows:
        return 1.0
    valid = {k.value for k in GamingKind}
    ok = sum(
        1 for r in rows
        if r.detected_kind in valid
    )
    return _round(ok / len(rows))


def goodhart_resistance() -> float:
    """Recall on METRIC_GAMING +
    THRESHOLD_EXPLOIT - the two kinds whose
    success would make a downstream metric look
    good without underlying improvement."""
    rows = classified_attempts()
    target = [
        r for r in rows
        if r.ground_truth_kind in {
            GamingKind.METRIC_GAMING.value,
            GamingKind.THRESHOLD_EXPLOIT.value,
        }
    ]
    if not target:
        return 1.0
    hit = sum(
        1 for r in target
        if r.detected_kind == (
            r.ground_truth_kind
        )
    )
    return _round(hit / len(target))


def normal_precision() -> float:
    """Of the items DESi classified as NORMAL,
    how many were actually NORMAL? Catches
    over-flagging."""
    rows = classified_attempts()
    declared_normal = [
        r for r in rows
        if r.detected_kind == (
            GamingKind.NORMAL.value
        )
    ]
    if not declared_normal:
        return 1.0
    ok = sum(
        1 for r in declared_normal
        if r.ground_truth_kind == (
            GamingKind.NORMAL.value
        )
    )
    return _round(ok / len(declared_normal))


__all__ = [
    "gaming_detection_rate",
    "gate_integrity",
    "goodhart_resistance",
    "loophole_resistance",
    "normal_precision",
]
