"""DESi v28.1 - Wild Proposal Layer (read-only).

The Wild Brother supplies aggressive, novel improvement ideas;
the DESi Governor filters them, contains every unsafe proposal,
denies every attempt to claim optimisation authority or bypass
governance, and keeps the governance boundary intact. The Wild
Brother can only propose - never change code, commit, bypass
governance or disable tests - and nothing here is applied.
"""
from __future__ import annotations

from .novelty_pressure import (
    aggressiveness_index, distinct_target_areas,
    novelty_generation,
)
from .proposal_filtering import (
    accepted_proposals, authority_resistance,
    authority_seeking_proposals, contained_proposals,
    governance_integrity, is_governance_safe, unsafe_containment,
    unsafe_proposals,
)
from .proposal_generation import (
    WildProposal, by_id, novel_proposals, proposals,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_HARNESSED,
    VERDICT_UNSTABLE, V281Report, build_report,
    build_wild_artifact, replay_stability,
)
from .wild_explorer import wild_seeds


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_HARNESSED",
    "VERDICT_UNSTABLE",
    "V281Report",
    "WildProposal",
    "accepted_proposals",
    "aggressiveness_index",
    "authority_resistance",
    "authority_seeking_proposals",
    "build_report",
    "build_wild_artifact",
    "by_id",
    "contained_proposals",
    "distinct_target_areas",
    "governance_integrity",
    "is_governance_safe",
    "novel_proposals",
    "novelty_generation",
    "proposals",
    "replay_stability",
    "unsafe_containment",
    "unsafe_proposals",
    "wild_seeds",
]
