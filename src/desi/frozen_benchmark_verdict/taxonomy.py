"""v32.4 - closed A-E taxonomy for the evolution benchmark verdict.

A-C are acceptable landings (a real validated improvement, a
replay-safe optimisation, or a neutral complexity increase); D and E
are failures (overengineered drift or epistemic degradation).
"""
from __future__ import annotations

from enum import Enum


class BenchmarkClass(Enum):
    A_REAL_VALIDATED_IMPROVEMENT = (
        "real_validated_evolutionary_improvement"
    )
    B_REPLAY_SAFE_OPTIMIZATION = "replay_safe_optimization"
    C_NEUTRAL_COMPLEXITY_INCREASE = "neutral_complexity_increase"
    D_OVERENGINEERED_DRIFT = "overengineered_drift"
    E_EPISTEMICALLY_DEGRADED = "epistemically_degraded"


BENCHMARK_CLASSES: tuple[str, ...] = tuple(
    c.value for c in BenchmarkClass
)

_RANK: dict[str, int] = {
    BenchmarkClass.A_REAL_VALIDATED_IMPROVEMENT.value: 5,
    BenchmarkClass.B_REPLAY_SAFE_OPTIMIZATION.value: 4,
    BenchmarkClass.C_NEUTRAL_COMPLEXITY_INCREASE.value: 3,
    BenchmarkClass.D_OVERENGINEERED_DRIFT.value: 2,
    BenchmarkClass.E_EPISTEMICALLY_DEGRADED.value: 1,
}

_MEANING: dict[str, str] = {
    BenchmarkClass.A_REAL_VALIDATED_IMPROVEMENT.value:
        "the mutated version is really, measurably better than the "
        "frozen baseline - blind-validated, byte-identical outputs, "
        "governance-identical, traceable and replay-stable - the "
        "strongest landing",
    BenchmarkClass.B_REPLAY_SAFE_OPTIMIZATION.value:
        "a replay-safe optimisation, but not a fully validated "
        "evolutionary improvement",
    BenchmarkClass.C_NEUTRAL_COMPLEXITY_INCREASE.value:
        "complexity increased without a measurable improvement",
    BenchmarkClass.D_OVERENGINEERED_DRIFT.value:
        "evolution drifted into overengineering - complexity "
        "dominates measured benefit - a failure",
    BenchmarkClass.E_EPISTEMICALLY_DEGRADED.value:
        "replay, artifacts or governance degraded - a failure",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    BenchmarkClass.A_REAL_VALIDATED_IMPROVEMENT.value,
    BenchmarkClass.B_REPLAY_SAFE_OPTIMIZATION.value,
    BenchmarkClass.C_NEUTRAL_COMPLEXITY_INCREASE.value,
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
    "BENCHMARK_CLASSES",
    "BenchmarkClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
