"""v3.31 — plateau census extractor.

Walks the entire 395-trajectory corpus, records every
trajectory's support_state landing, and tags plateaus.
The v3.30 cause-aware-control non-rescued set is also
loaded so the census can cross-reference plateau and
non-rescued.
"""
from __future__ import annotations

from ..cause_aware_control.controller import control_all
from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from .state import (
    PlateauKind, PlateauObservation,
    _PLATEAU_SUPPORT_VALUE, visits_to_plateau,
)


def census(
) -> tuple[PlateauObservation, ...]:
    trajs = extract_all_trajectories()
    out: list[PlateauObservation] = []
    for t in trajs:
        final = t.states[-1].support_state
        visits = visits_to_plateau(t.states)
        is_plateau = final == _PLATEAU_SUPPORT_VALUE
        if is_plateau:
            kind = PlateauKind.TERMINAL_PLATEAU.value
        elif visits > 0:
            kind = PlateauKind.TRANSIENT_PLATEAU.value
        else:
            kind = PlateauKind.NON_PLATEAU.value
        out.append(PlateauObservation(
            trajectory_id=t.trajectory_id,
            source=t.source.value,
            final_support_state=final,
            visits_to_plateau=visits,
            is_plateau=is_plateau, kind=kind,
        ))
    return tuple(out)


def non_rescued_ids() -> tuple[str, ...]:
    """Trajectory IDs the v3.30 cause-aware controller
    intervened on but did not rescue (intervention
    fired, original_final != counterfactual_final → not
    a REJECTED rescue)."""
    outs = control_all()
    return tuple(
        o.trajectory_id for o in outs
        if o.intervened and not o.rescued
        and o.cause != "UNKNOWN"
    )


def plateau_trajectory_ids() -> tuple[str, ...]:
    return tuple(
        o.trajectory_id for o in census()
        if o.is_plateau
    )


__all__ = [
    "census", "non_rescued_ids",
    "plateau_trajectory_ids",
]
