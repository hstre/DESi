"""v3.38 — single-feature boundary scan.

For every (dimension, state_index) pair in the closed
trajectory schema, find the threshold-based linear
classifier that maximises accuracy on the
(plateau, unexpected-rescue) labelling. The best feature
is the directive's ``best_separating_dimension``.

This intentionally compares ``support_state`` at the
final index (the verdict itself, accuracy 1.0 by
construction) against every other feature. If any
pre-audit feature also achieves 1.0, the plateau /
rescue distinction is observable BEFORE the audit step
- the v3.39 specificity-recovery search has a usable
gate.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.state import DIMENSION_NAMES


PLATEAU_LABEL = "plateau"
RESCUE_LABEL  = "causal_leap"


@dataclass(frozen=True)
class FeatureSplit:
    dimension: str
    state_index: int
    threshold: float
    direction: str       # "ge" -> plateau when value >= t
    accuracy: float

    @property
    def feature_id(self) -> str:
        return f"{self.dimension}@{self.state_index}"

    def to_dict(self) -> dict[str, object]:
        return {
            "dimension": self.dimension,
            "state_index": self.state_index,
            "threshold": self.threshold,
            "direction": self.direction,
            "accuracy": self.accuracy,
            "feature_id": self.feature_id,
        }


def _candidate_thresholds(values: list[float]) -> list[float]:
    """Midpoints between consecutive unique sorted values
    plus the unique values themselves."""
    uniq = sorted(set(values))
    if not uniq:
        return [0.0]
    mids = [
        (uniq[i] + uniq[i + 1]) / 2.0
        for i in range(len(uniq) - 1)
    ]
    return uniq + mids


def _evaluate_split(
    values: list[float], labels: list[str],
    threshold: float, direction: str,
) -> float:
    correct = 0
    for v, lbl in zip(values, labels):
        if direction == "ge":
            pred = (
                PLATEAU_LABEL if v >= threshold
                else RESCUE_LABEL
            )
        else:
            pred = (
                PLATEAU_LABEL if v < threshold
                else RESCUE_LABEL
            )
        if pred == lbl:
            correct += 1
    return round(correct / len(values), 6) if values else 0.0


def best_split_for_feature(
    dim: str, state_index: int,
    items: tuple[tuple[str, str, tuple[float, ...]], ...],
    states_by_id: dict,
) -> FeatureSplit:
    values: list[float] = []
    labels: list[str] = []
    for tid, lbl, _vec in items:
        states = states_by_id[tid]
        values.append(getattr(states[state_index], dim))
        labels.append(lbl)
    best = FeatureSplit(
        dimension=dim, state_index=state_index,
        threshold=0.0, direction="ge", accuracy=0.0,
    )
    for t in _candidate_thresholds(values):
        for direction in ("ge", "lt"):
            acc = _evaluate_split(values, labels, t, direction)
            if acc > best.accuracy:
                best = FeatureSplit(
                    dimension=dim,
                    state_index=state_index,
                    threshold=round(t, 6),
                    direction=direction,
                    accuracy=acc,
                )
    return best


def all_feature_splits(
    items: tuple[tuple[str, str, tuple[float, ...]], ...],
    states_by_id: dict, n_states: int,
) -> tuple[FeatureSplit, ...]:
    out: list[FeatureSplit] = []
    for state_index in range(n_states):
        for dim in DIMENSION_NAMES:
            out.append(best_split_for_feature(
                dim, state_index, items, states_by_id,
            ))
    return tuple(out)


def best_separating_split(
    splits: tuple[FeatureSplit, ...],
) -> FeatureSplit:
    """The split with the highest accuracy. Ties broken
    by preferring earlier state_index (so a pre-audit
    feature wins over the final-state verdict feature
    when both are perfect), then alphabetical dimension."""
    return min(
        splits,
        key=lambda s: (
            -s.accuracy, s.state_index, s.dimension,
        ),
    )


def support_final_split(
    splits: tuple[FeatureSplit, ...], n_states: int,
) -> FeatureSplit:
    """The directive's named baseline: support_state at
    the final index."""
    for s in splits:
        if (
            s.dimension == "support_state"
            and s.state_index == n_states - 1
        ):
            return s
    raise LookupError("support_state@final not in splits")


__all__ = [
    "FeatureSplit", "PLATEAU_LABEL", "RESCUE_LABEL",
    "all_feature_splits", "best_separating_split",
    "best_split_for_feature", "support_final_split",
]
