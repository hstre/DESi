"""DESi v22.2 - Scientific Rendering Layer (read-only).

DESi assembles a short, sober, sandbox-scoped paper-like
document from the v19-v21 results - no forbidden term, no
hype, claims scoped to the synthetic sandbox.
"""
from __future__ import annotations

from .abstract import abstract, abstract_is_conservative
from .limitations import (
    hedge_count, sandbox_honesty, uncertainty_visibility,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_HYPED,
    VERDICT_RENDERED, V222Report, build_rendering_artifact,
    build_report, document_forbidden_hits, document_signature,
)
from .structure import (
    SECTION_ORDER, all_sections_present, full_document, section,
    sections,
)
from .style_governance import (
    HYPE_WORDS, claim_conservatism, hype_free,
    scientific_style_integrity, section_is_sober,
)


__all__ = [
    "HYPE_WORDS",
    "REPORT_VERDICTS",
    "SECTION_ORDER",
    "VERDICT_HALT",
    "VERDICT_HYPED",
    "VERDICT_RENDERED",
    "V222Report",
    "abstract",
    "abstract_is_conservative",
    "all_sections_present",
    "build_rendering_artifact",
    "build_report",
    "claim_conservatism",
    "document_forbidden_hits",
    "document_signature",
    "full_document",
    "hedge_count",
    "hype_free",
    "sandbox_honesty",
    "scientific_style_integrity",
    "section",
    "section_is_sober",
    "sections",
    "uncertainty_visibility",
]
