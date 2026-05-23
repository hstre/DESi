"""desi.gates.concept_gate - the closed six-condition Concept Gate.

Concept gates are implemented per phase as closed enumerations of
conditions; every phase verdict module exposes a `gate_conditions()`
returning frozen `GateCondition` records and a `gate_passes_all()`.
This module provides the shared, reusable gate structure and a generic
evaluator, plus a registry pointing at the real per-phase gates. It
invents no new gate semantics.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateCondition:
    """A single Concept-Gate condition (mirrors the per-phase
    dataclass used repo-wide)."""
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


def evaluate(value: float, threshold: float, comparator: str) -> bool:
    if comparator == ">=":
        return value >= threshold
    if comparator == "<=":
        return value <= threshold
    if comparator == "==":
        return value == threshold
    raise ValueError(f"unknown comparator: {comparator}")


def passes_all(conditions) -> bool:
    """True iff every condition passed (closed-gate semantics: a phase
    passes only if all conditions hold)."""
    return all(getattr(c, "passed", False) for c in conditions)


def failing(conditions) -> tuple[str, ...]:
    return tuple(
        getattr(c, "name", "?") for c in conditions
        if not getattr(c, "passed", False)
    )


def phase_gate(phase: str):
    """Return the REAL gate_conditions() for a packaged phase verdict.

    `phase` is one of the registered verdict modules; this maps the
    public name to the in-place implementation without copying it.
    """
    import importlib

    registry = {
        "benchmark_runs": "desi.benchmark_runs_verdict",
        "external_benchmarks": "desi.external_benchmarks_verdict",
        "reasoning_benchmarks": "desi.reasoning_benchmarks_verdict",
        "audit_benchmarks": "desi.audit_benchmarks_verdict",
        "live_llm_validation": "desi.live_llm_validation_verdict",
        "benchmark_api": "desi.benchmark_api_verdict",
    }
    if phase not in registry:
        raise KeyError(phase)
    mod = importlib.import_module(registry[phase])
    return mod.gate_conditions()


def registered_phases() -> tuple[str, ...]:
    return (
        "benchmark_runs", "external_benchmarks", "reasoning_benchmarks",
        "audit_benchmarks", "live_llm_validation", "benchmark_api",
    )


__all__ = [
    "GateCondition",
    "evaluate",
    "failing",
    "passes_all",
    "phase_gate",
    "registered_phases",
]
