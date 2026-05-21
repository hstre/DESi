"""v33.4 - closed A-E taxonomy for benchmark compatibility.

A and B are healthy landings (a fully benchmark-compatible
governance system, or an adapter-stable benchmark system); C is a
warning (partially compatible but fragile); D and E are failures
(benchmark-overfitted, or benchmark-unsafe).
"""
from __future__ import annotations

from enum import Enum


class CompatibilityClass(Enum):
    A_BENCHMARK_COMPATIBLE_GOVERNANCE = (
        "benchmark_compatible_governance_system"
    )
    B_ADAPTER_STABLE = "adapter_stable_benchmark_system"
    C_PARTIALLY_COMPATIBLE_FRAGILE = "partially_compatible_but_fragile"
    D_BENCHMARK_OVERFITTED = "benchmark_overfitted"
    E_BENCHMARK_UNSAFE = "benchmark_unsafe"


COMPATIBILITY_CLASSES: tuple[str, ...] = tuple(
    c.value for c in CompatibilityClass
)

_RANK: dict[str, int] = {
    CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value: 5,
    CompatibilityClass.B_ADAPTER_STABLE.value: 4,
    CompatibilityClass.C_PARTIALLY_COMPATIBLE_FRAGILE.value: 3,
    CompatibilityClass.D_BENCHMARK_OVERFITTED.value: 2,
    CompatibilityClass.E_BENCHMARK_UNSAFE.value: 1,
}

_MEANING: dict[str, str] = {
    CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value:
        "DESi serves external benchmarks through controlled "
        "adapters with a fully independent governance core and an "
        "unchanged epistemic core - the strongest landing",
    CompatibilityClass.B_ADAPTER_STABLE.value:
        "the adapters are stable and the core is intact, but "
        "governance independence is not yet perfect",
    CompatibilityClass.C_PARTIALLY_COMPATIBLE_FRAGILE.value:
        "benchmarks can be mapped but the mapping or scorecard "
        "traceability is incomplete - fragile",
    CompatibilityClass.D_BENCHMARK_OVERFITTED.value:
        "DESi adapted itself to the benchmarks - overfitting - a "
        "failure",
    CompatibilityClass.E_BENCHMARK_UNSAFE.value:
        "the benchmark layer broke the core, governance or replay - "
        "a failure",
}

_ACCEPTABLE: frozenset[str] = frozenset({
    CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value,
    CompatibilityClass.B_ADAPTER_STABLE.value,
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
    "COMPATIBILITY_CLASSES",
    "CompatibilityClass",
    "class_meaning",
    "class_rank",
    "is_acceptable",
]
