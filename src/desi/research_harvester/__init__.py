"""DESi v27.0 - Research Claim Harvester Topology (read-only).

Models AI/ML research papers not as text documents but as
temporary epistemic states: each paper is decomposed into typed,
paper-anchored claims (a closed taxonomy) with explicit
limitations and open questions, over a deterministic fixture
corpus. Exactly one paper is the real base-paper anchor; every
other is explicitly synthetic and illustrative. DESi structures
research - it does not rank, score, peer-review, judge truth or
debunk.
"""
from __future__ import annotations

from .claims import Claim
from .metadata import PaperMetadata
from .papers import (
    PaperRecord, all_assumptions, all_authors, all_claims,
    all_datasets, all_methods, all_metrics, by_id,
    claims_by_class, claims_of, paper_ids, papers,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL,
    VERDICT_STRUCTURED, V270Report, build_report,
    build_topology_artifact, claim_extraction_consistency,
    limitation_visibility, open_question_visibility,
    provenance_integrity, replay_stability,
)
from .taxonomy import (
    CLAIM_CLASSES, SOURCES, TOPIC_AREAS, ClaimClass,
    is_claim_class, is_source, is_topic_area,
)


__all__ = [
    "CLAIM_CLASSES",
    "REPORT_VERDICTS",
    "SOURCES",
    "TOPIC_AREAS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_STRUCTURED",
    "Claim",
    "ClaimClass",
    "PaperMetadata",
    "PaperRecord",
    "V270Report",
    "all_assumptions",
    "all_authors",
    "all_claims",
    "all_datasets",
    "all_methods",
    "all_metrics",
    "build_report",
    "build_topology_artifact",
    "by_id",
    "claim_extraction_consistency",
    "claims_by_class",
    "claims_of",
    "is_claim_class",
    "is_source",
    "is_topic_area",
    "limitation_visibility",
    "open_question_visibility",
    "paper_ids",
    "papers",
    "provenance_integrity",
    "replay_stability",
]
