"""v34.3 - scientific rendering benchmark task definition.

Names the rendering / citation checks the run performs and the
output-port type it renders against. The checks reuse the v25 output
ports and citation governance - no new rendering logic is built.
"""
from __future__ import annotations

from desi.output_ports import PORT_TYPES

RENDERING_CHECKS: tuple[str, ...] = (
    "citation_completeness",
    "phantom_citation_detection",
    "no_naked_claims",
    "metric_derivation_visibility",
    "limitation_visibility",
    "paper_port_compliance",
)

PAPER_PORT = "arxiv_paper_port"


def paper_port() -> str:
    return PAPER_PORT if PAPER_PORT in PORT_TYPES else PORT_TYPES[0]


__all__ = [
    "PAPER_PORT",
    "RENDERING_CHECKS",
    "paper_port",
]
