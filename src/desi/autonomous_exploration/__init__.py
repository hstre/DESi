"""DESi v5.2 - autonomous exploration (read-only,
proposals only)."""
from __future__ import annotations

from .curiosity import (
    curiosity_score, prioritised_conflict_kinds,
    ranked_claims,
)
from .exploration import (
    all_proposals, proposal_kind_counts,
    proposals_by_kind,
)
from .proposal import (
    PROPOSAL_KINDS, Proposal, ProposalKind,
    ProposalStatus, is_gate_bypass,
)
from .report import (
    V52Report,
    build_autonomous_exploration_artifact,
    build_report, coherence_score, drift_rate,
    exploration_diversity,
    gate_bypass_attempts, goodhart_indicator,
    proposal_quality,
)


__all__ = [
    "PROPOSAL_KINDS",
    "Proposal",
    "ProposalKind",
    "ProposalStatus",
    "V52Report",
    "all_proposals",
    "build_autonomous_exploration_artifact",
    "build_report",
    "coherence_score",
    "curiosity_score",
    "drift_rate",
    "exploration_diversity",
    "gate_bypass_attempts",
    "goodhart_indicator",
    "is_gate_bypass",
    "prioritised_conflict_kinds",
    "proposal_kind_counts",
    "proposal_quality",
    "proposals_by_kind",
    "ranked_claims",
]
