"""v20.4 - aggregate metrics, concept gate, and corpus
classification.

Rolls up v20.0-v20.3 into the five directive metrics and the
six-condition concept gate, and assigns the dual-agent
governance one closed A-E class. Reads only the sprints'
published metrics.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.dual_agent_exploration import (
    build_report as _v0_report, productivity_gain,
    wild_not_eliminated,
)
from desi.dual_agent_pressure import (
    authority_resistance as _v1_authority,
    build_report as _v1_report,
    hallucination_containment, novelty_gain as _v1_novelty,
)
from desi.dual_agent_negotiation import (
    build_report as _v2_report, conflict_productivity,
    dissent_preservation, exploration_diversity,
)
from desi.dual_agent_ecology import (
    authority_resistance as _v3_authority,
    build_report as _v3_report, capture_resistance,
    novelty_visibility as _v3_novelty,
)

from .taxonomy import DualAgentClass, class_rank

# Concept-gate floors (directive § v20.4).
GATE_HALLUCINATION_CONTAINMENT = 0.90
GATE_NOVELTY_PRESERVATION = 0.90
GATE_AUTHORITY_RESISTANCE = 0.90
GATE_PRODUCTIVE_CONFLICT = 0.90
GATE_EXPLORATION_DIVERSITY = 0.90

GATE_PASS_STATEMENT = (
    "DESi kann wilde Exploration epistemisch governieren ohne "
    "Exploration oder epistemische Freiheit zu zerstoeren."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt instabil gegenueber ungovernter Exploration."
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def novelty_preservation() -> float:
    """Mean of the adversarial-pressure novelty gain and the
    long-horizon novelty visibility."""
    return _round(_mean([_v1_novelty(), _v3_novelty()]))


def authority_resistance() -> float:
    """Mean authority resistance across the pressure and
    ecology sprints."""
    return _round(_mean([_v1_authority(), _v3_authority()]))


def productive_conflict() -> float:
    return _round(conflict_productivity())


def _sub_replays() -> list[float]:
    return [
        _v0_report().replay_stability,
        _v1_report().replay_stability,
        _v2_report().replay_stability,
        _v3_report().replay_stability,
    ]


def _aggregate_tuple() -> tuple[float, ...]:
    return (
        hallucination_containment(), novelty_preservation(),
        authority_resistance(), productive_conflict(),
        exploration_diversity(),
    )


def _meta_replay() -> float:
    if min(_sub_replays()) < 1.0:
        return 0.0
    return 1.0 if _aggregate_tuple() == _aggregate_tuple() else 0.0


@dataclass(frozen=True)
class AggregateMetrics:
    hallucination_containment: float
    novelty_preservation: float
    authority_resistance: float
    productive_conflict: float
    exploration_diversity: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "hallucination_containment":
                self.hallucination_containment,
            "novelty_preservation": self.novelty_preservation,
            "authority_resistance": self.authority_resistance,
            "productive_conflict": self.productive_conflict,
            "exploration_diversity": self.exploration_diversity,
            "replay_stability": self.replay_stability,
        }


def aggregate() -> AggregateMetrics:
    return AggregateMetrics(
        hallucination_containment=hallucination_containment(),
        novelty_preservation=novelty_preservation(),
        authority_resistance=authority_resistance(),
        productive_conflict=productive_conflict(),
        exploration_diversity=exploration_diversity(),
        replay_stability=_meta_replay(),
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
    raw = [
        (
            "hallucination_containment",
            m.hallucination_containment,
            GATE_HALLUCINATION_CONTAINMENT, ">=",
            m.hallucination_containment
            >= GATE_HALLUCINATION_CONTAINMENT,
        ),
        (
            "novelty_preservation", m.novelty_preservation,
            GATE_NOVELTY_PRESERVATION, ">=",
            m.novelty_preservation >= GATE_NOVELTY_PRESERVATION,
        ),
        (
            "authority_resistance", m.authority_resistance,
            GATE_AUTHORITY_RESISTANCE, ">=",
            m.authority_resistance >= GATE_AUTHORITY_RESISTANCE,
        ),
        (
            "productive_conflict", m.productive_conflict,
            GATE_PRODUCTIVE_CONFLICT, ">=",
            m.productive_conflict >= GATE_PRODUCTIVE_CONFLICT,
        ),
        (
            "exploration_diversity", m.exploration_diversity,
            GATE_EXPLORATION_DIVERSITY, ">=",
            m.exploration_diversity >= GATE_EXPLORATION_DIVERSITY,
        ),
        (
            "replay_stability", m.replay_stability, 1.0, "==",
            m.replay_stability == 1.0,
        ),
    ]
    return tuple(
        GateCondition(
            name=n, value=_round(v), threshold=t,
            comparator=c, passed=p,
        )
        for (n, v, t, c, p) in raw
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions() if not c.passed
    )


def conflict_rich() -> bool:
    return conflict_productivity() >= 0.50


def classify_corpus() -> str:
    """Priority-ordered A-E classification (most collapsed
    wins). About DESi's governance of the wild, never an
    optimality verdict."""
    C = DualAgentClass
    if authority_resistance() < GATE_AUTHORITY_RESISTANCE:
        return C.E_AUTHORITY_COLLAPSED.value
    if hallucination_containment() < GATE_HALLUCINATION_CONTAINMENT:
        return C.D_HALLUCINATION_DRIFTED.value
    if conflict_rich():
        return C.C_CONFLICT_RICH_BUT_PRODUCTIVE.value
    if novelty_preservation() >= GATE_NOVELTY_PRESERVATION:
        return C.B_NOVELTY_STABLE.value
    return C.A_GOVERNED_EXPLORATORY.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "AggregateMetrics",
    "GateCondition",
    "aggregate",
    "authority_resistance",
    "class_rank",
    "classify_corpus",
    "conflict_rich",
    "exploration_diversity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "hallucination_containment",
    "novelty_preservation",
    "productive_conflict",
    "productivity_gain",
    "wild_not_eliminated",
]
