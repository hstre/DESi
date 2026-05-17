"""v3.57 — content vs method feature partition.

The directive's feature taxonomy (§ v3.57) maps onto
the closed 9-dimensional StateVector schema as follows:

CONTENT_DIMS (5):
* frame_id           — what frame the audit is in
  (directive "frame_id")
* novelty            — semantic novelty of this state
  (directive "claim pattern" / vocabulary)
* anchor_density     — density of premises supporting
  the content (directive "vocabulary overlap")
* contradiction_load — contradictions present in the
  content (directive "semantic family")
* source_quality     — quality / family of the source
  (directive "source corpus" projected onto a numeric
  axis)

METHOD_DIMS (4):
* support_state      — audit's commitment trajectory
  (directive "support_state path")
* routing_state      — which resolver branch
  (directive "resolver branch pattern")
* branch_cost        — how much branching the method
  cost (directive "intervention path")
* confidence         — how confident the method is
  (directive "gate path" / audit decision sequence)

The split is exhaustive: 5 + 4 = 9 = all StateVector
dimensions. The directive's additional content
features (source corpus, claim pattern) are reflected
either via these numeric dims or via the trajectory
ID's source-corpus prefix (a categorical add-on).
"""
from __future__ import annotations

from ..epistemic_trajectory.state import (
    DIMENSION_NAMES, StateVector,
)


CONTENT_DIMS: tuple[str, ...] = (
    "frame_id", "novelty", "anchor_density",
    "contradiction_load", "source_quality",
)
METHOD_DIMS: tuple[str, ...] = (
    "support_state", "routing_state",
    "branch_cost", "confidence",
)


# Sanity check: the partition covers every dimension.
assert (
    set(CONTENT_DIMS) | set(METHOD_DIMS)
) == set(DIMENSION_NAMES), (
    "CONTENT_DIMS U METHOD_DIMS must equal the full "
    "DIMENSION_NAMES set"
)
assert (
    set(CONTENT_DIMS) & set(METHOD_DIMS)
) == set(), (
    "CONTENT_DIMS and METHOD_DIMS must be disjoint"
)


def content_state(state: StateVector) -> tuple[float, ...]:
    return tuple(
        getattr(state, d) for d in CONTENT_DIMS
    )


def method_state(state: StateVector) -> tuple[float, ...]:
    return tuple(
        getattr(state, d) for d in METHOD_DIMS
    )


def content_vector(
    states: tuple[StateVector, ...],
) -> tuple[float, ...]:
    """Concatenate per-state content tuples into the
    flat trajectory feature vector."""
    out: list[float] = []
    for s in states:
        out.extend(content_state(s))
    return tuple(out)


def method_vector(
    states: tuple[StateVector, ...],
) -> tuple[float, ...]:
    out: list[float] = []
    for s in states:
        out.extend(method_state(s))
    return tuple(out)


__all__ = [
    "CONTENT_DIMS", "METHOD_DIMS", "content_state",
    "content_vector", "method_state",
    "method_vector",
]
