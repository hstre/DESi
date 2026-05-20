"""v25.0 - formal output-port schemas.

For each port, declares its required and optional sections and
its citation / metric / limitation / provenance requirements and
forbidden patterns. The schema is the contract a renderer must
satisfy; it decides nothing and renders nothing itself.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .port_types import PORT_TYPES, PortType
from .requirements import (
    BASE_PAPER_REF, FORBIDDEN_OUTPUT_PATTERNS, PROVENANCE_KINDS,
    CitationRequirement, LimitationRequirement,
    MetricRequirement, ProvenanceRequirement,
)
from .sections import SectionType as S


@dataclass(frozen=True)
class PortSchema:
    port_type: str
    required_sections: tuple[str, ...]
    optional_sections: tuple[str, ...]
    citation: CitationRequirement
    metric: MetricRequirement
    limitation: LimitationRequirement
    provenance: ProvenanceRequirement
    forbidden_patterns: tuple[str, ...]

    def is_complete(self) -> bool:
        return (
            bool(self.required_sections)
            and bool(self.forbidden_patterns)
            and bool(self.provenance.allowed_kinds)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "port_type": self.port_type,
            "required_sections": list(self.required_sections),
            "optional_sections": list(self.optional_sections),
            "citation": self.citation.to_dict(),
            "metric": self.metric.to_dict(),
            "limitation": self.limitation.to_dict(),
            "provenance": self.provenance.to_dict(),
            "forbidden_patterns": list(self.forbidden_patterns),
        }


_FULL_PROVENANCE = ProvenanceRequirement(True, PROVENANCE_KINDS)
_PAPER_CITATION = CitationRequirement(
    True, 1, (BASE_PAPER_REF,),
)


_SCHEMAS: dict[str, PortSchema] = {
    PortType.ARXIV_PAPER.value: PortSchema(
        port_type=PortType.ARXIV_PAPER.value,
        required_sections=(
            S.TITLE.value, S.ABSTRACT.value,
            S.INTRODUCTION.value, S.RELATED_WORK.value,
            S.PROBLEM_STATEMENT.value, S.METHOD.value,
            S.EXPERIMENTAL_CONDITIONS.value, S.METRICS.value,
            S.RESULTS.value, S.LIMITATIONS.value,
            S.REPRODUCIBILITY_STATEMENT.value,
            S.CONCLUSION.value, S.REFERENCES.value,
        ),
        optional_sections=(S.CITATION_MAP.value,),
        citation=_PAPER_CITATION,
        metric=MetricRequirement(True, True, True),
        limitation=LimitationRequirement(True, True),
        provenance=_FULL_PROVENANCE,
        forbidden_patterns=FORBIDDEN_OUTPUT_PATTERNS,
    ),
    PortType.WORKSHOP_NOTE.value: PortSchema(
        port_type=PortType.WORKSHOP_NOTE.value,
        required_sections=(
            S.TITLE.value, S.ABSTRACT.value, S.METHOD.value,
            S.RESULTS.value, S.LIMITATIONS.value,
            S.REFERENCES.value,
        ),
        optional_sections=(
            S.INTRODUCTION.value, S.METRICS.value,
        ),
        citation=CitationRequirement(True, 1, (BASE_PAPER_REF,)),
        metric=MetricRequirement(True, True, True),
        limitation=LimitationRequirement(True, True),
        provenance=_FULL_PROVENANCE,
        forbidden_patterns=FORBIDDEN_OUTPUT_PATTERNS,
    ),
    PortType.TECHNICAL_REPORT.value: PortSchema(
        port_type=PortType.TECHNICAL_REPORT.value,
        required_sections=(
            S.TITLE.value, S.ABSTRACT.value, S.METHOD.value,
            S.EXPERIMENTAL_CONDITIONS.value, S.METRICS.value,
            S.RESULTS.value, S.LIMITATIONS.value,
            S.REPRODUCIBILITY_STATEMENT.value,
            S.REFERENCES.value,
        ),
        optional_sections=(
            S.PROBLEM_STATEMENT.value, S.CONCLUSION.value,
        ),
        citation=_PAPER_CITATION,
        metric=MetricRequirement(True, True, True),
        limitation=LimitationRequirement(True, True),
        provenance=_FULL_PROVENANCE,
        forbidden_patterns=FORBIDDEN_OUTPUT_PATTERNS,
    ),
    PortType.CITATION_APPENDIX.value: PortSchema(
        port_type=PortType.CITATION_APPENDIX.value,
        required_sections=(
            S.TITLE.value, S.CITATION_MAP.value,
            S.LIMITATIONS.value, S.REFERENCES.value,
        ),
        optional_sections=(),
        citation=CitationRequirement(True, 1, (BASE_PAPER_REF,)),
        metric=MetricRequirement(False, True, False),
        limitation=LimitationRequirement(True, True),
        provenance=_FULL_PROVENANCE,
        forbidden_patterns=FORBIDDEN_OUTPUT_PATTERNS,
    ),
    PortType.REPRODUCIBILITY_STATEMENT.value: PortSchema(
        port_type=PortType.REPRODUCIBILITY_STATEMENT.value,
        required_sections=(
            S.TITLE.value, S.REPRODUCIBILITY_STATEMENT.value,
            S.REPLAY_HASHES.value, S.METRICS.value,
            S.LIMITATIONS.value,
        ),
        optional_sections=(S.REFERENCES.value,),
        citation=CitationRequirement(False, 0, ()),
        metric=MetricRequirement(True, True, True),
        limitation=LimitationRequirement(True, True),
        provenance=_FULL_PROVENANCE,
        forbidden_patterns=FORBIDDEN_OUTPUT_PATTERNS,
    ),
}


def port_schemas() -> tuple[PortSchema, ...]:
    return tuple(_SCHEMAS[p] for p in PORT_TYPES)


def schema_for(port_type: str) -> PortSchema:
    if port_type not in _SCHEMAS:
        raise KeyError(port_type)
    return _SCHEMAS[port_type]


def required_sections(port_type: str) -> tuple[str, ...]:
    return schema_for(port_type).required_sections


def schema_signature() -> str:
    parts = []
    for p in PORT_TYPES:
        s = _SCHEMAS[p]
        parts.append(
            f"{p}|req={','.join(s.required_sections)}|"
            f"cit={s.citation.required}:{s.citation.min_citations}|"
            f"lim={s.limitation.required}|"
            f"met={s.metric.required}|"
            f"prov={s.provenance.required}"
        )
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


__all__ = [
    "PortSchema",
    "port_schemas",
    "required_sections",
    "schema_for",
    "schema_signature",
]
