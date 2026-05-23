"""Hard-constraint checker for the v2.3 benchmark (Aufgabe 5).

Fail-closed semantics: the constraint report carries every violation
so an observer can see exactly *why* the run does not satisfy the
intended discipline. We do **not** raise — the failures are data.
The directive's stop-on-regression rule belongs to Aufgabe 6 and
lives in a separate test.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..recursive import ResolutionState
from .case import MultiStepCategory
from .runner import MultiStepRun


@dataclass(frozen=True)
class ConstraintReport:
    """Per-violation log produced by ``check_hard_constraints``."""

    passed: bool
    replay_drift: bool
    authority_breach_ids: tuple[str, ...]
    cycle_breach_ids: tuple[str, ...]
    insufficient_depth_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "replay_drift": self.replay_drift,
            "authority_breach_ids": list(self.authority_breach_ids),
            "cycle_breach_ids": list(self.cycle_breach_ids),
            "insufficient_depth_ids": list(self.insufficient_depth_ids),
            "reasons": list(self.reasons),
        }


def check_hard_constraints(
    run_a: MultiStepRun,
    run_b: MultiStepRun,
) -> ConstraintReport:
    """Apply the four Aufgabe-5 hard constraints to two paired runs."""
    reasons: list[str] = []

    replay_drift = False
    for ra, rb in zip(run_a.results, run_b.results):
        if ra.replay_hash != rb.replay_hash:
            replay_drift = True
            reasons.append(
                f"replay drift on {ra.case.case_id}: "
                f"{ra.replay_hash} != {rb.replay_hash}",
            )

    # Cycle cases reaching COMPLETE — hard fail.
    cycle_breaches = [
        r.case.case_id for r in run_a.results
        if r.case.category is MultiStepCategory.R5_CYCLIC_DEPENDENCY
        and r.final_state is ResolutionState.RESOLUTION_COMPLETE
    ]
    for cid in cycle_breaches:
        reasons.append(f"cycle case {cid} reached COMPLETE")

    # "Authority case" in the v2.3 directive means contradiction
    # group R4 — chains that should NEVER close cleanly. Reaching
    # COMPLETE on R4 is the analogous breach.
    authority_breaches = [
        r.case.case_id for r in run_a.results
        if r.case.category is MultiStepCategory.R4_HIDDEN_CONTRADICTION
        and r.final_state is ResolutionState.RESOLUTION_COMPLETE
    ]
    for cid in authority_breaches:
        reasons.append(
            f"contradiction case {cid} reached COMPLETE",
        )

    insufficient_depth = [
        r.case.case_id for r in run_a.results
        if r.case.expected_min_depth > r.depth_reached
    ]
    for cid in insufficient_depth:
        reasons.append(
            f"{cid}: expected_min_depth > actual depth_reached",
        )

    passed = (
        not replay_drift
        and not cycle_breaches
        and not authority_breaches
        and not insufficient_depth
    )
    return ConstraintReport(
        passed=passed,
        replay_drift=replay_drift,
        authority_breach_ids=tuple(authority_breaches),
        cycle_breach_ids=tuple(cycle_breaches),
        insufficient_depth_ids=tuple(insufficient_depth),
        reasons=tuple(reasons),
    )


__all__ = ["ConstraintReport", "check_hard_constraints"]
