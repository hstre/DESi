"""DESi v16.0 - Historical Criminal Case Epistemics:
Evidence Topology Audit (Kennedy sandbox, read-only).

DESi structures publicly documented evidence, maps
lineage and conflicts, and keeps uncertainty
visible. It NEVER names a perpetrator, declares the
case solved, confirms a conspiracy, presents
speculation as fact, or claims historical
authority. Claim statuses record the PUBLIC
evidentiary standing only.
"""
from __future__ import annotations

from .ballistics import (
    ballistics_claims, ballistics_only_claims,
    ballistics_supported_fraction,
)
from .claims import (
    CLAIM_STATUSES, SOURCES, Claim, ClaimStatus,
    Source, by_id, claim_ids, claims,
    evidence_rank, topics,
)
from .lineage import (
    escalation_instances, evidence_independence,
    independently_supported, lineage_map,
    single_source_claims, source_dependency,
    unsupported_claims,
    unsupported_escalation_detection,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT,
    VERDICT_STRUCTURED,
    VERDICT_UNCERTAINTY_COLLAPSE, V160Report,
    build_report, build_topology_artifact,
    conflict_clusters, conflict_detection,
    status_histogram, uncertainty_visible,
)
from .timeline import (
    TimelineEvent, backbone_is_ordered, events,
    timeline_consistency, timeline_inconsistencies,
)
from .witnesses import (
    WitnessStatement, statements,
    uncertainty_preserved, witness_conflict_pairs,
    witness_conflict_topics,
)


__all__ = [
    "CLAIM_STATUSES",
    "REPORT_VERDICTS",
    "SOURCES",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNCERTAINTY_COLLAPSE",
    "Claim",
    "ClaimStatus",
    "Source",
    "TimelineEvent",
    "V160Report",
    "WitnessStatement",
    "backbone_is_ordered",
    "ballistics_claims",
    "ballistics_only_claims",
    "ballistics_supported_fraction",
    "build_report",
    "build_topology_artifact",
    "by_id",
    "claim_ids",
    "claims",
    "conflict_clusters",
    "conflict_detection",
    "escalation_instances",
    "events",
    "evidence_independence",
    "evidence_rank",
    "independently_supported",
    "lineage_map",
    "single_source_claims",
    "source_dependency",
    "statements",
    "status_histogram",
    "timeline_consistency",
    "timeline_inconsistencies",
    "topics",
    "uncertainty_preserved",
    "uncertainty_visible",
    "unsupported_claims",
    "unsupported_escalation_detection",
    "witness_conflict_pairs",
    "witness_conflict_topics",
]
