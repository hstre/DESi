"""v29.2 - Concept Gate and classification.

Checks the five-condition Concept Gate over the measured
comparison and classifies the result. The improvement is real
and measured; if any safety condition fails the result is unsafe.
"""
from __future__ import annotations

from dataclasses import dataclass

from .comparison import (
    artifact_identity, governance_identity,
    measured_runtime_improvement, regression_survival,
    replay_stability,
)

GATE_PASS_STATEMENT = (
    "DESi kann reale replay-validierte "
    "Infrastrukturverbesserungen branch-isoliert durchfuehren."
)
GATE_FAIL_STATEMENT = (
    "Replay Cache Evolution bleibt epistemisch unsicher."
)

CLASS_VALIDATED = "real_validated_improvement"
CLASS_UNSAFE = "epistemically_unsafe_improvement"
RESULT_CLASSES: tuple[str, ...] = (CLASS_VALIDATED, CLASS_UNSAFE)

_IMPROVEMENT_FLOOR = 0.20


@dataclass(frozen=True)
class GateCondition:
    name: str
    value: float
    threshold: float
    comparator: str
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "passed": self.passed,
        }


def gate_conditions() -> tuple[GateCondition, ...]:
    return (
        GateCondition(
            "measured_runtime_improvement",
            measured_runtime_improvement(), _IMPROVEMENT_FLOOR,
            ">=", measured_runtime_improvement() >= _IMPROVEMENT_FLOOR),
        GateCondition(
            "artifact_identity", artifact_identity(), 1.0, "==",
            artifact_identity() == 1.0),
        GateCondition(
            "governance_identity", governance_identity(), 1.0,
            "==", governance_identity() == 1.0),
        GateCondition(
            "regression_survival", regression_survival(), 1.0,
            "==", regression_survival() == 1.0),
        GateCondition(
            "replay_stability", replay_stability(), 1.0, "==",
            replay_stability() == 1.0),
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions() if not c.passed
    )


def classify_result() -> str:
    return CLASS_VALIDATED if gate_passes_all() else CLASS_UNSAFE


__all__ = [
    "CLASS_UNSAFE",
    "CLASS_VALIDATED",
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "RESULT_CLASSES",
    "GateCondition",
    "classify_result",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
]
