"""v27.4 - aggregate metrics, Concept Gate, classification.

Pulls one signal per gate dimension from the v27 layers (v27.0
topology, v27.1 claim graph, v27.2 convergence, v27.3 ecology),
checks the six-condition Concept Gate, and classifies the
research harvester on the closed A-E taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.research_harvester import (
    claim_extraction_consistency as _v270_extraction,
    open_question_visibility as _v270_open_q,
    provenance_integrity as _v270_provenance,
    replay_stability as _v270_replay,
)
from desi.research_claim_graph import (
    conflict_visibility as _v271_conflict,
    graph_connectivity as _v271_connectivity,
    lineage_integrity as _v271_lineage,
    open_problem_visibility as _v271_open_p,
    replay_stability as _v271_replay,
)
from desi.research_convergence import (
    conflict_structure_visibility as _v272_conflict,
    epistemic_neutrality as _v272_neutrality,
    replay_stability as _v272_replay,
)
from desi.research_ecology import (
    conflict_preservation as _v273_conflict,
    fragility_visibility as _v273_fragility,
    open_question_preservation as _v273_open_q,
    plurality_preservation as _v273_plurality,
    replay_stability as _v273_replay,
)

from .taxonomy import HarvesterClass

GATE_PASS_STATEMENT = (
    "DESi kann wissenschaftliche Forschung als replay-"
    "validierten epistemischen Claim-Raum modellieren."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt epistemisch instabil gegenueber dynamischen "
    "Forschungsraeumen."
)

_FLOOR = 0.90
_NEUTRALITY_FLOOR = 0.95
_INTEGRITY_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def claim_extraction_consistency() -> float:
    return _round(_v270_extraction())


def lineage_visibility() -> float:
    return _round(min(_v270_provenance(), _v271_lineage()))


def open_question_visibility() -> float:
    return _round(min(
        _v270_open_q(), _v271_open_p(), _v273_open_q(),
    ))


def conflict_preservation() -> float:
    return _round(min(
        _v271_conflict(), _v272_conflict(), _v273_conflict(),
    ))


def epistemic_neutrality() -> float:
    return _round(_v272_neutrality())


def graph_integrity() -> float:
    return _round(min(_v271_lineage(), _v271_connectivity()))


def _layer_replays() -> tuple[float, ...]:
    return (
        _v270_replay(), _v271_replay(), _v272_replay(),
        _v273_replay(),
    )


@dataclass(frozen=True)
class HarvesterMetrics:
    claim_extraction_consistency: float
    lineage_visibility: float
    open_question_visibility: float
    conflict_preservation: float
    epistemic_neutrality: float
    graph_integrity: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_extraction_consistency":
                self.claim_extraction_consistency,
            "lineage_visibility": self.lineage_visibility,
            "open_question_visibility":
                self.open_question_visibility,
            "conflict_preservation": self.conflict_preservation,
            "epistemic_neutrality": self.epistemic_neutrality,
            "graph_integrity": self.graph_integrity,
            "replay_stability": self.replay_stability,
        }


def _core_values() -> tuple[float, ...]:
    return (
        claim_extraction_consistency(), lineage_visibility(),
        open_question_visibility(), conflict_preservation(),
        epistemic_neutrality(), graph_integrity(),
    )


def replay_stability() -> float:
    if _core_values() != _core_values():
        return 0.0
    if any(r != 1.0 for r in _layer_replays()):
        return 0.0
    return 1.0


@lru_cache(maxsize=1)
def aggregate() -> HarvesterMetrics:
    return HarvesterMetrics(
        claim_extraction_consistency=
            claim_extraction_consistency(),
        lineage_visibility=lineage_visibility(),
        open_question_visibility=open_question_visibility(),
        conflict_preservation=conflict_preservation(),
        epistemic_neutrality=epistemic_neutrality(),
        graph_integrity=graph_integrity(),
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
            "claim_extraction_consistency",
            m.claim_extraction_consistency, _FLOOR, ">=",
            m.claim_extraction_consistency >= _FLOOR),
        GateCondition(
            "lineage_visibility", m.lineage_visibility, _FLOOR,
            ">=", m.lineage_visibility >= _FLOOR),
        GateCondition(
            "conflict_preservation", m.conflict_preservation,
            _FLOOR, ">=", m.conflict_preservation >= _FLOOR),
        GateCondition(
            "epistemic_neutrality", m.epistemic_neutrality,
            _NEUTRALITY_FLOOR, ">=",
            m.epistemic_neutrality >= _NEUTRALITY_FLOOR),
        GateCondition(
            "graph_integrity", m.graph_integrity,
            _INTEGRITY_FLOOR, ">=",
            m.graph_integrity >= _INTEGRITY_FLOOR),
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
    # E - epistemically collapsed (lineage / graph integrity)
    if (
        m.lineage_visibility < _FLOOR
        or m.graph_integrity < _INTEGRITY_FLOOR
        or m.replay_stability < 1.0
    ):
        return HarvesterClass.E_EPISTEMICALLY_COLLAPSED.value
    # D - hype-fragile / authority leak
    if (
        m.epistemic_neutrality < _NEUTRALITY_FLOOR
        or _v273_fragility() < _FLOOR
        or _v273_plurality() < _FLOOR
    ):
        return HarvesterClass.D_HYPE_FRAGILE.value
    # C - convergent but incomplete
    if (
        m.claim_extraction_consistency < _FLOOR
        or m.open_question_visibility < _FLOOR
    ):
        return HarvesterClass.C_CONVERGENT_INCOMPLETE.value
    # A - epistemically connected
    if (
        gate_passes_all()
        and m.conflict_preservation >= _FLOOR
        and _v271_connectivity() >= _FLOOR
    ):
        return HarvesterClass.A_EPISTEMICALLY_CONNECTED.value
    # B - conflict-rich but stable
    return HarvesterClass.B_CONFLICT_RICH_STABLE.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "GateCondition",
    "HarvesterMetrics",
    "aggregate",
    "claim_extraction_consistency",
    "classify_corpus",
    "conflict_preservation",
    "epistemic_neutrality",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "graph_integrity",
    "lineage_visibility",
    "open_question_visibility",
    "replay_stability",
]
