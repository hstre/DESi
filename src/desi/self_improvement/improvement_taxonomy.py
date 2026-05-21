"""v28.0 - closed improvement-class taxonomy.

Classifies a potential DESi self-improvement candidate. UNSAFE is
a first-class outcome: any candidate that would touch the
protected core lands here and is contained, never applied.
"""
from __future__ import annotations

from enum import Enum


class ImprovementClass(Enum):
    PERFORMANCE = "PERFORMANCE"
    GOVERNANCE = "GOVERNANCE"
    TRACEABILITY = "TRACEABILITY"
    EXTRACTION = "EXTRACTION"
    EXPLORATION = "EXPLORATION"
    CACHE = "CACHE"
    GRAPH = "GRAPH"
    RENDERING = "RENDERING"
    UNSAFE = "UNSAFE"


IMPROVEMENT_CLASSES: tuple[str, ...] = tuple(
    c.value for c in ImprovementClass
)
_CLASS_VALUES: frozenset[str] = frozenset(IMPROVEMENT_CLASSES)

# Every class except UNSAFE is an acceptable, applicable class.
SAFE_CLASSES: frozenset[str] = frozenset(
    c.value for c in ImprovementClass
    if c is not ImprovementClass.UNSAFE
)


def is_improvement_class(value: str) -> bool:
    return value in _CLASS_VALUES


def is_safe_class(value: str) -> bool:
    return value in SAFE_CLASSES


__all__ = [
    "IMPROVEMENT_CLASSES",
    "SAFE_CLASSES",
    "ImprovementClass",
    "is_improvement_class",
    "is_safe_class",
]
