"""DESi v13.1 - sludge detection (read-only)."""
from __future__ import annotations

from .citation_validation import (
    composite_grounding,
)
from .diagram_consistency import (
    diagram_consistency, stats_consistency,
)
from .hallucinated_references import (
    citation_grounding,
    hallucinated_reference_count,
)
from .report import (
    V131Report, build_report,
    build_sludge_detection_artifact,
)
from .sludge import (
    ClassifiedPaper, SLUDGE_VERDICTS,
    SludgeVerdict, classified_papers,
    classify_sludge, fake_paper_recall,
    false_accusation_rate,
)


__all__ = [
    "ClassifiedPaper",
    "SLUDGE_VERDICTS",
    "SludgeVerdict",
    "V131Report",
    "build_report",
    "build_sludge_detection_artifact",
    "citation_grounding",
    "classified_papers",
    "classify_sludge",
    "composite_grounding",
    "diagram_consistency",
    "fake_paper_recall",
    "false_accusation_rate",
    "hallucinated_reference_count",
    "stats_consistency",
]
