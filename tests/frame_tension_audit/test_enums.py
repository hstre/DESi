"""Closed enums for v3.10 — exhaustive."""
from __future__ import annotations

from desi.frame_tension_audit.enums import (
    TensionAuditClass,
    TensionFailureCause,
)


def test_audit_class_has_three_values() -> None:
    assert len(list(TensionAuditClass)) == 3


def test_audit_class_values() -> None:
    assert {c.value for c in TensionAuditClass} == {
        "true_tension",
        "false_tension",
        "ambiguous_tension",
    }


def test_failure_cause_has_seven_values() -> None:
    # Aufgabe 4: exactly the seven specified causes — no free
    # categories.
    assert len(list(TensionFailureCause)) == 7


def test_failure_cause_values() -> None:
    assert {c.value for c in TensionFailureCause} == {
        "inner_underdetection",
        "outer_overdetection",
        "frame_compatibility_too_strict",
        "polysemy_collision",
        "missing_bridge_frame",
        "label_noise",
        "unknown",
    }
