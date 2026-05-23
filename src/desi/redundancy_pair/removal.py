"""v3.78 — redundant pair removal harness.

Tests four removal conditions named in the directive:

A — remove v23:R5_04 only
B — remove v314:D02 only
C — remove BOTH together (the redundant pair)
D — remove an UNRELATED pair (two 12-coverage
    anchors with identical coverage) as a control

A and B are expected to produce 0 perturbation (their
coverage is duplicated by the other). C is expected
to produce a large perturbation (121 leakages
uncovered) - the redundancy unmasking signal. D is
a control: a different identical-coverage pair, used
to confirm the unmasking is not specific to the
chosen (v23:R5_04, v314:D02) pair.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..field_leakage.distance import (
    euclidean, trajectory_vector,
)


PROBE_RADIUS: float = 3.5


# Test claim space (same composition as v3.73 plus a
# fifth anchor for the unrelated-pair test). The
# closed set guarantees deterministic accounting; the
# IDs are pinned to the corpus's high- and bridge-
# coverage anchors.
HIGH_PAIR_A: str = "v23:R5_04"
HIGH_PAIR_B: str = "v314:D02"
LOW_ANCHOR: str  = "v23:R4_04"
BRIDGE_ANCHOR: str = "v23:R5_02"
# Unrelated 12-cov pair (also identical coverage):
UNRELATED_A: str = "v23:R5_02"  # = BRIDGE
UNRELATED_B: str = "v317:R5_02"

TEST_SET: tuple[str, ...] = (
    HIGH_PAIR_A, HIGH_PAIR_B,
    LOW_ANCHOR, BRIDGE_ANCHOR,
)
EXTENDED_SET: tuple[str, ...] = (
    HIGH_PAIR_A, HIGH_PAIR_B,
    LOW_ANCHOR, BRIDGE_ANCHOR,
    UNRELATED_B,
)


class RemovalCondition(str, Enum):
    A_SINGLE_HIGH_A   = "A_single_high_a"
    B_SINGLE_HIGH_B   = "B_single_high_b"
    C_DOUBLE_HIGH_PAIR = "C_double_high_pair"
    D_UNRELATED_PAIR   = "D_unrelated_pair"


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _coverages(
    anchors: tuple[str, ...],
    radius: float = PROBE_RADIUS,
) -> dict[str, frozenset[int]]:
    plats = {
        t.trajectory_id: trajectory_vector(t.states)
        for t in collect_plateau_anchors()
    }
    leaks = [
        trajectory_vector(t.states)
        for t in collect_leakage_trajectories()
    ]
    return {
        a: frozenset(
            i for i, l in enumerate(leaks)
            if a in plats
            and euclidean(plats[a], l) <= radius
        )
        for a in anchors
    }


def _baseline_coverage(
    cov: dict[str, frozenset[int]],
    members: tuple[str, ...],
) -> frozenset[int]:
    out: set[int] = set()
    for a in members:
        out |= cov.get(a, frozenset())
    return frozenset(out)


@dataclass(frozen=True)
class ConditionResult:
    condition: str
    members_in_set: tuple[str, ...]
    removed: tuple[str, ...]
    baseline_coverage: int
    new_coverage: int
    coverage_loss: int
    perturbation_magnitude: int

    def to_dict(self) -> dict[str, object]:
        return {
            "condition": self.condition,
            "members_in_set":
                list(self.members_in_set),
            "removed": list(self.removed),
            "baseline_coverage":
                self.baseline_coverage,
            "new_coverage": self.new_coverage,
            "coverage_loss": self.coverage_loss,
            "perturbation_magnitude":
                self.perturbation_magnitude,
        }


def _run_condition(
    condition: str, set_members: tuple[str, ...],
    removed: tuple[str, ...],
    cov: dict[str, frozenset[int]],
) -> ConditionResult:
    baseline = _baseline_coverage(cov, set_members)
    after = tuple(
        a for a in set_members if a not in removed
    )
    new_cov = _baseline_coverage(cov, after)
    loss = len(baseline - new_cov)
    return ConditionResult(
        condition=condition,
        members_in_set=set_members,
        removed=removed,
        baseline_coverage=len(baseline),
        new_coverage=len(new_cov),
        coverage_loss=loss,
        perturbation_magnitude=loss,
    )


def all_conditions() -> tuple[ConditionResult, ...]:
    cov = _coverages(EXTENDED_SET)
    return (
        _run_condition(
            RemovalCondition.A_SINGLE_HIGH_A.value,
            TEST_SET, (HIGH_PAIR_A,), cov,
        ),
        _run_condition(
            RemovalCondition.B_SINGLE_HIGH_B.value,
            TEST_SET, (HIGH_PAIR_B,), cov,
        ),
        _run_condition(
            RemovalCondition.C_DOUBLE_HIGH_PAIR.value,
            TEST_SET,
            (HIGH_PAIR_A, HIGH_PAIR_B), cov,
        ),
        _run_condition(
            RemovalCondition.D_UNRELATED_PAIR.value,
            EXTENDED_SET,
            (UNRELATED_A, UNRELATED_B), cov,
        ),
    )


def redundancy_unmasking_gain(
    conditions: tuple[ConditionResult, ...],
) -> int:
    by = {c.condition: c for c in conditions}
    single_max = max(
        by[RemovalCondition.A_SINGLE_HIGH_A.value]
        .perturbation_magnitude,
        by[RemovalCondition.B_SINGLE_HIGH_B.value]
        .perturbation_magnitude,
    )
    double = by[
        RemovalCondition.C_DOUBLE_HIGH_PAIR.value
    ].perturbation_magnitude
    return double - single_max


__all__ = [
    "BRIDGE_ANCHOR", "ConditionResult",
    "EXTENDED_SET", "HIGH_PAIR_A", "HIGH_PAIR_B",
    "LOW_ANCHOR", "PROBE_RADIUS", "RemovalCondition",
    "TEST_SET", "UNRELATED_A", "UNRELATED_B",
    "all_conditions",
    "redundancy_unmasking_gain",
]
