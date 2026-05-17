"""v3.46 — GAP_DETECTED inventory.

Identifies every trajectory in the corpus whose final
state or any intermediate state lands at
``GAP_DETECTED`` (support_state = 1.0). Classifies
each by pattern and cross-references against the
v3.30 cause-aware controller's non-rescued set so we
can answer the directive's question 2 ("any GAP
outside the 22 non-rescued?").
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..cause_aware_control.controller import control_all
from ..epistemic_trajectory.extractor import (
    Trajectory, extract_all_trajectories,
)
from .state import (
    GAP_DETECTED_STATE, GapPattern, classify_gap,
)


def _source_corpus(traj_id: str) -> str:
    """Trajectory IDs are ``<source>:<rest>``. Extract
    the source token (matches TrajectorySource values
    used elsewhere in the corpus)."""
    if ":" in traj_id:
        return traj_id.split(":", 1)[0]
    return traj_id


@dataclass(frozen=True)
class GapCase:
    trajectory_id: str
    source_corpus: str
    trajectory_length: int
    pattern: str                 # GapPattern value
    gap_index_first: int
    gap_index_last: int
    gap_visit_count: int
    final_support_state: float
    in_v330_non_rescued: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "source_corpus": self.source_corpus,
            "trajectory_length":
                self.trajectory_length,
            "pattern": self.pattern,
            "gap_index_first": self.gap_index_first,
            "gap_index_last": self.gap_index_last,
            "gap_visit_count": self.gap_visit_count,
            "final_support_state":
                self.final_support_state,
            "in_v330_non_rescued":
                self.in_v330_non_rescued,
        }


def _non_rescued_ids() -> set[str]:
    return {
        o.trajectory_id for o in control_all()
        if not o.rescued
    }


def _gap_indices(traj: Trajectory) -> list[int]:
    return [
        i for i, s in enumerate(traj.states)
        if s.support_state == GAP_DETECTED_STATE
    ]


def collect_gap_cases() -> tuple[GapCase, ...]:
    nr = _non_rescued_ids()
    out: list[GapCase] = []
    for t in extract_all_trajectories():
        visits = _gap_indices(t)
        if not visits:
            continue
        out.append(GapCase(
            trajectory_id=t.trajectory_id,
            source_corpus=_source_corpus(t.trajectory_id),
            trajectory_length=len(t.states),
            pattern=classify_gap(t.states).value,
            gap_index_first=visits[0],
            gap_index_last=visits[-1],
            gap_visit_count=len(visits),
            final_support_state=t.states[-1].support_state,
            in_v330_non_rescued=(
                t.trajectory_id in nr
            ),
        ))
    return tuple(out)


def terminal_gap_cases() -> tuple[GapCase, ...]:
    return tuple(
        c for c in collect_gap_cases()
        if c.pattern in (
            GapPattern.TERMINAL_GAP.value,
            GapPattern.MID_RUN_GAP.value,
        )
    )


def transient_gap_cases() -> tuple[GapCase, ...]:
    return tuple(
        c for c in collect_gap_cases()
        if c.pattern == GapPattern.TRANSIENT_GAP.value
    )


def gap_cases_outside_non_rescued(
) -> tuple[GapCase, ...]:
    return tuple(
        c for c in collect_gap_cases()
        if not c.in_v330_non_rescued
    )


def source_corpus_distribution(
) -> dict[str, int]:
    return dict(Counter(
        c.source_corpus for c in collect_gap_cases()
    ))


__all__ = [
    "GapCase", "collect_gap_cases",
    "gap_cases_outside_non_rescued",
    "source_corpus_distribution",
    "terminal_gap_cases", "transient_gap_cases",
]
