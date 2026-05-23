"""v35.4 - aggregate real benchmark scores, Concept Gate, classification.

Aggregates one score per real benchmark dimension from the v35.0-v35.3
layers (plus the v34.2 reproducibility run), checks the six-condition
Concept Gate and classifies the real external benchmark runs on the
closed A-E taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.benchmark_runs_repro import reproducibility_metrics
from desi.external_benchmarks import (
    governance_independence as _connector_gov,
    replay_stability as _connector_replay,
)
from desi.external_benchmarks_drift import (
    build_report as _drift_report,
    drift_run_metrics,
    governance_preservation as _drift_gov,
    replay_stability as _drift_replay,
)
from desi.external_benchmarks_export import (
    governance_visibility as _export_gov,
    replay_stability as _export_replay,
)
from desi.external_benchmarks_search import (
    build_report as _search_report,
    replay_stability as _search_replay,
    search_run_metrics,
)
from desi.peripheral_mutation import (
    core_identity as _core_identity,
    replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .taxonomy import RealBenchmarkClass

GATE_PASS_STATEMENT = (
    "DESi besteht reale externe Benchmark-Suites als replay-governed "
    "epistemic governance system."
)
GATE_FAIL_STATEMENT = (
    "DESi ist noch nicht robust genug fuer reale oeffentliche "
    "Benchmark-Suites."
)

_DRIFT_FLOOR = 0.85
_SEARCH_FLOOR = 0.85
_REPRO_FLOOR = 0.95
_GOV_FLOOR = 0.95
_FRAGILE_FLOOR = 0.70


def _mean(d: dict[str, float]) -> float:
    return round(sum(d.values()) / len(d), 6) if d else 0.0


def real_drift_score() -> float:
    return _mean(drift_run_metrics())


def real_search_score() -> float:
    return _mean(search_run_metrics())


def reproducibility_score() -> float:
    return _mean(reproducibility_metrics())


def governance_stability() -> float:
    return round(min(
        _drift_gov(), _connector_gov(), _export_gov(),
    ), 6)


def core_identity() -> float:
    return round(_core_identity(), 6)


def _run_halts() -> tuple[bool, ...]:
    return (_drift_report().halt, _search_report().halt)


def replay_stability() -> float:
    layers = (
        _connector_replay(), _drift_replay(), _search_replay(),
        _export_replay(), _core_replay(),
    )
    return 1.0 if all(r == 1.0 for r in layers) else 0.0


@dataclass(frozen=True)
class RealBenchmarkMetrics:
    real_drift_score: float
    real_search_score: float
    reproducibility_score: float
    governance_stability: float
    core_identity: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "real_drift_score": self.real_drift_score,
            "real_search_score": self.real_search_score,
            "reproducibility_score": self.reproducibility_score,
            "governance_stability": self.governance_stability,
            "core_identity": self.core_identity,
            "replay_stability": self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> RealBenchmarkMetrics:
    return RealBenchmarkMetrics(
        real_drift_score=real_drift_score(),
        real_search_score=real_search_score(),
        reproducibility_score=reproducibility_score(),
        governance_stability=governance_stability(),
        core_identity=core_identity(),
        replay_stability=replay_stability(),
    )


@dataclass(frozen=True)
class GateCondition:
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


def gate_conditions() -> tuple[GateCondition, ...]:
    m = aggregate()
    return (
        GateCondition(
            "real_drift_score", m.real_drift_score, _DRIFT_FLOOR,
            ">=", m.real_drift_score >= _DRIFT_FLOOR),
        GateCondition(
            "real_search_score", m.real_search_score, _SEARCH_FLOOR,
            ">=", m.real_search_score >= _SEARCH_FLOOR),
        GateCondition(
            "reproducibility_score", m.reproducibility_score,
            _REPRO_FLOOR, ">=",
            m.reproducibility_score >= _REPRO_FLOOR),
        GateCondition(
            "governance_stability", m.governance_stability,
            _GOV_FLOOR, ">=", m.governance_stability >= _GOV_FLOOR),
        GateCondition(
            "core_identity", m.core_identity, 1.0, "==",
            m.core_identity == 1.0),
        GateCondition(
            "replay_stability", m.replay_stability, 1.0, "==",
            m.replay_stability == 1.0),
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(c.name for c in gate_conditions() if not c.passed)


def _real_scores() -> tuple[float, ...]:
    m = aggregate()
    return (
        m.real_drift_score, m.real_search_score,
        m.reproducibility_score,
    )


def classify_corpus() -> str:
    """Priority-ordered classification (most severe first)."""
    m = aggregate()
    # E - benchmark-unsafe
    if (
        m.replay_stability < 1.0
        or m.core_identity < 1.0
        or m.governance_stability < _GOV_FLOOR
    ):
        return RealBenchmarkClass.E_BENCHMARK_UNSAFE.value
    # D - benchmark-fragile
    if any(s < _FRAGILE_FLOOR for s in _real_scores()) or any(
        _run_halts()
    ):
        return RealBenchmarkClass.D_BENCHMARK_FRAGILE.value
    # A - externally benchmark-robust
    if gate_passes_all():
        return RealBenchmarkClass.A_EXTERNALLY_ROBUST.value
    # B - externally benchmark-compatible
    if (
        m.core_identity == 1.0
        and m.replay_stability == 1.0
        and m.real_drift_score >= _DRIFT_FLOOR
        and m.real_search_score >= _SEARCH_FLOOR
    ):
        return RealBenchmarkClass.B_EXTERNALLY_COMPATIBLE.value
    # C - partially robust but unstable
    return RealBenchmarkClass.C_PARTIALLY_ROBUST_UNSTABLE.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "GateCondition",
    "RealBenchmarkMetrics",
    "aggregate",
    "classify_corpus",
    "core_identity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_stability",
    "real_drift_score",
    "real_search_score",
    "replay_stability",
    "reproducibility_score",
]
