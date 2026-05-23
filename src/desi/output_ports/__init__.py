"""DESi v25.0 - Output Port Schema (read-only).

Formal schemas for DESi's scientific output ports. An output
port is a deterministic interface between the epistemic state
and a document format - not free text generation. Each port
declares its required / optional sections and its citation,
metric, limitation and provenance requirements, together with
forbidden output patterns. The central rule: no central claim
may be naked - every one needs at least one provenance kind.
"""
from __future__ import annotations

from .port_types import PORT_TYPES, PortType, is_port_type
from .report import (
    REPORT_VERDICTS, VERDICT_FORMAL, VERDICT_HALT,
    VERDICT_INCOMPLETE, V250Report, build_report,
    build_schema_artifact, citation_requirement_visibility,
    limitation_requirement_visibility, port_schema_coverage,
    replay_stability, required_section_visibility,
)
from .requirements import (
    BASE_PAPER_CITATION, BASE_PAPER_REF,
    FORBIDDEN_OUTPUT_PATTERNS, PROVENANCE_KINDS,
    CitationRequirement, LimitationRequirement,
    MetricRequirement, ProvenanceRequirement,
)
from .schema import (
    PortSchema, port_schemas, required_sections, schema_for,
    schema_signature,
)
from .sections import (
    SECTION_TYPES, SectionType, is_section_type, section_title,
)


__all__ = [
    "BASE_PAPER_CITATION",
    "BASE_PAPER_REF",
    "FORBIDDEN_OUTPUT_PATTERNS",
    "PORT_TYPES",
    "PROVENANCE_KINDS",
    "REPORT_VERDICTS",
    "SECTION_TYPES",
    "VERDICT_FORMAL",
    "VERDICT_HALT",
    "VERDICT_INCOMPLETE",
    "CitationRequirement",
    "LimitationRequirement",
    "MetricRequirement",
    "PortSchema",
    "PortType",
    "ProvenanceRequirement",
    "SectionType",
    "V250Report",
    "build_report",
    "build_schema_artifact",
    "citation_requirement_visibility",
    "is_port_type",
    "is_section_type",
    "limitation_requirement_visibility",
    "port_schema_coverage",
    "port_schemas",
    "replay_stability",
    "required_section_visibility",
    "required_sections",
    "schema_for",
    "schema_signature",
    "section_title",
]
