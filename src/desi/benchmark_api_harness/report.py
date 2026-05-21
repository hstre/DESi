"""v33.3 - Benchmark Harness & Blind Runner report.

Pflichtmetriken (directive § v33.3):

* blind_evaluation_integrity
* core_separation
* result_validation
* scorecard_traceability
* replay_stability

Killerfrage: "Kann DESi externe Benchmarks ausfuehren ohne sich an
den Benchmark anzupassen?"

A general harness loads BenchmarkTasks, runs the matching DESi
adapter, validates the results, supports blind evaluation and emits
traceable scorecards - all without importing or touching a protected
core module.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.peripheral_mutation import (
    core_fingerprint, core_identity,
    replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .blind_runner import (
    blind_evaluation_integrity, blind_scores, sealed_map,
)
from .harness import load_tasks, run_all
from .result_validator import result_validation, validation_failures
from .scorecard import scorecard_traceability, scorecards

VERDICT_RAN = "BENCHMARK_HARNESS_RAN_CLEAN"
VERDICT_PARTIAL = "BENCHMARK_HARNESS_PARTIAL"
VERDICT_HALT = "BENCHMARK_HARNESS_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_RAN, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def core_separation() -> float:
    """1.0 iff running the whole benchmark suite leaves the core
    fingerprint identical (benchmarks are separate from the core)."""
    before = core_fingerprint()
    run_all()
    after = core_fingerprint()
    if before != after:
        return 0.0
    return 1.0 if core_identity() == 1.0 else 0.0


def replay_stability() -> float:
    """1.0 iff a fresh harness run reproduces identical replay hashes
    and the core replay layer is stable."""
    a = [r.replay_hash for _, r in run_all()]
    b = [r.replay_hash for _, r in run_all()]
    if a != b:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def harness_metrics() -> dict[str, float]:
    return {
        "blind_evaluation_integrity": blind_evaluation_integrity(),
        "core_separation": core_separation(),
        "result_validation": result_validation(),
        "scorecard_traceability": scorecard_traceability(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = harness_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation() -> str:
    m = harness_metrics()
    if m["replay_stability"] < 1.0 or m["core_separation"] < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_RAN
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V333Report:
    task_count: int
    blind_evaluation_integrity: float
    core_separation: float
    result_validation: float
    scorecard_traceability: float
    replay_stability: float
    core_identity: float
    validation_failures: tuple[str, ...]
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_count": self.task_count,
            "blind_evaluation_integrity":
                self.blind_evaluation_integrity,
            "core_separation": self.core_separation,
            "result_validation": self.result_validation,
            "scorecard_traceability": self.scorecard_traceability,
            "replay_stability": self.replay_stability,
            "core_identity": self.core_identity,
            "validation_failures": list(self.validation_failures),
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


def build_report() -> V333Report:
    m = harness_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0 or m["core_separation"] < 1.0
    rationale = (
        f"INFO: harness ran {len(load_tasks())} benchmark tasks "
        f"through registered adapters; results validated and scored",
        f"{'PASS' if m['blind_evaluation_integrity'] >= _FLOOR else 'FAIL'}"
        f": blind_evaluation_integrity "
        f"{m['blind_evaluation_integrity']} >= 0.95 (scored by "
        f"objective properties under anonymous labels)",
        f"{'PASS' if m['core_separation'] >= _FLOOR else 'FAIL'}: "
        f"core_separation {m['core_separation']} >= 0.95 (core "
        f"fingerprint unchanged by the run)",
        f"{'PASS' if m['result_validation'] >= _FLOOR else 'FAIL'}: "
        f"result_validation {m['result_validation']} >= 0.95 "
        f"(failures: {list(validation_failures())})",
        f"{'PASS' if m['scorecard_traceability'] >= _FLOOR else 'FAIL'}"
        f": scorecard_traceability {m['scorecard_traceability']} "
        f">= 0.95",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; core_identity {core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V333Report(
        task_count=len(load_tasks()),
        blind_evaluation_integrity=m["blind_evaluation_integrity"],
        core_separation=m["core_separation"],
        result_validation=m["result_validation"],
        scorecard_traceability=m["scorecard_traceability"],
        replay_stability=replay,
        core_identity=core_identity(),
        validation_failures=validation_failures(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_harness_artifact() -> dict[str, object]:
    m = harness_metrics()
    return {
        "schema_version": "v33_3_benchmark_harness",
        "disclaimer": (
            "A general benchmark harness that loads BenchmarkTasks, "
            "dispatches each to the matching DESi adapter, validates "
            "the results, scores them under blind anonymous labels "
            "and emits traceable scorecards. The harness is "
            "read-only: it never imports or mutates a protected core "
            "module, and running the whole suite leaves the core "
            "fingerprint identical. Blind scoring uses only "
            "objective result properties, so DESi cannot adapt its "
            "output to a known benchmark. Human approval is "
            "mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "task_count": len(load_tasks()),
        "registered_benchmarks": [
            t.benchmark_name for t in load_tasks()
        ],
        "blind_scores": blind_scores(),
        "blind_sealed_map": sealed_map(),
        "scorecards": [c.to_dict() for c in scorecards()],
        "blind_evaluation_integrity": m["blind_evaluation_integrity"],
        "core_separation": m["core_separation"],
        "result_validation": m["result_validation"],
        "scorecard_traceability": m["scorecard_traceability"],
        "replay_stability": m["replay_stability"],
        "core_identity": core_identity(),
        "validation_failures": list(validation_failures()),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_RAN",
    "V333Report",
    "build_harness_artifact",
    "build_report",
    "core_separation",
    "harness_metrics",
    "replay_stability",
]
