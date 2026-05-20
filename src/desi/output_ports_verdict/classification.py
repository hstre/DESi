"""v25.4 - aggregate metrics, Concept Gate, classification.

Pulls one signal per gate dimension from the v25 layers (v25.0
schema, v25.1 arXiv port, v25.2 citation governance, v25.3
multi-port), checks the six-condition Concept Gate, and
classifies the output-port system on the closed A-E taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.output_ports import (
    limitation_requirement_visibility, port_schema_coverage,
    replay_stability as _v250_replay,
    required_section_visibility,
)
from desi.output_ports_arxiv import (
    citation_completeness, metric_definition_coverage,
    paper_forbidden_hits,
    replay_stability as _v251_replay,
    result_derivation_visibility,
)
from desi.output_ports_citation import (
    citation_traceability, claim_reference_alignment,
    missing_citations, phantom_citation_detection,
    phantom_citations, reference_usage_integrity,
    replay_stability as _v252_replay,
)
from desi.output_ports_multi import (
    corpus_forbidden_hits, cross_port_claim_consistency,
    cross_port_metric_consistency, limitation_preservation,
    replay_stability as _v253_replay,
)

from .taxonomy import PortClass

GATE_PASS_STATEMENT = (
    "DESi kann wissenschaftliche Dokumente als zitierfaehige, "
    "graph-gebundene, replay-stabile Output-Ports erzeugen."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt wissenschaftlich ausgabeinstabil."
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def port_schema_integrity() -> float:
    return _round(min(
        port_schema_coverage(),
        required_section_visibility(),
        limitation_requirement_visibility(),
    ))


def citation_integrity() -> float:
    return _round(min(
        citation_completeness(),
        phantom_citation_detection(),
        claim_reference_alignment(),
        reference_usage_integrity(),
        citation_traceability(),
    ))


def result_traceability() -> float:
    return _round(min(
        result_derivation_visibility(),
        metric_definition_coverage(),
    ))


def cross_port_consistency() -> float:
    return _round(min(
        cross_port_claim_consistency(),
        cross_port_metric_consistency(),
    ))


def no_naked_claims() -> float:
    """Fraction of the naked-claim safety checks that pass: no
    underived numbers, no forbidden output, no phantom or
    missing citations, in [0, 1]."""
    checks = [
        result_derivation_visibility() == 1.0,
        not paper_forbidden_hits(),
        not corpus_forbidden_hits(),
        not phantom_citations(),
        not missing_citations(),
    ]
    return _round(sum(1 for c in checks if c) / len(checks))


def _layer_replays() -> tuple[float, ...]:
    return (
        _v250_replay(), _v251_replay(), _v252_replay(),
        _v253_replay(),
    )


@dataclass(frozen=True)
class PortMetrics:
    port_schema_integrity: float
    citation_integrity: float
    result_traceability: float
    cross_port_consistency: float
    no_naked_claims: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "port_schema_integrity": self.port_schema_integrity,
            "citation_integrity": self.citation_integrity,
            "result_traceability": self.result_traceability,
            "cross_port_consistency":
                self.cross_port_consistency,
            "no_naked_claims": self.no_naked_claims,
            "replay_stability": self.replay_stability,
        }


def _core_values() -> tuple[float, float, float, float, float]:
    return (
        port_schema_integrity(),
        citation_integrity(),
        result_traceability(),
        cross_port_consistency(),
        no_naked_claims(),
    )


def replay_stability() -> float:
    if _core_values() != _core_values():
        return 0.0
    if any(r != 1.0 for r in _layer_replays()):
        return 0.0
    return 1.0


@lru_cache(maxsize=1)
def aggregate() -> PortMetrics:
    psi, ci, rt, cpc, nnc = _core_values()
    return PortMetrics(
        port_schema_integrity=psi,
        citation_integrity=ci,
        result_traceability=rt,
        cross_port_consistency=cpc,
        no_naked_claims=nnc,
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
            "port_schema_integrity", m.port_schema_integrity,
            _FLOOR, ">=", m.port_schema_integrity >= _FLOOR),
        GateCondition(
            "citation_integrity", m.citation_integrity, _FLOOR,
            ">=", m.citation_integrity >= _FLOOR),
        GateCondition(
            "result_traceability", m.result_traceability,
            _FLOOR, ">=", m.result_traceability >= _FLOOR),
        GateCondition(
            "cross_port_consistency", m.cross_port_consistency,
            _FLOOR, ">=", m.cross_port_consistency >= _FLOOR),
        GateCondition(
            "no_naked_claims", m.no_naked_claims, _FLOOR, ">=",
            m.no_naked_claims >= _FLOOR),
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
    # E - unsafe renderer (naked claims / forbidden output)
    if m.no_naked_claims < _FLOOR:
        return PortClass.E_UNSAFE_RENDERER.value
    # D - citation fragile
    if m.citation_integrity < _FLOOR:
        return PortClass.D_CITATION_FRAGILE.value
    # C - format stable but incomplete
    if (
        m.port_schema_integrity < _FLOOR
        or m.result_traceability < _FLOOR
    ):
        return PortClass.C_FORMAT_STABLE_INCOMPLETE.value
    # A - publication-ready
    if (
        gate_passes_all()
        and m.cross_port_consistency >= _FLOOR
        and m.replay_stability == 1.0
    ):
        return PortClass.A_PUBLICATION_READY.value
    # B - traceable output
    return PortClass.B_TRACEABLE.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "GateCondition",
    "PortMetrics",
    "aggregate",
    "citation_integrity",
    "classify_corpus",
    "cross_port_consistency",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "no_naked_claims",
    "port_schema_integrity",
    "replay_stability",
    "result_traceability",
]
