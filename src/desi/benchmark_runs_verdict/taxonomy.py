"""v34.4 - closed A-E taxonomy for the external benchmark runs.

A and B are healthy landings (a benchmark-robust epistemic system, or
a benchmark-compatible but limited one); C is a warning (partially
robust); D and E are failures (benchmark-fragile, or benchmark-unsafe).
"""
from __future__ import annotations

from enum import Enum


class BenchmarkRunClass(Enum):
    A_BENCHMARK_ROBUST = "benchmark_robust_epistemic_system"
    B_COMPATIBLE_LIMITED = "benchmark_compatible_but_limited"
    C_PARTIALLY_ROBUST = "partially_robust"
    D_BENCHMARK_FRAGILE = "benchmark_fragile"
    E_BENCHMARK_UNSAFE = "benchmark_unsafe"


BENCHMARK_RUN_CLASSES: tuple[str, ...] = tuple(
    c.value for c in BenchmarkRunClass
)

_RANK: dict[str, int] = {
    BenchmarkRunClass.A_BENCHMARK_ROBUST.value: 5,
    BenchmarkRunClass.B_COMPATIBLE_LIMITED.value: 4,
    BenchmarkRunClass.C_PARTIALLY_ROBUST.value: 3,
    BenchmarkRunClass.D_BENCHMARK_FRAGILE.value: 2,
    BenchmarkRunClass.E_BENCHMARK_UNSAFE.value: 1,
}

_MEANING: dict[str, str] = {
    BenchmarkRunClass.A_BENCHMARK_ROBUST.value:
        "DESi passes all four external benchmark families with the "
        "core unchanged and replay stable - a benchmark-robust "
        "epistemic governance system, the strongest landing",
    BenchmarkRunClass.B_COMPATIBLE_LIMITED.value:
        "DESi is benchmark-compatible and core-safe, but one or more "
        "families fall short of the higher reproducibility/rendering "
        "bar",
    BenchmarkRunClass.C_PARTIALLY_ROBUST.value:
        "some benchmark families pass while others miss their gate - "
        "partially robust",
    BenchmarkRunClass.D_BENCHMARK_FRAGILE.value:
        "a benchmark family failed badly or a run halted - fragile",
    BenchmarkRunClass.E_BENCHMARK_UNSAFE.value:
        "the core identity or replay broke under the benchmark runs "
        "- unsafe",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    BenchmarkRunClass.A_BENCHMARK_ROBUST.value,
    BenchmarkRunClass.B_COMPATIBLE_LIMITED.value,
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
    "BENCHMARK_RUN_CLASSES",
    "BenchmarkRunClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
