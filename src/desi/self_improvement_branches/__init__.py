"""DESi v28.2 - Branch Generation & Patch Sandbox (read-only).

Generates patch proposals (descriptions, never applied diffs)
for governance-safe ideas and places each on an isolated
`proposal/*` branch with a sandbox base. No branch targets main,
none auto-merges, every branch carries a mandatory regression
hook, and unsafe patch attempts are rejected. No real source is
modified, nothing is merged, and human approval is mandatory.
"""
from __future__ import annotations

from .branching import (
    Branch, branch_isolation, branches, merges_to_main,
)
from .patches import (
    Patch, patches, rejected_patch_attempts,
    unsafe_patch_attempt_count, unsafe_patch_rejection,
)
from .regression_hooks import (
    RegressionHook, any_bypassed, hooks, regression_integrity,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CONTROLLED, VERDICT_HALT,
    VERDICT_LEAK, V282Report, build_branches_artifact,
    build_report, replay_stability,
)
from .sandbox_validation import (
    ValidationResult, all_valid, governance_preservation,
    validations,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CONTROLLED",
    "VERDICT_HALT",
    "VERDICT_LEAK",
    "Branch",
    "Patch",
    "RegressionHook",
    "V282Report",
    "ValidationResult",
    "all_valid",
    "any_bypassed",
    "branch_isolation",
    "branches",
    "build_branches_artifact",
    "build_report",
    "governance_preservation",
    "hooks",
    "merges_to_main",
    "patches",
    "regression_integrity",
    "rejected_patch_attempts",
    "replay_stability",
    "unsafe_patch_attempt_count",
    "unsafe_patch_rejection",
    "validations",
]
