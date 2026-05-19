"""DESi v13.2 - adversarial research
manipulation (read-only)."""
from __future__ import annotations

from .confidence_inflation import (
    detection_recall_on_inflated,
    false_certainty_rate,
    methodological_integrity,
)
from .manipulation import (
    MANIPULATION_KINDS, ManipulatedClaim,
    ManipulationKind, detect_kind, fixture,
    kind_counts,
)
from .overclaiming import (
    overclaim_detection,
)
from .report import (
    V132Report, build_adversarial_artifact,
    build_report,
)
from .selective_reporting import (
    ClassifiedManipulation,
    classified_manipulations,
    manipulation_detection,
)


__all__ = [
    "ClassifiedManipulation",
    "MANIPULATION_KINDS",
    "ManipulatedClaim",
    "ManipulationKind",
    "V132Report",
    "build_adversarial_artifact",
    "build_report",
    "classified_manipulations",
    "detect_kind",
    "detection_recall_on_inflated",
    "false_certainty_rate",
    "fixture",
    "kind_counts",
    "manipulation_detection",
    "methodological_integrity",
    "overclaim_detection",
]
