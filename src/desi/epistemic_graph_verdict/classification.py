"""v24.4 - aggregate metrics, Concept Gate, classification.

Pulls one signal per gate dimension from the v24 layers (v24.0
schema, v24.1 export, v24.2 cache, v24.3 queries), checks the
six-condition Concept Gate, and classifies the epistemic graph
layer on the closed A-E taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.epistemic_graph import (
    lineage_visibility as _graph_lineage_visibility,
    replay_stability as _graph_replay_stability,
)
from desi.epistemic_graph_export import (
    canonical_preservation as _export_canonical,
    export_determinism as _export_determinism,
    governance_independence as _export_governance_independence,
    replay_integrity as _export_replay_integrity,
)
from desi.epistemic_graph_cache import (
    cache_validity as _cache_validity,
    invalidation_integrity as _cache_invalidation_integrity,
    replay_stability as _cache_replay_stability,
    stale_detection as _cache_stale_detection,
)
from desi.epistemic_graph_queries import (
    lineage_integrity as _query_lineage_integrity,
    replay_stability as _query_replay_stability,
    scientific_traceability as _query_traceability,
)

from .taxonomy import GraphClass

GATE_PASS_STATEMENT = (
    "DESi kann replay-validiertes epistemisches Gedaechtnis "
    "besitzen ohne versteckte Optimierungsautoritaet oder "
    "nichtdeterministischen Drift einzufuehren."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt epistemisch instabil gegenueber persistentem "
    "State."
)

_FLOOR = 0.90
_REPLAY_INTEGRITY_FLOOR = 0.95
_GOV_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class GraphMetrics:
    replay_integrity: float
    lineage_visibility: float
    cache_validity: float
    traceability: float
    governance_independence: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "replay_integrity": self.replay_integrity,
            "lineage_visibility": self.lineage_visibility,
            "cache_validity": self.cache_validity,
            "traceability": self.traceability,
            "governance_independence":
                self.governance_independence,
            "replay_stability": self.replay_stability,
        }


def _layer_replays() -> tuple[float, ...]:
    return (
        _graph_replay_stability(),
        _cache_replay_stability(),
        _query_replay_stability(),
        _export_determinism(),
        _export_canonical(),
    )


def _core_values() -> tuple[float, float, float, float, float]:
    return (
        _export_replay_integrity(),
        _graph_lineage_visibility(),
        _cache_validity(),
        _query_traceability(),
        _export_governance_independence(),
    )


def replay_stability() -> float:
    """1.0 iff the core metric tuple is stable across a second
    computation and every v24 layer is replay-stable."""
    if _core_values() != _core_values():
        return 0.0
    if any(r != 1.0 for r in _layer_replays()):
        return 0.0
    return 1.0


@lru_cache(maxsize=1)
def aggregate() -> GraphMetrics:
    ri, lv, cv, tr, gi = _core_values()
    return GraphMetrics(
        replay_integrity=ri,
        lineage_visibility=lv,
        cache_validity=cv,
        traceability=tr,
        governance_independence=gi,
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
            "replay_integrity", m.replay_integrity,
            _REPLAY_INTEGRITY_FLOOR, ">=",
            m.replay_integrity >= _REPLAY_INTEGRITY_FLOOR),
        GateCondition(
            "lineage_visibility", m.lineage_visibility, _FLOOR,
            ">=", m.lineage_visibility >= _FLOOR),
        GateCondition(
            "cache_validity", m.cache_validity, _FLOOR, ">=",
            m.cache_validity >= _FLOOR),
        GateCondition(
            "traceability", m.traceability, _FLOOR, ">=",
            m.traceability >= _FLOOR),
        GateCondition(
            "governance_independence",
            m.governance_independence, _GOV_FLOOR, ">=",
            m.governance_independence >= _GOV_FLOOR),
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


def classify_corpus() -> str:
    """Priority-ordered classification (most severe first)."""
    m = aggregate()
    # E - epistemically fragmented
    if (
        m.lineage_visibility < _FLOOR
        or m.traceability < _FLOOR
        or _query_lineage_integrity() < 1.0
        or m.replay_integrity < _REPLAY_INTEGRITY_FLOOR
    ):
        return GraphClass.E_FRAGMENTED.value
    # D - stale-state drift / governance leak
    if (
        m.cache_validity < _FLOOR
        or m.governance_independence < _GOV_FLOOR
        or _cache_stale_detection() < _FLOOR
        or _cache_invalidation_integrity() < _FLOOR
    ):
        return GraphClass.D_STALE_DRIFTED.value
    # A - replay-governed (top)
    if (
        gate_passes_all()
        and m.replay_stability == 1.0
        and m.replay_integrity >= _REPLAY_INTEGRITY_FLOOR
        and m.governance_independence >= _GOV_FLOOR
    ):
        return GraphClass.A_REPLAY_GOVERNED.value
    # B - lineage visible
    if m.lineage_visibility >= _FLOOR and m.traceability >= _FLOOR:
        return GraphClass.B_LINEAGE_VISIBLE.value
    # C - conflict-rich but stable
    return GraphClass.C_CONFLICT_RICH_STABLE.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "GateCondition",
    "GraphMetrics",
    "aggregate",
    "classify_corpus",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "replay_stability",
]
