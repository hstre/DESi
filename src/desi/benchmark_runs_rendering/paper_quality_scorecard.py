"""v34.3 - paper-port compliance and limitation visibility.

Reads the v25 output-port schema to confirm the rendered paper port
requires citations, surfaces limitations, exposes every required
section and derives its metrics - the structural quality gates of a
benchmark-ready scientific document.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.output_ports import (
    citation_requirement_visibility, limitation_requirement_visibility,
    port_schema_coverage, required_section_visibility,
)

from .citation_runner import (
    citation_completeness, result_traceability, usage_integrity,
)
from .phantom_citation_check import phantom_citation_resistance


def limitation_visibility() -> float:
    return round(limitation_requirement_visibility(), 6)


def metric_derivation_visibility() -> float:
    """Numbers are derived/traceable: the port requires metric
    provenance and citations resolve."""
    return round(min(
        citation_requirement_visibility(), result_traceability(),
    ), 6)


def paper_port_compliance() -> float:
    return round(min(
        citation_requirement_visibility(),
        limitation_requirement_visibility(),
        required_section_visibility(),
        port_schema_coverage(),
    ), 6)


@dataclass(frozen=True)
class PaperQualityScorecard:
    phantom_citation_resistance: float
    citation_completeness: float
    result_traceability: float
    limitation_visibility: float
    metric_derivation_visibility: float
    paper_port_compliance: float
    usage_integrity: float

    def to_dict(self) -> dict[str, object]:
        return {
            "phantom_citation_resistance":
                self.phantom_citation_resistance,
            "citation_completeness": self.citation_completeness,
            "result_traceability": self.result_traceability,
            "limitation_visibility": self.limitation_visibility,
            "metric_derivation_visibility":
                self.metric_derivation_visibility,
            "paper_port_compliance": self.paper_port_compliance,
            "usage_integrity": self.usage_integrity,
        }


def paper_quality_scorecard() -> PaperQualityScorecard:
    return PaperQualityScorecard(
        phantom_citation_resistance=phantom_citation_resistance(),
        citation_completeness=citation_completeness(),
        result_traceability=result_traceability(),
        limitation_visibility=limitation_visibility(),
        metric_derivation_visibility=metric_derivation_visibility(),
        paper_port_compliance=paper_port_compliance(),
        usage_integrity=usage_integrity(),
    )


__all__ = [
    "PaperQualityScorecard",
    "limitation_visibility",
    "metric_derivation_visibility",
    "paper_port_compliance",
    "paper_quality_scorecard",
]
