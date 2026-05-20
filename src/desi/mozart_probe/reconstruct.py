"""v3.69 — historical probe reconstruction.

Wraps the coverage primitives with bridge-expansion
and gap-event timelines so the report can answer the
directive's per-probe questions without re-deriving
the state-by-state structure.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from .coverage import (
    HISTORICAL_PROBES, ProbeCoverage,
    historical_coverages, probe_coverage,
)


@dataclass(frozen=True)
class ProbeTimeline:
    trajectory_id: str
    support_path: tuple[float, ...]
    frame_path: tuple[float, ...]
    bridge_indices: tuple[int, ...]
    gap_indices: tuple[int, ...]
    available: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "support_path": list(self.support_path),
            "frame_path": list(self.frame_path),
            "bridge_indices":
                list(self.bridge_indices),
            "gap_indices": list(self.gap_indices),
            "available": self.available,
        }


def _missing_timeline(tid: str) -> ProbeTimeline:
    return ProbeTimeline(
        trajectory_id=tid, support_path=(),
        frame_path=(), bridge_indices=(),
        gap_indices=(), available=False,
    )


def probe_timeline(tid: str) -> ProbeTimeline:
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    t = trajs.get(tid)
    if t is None:
        return _missing_timeline(tid)
    return ProbeTimeline(
        trajectory_id=tid,
        support_path=tuple(
            s.support_state for s in t.states
        ),
        frame_path=tuple(
            s.frame_id for s in t.states
        ),
        bridge_indices=tuple(
            i for i, s in enumerate(t.states)
            if s.support_state == 2.0
        ),
        gap_indices=tuple(
            i for i, s in enumerate(t.states)
            if s.support_state == 1.0
        ),
        available=True,
    )


def historical_timelines() -> tuple[
    ProbeTimeline, ...,
]:
    return tuple(
        probe_timeline(p) for p in HISTORICAL_PROBES
    )


def present_probes() -> tuple[str, ...]:
    return tuple(
        p for p in HISTORICAL_PROBES
        if probe_coverage(p).available
    )


def missing_probes() -> tuple[str, ...]:
    return tuple(
        p for p in HISTORICAL_PROBES
        if not probe_coverage(p).available
    )


__all__ = [
    "ProbeTimeline", "historical_timelines",
    "missing_probes", "present_probes",
    "probe_timeline",
]
