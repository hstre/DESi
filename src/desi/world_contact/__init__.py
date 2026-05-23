"""DESi v6.0 - scientific paper audit
(read-only, snapshot corpus)."""
from __future__ import annotations

from .audit import (
    blindness_pools_added,
    bridge_audit_coverage,
    claim_extraction_accuracy,
    frame_distribution, frame_diversity,
    unsupported_leap_detection,
)
from .claim_extractor import (
    ExtractedKind, ExtractedUnit,
    ExtractionScore, all_scores,
    corpus_extractions, extract,
    hallucination_rate, score_paper,
)
from .paper_reader import (
    Paper, VENUES, Venue, corpus,
    paper_by_id, venue_counts,
)
from .report import (
    V60Report, build_paper_audit_artifact,
    build_report,
)


__all__ = [
    "ExtractedKind",
    "ExtractedUnit",
    "ExtractionScore",
    "Paper",
    "V60Report",
    "VENUES",
    "Venue",
    "all_scores",
    "blindness_pools_added",
    "bridge_audit_coverage",
    "build_paper_audit_artifact",
    "build_report",
    "claim_extraction_accuracy",
    "corpus",
    "corpus_extractions",
    "extract",
    "frame_distribution",
    "frame_diversity",
    "hallucination_rate",
    "paper_by_id",
    "score_paper",
    "unsupported_leap_detection",
    "venue_counts",
]
