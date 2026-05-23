"""v3.123 — closed 2D rule search.

Test orthogonal-axis candidate rules of the form

    text_variance >= T1
    AND <axis>(pool) >= T2

over a small fixed set of interpretable
candidates. Each candidate axis is a closed
function of the pool's structure (no ML, no
blackbox).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ..state_blindness.census import (
    BlindnessPool, cross_family_pools,
)
from ..t10_boundary.boundary import (
    all_pool_recoverability,
)


class SecondAxis(str, Enum):
    MEMBERS_PER_FAMILY    = (
        "members_per_family"
    )
    FAMILY_COUNT          = "family_count"
    POOL_ENTROPY          = "pool_entropy"
    MEMBER_COUNT          = "member_count"


SECOND_AXES: tuple[str, ...] = tuple(
    a.value for a in SecondAxis
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _members_per_family(
    pool: BlindnessPool,
) -> float:
    if pool.family_count <= 0:
        return 0.0
    return _round(
        pool.member_count / pool.family_count,
    )


def _family_count(pool: BlindnessPool) -> float:
    return float(pool.family_count)


def _member_count(pool: BlindnessPool) -> float:
    return float(pool.member_count)


def _pool_entropy(pool: BlindnessPool) -> float:
    """Shannon entropy over the family
    distribution within the pool. High entropy
    = members spread evenly across families."""
    import math
    from collections import Counter
    cnt = Counter()
    for mid in pool.member_ids:
        for fid in pool.family_ids:
            if mid.startswith(fid):
                cnt[fid] += 1
                break
    total = sum(cnt.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in cnt.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return _round(h)


_AXIS_FNS: dict[str, "callable"] = {
    SecondAxis.MEMBERS_PER_FAMILY.value:
        _members_per_family,
    SecondAxis.FAMILY_COUNT.value:
        _family_count,
    SecondAxis.POOL_ENTROPY.value:
        _pool_entropy,
    SecondAxis.MEMBER_COUNT.value:
        _member_count,
}


def axis_value(
    axis: str, pool: BlindnessPool,
) -> float:
    return _AXIS_FNS[axis](pool)


_T1: float = 0.541667
"""Pinned v3.119 recoverability threshold."""

_T2_GRID: tuple[float, ...] = tuple(
    _round(0.5 + 0.5 * i)
    for i in range(12)
)
"""Search points for T2 across plausible values
(0.5, 1.0, 1.5, ..., 6.0)."""


_AXIS_DIRECTION: dict[str, str] = {
    # MEMBERS_PER_FAMILY: rescuable >= T2;
    # higher excludes the singleton-pool
    # false positives.
    SecondAxis.MEMBERS_PER_FAMILY.value: ">=",
    # FAMILY_COUNT: lower is more rescuable
    # (the false positives have higher family
    # count than the rescuable 2-family pools).
    SecondAxis.FAMILY_COUNT.value:        "<=",
    # POOL_ENTROPY: rescuable >= T2.
    SecondAxis.POOL_ENTROPY.value:        ">=",
    # MEMBER_COUNT: rescuable >= T2.
    SecondAxis.MEMBER_COUNT.value:        ">=",
}


@dataclass(frozen=True)
class TwoDRule:
    axis: str
    t1: float
    t2: float
    far: float
    tpr: float
    allowed_count: int
    blocked_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "axis": self.axis,
            "t1": self.t1,
            "t2": self.t2,
            "far": self.far,
            "tpr": self.tpr,
            "allowed_count":
                self.allowed_count,
            "blocked_count":
                self.blocked_count,
        }


def _check(
    pool: BlindnessPool, recoverability,
    axis: str, t1: float, t2: float,
) -> bool:
    if recoverability.text_variance < t1:
        return False
    v = axis_value(axis, pool)
    direction = _AXIS_DIRECTION[axis]
    if direction == ">=":
        return v >= t2
    return v <= t2


@lru_cache(maxsize=1)
def all_rules() -> tuple[TwoDRule, ...]:
    pools_by_id = {
        p.pool_id: p for p in cross_family_pools()
    }
    rec = list(all_pool_recoverability())
    out: list[TwoDRule] = []
    for axis in SECOND_AXES:
        for t2 in _T2_GRID:
            allowed = 0
            blocked = 0
            tp = 0
            fp = 0
            fn = 0
            for r in rec:
                pool = pools_by_id[r.pool_id]
                ok = _check(
                    pool, r, axis, _T1, t2,
                )
                if ok:
                    allowed += 1
                    if r.rescuable:
                        tp += 1
                    else:
                        fp += 1
                else:
                    blocked += 1
                    if r.rescuable:
                        fn += 1
            total_pos = sum(
                1 for r in rec if r.rescuable
            )
            tpr = (
                _round(tp / total_pos)
                if total_pos else 0.0
            )
            far = (
                _round(fp / allowed)
                if allowed else 0.0
            )
            out.append(TwoDRule(
                axis=axis, t1=_T1, t2=t2,
                far=far, tpr=tpr,
                allowed_count=allowed,
                blocked_count=blocked,
            ))
    return tuple(out)


def best_rule() -> TwoDRule:
    """Pick by (tpr desc, far asc, t2 asc)."""
    return max(
        all_rules(),
        key=lambda r: (
            r.tpr, -r.far, -r.t2,
            r.axis,
        ),
    )


__all__ = [
    "SECOND_AXES",
    "SecondAxis",
    "TwoDRule",
    "all_rules",
    "axis_value",
    "best_rule",
]
