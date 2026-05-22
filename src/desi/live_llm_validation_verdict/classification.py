"""v38.4 - aggregate live scores, Concept Gate, classification.

Aggregates one score per dimension from the v38.0-v38.3 live runs
(Granite, DeepSeek, routing) over REAL captured OpenRouter outputs,
checks the six-condition Concept Gate and classifies on the closed
A-E taxonomy. Hallucination containment combines Granite's low
hallucination rate with DeepSeek's full hallucination visibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.live_llm_validation import governance_identity as _conn_gov
from desi.live_llm_validation import (
    replay_stability as _conn_replay,
)
from desi.live_llm_validation_deepseek import (
    build_report as _ds_report, deepseek_metrics,
    governance_stability as _ds_gov, hallucination_visibility,
    replay_stability as _ds_replay,
)
from desi.live_llm_validation_granite import (
    build_report as _gr_report, granite_metrics, hallucination_rate,
    replay_stability as _gr_replay,
)
from desi.live_llm_validation_routing import (
    build_report as _rt_report, governance_stability as _rt_gov,
    quality_preservation, replay_stability as _rt_replay,
    routing_cost_reduction,
)
from desi.peripheral_mutation import (
    core_identity as _core_identity,
    replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .taxonomy import LiveClass

GATE_PASS_STATEMENT = (
    "DESi besteht echte OpenRouter-basierte Live-LLM-Validierung als "
    "replay-governed epistemic governance system."
)
GATE_FAIL_STATEMENT = (
    "DESi ist noch nicht robust genug fuer echte "
    "Live-LLM-Governance."
)

_GRANITE_FLOOR = 0.80
_DEEPSEEK_FLOOR = 0.85
_ROUTING_FLOOR = 0.85
_HALLUCINATION_FLOOR = 0.90


def _mean(xs: list[float]) -> float:
    return round(sum(xs) / len(xs), 6) if xs else 0.0


def granite_score() -> float:
    m = granite_metrics()
    return _mean([
        m["granite_success_rate"], m["schema_compliance"],
        1.0 - m["hallucination_rate"], m["cost_efficiency"],
        m["replay_stability"],
    ])


def deepseek_score() -> float:
    return _mean(list(deepseek_metrics().values()))


def routing_score() -> float:
    return _mean([
        routing_cost_reduction(), quality_preservation(),
        _rt_gov(), _rt_replay(),
    ])


def governance_identity() -> float:
    return round(min(
        _conn_gov(), _ds_gov(), _rt_gov(),
        _gr_report().governance_identity,
    ), 6)


def hallucination_containment() -> float:
    """Granite's hallucinations stay low and DeepSeek's are always
    visible; containment is the lower of the two."""
    return round(min(
        1.0 - hallucination_rate(), hallucination_visibility(),
    ), 6)


def _run_halts() -> tuple[bool, ...]:
    return (
        _gr_report().halt, _ds_report().halt, _rt_report().halt,
    )


def replay_stability() -> float:
    layers = (
        _conn_replay(), _gr_replay(), _ds_replay(), _rt_replay(),
        _core_replay(),
    )
    return 1.0 if all(r == 1.0 for r in layers) else 0.0


@dataclass(frozen=True)
class LiveMetrics:
    granite_score: float
    deepseek_score: float
    routing_score: float
    governance_identity: float
    hallucination_containment: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "granite_score": self.granite_score,
            "deepseek_score": self.deepseek_score,
            "routing_score": self.routing_score,
            "governance_identity": self.governance_identity,
            "hallucination_containment": self.hallucination_containment,
            "replay_stability": self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> LiveMetrics:
    return LiveMetrics(
        granite_score=granite_score(),
        deepseek_score=deepseek_score(),
        routing_score=routing_score(),
        governance_identity=governance_identity(),
        hallucination_containment=hallucination_containment(),
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
            "granite_score", m.granite_score, _GRANITE_FLOOR, ">=",
            m.granite_score >= _GRANITE_FLOOR),
        GateCondition(
            "deepseek_score", m.deepseek_score, _DEEPSEEK_FLOOR, ">=",
            m.deepseek_score >= _DEEPSEEK_FLOOR),
        GateCondition(
            "routing_score", m.routing_score, _ROUTING_FLOOR, ">=",
            m.routing_score >= _ROUTING_FLOOR),
        GateCondition(
            "governance_identity", m.governance_identity, 1.0, "==",
            m.governance_identity == 1.0),
        GateCondition(
            "hallucination_containment", m.hallucination_containment,
            _HALLUCINATION_FLOOR, ">=",
            m.hallucination_containment >= _HALLUCINATION_FLOOR),
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
    if m.replay_stability < 1.0 or m.governance_identity < 1.0:
        return LiveClass.E_GOVERNANCE_UNSAFE.value
    if m.hallucination_containment < _HALLUCINATION_FLOOR or any(
        _run_halts()
    ):
        return LiveClass.D_LIVE_UNSTABLE.value
    if gate_passes_all():
        return LiveClass.A_LIVE_VALIDATED.value
    if (
        m.governance_identity == 1.0
        and m.replay_stability == 1.0
        and m.routing_score >= _ROUTING_FLOOR
    ):
        return LiveClass.B_STABLE_ROUTING.value
    return LiveClass.C_PARTIALLY_ROBUST.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "GateCondition",
    "LiveMetrics",
    "aggregate",
    "classify_corpus",
    "deepseek_score",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "governance_identity",
    "granite_score",
    "hallucination_containment",
    "replay_stability",
    "routing_score",
]
