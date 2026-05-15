"""DESi v3.1 documentation anchor discipline."""
from __future__ import annotations

from .autoinsert import AnchorProposal, apply_proposals, propose_anchors
from .parser import parse_anchors, parse_legacy_markers
from .report import (
    AnchorCoverageReport,
    build_anchor_report,
    compute_report_replay_hash,
)
from .schema import (
    ANCHOR_PREFIX,
    ClaimAnchor,
    LEGACY_MARKER,
    LegacyExemption,
)
from .validator import (
    AnchorOutcome,
    AnchorVerdict,
    validate_anchor,
    validate_anchors,
)

__all__ = [
    "ANCHOR_PREFIX",
    "AnchorCoverageReport",
    "AnchorOutcome",
    "AnchorProposal",
    "AnchorVerdict",
    "ClaimAnchor",
    "LEGACY_MARKER",
    "LegacyExemption",
    "apply_proposals",
    "build_anchor_report",
    "compute_report_replay_hash",
    "parse_anchors",
    "parse_legacy_markers",
    "propose_anchors",
    "validate_anchor",
    "validate_anchors",
]
