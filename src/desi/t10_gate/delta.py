"""v3.104a — per-cell delta aggregates.

Counts and AUC-typed deltas split by direction:

* ``beneficial_flip_count`` - stored FAIL → cf PASS
* ``adverse_flip_count``    - stored PASS → cf FAIL
* ``neutral_count``         - stored == cf
* ``adverse_auc_delta``     - max |delta| among
  AUC-typed metrics whose direction is adverse.
* ``beneficial_auc_delta``  - max |delta| among
  AUC-typed metrics whose direction is
  beneficial.
* ``historical_delta_map``  - {sprint_id ->
  list of classified outcomes}.
"""
from __future__ import annotations

from collections import defaultdict

from .classify import (
    ClassifiedOutcome, DeltaKind,
    all_classified_outcomes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def beneficial_flip_count() -> int:
    return sum(
        1 for o in all_classified_outcomes()
        if o.kind == DeltaKind.BENEFICIAL_FLIP.value
    )


def adverse_flip_count() -> int:
    return sum(
        1 for o in all_classified_outcomes()
        if o.kind == DeltaKind.ADVERSE_FLIP.value
    )


def neutral_count() -> int:
    return sum(
        1 for o in all_classified_outcomes()
        if o.kind in (
            DeltaKind.NEUTRAL_PASS.value,
            DeltaKind.NEUTRAL_FAIL.value,
        )
    )


def _is_auc_metric(metric: str) -> bool:
    return "auc" in metric.lower()


def adverse_auc_delta() -> float:
    deltas = [
        abs(o.value_delta)
        for o in all_classified_outcomes()
        if _is_auc_metric(o.gate_metric)
        and o.kind == DeltaKind.ADVERSE_FLIP.value
    ]
    return _round(max(deltas)) if deltas else 0.0


def beneficial_auc_delta() -> float:
    deltas = [
        abs(o.value_delta)
        for o in all_classified_outcomes()
        if _is_auc_metric(o.gate_metric)
        and o.kind == DeltaKind.BENEFICIAL_FLIP.value
    ]
    return _round(max(deltas)) if deltas else 0.0


def historical_delta_map() -> dict[
    str, list[dict],
]:
    out: dict[str, list[dict]] = defaultdict(list)
    for o in all_classified_outcomes():
        out[o.sprint_id].append(o.to_dict())
    return {k: out[k] for k in sorted(out)}


def affected_sprint_ids() -> tuple[str, ...]:
    """Sprints with any non-neutral classified
    outcome."""
    affected: set[str] = set()
    for o in all_classified_outcomes():
        if o.kind in (
            DeltaKind.BENEFICIAL_FLIP.value,
            DeltaKind.ADVERSE_FLIP.value,
        ):
            affected.add(o.sprint_id)
    return tuple(sorted(affected))


__all__ = [
    "adverse_auc_delta",
    "adverse_flip_count",
    "affected_sprint_ids",
    "beneficial_auc_delta",
    "beneficial_flip_count",
    "historical_delta_map",
    "neutral_count",
]
