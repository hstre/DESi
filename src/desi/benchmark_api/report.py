"""v33.0 - Benchmark API Schema report.

Pflichtmetriken (directive § v33.0):

* schema_coverage
* operation_boundary_visibility
* output_traceability
* governance_independence
* replay_stability

Killerfrage: "Kann DESi externe Benchmarks als kontrollierte
epistemische Aufgaben annehmen?"

Defines the formal API by which external benchmarks hand DESi a
BenchmarkTask and receive a replay-bound BenchmarkResult. The schema
pins explicit allowed/forbidden operations so a benchmark can test
DESi but never steer its protected core.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .constraints import (
    ALLOWED_BENCHMARK_OPERATIONS, FORBIDDEN_BENCHMARK_OPERATIONS,
)
from .registry import canonical_tasks
from .result_types import RESULT_FIELDS
from .schema import (
    REQUIRED_BENCHMARKS, core_identity, governance_independence,
    operation_boundary_visibility, output_traceability,
    replay_stability, schema_coverage, schema_fingerprint,
    schema_metrics,
)
from .task_types import SUPPORTED_BENCHMARKS

VERDICT_DEFINED = "BENCHMARK_API_SCHEMA_DEFINED"
VERDICT_INCOMPLETE = "BENCHMARK_API_SCHEMA_INCOMPLETE"
VERDICT_HALT = "BENCHMARK_API_SCHEMA_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_DEFINED, VERDICT_INCOMPLETE, VERDICT_HALT,
)

_FLOOR = 0.95


def _signature() -> str:
    m = schema_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    parts.append(f"fingerprint={schema_fingerprint()}")
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = schema_metrics()
    if m["replay_stability"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    floored = (
        "schema_coverage", "operation_boundary_visibility",
        "output_traceability", "governance_independence",
    )
    if all(m[k] >= _FLOOR for k in floored):
        return VERDICT_DEFINED
    return VERDICT_INCOMPLETE


@dataclass(frozen=True)
class V330Report:
    supported_benchmarks: tuple[str, ...]
    core_identity: float
    schema_coverage: float
    operation_boundary_visibility: float
    output_traceability: float
    governance_independence: float
    replay_stability: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "supported_benchmarks": list(self.supported_benchmarks),
            "core_identity": self.core_identity,
            "schema_coverage": self.schema_coverage,
            "operation_boundary_visibility":
                self.operation_boundary_visibility,
            "output_traceability": self.output_traceability,
            "governance_independence": self.governance_independence,
            "replay_stability": self.replay_stability,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V330Report:
    m = schema_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        f"INFO: defined the benchmark API surface for "
        f"{len(SUPPORTED_BENCHMARKS)} families "
        f"{list(SUPPORTED_BENCHMARKS)}; benchmarks may test DESi, "
        f"never steer it",
        f"{'PASS' if m['schema_coverage'] >= _FLOOR else 'FAIL'}: "
        f"schema_coverage {m['schema_coverage']} >= 0.95 "
        f"({len(REQUIRED_BENCHMARKS)} required families)",
        f"{'PASS' if m['operation_boundary_visibility'] >= _FLOOR else 'FAIL'}"
        f": operation_boundary_visibility "
        f"{m['operation_boundary_visibility']} >= 0.95 (allowed + "
        f"forbidden explicit, core boundary covered)",
        f"{'PASS' if m['output_traceability'] >= _FLOOR else 'FAIL'}"
        f": output_traceability {m['output_traceability']} >= 0.95 "
        f"(results replay-bound: {list(RESULT_FIELDS)})",
        f"{'PASS' if m['governance_independence'] >= _FLOOR else 'FAIL'}"
        f": governance_independence {m['governance_independence']} "
        f">= 0.95 (governance read from core, not benchmark input)",
        f"{'PASS' if m['replay_stability'] == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} == 1.0; core_identity "
        f"{core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V330Report(
        supported_benchmarks=SUPPORTED_BENCHMARKS,
        core_identity=core_identity(),
        schema_coverage=m["schema_coverage"],
        operation_boundary_visibility=(
            m["operation_boundary_visibility"]
        ),
        output_traceability=m["output_traceability"],
        governance_independence=m["governance_independence"],
        replay_stability=replay,
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_schema_artifact() -> dict[str, object]:
    m = schema_metrics()
    return {
        "schema_version": "v33_0_benchmark_api_schema",
        "disclaimer": (
            "Formal external-benchmark API for DESi. A benchmark "
            "hands DESi a BenchmarkTask (task_id, benchmark_name, "
            "input_payload, expected_output_schema, "
            "allowed_operations, forbidden_operations, "
            "evaluation_mode) and receives a replay-bound "
            "BenchmarkResult (claim_outputs, metrics, replay_hash, "
            "provenance, limitations, refusal_reason_if_any, "
            "governance_status). The protected-core boundary "
            "(replay kernel, determinism scanner, concept gates, "
            "governance core, authority filters) is imported from "
            "the v31 boundary layer and cannot be widened here. "
            "Benchmarks may TEST DESi but never STEER it; governance "
            "is read from the core, not from benchmark input. Human "
            "approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "supported_benchmarks": list(SUPPORTED_BENCHMARKS),
        "result_fields": list(RESULT_FIELDS),
        "allowed_operations": list(ALLOWED_BENCHMARK_OPERATIONS),
        "forbidden_operations": list(FORBIDDEN_BENCHMARK_OPERATIONS),
        "canonical_tasks": [t.to_dict() for t in canonical_tasks()],
        "core_identity": core_identity(),
        "schema_coverage": m["schema_coverage"],
        "operation_boundary_visibility":
            m["operation_boundary_visibility"],
        "output_traceability": m["output_traceability"],
        "governance_independence": m["governance_independence"],
        "replay_stability": m["replay_stability"],
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "schema_fingerprint": schema_fingerprint(),
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DEFINED",
    "VERDICT_HALT",
    "VERDICT_INCOMPLETE",
    "V330Report",
    "build_report",
    "build_schema_artifact",
]
