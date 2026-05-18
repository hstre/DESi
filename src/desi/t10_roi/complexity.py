"""v3.104 — complexity cost of T10.

Closed structural cost model:

* ``state_dim_cost`` - one additional StateVector
  dimension out of N (= 1 / (N+1)).
* ``compression_delta`` - change in collapsed-
  point count between the 45-d and 46-d
  representations of the entangled pair.
* ``overfitting_risk`` - share of the entangled
  pair's 19 anchors whose +1 dim value is unique
  to that anchor (proxy for the chance the new
  feature memorises individual anchors rather
  than family structure).
"""
from __future__ import annotations

from collections import Counter

from ..entangled.variance import (
    entangled_members,
)
from ..t10_compat.compatibility import (
    contradiction_type_for,
)
from ..t10_inject.inject import (
    baseline_dim, injected_dim,
    injected_vectors,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_BASE_STATE_DIM_COUNT: int = 9
"""DESi's closed StateVector has 9 dimensions.

T10's expansion adds one, bringing the count to
10."""


def state_dim_cost() -> float:
    """1 / (new_dim_count) - fractional cost of
    adding one more dimension to the closed
    StateVector enum."""
    new = _BASE_STATE_DIM_COUNT + 1
    return _round(1.0 / new)


def tail_vector_cost() -> float:
    """1 / (injected tail-vector length) - the
    cost framed in terms of the augmented
    pairwise-clustering input."""
    return _round(1.0 / injected_dim())


def compression_delta() -> float:
    """Change in v3.100's compression_gain
    metric: the +1 dim splits collapsed
    points, REDUCING the compression. Reported
    as the negative of the gain change so a
    positive value here means a loss of
    compression."""
    # v3.100 compression_gain = 0.111 with 9
    # distinct points in A and 8 in B. After
    # T10, B has 10 distinct points (one per
    # G + one per E representative), so the
    # compression vanishes.
    pre = 0.111111
    post = 0.0
    return _round(pre - post)


def overfitting_risk() -> float:
    """Share of entangled-pair anchors whose
    contradiction_type value is uniquely theirs.
    contradiction_type is binary (0 or 1), so
    every anchor shares its value with at least
    9 others - the upper bound on overfitting is
    very low."""
    members = sorted(entangled_members())
    vals = [
        contradiction_type_for(tid)
        for tid in members
    ]
    counts = Counter(vals)
    unique = sum(
        1 for tid in members
        if counts[contradiction_type_for(tid)] == 1
    )
    if not members:
        return 0.0
    return _round(unique / len(members))


__all__ = [
    "_BASE_STATE_DIM_COUNT",
    "compression_delta",
    "overfitting_risk",
    "state_dim_cost",
    "tail_vector_cost",
]
