"""v10.2 — norm-drift and path-rigidity
metrics."""
from __future__ import annotations

import math

from .memory import fixture


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _euclidean(a, b) -> float:
    return math.sqrt(sum(
        (x - y) ** 2 for x, y in zip(a, b)
    ))


def norm_drift() -> float:
    """L2 distance between the earliest and the
    most recent norm_vector. Bounded drift means
    the institutional norm has evolved but not
    runaway."""
    rows = sorted(
        fixture(), key=lambda d: d.timestamp,
    )
    if len(rows) < 2:
        return 0.0
    first = rows[0].norm_vector
    last = rows[-1].norm_vector
    return _round(_euclidean(first, last))


def path_rigidity() -> float:
    """How much does the present norm depend on
    the EARLIEST decision rather than recent
    ones? Operationalized as
    cosine_similarity(earliest, latest);
    very high values (> 0.95) AND zero overturn
    events would mean the system is locked into
    its origin."""
    rows = sorted(
        fixture(), key=lambda d: d.timestamp,
    )
    if len(rows) < 2:
        return 0.0
    a = rows[0].norm_vector
    b = rows[-1].norm_vector
    dot = sum(
        x * y for x, y in zip(a, b)
    )
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    cos = dot / (na * nb)
    has_overturn = any(
        d.overturned_by is not None
        for d in fixture()
    )
    # Pure cosine similarity penalised by an
    # observable overturn event - if the system
    # ever changed its mind, the rigidity score
    # is reduced.
    if has_overturn:
        return _round(max(0.0, cos - 0.10))
    return _round(cos)


__all__ = [
    "norm_drift",
    "path_rigidity",
]
