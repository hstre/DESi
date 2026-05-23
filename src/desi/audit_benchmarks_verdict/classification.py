"""v37.4 - aggregate audit scores, Concept Gate, classification.

Aggregates one score per semantic-audit dimension from the v37.0-v37.3
runs (semantic risk, evidence reasoning, adversarial semantics),
checks the six-condition Concept Gate and classifies on the closed
A-E taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.audit_benchmarks import (
    connector_metrics as _connector_metrics,
    replay_stability as _connector_replay,
)
from desi.audit_benchmarks_adversarial import (
    adversarial_metrics, build_report as _adv_report,
    replay_stability as _adv_replay,
)
from desi.audit_benchmarks_reasoning import (
    build_report as _reasoning_report,
    reasoning_metrics, replay_stability as _reasoning_replay,
)
from desi.audit_benchmarks_risk import (
    build_report as _risk_report, replay_stability as _risk_replay,
    risk_metrics,
)
from desi.peripheral_mutation import (
    core_identity as _core_identity,
    replay_stability as _core_replay,
)
from desi.reasoning_benchmarks import governance_identity as _gov
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .taxonomy import AuditClass

GATE_PASS_STATEMENT = (
    "DESi besteht semantische Audit- und Finanzpruefungs-Benchmarks "
    "als replay-governed epistemic governance system."
)
GATE_FAIL_STATEMENT = (
    "DESi ist noch nicht robust genug fuer semantische Audit-/"
    "Pruefungsumgebungen."
)

_SCORE_FLOOR = 0.85
_FRAGILE_FLOOR = 0.70


def _mean(d: dict[str, float]) -> float:
    return round(sum(d.values()) / len(d), 6) if d else 0.0


def semantic_audit_score() -> float:
    return _mean(risk_metrics())


def evidence_reasoning_score() -> float:
    return _mean(reasoning_metrics())


def semantic_conflict_score() -> float:
    return _mean(adversarial_metrics())


def governance_identity() -> float:
    return round(min(
        _risk_report().governance_identity,
        _reasoning_report().governance_identity,
        _adv_report().governance_identity,
        _connector_metrics()["governance_identity"],
        _gov(),
    ), 6)


def core_identity() -> float:
    return round(_core_identity(), 6)


def _run_halts() -> tuple[bool, ...]:
    return (
        _risk_report().halt, _reasoning_report().halt,
        _adv_report().halt,
    )


def replay_stability() -> float:
    layers = (
        _connector_replay(), _risk_replay(), _reasoning_replay(),
        _adv_replay(), _core_replay(),
    )
    return 1.0 if all(r == 1.0 for r in layers) else 0.0


@dataclass(frozen=True)
class AuditMetrics:
    semantic_audit_score: float
    evidence_reasoning_score: float
    semantic_conflict_score: float
    governance_identity: float
    core_identity: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "semantic_audit_score": self.semantic_audit_score,
            "evidence_reasoning_score": self.evidence_reasoning_score,
            "semantic_conflict_score": self.semantic_conflict_score,
            "governance_identity": self.governance_identity,
            "core_identity": self.core_identity,
            "replay_stability": self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> AuditMetrics:
    return AuditMetrics(
        semantic_audit_score=semantic_audit_score(),
        evidence_reasoning_score=evidence_reasoning_score(),
        semantic_conflict_score=semantic_conflict_score(),
        governance_identity=governance_identity(),
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
            "semantic_audit_score", m.semantic_audit_score,
            _SCORE_FLOOR, ">=", m.semantic_audit_score >= _SCORE_FLOOR),
        GateCondition(
            "evidence_reasoning_score", m.evidence_reasoning_score,
            _SCORE_FLOOR, ">=",
            m.evidence_reasoning_score >= _SCORE_FLOOR),
        GateCondition(
            "semantic_conflict_score", m.semantic_conflict_score,
            _SCORE_FLOOR, ">=",
            m.semantic_conflict_score >= _SCORE_FLOOR),
        GateCondition(
            "governance_identity", m.governance_identity, 1.0, "==",
            m.governance_identity == 1.0),
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


def _scores() -> tuple[float, ...]:
    m = aggregate()
    return (
        m.semantic_audit_score, m.evidence_reasoning_score,
        m.semantic_conflict_score,
    )


def classify_corpus() -> str:
    """Priority-ordered classification (most severe first)."""
    m = aggregate()
    if (
        m.replay_stability < 1.0
        or m.core_identity < 1.0
        or m.governance_identity < 1.0
    ):
        return AuditClass.E_AUDIT_UNSAFE.value
    if any(s < _FRAGILE_FLOOR for s in _scores()) or any(_run_halts()):
        return AuditClass.D_SEMANTICALLY_FRAGILE.value
    if gate_passes_all():
        return AuditClass.A_SEMANTIC_AUDIT_ROBUST.value
    if (
        m.core_identity == 1.0
        and m.governance_identity == 1.0
        and m.replay_stability == 1.0
        and all(s >= _FRAGILE_FLOOR for s in _scores())
    ):
        return AuditClass.B_AUDIT_COMPATIBLE.value
    return AuditClass.C_PARTIALLY_ROBUST.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "AuditMetrics",
    "GateCondition",
    "aggregate",
    "classify_corpus",
    "core_identity",
    "evidence_reasoning_score",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "replay_stability",
    "semantic_audit_score",
    "semantic_conflict_score",
]
