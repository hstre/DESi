"""v33.4 - aggregate metrics, Concept Gate, classification.

Pulls one signal per gate dimension from the v33 layers (v33.0
schema, v33.1 drift adapter, v33.2 search adapter, v33.3 harness),
checks the six-condition Concept Gate and classifies benchmark
compatibility on the closed A-E taxonomy. Overfitting resistance is
the new aggregate: it measures the degree to which DESi does NOT
adapt to benchmarks.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.benchmark_api import (
    FORBIDDEN_BENCHMARK_OPERATIONS,
    governance_independence as _v330_gov_independence,
    replay_stability as _v330_replay,
)
from desi.benchmark_api_drift import (
    drift_mapping_integrity as _v331_mapping,
    governance_preservation as _v331_gov,
    replay_stability as _v331_replay,
)
from desi.benchmark_api_harness import (
    blind_evaluation_integrity as _v333_blind,
    core_separation as _v333_core_sep,
    replay_stability as _v333_replay,
    scorecard_traceability as _v333_scorecard,
)
from desi.benchmark_api_search import (
    compression_measurement as _v332_compression,
    replay_stability as _v332_replay,
)
from desi.peripheral_mutation import (
    core_identity as _core_identity,
    replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .taxonomy import CompatibilityClass

GATE_PASS_STATEMENT = (
    "DESi kann externe Benchmarks ueber kontrollierte Adapter "
    "bedienen, ohne ihren epistemischen Kern oder ihre Governance "
    "zu veraendern."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt nicht stabil gegenueber externen "
    "Benchmark-Interfaces."
)

_FLOOR = 0.95

# Overfitting vectors that the API must structurally forbid.
_OVERFIT_VECTORS: tuple[str, ...] = (
    "benchmark_overfitting", "score_hacking",
    "hidden_test_adaptation", "benchmark_driven_core_change",
    "benchmark_specific_governance_weakening",
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def core_identity() -> float:
    return _round(_core_identity())


def governance_independence() -> float:
    return _round(min(_v330_gov_independence(), _v331_gov()))


def benchmark_mapping_integrity() -> float:
    return _round(min(_v331_mapping(), _v332_compression()))


def scorecard_traceability() -> float:
    return _round(_v333_scorecard())


def _overfit_vectors_forbidden() -> bool:
    forb = set(FORBIDDEN_BENCHMARK_OPERATIONS)
    return all(v in forb for v in _OVERFIT_VECTORS)


def overfitting_resistance() -> float:
    """The degree to which DESi does NOT adapt to benchmarks: the
    core stays separate, scoring is blind, governance is independent,
    and every overfitting vector is structurally forbidden."""
    if not _overfit_vectors_forbidden():
        return 0.0
    return _round(min(
        _v333_core_sep(), _v333_blind(), governance_independence(),
    ))


def _layer_replays() -> tuple[float, ...]:
    return (
        _v330_replay(), _v331_replay(), _v332_replay(),
        _v333_replay(), _core_replay(),
    )


def replay_stability() -> float:
    if any(r != 1.0 for r in _layer_replays()):
        return 0.0
    return 1.0


@dataclass(frozen=True)
class CompatibilityMetrics:
    core_identity: float
    governance_independence: float
    benchmark_mapping_integrity: float
    scorecard_traceability: float
    overfitting_resistance: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "core_identity": self.core_identity,
            "governance_independence": self.governance_independence,
            "benchmark_mapping_integrity":
                self.benchmark_mapping_integrity,
            "scorecard_traceability": self.scorecard_traceability,
            "overfitting_resistance": self.overfitting_resistance,
            "replay_stability": self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> CompatibilityMetrics:
    return CompatibilityMetrics(
        core_identity=core_identity(),
        governance_independence=governance_independence(),
        benchmark_mapping_integrity=benchmark_mapping_integrity(),
        scorecard_traceability=scorecard_traceability(),
        overfitting_resistance=overfitting_resistance(),
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
            "core_identity", m.core_identity, 1.0, "==",
            m.core_identity == 1.0),
        GateCondition(
            "governance_independence", m.governance_independence,
            _FLOOR, ">=", m.governance_independence >= _FLOOR),
        GateCondition(
            "benchmark_mapping_integrity",
            m.benchmark_mapping_integrity, _FLOOR, ">=",
            m.benchmark_mapping_integrity >= _FLOOR),
        GateCondition(
            "scorecard_traceability", m.scorecard_traceability,
            _FLOOR, ">=", m.scorecard_traceability >= _FLOOR),
        GateCondition(
            "overfitting_resistance", m.overfitting_resistance,
            _FLOOR, ">=", m.overfitting_resistance >= _FLOOR),
        GateCondition(
            "replay_stability", m.replay_stability, 1.0, "==",
            m.replay_stability == 1.0),
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(c.name for c in gate_conditions() if not c.passed)


def classify_corpus() -> str:
    """Priority-ordered classification (most severe first)."""
    m = aggregate()
    # E - benchmark-unsafe (core/governance/replay broke)
    if (
        m.replay_stability < 1.0
        or m.core_identity < 1.0
        or m.governance_independence < _FLOOR
    ):
        return CompatibilityClass.E_BENCHMARK_UNSAFE.value
    # D - benchmark-overfitted
    if m.overfitting_resistance < _FLOOR:
        return CompatibilityClass.D_BENCHMARK_OVERFITTED.value
    # C - partially compatible but fragile
    if (
        m.benchmark_mapping_integrity < _FLOOR
        or m.scorecard_traceability < _FLOOR
    ):
        return CompatibilityClass.C_PARTIALLY_COMPATIBLE_FRAGILE.value
    # A - benchmark-compatible governance system
    if gate_passes_all() and m.governance_independence == 1.0:
        return (
            CompatibilityClass.A_BENCHMARK_COMPATIBLE_GOVERNANCE.value
        )
    # B - adapter-stable benchmark system
    return CompatibilityClass.B_ADAPTER_STABLE.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "CompatibilityMetrics",
    "GateCondition",
    "aggregate",
    "benchmark_mapping_integrity",
    "classify_corpus",
    "core_identity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_independence",
    "overfitting_resistance",
    "replay_stability",
    "scorecard_traceability",
]
