"""v36.4 - aggregate reasoning scores, Concept Gate, classification.

Aggregates one score per reasoning family from the v36.0-v36.3 runs
(instruction, scientific grounding, logic, multi-hop), checks the
six-condition Concept Gate and classifies on the closed A-E taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.reasoning_benchmarks import (
    governance_identity as _ifeval_gov, ifeval_metrics,
)
from desi.reasoning_benchmarks import build_report as _ifeval_report
from desi.reasoning_benchmarks_logic import (
    build_report as _logic_report, logic_metrics,
)
from desi.reasoning_benchmarks_multihop import (
    build_report as _multihop_report, multihop_metrics,
)
from desi.reasoning_benchmarks_scifact import (
    build_report as _scifact_report, scifact_metrics,
)
from desi.peripheral_mutation import (
    replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .taxonomy import ReasoningClass

GATE_PASS_STATEMENT = (
    "DESi besteht Reasoning-, Instruction- und "
    "Scientific-Grounding-Benchmarks als replay-stabiles "
    "epistemisches Governance-System."
)
GATE_FAIL_STATEMENT = (
    "DESi besteht die Reasoning-Benchmarks noch nicht vollstaendig "
    "als replay-stabiles Governance-System."
)

_INSTRUCTION_FLOOR = 0.85
_SCIENCE_FLOOR = 0.85
_LOGIC_FLOOR = 0.80
_MULTIHOP_FLOOR = 0.80
_FRAGILE_FLOOR = 0.70


def _mean(d: dict[str, float]) -> float:
    return round(sum(d.values()) / len(d), 6) if d else 0.0


def instruction_score() -> float:
    return _mean(ifeval_metrics())


def scientific_grounding_score() -> float:
    return _mean(scifact_metrics())


def logic_score() -> float:
    return _mean(logic_metrics())


def multihop_score() -> float:
    return _mean(multihop_metrics())


def governance_identity() -> float:
    return round(min(
        _ifeval_report().governance_identity,
        _scifact_report().governance_identity,
        _logic_report().governance_identity,
        _multihop_report().governance_identity,
        _ifeval_gov(),
    ), 6)


def _run_halts() -> tuple[bool, ...]:
    return (
        _ifeval_report().halt, _scifact_report().halt,
        _logic_report().halt, _multihop_report().halt,
    )


def replay_stability() -> float:
    layers = (
        ifeval_metrics()["replay_stability"],
        scifact_metrics()["replay_stability"],
        logic_metrics()["replay_stability"],
        multihop_metrics()["replay_stability"],
    )
    if any(r != 1.0 for r in layers):
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


@dataclass(frozen=True)
class ReasoningMetrics:
    instruction_score: float
    scientific_grounding_score: float
    logic_score: float
    multihop_score: float
    governance_identity: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "instruction_score": self.instruction_score,
            "scientific_grounding_score":
                self.scientific_grounding_score,
            "logic_score": self.logic_score,
            "multihop_score": self.multihop_score,
            "governance_identity": self.governance_identity,
            "replay_stability": self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> ReasoningMetrics:
    return ReasoningMetrics(
        instruction_score=instruction_score(),
        scientific_grounding_score=scientific_grounding_score(),
        logic_score=logic_score(),
        multihop_score=multihop_score(),
        governance_identity=governance_identity(),
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
            "instruction_score", m.instruction_score,
            _INSTRUCTION_FLOOR, ">=",
            m.instruction_score >= _INSTRUCTION_FLOOR),
        GateCondition(
            "scientific_grounding_score",
            m.scientific_grounding_score, _SCIENCE_FLOOR, ">=",
            m.scientific_grounding_score >= _SCIENCE_FLOOR),
        GateCondition(
            "logic_score", m.logic_score, _LOGIC_FLOOR, ">=",
            m.logic_score >= _LOGIC_FLOOR),
        GateCondition(
            "multihop_score", m.multihop_score, _MULTIHOP_FLOOR,
            ">=", m.multihop_score >= _MULTIHOP_FLOOR),
        GateCondition(
            "governance_identity", m.governance_identity, 1.0, "==",
            m.governance_identity == 1.0),
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
        m.instruction_score, m.scientific_grounding_score,
        m.logic_score, m.multihop_score,
    )


def classify_corpus() -> str:
    """Priority-ordered classification (most severe first)."""
    m = aggregate()
    if m.replay_stability < 1.0 or m.governance_identity < 1.0:
        return ReasoningClass.E_EPISTEMICALLY_UNSAFE.value
    if any(s < _FRAGILE_FLOOR for s in _family_scores()) or any(
        _run_halts()
    ):
        return ReasoningClass.D_BENCHMARK_FRAGILE.value
    if gate_passes_all():
        return ReasoningClass.A_REASONING_ROBUST.value
    if (
        m.governance_identity == 1.0
        and m.replay_stability == 1.0
        and all(s >= _MULTIHOP_FLOOR for s in _family_scores())
    ):
        return ReasoningClass.B_INSTRUCTION_SCIENCE_SEARCH_COMPATIBLE.value
    return ReasoningClass.C_PARTIALLY_ROBUST.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "GateCondition",
    "ReasoningMetrics",
    "aggregate",
    "classify_corpus",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "instruction_score",
    "logic_score",
    "multihop_score",
    "replay_stability",
    "scientific_grounding_score",
]
