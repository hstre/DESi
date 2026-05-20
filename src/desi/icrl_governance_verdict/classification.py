"""v19.4 - aggregate metrics, concept gate, and corpus
classification.

Rolls up v19.0-v19.3 into the five directive metrics and
the six-condition concept gate, and assigns DESi's
exploration governance one closed A-E class. Reads only
the sprints' published metrics.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.icrl_governance import (
    build_report as _v0_report,
    novelty_visibility as _v0_novelty, redundant_fraction,
)
from desi.icrl_governed import (
    build_report as _v1_report, exploration_preservation,
    hidden_authority_drift, redundancy_reduction,
)
from desi.icrl_sparse_reward import (
    build_report as _v2_report, exploration_collapse,
    novelty_preservation as _v2_novelty,
)
from desi.icrl_ecology import (
    build_report as _v3_report,
    novelty_visibility as _v3_novelty,
    trajectory_capture_resistance,
)

from .taxonomy import ExplorationGovernanceClass, class_rank

# Concept-gate floors / ceilings (directive § v19.4).
GATE_REDUNDANCY_REDUCTION = 0.40
GATE_EXPLORATION_PRESERVATION = 0.90
GATE_CAPTURE_RESISTANCE = 0.90
GATE_NOVELTY_VISIBILITY = 0.90
GATE_HIDDEN_AUTHORITY = 0.05

GATE_PASS_STATEMENT = (
    "DESi kann Exploration epistemisch strukturieren ohne "
    "versteckte Optimierungsautoritaet zu uebernehmen."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt epistemisch instabil gegenueber Exploration "
    "Collapse."
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def capture_resistance() -> float:
    return _round(trajectory_capture_resistance())


def novelty_visibility() -> float:
    """Mean novelty visibility across the audit, sparse-
    reward, and long-horizon sprints."""
    return _round(_mean([
        _v0_novelty(), _v2_novelty(), _v3_novelty(),
    ]))


def _sub_replays() -> list[float]:
    return [
        _v0_report().replay_stability,
        _v1_report().replay_stability,
        _v2_report().replay_stability,
        _v3_report().replay_stability,
    ]


def _aggregate_tuple() -> tuple[float, ...]:
    return (
        redundancy_reduction(), exploration_preservation(),
        capture_resistance(), novelty_visibility(),
        hidden_authority_drift(),
    )


def _meta_replay() -> float:
    if min(_sub_replays()) < 1.0:
        return 0.0
    return 1.0 if _aggregate_tuple() == _aggregate_tuple() else 0.0


@dataclass(frozen=True)
class AggregateMetrics:
    redundancy_reduction: float
    exploration_preservation: float
    capture_resistance: float
    novelty_visibility: float
    hidden_authority_drift: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "redundancy_reduction": self.redundancy_reduction,
            "exploration_preservation":
                self.exploration_preservation,
            "capture_resistance": self.capture_resistance,
            "novelty_visibility": self.novelty_visibility,
            "hidden_authority_drift":
                self.hidden_authority_drift,
            "replay_stability": self.replay_stability,
        }


def aggregate() -> AggregateMetrics:
    return AggregateMetrics(
        redundancy_reduction=redundancy_reduction(),
        exploration_preservation=exploration_preservation(),
        capture_resistance=capture_resistance(),
        novelty_visibility=novelty_visibility(),
        hidden_authority_drift=hidden_authority_drift(),
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
            "redundancy_reduction", m.redundancy_reduction,
            GATE_REDUNDANCY_REDUCTION, ">=",
            m.redundancy_reduction >= GATE_REDUNDANCY_REDUCTION,
        ),
        (
            "exploration_preservation",
            m.exploration_preservation,
            GATE_EXPLORATION_PRESERVATION, ">=",
            m.exploration_preservation
            >= GATE_EXPLORATION_PRESERVATION,
        ),
        (
            "capture_resistance", m.capture_resistance,
            GATE_CAPTURE_RESISTANCE, ">=",
            m.capture_resistance >= GATE_CAPTURE_RESISTANCE,
        ),
        (
            "novelty_visibility", m.novelty_visibility,
            GATE_NOVELTY_VISIBILITY, ">=",
            m.novelty_visibility >= GATE_NOVELTY_VISIBILITY,
        ),
        (
            "hidden_authority_drift", m.hidden_authority_drift,
            GATE_HIDDEN_AUTHORITY, "<=",
            m.hidden_authority_drift <= GATE_HIDDEN_AUTHORITY,
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
    return redundant_fraction() >= 0.40 or (
        exploration_collapse() >= 0.40
    )


def classify_corpus() -> str:
    """Priority-ordered A-E classification of DESi's
    exploration-governance state (most captured wins).
    About DESi's governance, never an optimality claim."""
    C = ExplorationGovernanceClass
    if capture_resistance() < GATE_CAPTURE_RESISTANCE:
        return C.E_TRAJECTORY_CAPTURED.value
    if (
        exploration_preservation() < GATE_EXPLORATION_PRESERVATION
        or redundancy_reduction() < GATE_REDUNDANCY_REDUCTION
    ):
        return C.D_EXPLORATION_COLLAPSED.value
    if conflict_rich():
        return C.C_CONFLICT_RICH_BUT_STABLE.value
    if novelty_visibility() >= GATE_NOVELTY_VISIBILITY:
        return C.B_NOVELTY_PRESERVING.value
    return C.A_EXPLORATION_GOVERNED.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "AggregateMetrics",
    "GateCondition",
    "aggregate",
    "capture_resistance",
    "class_rank",
    "classify_corpus",
    "conflict_rich",
    "exploration_preservation",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "hidden_authority_drift",
    "novelty_visibility",
    "redundancy_reduction",
]
