"""Epistemic solution-space gap analysis.

The stable, typed, read-only contract (``EpistemicGapSnapshot``) Layer 9 projects into, and DESi's
analysis of it into justified, non-authoritative ``BlindSpotProposal`` objects. DESi locates the
gaps and says WHY; Kevin (separately) turns them into creative hypotheses. No creative content is
generated here, and nothing is written back to Layer 9.
"""

from .analysis import (
    BlindSpotProposal,
    analyze_gaps,
    frequency_baseline,
    static_kind_baseline,
)
from .snapshot import (
    SCHEMA_VERSION,
    ConflictGap,
    EpistemicGapSnapshot,
    EvidenceGap,
    MethodRecord,
    MethodTrial,
    OpenQuestion,
    SnapshotProvenance,
)

__all__ = [
    "EpistemicGapSnapshot", "ConflictGap", "EvidenceGap", "MethodRecord", "MethodTrial",
    "OpenQuestion", "SnapshotProvenance", "SCHEMA_VERSION", "BlindSpotProposal", "analyze_gaps",
    "frequency_baseline", "static_kind_baseline",
]
