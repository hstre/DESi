"""DESi v25.3 - Multi-Port Rendering (read-only).

Renders the same epistemic state into several scientific
document formats - arXiv paper, workshop note, technical report,
citation appendix and reproducibility statement - from one
shared section provider. Claims, numbers, references and
limitations are byte-identical across ports; only the title and
the included-section set differ by format.
"""
from __future__ import annotations

from .appendix_port import (
    CITATION_APPENDIX, REPRODUCIBILITY_STATEMENT,
    render_citation_appendix, render_reproducibility_statement,
)
from .renderer import (
    all_renders, canonical_body, port_title, render_port,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_INCONSISTENT,
    VERDICT_PUBLISHABLE, V253Report, build_multi_port_artifact,
    build_report, corpus_forbidden_hits,
    cross_port_claim_consistency, cross_port_metric_consistency,
    format_validity, limitation_preservation, replay_stability,
)
from .technical_report_port import render as render_technical_report
from .workshop_port import render as render_workshop_note


__all__ = [
    "CITATION_APPENDIX",
    "REPORT_VERDICTS",
    "REPRODUCIBILITY_STATEMENT",
    "VERDICT_HALT",
    "VERDICT_INCONSISTENT",
    "VERDICT_PUBLISHABLE",
    "V253Report",
    "all_renders",
    "build_multi_port_artifact",
    "build_report",
    "canonical_body",
    "corpus_forbidden_hits",
    "cross_port_claim_consistency",
    "cross_port_metric_consistency",
    "format_validity",
    "limitation_preservation",
    "port_title",
    "render_citation_appendix",
    "render_port",
    "render_reproducibility_statement",
    "render_technical_report",
    "render_workshop_note",
    "replay_stability",
]
