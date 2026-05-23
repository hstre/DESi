"""v31.4 - aggregate metrics, Concept Gate, classification.

Pulls one signal per gate dimension from the v31 layers (v31.0
boundary enforcement, v31.1 real mutation, v31.2 comparison, v31.3
long-horizon ecology), checks the six-condition Concept Gate, and
classifies the peripheral mutation programme on the closed A-E
taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED
from desi.peripheral_mutation import (
    core_identity as _v310_core,
    governance_preservation as _v310_governance,
    mutation_traceability as _v310_traceability,
    replay_stability as _v310_replay,
)
from desi.peripheral_mutation_real import (
    core_identity as _v311_core,
    governance_identity as _v311_governance,
    replay_stability as _v311_replay,
)
from desi.peripheral_mutation_comparison import (
    core_identity as _v312_core,
    governance_identity as _v312_governance,
    regression_survival as _v312_regression,
    replay_stability as _v312_replay,
)
from desi.peripheral_mutation_ecology import (
    core_preservation as _v313_core,
    generation_stability as _v313_gen_stability,
    governance_preservation as _v313_governance,
    lineage_integrity as _v313_lineage,
    replay_stability as _v313_replay,
)

from .taxonomy import MutationClass

GATE_PASS_STATEMENT = (
    "DESi kann reale, branch-isolierte Infrastruktur-Mutationen "
    "ausserhalb des geschuetzten Kerns durchfuehren - replay-"
    "validiert, kern-invariant und unter menschlicher Governance."
)
GATE_FAIL_STATEMENT = (
    "Peripheral Mutation bleibt epistemisch instabil oder "
    "erodiert den Kern."
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def replay_integrity() -> float:
    return _round(min(
        _v310_replay(), _v311_replay(), _v312_replay(),
        _v313_replay(),
    ))


def core_identity() -> float:
    return _round(min(
        _v310_core(), _v311_core(), _v312_core(), _v313_core(),
    ))


def governance_identity() -> float:
    return _round(min(
        _v310_governance(), _v311_governance(),
        _v312_governance(), _v313_governance(),
    ))


def lineage_integrity() -> float:
    return _round(_v313_lineage())


def human_approval_enforcement() -> float:
    if not HUMAN_APPROVAL_REQUIRED:
        return 0.0
    return 1.0


def mutation_traceability() -> float:
    return _round(min(_v310_traceability(), _v313_gen_stability()))


def regression_survival() -> float:
    return _round(_v312_regression())


def _layer_replays() -> tuple[float, ...]:
    return (
        _v310_replay(), _v311_replay(), _v312_replay(),
        _v313_replay(),
    )


@dataclass(frozen=True)
class MutationMetrics:
    replay_integrity: float
    core_identity: float
    governance_identity: float
    lineage_integrity: float
    human_approval_enforcement: float
    mutation_traceability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "replay_integrity": self.replay_integrity,
            "core_identity": self.core_identity,
            "governance_identity": self.governance_identity,
            "lineage_integrity": self.lineage_integrity,
            "human_approval_enforcement":
                self.human_approval_enforcement,
            "mutation_traceability": self.mutation_traceability,
        }


def _core_values() -> tuple[float, ...]:
    return (
        replay_integrity(), core_identity(),
        governance_identity(), lineage_integrity(),
        human_approval_enforcement(), mutation_traceability(),
    )


def replay_stability() -> float:
    if _core_values() != _core_values():
        return 0.0
    if any(r != 1.0 for r in _layer_replays()):
        return 0.0
    return 1.0


@lru_cache(maxsize=1)
def aggregate() -> MutationMetrics:
    return MutationMetrics(
        replay_integrity=replay_integrity(),
        core_identity=core_identity(),
        governance_identity=governance_identity(),
        lineage_integrity=lineage_integrity(),
        human_approval_enforcement=human_approval_enforcement(),
        mutation_traceability=mutation_traceability(),
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
            "core_identity", m.core_identity, 1.0, "==",
            m.core_identity == 1.0),
        GateCondition(
            "governance_identity", m.governance_identity, 1.0,
            "==", m.governance_identity == 1.0),
        GateCondition(
            "lineage_integrity", m.lineage_integrity, _FLOOR,
            ">=", m.lineage_integrity >= _FLOOR),
        GateCondition(
            "human_approval_enforcement",
            m.human_approval_enforcement, 1.0, "==",
            m.human_approval_enforcement == 1.0),
        GateCondition(
            "mutation_traceability", m.mutation_traceability,
            _FLOOR, ">=", m.mutation_traceability >= _FLOOR),
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
        or m.mutation_traceability < _FLOOR
        or replay_stability() < 1.0
    ):
        return MutationClass.E_EPISTEMICALLY_UNSTABLE.value
    # D - hidden core erosion (the protected core changed)
    if m.core_identity < 1.0:
        return MutationClass.D_HIDDEN_CORE_EROSION.value
    # C - productive but drifting
    if (
        m.lineage_integrity < _FLOOR
        or m.governance_identity < 1.0
    ):
        return MutationClass.C_PRODUCTIVE_DRIFTING.value
    # A - stable peripheral evolution
    if (
        gate_passes_all()
        and m.core_identity == 1.0
        and m.human_approval_enforcement == 1.0
    ):
        return MutationClass.A_STABLE_PERIPHERAL_EVOLUTION.value
    # B - replay-safe mutation
    return MutationClass.B_REPLAY_SAFE_MUTATION.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "GateCondition",
    "MutationMetrics",
    "aggregate",
    "classify_corpus",
    "core_identity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "human_approval_enforcement",
    "lineage_integrity",
    "mutation_traceability",
    "regression_survival",
    "replay_integrity",
    "replay_stability",
]
