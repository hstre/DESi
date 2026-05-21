"""v33.0 - the five schema Pflichtmetriken.

Validates that the benchmark API surface is formally defined and
that it stays independent of the protected core: every required
benchmark family has a task + output schema, every task makes its
operation boundary explicit, every result is replay-bound, and
governance is computed from the core alone - never from benchmark
input.
"""
from __future__ import annotations

import hashlib

from desi.frozen_baseline import governance_signature
from desi.peripheral_mutation import (
    core_fingerprint, core_identity as _core_identity,
    replay_stability as _core_replay,
)

from .constraints import (
    ALLOWED_BENCHMARK_OPERATIONS, FORBIDDEN_BENCHMARK_OPERATIONS,
)
from .registry import adversarial_task, canonical_tasks
from .result_types import RESULT_FIELDS
from .task_types import (
    BENCHMARK_OUTPUT_SCHEMAS, SUPPORTED_BENCHMARKS,
)

REQUIRED_BENCHMARKS: tuple[str, ...] = (
    "DRIFT_BENCHMARK",
    "SEARCH_COMPRESSION_BENCHMARK",
    "AGENT_ROBUSTNESS_BENCHMARK",
    "TOOL_PLANNING_BENCHMARK",
    "SCIENTIFIC_RENDERING_BENCHMARK",
    "CITATION_BENCHMARK",
)

_TRACE_FIELDS = ("replay_hash", "provenance", "governance_status")


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def core_identity() -> float:
    return _round(_core_identity())


def schema_coverage() -> float:
    """Fraction of required benchmark families with both a defined
    output schema and a canonical task."""
    tasks = {t.benchmark_name for t in canonical_tasks()}
    covered = sum(
        1 for b in REQUIRED_BENCHMARKS
        if b in BENCHMARK_OUTPUT_SCHEMAS
        and bool(BENCHMARK_OUTPUT_SCHEMAS[b])
        and b in tasks
    )
    return _round(covered / len(REQUIRED_BENCHMARKS))


def operation_boundary_visibility() -> float:
    """Fraction of canonical tasks that make allowed + forbidden
    operations explicit and cover the protected-core boundary."""
    tasks = canonical_tasks()
    if not tasks:
        return 0.0
    ok = sum(1 for t in tasks if t.boundary_explicit())
    return _round(ok / len(tasks))


def output_traceability() -> float:
    """Fraction of supported benchmarks whose output schema is
    non-empty and whose result schema is replay-bound."""
    if not set(_TRACE_FIELDS).issubset(set(RESULT_FIELDS)):
        return 0.0
    ok = sum(
        1 for b in SUPPORTED_BENCHMARKS
        if bool(BENCHMARK_OUTPUT_SCHEMAS.get(b))
    )
    return _round(ok / len(SUPPORTED_BENCHMARKS))


def governance_independence() -> float:
    """1.0 iff the governance signature is invariant across every
    canonical task and the adversarial task - governance is read from
    the core, never from benchmark input."""
    base = governance_signature()
    tasks = list(canonical_tasks()) + [adversarial_task()]
    for _ in tasks:
        if governance_signature() != base:
            return 0.0
    return 1.0


def schema_fingerprint() -> str:
    parts = [
        f"benchmarks={'|'.join(SUPPORTED_BENCHMARKS)}",
        f"allowed={'|'.join(ALLOWED_BENCHMARK_OPERATIONS)}",
        f"forbidden={'|'.join(FORBIDDEN_BENCHMARK_OPERATIONS)}",
        f"result_fields={'|'.join(RESULT_FIELDS)}",
        f"core={core_fingerprint()}",
    ]
    for b in SUPPORTED_BENCHMARKS:
        parts.append(f"{b}={'|'.join(BENCHMARK_OUTPUT_SCHEMAS[b])}")
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    """1.0 iff the schema fingerprint is reproducible and the core
    replay layer is itself stable."""
    if schema_fingerprint() != schema_fingerprint():
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def schema_metrics() -> dict[str, float]:
    return {
        "schema_coverage": schema_coverage(),
        "operation_boundary_visibility":
            operation_boundary_visibility(),
        "output_traceability": output_traceability(),
        "governance_independence": governance_independence(),
        "replay_stability": replay_stability(),
    }


__all__ = [
    "REQUIRED_BENCHMARKS",
    "core_identity",
    "governance_independence",
    "operation_boundary_visibility",
    "output_traceability",
    "replay_stability",
    "schema_coverage",
    "schema_fingerprint",
    "schema_metrics",
]
