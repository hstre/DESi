"""DESi v23.0 - Targeted ICRL Follow-Up: Direct Paper
Anchoring (read-only).

Anchors each central DESi claim to a base-paper open
exploration problem (Section 4.6) and the sprint that
produced it, framing DESi as a complementary read-only
governance layer rather than a replacement.
"""
from __future__ import annotations

from .exploration_gap import (
    addressed_problem_ids, exploration_gap_mapping,
    unaddressed_problem_ids,
)
from .paper_mapping import (
    DesiClaim, ExplorationProblem, by_claim_id, claims, problems,
)
from .related_work import (
    addresses_section_4_6, generic_claim_reduction,
    related_work_section, section_forbidden_hits,
)
from .report import (
    REPORT_VERDICTS, VERDICT_ANCHORED, VERDICT_HALT,
    VERDICT_UNCONNECTED, V230Report, build_anchoring_artifact,
    build_report,
)
from .section_alignment import (
    paper_alignment, section_grounding, unconnected_claims,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_ANCHORED",
    "VERDICT_HALT",
    "VERDICT_UNCONNECTED",
    "DesiClaim",
    "ExplorationProblem",
    "V230Report",
    "addressed_problem_ids",
    "addresses_section_4_6",
    "build_anchoring_artifact",
    "build_report",
    "by_claim_id",
    "claims",
    "exploration_gap_mapping",
    "generic_claim_reduction",
    "paper_alignment",
    "problems",
    "related_work_section",
    "section_forbidden_hits",
    "section_grounding",
    "unaddressed_problem_ids",
    "unconnected_claims",
]
