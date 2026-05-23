"""DESi v25.1 - arXiv Paper Port (read-only).

Renders an arXiv-compatible short paper deterministically from
DESi's epistemic state. All 13 mandated sections are present,
the base paper (Rentschler and Roberts, 2025; arXiv:2501.14176)
is cited, every metric is defined, every number is derived from
a named sprint, and the document carries no forbidden term. A
provenance-bound export, not free text generation.
"""
from __future__ import annotations

from .arxiv_port import (
    PORT, missing_sections, render, required_sections,
    section_completeness,
)
from .citation_rules import (
    ExternalClaim, base_paper_cited, cited_reference_keys,
    citation_completeness, external_claims, phantom_citations,
    unreferenced_external_claims, unused_references,
)
from .reference_manager import (
    Reference, is_registered, reference_keys, references,
    references_body, references_section, resolve,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_INCOMPLETE,
    VERDICT_TRACEABLE, V251Report, build_arxiv_artifact,
    build_report, metric_definition_coverage,
    paper_forbidden_hits, replay_stability,
    result_derivation_visibility,
)
from .section_builder import (
    ResultLine, build_section, build_sections, result_lines,
)


__all__ = [
    "PORT",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_INCOMPLETE",
    "VERDICT_TRACEABLE",
    "ExternalClaim",
    "Reference",
    "ResultLine",
    "V251Report",
    "base_paper_cited",
    "build_arxiv_artifact",
    "build_report",
    "build_section",
    "build_sections",
    "citation_completeness",
    "cited_reference_keys",
    "external_claims",
    "is_registered",
    "metric_definition_coverage",
    "missing_sections",
    "paper_forbidden_hits",
    "phantom_citations",
    "reference_keys",
    "references",
    "references_body",
    "references_section",
    "render",
    "replay_stability",
    "required_sections",
    "resolve",
    "result_derivation_visibility",
    "result_lines",
    "section_completeness",
    "unreferenced_external_claims",
    "unused_references",
]
