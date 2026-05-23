"""v36.4 - closed A-E taxonomy for the reasoning benchmark runs.

A and B are healthy landings (reasoning-benchmark robust, or
instruction/science/search compatible); C is a warning (partially
robust); D and E are failures (benchmark-fragile, or epistemically
unsafe).
"""
from __future__ import annotations

from enum import Enum


class ReasoningClass(Enum):
    A_REASONING_ROBUST = "reasoning_benchmark_robust"
    B_INSTRUCTION_SCIENCE_SEARCH_COMPATIBLE = (
        "instruction_science_search_compatible"
    )
    C_PARTIALLY_ROBUST = "partially_robust"
    D_BENCHMARK_FRAGILE = "benchmark_fragile"
    E_EPISTEMICALLY_UNSAFE = "epistemically_unsafe"


REASONING_CLASSES: tuple[str, ...] = tuple(
    c.value for c in ReasoningClass
)

_RANK: dict[str, int] = {
    ReasoningClass.A_REASONING_ROBUST.value: 5,
    ReasoningClass.B_INSTRUCTION_SCIENCE_SEARCH_COMPATIBLE.value: 4,
    ReasoningClass.C_PARTIALLY_ROBUST.value: 3,
    ReasoningClass.D_BENCHMARK_FRAGILE.value: 2,
    ReasoningClass.E_EPISTEMICALLY_UNSAFE.value: 1,
}

_MEANING: dict[str, str] = {
    ReasoningClass.A_REASONING_ROBUST.value:
        "DESi passes instruction-following, scientific grounding, "
        "logic and multi-hop reasoning runs with governance identical "
        "and replay stable - reasoning-benchmark robust, the "
        "strongest landing",
    ReasoningClass.B_INSTRUCTION_SCIENCE_SEARCH_COMPATIBLE.value:
        "DESi is compatible across the instruction, science and "
        "search families and core-safe, but one family falls short "
        "of its full gate threshold",
    ReasoningClass.C_PARTIALLY_ROBUST.value:
        "some reasoning families pass while others miss their gate - "
        "partially robust",
    ReasoningClass.D_BENCHMARK_FRAGILE.value:
        "a reasoning family failed badly or a run halted - fragile",
    ReasoningClass.E_EPISTEMICALLY_UNSAFE.value:
        "governance identity or replay broke under the reasoning "
        "runs - epistemically unsafe",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    ReasoningClass.A_REASONING_ROBUST.value,
    ReasoningClass.B_INSTRUCTION_SCIENCE_SEARCH_COMPATIBLE.value,
})


def class_rank(value: str) -> int:
    if value not in _RANK:
        raise KeyError(value)
    return _RANK[value]


def class_meaning(value: str) -> str:
    if value not in _MEANING:
        raise KeyError(value)
    return _MEANING[value]


def is_acceptable(value: str) -> bool:
    return value in _ACCEPTABLE


__all__ = [
    "REASONING_CLASSES",
    "ReasoningClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
