"""v3.103 — counterfactual +1 dim historical
compatibility primitives.

Defines:

* ``contradiction_type_for_text(text)`` -
  the deterministic rule used by v3.101's
  best candidate, generalised so it can score
  ANY trajectory text (not only the entangled
  pair).
* ``augmented_vector(traj_id, base_vec)`` -
  appends one extra coordinate (the
  contradiction_type) to a tail vector.
* ``augmented_dict(base_dict)`` - dict-level
  helper.
"""
from __future__ import annotations

from functools import lru_cache

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..t10.candidate import (
    CandidateDim, _CANDIDATE_FNS,
)
from ..t10_inject.inject import selected_candidate


CONTRADICTION_TYPE = (
    CandidateDim.CONTRADICTION_TYPE.value
)


@lru_cache(maxsize=1)
def _text_lookup() -> dict[str, str]:
    return {
        t.trajectory_id: t.text
        for t in extract_all_trajectories()
    }


def contradiction_type_for_text(text: str) -> float:
    """Return the v3.101 contradiction_type signal
    for any text - 1.0 if text contains a closed-
    set self-referential predicate pair, else
    0.0."""
    fn = _CANDIDATE_FNS[CONTRADICTION_TYPE]
    return fn(text)


def contradiction_type_for(
    trajectory_id: str,
) -> float:
    """Lookup the contradiction_type for any
    trajectory id; 0.0 if the id is unknown."""
    text = _text_lookup().get(trajectory_id, "")
    return contradiction_type_for_text(text)


def augmented_vector(
    trajectory_id: str,
    base_vec: tuple[float, ...],
) -> tuple[float, ...]:
    return base_vec + (
        contradiction_type_for(trajectory_id),
    )


def augmented_dict(
    base_dict: dict[str, tuple[float, ...]],
) -> dict[str, tuple[float, ...]]:
    return {
        tid: augmented_vector(tid, vec)
        for tid, vec in base_dict.items()
    }


__all__ = [
    "CONTRADICTION_TYPE",
    "augmented_dict",
    "augmented_vector",
    "contradiction_type_for",
    "contradiction_type_for_text",
    "selected_candidate",
]
