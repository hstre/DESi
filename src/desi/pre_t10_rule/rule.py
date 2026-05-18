"""v3.120 — pre-T10 blindness check.

Closed deployment rule:

    Before activating T10 on a blindness pool,
    require the pool's text_variance to be at
    or above ``BLINDNESS_CHECK_THRESHOLD``.
    Pools below the threshold are by definition
    irrecoverable; T10 must not be applied.

The threshold is pinned to the v3.119
recoverability_threshold so any drift surfaces
immediately.
"""
from __future__ import annotations

from functools import lru_cache

from ..state_blindness.census import (
    BlindnessPool, cross_family_pools,
)
from ..state_blindness_taxonomy.taxonomy import (
    _mean_pairwise_jaccard,
)
from ..t10_boundary.boundary import (
    recoverability_threshold as v3119_threshold,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=1)
def BLINDNESS_CHECK_THRESHOLD() -> float:
    """Pinned to v3.119."""
    return v3119_threshold()


def pool_text_variance(
    pool: BlindnessPool,
) -> float:
    return _round(
        1.0 - _mean_pairwise_jaccard(
            pool.member_ids,
        ),
    )


def rule_allows_t10(
    pool: BlindnessPool,
) -> bool:
    return pool_text_variance(pool) >= (
        BLINDNESS_CHECK_THRESHOLD()
    )


def pools_allowed() -> tuple[
    BlindnessPool, ...,
]:
    return tuple(
        p for p in cross_family_pools()
        if rule_allows_t10(p)
    )


def pools_blocked() -> tuple[
    BlindnessPool, ...,
]:
    return tuple(
        p for p in cross_family_pools()
        if not rule_allows_t10(p)
    )


__all__ = [
    "BLINDNESS_CHECK_THRESHOLD",
    "pool_text_variance",
    "pools_allowed",
    "pools_blocked",
    "rule_allows_t10",
]
