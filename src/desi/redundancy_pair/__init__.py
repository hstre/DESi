"""DESi v3.78 — redundant pair removal.

Tests four conditions on the v3.73 test claim space
to confirm whether removing both members of a
redundant high-coverage pair unmasks the missing-
claim perturbation.
"""
from __future__ import annotations

from .removal import (
    BRIDGE_ANCHOR, ConditionResult, EXTENDED_SET,
    HIGH_PAIR_A, HIGH_PAIR_B, LOW_ANCHOR,
    PROBE_RADIUS, RemovalCondition, TEST_SET,
    UNRELATED_A, UNRELATED_B, all_conditions,
    redundancy_unmasking_gain,
)
from .report import (
    V378Report,
    build_redundant_pair_removal_artifact,
    build_report,
)


__all__ = [
    "BRIDGE_ANCHOR", "ConditionResult",
    "EXTENDED_SET", "HIGH_PAIR_A", "HIGH_PAIR_B",
    "LOW_ANCHOR", "PROBE_RADIUS",
    "RemovalCondition", "TEST_SET",
    "UNRELATED_A", "UNRELATED_B", "V378Report",
    "all_conditions",
    "build_redundant_pair_removal_artifact",
    "build_report",
    "redundancy_unmasking_gain",
]
