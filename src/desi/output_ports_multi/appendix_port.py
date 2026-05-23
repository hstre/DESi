"""v25.3 - citation appendix and reproducibility statement ports.

Two short, specialised exports rendered from the same epistemic
state: a citation appendix (citation-as-edge map plus the
reference list) and a reproducibility statement (replay hashes,
metric definitions and limitations).
"""
from __future__ import annotations

from desi.output_ports import PortType

from .renderer import render_port

CITATION_APPENDIX = PortType.CITATION_APPENDIX.value
REPRODUCIBILITY_STATEMENT = (
    PortType.REPRODUCIBILITY_STATEMENT.value
)


def render_citation_appendix() -> str:
    return render_port(CITATION_APPENDIX)


def render_reproducibility_statement() -> str:
    return render_port(REPRODUCIBILITY_STATEMENT)


__all__ = [
    "CITATION_APPENDIX",
    "REPRODUCIBILITY_STATEMENT",
    "render_citation_appendix",
    "render_reproducibility_statement",
]
