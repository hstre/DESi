"""v30.4 - aggregate metrics, Concept Gate, classification.

Pulls one signal per gate dimension from the v30 layers (v30.0
topology, v30.1 rejections, v30.2 attractors, v30.3 ecology),
checks the six-condition Concept Gate, and classifies the
evolution memory on the closed A-E taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED
from desi.evolution_memory import (
    evolution_traceability as _v300_traceability,
    lineage_visibility as _v300_lineage,
    replay_stability as _v300_replay,
)
from desi.evolution_memory_rejections import (
    governance_neutrality as _v301_neutrality,
    risk_pattern_visibility as _v301_risk_pattern,
    replay_stability as _v301_replay,
    unsafe_recurrence_visibility as _v301_recurrence,
)
from desi.evolution_memory_attractors import (
    evolution_diversity as _v302_diversity,
    replay_stability as _v302_replay,
)
from desi.evolution_memory_ecology import (
    branch_lineage_integrity as _v303_lineage,
    generation_traceability as _v303_gen_trace,
    governance_preservation as _v303_governance,
    human_approval_enforcement as _v303_human,
    replay_stability as _v303_replay,
)

from .taxonomy import EvolutionClass

GATE_PASS_STATEMENT = (
    "DESi kann replay-validierte evolutionaere Branch-Historien "
    "dauerhaft epistemisch strukturieren."
)
GATE_FAIL_STATEMENT = (
    "Evolution Memory bleibt epistemisch instabil."
)

_FLOOR = 0.95
_DIVERSITY_FLOOR = 0.50


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def replay_integrity() -> float:
    return _round(min(
        _v300_replay(), _v301_replay(), _v302_replay(),
        _v303_replay(),
    ))


def governance_preservation() -> float:
    return _round(min(_v301_neutrality(), _v303_governance()))


def lineage_integrity() -> float:
    return _round(min(_v300_lineage(), _v303_lineage()))


def risk_visibility() -> float:
    return _round(min(_v301_risk_pattern(), _v301_recurrence()))


def human_approval_enforcement() -> float:
    if not HUMAN_APPROVAL_REQUIRED:
        return 0.0
    return _round(_v303_human())


def evolution_traceability() -> float:
    return _round(min(_v300_traceability(), _v303_gen_trace()))


def _layer_replays() -> tuple[float, ...]:
    return (
        _v300_replay(), _v301_replay(), _v302_replay(),
        _v303_replay(),
    )


@dataclass(frozen=True)
class EvolutionMetrics:
    replay_integrity: float
    governance_preservation: float
    lineage_integrity: float
    risk_visibility: float
    human_approval_enforcement: float
    evolution_traceability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "replay_integrity": self.replay_integrity,
            "governance_preservation":
                self.governance_preservation,
            "lineage_integrity": self.lineage_integrity,
            "risk_visibility": self.risk_visibility,
            "human_approval_enforcement":
                self.human_approval_enforcement,
            "evolution_traceability": self.evolution_traceability,
        }


def _core_values() -> tuple[float, ...]:
    return (
        replay_integrity(), governance_preservation(),
        lineage_integrity(), risk_visibility(),
        human_approval_enforcement(), evolution_traceability(),
    )


def replay_stability() -> float:
    if _core_values() != _core_values():
        return 0.0
    if any(r != 1.0 for r in _layer_replays()):
        return 0.0
    return 1.0


@lru_cache(maxsize=1)
def aggregate() -> EvolutionMetrics:
    return EvolutionMetrics(
        replay_integrity=replay_integrity(),
        governance_preservation=governance_preservation(),
        lineage_integrity=lineage_integrity(),
        risk_visibility=risk_visibility(),
        human_approval_enforcement=human_approval_enforcement(),
        evolution_traceability=evolution_traceability(),
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
            "replay_integrity", m.replay_integrity, _FLOOR,
            ">=", m.replay_integrity >= _FLOOR),
        GateCondition(
            "governance_preservation", m.governance_preservation,
            _FLOOR, ">=", m.governance_preservation >= _FLOOR),
        GateCondition(
            "lineage_integrity", m.lineage_integrity, _FLOOR,
            ">=", m.lineage_integrity >= _FLOOR),
        GateCondition(
            "risk_visibility", m.risk_visibility, _FLOOR, ">=",
            m.risk_visibility >= _FLOOR),
        GateCondition(
            "human_approval_enforcement",
            m.human_approval_enforcement, 1.0, "==",
            m.human_approval_enforcement == 1.0),
        GateCondition(
            "evolution_traceability", m.evolution_traceability,
            _FLOOR, ">=", m.evolution_traceability >= _FLOOR),
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions() if not c.passed
    )


def classify_corpus() -> str:
    """Priority-ordered classification (most severe first)."""
    m = aggregate()
    # E - epistemically unstable
    if (
        m.replay_integrity < _FLOOR
        or m.evolution_traceability < _FLOOR
        or replay_stability() < 1.0
    ):
        return EvolutionClass.E_EPISTEMICALLY_UNSTABLE.value
    # D - optimization-trapped (evolution collapsed)
    if _v302_diversity() < _DIVERSITY_FLOOR:
        return EvolutionClass.D_OPTIMIZATION_TRAPPED.value
    # C - productive but drifting
    if (
        m.lineage_integrity < _FLOOR
        or m.governance_preservation < _FLOOR
    ):
        return EvolutionClass.C_PRODUCTIVE_DRIFTING.value
    # A - replay-governed evolutionary memory
    if gate_passes_all() and m.human_approval_enforcement == 1.0:
        return EvolutionClass.A_REPLAY_GOVERNED_MEMORY.value
    # B - stable branch ecology
    return EvolutionClass.B_STABLE_BRANCH_ECOLOGY.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "EvolutionMetrics",
    "GateCondition",
    "aggregate",
    "classify_corpus",
    "evolution_traceability",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_preservation",
    "human_approval_enforcement",
    "lineage_integrity",
    "replay_integrity",
    "replay_stability",
    "risk_visibility",
]
