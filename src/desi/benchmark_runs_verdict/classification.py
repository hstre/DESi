"""v34.4 - aggregate benchmark scores, Concept Gate, classification.

Aggregates one score per benchmark family from the v34.0-v34.3 runs,
checks the six-condition Concept Gate and classifies the external
benchmark runs on the closed A-E taxonomy. Each family score is the
mean of that run's preservation/identity metrics (reduction
magnitudes are reported, not scored).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.benchmark_runs import (
    build_report as _drift_report,
    claim_lineage_preservation as _d_lineage,
    drift_visibility as _d_visibility,
    memory_poisoning_resistance as _d_poison,
    objective_drift_resistance as _d_objective,
    replay_stability as _d_replay,
)
from desi.benchmark_runs_rendering import (
    build_report as _rendering_report,
    citation_completeness as _r_citation,
    limitation_visibility as _r_limitation,
    phantom_citation_resistance as _r_phantom,
    replay_stability as _r_replay,
    result_traceability as _r_trace,
)
from desi.benchmark_runs_repro import (
    artifact_identity as _p_artifact,
    build_report as _repro_report,
    citation_identity as _p_citation,
    metric_identity as _p_metric,
    output_identity as _p_output,
    replay_stability as _p_replay,
)
from desi.benchmark_runs_search import (
    build_report as _search_report,
    critical_branch_preservation as _s_critical,
    novelty_preservation as _s_novelty,
    quality_preservation as _s_quality,
    replay_stability as _s_replay,
)
from desi.peripheral_mutation import (
    core_identity as _core_identity,
    replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .taxonomy import BenchmarkRunClass

GATE_PASS_STATEMENT = (
    "DESi besteht kontrollierte externe Benchmark-Runs als "
    "replay-stabiles epistemisches Governance-System."
)
GATE_FAIL_STATEMENT = (
    "DESi ist noch nicht robust genug fuer externe "
    "Benchmark-Kompatibilitaet."
)

_DRIFT_FLOOR = 0.90
_SEARCH_FLOOR = 0.90
_REPRO_FLOOR = 0.95
_RENDER_FLOOR = 0.95
_FRAGILE_FLOOR = 0.70


def _mean(values: tuple[float, ...]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def drift_benchmark_score() -> float:
    return _mean((
        _d_lineage(), _d_visibility(), _d_poison(), _d_objective(),
        _d_replay(),
    ))


def search_compression_score() -> float:
    return _mean((
        _s_critical(), _s_novelty(), _s_quality(), _s_replay(),
    ))


def reproducibility_score() -> float:
    return _mean((
        _p_output(), _p_metric(), _p_citation(), _p_artifact(),
        _p_replay(),
    ))


def scientific_rendering_score() -> float:
    return _mean((
        _r_phantom(), _r_citation(), _r_trace(), _r_limitation(),
        _r_replay(),
    ))


def core_identity() -> float:
    return round(_core_identity(), 6)


def _run_halts() -> tuple[bool, ...]:
    return (
        _drift_report().halt, _search_report().halt,
        _repro_report().halt, _rendering_report().halt,
    )


def replay_stability() -> float:
    layers = (
        _d_replay(), _s_replay(), _p_replay(), _r_replay(),
        _core_replay(),
    )
    return 1.0 if all(r == 1.0 for r in layers) else 0.0


@dataclass(frozen=True)
class BenchmarkRunMetrics:
    drift_benchmark_score: float
    search_compression_score: float
    reproducibility_score: float
    scientific_rendering_score: float
    core_identity: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "drift_benchmark_score": self.drift_benchmark_score,
            "search_compression_score":
                self.search_compression_score,
            "reproducibility_score": self.reproducibility_score,
            "scientific_rendering_score":
                self.scientific_rendering_score,
            "core_identity": self.core_identity,
            "replay_stability": self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> BenchmarkRunMetrics:
    return BenchmarkRunMetrics(
        drift_benchmark_score=drift_benchmark_score(),
        search_compression_score=search_compression_score(),
        reproducibility_score=reproducibility_score(),
        scientific_rendering_score=scientific_rendering_score(),
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
            "drift_benchmark_score", m.drift_benchmark_score,
            _DRIFT_FLOOR, ">=",
            m.drift_benchmark_score >= _DRIFT_FLOOR),
        GateCondition(
            "search_compression_score", m.search_compression_score,
            _SEARCH_FLOOR, ">=",
            m.search_compression_score >= _SEARCH_FLOOR),
        GateCondition(
            "reproducibility_score", m.reproducibility_score,
            _REPRO_FLOOR, ">=",
            m.reproducibility_score >= _REPRO_FLOOR),
        GateCondition(
            "scientific_rendering_score",
            m.scientific_rendering_score, _RENDER_FLOOR, ">=",
            m.scientific_rendering_score >= _RENDER_FLOOR),
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


def _family_scores() -> tuple[float, ...]:
    m = aggregate()
    return (
        m.drift_benchmark_score, m.search_compression_score,
        m.reproducibility_score, m.scientific_rendering_score,
    )


def classify_corpus() -> str:
    """Priority-ordered classification (most severe first)."""
    m = aggregate()
    # E - benchmark-unsafe
    if m.replay_stability < 1.0 or m.core_identity < 1.0:
        return BenchmarkRunClass.E_BENCHMARK_UNSAFE.value
    # D - benchmark-fragile
    if any(s < _FRAGILE_FLOOR for s in _family_scores()) or any(
        _run_halts()
    ):
        return BenchmarkRunClass.D_BENCHMARK_FRAGILE.value
    # A - benchmark-robust epistemic system
    if gate_passes_all():
        return BenchmarkRunClass.A_BENCHMARK_ROBUST.value
    # B - compatible but limited (core/replay safe, all families
    # above the fragile floor, but a gate threshold missed)
    if (
        m.core_identity == 1.0
        and m.replay_stability == 1.0
        and all(s >= _DRIFT_FLOOR for s in _family_scores())
    ):
        return BenchmarkRunClass.B_COMPATIBLE_LIMITED.value
    # C - partially robust
    return BenchmarkRunClass.C_PARTIALLY_ROBUST.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "BenchmarkRunMetrics",
    "GateCondition",
    "aggregate",
    "classify_corpus",
    "core_identity",
    "drift_benchmark_score",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "reproducibility_score",
    "replay_stability",
    "scientific_rendering_score",
    "search_compression_score",
]
