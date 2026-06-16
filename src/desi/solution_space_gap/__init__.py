"""Epistemic solution-space gap analysis.

The stable, typed, read-only contract (``EpistemicGapSnapshot``) Layer 9 projects into, and DESi's
analysis of it into justified, non-authoritative ``BlindSpotProposal`` objects. DESi locates the
gaps and says WHY; Kevin (separately) turns them into creative hypotheses. No creative content is
generated here, and nothing is written back to Layer 9.
"""

from .analysis import BlindSpotProposal, analyze_gaps, frequency_baseline
from .snapshot import (
    ConflictGap,
    EpistemicGapSnapshot,
    EvidenceGap,
    MethodRecord,
    OpenQuestion,
    SnapshotProvenance,
)

__all__ = [
    "EpistemicGapSnapshot", "ConflictGap", "EvidenceGap", "MethodRecord", "OpenQuestion",
    "SnapshotProvenance", "BlindSpotProposal", "analyze_gaps", "frequency_baseline",
]
