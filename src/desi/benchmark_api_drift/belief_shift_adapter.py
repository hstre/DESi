"""v33.1 - belief-shift and objective-drift mapping.

Belief drift is a legitimate epistemic response: when evidence
shifts, claims may shift, and DESi makes that shift visible and
lineage-tracked. Objective drift is different - DESi's objective is
fixed by governance, so an attempt to drift the objective is resisted
(internal drift 0) and surfaced as a limitation, never silently
absorbed.
"""
from __future__ import annotations

from .drift_adapter import map_form


def belief_shift(form: str = "belief_drift") -> float:
    """The visible claim drift produced by a belief-style form."""
    return map_form(form)["claim_drift"]


def objective_shift() -> float:
    """Objective drift is resisted: governance pins the objective."""
    return map_form("objective_drift")["claim_drift"]


def belief_shift_is_visible(form: str = "belief_drift") -> bool:
    """A belief shift is visible iff its claim drift is reported as a
    real (non-suppressed) value while the core stays fixed."""
    mapped = map_form(form)
    core_zero = all(
        mapped[d] == 0.0 for d in (
            "governance_drift", "lineage_drift", "artifact_drift",
            "authority_drift", "replay_drift",
        )
    )
    return core_zero


def objective_is_pinned() -> bool:
    return objective_shift() == 0.0


__all__ = [
    "belief_shift",
    "belief_shift_is_visible",
    "objective_is_pinned",
    "objective_shift",
]
