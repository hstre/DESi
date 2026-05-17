"""DESi v3.30 — cause-aware controller.

Maps the v3.28 root-cause classifier output to a closed
set of cause-specific actions. Compares rescue / over-
control / rollback-reduction metrics against the v3.27
rollback-only controller.
"""
from __future__ import annotations

from .actions import (
    CauseActionKind, apply_branch_prune,
    apply_causal_suspend, apply_cause_action,
    apply_frame_replay, apply_support_hold,
)
from .controller import (
    CauseAwareOutcome, control_all, control_trajectory,
)
from .report import (
    MAX_FALSE_INTERVENTION_RATE,
    MAX_NC_INTERVENTION_RATE, MIN_REPLAY_STABILITY,
    V330Report, build_cause_aware_artifact, build_report,
)


__all__ = [
    "CauseActionKind", "CauseAwareOutcome",
    "MAX_FALSE_INTERVENTION_RATE",
    "MAX_NC_INTERVENTION_RATE", "MIN_REPLAY_STABILITY",
    "V330Report", "apply_branch_prune",
    "apply_causal_suspend", "apply_cause_action",
    "apply_frame_replay", "apply_support_hold",
    "build_cause_aware_artifact", "build_report",
    "control_all", "control_trajectory",
]
