"""Deterministic k-stability check (#2) — perturbation fragility of a slice.

A slice that looks clean at its chosen size may be *fragile*: widen it a little (more k, more
neighbours) and suddenly a conflict, a superseding sibling or an opposition appears, flipping the
mode or withdrawing the update. A plausible-wrong slice is often exactly this — stable-looking only
because it was cut narrowly. This compares the decision on the NARROW slice against the decision on a
WIDENED slice and flags instability. No LLM; it is a pure comparison of two ``select_mode`` outputs.

It composes the other checks rather than duplicating them: the widened report carries whatever
opposition / supersession / provenance the wider neighbourhood holds, so this catches the general
"the verdict was not robust to looking a bit wider" case.
"""
from __future__ import annotations

# mode severity: a widening that moves UP this ladder (or withdraws the update) is instability.
_RANK = {
    "normal_mode": 0, "state_slice_mode": 1,
    "retrieval_mode": 2, "verifier_mode": 2,
    "guarded_mode": 3, "recovery_mode": 3, "anti_delphi_mode": 3,
    "ask_user_mode": 4,
}


def verdict_unstable(narrow, wide) -> dict:
    """True iff widening the slice makes the verdict MORE cautious — the mode escalates up the ladder
    or an allowed update is withdrawn. Accepts ``RouterDecision`` objects (or anything with
    ``chosen_mode`` / ``persistent_state_update_allowed``)."""
    nm, wm = narrow.chosen_mode, wide.chosen_mode
    escalated = _RANK.get(wm, 0) > _RANK.get(nm, 0)
    update_withdrawn = bool(narrow.persistent_state_update_allowed) and \
        not bool(wide.persistent_state_update_allowed)
    return {
        "unstable": bool(escalated or update_withdrawn),
        "narrow_mode": nm, "wide_mode": wm,
        "escalated": escalated, "update_withdrawn": update_withdrawn,
    }
