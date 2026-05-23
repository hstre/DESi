"""v25.0 - closed set of scientific output ports.

An output port is not a prompt and not free text generation: it
is a deterministic interface between the epistemic state (graph,
artifacts, claims, metrics, references, replay hashes) and a
concrete document format.
"""
from __future__ import annotations

from enum import Enum


class PortType(Enum):
    ARXIV_PAPER = "arxiv_paper_port"
    WORKSHOP_NOTE = "workshop_note_port"
    TECHNICAL_REPORT = "technical_report_port"
    CITATION_APPENDIX = "citation_appendix_port"
    REPRODUCIBILITY_STATEMENT = "reproducibility_statement_port"


PORT_TYPES: tuple[str, ...] = tuple(p.value for p in PortType)
_PORT_VALUES: frozenset[str] = frozenset(PORT_TYPES)


def is_port_type(value: str) -> bool:
    return value in _PORT_VALUES


__all__ = [
    "PORT_TYPES",
    "PortType",
    "is_port_type",
]
