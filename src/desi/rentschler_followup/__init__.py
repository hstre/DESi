"""DESi v26 - Rentschler Follow-Up Paper via the arXiv Output
Port (read-only).

Renders a directly-connectable, citeable, traceable short paper
for the base paper's authors through the v25 arXiv output port.
It anchors to Section 4.6 of the base paper, describes DESi only
as a local read-only governance layer (no mythology), derives
every number, references every external claim, and is gated by a
six-condition Concept Gate. If the gate passes, the paper is
shippable to Rentschler.
"""
from __future__ import annotations

from .paper import (
    missing_sections, render, required_sections,
    section_completeness,
)
from .report import (
    GATE_PASS_STATEMENT, REPORT_VERDICTS, VERDICT_HALT,
    VERDICT_NOT_READY, VERDICT_SHIPPABLE, GateCondition,
    V26Report, base_paper_in_paper, build_followup_artifact,
    build_report, citation_integrity, desi_mechanism_clarity,
    gate_conditions, gate_failing_conditions, gate_passes_all,
    no_naked_claims, paper_alignment, paper_forbidden_hits,
    replay_stability, result_traceability,
)
from .sections import (
    CORE_THESIS, MECHANISM_MARKERS, SECTION_ORDER,
    build_section, build_sections, section_title,
)


__all__ = [
    "CORE_THESIS",
    "GATE_PASS_STATEMENT",
    "MECHANISM_MARKERS",
    "REPORT_VERDICTS",
    "SECTION_ORDER",
    "VERDICT_HALT",
    "VERDICT_NOT_READY",
    "VERDICT_SHIPPABLE",
    "GateCondition",
    "V26Report",
    "base_paper_in_paper",
    "build_followup_artifact",
    "build_report",
    "build_section",
    "build_sections",
    "citation_integrity",
    "desi_mechanism_clarity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "missing_sections",
    "no_naked_claims",
    "paper_alignment",
    "paper_forbidden_hits",
    "render",
    "replay_stability",
    "required_sections",
    "result_traceability",
    "section_completeness",
    "section_title",
]
