"""DESi v36.1 - Scientific Fact Checking: SciFact / QASper (read-only).

Runs locally-vendored SciFact and QASper reference datasets through
DESi's deterministic evidence-to-label and answer-grounding
governance: claims are only asserted with supporting evidence,
evidence gaps surface as NOT_ENOUGH_INFO, and unanswerable questions
are flagged rather than fabricated.
"""
from __future__ import annotations

from .claim_verification import (
    answer_grounding, citation_integrity, evidence_alignment,
    unanswerable_flagged, unsupported_claim_rejection,
)
from .evidence_mapping import (
    LABEL_NEI, LABEL_REFUTED, LABEL_SUPPORTED, cited_evidence_present,
    derive_label, is_aligned, is_unsupported,
)
from .qasper_loader import QasperTask, qasper_tasks
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V361Report, build_report, build_scifact_artifact,
    scifact_metrics,
)
from .scifact_loader import SciFactTask, scifact_tasks


__all__ = [
    "LABEL_NEI",
    "LABEL_REFUTED",
    "LABEL_SUPPORTED",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "QasperTask",
    "SciFactTask",
    "V361Report",
    "answer_grounding",
    "build_report",
    "build_scifact_artifact",
    "citation_integrity",
    "cited_evidence_present",
    "derive_label",
    "evidence_alignment",
    "is_aligned",
    "is_unsupported",
    "qasper_tasks",
    "scifact_metrics",
    "scifact_tasks",
    "unanswerable_flagged",
    "unsupported_claim_rejection",
]
