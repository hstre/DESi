"""DESi v3.73 — known-claim removal.

Constructs a 4-anchor test claim space (HIGH / LOW /
BRIDGE / REDUNDANT) and measures the perturbation
each role-targeted removal produces.
"""
from __future__ import annotations

from .perturbation import (
    aggregate, total_support_shift,
)
from .remove import (
    ClaimRole, PROBE_RADIUS, RemovalOutcome,
    TEST_CLAIM_SET, all_removal_outcomes,
    baseline_coverage, coverage_set,
    nearest_anchor_per_leakage, removal_outcome,
    support_shift,
)
from .report import (
    V373Report,
    build_removal_perturbation_artifact,
    build_report,
)


__all__ = [
    "ClaimRole", "PROBE_RADIUS", "RemovalOutcome",
    "TEST_CLAIM_SET", "V373Report",
    "aggregate", "all_removal_outcomes",
    "baseline_coverage",
    "build_removal_perturbation_artifact",
    "build_report", "coverage_set",
    "nearest_anchor_per_leakage",
    "removal_outcome", "support_shift",
    "total_support_shift",
]
