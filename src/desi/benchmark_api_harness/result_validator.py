"""v33.3 - result validation.

Every result a benchmark gets back must be structurally complete,
replay-bound, governance-tagged, and (for non-refusals) carry metrics
in the unit interval. Validation is what lets a benchmark trust a
score without trusting DESi to grade itself.
"""
from __future__ import annotations

from desi.benchmark_api import (
    GOVERNANCE_INDEPENDENT, BenchmarkResult, schema_complete,
)

from .harness import run_all


def validate(result: BenchmarkResult) -> bool:
    if not schema_complete(result):
        return False
    if not result.is_traceable():
        return False
    if result.governance_status != GOVERNANCE_INDEPENDENT:
        return False
    if result.is_refusal():
        # a refusal is valid: no metrics, an explicit reason
        return bool(result.refusal_reason_if_any)
    for _, v in result.metrics:
        if not (0.0 <= v <= 1.0):
            return False
    return True


def validation_failures() -> tuple[str, ...]:
    return tuple(
        t.task_id for t, r in run_all() if not validate(r)
    )


def result_validation() -> float:
    runs = run_all()
    if not runs:
        return 0.0
    ok = sum(1 for _, r in runs if validate(r))
    return round(ok / len(runs), 6)


__all__ = [
    "result_validation",
    "validate",
    "validation_failures",
]
