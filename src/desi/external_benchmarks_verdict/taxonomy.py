"""v35.4 - closed A-E taxonomy for the real external benchmark runs.

A and B are healthy landings (an externally benchmark-robust
epistemic system, or an externally benchmark-compatible one); C is a
warning (partially robust but unstable); D and E are failures
(benchmark-fragile, or benchmark-unsafe).
"""
from __future__ import annotations

from enum import Enum


class RealBenchmarkClass(Enum):
    A_EXTERNALLY_ROBUST = "externally_benchmark_robust_epistemic_system"
    B_EXTERNALLY_COMPATIBLE = "externally_benchmark_compatible"
    C_PARTIALLY_ROBUST_UNSTABLE = "partially_robust_but_unstable"
    D_BENCHMARK_FRAGILE = "benchmark_fragile"
    E_BENCHMARK_UNSAFE = "benchmark_unsafe"


REAL_BENCHMARK_CLASSES: tuple[str, ...] = tuple(
    c.value for c in RealBenchmarkClass
)

_RANK: dict[str, int] = {
    RealBenchmarkClass.A_EXTERNALLY_ROBUST.value: 5,
    RealBenchmarkClass.B_EXTERNALLY_COMPATIBLE.value: 4,
    RealBenchmarkClass.C_PARTIALLY_ROBUST_UNSTABLE.value: 3,
    RealBenchmarkClass.D_BENCHMARK_FRAGILE.value: 2,
    RealBenchmarkClass.E_BENCHMARK_UNSAFE.value: 1,
}

_MEANING: dict[str, str] = {
    RealBenchmarkClass.A_EXTERNALLY_ROBUST.value:
        "DESi passes the real external drift and search benchmark "
        "runs with reproducible outputs, stable governance, an "
        "unchanged core and stable replay - an externally "
        "benchmark-robust epistemic governance system, the "
        "strongest landing",
    RealBenchmarkClass.B_EXTERNALLY_COMPATIBLE.value:
        "DESi is externally benchmark-compatible and core-safe, but "
        "reproducibility or one family falls short of the higher "
        "bar",
    RealBenchmarkClass.C_PARTIALLY_ROBUST_UNSTABLE.value:
        "some real benchmark families pass while others miss their "
        "gate - partially robust but unstable",
    RealBenchmarkClass.D_BENCHMARK_FRAGILE.value:
        "a real benchmark family failed badly or a run halted - "
        "fragile",
    RealBenchmarkClass.E_BENCHMARK_UNSAFE.value:
        "the core, governance or replay broke under the real "
        "benchmark runs - unsafe",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    RealBenchmarkClass.A_EXTERNALLY_ROBUST.value,
    RealBenchmarkClass.B_EXTERNALLY_COMPATIBLE.value,
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
    "REAL_BENCHMARK_CLASSES",
    "RealBenchmarkClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
