"""v32.4 - aggregate metrics, Concept Gate, classification.

Pulls one signal per gate dimension from the v32 layers (v32.0
frozen baseline, v32.1 real benchmark, v32.2 blind evaluation, v32.3
utility analysis), checks the six-condition Concept Gate, and
classifies the longitudinal evolution benchmark on the closed A-E
taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.evolution_memory import (
    evolution_traceability as _v300_traceability,
)
from desi.frozen_baseline import (
    governance_identity as _v320_governance,
    replay_stability as _v320_replay,
)
from desi.frozen_benchmark import (
    artifact_identity as _v321_artifact,
    measured_improvement as _v321_improvement,
    regression_survival as _v321_regression,
    replay_stability as _v321_replay,
)
from desi.frozen_benchmark_blind import (
    bias_resistance as _v322_bias,
    blindness_integrity as _v322_blind,
    blind_winner_is_mutated as _v322_winner_mutated,
    replay_stability as _v322_replay,
)
from desi.frozen_benchmark_utility import (
    evolution_features as _v323_features,
    evolution_utility as _v323_utility,
    overengineered_features as _v323_overeng,
    replay_stability as _v323_replay,
)
from desi.peripheral_mutation import (
    mutation_traceability as _v310_traceability,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .taxonomy import BenchmarkClass

GATE_PASS_STATEMENT = (
    "DESi hat erstmals wissenschaftlich messbare, replay-validierte "
    "evolutionaere Infrastrukturverbesserung gegenueber einer "
    "eingefrorenen Ursprungsversion demonstriert."
)
GATE_FAIL_STATEMENT = (
    "Die evolutionaere Infrastruktur hat keinen validierten "
    "messbaren Vorteil erzeugt."
)

_FLOOR = 0.95
_IMPROVEMENT_FLOOR = 0.20


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def measured_evolutionary_improvement() -> float:
    return _round(_v321_improvement())


def governance_identity() -> float:
    return _round(_v320_governance())


def artifact_identity() -> float:
    return _round(_v321_artifact())


def human_approval_enforcement() -> float:
    if not HUMAN_APPROVAL_REQUIRED:
        return 0.0
    return 1.0


def evolution_traceability() -> float:
    return _round(min(
        _v300_traceability(), _v310_traceability(),
    ))


def blind_validation() -> float:
    """Blind evaluation integrity and bias resistance, and the blind
    winner being the mutated version."""
    base = min(_v322_blind(), _v322_bias())
    return _round(base if _v322_winner_mutated() else 0.0)


def _layer_replays() -> tuple[float, ...]:
    return (
        _v320_replay(), _v321_replay(), _v322_replay(),
        _v323_replay(),
    )


@dataclass(frozen=True)
class BenchmarkMetrics:
    measured_evolutionary_improvement: float
    governance_identity: float
    artifact_identity: float
    human_approval_enforcement: float
    evolution_traceability: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "measured_evolutionary_improvement":
                self.measured_evolutionary_improvement,
            "governance_identity": self.governance_identity,
            "artifact_identity": self.artifact_identity,
            "human_approval_enforcement":
                self.human_approval_enforcement,
            "evolution_traceability": self.evolution_traceability,
            "replay_stability": self.replay_stability,
        }


def _core_values() -> tuple[float, ...]:
    return (
        measured_evolutionary_improvement(), governance_identity(),
        artifact_identity(), human_approval_enforcement(),
        evolution_traceability(),
    )


def replay_stability() -> float:
    if _core_values() != _core_values():
        return 0.0
    if any(r != 1.0 for r in _layer_replays()):
        return 0.0
    return 1.0


@lru_cache(maxsize=1)
def aggregate() -> BenchmarkMetrics:
    return BenchmarkMetrics(
        measured_evolutionary_improvement=(
            measured_evolutionary_improvement()
        ),
        governance_identity=governance_identity(),
        artifact_identity=artifact_identity(),
        human_approval_enforcement=human_approval_enforcement(),
        evolution_traceability=evolution_traceability(),
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
            "measured_evolutionary_improvement",
            m.measured_evolutionary_improvement, _IMPROVEMENT_FLOOR,
            ">=",
            m.measured_evolutionary_improvement >= _IMPROVEMENT_FLOOR),
        GateCondition(
            "governance_identity", m.governance_identity, 1.0,
            "==", m.governance_identity == 1.0),
        GateCondition(
            "artifact_identity", m.artifact_identity, 1.0, "==",
            m.artifact_identity == 1.0),
        GateCondition(
            "human_approval_enforcement",
            m.human_approval_enforcement, 1.0, "==",
            m.human_approval_enforcement == 1.0),
        GateCondition(
            "evolution_traceability", m.evolution_traceability,
            _FLOOR, ">=", m.evolution_traceability >= _FLOOR),
        GateCondition(
            "replay_stability", m.replay_stability, 1.0, "==",
            m.replay_stability == 1.0),
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions() if not c.passed
    )


def _overengineering_dominates() -> bool:
    """True iff more evolution features are overengineered than not -
    a drift into complexity."""
    total = len(_v323_features())
    flagged = len(_v323_overeng())
    return total > 0 and flagged * 2 > total


def classify_corpus() -> str:
    """Priority-ordered classification (most severe first)."""
    m = aggregate()
    # E - epistemically degraded
    if (
        m.replay_stability < 1.0
        or m.artifact_identity < 1.0
        or m.governance_identity < 1.0
    ):
        return BenchmarkClass.E_EPISTEMICALLY_DEGRADED.value
    # D - overengineered drift
    if _overengineering_dominates() or _v323_utility() <= 0.0:
        return BenchmarkClass.D_OVERENGINEERED_DRIFT.value
    # C - neutral complexity increase (no measurable improvement)
    if m.measured_evolutionary_improvement < _IMPROVEMENT_FLOOR:
        return BenchmarkClass.C_NEUTRAL_COMPLEXITY_INCREASE.value
    # A - real validated evolutionary improvement
    if (
        gate_passes_all()
        and blind_validation() == 1.0
        and m.human_approval_enforcement == 1.0
        and m.evolution_traceability >= _FLOOR
    ):
        return BenchmarkClass.A_REAL_VALIDATED_IMPROVEMENT.value
    # B - replay-safe optimisation
    return BenchmarkClass.B_REPLAY_SAFE_OPTIMIZATION.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "BenchmarkMetrics",
    "GateCondition",
    "aggregate",
    "artifact_identity",
    "blind_validation",
    "classify_corpus",
    "evolution_traceability",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "human_approval_enforcement",
    "measured_evolutionary_improvement",
    "replay_stability",
]
