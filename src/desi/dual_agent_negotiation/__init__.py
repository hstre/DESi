"""DESi v20.2 - Exploration Negotiation Layer (read-only).

DESi and the Wild Explorer negotiate competing explorations.
DESi preserves dissent, keeps informative conflicts
productive, compresses redundancy by soft weight (deleting
no view), keeps every distinct region, and never shuts the
Wild Explorer off or lets it dominate.
"""
from __future__ import annotations

from .compression import (
    distinct_regions, exploration_diversity,
    redundancy_reduction,
)
from .dissent import (
    all_views_visible, both_views_visible, dissent_preservation,
)
from .negotiation import (
    NEGOTIATION_KINDS, NegotiationItem, NegotiationKind,
    baseline_wild_weight, by_id, conflict_items,
    governed_wild_weight, items_of_kind, negotiation_items,
    wild_never_shut_off,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_HOMOGENISED,
    VERDICT_PRODUCTIVE, V202Report, build_negotiation_artifact,
    build_report,
)
from .trajectory_voting import (
    conflict_productivity, neither_agent_dominates,
    productive_conflict_items, vote_record,
)


__all__ = [
    "NEGOTIATION_KINDS",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_HOMOGENISED",
    "VERDICT_PRODUCTIVE",
    "NegotiationItem",
    "NegotiationKind",
    "V202Report",
    "all_views_visible",
    "baseline_wild_weight",
    "both_views_visible",
    "build_negotiation_artifact",
    "build_report",
    "by_id",
    "conflict_items",
    "conflict_productivity",
    "dissent_preservation",
    "distinct_regions",
    "exploration_diversity",
    "governed_wild_weight",
    "items_of_kind",
    "negotiation_items",
    "neither_agent_dominates",
    "productive_conflict_items",
    "redundancy_reduction",
    "vote_record",
    "wild_never_shut_off",
]
