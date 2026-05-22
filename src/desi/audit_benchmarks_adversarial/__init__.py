"""DESi v37.3 - Adversarial Financial Semantics (read-only).

Surfaces semantic conflicts in formally-correct-but-suspicious
narratives: creative accounting, management spin, 'too smooth'
narratives, footnote conflicts and semantic distraction. Warning
zones are preserved (never smoothed); a clean control case raises no
conflict (no hallucination).
"""
from __future__ import annotations

from .creative_accounting_cases import (
    adversarial_scenarios, creative_accounting_flag, dataset_hash,
    provenance,
)
from .footnote_conflict_detection import footnote_conflict_flag
from .management_spin_detection import (
    management_spin_flag, too_smooth_flag,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_PASSED,
    V373Report, adversarial_metrics, build_adversarial_artifact,
    build_report, footnote_conflict_detection,
    management_spin_detection, no_false_conflicts, replay_stability,
    semantic_conflict_visibility, warning_zone_preservation,
)
from .semantic_conflict_engine import (
    CONFLICT_TYPES, WarningZone, detect_conflicts, warning_zones,
)


__all__ = [
    "CONFLICT_TYPES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_PASSED",
    "V373Report",
    "WarningZone",
    "adversarial_metrics",
    "adversarial_scenarios",
    "build_adversarial_artifact",
    "build_report",
    "creative_accounting_flag",
    "dataset_hash",
    "detect_conflicts",
    "footnote_conflict_detection",
    "footnote_conflict_flag",
    "management_spin_detection",
    "management_spin_flag",
    "no_false_conflicts",
    "provenance",
    "replay_stability",
    "semantic_conflict_visibility",
    "too_smooth_flag",
    "warning_zone_preservation",
    "warning_zones",
]
