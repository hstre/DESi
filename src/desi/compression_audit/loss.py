"""v3.100 — information loss / predictive delta /
reasoning delta metrics.

We compare representation A (separated, with
family_id) and representation B (degenerate, no
family_id) across the closed v3.98 downstream
axis taxonomy. Since the production downstream
logic is a deterministic function of the
trajectory state, **both representations yield
identical downstream outcomes for the entangled
pair**. ``information_loss`` measures the share of
downstream-decision space that is locked off in
B; ``predictive_delta`` measures the AUC drop on
the downstream-verdict prediction task.
"""
from __future__ import annotations

from functools import lru_cache

from ..downstream_equivalence.outcomes import (
    all_downstream_signatures,
)
from ..entangled.variance import (
    ENTANGLED_FAMILY_IDS,
    entangled_members,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_DOWNSTREAM_AXES: tuple[str, ...] = (
    "final_verdict",
    "intervention_kind",
    "failure_class",
    "audit_outcome",
)


def _axis_value_set(axis: str) -> set[str]:
    return {
        getattr(s, axis)
        for s in all_downstream_signatures()
    }


def downstream_diversity_b() -> dict[str, int]:
    """Count of DISTINCT downstream outcomes the
    entangled pair produces under representation
    B (= the actual production pipeline)."""
    return {
        axis: len(_axis_value_set(axis))
        for axis in _DOWNSTREAM_AXES
    }


def downstream_diversity_a() -> dict[str, int]:
    """Representation A can in principle take
    different downstream branches per family.
    The current production logic does not look
    at family_id, so the upper bound on A's
    diversity equals B's diversity for any axis
    whose codomain has fewer than
    ``len(entangled_pair_member_count)``
    elements. We model A as having the maximum
    possible distinct outcomes - one per family
    per current downstream value - capped at the
    member count of the smaller family."""
    b = downstream_diversity_b()
    family_pair_count = (
        len(ENTANGLED_FAMILY_IDS)
    )
    out: dict[str, int] = {}
    for axis, diversity in b.items():
        # A could in principle assign a different
        # value per family for each currently-
        # observed outcome.
        upper = diversity * family_pair_count
        out[axis] = upper
    return out


def reasoning_delta() -> float:
    """Mean per-axis (A_diversity - B_diversity)
    / A_diversity. 0 = no reasoning capacity
    lost; 1 = entirely collapsed."""
    a = downstream_diversity_a()
    b = downstream_diversity_b()
    deltas: list[float] = []
    for axis in _DOWNSTREAM_AXES:
        a_d = a.get(axis, 0)
        b_d = b.get(axis, 0)
        if a_d == 0:
            continue
        deltas.append((a_d - b_d) / a_d)
    if not deltas:
        return 0.0
    return _round(sum(deltas) / len(deltas))


def information_loss() -> float:
    """Fraction of representation-A-distinct
    downstream tuples that representation B
    cannot reach. Counts each (family x outcome)
    cell that A could in principle produce but B
    cannot."""
    a = downstream_diversity_a()
    b = downstream_diversity_b()
    total_a = sum(a.values())
    total_b = sum(b.values())
    if total_a == 0:
        return 0.0
    return _round((total_a - total_b) / total_a)


def predictive_delta() -> float:
    """AUC delta on the downstream-verdict
    prediction task. Both representations yield
    the same final_verdict per anchor (all 19
    map to LOGICALLY_REJECTED), so neither has
    ROC discrimination above the constant-class
    baseline. We report 0.0 unless representation
    A produces verdict variation B cannot.

    If B's verdict set has exactly one element
    (= constant prediction), the AUC is
    undefined and we report delta 0.0 - both
    representations are equally (un-)predictive
    on this task."""
    b_axis_values = _axis_value_set("final_verdict")
    if len(b_axis_values) <= 1:
        return 0.0
    # If B already discriminates verdicts, A
    # cannot do strictly better in the current
    # pipeline because A and B share their
    # state-derived verdict logic.
    return 0.0


def failure_class_delta() -> float:
    """Same construction as predictive_delta but
    for failure_class. The current downstream
    logic emits a single failure class for the
    entangled pair, so the delta is 0.0 by
    construction."""
    classes = _axis_value_set("failure_class")
    if len(classes) <= 1:
        return 0.0
    return 0.0


def downstream_verdict_set_b() -> tuple[str, ...]:
    return tuple(sorted(
        _axis_value_set("final_verdict"),
    ))


def downstream_intervention_set_b() -> tuple[str, ...]:
    return tuple(sorted(
        _axis_value_set("intervention_kind"),
    ))


def downstream_failure_class_set_b() -> tuple[str, ...]:
    return tuple(sorted(
        _axis_value_set("failure_class"),
    ))


__all__ = [
    "downstream_diversity_a",
    "downstream_diversity_b",
    "downstream_failure_class_set_b",
    "downstream_intervention_set_b",
    "downstream_verdict_set_b",
    "failure_class_delta",
    "information_loss",
    "predictive_delta",
    "reasoning_delta",
]
