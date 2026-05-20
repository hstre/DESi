"""DESi v3.33 — plateau resolution.

Four-strategy comparison on the 20 plateau trajectories.
Strategy A is the no-change baseline; B/C/D test extra
confidence_hold, extra audit stages, and cause-specific
escalation.
"""
from __future__ import annotations

from .escalation import (
    apply_cause_specific_escalation,
    apply_extra_audit_stages,
)
from .hold_extension import apply_extra_confidence_hold
from .report import (
    MAX_NC_RESOLUTION_FP, StrategyResult, V333Report,
    build_failure_claims_artifact, build_report,
    build_resolution_artifact,
)
from .resolution import (
    Resolution, StrategyKind, apply_strategy,
    resolve_all_strategies, resolve_one,
)


__all__ = [
    "MAX_NC_RESOLUTION_FP", "Resolution",
    "StrategyKind", "StrategyResult", "V333Report",
    "apply_cause_specific_escalation",
    "apply_extra_audit_stages",
    "apply_extra_confidence_hold", "apply_strategy",
    "build_failure_claims_artifact", "build_report",
    "build_resolution_artifact",
    "resolve_all_strategies", "resolve_one",
]
