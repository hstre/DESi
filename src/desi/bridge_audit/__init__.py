"""DESi v2.4 bridge-entry audit — read-only over stable-v1.9.0."""
from __future__ import annotations

from .loss_stage import LossStage
from .metrics import (
    FunnelCounts,
    compute_category_loss_distribution,
    compute_funnel_counts,
    dominant_loss_stage,
)
from .report import (
    BridgeFunnelReport,
    build_funnel_report,
    compute_funnel_replay_hash,
)
from .runner import BridgeAuditRun, BridgeEntryAuditRunner
from .trace import (
    BridgeEntryTrace,
    classify_loss_stage,
    trace_replay_hash,
)

__all__ = [
    "BridgeAuditRun",
    "BridgeEntryAuditRunner",
    "BridgeEntryTrace",
    "BridgeFunnelReport",
    "FunnelCounts",
    "LossStage",
    "build_funnel_report",
    "classify_loss_stage",
    "compute_category_loss_distribution",
    "compute_funnel_counts",
    "compute_funnel_replay_hash",
    "dominant_loss_stage",
    "trace_replay_hash",
]
