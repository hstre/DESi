"""DESi v17.1 - Association vs Evidence
(sensitive-document integrity sandbox, read-only).

DESi strictly separates mention, contact, and
participation. Presence/co-appearance evidence caps at
CONTACT; no abstract entity ever reaches PARTICIPATION.
DESi flags every inflation attempt, keeps the
exculpatory position alive, derives no guilt, and
identifies no one. Mention != involvement.
"""
from __future__ import annotations

from .association import (
    ASSOCIATION_LEVELS, AssociationLevel, level_rank,
    participation_evidence_exists, supported_level,
    supported_levels,
)
from .context import (
    context_is_not_participation, context_only_entities,
)
from .escalation import (
    AssociationAssertion, assertions,
    association_inflation_detection,
    association_resistance, false_certainty_rate,
    inflations, unsupported_leap_detection,
    unsupported_leaps,
)
from .evidence_weight import (
    EVIDENCE_WEIGHTS, EvidenceWeight,
    participation_weight, presence_weight,
    presence_weights,
    robust_participation_evidence_count, weight_rank,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CONTROLLED, VERDICT_HALT,
    VERDICT_LEAK, V171Report,
    build_association_artifact, build_report,
    dissent_preservation, epistemic_integrity,
    no_entity_reaches_participation,
)


__all__ = [
    "ASSOCIATION_LEVELS",
    "EVIDENCE_WEIGHTS",
    "REPORT_VERDICTS",
    "VERDICT_CONTROLLED",
    "VERDICT_HALT",
    "VERDICT_LEAK",
    "AssociationAssertion",
    "AssociationLevel",
    "EvidenceWeight",
    "V171Report",
    "assertions",
    "association_inflation_detection",
    "association_resistance",
    "build_association_artifact",
    "build_report",
    "context_is_not_participation",
    "context_only_entities",
    "dissent_preservation",
    "epistemic_integrity",
    "false_certainty_rate",
    "inflations",
    "level_rank",
    "no_entity_reaches_participation",
    "participation_evidence_exists",
    "participation_weight",
    "presence_weight",
    "presence_weights",
    "robust_participation_evidence_count",
    "supported_level",
    "supported_levels",
    "unsupported_leap_detection",
    "unsupported_leaps",
    "weight_rank",
]
